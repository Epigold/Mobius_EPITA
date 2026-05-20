# -*- coding: utf-8 -*-
# core/base_room.py - Salle de base + joueur + ennemis + support réseau multijoueur
# (voir commentaires détaillés dans network.py pour l'architecture réseau)

import pygame, math, random
from .constants  import *
from .graphics   import (SpriteCache, BackgroundRenderer, HUDRenderer,
                          ParticleSystem, FloatingTextSystem, ScreenEffects,
                          draw_weapon_in_hand, draw_enemy_health_bar, tint_surface)
from .mechanics  import Weapon, Bullet, MeleeAttack, EnemyBullet, PowerUp, Chest

# ══════════════════════════════════════════════════════════════════════════════
#  JOUEUR
# ══════════════════════════════════════════════════════════════════════════════
class Player(pygame.sprite.Sprite):
    """
    Représente un joueur (P1 local ou P2 réseau côté serveur).

    En mode réseau côté serveur, P2 est une instance de Player dont
    le déplacement est piloté par apply_network_inputs() + update_as_p2_server()
    au lieu du clavier local.

    MÉTHODES RÉSEAU :
      apply_network_inputs(inputs, chests, float_texts, particles)
        → Pose les flags internes depuis le dict inputs reçu du client
      update_as_p2_server()
        → Appelle _handle_move_network() au lieu de _handle_move(keys)
    """
    ANIM_FRAMES = {
        "idle": ["char_idle_one_arm"],
        "walk": ["char_walk_one_arm"],
        "run":  ["char_run1_one_arm","char_run2_one_arm","char_run3_one_arm"],
    }
    SIZE = 80

    def __init__(self, skill=None, start_pos=None):
        super().__init__()
        self.skill = skill

        # ── Stats de base ────────────────────────────────────────────────────
        self.max_health = 100; self.health = 100
        self.max_stamina = 100; self.stamina = 100
        self.stamina_regen = 0.25
        self.speed = 7
        self.kills = 0; self.coins = 0

        # ── Buffs de classe ───────────────────────────────────────────────────
        if skill == "tank":     self.max_health = self.health = 150; self.speed = 5
        elif skill == "berserker": self.max_health = self.health = 80; self.speed = 9
        elif skill == "mage":   self.max_stamina = self.stamina = 150; self.stamina_regen = 0.35

        # ── Dash ──────────────────────────────────────────────────────────────
        self.dashing = False; self.dash_time = 0; self.dash_cooldown = 0
        self._dash_cd_max = DASH_COOLDOWN // 2 if skill == "ninja" else DASH_COOLDOWN
        self.dir_x = self.dir_y = 0
        self.facing_right = True

        # ── Compétence ────────────────────────────────────────────────────────
        self.skill_cooldown = 0; self.skill_active = False; self.skill_duration = 0

        # ── Boosts power-up ───────────────────────────────────────────────────
        self.damage_boost = 1.0; self.speed_boost = 1.0; self.boost_timer = 0

        # ── Armes ─────────────────────────────────────────────────────────────
        self.inventory = ["rock"]; self.current_weapon = Weapon("rock")

        # ── Animation ─────────────────────────────────────────────────────────
        self._anim_cache = {}; self._anim_state = "idle"
        self._anim_frame = 0; self._anim_timer = 0; self._anim_speed = 8
        self._moving = False
        self._visual_bob = 0.0
        self._visual_tilt = 0.0
        self._stride_phase = 0.0
        self._load_sprites()
        self.image = self._get_frame()
        self.rect  = self.image.get_rect()
        self.rect.center = start_pos if start_pos else (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
        self.hitbox = pygame.Rect(0,0,self.SIZE*0.4,self.SIZE*0.4)
        self.hitbox.center = self.rect.center

        # Groupes de sprites (injectés par BaseRoom.start())
        self._bullets = None; self._melee_attacks = None; self._all_sprites = None

        # ── Flags réseau (utilisés uniquement pour P2 côté serveur) ──────────
        # Ces flags sont posés par apply_network_inputs() et consommés dans
        # _handle_move_network() → évite de traiter deux fois la même action
        self._net_dash    = False   # Dash demandé par le client ce frame
        self._net_skill   = False   # Skill demandée par le client ce frame
        self._net_fire    = False   # Tir demandé par le client ce frame
        self._net_fire_tx = 0       # Coordonnée X cible du tir
        self._net_fire_ty = 0       # Coordonnée Y cible du tir
        self._net_chest   = False   # Interaction coffre demandée
        self._network_controlled = False

    # ── Sprites ───────────────────────────────────────────────────────────────
    def _load_sprites(self):
        cache = SpriteCache.get()
        for state, names in self.ANIM_FRAMES.items():
            frames = []
            for name in names:
                img = cache.load("sprites_final", f"{name}.png", size=(self.SIZE,self.SIZE))
                frames.append(img)
            self._anim_cache[state] = frames

    def _get_frame(self):
        frames = self._anim_cache.get(self._anim_state, self._anim_cache["idle"])
        idx = min(self._anim_frame, len(frames)-1)
        img = frames[idx]
        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)
        return img

    # ── Update standard (P1 local) ────────────────────────────────────────────
    def update(self, keys):
        """Mise à jour standard du joueur local P1 (clavier+souris)."""
        self._update_stamina(); self._update_timers()
        self._handle_move(keys); self._update_anim()
        self.current_weapon.update_cooldown()

    # ── Update réseau (P2 côté serveur) ──────────────────────────────────────
    def update_as_p2_server(self):
        """
        Variante de update() pour P2 côté serveur.
        Lit les flags posés par apply_network_inputs() au lieu du clavier local.
        À appeler APRÈS apply_network_inputs().
        """
        self._update_stamina(); self._update_timers()
        self._handle_move_network(); self._update_anim()
        self.current_weapon.update_cooldown()
        # Réinitialiser les flags à usage unique
        self._net_dash = self._net_skill = self._net_fire = self._net_chest = False

    def apply_network_inputs(self, inputs: dict, chests=None,
                              float_texts=None, particles=None):
        """
        Applique les inputs réseau du client P2 sur ce joueur (côté serveur).
        Pose les flags internes qui seront lus dans update_as_p2_server().

        inputs : dict {"dx":float, "dy":float, "dash":bool, "skill":bool,
                        "fire":bool, "fire_tx":int, "fire_ty":int,
                        "chest":bool, "weapon_idx":int}
        """
        if not inputs:
            return  # Paquet perdu ce frame — garder l'ancienne direction

        # Mouvement : mise à jour de la direction normalisée
        dx = float(inputs.get('dx', 0.0))
        dy = float(inputs.get('dy', 0.0))
        if dx or dy:
            dist = math.hypot(dx, dy) or 1
            self.dir_x = dx / dist
            self.dir_y = dy / dist
            self.facing_right = dx >= 0   # Orient selon la direction de déplacement
        else:
            self.dir_x = 0
            self.dir_y = 0

        # Actions discrètes → flags consommés dans _handle_move_network()
        if inputs.get('dash'):  self._net_dash  = True
        if inputs.get('skill'): self._net_skill = True
        if inputs.get('fire') and not self._net_fire:
            self._net_fire = True
            self._net_fire_tx = int(inputs.get('fire_tx', self.rect.centerx + 100))
            self._net_fire_ty = int(inputs.get('fire_ty', self.rect.centery))

        # Interaction coffre (événement discret, exécuté immédiatement)
        if inputs.get('chest') and not self._net_chest:
            self._net_chest = True
            if chests:
                for chest in chests:
                    if chest.check_interaction(self.rect):
                        if chest.open(self):
                            if float_texts:
                                float_texts.add(self.rect.centerx, self.rect.top-20,
                                                f"+ {chest.weapon_inside}!", GOLD)
                            break

        # Changement d'arme (événement discret)
        widx = int(inputs.get('weapon_idx', -1))
        if 0 <= widx < len(self.inventory):
            self.change_weapon(self.inventory[widx])

    # ── Déplacement réseau (P2 serveur) ──────────────────────────────────────
    def _handle_move_network(self):
        """Déplace P2 selon les flags réseau (pas le clavier)."""
        if self.dashing:
            self._moving = True
            self.rect.x += self.dir_x * DASH_SPEED
            self.rect.y += self.dir_y * DASH_SPEED
            self.dash_time -= 1
            if self.dash_time <= 0: self.dashing = False
        else:
            moving = (self.dir_x != 0 or self.dir_y != 0)
            self._moving = moving
            eff = self.speed * self.speed_boost
            if moving:
                self.rect.x += self.dir_x * eff
                self.rect.y += self.dir_y * eff
            self._anim_state = "run" if moving else "idle"

            if self._net_dash and self.dash_cooldown == 0 and self.stamina >= DASH_STAMINA_COST:
                self.dashing = True; self.dash_time = DASH_TIME
                self.dash_cooldown = self._dash_cd_max; self.stamina -= DASH_STAMINA_COST
            if self._net_skill: self.use_skill()
            if self._net_fire:  self.attack(self._net_fire_tx, self._net_fire_ty)

        self.rect.clamp_ip(pygame.Rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT))
        self.hitbox.center = self.rect.center

    # ── Déplacement local (P1) ────────────────────────────────────────────────
    def _handle_move(self, keys):
        """Déplacement de P1 via clavier ZQSD/WASD + ESPACE pour dash."""
        mx, _ = pygame.mouse.get_pos()
        self.facing_right = mx >= self.rect.centerx

        if self.dashing:
            self._moving = True
            self.rect.x += self.dir_x * DASH_SPEED
            self.rect.y += self.dir_y * DASH_SPEED
            self.dash_time -= 1
            if self.dash_time <= 0: self.dashing = False
        else:
            dx = dy = 0
            if keys[pygame.K_d]: dx += 1
            if keys[pygame.K_q] or keys[pygame.K_a]: dx -= 1
            if keys[pygame.K_s]: dy += 1
            if keys[pygame.K_z] or keys[pygame.K_w]: dy -= 1
            if dx or dy:
                norm = math.hypot(dx,dy) or 1
                self.dir_x, self.dir_y = dx/norm, dy/norm
            else:
                self.dir_x = 0
                self.dir_y = 0
            self._moving = bool(dx or dy)
            eff = self.speed * self.speed_boost
            self.rect.x += self.dir_x*eff if (dx or dy) else 0
            self.rect.y += self.dir_y*eff if (dx or dy) else 0
            self._anim_state = "run" if (dx or dy) else "idle"
            if keys[pygame.K_SPACE] and self.dash_cooldown==0 and self.stamina>=DASH_STAMINA_COST:
                self.dashing=True; self.dash_time=DASH_TIME
                self.dash_cooldown=self._dash_cd_max; self.stamina-=DASH_STAMINA_COST

        self.rect.clamp_ip(pygame.Rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT))
        self.hitbox.center = self.rect.center

    def _update_stamina(self):
        if self.stamina < self.max_stamina:
            self.stamina = min(self.stamina + self.stamina_regen, self.max_stamina)

    def _update_timers(self):
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if self.skill_cooldown > 0: self.skill_cooldown -= 1
        if self.skill_duration > 0:
            self.skill_duration -= 1
            if self.skill_duration == 0: self.skill_active = False
        if self.boost_timer > 0:
            self.boost_timer -= 1
            if self.boost_timer == 0: self.damage_boost = self.speed_boost = 1.0

    def _update_anim(self):
        move_strength = math.hypot(self.dir_x, self.dir_y) if self._moving else 0.0
        if self.dashing:
            move_strength = 1.35
        if self._moving:
            self._stride_phase += 0.28 * max(0.8, move_strength)
            self._visual_bob = math.sin(self._stride_phase) * (4.0 if self.dashing else 2.4)
            target_tilt = max(-9.0, min(9.0, self.dir_x * (10.0 if self.dashing else 6.0)))
            self._visual_tilt += (target_tilt - self._visual_tilt) * 0.35
        else:
            self._stride_phase += 0.06
            self._visual_bob *= 0.72
            self._visual_tilt *= 0.68
        self._anim_timer += 1
        self._anim_speed = 5 if self.dashing else (6 if self._moving else 12)
        if self._anim_timer >= self._anim_speed:
            self._anim_timer = 0
            frames = self._anim_cache.get(self._anim_state, self._anim_cache["idle"])
            self._anim_frame = (self._anim_frame+1) % len(frames)
        self.image = self._get_frame()

    # ── Attaque ───────────────────────────────────────────────────────────────
    def attack(self, mx, my) -> bool:
        """Lance une attaque (ranged→Bullet, melee→MeleeAttack). Retourne True si réussi."""
        if not self.current_weapon.can_use(self.stamina): return False
        self.stamina -= self.current_weapon.stamina_cost
        self.current_weapon.use()
        dmult = self.damage_boost
        if self.current_weapon.type == "ranged":
            b = Bullet(self.rect.centerx,self.rect.centery,mx,my,self.current_weapon,dmult,owner=self)
            if self._bullets is not None:     self._bullets.add(b)
            if self._all_sprites is not None: self._all_sprites.add(b)
        else:
            m = MeleeAttack(self.rect.centerx,self.rect.centery,mx,my,self.current_weapon,dmult,owner=self)
            if self._melee_attacks is not None: self._melee_attacks.add(m)
            if self._all_sprites is not None:   self._all_sprites.add(m)
        return True

    # ── Compétence ────────────────────────────────────────────────────────────
    def use_skill(self) -> bool:
        """Active la compétence de classe. Fonctionne identiquement pour P1 et P2."""
        if self.skill_cooldown > 0 or not self.skill: return False
        if self.skill == "tank":
            self.skill_active=True; self.skill_duration=300; self.skill_cooldown=1800
        elif self.skill == "berserker":
            self.damage_boost=2.0; self.boost_timer=300; self.skill_cooldown=1200
        elif self.skill == "vampire":
            self.skill_active=True; self.skill_duration=600; self.skill_cooldown=900
        elif self.skill == "ninja":
            # P1 : téléportation souris · P2 réseau : téléportation en avant
            if self._network_controlled:
                dist = 180
                dx = self.dir_x if self.dir_x != 0 else (1 if self.facing_right else -1)
                dy = self.dir_y
                mx = self.rect.centerx + dx * dist
                my = self.rect.centery + dy * dist
            else:
                mx,my = pygame.mouse.get_pos()
            self.rect.center=(mx,my); self.hitbox.center=self.rect.center
            self.rect.clamp_ip(pygame.Rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT))
            self.hitbox.center=self.rect.center
            self.skill_cooldown=600
        elif self.skill == "mage" and self._bullets is not None and self._all_sprites is not None:
            for deg in range(0,360,30):
                rad=math.radians(deg)
                tx=self.rect.centerx+math.cos(rad)*500; ty=self.rect.centery+math.sin(rad)*500
                b=Bullet(self.rect.centerx,self.rect.centery,tx,ty,self.current_weapon,1.5,owner=self)
                self._bullets.add(b); self._all_sprites.add(b)
            self.skill_cooldown=1200
        return True

    def change_weapon(self, key):
        if key in self.inventory: self.current_weapon = Weapon(key)
    def add_weapon(self, key):
        if key not in self.inventory: self.inventory.append(key)

    def take_damage(self, amount):
        if self.dashing: return
        if self.skill=="tank" and self.skill_active: amount *= 0.5
        self.health = max(0, self.health - amount)

    def add_kill(self):
        self.kills += 1
        if random.random() < 0.3: self.coins += 1
        if self.skill=="vampire" and self.skill_active:
            self.health = min(self.health+10, self.max_health)

    def apply_powerup(self, ptype):
        if ptype=="damage":  self.damage_boost=1.5; self.boost_timer=600
        elif ptype=="speed": self.speed_boost=1.5;  self.boost_timer=600
        elif ptype=="health": self.health=min(self.health+30, self.max_health)
        elif ptype=="stamina": self.max_stamina+=10; self.stamina=self.max_stamina


# ══════════════════════════════════════════════════════════════════════════════
#  ENNEMIS
# ══════════════════════════════════════════════════════════════════════════════
class Enemy(pygame.sprite.Sprite):
    """
    Ennemi de base. En mode réseau serveur, player peut être [p1, p2].
    L'ennemi cible alors le joueur vivant le plus proche chaque frame.
    """
    def __init__(self, player, epoch_key, enemy_type="rusher", sprite_path=None):
        super().__init__()
        self._players   = player if isinstance(player, list) else [player]
        self.player     = self._players[0]
        self.epoch_key  = epoch_key
        self.enemy_type = enemy_type
        cfg  = ENEMY_CONFIG.get(epoch_key, ENEMY_CONFIG["prehistoire"])[enemy_type]
        diff = EPOCHS.get(epoch_key,{}).get("difficulty",1.0)
        self.speed=cfg["speed"]; self.max_health=int(cfg["health"]*diff)
        self.health=self.max_health; self.damage=int(cfg["damage"]*diff); self.size=cfg["size"]
        self.damage_cooldown=0; self.shoot_cooldown=0
        epoch_color=EPOCHS.get(epoch_key,{}).get("enemy_tint",(180,80,80))
        self._build_sprite(sprite_path, epoch_color)
        self._spawn_on_edge()

    def _get_nearest_player(self):
        """Retourne le joueur vivant le plus proche (crucial en multijoueur)."""
        alive=[p for p in self._players if p.health > 0]
        if not alive: return self._players[0]
        return min(alive, key=lambda p: math.hypot(
            p.rect.centerx-self.rect.centerx, p.rect.centery-self.rect.centery))

    def _build_sprite(self, sprite_path, tint_color):
        if sprite_path:
            try:
                cache=SpriteCache.get(); img=cache.load(*sprite_path,size=(self.size,self.size))
                self.base_image=img; self.image=img.copy(); self.rect=self.image.get_rect(); return
            except Exception: pass
        self.base_image=self._draw_procedural(tint_color)
        self.image=self.base_image.copy(); self.rect=self.image.get_rect()

    def _draw_procedural(self, color):
        s=self.size; surf=pygame.Surface((s,s),pygame.SRCALPHA); r,g,b=color[:3]
        if self.enemy_type=="tank":
            pygame.draw.ellipse(surf,(r,g,b),(2,10,s-4,s-12))
            pygame.draw.ellipse(surf,(min(255,r+40),min(255,g+40),min(255,b+40)),(6,14,s-12,s-20))
            pygame.draw.circle(surf,(r,g,b),(s//2,s//4),s//5)
            pygame.draw.circle(surf,RED,(s//2-5,s//4),4); pygame.draw.circle(surf,RED,(s//2+5,s//4),4)
            pygame.draw.ellipse(surf,WHITE,(2,10,s-4,s-12),2)
        elif self.enemy_type=="rusher":
            pygame.draw.ellipse(surf,(r,g,b),(6,8,s-12,s-10))
            pygame.draw.circle(surf,(min(255,r+30),g,b),(s//2,s//5),s//6)
            pygame.draw.circle(surf,YELLOW,(s//2-4,s//5),3); pygame.draw.circle(surf,YELLOW,(s//2+4,s//5),3)
            for lx in [s//4,s*3//4]:
                pygame.draw.line(surf,(min(255,r+80),min(255,g+80),b),(lx,s//2),(lx-8,s*3//4),2)
        elif self.enemy_type=="sniper":
            pygame.draw.polygon(surf,(r,g,b),[(s//2,4),(s-6,s-6),(6,s-6)])
            pygame.draw.circle(surf,(min(255,r+50),min(255,g+50),min(255,b+50)),(s//2,s//3),s//6)
            cx,cy=s//2,s//3
            pygame.draw.circle(surf,WHITE,(cx,cy),s//6,1)
            pygame.draw.line(surf,WHITE,(cx-s//4,cy),(cx+s//4,cy),1)
            pygame.draw.line(surf,WHITE,(cx,cy-s//4),(cx,cy+s//4),1)
        elif self.enemy_type=="boss":
            pygame.draw.ellipse(surf,(r//2,g//2,b//2),(0,0,s,s)); pygame.draw.ellipse(surf,(r,g,b),(4,4,s-8,s-8))
            for i in range(8):
                angle=math.radians(i*45); px2=int(s//2+math.cos(angle)*(s//2-2)); py2=int(s//2+math.sin(angle)*(s//2-2))
                pygame.draw.circle(surf,(min(255,r+60),min(255,g+40),b),(px2,py2),5)
            pygame.draw.circle(surf,(255,0,0),(s//3,s//3),8); pygame.draw.circle(surf,(255,0,0),(s*2//3,s//3),8)
            pygame.draw.circle(surf,(255,150,150),(s//3,s//3),4); pygame.draw.circle(surf,(255,150,150),(s*2//3,s//3),4)
            pygame.draw.ellipse(surf,WHITE,(0,0,s,s),3)
        return surf

    def _spawn_on_edge(self):
        edge=random.choice(["top","bottom","left","right"])
        if edge=="top":      self.rect.centerx=random.randint(50,SCREEN_WIDTH-50);  self.rect.top=-self.size
        elif edge=="bottom": self.rect.centerx=random.randint(50,SCREEN_WIDTH-50);  self.rect.bottom=SCREEN_HEIGHT+self.size
        elif edge=="left":   self.rect.left=-self.size;   self.rect.centery=random.randint(50,SCREEN_HEIGHT-50)
        else:                self.rect.right=SCREEN_WIDTH+self.size; self.rect.centery=random.randint(50,SCREEN_HEIGHT-50)

    def basic_movement(self):
        dx=self.player.rect.x-self.rect.x; dy=self.player.rect.y-self.rect.y
        dist=math.hypot(dx,dy) or 1
        self.rect.x+=(dx/dist)*self.speed; self.rect.y+=(dy/dist)*self.speed

    def handle_collision(self):
        if self.damage_cooldown > 0: self.damage_cooldown -= 1; return
        if self.rect.colliderect(self.player.hitbox):
            self.player.take_damage(self.damage); self.damage_cooldown=30

    def update(self, *args):
        self.player=self._get_nearest_player(); self.basic_movement(); self.handle_collision()

    def draw_health_bar(self, surface):
        draw_enemy_health_bar(surface,self.rect,self.health,self.max_health,
                               EPOCHS.get(self.epoch_key,{}).get("color",RED),
                               is_boss=(self.enemy_type=="boss"),screen_w=SCREEN_WIDTH)

class TankEnemy(Enemy):
    def __init__(self,player,epoch_key): super().__init__(player,epoch_key,"tank"); self._hit_flash=0
    def update(self,*args):
        self.player=self._get_nearest_player(); self.basic_movement(); self.handle_collision()
        if self._hit_flash>0: self._hit_flash-=1

class RusherEnemy(Enemy):
    def __init__(self,player,epoch_key): super().__init__(player,epoch_key,"rusher")

class SniperEnemy(Enemy):
    def __init__(self,player,epoch_key,enemy_bullets_group,all_sprites_group):
        super().__init__(player,epoch_key,"sniper")
        self._eb_group=enemy_bullets_group; self._all_sprites=all_sprites_group
        self.shoot_delay=90; self.shoot_range=500
    def update(self,*args):
        self.player=self._get_nearest_player()
        dx=self.player.rect.x-self.rect.x; dy=self.player.rect.y-self.rect.y
        dist=math.hypot(dx,dy) or 1
        if dist>self.shoot_range: self.basic_movement()
        elif dist<self.shoot_range-60:
            self.rect.x-=(dx/dist)*self.speed; self.rect.y-=(dy/dist)*self.speed
        self.shoot_cooldown-=1
        if self.shoot_cooldown<=0 and dist<=self.shoot_range:
            b=EnemyBullet(self.rect.centerx,self.rect.centery,
                           self.player.rect.centerx,self.player.rect.centery,
                           speed=9,damage=self.damage,epoch_key=self.epoch_key)
            self._eb_group.add(b); self._all_sprites.add(b); self.shoot_cooldown=self.shoot_delay
        self.handle_collision()

class BossEnemy(Enemy):
    def __init__(self,player,epoch_key,wave,enemy_bullets_group,all_sprites_group):
        super().__init__(player,epoch_key,"boss")
        cfg=ENEMY_CONFIG.get(epoch_key,ENEMY_CONFIG["prehistoire"])["boss"]
        diff=EPOCHS.get(epoch_key,{}).get("difficulty",1.0)
        self.max_health=int(cfg["health"]*diff+wave*200); self.health=self.max_health
        self._eb_group=enemy_bullets_group; self._all_sprites=all_sprites_group
        self.wave=wave; self.phase=1; self.attack_cd=0
        self.charging=False; self.charge_time=0; self.target_pos=(0,0)
    def update(self,*args):
        self.player=self._get_nearest_player()
        if self.health<self.max_health*0.5 and self.phase==1:
            self.phase=2; self.speed=int(self.speed*1.4)
        self.attack_cd-=1
        if not self.charging:
            self.basic_movement()
            if self.attack_cd<=0:
                choice=random.choice(["charge","multishot"])
                if choice=="charge":
                    self.charging=True; self.charge_time=30
                    self.target_pos=self.player.rect.center; self.attack_cd=150
                elif choice=="multishot" and self.phase>=2:
                    count=8+self.wave*2
                    for i in range(count):
                        rad=math.radians(i*360//count)
                        tx=self.rect.centerx+math.cos(rad)*600; ty=self.rect.centery+math.sin(rad)*600
                        b=EnemyBullet(self.rect.centerx,self.rect.centery,tx,ty,
                                       speed=10,damage=self.damage,epoch_key=self.epoch_key)
                        self._eb_group.add(b); self._all_sprites.add(b)
                    self.attack_cd=100
        else:
            tx,ty=self.target_pos; dx=tx-self.rect.centerx; dy=ty-self.rect.centery
            dist=math.hypot(dx,dy) or 1
            self.rect.x+=(dx/dist)*16; self.rect.y+=(dy/dist)*16
            self.charge_time-=1
            if self.charge_time<=0: self.charging=False
        self.handle_collision()


# ══════════════════════════════════════════════════════════════════════════════
#  SALLE DE BASE
# ══════════════════════════════════════════════════════════════════════════════
class BaseRoom:
    """
    Classe commune à toutes les salles (époques).

    MODES :
      mode="solo"   → Partie solo classique (un seul joueur local)
      mode="server" → Host multijoueur en ligne :
                        P1 = joueur local, P2 = contrôlé via réseau
                        Appeler apply_p2_network_inputs() puis update() puis serialize_state()

    API RÉSEAU (mode="server") :
      room.apply_p2_network_inputs(inputs)  # Avant update()
      room.update()                          # Simulation
      state = room.serialize_state()        # Après update(), à envoyer au client
    """
    WAVES_BEFORE_NEXT_EPOCH = 3

    def __init__(self, game, epoch_key):
        self.game=game; self.epoch_key=epoch_key
        epoch=EPOCHS.get(epoch_key,{})
        self.weapons=epoch.get("weapons",["rock","bone"])

        self.bg_renderer=BackgroundRenderer(SCREEN_WIDTH,SCREEN_HEIGHT)
        self.hud=HUDRenderer(SCREEN_WIDTH,SCREEN_HEIGHT)
        self.particles=ParticleSystem(); self.float_texts=FloatingTextSystem()
        self.screen_fx=ScreenEffects(SCREEN_WIDTH,SCREEN_HEIGHT)

        self.all_sprites=pygame.sprite.Group(); self.enemies=pygame.sprite.Group()
        self.bullets=pygame.sprite.Group(); self.enemy_bullets=pygame.sprite.Group()
        self.melee_attacks=pygame.sprite.Group(); self.chests=pygame.sprite.Group()
        self.powerups=pygame.sprite.Group()

        self.wave=0; self.wave_complete=False; self.boss_wave=False
        self.boss_spawned=False; self.enemies_this_wave=0; self.enemies_spawned=0
        self.spawn_timer=0; self.next_wave_timer=0; self.show_chest_hint=False
        self._network_game_over=False; self._network_next_epoch=None
        self._boss_chest_opened=False
        self.objective_hint=""

        self.player=None; self.player2=None
        self.mode="solo"; self._running=False

    # ── Démarrage ─────────────────────────────────────────────────────────────
    def start(self, skill, player_stats=None, mode="solo", skill2=None, player2_stats=None):
        """
        Initialise la salle.
        skill        : str  → classe P1
        player_stats : dict → stats P1 à restaurer (transition d'époque)
        mode         : str  → "solo" | "server"
        skill2       : str  → classe P2 (None en solo)
        player2_stats: dict → stats P2 à restaurer
        """
        self.mode=mode
        self._network_game_over=False
        self._network_next_epoch=None
        self._boss_chest_opened=False
        self.objective_hint=""
        for grp in [self.all_sprites,self.enemies,self.bullets,
                    self.enemy_bullets,self.melee_attacks,self.chests,self.powerups]:
            grp.empty()

        # Créer P1
        p1_pos=(SCREEN_WIDTH//3,SCREEN_HEIGHT//2) if skill2 else (SCREEN_WIDTH//2,SCREEN_HEIGHT//2)
        self.player=Player(skill,start_pos=p1_pos)
        if player_stats: self._restore_stats(self.player,player_stats)
        self.player._bullets=self.bullets; self.player._melee_attacks=self.melee_attacks
        self.player._all_sprites=self.all_sprites
        for wk in self.weapons: self.player.add_weapon(wk)
        self.player.change_weapon(self.weapons[0])
        self.all_sprites.add(self.player)

        # Créer P2 (mode server seulement)
        self.player2=None
        if mode=="server" and skill2:
            p2_pos=(SCREEN_WIDTH*2//3,SCREEN_HEIGHT//2)
            self.player2=Player(skill2,start_pos=p2_pos)
            self.player2._network_controlled = True
            if player2_stats: self._restore_stats(self.player2,player2_stats)
            self.player2._bullets=self.bullets; self.player2._melee_attacks=self.melee_attacks
            self.player2._all_sprites=self.all_sprites
            for wk in self.weapons: self.player2.add_weapon(wk)
            self.player2.change_weapon(self.weapons[0])
            self.all_sprites.add(self.player2)

        self.wave=0; self._start_new_wave(); self._running=True; self.on_enter()

    def _restore_stats(self, player, stats):
        """Restaure les stats d'un joueur depuis un dict (transition d'époque)."""
        player.kills=stats.get("kills",0); player.coins=stats.get("coins",0)
        player.health=stats.get("health",player.max_health)
        player.max_health=stats.get("max_health",player.max_health)
        player.stamina=stats.get("stamina",player.max_stamina)
        player.max_stamina=stats.get("max_stamina",player.max_stamina)

    def on_enter(self): pass
    def on_exit(self):  pass
    def draw_epoch_decoration(self, surface): pass

    # ── Vagues ────────────────────────────────────────────────────────────────
    def _start_new_wave(self):
        """Démarre une nouvelle vague. En mode server, +20% d'ennemis pour le challenge."""
        self.wave+=1; self.wave_complete=False; self.boss_spawned=False; self.spawn_timer=0
        if self.wave%3==0:
            self.boss_wave=True; self.enemies_this_wave=0
        else:
            self.boss_wave=False
            base=8+self.wave*3
            if self.mode=="server" and self.player2: base=int(base*1.2)
            self.enemies_this_wave=base; self.enemies_spawned=0

    def _spawn_enemy(self):
        """Crée un ennemi. En mode server, les ennemis ciblent le joueur le plus proche."""
        etype=random.choices(["rusher","tank","sniper"],weights=[45,25,30])[0]
        target=[self.player,self.player2] if (self.mode=="server" and self.player2) else self.player
        if etype=="tank":    e=TankEnemy(target,self.epoch_key)
        elif etype=="sniper": e=SniperEnemy(target,self.epoch_key,self.enemy_bullets,self.all_sprites)
        else:                 e=RusherEnemy(target,self.epoch_key)
        self.enemies.add(e); self.all_sprites.add(e)

    def _spawn_boss(self):
        target=[self.player,self.player2] if (self.mode=="server" and self.player2) else self.player
        b=BossEnemy(target,self.epoch_key,self.wave,self.enemy_bullets,self.all_sprites)
        self.enemies.add(b); self.all_sprites.add(b); self.boss_spawned=True

    def _spawn_powerup(self, x, y):
        if random.random()<0.35:
            ptype=random.choice(["damage","speed","health","stamina"])
            pu=PowerUp(x,y,ptype); self.powerups.add(pu); self.all_sprites.add(pu)

    # ── API réseau ────────────────────────────────────────────────────────────
    def apply_p2_network_inputs(self, inputs: dict):
        """
        Applique les inputs réseau du client sur P2 côté serveur.
        À appeler AVANT update() dans la boucle serveur.
        Ne fait rien si mode!="server" ou player2 is None.
        """
        if self.mode!="server" or not self.player2: return
        self.player2.apply_network_inputs(inputs, chests=self.chests,
                                           float_texts=self.float_texts,
                                           particles=self.particles)

    def serialize_state(self) -> dict:
        """
        Sérialise l'état complet du jeu en dict JSON-compatible.
        À appeler APRÈS update() et envoyer via GameServer.send_state().
        """
        def sp(p):
            return {'x':p.rect.centerx,'y':p.rect.centery,
                    'health':round(p.health,1),'max_health':p.max_health,
                    'stamina':round(p.stamina,1),'max_stamina':p.max_stamina,
                    'kills':p.kills,'coins':p.coins,'facing_right':p.facing_right,
                    'anim_state':p._anim_state,'skill':p.skill,
                    'weapon':p.current_weapon.key,'inventory':list(p.inventory)}
        def se(e):
            return {'id':id(e),'x':e.rect.centerx,'y':e.rect.centery,
                    'health':e.health,'max_health':e.max_health,
                    'type':e.enemy_type,'size':e.size,'epoch':e.epoch_key}
        return {
            'epoch':self.epoch_key,'wave':self.wave,
            'wave_complete':self.wave_complete,'boss_wave':self.boss_wave,
            'enemies_left':len(self.enemies),'show_chest_hint':self.show_chest_hint,
            'objective_hint':self.objective_hint,
            'game_over':self._network_game_over,'next_epoch':self._network_next_epoch,
            'p1':sp(self.player) if self.player else None,
            'p2':sp(self.player2) if self.player2 else None,
            'enemies':[se(e) for e in self.enemies],
            'bullets':[{'x':b.rect.centerx,'y':b.rect.centery} for b in self.bullets],
            'enemy_bullets':[{'x':b.rect.centerx,'y':b.rect.centery} for b in self.enemy_bullets],
            'powerups':[{'x':p.rect.centerx,'y':p.rect.centery,'type':p.type} for p in self.powerups],
            'chests':[{'x':c.rect.centerx,'y':c.rect.centery,'opened':c.opened} for c in self.chests],
        }

    # ── Événements (P1 local) ─────────────────────────────────────────────────
    def handle_event(self, event):
        """Gère les événements de P1 (valide en solo ET en mode server)."""
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE: return "MENU"
            for i,wk in enumerate(self.player.inventory):
                if event.key==pygame.K_1+i: self.player.change_weapon(wk)
            if event.key==pygame.K_f:
                if self.player.use_skill() and self.player.skill=="mage":
                    self.particles.emit_magic(self.player.rect.centerx,self.player.rect.centery,color=TEAL,count=20)
            if event.key==pygame.K_e:
                for chest in self.chests:
                    if chest.check_interaction(self.player.rect):
                        if chest.open(self.player):
                            self.float_texts.add(self.player.rect.centerx,self.player.rect.top-20,
                                                  f"+ {chest.weapon_inside}!",GOLD)
                            self.show_chest_hint=False
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            mx,my=pygame.mouse.get_pos()
            if self.player.attack(mx,my):
                wtype=self.player.current_weapon.type
                if wtype=="melee": self.particles.emit_hit_spark(mx,my,YELLOW,5)
                elif self.player.current_weapon.key in ("magic_orb",): self.particles.emit_magic(mx,my,TEAL,6)
        return None

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self):
        """
        Simulation principale (une frame). Appelée par Game.run().
        En mode server : apply_p2_network_inputs() doit avoir été appelé AVANT.
        """
        self._network_game_over=False
        self._network_next_epoch=None
        self.objective_hint=""

        p1_dead=self.player.health<=0
        p2_dead=(self.player2 is None) or (self.player2.health<=0)
        if p1_dead and p2_dead:
            self._network_game_over=True
            return True

        keys=pygame.key.get_pressed()
        # Mettre à jour P1 (local)
        self.player.update(keys)
        # Mettre à jour P2 réseau (flags posés par apply_p2_network_inputs)
        if self.mode=="server" and self.player2:
            self.player2.update_as_p2_server()

        # ── CORRECTIF ITERATION ───────────────────────────────────────────────
        # On passe par list() pour créer un SNAPSHOT de all_sprites avant la
        # boucle. Sans ça, quand Bullet.update() appelle self.kill() (hors écran),
        # il modifie le dict interne du Group pendant l'itération → pygame saute
        # silencieusement certains sprites → les bullets ne bougent pas →
        # les collisions ne sont jamais détectées → ennemis invincibles.
        for sprite in list(self.all_sprites):
            if sprite is not self.player and sprite is not self.player2:
                sprite.update(keys)

        self.screen_fx.update(); self.particles.update(); self.float_texts.update()
        self.spawn_timer+=1

        # Spawn
        if not self.wave_complete and not self.boss_wave:
            if self.spawn_timer>=55 and self.enemies_spawned<self.enemies_this_wave:
                self._spawn_enemy(); self.enemies_spawned+=1; self.spawn_timer=0
        if self.boss_wave and not self.boss_spawned: self._spawn_boss()

        # ── CORRECTIF COLLISIONS : projectiles joueurs → ennemis ──────────────
        # On remplace groupcollide() par une boucle manuelle explicite.
        # groupcollide() utilise la bounding box de l'image APRÈS rotation, qui
        # peut être décalée/trop grande selon la version de pygame, ce qui cause
        # des faux-négatifs (bullet visiblement sur l'ennemi mais rect décalé).
        # La boucle manuelle utilise un rect centré sur la position réelle du
        # bullet, indépendamment de la taille de l'image rotée.
        dead_enemies = set()   # Ennemis tués ce frame (pour éviter les kills multiples)
        for bullet in list(self.bullets):
            bx, by = bullet.rect.centerx, bullet.rect.centery
            # Hitbox du bullet : petit carré centré sur sa position réelle
            # (indépendant de l'image rotée, plus fiable)
            b_hit = pygame.Rect(0, 0, 16, 16)
            b_hit.center = (bx, by)
            bullet_killed = False
            for enemy in list(self.enemies):
                if enemy in dead_enemies:
                    continue
                if b_hit.colliderect(enemy.rect):
                    bullet.kill()
                    bullet_killed = True
                    dmg = bullet.damage
                    enemy.health -= dmg
                    self.float_texts.add_damage(enemy.rect.centerx, enemy.rect.top-10, dmg)
                    self.particles.emit_blood(enemy.rect.centerx, enemy.rect.centery)
                    if enemy.health <= 0:
                        dead_enemies.add(enemy)
                        col = EPOCHS.get(self.epoch_key, {}).get("enemy_tint", RED)
                        self.particles.emit_death(enemy.rect.centerx, enemy.rect.centery, col)
                        self._spawn_powerup(enemy.rect.centerx, enemy.rect.centery)
                        owner = bullet.owner if getattr(bullet, "owner", None) else self.player
                        owner.add_kill()
                        enemy.kill()
                    break   # Un bullet ne touche qu'un seul ennemi
                if bullet_killed:
                    break

        # Mêlée → ennemis (boucle manuelle aussi pour la même raison)
        for melee in list(self.melee_attacks):
            for enemy in list(self.enemies):
                if enemy in dead_enemies:
                    continue
                if melee.rect.colliderect(enemy.rect) and enemy not in melee.hit_enemies:
                    melee.hit_enemies.add(enemy)
                    dmg = melee.damage
                    enemy.health -= dmg
                    self.float_texts.add_damage(enemy.rect.centerx, enemy.rect.top-10, dmg)
                    self.screen_fx.shake(4, 8)
                    if enemy.health <= 0:
                        dead_enemies.add(enemy)
                        col = EPOCHS.get(self.epoch_key, {}).get("enemy_tint", RED)
                        self.particles.emit_death(enemy.rect.centerx, enemy.rect.centery, col)
                        self._spawn_powerup(enemy.rect.centerx, enemy.rect.centery)
                        owner = melee.owner if getattr(melee, "owner", None) else self.player
                        owner.add_kill()
                        enemy.kill()

        # Balles ennemies → P1
        if self.player.health>0:
            for b in pygame.sprite.spritecollide(self.player,self.enemy_bullets,True):
                self.player.take_damage(b.damage)
                self.float_texts.add_damage(self.player.rect.centerx,self.player.rect.top-20,int(b.damage))
                self.particles.emit_hit_spark(self.player.rect.centerx,self.player.rect.centery,RED,6)
                self.screen_fx.flash(RED,7); self.screen_fx.shake(6,10)

        # Balles ennemies → P2 réseau
        if self.mode=="server" and self.player2 and self.player2.health>0:
            for b in pygame.sprite.spritecollide(self.player2,self.enemy_bullets,True):
                self.player2.take_damage(b.damage)
                self.float_texts.add_damage(self.player2.rect.centerx,self.player2.rect.top-20,int(b.damage))
                self.particles.emit_hit_spark(self.player2.rect.centerx,self.player2.rect.centery,(80,160,255),5)

        # Power-ups → P1
        for pu in pygame.sprite.spritecollide(self.player,self.powerups,True):
            self.player.apply_powerup(pu.type)
            label={"damage":"+DMG","speed":"+SPD","health":"+HP","stamina":"+STA"}.get(pu.type,"?")
            col={"damage":RED,"speed":CYAN,"health":(60,220,80),"stamina":BLUE}.get(pu.type,WHITE)
            self.float_texts.add(self.player.rect.centerx,self.player.rect.top-30,label,col,22)

        # Power-ups → P2 réseau
        if self.mode=="server" and self.player2 and self.player2.health>0:
            for pu in pygame.sprite.spritecollide(self.player2,self.powerups,True):
                self.player2.apply_powerup(pu.type)
                label={"damage":"+DMG","speed":"+SPD","health":"+HP","stamina":"+STA"}.get(pu.type,"?")
                col={"damage":RED,"speed":CYAN,"health":(60,220,80),"stamina":BLUE}.get(pu.type,WHITE)
                self.float_texts.add(self.player2.rect.centerx,self.player2.rect.top-30,f"P2 {label}",col,22)

        # Fin de vague
        if not self.wave_complete:
            if len(self.enemies)==0 and (self.boss_wave or self.enemies_spawned>=self.enemies_this_wave):
                self.wave_complete=True; self.next_wave_timer=0
                self.player.coins+=5
                if self.player2: self.player2.coins+=5
                if self.boss_wave:
                    chest_wk=self.weapons[1] if len(self.weapons)>1 else self.weapons[0]
                    chest=Chest(SCREEN_WIDTH//2,SCREEN_HEIGHT//2,chest_wk)
                    self.chests.add(chest); self.all_sprites.add(chest)
                    self.player.coins+=10
                    if self.player2: self.player2.coins+=10
                    self.on_exit()
        else:
            def near(p): return p and any(c.check_interaction(p.rect) and not c.opened for c in self.chests)
            if self.boss_wave:
                all_chests_opened = bool(self.chests) and all(c.opened for c in self.chests)
                players_near = near(self.player) or near(self.player2)
                self.show_chest_hint = players_near or (bool(self.chests) and not all_chests_opened) or self._boss_chest_opened
                if all_chests_opened:
                    if not self._boss_chest_opened:
                        self._boss_chest_opened = True
                        self.next_wave_timer = 0
                    self.objective_hint = "Passage temporel imminent..."
                    self.next_wave_timer += 1
                    if self.next_wave_timer >= 90:
                        next_epoch=EPOCHS.get(self.epoch_key,{}).get("next",None)
                        self._network_next_epoch=next_epoch
                        return f"NEXT_EPOCH:{next_epoch}" if next_epoch else "NEXT_EPOCH:None"
                else:
                    self.next_wave_timer = 0
                    self.objective_hint = "E : Ouvrir le coffre" if players_near else "Approchez-vous du coffre de fin d'epoque"
            else:
                self.next_wave_timer+=1
                self.show_chest_hint=False
                if self.next_wave_timer>=160:
                    self._start_new_wave()
        return None

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface):
        """Rendu de la scène (côté host, P1). En mode client, utiliser ClientRenderer."""
        ox,oy=self.screen_fx.offset
        bg=self.bg_renderer.get(self.epoch_key); surface.blit(bg,(ox,oy))
        for sprite in self.all_sprites:
            if sprite is self.player or sprite is self.player2:
                continue
            surface.blit(sprite.image,(sprite.rect.x+ox,sprite.rect.y+oy))
        if self.player:
            self._draw_player(surface, self.player, ox, oy)
        # Arme P2 réseau (visible côté host)
        if self.mode=="server" and self.player2 and self.player2.health>0:
            pr2=self._draw_player(surface, self.player2, ox, oy)
            font_lbl=pygame.font.Font(None,22)
            lbl=font_lbl.render("P2",True,(120,200,255))
            surface.blit(lbl,(pr2.centerx-lbl.get_width()//2,pr2.top-18))
        for enemy in self.enemies:
            r=enemy.rect.move(ox,oy)
            draw_enemy_health_bar(surface,r,enemy.health,enemy.max_health,
                                   EPOCHS.get(self.epoch_key,{}).get("color",RED),
                                   is_boss=(enemy.enemy_type=="boss"),screen_w=SCREEN_WIDTH)
        self.particles.draw(surface); self.float_texts.draw(surface); self.screen_fx.draw_flash(surface)
        self.hud.draw(surface,self.player,self.epoch_key,self.wave,
                       self.wave_complete,self.boss_wave,enemies_left=len(self.enemies))
        if self.mode=="server" and self.player2:
            self._draw_p2_hud(surface)
        self.draw_epoch_decoration(surface)
        if self.show_chest_hint:
            font=pygame.font.Font(None,32)
            hint_text = self.objective_hint or "E : Ouvrir le coffre"
            hint=font.render(hint_text,True,GOLD)
            hr=hint.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT-80))
            bg_s=pygame.Surface((hr.w+20,hr.h+10),pygame.SRCALPHA); bg_s.fill((0,0,0,160))
            surface.blit(bg_s,(hr.x-10,hr.y-5)); surface.blit(hint,hr)
        if len(self.player.inventory)>1:
            font=pygame.font.Font(None,22)
            hint=font.render("1/2:Arme | F:Skill | ESC:Menu",True,LIGHT_GRAY)
            surface.blit(hint,(10,SCREEN_HEIGHT-28))

    def _draw_p2_hud(self, surface):
        """HUD de P2 réseau, affiché en bas à droite côté host."""
        p2=self.player2; font=pygame.font.Font(None,22)
        PANEL_W,PANEL_H=210,70; px=SCREEN_WIDTH-PANEL_W-14; py=SCREEN_HEIGHT-PANEL_H-14
        bg=pygame.Surface((PANEL_W,PANEL_H),pygame.SRCALPHA); bg.fill((10,20,50,170))
        pygame.draw.rect(bg,(80,140,255),bg.get_rect(),2,border_radius=8); surface.blit(bg,(px,py))
        if p2.health<=0:
            t=font.render("P2 — KO",True,RED); surface.blit(t,(px+8,py+PANEL_H//2-t.get_height()//2)); return
        skill_name=SKILLS.get(p2.skill,{}).get("name","P2") if p2.skill else "P2"
        surface.blit(font.render(f"P2 — {skill_name}",True,(150,200,255)),(px+6,py+6))
        bw=PANEL_W-20; bx,by=px+10,py+28
        pygame.draw.rect(surface,(60,20,20),(bx,by,bw,12),border_radius=3)
        hp_r=max(0,p2.health/max(1,p2.max_health))
        pygame.draw.rect(surface,(int(220*(1-hp_r)),int(220*hp_r),60),(bx,by,int(bw*hp_r),12),border_radius=3)
        pygame.draw.rect(surface,WHITE,(bx,by,bw,12),1,border_radius=3)
        surface.blit(font.render(f"HP {int(p2.health)}/{p2.max_health}",True,WHITE),(bx,by+14))

    def _draw_player(self, surface, player, ox, oy):
        pr = player.rect.move(ox, oy)
        shadow_w = max(26, int(player.rect.width * (0.48 if player._moving else 0.42)))
        shadow_h = 13 if player._moving else 11
        shadow = pygame.Surface((shadow_w * 2, shadow_h * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 85), shadow.get_rect())
        surface.blit(shadow, (pr.centerx - shadow.get_width() // 2, pr.bottom - shadow_h))

        img = player.image
        if abs(player._visual_tilt) > 0.15:
            img = pygame.transform.rotate(img, player._visual_tilt)
        draw_rect = img.get_rect(center=(pr.centerx, pr.centery + int(player._visual_bob)))
        surface.blit(img, draw_rect)
        draw_weapon_in_hand(surface, draw_rect, player.current_weapon, player.facing_right)
        return draw_rect
