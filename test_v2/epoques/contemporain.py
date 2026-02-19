# -*- coding: utf-8 -*-
# contemporain.py - Salle de l'Époque Contemporaine (WW2)

"""
ÉPOQUE: ÉPOQUE CONTEMPORAINE (XXe SIÈCLE)
Personnage: Soldat WW2
Armes: AK-47 (distance), Baïonnette (mêlée)
Thème: Gris, guerre moderne
Difficulté: x2.2
"""

from core.base_room import BaseRoom
from core.constants import *
import pygame
import random
import math


class ContemporainRoom(BaseRoom):
    """
    Salle de l'Époque Contemporaine
    
    Cinquième époque : la guerre moderne.
    Les armes sont dévastatrices et les ennemis très résistants.
    """
    
    def __init__(self, game):
        super().__init__(game, "contemporain")
        
        # Personnalisation de l'époque
        self.epoch_name_display = "ÈRE CONTEMPORAINE"
        self.theme_color = GRAY
        
        # Messages spécifiques
        self.welcome_message = "Guerre totale !"
        self.victory_message = "La paix est restaurée !"
        
        # Effets de guerre
        self.explosions = []
        self.bullet_traces = []
        self.screen_shake = 0
        
        # Ambiance de guerre
        self.war_intensity = 0
    
    def on_enter(self):
        """Appelé quand le joueur entre dans cette salle"""
        print(f"⚔️ {self.welcome_message}")
    
    def on_exit(self):
        """Appelé quand le joueur quitte cette salle"""
        print(f"🕊️ {self.victory_message}")
    
    def add_explosion(self, x, y, size=20):
        """Ajoute un effet d'explosion"""
        self.explosions.append({
            'x': x,
            'y': y,
            'size': size,
            'max_size': size * 3,
            'lifetime': 20,
            'color': ORANGE
        })
        # Effet de tremblement d'écran
        self.screen_shake = 10
    
    def add_bullet_trace(self, start_x, start_y, end_x, end_y):
        """Ajoute une trace de balle"""
        self.bullet_traces.append({
            'start': (start_x, start_y),
            'end': (end_x, end_y),
            'lifetime': 5,
            'alpha': 255
        })
    
    def draw_epoch_decoration(self, surface):
        """Dessine des décorations spécifiques à l'époque"""
        # Titre avec style militaire moderne
        font = pygame.font.Font(None, 28)
        epoch_text = font.render(self.epoch_name_display, True, self.theme_color)
        text_rect = epoch_text.get_rect()
        text_rect.topright = (SCREEN_WIDTH - 20, 50)
        
        # Fond sombre militaire
        bg_rect = text_rect.inflate(40, 20)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.fill(BLACK)
        bg_surface.set_alpha(220)
        surface.blit(bg_surface, bg_rect)
        
        # Bordures métalliques
        pygame.draw.rect(surface, GRAY, bg_rect, 3)
        pygame.draw.rect(surface, SILVER, bg_rect.inflate(-4, -4), 1)
        
        surface.blit(epoch_text, text_rect)
        
        # Indicateur de danger (niveau de guerre)
        danger_level = min(self.war_intensity / 10, 1.0)
        danger_color = (int(255 * danger_level), int(255 * (1 - danger_level)), 0)
        pygame.draw.circle(surface, danger_color, (text_rect.left - 20, text_rect.centery), 8)
        pygame.draw.circle(surface, WHITE, (text_rect.left - 20, text_rect.centery), 8, 2)
    
    def update(self):
        """Mise à jour avec effets de guerre"""
        result = super().update()
        
        # Mise à jour des explosions
        for explosion in self.explosions[:]:
            explosion['lifetime'] -= 1
            explosion['size'] = min(explosion['size'] + 2, explosion['max_size'])
            
            if explosion['lifetime'] <= 0:
                self.explosions.remove(explosion)
        
        # Mise à jour des traces de balles
        for trace in self.bullet_traces[:]:
            trace['lifetime'] -= 1
            trace['alpha'] = int((trace['lifetime'] / 5) * 255)
            
            if trace['lifetime'] <= 0:
                self.bullet_traces.remove(trace)
        
        # Réduction du tremblement d'écran
        if self.screen_shake > 0:
            self.screen_shake -= 1
        
        # Ajouter des traces de balles pour les projectiles actifs
        if random.random() < 0.1 and len(self.bullets) > 0:
            bullet = list(self.bullets)[0]
            start_x = bullet.rect.x - bullet.vel_x * 2
            start_y = bullet.rect.y - bullet.vel_y * 2
            self.add_bullet_trace(start_x, start_y, bullet.rect.x, bullet.rect.y)
        
        # Explosions quand un ennemi meurt
        # (géré dans la logique de collision de base_room, ici on peut juste mettre à jour l'intensité)
        self.war_intensity = len(self.enemies) + len(self.bullets) + len(self.enemy_bullets)
        
        return result
    
    def draw(self, surface):
        """Surcharge pour ajouter des éléments visuels spécifiques"""
        # Effet de tremblement d'écran
        if self.screen_shake > 0:
            shake_x = random.randint(-self.screen_shake, self.screen_shake)
            shake_y = random.randint(-self.screen_shake, self.screen_shake)
            surface.scroll(shake_x, shake_y)
        
        super().draw(surface)
        
        # Dessiner les traces de balles
        for trace in self.bullet_traces:
            trace_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            color = (*YELLOW[:3], trace['alpha'])
            pygame.draw.line(trace_surface, color, trace['start'], trace['end'], 2)
            surface.blit(trace_surface, (0, 0))
        
        # Dessiner les explosions
        for explosion in self.explosions:
            # Cercle extérieur (orange)
            pygame.draw.circle(surface, ORANGE, 
                             (int(explosion['x']), int(explosion['y'])), 
                             int(explosion['size']))
            
            # Cercle intérieur (jaune)
            inner_size = int(explosion['size'] * 0.6)
            pygame.draw.circle(surface, YELLOW, 
                             (int(explosion['x']), int(explosion['y'])), 
                             inner_size)
            
            # Point blanc au centre
            core_size = int(explosion['size'] * 0.3)
            pygame.draw.circle(surface, WHITE, 
                             (int(explosion['x']), int(explosion['y'])), 
                             core_size)
        
        self.draw_epoch_decoration(surface)
        
        # Message de bienvenue avec style urgent
        if self.wave == 1 and not self.wave_complete and len(self.enemies) > 0:
            font = pygame.font.Font(None, 40)
            welcome = font.render(self.welcome_message, True, RED)
            welcome_rect = welcome.get_rect(center=(SCREEN_WIDTH // 2, 150))
            
            # Fond avec alerte
            bg_rect = welcome_rect.inflate(60, 30)
            pygame.draw.rect(surface, BLACK, bg_rect)
            pygame.draw.rect(surface, RED, bg_rect, 5)
            pygame.draw.rect(surface, YELLOW, bg_rect.inflate(-10, -10), 2)
            
            surface.blit(welcome, welcome_rect)
    
    def spawn_enemy(self):
        """Surcharge pour ajouter une explosion au spawn"""
        super().spawn_enemy()
        # Effet visuel au spawn d'ennemi
        if len(self.enemies) > 0:
            last_enemy = list(self.enemies)[-1]
            self.add_explosion(last_enemy.rect.centerx, last_enemy.rect.centery, 15)
    
    def get_epoch_tips(self):
        """Conseils spécifiques à l'époque"""
        return [
            "🔫 L'AK-47 a une cadence de tir rapide",
            "🗡️ La Baïonnette est votre dernier recours",
            "💣 Les ennemis sont très dangereux",
            "🎖️ Chaque victoire compte"
        ]