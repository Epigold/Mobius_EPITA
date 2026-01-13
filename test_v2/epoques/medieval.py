"""
Epoque Medievale - Deuxieme epoque du jeu
Ennemis: Chevaliers, archers, mages
Ambiance: Châteaux, forêts
"""

import pygame
import random
import math
from core.constants import *
from core.base_epoque import BaseEpoque
from entities.enemy import Enemy

class MedievalEpoque(BaseEpoque):
    def __init__(self, player):
        super().__init__(player, "Moyen Âge")
        self.bg_color = (60, 80, 60)  # Vert forêt
        
        # Armes spécifiques
        self.epoque_weapons = ['arc', 'épée']
        
        # Coffres avec armes
        self.spawn_chest_with_weapon('arc', SCREEN_WIDTH // 3, SCREEN_HEIGHT // 3)
        self.spawn_chest_with_weapon('épée', 2 * SCREEN_WIDTH // 3, 2 * SCREEN_HEIGHT // 3)
        
    def spawn_wave(self):
        """Génère une vague d'ennemis médiévaux"""
        self.current_wave += 1
        enemy_count = 4 + (self.current_wave - 1) * ENEMY_INCREASE_PER_WAVE
        
        is_boss_wave = self.current_wave % BOSS_WAVE == 0
        
        if is_boss_wave:
            # Boss: Chevalier noir
            boss = self.spawn_enemy('Tank', is_boss=True)
            boss.size = 55
            boss.health *= 3.5
            boss.max_health = boss.health
            boss.color = (20, 20, 20)  # Noir
            self.enemies.append(boss)
            enemy_count -= 1
        
        # Ennemis normaux
        enemy_types = ['Tank', 'Sniper', 'Rusher']
        weights = [0.3, 0.4, 0.3]  # Plus d'archers (Sniper)
        
        for _ in range(enemy_count):
            enemy_type = random.choices(enemy_types, weights=weights)[0]
            self.enemies.append(self.spawn_enemy(enemy_type))
            
    def spawn_enemy(self, enemy_type, is_boss=False):
        """Crée un ennemi médiéval"""
        while True:
            x = random.randint(SPAWN_MARGIN, SCREEN_WIDTH - SPAWN_MARGIN)
            y = random.randint(SPAWN_MARGIN, SCREEN_HEIGHT - SPAWN_MARGIN)
            
            dx = x - self.player.x
            dy = y - self.player.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > MIN_SPAWN_DISTANCE:
                enemy = Enemy(x, y, enemy_type, self.current_wave)
                
                # Couleurs médiévales
                if enemy_type == 'Tank':
                    enemy.color = (150, 150, 150)  # Armure argentée
                elif enemy_type == 'Rusher':
                    enemy.color = (139, 69, 19)  # Brun (guerrier)
                elif enemy_type == 'Sniper':
                    enemy.color = (34, 139, 34)  # Vert (archer)
                    
                return enemy
    
    def draw(self, screen):
        """Dessine l'epoque medievale"""
        screen.fill(self.bg_color)
        
        # Dessiner des tours de château
        for i in range(3):
            x = (i * 400 + 150) % SCREEN_WIDTH
            pygame.draw.rect(screen, (100, 100, 100), (x, 0, 50, 80))
            pygame.draw.polygon(screen, (80, 80, 80), 
                [(x, 80), (x + 25, 50), (x + 50, 80)])
        
        # Dessiner les entités
        super().draw_entities(screen)
        
        # UI
        self.player.draw_ui(screen)
        self.draw_wave_info(screen)