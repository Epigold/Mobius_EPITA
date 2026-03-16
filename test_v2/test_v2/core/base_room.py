# -*- coding: utf-8 -*-
# core/base_room.py - Salle de base + joueur + ennemis avec graphismes complets

import pygame
import math
import random
from .constants  import *
from .graphics   import (SpriteCache, BackgroundRenderer, HUDRenderer,
                          ParticleSystem, FloatingTextSystem, ScreenEffects,
                          draw_weapon_in_hand, draw_enemy_health_bar, tint_surface)
from .mechanics  import Weapon, Bullet, MeleeAttack, EnemyBullet, PowerUp, Chest


# ══════════════════════════════════════════════════════════════════════════════
#  JOUEUR
# ══════════════════════════════════════════════════════════════════════════════

class Player(pygame.sprite.Sprite):

    ANIM_FRAMES = {
        "idle": ["char_idle_one_arm"],
        "walk": ["char_walk_one_arm"],
        "run":  ["char_run1_one_arm", "char_run2_one_arm", "char_run3_one_arm"],
    }

    SIZE = 80

    def __init__(self, skill=None):
        super().__init__()
        self.skill = skill

        # ── Stats ───────────────────────────────────────────────────────────
        self.max_health  = 100
        self.health      = 100
        self.max_stamina = 100
        self.stamina     = 100
        self.stamina_regen = 0.25
        self.speed       = 7
        self.kills       = 0
        self.coins       = 0

        # ── Buffs compétence ────────────────────────────────────────────────
        if skill == "tank":
            self.max_health = self.health = 150
            self.speed = 5
        elif skill == "berserker":
            self.max_health = self.health = 80
            self.speed = 9
        elif skill == "mage":
            self.max_stamina = self.stamina = 150
            self.stamina_regen = 0.35

        # ── Dash ────────────────────────────────────────────────────────────
        self.dashing       = False
        self.dash_time     = 0
        self.dash_cooldown = 0
        self._dash_cd_max  = DASH_COOLDOWN // 2 if skill == "ninja" else DASH_COOLDOWN
        self.dir_x = self.dir_y = 0
        self.facing_right = True

        # ── Skill ────────────────────────────────────────────────────────────
        self.skill_cooldown = 0
        self.skill_active   = False
        self.skill_duration = 0

        # ── Boosts ───────────────────────────────────────────────────────────
        self.damage_boost = 1.0
        self.speed_boost  = 1.0
        self.boost_timer  = 0

        # ── Armes ────────────────────────────────────────────────────────────
        self.inventory = ["rock"]
        self.current_weapon = Weapon("rock")

        # ── Animation sprites ────────────────────────────────────────────────
        self._anim_cache  = {}
        self._anim_state  = "idle"
        self._anim_frame  = 0
        self._anim_timer  = 0
        self._anim_speed  = 8  # frames entre chaque sprite

        self._load_sprites()

        self.image = self._get_frame()
        self.rect  = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.hitbox = pygame.Rect(0, 0, self.SIZE * 0.4, self.SIZE * 0.4)
        self.hitbox.center = self.rect.center

        # Ref pour groupes de sprites (injectés par BaseRoom)
        self._bullets       = None
        self._melee_attacks = None
        self._all_sprites   = None

    # ── Chargement sprites ────────────────────────────────────────────────────

    def _load_sprites(self):
        cache = SpriteCache.get()
        for state, names in self.ANIM_FRAMES.items():
            frames = []
            for name in names:
                img = cache.load("sprites_final", f"{name}.png",
                                  size=(self.SIZE, self.SIZE))
                frames.append(img)
            self._anim_cache[state] = frames

    def _get_frame(self):
        frames = self._anim_cache.get(self._anim_state, self._anim_cache["idle"])
        idx    = min(self._anim_frame, len(frames) - 1)
        img    = frames[idx]
        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)
        return img

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, keys):
        self._update_stamina()
        self._update_timers()
        self._handle_move(keys)
        self._update_anim()
        self.current_weapon.update_cooldown()

    def _update_stamina(self):
        if self.stamina < self.max_stamina:
            self.stamina = min(self.stamina + self.stamina_regen, self.max_stamina)

    def _update_timers(self):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.skill_cooldown > 0:
            self.skill_cooldown -= 1
        if self.skill_duration > 0:
            self.skill_duration -= 1
            if self.skill_duration == 0:
                self.skill_active = False
        if self.boost_timer > 0:
            self.boost_timer -= 1
            if self.boost_timer == 0:
                self.damage_boost = self.speed_boost = 1.0

    def _handle_move(self, keys):
        # Orientation souris
        mx, _ = pygame.mouse.get_pos()
        self.facing_right = mx >= self.rect.centerx

        if self.dashing:
            self.rect.x += self.dir_x * DASH_SPEED
            self.rect.y += self.dir_y * DASH_SPEED
            self.dash_time -= 1
            if self.dash_time <= 0:
                self.dashing = False
        else:
            dx = dy = 0
            if keys[pygame.K_d]: dx += 1
            if keys[pygame.K_q] or keys[pygame.K_a]: dx -= 1
            if keys[pygame.K_s]: dy += 1
            if keys[pygame.K_z] or keys[pygame.K_w]: dy -= 1

            if dx or dy:
                norm = math.hypot(dx, dy) or 1
                self.dir_x, self.dir_y = dx / norm, dy / norm

            effective = self.speed * self.speed_boost
            self.rect.x += self.dir_x * effective if (dx or dy) else 0
            self.rect.y += self.dir_y * effective if (dx or dy) else 0
            self._anim_state = "run" if (dx or dy) else "idle"

            # Dash
            if keys[pygame.K_SPACE] and self.dash_cooldown == 0 and self.stamina >= DASH_STAMINA_COST:
                self.dashing       = True
                self.dash_time     = DASH_TIME
                self.dash_cooldown = self._dash_cd_max
                self.stamina      -= DASH_STAMINA_COST

        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.hitbox.center = self.rect.center

    def _update_anim(self):
        self._anim_timer += 1
        if self._anim_timer >= self._anim_speed:
            self._anim_timer = 0
            frames = self._anim_cache.get(self._anim_state, self._anim_cache["idle"])
            self._anim_frame = (self._anim_frame + 1) % len(frames)
        self.image = self._get_frame()

    # ── Attaque ───────────────────────────────────────────────────────────────

    def attack(self, mx, my) -> bool:
        if not self.current_weapon.can_use(self.stamina):
            return False

        self.stamina -= self.current_weapon.stamina_cost
        self.current_weapon.use()
        dmult = self.damage_boost

        if self.current_weapon.type == "ranged":
            b = Bullet(self.rect.centerx, self.rect.centery,
                       mx, my, self.current_weapon, dmult)
            if self._bullets is not None:
                self._bullets.add(b)
            if self._all_sprites is not None:
                self._all_sprites.add(b)
        else:
            m = MeleeAttack(self.rect.centerx, self.rect.centery,
                            mx, my, self.current_weapon, dmult)
            if self._melee_attacks is not None:
                self._melee_attacks.add(m)
            if self._all_sprites is not None:
                self._all_sprites.add(m)
        return True

    # ── Compétence ────────────────────────────────────────────────────────────

    def use_skill(self) -> bool:
        if self.skill_cooldown > 0 or not self.skill:
            return False
        if self.skill == "tank":
            self.skill_active   = True
            self.skill_duration = 300
            self.skill_cooldown = 1800
        elif self.skill == "berserker":
            self.damage_boost = 2.0
            self.boost_timer  = 300
            self.skill_cooldown = 1200
        elif self.skill == "vampire":
            self.skill_active   = True
            self.skill_duration = 600
            self.skill_cooldown = 900
        elif self.skill == "ninja":
            mx, my = pygame.mouse.get_pos()
            self.rect.center   = (mx, my)
            self.hitbox.center = self.rect.center
            self.skill_cooldown = 600
        elif self.skill == "mage" and self._bullets and self._all_sprites:
            for deg in range(0, 360, 30):
                rad = math.radians(deg)
                tx  = self.rect.centerx + math.cos(rad) * 500
                ty  = self.rect.centery + math.sin(rad) * 500
                b   = Bullet(self.rect.centerx, self.rect.centery,
                             tx, ty, self.current_weapon, 1.5)
                self._bullets.add(b)
                self._all_sprites.add(b)
            self.skill_cooldown = 1200
        return True

    # ── Armes ─────────────────────────────────────────────────────────────────

    def change_weapon(self, key: str):
        if key in self.inventory:
            self.current_weapon = Weapon(key)

    def add_weapon(self, key: str):
        if key not in self.inventory:
            self.inventory.append(key)

    # ── Dégâts / soins ────────────────────────────────────────────────────────

    def take_damage(self, amount: float):
        if self.dashing:
            return
        if self.skill == "tank" and self.skill_active:
            amount *= 0.5
        self.health = max(0, self.health - amount)

    def add_kill(self):
        self.kills += 1
        if random.random() < 0.3:
            self.coins += 1
        if self.skill == "vampire" and self.skill_active:
            self.health = min(self.health + 10, self.max_health)

    def apply_powerup(self, ptype: str):
        if ptype == "damage":
            self.damage_boost = 1.5
            self.boost_timer  = 600
        elif ptype == "speed":
            self.speed_boost = 1.5
            self.boost_timer = 600
        elif ptype == "health":
            self.health = min(self.health + 30, self.max_health)
        elif ptype == "stamina":
            self.max_stamina += 10
            self.stamina = self.max_stamina


# ══════════════════════════════════════════════════════════════════════════════
#  ENNEMIS
# ══════════════════════════════════════════════════════════════════════════════

class Enemy(pygame.sprite.Sprite):

    def __init__(self, player: Player, epoch_key: str,
                 enemy_type: str = "rusher",
                 sprite_path=None):
        super().__init__()
        self.player     = player
        self.epoch_key  = epoch_key
        self.enemy_type = enemy_type

        cfg = ENEMY_CONFIG.get(epoch_key, ENEMY_CONFIG["prehistoire"])[enemy_type]
        diff = EPOCHS.get(epoch_key, {}).get("difficulty", 1.0)

        self.speed      = cfg["speed"]
        self.max_health = int(cfg["health"] * diff)
        self.health     = self.max_health
        self.damage     = int(cfg["damage"] * diff)
        self.size       = cfg["size"]

        self.damage_cooldown = 0
        self.shoot_cooldown  = 0

        # ── Sprite ──────────────────────────────────────────────────────────
        epoch_color = EPOCHS.get(epoch_key, {}).get("enemy_tint", (180, 80, 80))
        self._build_sprite(sprite_path, epoch_color)
        self._spawn_on_edge()

    def _build_sprite(self, sprite_path, tint_color):
        """Génère un sprite procedural si pas de fichier, sinon charge l'image."""
        if sprite_path:
            try:
                cache = SpriteCache.get()
                img   = cache.load(*sprite_path, size=(self.size, self.size))
                self.base_image = img
                self.image      = img.copy()
                self.rect       = self.image.get_rect()
                return
            except Exception:
                pass
        # Fallback procedural
        self.base_image = self._draw_procedural(tint_color)
        self.image      = self.base_image.copy()
        self.rect       = self.image.get_rect()

    def _draw_procedural(self, color):
        """Dessin procédural selon le type d'ennemi."""
        s    = self.size
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        r, g, b = color[:3]

        if self.enemy_type == "tank":
            # Corps massif avec armure
            pygame.draw.ellipse(surf, (r, g, b), (2, 10, s - 4, s - 12))
            pygame.draw.ellipse(surf, (min(255, r + 40), min(255, g + 40), min(255, b + 40)),
                                (6, 14, s - 12, s - 20))
            # Tête
            pygame.draw.circle(surf, (r, g, b), (s // 2, s // 4), s // 5)
            # Yeux rouges
            pygame.draw.circle(surf, RED, (s // 2 - 5, s // 4), 4)
            pygame.draw.circle(surf, RED, (s // 2 + 5, s // 4), 4)
            # Bordure
            pygame.draw.ellipse(surf, WHITE, (2, 10, s - 4, s - 12), 2)

        elif self.enemy_type == "rusher":
            # Corps fin et agile
            pygame.draw.ellipse(surf, (r, g, b), (6, 8, s - 12, s - 10))
            pygame.draw.circle(surf, (min(255, r + 30), g, b), (s // 2, s // 5), s // 6)
            # Yeux jaunes
            pygame.draw.circle(surf, YELLOW, (s // 2 - 4, s // 5), 3)
            pygame.draw.circle(surf, YELLOW, (s // 2 + 4, s // 5), 3)
            # Lignes vitesse
            for lx in [s // 4, s * 3 // 4]:
                pygame.draw.line(surf, (min(255, r + 80), min(255, g + 80), b),
                                 (lx, s // 2), (lx - 8, s * 3 // 4), 2)

        elif self.enemy_type == "sniper":
            # Corps avec viseur
            pygame.draw.polygon(surf, (r, g, b),
                                [(s // 2, 4), (s - 6, s - 6), (6, s - 6)])
            pygame.draw.circle(surf, (min(255, r + 50), min(255, g + 50), min(255, b + 50)),
                                (s // 2, s // 3), s // 6)
            # Viseur
            cx, cy = s // 2, s // 3
            pygame.draw.circle(surf, WHITE, (cx, cy), s // 6, 1)
            pygame.draw.line(surf, WHITE, (cx - s // 4, cy), (cx + s // 4, cy), 1)
            pygame.draw.line(surf, WHITE, (cx, cy - s // 4), (cx, cy + s // 4), 1)

        elif self.enemy_type == "boss":
            # Boss : grand, menaçant
            pygame.draw.ellipse(surf, (r // 2, g // 2, b // 2), (0, 0, s, s))
            pygame.draw.ellipse(surf, (r, g, b), (4, 4, s - 8, s - 8))
            # Couronne/spikes
            for i in range(8):
                angle = math.radians(i * 45)
                px = int(s // 2 + math.cos(angle) * (s // 2 - 2))
                py = int(s // 2 + math.sin(angle) * (s // 2 - 2))
                pygame.draw.circle(surf, (min(255, r + 60), min(255, g + 40), b), (px, py), 5)
            # Yeux rouges brillants
            pygame.draw.circle(surf, (255, 0, 0), (s // 3, s // 3), 8)
            pygame.draw.circle(surf, (255, 0, 0), (s * 2 // 3, s // 3), 8)
            pygame.draw.circle(surf, (255, 150, 150), (s // 3, s // 3), 4)
            pygame.draw.circle(surf, (255, 150, 150), (s * 2 // 3, s // 3), 4)
            pygame.draw.ellipse(surf, WHITE, (0, 0, s, s), 3)

        return surf

    def _spawn_on_edge(self):
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            self.rect.centerx = random.randint(50, SCREEN_WIDTH - 50)
            self.rect.top     = -self.size
        elif edge == "bottom":
            self.rect.centerx = random.randint(50, SCREEN_WIDTH - 50)
            self.rect.bottom  = SCREEN_HEIGHT + self.size
        elif edge == "left":
            self.rect.left   = -self.size
            self.rect.centery = random.randint(50, SCREEN_HEIGHT - 50)
        else:
            self.rect.right   = SCREEN_WIDTH + self.size
            self.rect.centery = random.randint(50, SCREEN_HEIGHT - 50)

    # ── IA ────────────────────────────────────────────────────────────────────

    def basic_movement(self):
        dx = self.player.rect.x - self.rect.x
        dy = self.player.rect.y - self.rect.y
        dist = math.hypot(dx, dy) or 1
        self.rect.x += (dx / dist) * self.speed
        self.rect.y += (dy / dist) * self.speed

    def handle_collision(self):
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1
            return
        if self.rect.colliderect(self.player.hitbox):
            self.player.take_damage(self.damage)
            self.damage_cooldown = 30

    def update(self, *args):
        self.basic_movement()
        self.handle_collision()

    def draw_health_bar(self, surface):
        draw_enemy_health_bar(surface, self.rect, self.health, self.max_health,
                               EPOCHS.get(self.epoch_key, {}).get("color", RED),
                               is_boss=(self.enemy_type == "boss"),
                               screen_w=SCREEN_WIDTH)


class TankEnemy(Enemy):
    def __init__(self, player, epoch_key):
        super().__init__(player, epoch_key, "tank")
        self._hit_flash = 0

    def update(self, *args):
        self.basic_movement()
        self.handle_collision()
        if self._hit_flash > 0:
            self._hit_flash -= 1


class RusherEnemy(Enemy):
    def __init__(self, player, epoch_key):
        super().__init__(player, epoch_key, "rusher")


class SniperEnemy(Enemy):
    def __init__(self, player, epoch_key, enemy_bullets_group, all_sprites_group):
        super().__init__(player, epoch_key, "sniper")
        self._eb_group     = enemy_bullets_group
        self._all_sprites  = all_sprites_group
        self.shoot_delay   = 90
        self.shoot_range   = 500

    def update(self, *args):
        dx = self.player.rect.x - self.rect.x
        dy = self.player.rect.y - self.rect.y
        dist = math.hypot(dx, dy) or 1

        if dist > self.shoot_range:
            self.basic_movement()
        elif dist < self.shoot_range - 60:
            # Retraite
            self.rect.x -= (dx / dist) * self.speed
            self.rect.y -= (dy / dist) * self.speed

        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and dist <= self.shoot_range:
            b = EnemyBullet(self.rect.centerx, self.rect.centery,
                             self.player.rect.centerx, self.player.rect.centery,
                             speed=9, damage=self.damage,
                             epoch_key=self.epoch_key)
            self._eb_group.add(b)
            self._all_sprites.add(b)
            self.shoot_cooldown = self.shoot_delay

        self.handle_collision()


class BossEnemy(Enemy):
    def __init__(self, player, epoch_key, wave,
                 enemy_bullets_group, all_sprites_group):
        super().__init__(player, epoch_key, "boss")
        cfg = ENEMY_CONFIG.get(epoch_key, ENEMY_CONFIG["prehistoire"])["boss"]
        diff = EPOCHS.get(epoch_key, {}).get("difficulty", 1.0)
        self.max_health = int(cfg["health"] * diff + wave * 200)
        self.health     = self.max_health

        self._eb_group    = enemy_bullets_group
        self._all_sprites = all_sprites_group
        self.wave         = wave
        self.phase        = 1
        self.attack_cd    = 0
        self.charging     = False
        self.charge_time  = 0
        self.target_pos   = (0, 0)

    def update(self, *args):
        if self.health < self.max_health * 0.5 and self.phase == 1:
            self.phase = 2
            self.speed = int(self.speed * 1.4)

        self.attack_cd -= 1

        if not self.charging:
            self.basic_movement()
            if self.attack_cd <= 0:
                choice = random.choice(["charge", "multishot"])
                if choice == "charge":
                    self.charging    = True
                    self.charge_time = 30
                    self.target_pos  = self.player.rect.center
                    self.attack_cd   = 150
                elif choice == "multishot" and self.phase >= 2:
                    count = 8 + self.wave * 2
                    for i in range(count):
                        rad = math.radians(i * 360 // count)
                        tx  = self.rect.centerx + math.cos(rad) * 600
                        ty  = self.rect.centery + math.sin(rad) * 600
                        b   = EnemyBullet(self.rect.centerx, self.rect.centery,
                                           tx, ty, speed=10, damage=self.damage,
                                           epoch_key=self.epoch_key)
                        self._eb_group.add(b)
                        self._all_sprites.add(b)
                    self.attack_cd = 100
        else:
            tx, ty = self.target_pos
            dx = tx - self.rect.centerx
            dy = ty - self.rect.centery
            dist = math.hypot(dx, dy) or 1
            charge_spd = 16
            self.rect.x += (dx / dist) * charge_spd
            self.rect.y += (dy / dist) * charge_spd
            self.charge_time -= 1
            if self.charge_time <= 0:
                self.charging = False

        self.handle_collision()


# ══════════════════════════════════════════════════════════════════════════════
#  SALLE DE BASE
# ══════════════════════════════════════════════════════════════════════════════

class BaseRoom:
    """
    Classe abstraite pour toutes les époques.
    Gère : boucle update, spawn, collisions, rendu.
    """

    WAVES_BEFORE_NEXT_EPOCH = 3   # 3 vagues (dont 1 boss) par époque

    def __init__(self, game, epoch_key: str):
        self.game      = game
        self.epoch_key = epoch_key
        epoch          = EPOCHS.get(epoch_key, {})
        self.weapons   = epoch.get("weapons", ["rock", "bone"])

        # ── Systèmes graphiques ──────────────────────────────────────────────
        self.bg_renderer   = BackgroundRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.hud           = HUDRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particles     = ParticleSystem()
        self.float_texts   = FloatingTextSystem()
        self.screen_fx     = ScreenEffects(SCREEN_WIDTH, SCREEN_HEIGHT)

        # ── Groupes de sprites ───────────────────────────────────────────────
        self.all_sprites   = pygame.sprite.Group()
        self.enemies       = pygame.sprite.Group()
        self.bullets       = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.melee_attacks = pygame.sprite.Group()
        self.chests        = pygame.sprite.Group()
        self.powerups      = pygame.sprite.Group()

        # ── État vague ───────────────────────────────────────────────────────
        self.wave              = 0
        self.wave_complete     = False
        self.boss_wave         = False
        self.boss_spawned      = False
        self.enemies_this_wave = 0
        self.enemies_spawned   = 0
        self.spawn_timer       = 0
        self.next_wave_timer   = 0
        self.show_chest_hint   = False

        self.player    = None
        self._running  = False

    # ── Démarrage ─────────────────────────────────────────────────────────────

    def start(self, skill_or_playerdata, player_stats=None):
        """Lance la salle. skill_or_playerdata peut être une string skill ou un dict stats."""
        # Vider les groupes
        for grp in [self.all_sprites, self.enemies, self.bullets,
                    self.enemy_bullets, self.melee_attacks, self.chests, self.powerups]:
            grp.empty()

        # Créer le joueur
        if isinstance(skill_or_playerdata, str):
            skill = skill_or_playerdata
            self.player = Player(skill)
        else:
            skill = skill_or_playerdata
            self.player = Player(skill)

        # Transférer les stats si continuation
        if player_stats:
            self.player.kills       = player_stats.get("kills", 0)
            self.player.coins       = player_stats.get("coins", 0)
            self.player.health      = player_stats.get("health", self.player.max_health)
            self.player.max_health  = player_stats.get("max_health", self.player.max_health)
            self.player.stamina     = player_stats.get("stamina", self.player.max_stamina)
            self.player.max_stamina = player_stats.get("max_stamina", self.player.max_stamina)

        # Injecter les groupes dans le joueur
        self.player._bullets       = self.bullets
        self.player._melee_attacks = self.melee_attacks
        self.player._all_sprites   = self.all_sprites

        # Donner les armes de l'époque
        for wk in self.weapons:
            self.player.add_weapon(wk)
        self.player.change_weapon(self.weapons[0])

        self.all_sprites.add(self.player)

        # Première vague
        self.wave = 0
        self._start_new_wave()
        self._running = True
        self.on_enter()

    # ── Hooks pour les sous-classes ──────────────────────────────────────────

    def on_enter(self):       pass
    def on_exit(self):        pass
    def draw_epoch_decoration(self, surface): pass

    # ── Vague ─────────────────────────────────────────────────────────────────

    def _start_new_wave(self):
        self.wave          += 1
        self.wave_complete  = False
        self.boss_spawned   = False
        self.spawn_timer    = 0

        # Vague 3 → boss
        if self.wave % 3 == 0:
            self.boss_wave         = True
            self.enemies_this_wave = 0
        else:
            self.boss_wave         = False
            self.enemies_this_wave = 8 + self.wave * 3
            self.enemies_spawned   = 0

    def _spawn_enemy(self):
        etype = random.choices(
            ["rusher", "tank", "sniper"],
            weights=[45, 25, 30]
        )[0]
        if etype == "tank":
            e = TankEnemy(self.player, self.epoch_key)
        elif etype == "sniper":
            e = SniperEnemy(self.player, self.epoch_key,
                            self.enemy_bullets, self.all_sprites)
        else:
            e = RusherEnemy(self.player, self.epoch_key)
        self.enemies.add(e)
        self.all_sprites.add(e)

    def _spawn_boss(self):
        b = BossEnemy(self.player, self.epoch_key, self.wave,
                      self.enemy_bullets, self.all_sprites)
        self.enemies.add(b)
        self.all_sprites.add(b)
        self.boss_spawned = True

    def _spawn_powerup(self, x, y):
        if random.random() < 0.35:
            ptype   = random.choice(["damage", "speed", "health", "stamina"])
            powerup = PowerUp(x, y, ptype)
            self.powerups.add(powerup)
            self.all_sprites.add(powerup)

    # ── Handle event (appelé par Game) ────────────────────────────────────────

    def handle_event(self, event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "MENU"
            # Changement d'arme
            for i, wk in enumerate(self.player.inventory):
                if event.key == pygame.K_1 + i:
                    self.player.change_weapon(wk)
            # Compétence
            if event.key == pygame.K_f:
                if self.player.use_skill() and self.player.skill == "mage":
                    self.particles.emit_magic(self.player.rect.centerx,
                                              self.player.rect.centery,
                                              color=TEAL, count=20)
            # Coffre
            if event.key == pygame.K_e:
                for chest in self.chests:
                    if chest.check_interaction(self.player.rect):
                        if chest.open(self.player):
                            self.float_texts.add(self.player.rect.centerx,
                                                  self.player.rect.top - 20,
                                                  f"+ {chest.weapon_inside}!", GOLD)
                            self.show_chest_hint = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            if self.player.attack(mx, my):
                # Particules selon type arme
                wtype = self.player.current_weapon.type
                if wtype == "melee":
                    self.particles.emit_hit_spark(mx, my, YELLOW, 5)
                elif self.player.current_weapon.key in ("magic_orb",):
                    self.particles.emit_magic(mx, my, TEAL, 6)

        return None

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self):
        if self.player.health <= 0:
            return True  # Game over

        keys = pygame.key.get_pressed()
        self.all_sprites.update(keys)
        self.screen_fx.update()
        self.particles.update()
        self.float_texts.update()

        self.spawn_timer += 1

        # Spawn ennemis
        if not self.wave_complete and not self.boss_wave:
            if self.spawn_timer >= 55 and self.enemies_spawned < self.enemies_this_wave:
                self._spawn_enemy()
                self.enemies_spawned += 1
                self.spawn_timer = 0

        if self.boss_wave and not self.boss_spawned:
            self._spawn_boss()

        # ── Collisions ───────────────────────────────────────────────────────

        # Projectiles joueur → ennemis
        hits = pygame.sprite.groupcollide(self.bullets, self.enemies, True, False)
        for bullet, hit_list in hits.items():
            for enemy in hit_list:
                dmg = bullet.damage
                enemy.health -= dmg
                self.float_texts.add_damage(enemy.rect.centerx, enemy.rect.top - 10, dmg)
                self.particles.emit_blood(enemy.rect.centerx, enemy.rect.centery)
                if enemy.health <= 0:
                    col = EPOCHS.get(self.epoch_key, {}).get("enemy_tint", RED)
                    self.particles.emit_death(enemy.rect.centerx, enemy.rect.centery, col)
                    self._spawn_powerup(enemy.rect.centerx, enemy.rect.centery)
                    self.player.add_kill()
                    enemy.kill()

        # Corps à corps → ennemis
        for melee in self.melee_attacks:
            for enemy in pygame.sprite.spritecollide(melee, self.enemies, False):
                if enemy not in melee.hit_enemies:
                    melee.hit_enemies.add(enemy)
                    dmg = melee.damage
                    enemy.health -= dmg
                    self.float_texts.add_damage(enemy.rect.centerx, enemy.rect.top - 10, dmg)
                    self.screen_fx.shake(4, 8)
                    if enemy.health <= 0:
                        col = EPOCHS.get(self.epoch_key, {}).get("enemy_tint", RED)
                        self.particles.emit_death(enemy.rect.centerx, enemy.rect.centery, col)
                        self._spawn_powerup(enemy.rect.centerx, enemy.rect.centery)
                        self.player.add_kill()
                        enemy.kill()

        # Balles ennemies → joueur
        hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        for b in hits:
            self.player.take_damage(b.damage)
            self.float_texts.add_damage(self.player.rect.centerx,
                                        self.player.rect.top - 20, int(b.damage))
            self.particles.emit_hit_spark(self.player.rect.centerx,
                                           self.player.rect.centery, RED, 6)
            self.screen_fx.flash(RED, 7)
            self.screen_fx.shake(6, 10)

        # Powerups → joueur
        for pu in pygame.sprite.spritecollide(self.player, self.powerups, True):
            self.player.apply_powerup(pu.type)
            label = {"damage": "+DMG", "speed": "+SPD",
                     "health": "+HP",  "stamina": "+STA"}.get(pu.type, "?")
            col   = {"damage": RED, "speed": CYAN,
                     "health": (60, 220, 80), "stamina": BLUE}.get(pu.type, WHITE)
            self.float_texts.add(self.player.rect.centerx, self.player.rect.top - 30,
                                  label, col, 22)

        # Fin de vague
        if not self.wave_complete:
            cond = (len(self.enemies) == 0 and
                    (self.boss_wave or self.enemies_spawned >= self.enemies_this_wave))
            if cond:
                self.wave_complete = True
                self.next_wave_timer = 0
                self.player.coins  += 5
                if self.boss_wave:
                    chest_wk = self.weapons[1] if len(self.weapons) > 1 else self.weapons[0]
                    chest = Chest(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, chest_wk)
                    self.chests.add(chest)
                    self.all_sprites.add(chest)
                    self.player.coins += 10
                    self.on_exit()
        else:
            self.next_wave_timer += 1
            # Indication coffre
            self.show_chest_hint = any(
                c.check_interaction(self.player.rect) and not c.opened
                for c in self.chests
            )
            # Passage époque ou nouvelle vague
            if self.next_wave_timer >= 220:
                # Vague de boss = fin d'époque
                if self.boss_wave:
                    next_epoch = EPOCHS.get(self.epoch_key, {}).get("next", None)
                    return f"NEXT_EPOCH:{next_epoch}" if next_epoch else "NEXT_EPOCH:None"
                self._start_new_wave()

        return None

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface):
        ox, oy = self.screen_fx.offset

        # Background
        bg = self.bg_renderer.get(self.epoch_key)
        surface.blit(bg, (ox, oy))

        # Sprites (avec offset shake)
        for sprite in self.all_sprites:
            surface.blit(sprite.image,
                         (sprite.rect.x + ox, sprite.rect.y + oy))

        # Arme dans la main
        if self.player:
            pr = self.player.rect.move(ox, oy)
            draw_weapon_in_hand(surface, pr,
                                 self.player.current_weapon,
                                 self.player.facing_right)

        # Barres de vie ennemis
        for enemy in self.enemies:
            r = enemy.rect.move(ox, oy)
            draw_enemy_health_bar(surface, r, enemy.health, enemy.max_health,
                                   EPOCHS.get(self.epoch_key, {}).get("color", RED),
                                   is_boss=(enemy.enemy_type == "boss"),
                                   screen_w=SCREEN_WIDTH)

        # Particules & textes flottants
        self.particles.draw(surface)
        self.float_texts.draw(surface)

        # Flash screen
        self.screen_fx.draw_flash(surface)

        # HUD
        self.hud.draw(
            surface, self.player, self.epoch_key,
            self.wave, self.wave_complete, self.boss_wave,
            enemies_left=len(self.enemies)
        )

        # Décorations époque (hook)
        self.draw_epoch_decoration(surface)

        # Hint coffre
        if self.show_chest_hint:
            font = pygame.font.Font(None, 32)
            hint = font.render("E : Ouvrir le coffre", True, GOLD)
            hr   = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
            bg_s = pygame.Surface((hr.w + 20, hr.h + 10), pygame.SRCALPHA)
            bg_s.fill((0, 0, 0, 160))
            surface.blit(bg_s, (hr.x - 10, hr.y - 5))
            surface.blit(hint, hr)

        # Touches armes
        if len(self.player.inventory) > 1:
            font = pygame.font.Font(None, 22)
            hint = font.render("1/2 : Changer arme  |  F : Compétence  |  ESC : Menu",
                                True, LIGHT_GRAY)
            surface.blit(hint, (10, SCREEN_HEIGHT - 28))
