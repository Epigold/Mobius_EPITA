"""
Classe Player - Gestion du joueur et de ses capacités
"""

import pygame
import math
from core.constants import *

class Player:
    def __init__(self, player_class):
        self.player_class = player_class
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.size = PLAYER_SIZE
        
        # Stats basées sur la classe
        stats = CLASS_STATS[player_class]
        self.max_health = stats['health']
        self.health = self.max_health
        self.speed = PLAYER_BASE_SPEED * stats['speed_modifier']
        self.max_stamina = stats['stamina']
        self.stamina = self.max_stamina
        self.special_cooldown = stats['special_cooldown']
        
        # États
        self.last_dash = 0
        self.last_special = 0
        self.is_dashing = False
        self.dash_end_time = 0
        
        # Inventaire
        self.inventory = ['caillou']  # arme de base
        self.current_weapon = 0
        self.coins = 0
        
        # Effets actifs
        self.active_effects = {}
        
        # Direction pour le dash
        self.direction = pygame.math.Vector2(0, -1)
        
    def update(self, keys, current_time):
        """Met à jour le joueur"""
        # Régénération de stamina
        if self.stamina < self.max_stamina:
            regen_rate = STAMINA_REGEN
            if self.player_class == 'Mage':
                regen_rate *= 1.5
            self.stamina = min(self.max_stamina, self.stamina + regen_rate)
        
        # Mouvement
        dx = 0
        dy = 0
        
        if keys[pygame.K_z] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_q] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1
            
        # Normaliser le mouvement diagonal
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
            
        # Sauvegarder la direction pour le dash
        if dx != 0 or dy != 0:
            self.direction = pygame.math.Vector2(dx, dy).normalize()
        
        # Dash
        if self.is_dashing:
            if current_time < self.dash_end_time:
                self.x += self.direction.x * DASH_SPEED
                self.y += self.direction.y * DASH_SPEED
            else:
                self.is_dashing = False
        else:
            # Mouvement normal avec effets de vitesse
            speed = self.speed
            if 'speed' in self.active_effects:
                if current_time < self.active_effects['speed']:
                    speed *= POWERUP_TYPES['speed']['multiplier']
                else:
                    del self.active_effects['speed']
                    
            self.x += dx * speed
            self.y += dy * speed
        
        # Limites de l'écran
        self.x = max(self.size, min(SCREEN_WIDTH - self.size, self.x))
        self.y = max(self.size, min(SCREEN_HEIGHT - self.size, self.y))
        
        # Nettoyer les effets expirés
        expired = []
        for effect, end_time in self.active_effects.items():
            if current_time > end_time:
                expired.append(effect)
        for effect in expired:
            del self.active_effects[effect]
    
    def dash(self, current_time):
        """Effectue un dash"""
        if current_time - self.last_dash > DASH_COOLDOWN and self.stamina >= DASH_COST:
            self.stamina -= DASH_COST
            self.last_dash = current_time
            self.is_dashing = True
            self.dash_end_time = current_time + 200  # durée du dash
            return True
        return False
    
    def use_special(self, current_time):
        """Utilise la compétence spéciale"""
        if current_time - self.last_special > self.special_cooldown:
            self.last_special = current_time
            
            if self.player_class == 'Tank':
                # Bouclier - réduit les dégâts
                self.active_effects['shield'] = current_time + 5000
            elif self.player_class == 'Berserker':
                # Rage - double les dégâts
                self.active_effects['rage'] = current_time + 5000
            elif self.player_class == 'Vampire':
                # Vol de vie
                self.active_effects['lifesteal'] = current_time + 10000
            elif self.player_class == 'Ninja':
                # Téléportation - géré ailleurs
                return 'teleport'
            elif self.player_class == 'Mage':
                # Nova de projectiles - géré ailleurs
                return 'nova'
            
            return True
        return False
    
    def take_damage(self, damage):
        """Reçoit des dégâts"""
        if 'shield' in self.active_effects:
            damage *= 0.5
        self.health -= damage
        return self.health <= 0
    
    def heal(self, amount):
        """Soigne le joueur"""
        self.health = min(self.max_health, self.health + amount)
    
    def add_item(self, item):
        """Ajoute un objet à l'inventaire"""
        if item not in self.inventory:
            self.inventory.append(item)
    
    def switch_weapon(self, index):
        """Change d'arme"""
        if 0 <= index < len(self.inventory):
            self.current_weapon = index
            return True
        return False
    
    def get_weapon(self):
        """Retourne l'arme actuelle"""
        if self.current_weapon < len(self.inventory):
            return self.inventory[self.current_weapon]
        return 'caillou'
    
    def get_damage_multiplier(self):
        """Retourne le multiplicateur de dégâts actuel"""
        multiplier = 1.0
        if 'rage' in self.active_effects:
            multiplier *= 2.0
        if 'damage' in self.active_effects:
            multiplier *= POWERUP_TYPES['damage']['multiplier']
        return multiplier
    
    def apply_powerup(self, powerup_type, current_time):
        """Applique un power-up"""
        if powerup_type == 'health':
            self.heal(POWERUP_TYPES['health']['amount'])
        elif powerup_type == 'stamina':
            self.stamina = self.max_stamina
        else:
            self.active_effects[powerup_type] = current_time + POWERUP_DURATION
    
    def draw(self, screen):
        """Dessine le joueur"""
        # Couleur selon la classe
        color_map = {
            'Tank': BLUE,
            'Berserker': RED,
            'Vampire': DARK_RED,
            'Ninja': PURPLE,
            'Mage': (100, 100, 255)
        }
        color = color_map.get(self.player_class, WHITE)
        
        # Effet visuel pour les buffs
        if 'shield' in self.active_effects:
            pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), self.size + 5, 2)
        if 'rage' in self.active_effects:
            pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.size + 5, 2)
        
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)
        
    def draw_ui(self, screen):
        """Dessine l'interface utilisateur"""
        font = pygame.font.Font(None, 24)
        
        # Barre de vie
        health_bar_width = 200
        health_bar_height = 20
        health_ratio = self.health / self.max_health
        
        pygame.draw.rect(screen, RED, (10, 10, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, GREEN, (10, 10, health_bar_width * health_ratio, health_bar_height))
        pygame.draw.rect(screen, WHITE, (10, 10, health_bar_width, health_bar_height), 2)
        
        health_text = font.render(f"HP: {int(self.health)}/{self.max_health}", True, WHITE)
        screen.blit(health_text, (15, 12))
        
        # Barre de stamina
        stamina_ratio = self.stamina / self.max_stamina
        pygame.draw.rect(screen, (100, 100, 100), (10, 40, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, YELLOW, (10, 40, health_bar_width * stamina_ratio, health_bar_height))
        pygame.draw.rect(screen, WHITE, (10, 40, health_bar_width, health_bar_height), 2)
        
        stamina_text = font.render(f"STA: {int(self.stamina)}/{self.max_stamina}", True, WHITE)
        screen.blit(stamina_text, (15, 42))
        
        # Classe et arme
        class_text = font.render(f"Classe: {self.player_class}", True, WHITE)
        screen.blit(class_text, (10, 70))
        
        weapon_text = font.render(f"Arme: {self.get_weapon()}", True, WHITE)
        screen.blit(weapon_text, (10, 95))
        
        # Pièces
        coins_text = font.render(f"Pièces: {self.coins}", True, GOLD)
        screen.blit(coins_text, (10, 120))
        
        # Effets actifs
        y = 150
        for effect in self.active_effects:
            effect_text = font.render(f"[{effect.upper()}]", True, ORANGE)
            screen.blit(effect_text, (10, y))
            y += 25