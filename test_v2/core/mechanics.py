# -*- coding: utf-8 -*-
# mechanics.py - Tous les mécanismes du jeu (Armes, Joueur, Ennemis, Projectiles, PowerUps, Coffres)

import pygame
import random
import math
from .constants import *


class Weapon:
    """Gère les armes du jeu"""
    def __init__(self, weapon_key):
        self.key = weapon_key
        data = WEAPONS_DATA[weapon_key]
        self.name = data["name"]
        self.type = data["type"]
        self.damage = data["damage"]
        self.stamina_cost = data["stamina_cost"]
        self.cooldown_max = data["cooldown"]
        self.cooldown = 0
        self.size = data["size"]
        
        try:
            image_path = get_asset_path(*data["image_path"])
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.size, self.size))
        except:
            self.image = pygame.Surface((self.size, self.size))
            self.image.fill(WHITE if self.type == "ranged" else BROWN)
        
        self.original_image = self.image.copy()
        
        if self.type == "ranged":
            self.projectile_speed = data["projectile_speed"]
        else:
            self.melee_range = data["range"]
    
    def update_cooldown(self):
        if self.cooldown > 0:
            self.cooldown -= 1
    
    def can_use(self, stamina):
        return self.cooldown == 0 and stamina >= self.stamina_cost
    
    def use(self):
        self.cooldown = self.cooldown_max


class Player(pygame.sprite.Sprite):
    """Joueur avec compétences et système d'armes"""
    def __init__(self, skill=None, epoch="prehistoire"):
        super().__init__()
        
        # Chargement image
        try:
            player_img = pygame.image.load(get_asset_path("characteres", "chara_test.png")).convert_alpha()
            self.original_image = pygame.transform.scale(player_img, (TAILLE_PERSO, TAILLE_PERSO))
        except:
            self.original_image = pygame.Surface((TAILLE_PERSO, TAILLE_PERSO))
            self.original_image.fill(GREEN)
        
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.hitbox = pygame.Rect(0, 0, TAILLE_PERSO * 0.4, TAILLE_PERSO * 0.4)
        self.hitbox.center = self.rect.center
        
        # Stats de base
        self.speed = 7
        self.max_health = 100
        self.health = self.max_health
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_regen = 0.2
        
        # Mouvement
        self.dashing = False
        self.dash_time = 0
        self.dash_cooldown = 0
        self.dir_x, self.dir_y = 0, 0
        self.facing_right = True
        
        # Progression
        self.level = 1
        self.kills = 0
        self.coins = 0
        
        # Compétence
        self.skill = skill
        self.skill_cooldown = 0
        self.skill_active = False
        self.skill_duration = 0
        self._apply_skill_bonuses()
        
        # Armes selon l'époque
        epoch_weapons = EPOCHS[epoch]["weapons"]
        self.current_weapon = Weapon(epoch_weapons[0])
        self.inventory = epoch_weapons.copy() if PROTOTYPE_MODE else [epoch_weapons[0]]
        
        # Power-ups
        self.damage_boost = 1.0
        self.speed_boost = 1.0
        self.boost_timer = 0
    
    def _apply_skill_bonuses(self):
        """Applique les bonus de la compétence choisie"""
        if self.skill == "tank":
            self.max_health = 150
            self.health = 150
            self.speed = 5
        elif self.skill == "berserker":
            self.max_health = 80
            self.health = 80
            self.speed = 9
        elif self.skill == "vampire":
            self.lifesteal = 0.2
        elif self.skill == "ninja":
            self.speed = 8
        elif self.skill == "mage":
            self.max_stamina = 150
            self.stamina = 150
            self.stamina_regen = 0.3
    
    def update(self, keys, bullets_group, melee_group, all_sprites_group):
        """Mise à jour du joueur"""
        # Régénération stamina
        if self.stamina < self.max_stamina:
            self.stamina = min(self.stamina + self.stamina_regen, self.max_stamina)
        
        # Cooldowns
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.skill_cooldown > 0:
            self.skill_cooldown -= 1
        if self.skill_duration > 0:
            self.skill_duration -= 1
            if self.skill_duration == 0:
                self.skill_active = False
        
        self.current_weapon.update_cooldown()
        
        # Power-ups
        if self.boost_timer > 0:
            self.boost_timer -= 1
            if self.boost_timer == 0:
                self.damage_boost = 1.0
                self.speed_boost = 1.0
        
        # Orientation
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if (mouse_x < self.rect.centerx) != (not self.facing_right):
            self.facing_right = not self.facing_right
            self.image = pygame.transform.flip(self.original_image, True, False) if not self.facing_right else self.original_image.copy()
        
        # Mouvement
        if not self.dashing:
            dx = (keys[pygame.K_d] - (keys[pygame.K_q] or keys[pygame.K_a]))
            dy = (keys[pygame.K_s] - (keys[pygame.K_z] or keys[pygame.K_w]))
            
            if dx or dy:
                norm = math.hypot(dx, dy)
                self.dir_x, self.dir_y = dx / norm, dy / norm
                self.rect.x += self.dir_x * self.speed * self.speed_boost
                self.rect.y += self.dir_y * self.speed * self.speed_boost
            
            # Dash
            if keys[pygame.K_SPACE] and self.dash_cooldown == 0 and self.stamina >= DASH_STAMINA_COST:
                self.dashing = True
                self.dash_time = DASH_TIME
                self.dash_cooldown = DASH_COOLDOWN
                self.stamina -= DASH_STAMINA_COST
            
            self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.rect.x += self.dir_x * DASH_SPEED
            self.rect.y += self.dir_y * DASH_SPEED
            self.dash_time -= 1
            if self.dash_time <= 0:
                self.dashing = False
        
        self.hitbox.center = self.rect.center
    
    def use_skill(self, bullets_group, all_sprites_group):
        """Active la compétence spéciale"""
        if self.skill_cooldown > 0 or not self.skill:
            return False
        
        if self.skill == "tank":
            self.skill_active = True
            self.skill_duration = 300
            self.skill_cooldown = 1800
        elif self.skill == "berserker":
            self.damage_boost = 2.0
            self.boost_timer = 300
            self.skill_cooldown = 1200
        elif self.skill == "vampire":
            self.skill_active = True
            self.skill_duration = 600
            self.skill_cooldown = 900
        elif self.skill == "ninja":
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.rect.center = (mouse_x, mouse_y)
            self.hitbox.center = self.rect.center
            self.skill_cooldown = 600
        elif self.skill == "mage":
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                target_x = self.rect.centerx + math.cos(rad) * 500
                target_y = self.rect.centery + math.sin(rad) * 500
                bullet = Bullet(self.rect.centerx, self.rect.centery, target_x, target_y, self.current_weapon, 1.5)
                bullets_group.add(bullet)
                all_sprites_group.add(bullet)
            self.skill_cooldown = 1200
        
        return True
    
    def attack(self, mouse_x, mouse_y, bullets_group, melee_group, all_sprites_group):
        """Attaque avec l'arme actuelle"""
        if not self.current_weapon.can_use(self.stamina):
            return False
        
        self.stamina -= self.current_weapon.stamina_cost
        self.current_weapon.use()
        
        if self.current_weapon.type == "ranged":
            bullet = Bullet(self.rect.centerx, self.rect.centery, mouse_x, mouse_y, self.current_weapon, self.damage_boost)
            bullets_group.add(bullet)
            all_sprites_group.add(bullet)
        else:
            melee = MeleeAttack(self.rect.centerx, self.rect.centery, mouse_x, mouse_y, self.current_weapon, self.damage_boost)
            melee_group.add(melee)
            all_sprites_group.add(melee)
        
        return True
    
    def change_weapon(self, weapon_key):
        if weapon_key in self.inventory:
            self.current_weapon = Weapon(weapon_key)
    
    def add_weapon(self, weapon_key):
        if weapon_key not in self.inventory:
            self.inventory.append(weapon_key)
    
    def apply_powerup(self, powerup_type):
        if powerup_type == "damage":
            self.damage_boost = 1.5
            self.boost_timer = 600
        elif powerup_type == "speed":
            self.speed_boost = 1.5
            self.boost_timer = 600
        elif powerup_type == "health":
            self.health = min(self.health + 30, self.max_health)
        elif powerup_type == "stamina":
            self.max_stamina += 10
            self.stamina = self.max_stamina
    
    def take_damage(self, amount):
        if not self.dashing:
            if self.skill == "tank" and self.skill_active:
                amount *= 0.5
            self.health -= amount
            self.health = max(0, self.health)
    
    def add_kill(self):
        self.kills += 1
        if random.random() < 0.3:
            self.coins += 1
        if self.skill == "vampire" and self.skill_active:
            self.health = min(self.health + 10, self.max_health)
    
    def draw_health_bar(self, surface):
        bar_x, bar_y, bar_width, bar_height = 10, 10, 200, 20
        pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_width, bar_height))
        health_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        font = pygame.font.Font(None, 24)
        text = font.render(f"HP: {int(self.health)}/{self.max_health}", True, WHITE)
        surface.blit(text, (bar_x + bar_width + 10, bar_y))
    
    def draw_stamina_bar(self, surface):
        bar_x, bar_y, bar_width, bar_height = 10, 35, 200, 15
        pygame.draw.rect(surface, DARK_BLUE, (bar_x, bar_y, bar_width, bar_height))
        stamina_width = int((self.stamina / self.max_stamina) * bar_width)
        pygame.draw.rect(surface, BLUE, (bar_x, bar_y, stamina_width, bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        font = pygame.font.Font(None, 20)
        text = font.render(f"Stamina: {int(self.stamina)}/{self.max_stamina}", True, WHITE)
        surface.blit(text, (bar_x + bar_width + 10, bar_y))
    
    def draw_stats(self, surface, epoch_name):
        font = pygame.font.Font(None, 24)
        y = 55
        
        texts = [
            (f"Époque: {epoch_name}", EPOCHS[next((k for k, v in EPOCHS.items() if v["name"] == epoch_name), "prehistoire")]["color_theme"]),
            (f"Arme: {self.current_weapon.name}", WHITE),
            (f"Kills: {self.kills} | Pièces: {self.coins}", GOLD)
        ]
        
        for text, color in texts:
            surface.blit(font.render(text, True, color), (10, y))
            y += 25
        
        if self.skill:
            skill_name = SKILLS[self.skill]["name"]
            surface.blit(font.render(f"Classe: {skill_name}", True, CYAN), (10, y))
            y += 25
            
            cd_text = f"Compétence: {self.skill_cooldown // 60}s" if self.skill_cooldown > 0 else "Compétence: Prête (F)"
            cd_color = RED if self.skill_cooldown > 0 else GREEN
            surface.blit(font.render(cd_text, True, cd_color), (10, y))
            y += 25
        
        # Status actifs
        if self.boost_timer > 0:
            boost_text = "DÉGÂTS x1.5" if self.damage_boost > 1.0 else "VITESSE x1.5" if self.speed_boost > 1.0 else ""
            if boost_text:
                surface.blit(font.render(boost_text, True, CYAN), (10, y))
        elif self.skill == "tank" and self.skill_active:
            surface.blit(font.render("BOUCLIER ACTIF", True, BLUE), (10, y))
        elif self.skill == "vampire" and self.skill_active:
            surface.blit(font.render("VOL DE VIE ACTIF", True, RED), (10, y))
    
    def draw_weapon_in_hand(self, surface):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx, dy = mouse_x - self.rect.centerx, mouse_y - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx))
        rotated_weapon = pygame.transform.rotate(self.current_weapon.original_image, angle)
        weapon_offset = 40
        weapon_pos = (
            self.rect.centerx + math.cos(math.radians(angle)) * weapon_offset,
            self.rect.centery - math.sin(math.radians(angle)) * weapon_offset
        )
        surface.blit(rotated_weapon, rotated_weapon.get_rect(center=weapon_pos))


class Enemy(pygame.sprite.Sprite):
    """Ennemi de base"""
    def __init__(self, player, size, speed, health, damage, color_tint=None):
        super().__init__()
        
        try:
            enemy_img = pygame.image.load(get_asset_path("characteres", "monstre_dj_1.png")).convert_alpha()
            self.base_image = pygame.transform.scale(enemy_img, (size, size))
        except:
            self.base_image = pygame.Surface((size, size))
            self.base_image.fill(RED)
        
        self.image = self.base_image.copy()
        if color_tint:
            self.image.fill(color_tint, special_flags=pygame.BLEND_MULT)
        
        self.rect = self.image.get_rect()
        self.speed = speed
        self.max_health = health
        self.health = self.max_health
        self.damage = damage
        self.player = player
        self.damage_cooldown = 0
        self.spawn_on_edge()
    
    def spawn_on_edge(self):
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            self.rect.center = (random.randint(0, SCREEN_WIDTH), 0)
        elif edge == "bottom":
            self.rect.center = (random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT)
        elif edge == "left":
            self.rect.center = (0, random.randint(0, SCREEN_HEIGHT))
        else:
            self.rect.center = (SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT))
    
    def basic_movement(self):
        dx, dy = self.player.rect.x - self.rect.x, self.player.rect.y - self.rect.y
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed
    
    def handle_collision(self):
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1
        if self.rect.colliderect(self.player.hitbox) and self.damage_cooldown == 0:
            self.player.take_damage(self.damage)
            self.damage_cooldown = 30
    
    def update(self, *args):
        self.basic_movement()
        self.handle_collision()
    
    def draw_health_bar(self, surface):
        bar_width, bar_height = 60, 6
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 10
        pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_width, bar_height))
        health_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)


class Tank(Enemy):
    def __init__(self, player, multiplier=1.0):
        super().__init__(player, TAILLE_TANK, 3, int(250 * multiplier), 20, (200, 100, 100))
        self.type = "TANK"


class Rusher(Enemy):
    def __init__(self, player, multiplier=1.0):
        super().__init__(player, TAILLE_RUSHER, 9, int(60 * multiplier), 8, (255, 200, 100))
        self.type = "RUSHER"


class Sniper(Enemy):
    def __init__(self, player, multiplier=1.0):
        super().__init__(player, TAILLE_SNIPER, 4, int(100 * multiplier), 10, (150, 150, 255))
        self.type = "SNIPER"
        self.shoot_cooldown = 0
        self.shoot_delay = 100
        self.shoot_range = 450
        self.enemy_bullets_group = None
        self.all_sprites_group = None
    
    def set_bullet_group(self, bullets_group, all_sprites_group):
        self.enemy_bullets_group = bullets_group
        self.all_sprites_group = all_sprites_group
    
    def update(self, *args):
        dx, dy = self.player.rect.x - self.rect.x, self.player.rect.y - self.rect.y
        dist = math.hypot(dx, dy)
        
        if dist > self.shoot_range:
            self.basic_movement()
        elif dist < self.shoot_range - 50:
            self.rect.x -= (dx / dist) * self.speed
            self.rect.y -= (dy / dist) * self.speed
        
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and dist <= self.shoot_range and self.enemy_bullets_group:
            bullet = EnemyBullet(self.rect.centerx, self.rect.centery, self.player.rect.centerx, self.player.rect.centery)
            self.enemy_bullets_group.add(bullet)
            self.all_sprites_group.add(bullet)
            self.shoot_cooldown = self.shoot_delay
        
        self.handle_collision()


class Boss(Enemy):
    def __init__(self, player, wave, multiplier=1.0):
        super().__init__(player, TAILLE_BOSS, 5, int((1000 + wave * 200) * multiplier), 25, (150, 50, 150))
        self.type = "BOSS"
        self.phase = 1
        self.attack_cooldown = 0
        self.charge_speed = 15
        self.charging = False
        self.charge_time = 0
        self.target_x = 0
        self.target_y = 0
        self.wave = wave
        self.enemy_bullets_group = None
        self.all_sprites_group = None
    
    def set_bullet_group(self, bullets_group, all_sprites_group):
        self.enemy_bullets_group = bullets_group
        self.all_sprites_group = all_sprites_group
    
    def update(self, *args):
        if self.health < self.max_health * 0.5 and self.phase == 1:
            self.phase = 2
            self.speed = 7
        
        self.attack_cooldown -= 1
        
        if not self.charging:
            self.basic_movement()
            
            if self.attack_cooldown <= 0:
                attack_type = random.choice(["charge", "multi_shot"])
                
                if attack_type == "charge":
                    self.charging = True
                    self.charge_time = 30
                    self.target_x = self.player.rect.centerx
                    self.target_y = self.player.rect.centery
                    self.attack_cooldown = 150
                elif attack_type == "multi_shot" and self.phase == 2 and self.enemy_bullets_group:
                    num_projectiles = 8 + (self.wave * 2)
                    for i in range(num_projectiles):
                        angle = i * (360 // num_projectiles)
                        rad = math.radians(angle)
                        target = (self.rect.centerx + math.cos(rad) * 500, self.rect.centery + math.sin(rad) * 500)
                        bullet = EnemyBullet(self.rect.centerx, self.rect.centery, *target)
                        self.enemy_bullets_group.add(bullet)
                        self.all_sprites_group.add(bullet)
                    self.attack_cooldown = 100
        else:
            dx, dy = self.target_x - self.rect.centerx, self.target_y - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.rect.x += (dx / dist) * self.charge_speed
                self.rect.y += (dy / dist) * self.charge_speed
            
            self.charge_time -= 1
            if self.charge_time <= 0:
                self.charging = False
        
        self.handle_collision()
    
    def draw_health_bar(self, surface):
        bar_width, bar_height = 300, 20
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = 50
        
        pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_width, bar_height))
        health_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(surface, PURPLE, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 3)
        
        font = pygame.font.Font(None, 36)
        text = font.render(f"BOSS Vague {self.wave} - Phase {self.phase}", True, PURPLE)
        surface.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 30)))


class Bullet(pygame.sprite.Sprite):
    """Projectile du joueur"""
    def __init__(self, x, y, target_x, target_y, weapon, damage_mult=1.0):
        super().__init__()
        self.image = weapon.image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.damage = int(weapon.damage * damage_mult)
        
        dx, dy = target_x - x, target_y - y
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.vel_x = (dx / dist) * weapon.projectile_speed
            self.vel_y = (dy / dist) * weapon.projectile_speed
        else:
            self.vel_x = self.vel_y = 0
    
    def update(self, *args):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        if not pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).colliderect(self.rect):
            self.kill()


class MeleeAttack(pygame.sprite.Sprite):
    """Attaque de mêlée"""
    def __init__(self, x, y, target_x, target_y, weapon, damage_mult=1.0):
        super().__init__()
        self.damage = int(weapon.damage * damage_mult)
        self.duration = 15
        
        dx, dy = target_x - x, target_y - y
        dist = math.hypot(dx, dy)
        if dist != 0:
            dx, dy = dx / dist, dy / dist
        
        self.image = pygame.Surface((weapon.melee_range, 50), pygame.SRCALPHA)
        self.image.fill((255, 255, 255, 120))
        self.rect = self.image.get_rect(center=(x + dx * weapon.melee_range // 2, y + dy * weapon.melee_range // 2))
        self.hit_enemies = set()
    
    def update(self, *args):
        self.duration -= 1
        if self.duration <= 0:
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    """Projectile ennemi"""
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((15, 15))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=(x, y))
        self.damage = 12
        
        dx, dy = target_x - x, target_y - y
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.vel_x = (dx / dist) * 10
            self.vel_y = (dy / dist) * 10
        else:
            self.vel_x = self.vel_y = 0
    
    def update(self, *args):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        if not pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).colliderect(self.rect):
            self.kill()


class PowerUp(pygame.sprite.Sprite):
    """Power-up ramassable"""
    COLORS = {"damage": RED, "speed": CYAN, "health": GREEN, "stamina": BLUE}
    
    def __init__(self, x, y, powerup_type):
        super().__init__()
        self.type = powerup_type
        self.image = pygame.Surface((30, 30))
        self.image.fill(self.COLORS.get(powerup_type, WHITE))
        self.rect = self.image.get_rect(center=(x, y))
        self.lifetime = 600
    
    def update(self, *args):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


class Chest(pygame.sprite.Sprite):
    """Coffre contenant une arme"""
    def __init__(self, x, y, weapon_inside):
        super().__init__()
        self.image = pygame.Surface((60, 50))
        self.image.fill(BROWN)
        pygame.draw.rect(self.image, YELLOW, (5, 5, 50, 40), 3)
        self.rect = self.image.get_rect(center=(x, y))
        self.opened = False
        self.weapon_inside = weapon_inside
    
    def check_interaction(self, player_rect):
        return not self.opened and self.rect.colliderect(player_rect.inflate(50, 50))
    
    def open(self, player):
        if not self.opened:
            self.opened = True
            player.add_weapon(self.weapon_inside)
            self.image.fill(GREEN)
            pygame.draw.rect(self.image, YELLOW, (5, 5, 50, 40), 3)
            return True
        return False