"""
Epoque Moderne - Troisieme epoque du jeu
Ennemis: Soldats, tanks, snipers
Ambiance: Ville moderne, guerre
"""

import pygame
import random
import math
from core.constants import *
from core.base_epoque import BaseEpoque
from entities.enemy import Enemy

class ModernEpoque(BaseEpoque):
    def __init__(self, player):
        super().__init__(player, "Ère Moderne")
        self.bg_color = (70, 70, 80)  # Gris urbain
        
        # Armes spécifiques
        self.epoque_weapons = ['pistolet', 'fusil']
        
        # Coffres avec armes
        self.spawn_chest_with_weapon('pistolet', SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)
        self.spawn_chest_with_weapon('fusil', 3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)
        
    def spawn_wave(self):
        """Génère une vague d'ennemis modernes"""
        self.current_wave += 1
        enemy_count = 5 + (self.current_wave - 1) * ENEMY_INCREASE_PER_WAVE
        
        is_boss_wave = self.current_wave % BOSS_WAVE == 0
        
        if is_boss_wave:
            # Boss: Tank militaire
            boss = self.spawn_enemy('Tank', is_boss=True)
            boss.size = 65
            boss.health *= 4
            boss.max_health = boss.health
            boss.color = (50, 50, 50)  # Gris foncé
            self.enemies.append(boss)
            enemy_count -= 1
        
        # Ennemis normaux
        enemy_types = ['Tank', 'Sniper', 'Rusher']
        weights = [0.25, 0.4, 0.35]  # Équilibré avec plus de snipers
        
        for _ in range(enemy_count):
            enemy_type = random.choices(enemy_types, weights=weights)[0]
            self.enemies.append(self.spawn_enemy(enemy_type))
            
    def spawn_enemy(self, enemy_type, is_boss=False):
        """Crée un ennemi moderne"""
        while True:
            x = random.randint(SPAWN_MARGIN, SCREEN_WIDTH - SPAWN_MARGIN)
            y = random.randint(SPAWN_MARGIN, SCREEN_HEIGHT - SPAWN_MARGIN)
            
            dx = x - self.player.x
            dy = y - self.player.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > MIN_SPAWN_DISTANCE:
                enemy = Enemy(x, y, enemy_type, self.current_wave)
                
                # Couleurs modernes/militaires
                if enemy_type == 'Tank':
                    enemy.color = (100, 100, 100)  # Tank gris
                elif enemy_type == 'Rusher':
                    enemy.color = (85, 107, 47)  # Vert olive (soldat)
                elif enemy_type == 'Sniper':
                    enemy.color = (112, 128, 144)  # Gris ardoise
                    
                return enemy
    
    def draw(self, screen):
        """Dessine l'epoque moderne"""
        screen.fill(self.bg_color)
        
        # Dessiner des bâtiments
        for i in range(6):
            x = i * 200 + 50
            height = 100 + (i % 3) * 50
            pygame.draw.rect(screen, (60, 60, 70), (x, SCREEN_HEIGHT - height, 80, height))
            
            # Fenêtres
            for row in range(int(height / 30)):
                for col in range(2):
                    window_x = x + 20 + col * 40
                    window_y = SCREEN_HEIGHT - height + 10 + row * 30
                    pygame.draw.rect(screen, YELLOW, (window_x, window_y, 15, 20))
        
        # Dessiner les entités
        super().draw_entities(screen)
        
        # UI
        self.player.draw_ui(screen)
        self.draw_wave_info(screen)