# -*- coding: utf-8 -*-
# core/mechanics.py - Classes de mecanique : Weapon, Projectile, MeleeAttack, PowerUp, Chest

import pygame
import math
import random
from .constants import *
from .graphics   import SpriteCache, draw_weapon_in_hand


# ==============================================================================
#  ARME
# ==============================================================================

class Weapon:
    """Represente une arme tenue par le joueur."""

    def __init__(self, weapon_key: str):
        self.key  = weapon_key
        data      = WEAPONS_DATA.get(weapon_key, {})

        self.name         = data.get("name",         "Arme inconnue")
        self.type         = data.get("type",         "ranged")
        self.damage       = data.get("damage",        30)
        self.stamina_cost = data.get("stamina_cost",   1)
        self.cooldown_max = data.get("cooldown",       20)
        self.cooldown     = 0
        self.size         = data.get("size",           48)

        if self.type == "ranged":
            self.projectile_speed = data.get("projectile_speed", 18)
        else:
            self.melee_range = data.get("range", 110)

        # Chargement sprite
        cache = SpriteCache.get()
        self.original_image = cache.load_weapon(weapon_key, (self.size, self.size))
        self.image          = self.original_image.copy()

    # -- Cooldown -------------------------------------------------------------
    def update_cooldown(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def can_use(self, stamina: float) -> bool:
        return self.cooldown == 0 and stamina >= self.stamina_cost

    def use(self):
        self.cooldown = self.cooldown_max


# ==============================================================================
#  PROJECTILE JOUEUR
# ==============================================================================

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, weapon: Weapon,
                 damage_mult=1.0, epoch_key="prehistoire", owner=None):
        super().__init__()
        self.damage = int(weapon.damage * damage_mult)
        self.epoch  = epoch_key
        self.owner  = owner
        self.weapon_key = weapon.key

        # Sprite : copie du sprite de l'arme (redimensionne)
        base = weapon.image
        proj_size = max(20, weapon.size // 2)
        self.original_image = pygame.transform.scale(base, (proj_size, proj_size))
        self.image  = self.original_image.copy()
        self.rect   = self.image.get_rect(center=(x, y))

        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy) or 1
        self.vel_x = (dx / dist) * weapon.projectile_speed
        self.vel_y = (dy / dist) * weapon.projectile_speed

        # Rotation de l'image
        angle = math.degrees(math.atan2(-dy, dx))
        self.angle = angle
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect  = self.image.get_rect(center=(x, y))

        self._fx = float(x)
        self._fy = float(y)

    def update(self, *args):
        self._fx += self.vel_x
        self._fy += self.vel_y
        self.rect.center = (int(self._fx), int(self._fy))

        sw, sh = SCREEN_WIDTH, SCREEN_HEIGHT
        if (self.rect.right < -20 or self.rect.left > sw + 20 or
                self.rect.bottom < -20 or self.rect.top > sh + 20):
            self.kill()


# ==============================================================================
#  ATTAQUE MELEE JOUEUR
# ==============================================================================

class MeleeAttack(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, weapon: Weapon, damage_mult=1.0, owner=None):
        super().__init__()
        self.damage   = int(weapon.damage * damage_mult)
        self.duration = 14
        self.hit_enemies: set = set()
        self.owner = owner

        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy) or 1
        ndx, ndy = dx / dist, dy / dist

        arc_w = weapon.melee_range
        arc_h = max(40, weapon.size // 2)
        self.image = pygame.Surface((arc_w, arc_h), pygame.SRCALPHA)

        # Dessin arc d'attaque
        arc_color = (255, 255, 255, 100)
        pygame.draw.ellipse(self.image, arc_color, (0, 0, arc_w, arc_h))

        self.rect = self.image.get_rect()
        self.rect.center = (int(x + ndx * arc_w // 2),
                            int(y + ndy * arc_w // 2))

    def update(self, *args):
        self.duration -= 1
        if self.duration <= 0:
            self.kill()


# ==============================================================================
#  PROJECTILE ENNEMI
# ==============================================================================

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y,
                 speed=10, damage=12, epoch_key="prehistoire",
                 sprite_path=None, size=None):
        super().__init__()
        self.damage   = damage
        self.epoch    = epoch_key
        self.sprite_path = sprite_path
        self.render_size = size

        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy) or 1
        self.vel_x = (dx / dist) * speed
        self.vel_y = (dy / dist) * speed

        self.original_image = None
        if sprite_path:
            try:
                target_size = size or (42, 18)
                self.original_image = SpriteCache.get().load(*sprite_path, size=target_size)
            except Exception:
                self.original_image = None

        if self.original_image is None:
            bullet_size = size or 14
            if isinstance(bullet_size, tuple):
                bullet_size = max(bullet_size)
            self.original_image = pygame.Surface((bullet_size, bullet_size), pygame.SRCALPHA)
            color = EPOCHS.get(epoch_key, {}).get("enemy_tint", RED)
            pygame.draw.circle(self.original_image, color, (bullet_size // 2, bullet_size // 2), bullet_size // 2)
            pygame.draw.circle(self.original_image, WHITE, (bullet_size // 2, bullet_size // 2), bullet_size // 2, 1)

        angle = math.degrees(math.atan2(-dy, dx))
        self.angle = angle
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=(x, y))
        self._fx, self._fy = float(x), float(y)

    def update(self, *args):
        self._fx += self.vel_x
        self._fy += self.vel_y
        self.rect.center = (int(self._fx), int(self._fy))

        sw, sh = SCREEN_WIDTH, SCREEN_HEIGHT
        if (self.rect.right < -20 or self.rect.left > sw + 20 or
                self.rect.bottom < -20 or self.rect.top > sh + 20):
            self.kill()


# ==============================================================================
#  POWER-UP
# ==============================================================================

_POWERUP_STYLES = {
    "damage":  {"color": (220, 60, 60),  "symbol": "DMG", "label": "DMG"},
    "speed":   {"color": (60, 200, 220), "symbol": "SPD", "label": "SPD"},
    "health":  {"color": (60, 200, 80),  "symbol": "HP",  "label": "HP"},
    "stamina": {"color": (80, 120, 255), "symbol": "STA", "label": "STA"},
}

class PowerUp(pygame.sprite.Sprite):
    SIZE = 34

    def __init__(self, x, y, powerup_type):
        super().__init__()
        self.type = powerup_type
        s = self.SIZE
        self._timer = 0
        self.lifetime = 600

        style = _POWERUP_STYLES.get(powerup_type, {"color": GRAY, "symbol": "?", "label": "?"})
        self._color = style["color"]
        self._label = style["label"]

        self._base_image = self._build(s, style)
        self.image = self._base_image.copy()
        self.rect  = self.image.get_rect(center=(x, y))

    @staticmethod
    def _build(s, style):
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        # Fond cercle
        pygame.draw.circle(surf, (*style["color"], 200), (s // 2, s // 2), s // 2)
        pygame.draw.circle(surf, WHITE, (s // 2, s // 2), s // 2, 2)
        # Lettre
        font = pygame.font.Font(None, 18)
        txt  = font.render(style["label"], True, WHITE)
        surf.blit(txt, (s // 2 - txt.get_width() // 2, s // 2 - txt.get_height() // 2))
        return surf

    def update(self, *args):
        self._timer   += 1
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
            return
        # Pulsation
        scale = 1.0 + 0.08 * math.sin(self._timer * 0.2)
        s = int(self.SIZE * scale)
        self.image = pygame.transform.scale(self._base_image, (s, s))
        self.rect  = self.image.get_rect(center=self.rect.center)


# ==============================================================================
#  COFFRE
# ==============================================================================

class Chest(pygame.sprite.Sprite):
    W, H = 160, 160
    _portal_frames = None
    _portal_open_frames = None

    @classmethod
    def _load_portal_frames(cls):
        if cls._portal_frames is not None and cls._portal_open_frames is not None:
            return
        frames = SpriteCache.get().load_sheet(
            "items", "portal_blue_sheet.png",
            cols=8, rows=1, size=(cls.W, cls.H), alpha=True, trim=True
        )[0]
        cls._portal_frames = frames
        cls._portal_open_frames = list(frames)

    def __init__(self, x, y, weapon_inside="bone"):
        super().__init__()
        self._load_portal_frames()
        self.weapon_inside = weapon_inside
        self.opened = False
        self._pulse = 0
        self._frame_idx = 0
        self.image  = self._portal_frames[0]
        self.rect   = self.image.get_rect(center=(x, y))

    def update(self, *args):
        self._pulse += 1
        if self._pulse % 5 == 0:
            frames = self._portal_open_frames if self.opened else self._portal_frames
            self._frame_idx = (self._frame_idx + 1) % len(frames)
            center = self.rect.center
            self.image = frames[self._frame_idx]
            self.rect = self.image.get_rect(center=center)

    def check_interaction(self, player_rect) -> bool:
        return not self.opened and self.rect.inflate(50, 50).colliderect(player_rect)

    def open(self, player) -> bool:
        if not self.opened:
            self.opened = True
            player.add_weapon(self.weapon_inside)
            self.image = self._portal_open_frames[self._frame_idx]
            return True
        return False
