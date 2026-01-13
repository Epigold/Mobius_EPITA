"""
Epoque Prehistorique - Premiere epoque du jeu
Ennemis: Dinosaures, hommes des cavernes hostiles
Ambiance: Jungle préhistorique, volcans
"""

import pygame
import random
import math
from core.constants import *
from core.base_epoque import BaseEpoque
from entities.enemy import Enemy
from entities.projectile import Projectile
from entities.powerup import PowerUp
from entities.chest import Chest

class PrehistoricEpoque(BaseEpoque):
    def __init__(self, player):
        super().__init__(player, "Préhistoire")
        self.bg_color = (100, 70, 40)  # Terre marron
        
        # Armes specifiques à l'epoque
        self.epoque_weapons = ['caillou', 'os', 'massue']
        
        # Premier coffre avec l'os
        self.spawn_chest_with_weapon('os', SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)
        
    def spawn_wave(self):
        """Génère une vague d'ennemis préhistoriques"""
        self.current_wave += 1
        enemy_count = 3 + (self.current_wave - 1) * ENEMY_INCREASE_PER_WAVE
        
        is_boss_wave = self.current_wave % BOSS_WAVE == 0
        
        if is_boss_wave:
            # Boss: Grand dinosaure
            boss = self.spawn_enemy('Tank', is_boss=True)
            boss.size = 60
            boss.health *= 3
            boss.max_health = boss.health
            self.enemies.append(boss)
            enemy_count -= 1
        
        # Ennemis normaux
        enemy_types = ['Rusher', 'Tank', 'Sniper']
        weights = [0.5, 0.3, 0.2]  # Plus de Rushers (dinosaures rapides)
        
        for _ in range(enemy_count):
            enemy_type = random.choices(enemy_types, weights=weights)[0]
            self.enemies.append(self.spawn_enemy(enemy_type))
            
    def spawn_enemy(self, enemy_type, is_boss=False):
        """Crée un ennemi préhistorique"""
        while True:
            x = random.randint(SPAWN_MARGIN, SCREEN_WIDTH - SPAWN_MARGIN)
            y = random.randint(SPAWN_MARGIN, SCREEN_HEIGHT - SPAWN_MARGIN)
            
            dx = x - self.player.x
            dy = y - self.player.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > MIN_SPAWN_DISTANCE:
                enemy = Enemy(x, y, enemy_type, self.current_wave)
                
                # Couleurs préhistoriques
                if enemy_type == 'Tank':
                    enemy.color = (80, 60, 40)  # Dinosaure brun
                elif enemy_type == 'Rusher':
                    enemy.color = (120, 100, 60)  # Dinosaure rapide
                elif enemy_type == 'Sniper':
                    enemy.color = (100, 80, 50)  # Homme des cavernes
                    
                return enemy
    
    def draw(self, screen):
        """Dessine l'epoque prehistorique"""
        screen.fill(self.bg_color)
        
        # Dessiner des rochers décoratifs
        for i in range(5):
            x = (i * 250 + 100) % SCREEN_WIDTH
            y = (i * 150 + 50) % SCREEN_HEIGHT
            pygame.draw.circle(screen, (60, 50, 30), (x, y), 30)
        
        # Dessiner les entités
        super().draw_entities(screen)
        
        # UI
        self.player.draw_ui(screen)
        self.draw_wave_info(screen)
        
    def get_next_weapon_reward(self):
        """Retourne la prochaine arme à débloquer"""
        if 'os' not in self.player.inventory:
            return 'os'
        elif 'massue' not in self.player.inventory:
            return 'massue'
        return None