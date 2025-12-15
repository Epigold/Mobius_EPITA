# -*- coding: utf-8 -*-
# Jeu Roguelike Mobius
# Améliorations : salles, vagues d'ennemis, système de progression, power-ups

import pygame
import random
import math

# Initialisation de Pygame
pygame.init()
info = pygame.display.Info()
screen_width, screen_height = info.current_w, info.current_h
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Mobius Roguelike")
clock = pygame.time.Clock()

# Couleurs
WHITE = (255, 255, 255)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
DARK_RED = (100, 0, 0)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
DARK_BLUE = (30, 80, 150)
ORANGE = (255, 165, 0)
PURPLE = (150, 50, 200)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
GOLD = (255, 215, 0)
CYAN = (0, 255, 255)

# Tailles
TAILLE_PERSO = 80
TAILLE_ARME = 50
TAILLE_TANK = 120
TAILLE_RUSHER = 70
TAILLE_SNIPER = 90
TAILLE_BOSS = 200

# Paramètres joueur
DASH_SPEED = 20
DASH_TIME = 10
DASH_COOLDOWN = 30
DASH_STAMINA_COST = 15

# MODE PROTOTYPE
PROTOTYPE_MODE = True

# États du jeu
MENU = 0
PLAYING = 1
GAME_OVER = 2

# Chargement des images
player_image = pygame.image.load("assets/characteres/chara_test.png").convert_alpha()
player_image = pygame.transform.scale(player_image, (TAILLE_PERSO, TAILLE_PERSO))
enemy_image = pygame.image.load("assets/characteres/monstre_dj_1.png").convert_alpha()
background_image = pygame.image.load("assets/backgrounds/decor_dj_1.jpg").convert()
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

class Weapon:
    """Classe pour gérer les différentes armes"""
    WEAPONS_DATA = {
        "caillou": {
            "name": "Caillou",
            "image_path": "assets/weapons/caillou_dj_1.png",
            "type": "ranged",
            "damage": 40,
            "stamina_cost": 1,
            "cooldown": 15,
            "projectile_speed": 18,
            "size": 50
        },
        "os": {
            "name": "Os",
            "image_path": "assets/weapons/os_dj_1.png",
            "type": "melee",
            "damage": 80,
            "stamina_cost": 3,
            "cooldown": 25,
            "range": 120,
            "size": 60
        }
    }
    
    def __init__(self, weapon_key):
        self.key = weapon_key
        data = self.WEAPONS_DATA[weapon_key]
        self.name = data["name"]
        self.type = data["type"]
        self.damage = data["damage"]
        self.stamina_cost = data["stamina_cost"]
        self.cooldown_max = data["cooldown"]
        self.cooldown = 0
        self.size = data["size"]
        
        try:
            self.image = pygame.image.load(data["image_path"]).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.size, self.size))
        except:
            self.image = pygame.Surface((self.size, self.size))
            if self.type == "ranged":
                self.image.fill(WHITE)
            else:
                self.image.fill(BROWN)
        
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
    def __init__(self, skill=None):
        super().__init__()
        self.original_image = player_image
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (screen_width // 2, screen_height // 2)
        
        self.hitbox = pygame.Rect(0, 0, TAILLE_PERSO * 0.4, TAILLE_PERSO * 0.4)
        self.hitbox.center = self.rect.center
        
        self.speed = 7
        self.max_health = 100
        self.health = self.max_health
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_regen = 0.2
        self.dashing = False
        self.dash_time = 0
        self.dash_cooldown = 0
        self.dir_x, self.dir_y = 0, 0
        self.facing_right = True
        
        # Stats roguelike
        self.level = 1
        self.kills = 0
        self.coins = 0
        
        # Compétence choisie
        self.skill = skill
        self.skill_cooldown = 0
        self.skill_active = False
        self.skill_duration = 0
        
        # Appliquer les bonus de la compétence
        if skill == "tank":
            self.max_health = 150
            self.health = 150
            self.speed = 5
        elif skill == "berserker":
            self.max_health = 80
            self.health = 80
            self.speed = 9
        elif skill == "vampire":
            self.lifesteal = 0.2  # 20% de vol de vie
        elif skill == "ninja":
            self.speed = 8
            DASH_COOLDOWN = 15  # Cooldown réduit
        elif skill == "mage":
            self.max_stamina = 150
            self.stamina = 150
            self.stamina_regen = 0.3
        
        # Système d'armes
        self.current_weapon = Weapon("caillou")
        if PROTOTYPE_MODE:
            self.inventory = ["caillou", "os"]
        else:
            self.inventory = ["caillou"]
        
        # Power-ups temporaires
        self.damage_boost = 1.0
        self.speed_boost = 1.0
        self.boost_timer = 0

    def update(self, keys):
        # Régénération de stamina
        if self.stamina < self.max_stamina:
            self.stamina += self.stamina_regen
            if self.stamina > self.max_stamina:
                self.stamina = self.max_stamina

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        
        if self.skill_cooldown > 0:
            self.skill_cooldown -= 1
        
        if self.skill_duration > 0:
            self.skill_duration -= 1
            if self.skill_duration == 0:
                self.skill_active = False
        
        self.current_weapon.update_cooldown()
        
        # Décompte des power-ups
        if self.boost_timer > 0:
            self.boost_timer -= 1
            if self.boost_timer == 0:
                self.damage_boost = 1.0
                self.speed_boost = 1.0

        # Orientation vers la souris
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x < self.rect.centerx and not self.facing_right:
            self.facing_right = True
            self.image = self.original_image.copy()
        elif mouse_x > self.rect.centerx and self.facing_right:
            self.facing_right = False
            self.image = pygame.transform.flip(self.original_image, True, False)

        if not self.dashing:
            dx = (keys[pygame.K_d] - keys[pygame.K_q])
            dy = (keys[pygame.K_s] - keys[pygame.K_z])
            if dx or dy:
                norm = math.hypot(dx, dy)
                dx, dy = dx / norm, dy / norm
                self.dir_x, self.dir_y = dx, dy
            
            effective_speed = self.speed * self.speed_boost
            self.rect.x += dx * effective_speed
            self.rect.y += dy * effective_speed
            self.hitbox.center = self.rect.center

            if keys[pygame.K_SPACE] and self.dash_cooldown == 0 and self.stamina >= DASH_STAMINA_COST:
                self.dashing = True
                self.dash_time = DASH_TIME
                self.dash_cooldown = DASH_COOLDOWN
                self.stamina -= DASH_STAMINA_COST
            
            self.rect.clamp_ip(pygame.Rect(0, 0, screen_width, screen_height))
            self.hitbox.center = self.rect.center
        else:
            self.rect.x += self.dir_x * DASH_SPEED
            self.rect.y += self.dir_y * DASH_SPEED
            self.hitbox.center = self.rect.center
            self.dash_time -= 1
            if self.dash_time <= 0:
                self.dashing = False

    def use_skill(self):
        """Active la compétence spéciale du joueur"""
        if self.skill_cooldown > 0 or not self.skill:
            return False
        
        if self.skill == "tank":
            # Bouclier temporaire
            self.skill_active = True
            self.skill_duration = 300  # 5 secondes
            self.skill_cooldown = 1800  # 30 secondes
            return True
        
        elif self.skill == "berserker":
            # Rage : dégâts x2 pendant 5 secondes
            self.damage_boost = 2.0
            self.boost_timer = 300
            self.skill_cooldown = 1200  # 20 secondes
            return True
        
        elif self.skill == "vampire":
            # Vol de vie actif sur la prochaine attaque
            self.skill_active = True
            self.skill_duration = 600  # 10 secondes
            self.skill_cooldown = 900  # 15 secondes
            return True
        
        elif self.skill == "ninja":
            # Téléportation à la souris
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.rect.center = (mouse_x, mouse_y)
            self.hitbox.center = self.rect.center
            self.skill_cooldown = 600  # 10 secondes
            return True
        
        elif self.skill == "mage":
            # Nova de projectiles
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                target_x = self.rect.centerx + math.cos(rad) * 500
                target_y = self.rect.centery + math.sin(rad) * 500
                bullet = Bullet(self.rect.centerx, self.rect.centery,
                              target_x, target_y, self.current_weapon, 1.5)
                bullets.add(bullet)
                all_sprites.add(bullet)
            self.skill_cooldown = 1200  # 20 secondes
            return True
        
        return False

    def attack(self, mouse_x, mouse_y):
        if self.current_weapon.can_use(self.stamina):
            self.stamina -= self.current_weapon.stamina_cost
            self.current_weapon.use()
            
            damage_mult = self.damage_boost
            
            if self.current_weapon.type == "ranged":
                bullet = Bullet(self.rect.centerx, self.rect.centery, 
                              mouse_x, mouse_y, self.current_weapon, damage_mult)
                bullets.add(bullet)
                all_sprites.add(bullet)
            else:
                melee = MeleeAttack(self.rect.centerx, self.rect.centery,
                                   mouse_x, mouse_y, self.current_weapon, damage_mult)
                melee_attacks.add(melee)
                all_sprites.add(melee)
            
            return True
        return False

    def change_weapon(self, weapon_key):
        if weapon_key in self.inventory:
            self.current_weapon = Weapon(weapon_key)

    def add_weapon(self, weapon_key):
        if weapon_key not in self.inventory:
            self.inventory.append(weapon_key)

    def apply_powerup(self, powerup_type):
        if powerup_type == "damage":
            self.damage_boost = 1.5
            self.boost_timer = 600  # 10 secondes
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
            self.health -= amount
            if self.health < 0:
                self.health = 0

    def add_kill(self):
        self.kills += 1
        # Chance de drop de pièce
        if random.random() < 0.3:
            self.coins += 1

    def draw_health_bar(self, surface):
        bar_width = 200
        bar_height = 20
        bar_x = 10
        bar_y = 10
        pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_width, bar_height))
        health_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        font = pygame.font.Font(None, 24)
        text = font.render(f"HP: {int(self.health)}/{self.max_health}", True, WHITE)
        surface.blit(text, (bar_x + bar_width + 10, bar_y))

    def draw_stamina_bar(self, surface):
        bar_width = 200
        bar_height = 15
        bar_x = 10
        bar_y = 35
        pygame.draw.rect(surface, DARK_BLUE, (bar_x, bar_y, bar_width, bar_height))
        stamina_width = int((self.stamina / self.max_stamina) * bar_width)
        pygame.draw.rect(surface, BLUE, (bar_x, bar_y, stamina_width, bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        font = pygame.font.Font(None, 20)
        text = font.render(f"Stamina: {int(self.stamina)}/{self.max_stamina}", True, WHITE)
        surface.blit(text, (bar_x + bar_width + 10, bar_y))
    
    def draw_stats(self, surface):
        font = pygame.font.Font(None, 24)
        
        # Arme actuelle
        weapon_text = font.render(f"Arme: {self.current_weapon.name}", True, WHITE)
        surface.blit(weapon_text, (10, 55))
        
        # Stats
        stats_text = font.render(f"Kills: {self.kills} | Pièces: {self.coins}", True, GOLD)
        surface.blit(stats_text, (10, 80))
        
        # Compétence
        if self.skill:
            skill_names = {
                "tank": "Tank",
                "berserker": "Berserker", 
                "vampire": "Vampire",
                "ninja": "Ninja",
                "mage": "Mage"
            }
            skill_text = font.render(f"Classe: {skill_names.get(self.skill, 'Aucune')}", True, CYAN)
            surface.blit(skill_text, (10, 105))
            
            # Cooldown de compétence
            if self.skill_cooldown > 0:
                cd_text = font.render(f"Compétence: {self.skill_cooldown // 60}s", True, RED)
            else:
                cd_text = font.render("Compétence: Prête (A)", True, GREEN)
            surface.blit(cd_text, (10, 130))
        
        # Power-ups actifs
        if self.boost_timer > 0:
            boost_text = ""
            if self.damage_boost > 1.0:
                boost_text = "DÉGÂTS x1.5"
            elif self.speed_boost > 1.0:
                boost_text = "VITESSE x1.5"
            
            if boost_text:
                boost_render = font.render(boost_text, True, CYAN)
                surface.blit(boost_render, (10, 155))
        
        # Bouclier tank actif
        if self.skill == "tank" and self.skill_active:
            shield_text = font.render("BOUCLIER ACTIF", True, BLUE)
            surface.blit(shield_text, (10, 155))
        
        # Vol de vie vampire actif
        if self.skill == "vampire" and self.skill_active:
            vampire_text = font.render("VOL DE VIE ACTIF", True, RED)
            surface.blit(vampire_text, (10, 155))

    def draw_weapon_in_hand(self, surface):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        dx = mouse_x - self.rect.centerx
        dy = mouse_y - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx))
        
        rotated_weapon = pygame.transform.rotate(self.current_weapon.original_image, angle)
        
        weapon_offset = 40
        weapon_x = self.rect.centerx + math.cos(math.radians(angle)) * weapon_offset
        weapon_y = self.rect.centery - math.sin(math.radians(angle)) * weapon_offset
        
        weapon_rect = rotated_weapon.get_rect(center=(weapon_x, weapon_y))
        surface.blit(rotated_weapon, weapon_rect)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, player, size, speed, health, damage, color_tint=None):
        super().__init__()
        self.base_image = pygame.transform.scale(enemy_image, (size, size))
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
            self.rect.centerx = random.randint(0, screen_width)
            self.rect.top = 0
        elif edge == "bottom":
            self.rect.centerx = random.randint(0, screen_width)
            self.rect.bottom = screen_height
        elif edge == "left":
            self.rect.left = 0
            self.rect.centery = random.randint(0, screen_height)
        else:
            self.rect.right = screen_width
            self.rect.centery = random.randint(0, screen_height)

    def basic_movement(self):
        dx = self.player.rect.x - self.rect.x
        dy = self.player.rect.y - self.rect.y
        dist = math.hypot(dx, dy)
        if dist != 0:
            dx, dy = dx / dist, dy / dist
            self.rect.x += dx * self.speed
            self.rect.y += dy * self.speed

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
        bar_width = 60
        bar_height = 6
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 10
        pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_width, bar_height))
        health_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)

class Tank(Enemy):
    def __init__(self, player):
        super().__init__(player, TAILLE_TANK, 3, 250, 20, (200, 100, 100))
        self.type = "TANK"

class Rusher(Enemy):
    def __init__(self, player):
        super().__init__(player, TAILLE_RUSHER, 9, 60, 8, (255, 200, 100))
        self.type = "RUSHER"

class Sniper(Enemy):
    def __init__(self, player):
        super().__init__(player, TAILLE_SNIPER, 4, 100, 10, (150, 150, 255))
        self.type = "SNIPER"
        self.shoot_cooldown = 0
        self.shoot_delay = 100
        self.shoot_range = 450

    def update(self, *args):
        dx = self.player.rect.x - self.rect.x
        dy = self.player.rect.y - self.rect.y
        dist = math.hypot(dx, dy)
        
        if dist > self.shoot_range:
            self.basic_movement()
        elif dist < self.shoot_range - 50:
            if dist != 0:
                dx, dy = -dx / dist, -dy / dist
                self.rect.x += dx * self.speed
                self.rect.y += dy * self.speed
        
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and dist <= self.shoot_range:
            self.shoot_at_player()
            self.shoot_cooldown = self.shoot_delay
        
        self.handle_collision()

    def shoot_at_player(self):
        bullet = EnemyBullet(self.rect.centerx, self.rect.centery, 
                            self.player.rect.centerx, self.player.rect.centery)
        enemy_bullets.add(bullet)
        all_sprites.add(bullet)

class Boss(Enemy):
    def __init__(self, player, wave):
        health = 1000 + (wave * 200)
        super().__init__(player, TAILLE_BOSS, 5, health, 25, (150, 50, 150))
        self.type = "BOSS"
        self.phase = 1
        self.attack_cooldown = 0
        self.charge_speed = 15
        self.charging = False
        self.charge_time = 0
        self.target_x = 0
        self.target_y = 0
        self.wave = wave

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
                
                elif attack_type == "multi_shot" and self.phase == 2:
                    num_projectiles = 8 + (self.wave * 2)
                    angle_step = 360 // num_projectiles
                    for i in range(num_projectiles):
                        angle = i * angle_step
                        rad = math.radians(angle)
                        target_x = self.rect.centerx + math.cos(rad) * 500
                        target_y = self.rect.centery + math.sin(rad) * 500
                        bullet = EnemyBullet(self.rect.centerx, self.rect.centery, target_x, target_y)
                        enemy_bullets.add(bullet)
                        all_sprites.add(bullet)
                    self.attack_cooldown = 100
        else:
            dx = self.target_x - self.rect.centerx
            dy = self.target_y - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 5:
                dx, dy = dx / dist, dy / dist
                self.rect.x += dx * self.charge_speed
                self.rect.y += dy * self.charge_speed
            
            self.charge_time -= 1
            if self.charge_time <= 0:
                self.charging = False
        
        self.handle_collision()

    def draw_health_bar(self, surface):
        bar_width = 300
        bar_height = 20
        bar_x = screen_width // 2 - bar_width // 2
        bar_y = 50
        
        pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_width, bar_height))
        health_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(surface, PURPLE, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 3)
        
        font = pygame.font.Font(None, 36)
        text = font.render(f"BOSS Vague {self.wave} - Phase {self.phase}", True, PURPLE)
        text_rect = text.get_rect(center=(screen_width // 2, 30))
        surface.blit(text, text_rect)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, weapon, damage_mult=1.0):
        super().__init__()
        self.image = weapon.image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.damage = int(weapon.damage * damage_mult)
        
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        
        if dist != 0:
            self.vel_x = (dx / dist) * weapon.projectile_speed
            self.vel_y = (dy / dist) * weapon.projectile_speed
        else:
            self.vel_x = 0
            self.vel_y = 0

    def update(self, *args):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        
        if (self.rect.right < 0 or self.rect.left > screen_width or 
            self.rect.bottom < 0 or self.rect.top > screen_height):
            self.kill()

class MeleeAttack(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, weapon, damage_mult=1.0):
        super().__init__()
        self.damage = int(weapon.damage * damage_mult)
        self.duration = 15
        
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        
        if dist != 0:
            dx, dy = dx / dist, dy / dist
        
        self.image = pygame.Surface((weapon.melee_range, 50), pygame.SRCALPHA)
        self.image.fill((255, 255, 255, 120))
        self.rect = self.image.get_rect()
        self.rect.center = (x + dx * weapon.melee_range // 2, 
                           y + dy * weapon.melee_range // 2)
        
        self.hit_enemies = set()

    def update(self, *args):
        self.duration -= 1
        if self.duration <= 0:
            self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((15, 15))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=(x, y))
        self.damage = 12
        
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        
        if dist != 0:
            self.vel_x = (dx / dist) * 10
            self.vel_y = (dy / dist) * 10
        else:
            self.vel_x = 0
            self.vel_y = 0

    def update(self, *args):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        
        if (self.rect.right < 0 or self.rect.left > screen_width or 
            self.rect.bottom < 0 or self.rect.top > screen_height):
            self.kill()
        
        if self.rect.colliderect(player.hitbox):
            player.take_damage(self.damage)
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, powerup_type):
        super().__init__()
        self.type = powerup_type
        self.image = pygame.Surface((30, 30))
        
        if powerup_type == "damage":
            self.image.fill(RED)
        elif powerup_type == "speed":
            self.image.fill(CYAN)
        elif powerup_type == "health":
            self.image.fill(GREEN)
        elif powerup_type == "stamina":
            self.image.fill(BLUE)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.lifetime = 600  # 10 secondes

    def update(self, *args):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
        
        # Effet de pulsation
        if self.lifetime % 20 < 10:
            self.rect.inflate_ip(2, 2)
        else:
            self.rect.inflate_ip(-2, -2)

class Chest(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((60, 50))
        self.image.fill(BROWN)
        pygame.draw.rect(self.image, YELLOW, (5, 5, 50, 40), 3)
        self.rect = self.image.get_rect(center=(x, y))
        self.opened = False
        self.weapon_inside = "os"

    def check_interaction(self, player_rect):
        if not self.opened and self.rect.colliderect(player_rect.inflate(50, 50)):
            return True
        return False

    def open(self, player):
        if not self.opened:
            self.opened = True
            player.add_weapon(self.weapon_inside)
            self.image.fill(GREEN)
            pygame.draw.rect(self.image, YELLOW, (5, 5, 50, 40), 3)
            return True
        return False

# Groupes de sprites
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
melee_attacks = pygame.sprite.Group()
chests = pygame.sprite.Group()
powerups = pygame.sprite.Group()

# Variables du jeu
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 24)
running = True
game_state = MENU
selected_skill = None
player = None

# Variables de partie
wave = 1
enemies_this_wave = 10
enemies_spawned = 0
wave_complete = False
boss_wave = False
boss_spawned = False
spawn_timer = 0
show_chest_hint = False

# Définition des compétences
SKILLS = {
    "tank": {
        "name": "Tank",
        "desc": "150 PV, -30% vitesse",
        "special": "Bouclier -50% dégâts",
        "color": BLUE
    },
    "berserker": {
        "name": "Berserker", 
        "desc": "80 PV, +30% vitesse",
        "special": "Rage x2 dégâts 5s",
        "color": RED
    },
    "vampire": {
        "name": "Vampire",
        "desc": "Stats normales",
        "special": "+10 PV par kill 10s",
        "color": PURPLE
    },
    "ninja": {
        "name": "Ninja",
        "desc": "+15% vitesse, Dash CD/2",
        "special": "Téléportation souris",
        "color": BLACK
    },
    "mage": {
        "name": "Mage",
        "desc": "150 Stamina, +50% regen",
        "special": "Nova de projectiles",
        "color": CYAN
    }
}

def draw_menu():
    """Affiche le menu de sélection de compétences"""
    screen.blit(background_image, (0, 0))
    
    # Titre
    title_text = font_large.render("MOBIUS ROGUELIKE", True, WHITE)
    title_rect = title_text.get_rect(center=(screen_width // 2, 100))
    screen.blit(title_text, title_rect)
    
    subtitle_text = font_medium.render("Choisissez votre classe", True, WHITE)
    subtitle_rect = subtitle_text.get_rect(center=(screen_width // 2, 160))
    screen.blit(subtitle_text, subtitle_rect)
    
    # Cartes de compétences
    skill_keys = list(SKILLS.keys())
    card_width = 200
    card_height = 250
    spacing = 30
    total_width = len(skill_keys) * card_width + (len(skill_keys) - 1) * spacing
    start_x = (screen_width - total_width) // 2
    y = 250
    
    mouse_pos = pygame.mouse.get_pos()
    
    for i, skill_key in enumerate(skill_keys):
        skill = SKILLS[skill_key]
        x = start_x + i * (card_width + spacing)
        
        # Rectangle de la carte
        card_rect = pygame.Rect(x, y, card_width, card_height)
        
        # Hover effect
        is_hover = card_rect.collidepoint(mouse_pos)
        border_color = GOLD if is_hover else WHITE
        border_width = 4 if is_hover else 2
        
        # Fond de carte
        card_surface = pygame.Surface((card_width, card_height))
        card_surface.fill(skill["color"])
        card_surface.set_alpha(150)
        screen.blit(card_surface, (x, y))
        
        # Bordure
        pygame.draw.rect(screen, border_color, card_rect, border_width)
        
        # Nom de la classe
        name_text = font_medium.render(skill["name"], True, WHITE)
        name_rect = name_text.get_rect(center=(x + card_width // 2, y + 30))
        screen.blit(name_text, name_rect)
        
        # Description
        desc_lines = [skill["desc"], "", skill["special"]]
        y_offset = 70
        for line in desc_lines:
            if line:
                desc_text = font_small.render(line, True, WHITE)
                desc_rect = desc_text.get_rect(center=(x + card_width // 2, y + y_offset))
                screen.blit(desc_text, desc_rect)
            y_offset += 25
        
        # Numéro de sélection
        num_text = font_small.render(f"Appuyez sur {i+1}", True, YELLOW)
        num_rect = num_text.get_rect(center=(x + card_width // 2, y + card_height - 30))
        screen.blit(num_text, num_rect)
        
        # Stocker le rect pour la détection de clic
        card_rect = skill_key
        if is_hover:
            global selected_skill
            selected_skill = skill_key
    
    # Instructions
    instructions = font_small.render("Cliquez sur une carte ou utilisez les touches 1-5", True, WHITE)
    inst_rect = instructions.get_rect(center=(screen_width // 2, screen_height - 50))
    screen.blit(instructions, inst_rect)

def start_game(skill):
    """Initialise une nouvelle partie avec la compétence choisie"""
    global player, game_state, wave, enemies_this_wave, enemies_spawned
    global wave_complete, boss_wave, boss_spawned, spawn_timer, show_chest_hint
    
    # Réinitialisation
    all_sprites.empty()
    enemies.empty()
    bullets.empty()
    enemy_bullets.empty()
    melee_attacks.empty()
    chests.empty()
    powerups.empty()
    
    # Création du joueur avec la compétence
    player = Player(skill)
    all_sprites.add(player)
    
    # Réinitialisation des variables
    wave = 1
    enemies_this_wave = 10
    enemies_spawned = 0
    wave_complete = False
    boss_wave = False
    boss_spawned = False
    spawn_timer = 0
    show_chest_hint = False
    
    game_state = PLAYING

def spawn_enemy():
    enemy_type = random.choices(
        [Tank, Rusher, Sniper],
        weights=[20, 40, 40]
    )[0]
    enemy = enemy_type(player)
    enemies.add(enemy)
    all_sprites.add(enemy)

def spawn_boss():
    boss = Boss(player, wave)
    enemies.add(boss)
    all_sprites.add(boss)
    return boss

def spawn_powerup(x, y):
    if random.random() < 0.3:  # 30% de chance
        powerup_type = random.choice(["damage", "speed", "health", "stamina"])
        powerup = PowerUp(x, y, powerup_type)
        powerups.add(powerup)
        all_sprites.add(powerup)

def start_new_wave():
    global wave, enemies_this_wave, enemies_spawned, wave_complete, boss_wave, boss_spawned
    wave += 1
    wave_complete = False
    boss_spawned = False
    
    if wave % 3 == 0:  # Boss tous les 3 vagues
        boss_wave = True
        enemies_this_wave = 0
    else:
        boss_wave = False
        enemies_this_wave = 10 + (wave * 3)
        enemies_spawned = 0

# Boucle principale
while running:
    clock.tick(60)
    
    if game_state == MENU:
        draw_menu()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_1:
                    start_game("tank")
                elif event.key == pygame.K_2:
                    start_game("berserker")
                elif event.key == pygame.K_3:
                    start_game("vampire")
                elif event.key == pygame.K_4:
                    start_game("ninja")
                elif event.key == pygame.K_5:
                    start_game("mage")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and selected_skill:
                    start_game(selected_skill)
    
    elif game_state == PLAYING:
        spawn_timer += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = MENU
                elif event.key == pygame.K_1 and "caillou" in player.inventory:
                    player.change_weapon("caillou")
                elif event.key == pygame.K_2 and "os" in player.inventory:
                    player.change_weapon("os")
                elif event.key == pygame.K_a:
                    player.use_skill()
                elif event.key == pygame.K_e:
                    for chest in chests:
                        if chest.check_interaction(player.rect):
                            if chest.open(player):
                                show_chest_hint = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    player.attack(mouse_x, mouse_y)
        # Spawn des ennemis
        if not wave_complete and not boss_wave:
            if spawn_timer >= 60 and enemies_spawned < enemies_this_wave:
                spawn_enemy()
                enemies_spawned += 1
                spawn_timer = 0
        
        # Spawn du boss
        if boss_wave and not boss_spawned:
            spawn_boss()
            boss_spawned = True
        
        # Vérifier si la vague est terminée
        if len(enemies) == 0 and not wave_complete:
            if boss_wave or enemies_spawned >= enemies_this_wave:
                wave_complete = True
                # Récompenses de fin de vague
                player.coins += 5
                if boss_wave:
                    # Spawn du coffre après le boss
                    chest = Chest(screen_width // 2, screen_height // 2)
                    chests.add(chest)
                    all_sprites.add(chest)
                    player.coins += 10
        
        keys = pygame.key.get_pressed()
        all_sprites.update(keys)

        # Collisions projectiles / ennemis
        hits = pygame.sprite.groupcollide(bullets, enemies, True, False)
        for bullet, hit_enemies in hits.items():
            for enemy in hit_enemies:
                enemy.health -= bullet.damage
                if enemy.health <= 0:
                    spawn_powerup(enemy.rect.centerx, enemy.rect.centery)
                    player.add_kill()
                    enemy.kill()

        # Collisions melee / ennemis
        for melee in melee_attacks:
            hits = pygame.sprite.spritecollide(melee, enemies, False)
            for enemy in hits:
                if enemy not in melee.hit_enemies:
                    melee.hit_enemies.add(enemy)
                    enemy.health -= melee.damage
                    if enemy.health <= 0:
                        spawn_powerup(enemy.rect.centerx, enemy.rect.centery)
                        player.add_kill()
                        enemy.kill()

        # Collisions powerups / joueur
        powerup_hits = pygame.sprite.spritecollide(player, powerups, True)
        for powerup in powerup_hits:
            player.apply_powerup(powerup.type)

        # Vérifier interaction coffre
        show_chest_hint = False
        for chest in chests:
            if chest.check_interaction(player.rect) and not chest.opened:
                show_chest_hint = True

        if player.health <= 0:
            game_state = GAME_OVER

        # Affichage
        screen.blit(background_image, (0, 0))
        
        all_sprites.draw(screen)
        player.draw_weapon_in_hand(screen)
        
        for enemy in enemies:
            enemy.draw_health_bar(screen)
        
        # Interface
        player.draw_health_bar(screen)
        player.draw_stamina_bar(screen)
        player.draw_stats(screen)
        
        # Indicateurs
        if len(player.inventory) > 1:
            weapon_hint = font_small.render("1/2: Changer d'arme | A: Compétence", True, WHITE)
            screen.blit(weapon_hint, (10, 180))
        
        # Affichage de la vague
        if not wave_complete:
            if boss_wave:
                wave_text = font_medium.render(f"VAGUE {wave} - BOSS", True, PURPLE)
            else:
                wave_text = font_medium.render(f"Vague {wave} - Ennemis: {len(enemies)}", True, WHITE)
            wave_rect = wave_text.get_rect()
            wave_rect.topright = (screen_width - 20, 10)
            screen.blit(wave_text, wave_rect)
        else:
            complete_text = font_large.render("VAGUE TERMINÉE !", True, GREEN)
            complete_rect = complete_text.get_rect(center=(screen_width // 2, 100))
            screen.blit(complete_text, complete_rect)
            
            next_text = font_medium.render("Préparez-vous pour la prochaine vague...", True, WHITE)
            next_rect = next_text.get_rect(center=(screen_width // 2, 150))
            screen.blit(next_text, next_rect)
            
            # Timer pour la prochaine vague
            if spawn_timer >= 180:  # 3 secondes
                start_new_wave()
                spawn_timer = 0
        
        if show_chest_hint:
            chest_text = font_medium.render("Appuyez sur E pour ouvrir", True, YELLOW)
            chest_rect = chest_text.get_rect(center=(screen_width // 2, screen_height - 100))
            screen.blit(chest_text, chest_rect)
    
    elif game_state == GAME_OVER:
        # Écran de game over
        screen.blit(background_image, (0, 0))
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        game_over_text = font_large.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(screen_width // 2, screen_height // 2 - 100))
        screen.blit(game_over_text, text_rect)
        
        stats_text = font_medium.render(f"Vague atteinte: {wave}", True, WHITE)
        stats_rect = stats_text.get_rect(center=(screen_width // 2, screen_height // 2 - 30))
        screen.blit(stats_text, stats_rect)
        
        kills_text = font_medium.render(f"Ennemis tués: {player.kills}", True, WHITE)
        kills_rect = kills_text.get_rect(center=(screen_width // 2, screen_height // 2 + 10))
        screen.blit(kills_text, kills_rect)
        
        coins_text = font_medium.render(f"Pièces collectées: {player.coins}", True, GOLD)
        coins_rect = coins_text.get_rect(center=(screen_width // 2, screen_height // 2 + 50))
        screen.blit(coins_text, coins_rect)
        
        restart_text = font_medium.render("R: Rejouer | M: Menu", True, WHITE)
        restart_rect = restart_text.get_rect(center=(screen_width // 2, screen_height // 2 + 120))
        screen.blit(restart_text, restart_rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    start_game(player.skill)
                elif event.key == pygame.K_m:
                    game_state = MENU
                elif event.key == pygame.K_ESCAPE:
                    running = False
    
    pygame.display.flip()

pygame.quit()