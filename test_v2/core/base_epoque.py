"""
Classe de base pour toutes les epoques
Contient la logique commune de gestion des vagues, ennemis, etc.
"""

import pygame
import random
import math
from core.constants import *
from entities.enemy import Enemy
from entities.projectile import Projectile
from entities.powerup import PowerUp
from entities.chest import Chest

class BaseEpoque:
    def __init__(self, player, name):
        self.name = name
        self.player = player
        self.current_wave = 0
        self.enemies = []
        self.projectiles = []
        self.powerups = []
        self.chests = []
        self.wave_complete = False
        self.epoque_complete = False
        self.last_shot_time = 0
        self.bg_color = (50, 50, 50)
        
        # Démarrer la première vague
        self.spawn_wave()
        
    def spawn_wave(self):
        """À implémenter par les classes filles"""
        pass
    
    def spawn_enemy(self, enemy_type, is_boss=False):
        """À implémenter par les classes filles"""
        pass
    
    def spawn_chest_with_weapon(self, weapon, x, y):
        """Crée un coffre contenant une arme"""
        chest = Chest(x, y, weapon)
        self.chests.append(chest)
        
    def update(self):
        """Met à jour l'epoque"""
        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        # Mettre à jour le joueur
        self.player.update(keys, current_time)
        
        # Gérer les inputs
        self.handle_input(keys, mouse_buttons, mouse_pos, current_time)
        
        # Mettre à jour les ennemis
        for enemy in self.enemies[:]:
            enemy.update(self.player, current_time)
            
            # Attaque des ennemis
            if enemy.can_attack(self.player, current_time):
                if enemy.enemy_type == 'Sniper':
                    self.spawn_enemy_projectile(enemy, self.player)
                else:
                    if self.player.take_damage(enemy.damage):
                        return "game_over"
        
        # Mettre à jour les projectiles
        for proj in self.projectiles[:]:
            proj.update()
            
            if not proj.is_active():
                self.projectiles.remove(proj)
                continue
                
            # Collision avec ennemis
            for enemy in self.enemies[:]:
                if proj.check_collision(enemy):
                    damage = proj.damage * self.player.get_damage_multiplier()
                    
                    # Lifesteal pour vampire
                    if 'lifesteal' in self.player.active_effects:
                        self.player.heal(damage * 0.2)
                    
                    if enemy.take_damage(damage):
                        self.enemies.remove(enemy)
                        self.player.coins += 1
                        
                        # Chance de spawn power-up
                        if random.random() < POWERUP_SPAWN_CHANCE:
                            self.spawn_powerup(enemy.x, enemy.y)
                    
                    proj.active = False
                    break
        
        # Mettre à jour les power-ups
        for powerup in self.powerups[:]:
            if powerup.check_collision(self.player):
                self.player.apply_powerup(powerup.powerup_type, current_time)
                self.powerups.remove(powerup)
        
        # Mettre à jour les coffres
        for chest in self.chests[:]:
            if chest.check_collision(self.player) and keys[pygame.K_e]:
                if not chest.opened:
                    chest.open(self.player)
        
        # Vérifier si la vague est terminée
        if len(self.enemies) == 0 and not self.wave_complete:
            self.wave_complete = True
            
            if self.current_wave >= WAVES_PER_EPOQUE:
                self.epoque_complete = True
                return "next_epoque"
            else:
                # Spawn next wave après un délai
                pygame.time.wait(1000)
                self.wave_complete = False
                self.spawn_wave()
        
        return None
    
    def handle_input(self, keys, mouse_buttons, mouse_pos, current_time):
        """Gère les entrées du joueur"""
        # Dash
        if keys[pygame.K_SPACE]:
            self.player.dash(current_time)
        
        # Compétence spéciale
        if keys[pygame.K_f]:
            result = self.player.use_special(current_time)
            if result == 'teleport':
                self.player.x = mouse_pos[0]
                self.player.y = mouse_pos[1]
            elif result == 'nova':
                self.spawn_nova_projectiles()
        
        # Changement d'arme
        if keys[pygame.K_1]:
            self.player.switch_weapon(0)
        elif keys[pygame.K_2]:
            self.player.switch_weapon(1)
        elif keys[pygame.K_3]:
            self.player.switch_weapon(2)
        
        # Attaque
        if mouse_buttons[0] and current_time - self.last_shot_time > WEAPON_COOLDOWN:
            self.last_shot_time = current_time
            weapon = self.player.get_weapon()
            
            if weapon in ['caillou', 'os', 'arc', 'pistolet', 'laser']:
                # Arme à distance
                self.spawn_player_projectile(mouse_pos)
            else:
                # Arme de mêlée
                self.melee_attack()
    
    def spawn_player_projectile(self, target_pos):
        """Crée un projectile du joueur"""
        dx = target_pos[0] - self.player.x
        dy = target_pos[1] - self.player.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            dx /= distance
            dy /= distance
            
        proj = Projectile(
            self.player.x, self.player.y,
            dx, dy,
            PROJECTILE_DAMAGE, True
        )
        self.projectiles.append(proj)
    
    def spawn_enemy_projectile(self, enemy, target):
        """Crée un projectile ennemi"""
        dx = target.x - enemy.x
        dy = target.y - enemy.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            dx /= distance
            dy /= distance
            
        proj = Projectile(
            enemy.x, enemy.y,
            dx, dy,
            enemy.damage, False
        )
        self.projectiles.append(proj)
    
    def spawn_nova_projectiles(self):
        """Crée une nova de projectiles (Mage)"""
        for i in range(12):
            angle = i * (2 * math.pi / 12)
            dx = math.cos(angle)
            dy = math.sin(angle)
            
            proj = Projectile(
                self.player.x, self.player.y,
                dx, dy,
                PROJECTILE_DAMAGE * 1.5, True
            )
            self.projectiles.append(proj)
    
    def melee_attack(self):
        """Attaque de mêlée"""
        for enemy in self.enemies[:]:
            dx = enemy.x - self.player.x
            dy = enemy.y - self.player.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < WEAPON_RANGE + self.player.size + enemy.size:
                damage = PROJECTILE_DAMAGE * 1.5 * self.player.get_damage_multiplier()
                
                if 'lifesteal' in self.player.active_effects:
                    self.player.heal(damage * 0.2)
                
                if enemy.take_damage(damage):
                    self.enemies.remove(enemy)
                    self.player.coins += 1
                    
                    if random.random() < POWERUP_SPAWN_CHANCE:
                        self.spawn_powerup(enemy.x, enemy.y)
    
    def spawn_powerup(self, x, y):
        """Crée un power-up"""
        powerup_type = random.choice(['damage', 'speed', 'health', 'stamina'])
        powerup = PowerUp(x, y, powerup_type)
        self.powerups.append(powerup)
    
    def draw_entities(self, screen):
        """Dessine toutes les entités"""
        # Power-ups
        for powerup in self.powerups:
            powerup.draw(screen)
        
        # Coffres
        for chest in self.chests:
            chest.draw(screen)
        
        # Projectiles
        for proj in self.projectiles:
            proj.draw(screen)
        
        # Ennemis
        for enemy in self.enemies:
            enemy.draw(screen)
        
        # Joueur
        self.player.draw(screen)
    
    def draw_wave_info(self, screen):
        """Affiche les informations de vague"""
        font = pygame.font.Font(None, 36)
        wave_text = font.render(f"Vague: {self.current_wave}/{WAVES_PER_EPOQUE}", True, WHITE)
        screen.blit(wave_text, (SCREEN_WIDTH - 250, 10))
        
        epoch_text = font.render(self.name, True, GOLD)
        screen.blit(epoch_text, (SCREEN_WIDTH - 250, 50))
    
    def draw(self, screen):
        """À implémenter par les classes filles"""
        pass