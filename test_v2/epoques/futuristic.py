"""
Epoque Futuriste - Quatrieme et derniere epoque
Ennemis: Robots, drones, mechs
Ambiance: Sci-fi, cyberpunk
"""

import pygame
import random
import math
from core.constants import *
from core.base_epoque import BaseEpoque
from entities.enemy import Enemy

class FuturisticEpoque(BaseEpoque):
    def __init__(self, player):
        super().__init__(player, "Futur")
        self.bg_color = (30, 30, 50)  # Bleu sombre cyber
        
        # Armes spécifiques
        self.epoque_weapons = ['laser', 'plasma']
        
        # Coffres avec armes futuristes
        self.spawn_chest_with_weapon('laser', SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2)
        self.spawn_chest_with_weapon('plasma', SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2)
        
        # Effet néon
        self.neon_alpha = 0
        
    def spawn_wave(self):
        """Génère une vague d'ennemis futuristes"""
        self.current_wave += 1
        enemy_count = 6 + (self.current_wave - 1) * ENEMY_INCREASE_PER_WAVE
        
        is_boss_wave = self.current_wave % BOSS_WAVE == 0
        
        if is_boss_wave:
            # Boss: Mech géant
            boss = self.spawn_enemy('Tank', is_boss=True)
            boss.size = 70
            boss.health *= 5
            boss.max_health = boss.health
            boss.color = (255, 0, 255)  # Magenta
            self.enemies.append(boss)
            enemy_count -= 1
        
        # Ennemis normaux
        enemy_types = ['Tank', 'Sniper', 'Rusher']
        weights = [0.3, 0.35, 0.35]  # Équilibré
        
        for _ in range(enemy_count):
            enemy_type = random.choices(enemy_types, weights=weights)[0]
            self.enemies.append(self.spawn_enemy(enemy_type))
            
    def spawn_enemy(self, enemy_type, is_boss=False):
        """Crée un ennemi futuriste"""
        while True:
            x = random.randint(SPAWN_MARGIN, SCREEN_WIDTH - SPAWN_MARGIN)
            y = random.randint(SPAWN_MARGIN, SCREEN_HEIGHT - SPAWN_MARGIN)
            
            dx = x - self.player.x
            dy = y - self.player.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > MIN_SPAWN_DISTANCE:
                enemy = Enemy(x, y, enemy_type, self.current_wave)
                
                # Couleurs futuristes/néon
                if enemy_type == 'Tank':
                    enemy.color = (0, 255, 255)  # Cyan (robot lourd)
                elif enemy_type == 'Rusher':
                    enemy.color = (255, 0, 255)  # Magenta (drone rapide)
                elif enemy_type == 'Sniper':
                    enemy.color = (0, 255, 0)  # Vert néon (tourelle)
                    
                return enemy
    
    def update(self):
        """Met à jour l'epoque avec effets speciaux"""
        # Effet de pulsation néon
        self.neon_alpha = (self.neon_alpha + 2) % 100
        
        return super().update()
    
    def draw(self, screen):
        """Dessine l'époque futuriste"""
        screen.fill(self.bg_color)
        
        # Grille cyberpunk au sol
        grid_color = (0, 100, 150, 50)
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(screen, (0, 100, 150), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(screen, (0, 100, 150), (0, y), (SCREEN_WIDTH, y), 1)
        
        # Structures futuristes
        for i in range(4):
            x = i * 300 + 100
            y = SCREEN_HEIGHT - 150
            # Tour avec effet néon
            alpha = (self.neon_alpha + i * 25) % 100
            color_intensity = int(100 + alpha * 1.55)
            pygame.draw.rect(screen, (0, color_intensity, 255), (x, y, 60, 150))
            pygame.draw.circle(screen, (0, 255, 255), (x + 30, y - 20), 30, 3)
        
        # Dessiner les entités
        super().draw_entities(screen)
        
        # UI
        self.player.draw_ui(screen)
        self.draw_wave_info(screen)
        
        # Message final si dernière vague
        if self.current_wave == WAVES_PER_EPOQUE and len(self.enemies) == 0:
            font = pygame.font.Font(None, 48)
            text = font.render("FÉLICITATIONS! Vous avez vaincu toutes les époques!", True, GOLD)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))