# -*- coding: utf-8 -*-
# moderne.py - Salle de l'Époque Moderne (Napoléon)

"""
ÉPOQUE: ÉPOQUE MODERNE (XIXe SIÈCLE)
Personnage: Soldat napoléonien
Armes: Carabine à baïonnette (mêlée), Pistolet (distance)
Thème: Bleu, uniformes militaires
Difficulté: x1.8
"""
from math import cos, sin
from core.base_room import BaseRoom
from core.constants import *
import pygame
import random


class ModerneRoom(BaseRoom):
    """
    Salle de l'Époque Moderne
    
    Quatrième époque : l'ère des armes à feu commence.
    Les armes sont plus puissantes et précises.
    """
    
    def __init__(self, game):
        super().__init__(game, "moderne")
        
        # Personnalisation de l'époque
        self.epoch_name_display = "ÉPOQUE MODERNE"
        self.theme_color = BLUE
        
        # Messages spécifiques
        self.welcome_message = "En avant, soldats !"
        self.victory_message = "Victoire militaire éclatante !"
        
        # Effets de fumée pour les tirs
        self.smoke_effects = []
        
        # Son de bataille (simulation visuelle)
        self.battle_intensity = 0
    
    def on_enter(self):
        """Appelé quand le joueur entre dans cette salle"""
        print(f"🎖️ {self.welcome_message}")
    
    def on_exit(self):
        """Appelé quand le joueur quitte cette salle"""
        print(f"🏅 {self.victory_message}")
    
    def add_smoke_effect(self, x, y):
        """Ajoute un effet de fumée (pour les tirs d'armes à feu)"""
        self.smoke_effects.append({
            'x': x,
            'y': y,
            'radius': 5,
            'lifetime': 30,
            'alpha': 255
        })
    
    def draw_epoch_decoration(self, surface):
        """Dessine des décorations spécifiques à l'époque"""
        # Titre militaire
        font = pygame.font.Font(None, 30)
        epoch_text = font.render(self.epoch_name_display, True, self.theme_color)
        text_rect = epoch_text.get_rect()
        text_rect.topright = (SCREEN_WIDTH - 20, 50)
        
        # Fond avec style militaire
        bg_rect = text_rect.inflate(40, 20)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.fill(DARK_BLUE)
        bg_surface.set_alpha(200)
        surface.blit(bg_surface, bg_rect)
        
        # Bordure bleue
        pygame.draw.rect(surface, BLUE, bg_rect, 4)
        
        # Étoiles décoratives (grade militaire)
        star_y = text_rect.top - 5
        for i in range(3):
            star_x = text_rect.left - 30 + (i * 12)
            self._draw_star(surface, star_x, star_y, 4, GOLD)
        
        surface.blit(epoch_text, text_rect)
    
    def _draw_star(self, surface, x, y, size, color):
        """Dessine une étoile (symbole militaire)"""
        points = []
        for i in range(5):
            angle = (i * 144 - 90) * 3.14159 / 180
            px = x + size * math.cos(angle)
            py = y + size * math.sin(angle)
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)
    
    def update(self):
        """Mise à jour avec effets de fumée"""
        result = super().update()
        
        # Mise à jour des effets de fumée
        for smoke in self.smoke_effects[:]:
            smoke['lifetime'] -= 1
            smoke['radius'] += 0.5
            smoke['alpha'] = int((smoke['lifetime'] / 30) * 255)
            
            if smoke['lifetime'] <= 0:
                self.smoke_effects.remove(smoke)
        
        # Ajouter de la fumée aléatoire pendant les combats
        if len(self.enemies) > 0 and random.random() < 0.05:
            if len(self.bullets) > 0:
                bullet = list(self.bullets)[0]
                self.add_smoke_effect(bullet.rect.x, bullet.rect.y)
        
        # Intensité de bataille
        self.battle_intensity = len(self.enemies) + len(self.bullets)
        
        return result
    
    def draw(self, surface):
        """Surcharge pour ajouter des éléments visuels spécifiques"""
        super().draw(surface)
        
        # Dessiner les effets de fumée
        for smoke in self.smoke_effects:
            smoke_surface = pygame.Surface((int(smoke['radius'] * 2), int(smoke['radius'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(smoke_surface, (150, 150, 150, smoke['alpha']), 
                             (int(smoke['radius']), int(smoke['radius'])), 
                             int(smoke['radius']))
            surface.blit(smoke_surface, (smoke['x'] - smoke['radius'], smoke['y'] - smoke['radius']))
        
        self.draw_epoch_decoration(surface)
        
        # Message de bienvenue
        if self.wave == 1 and not self.wave_complete and len(self.enemies) > 0:
            font = pygame.font.Font(None, 36)
            welcome = font.render(self.welcome_message, True, BLUE)
            welcome_rect = welcome.get_rect(center=(SCREEN_WIDTH // 2, 150))
            
            bg_rect = welcome_rect.inflate(50, 25)
            pygame.draw.rect(surface, DARK_BLUE, bg_rect)
            pygame.draw.rect(surface, BLUE, bg_rect, 4)
            
            surface.blit(welcome, welcome_rect)
    
    def get_epoch_tips(self):
        """Conseils spécifiques à l'époque"""
        return [
            "🔫 Le Pistolet tire vite et loin",
            "⚔️ La Carabine combine tir et mêlée",
            "💥 Les armes à feu changent le combat",
            "🎯 Gardez vos distances"
        ]