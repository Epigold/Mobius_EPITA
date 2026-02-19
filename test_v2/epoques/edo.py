# -*- coding: utf-8 -*-
# edo.py - Salle de l'époque Japon Edo

"""
ÉPOQUE: JAPON EDO (ÈRE FÉODALE)
Personnage: Samouraï
Armes: Katana (mêlée), Shuriken (distance)
Thème: Rouge, architecture japonaise
Difficulté: x1.5
"""

from core.base_room import BaseRoom
from core.constants import *
import pygame
import math


class EdoRoom(BaseRoom):
    """
    Salle de l'époque Japon Edo
    
    Troisième époque : le combat devient plus intense.
    Les armes japonaises sont rapides et précises.
    """
    
    def __init__(self, game):
        super().__init__(game, "edo")
        
        # Personnalisation de l'époque
        self.epoch_name_display = "ÈRE EDO - JAPON"
        self.theme_color = RED
        
        # Messages spécifiques
        self.welcome_message = "Le chemin du samouraï commence..."
        self.victory_message = "Honneur et gloire au samouraï !"
        
        # Effets visuels japonais
        self.cherry_blossoms = []
        self.wind_effect = 0
    
    def on_enter(self):
        """Appelé quand le joueur entre dans cette salle"""
        print(f"🗾 {self.welcome_message}")
        # Peut générer des pétales de cerisier
        self._generate_cherry_blossoms()
    
    def _generate_cherry_blossoms(self):
        """Génère des pétales de cerisier pour l'ambiance"""
        import random
        for _ in range(20):
            self.cherry_blossoms.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(-100, SCREEN_HEIGHT),
                'speed': random.uniform(0.5, 2.0),
                'size': random.randint(3, 6)
            })
    
    def on_exit(self):
        """Appelé quand le joueur quitte cette salle"""
        print(f"⛩️ {self.victory_message}")
    
    def draw_epoch_decoration(self, surface):
        """Dessine des décorations spécifiques à l'époque"""
        # Titre avec style japonais
        font = pygame.font.Font(None, 30)
        epoch_text = font.render(self.epoch_name_display, True, self.theme_color)
        text_rect = epoch_text.get_rect()
        text_rect.topright = (SCREEN_WIDTH - 20, 50)
        
        # Fond noir avec bordure rouge
        bg_rect = text_rect.inflate(35, 18)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.fill(BLACK)
        bg_surface.set_alpha(180)
        surface.blit(bg_surface, bg_rect)
        
        # Double bordure (style japonais)
        pygame.draw.rect(surface, RED, bg_rect, 3)
        inner_rect = bg_rect.inflate(-6, -6)
        pygame.draw.rect(surface, DARK_RED, inner_rect, 1)
        
        surface.blit(epoch_text, text_rect)
        
        # Symbole japonais (Kanji stylisé - représenté par un cercle rouge)
        pygame.draw.circle(surface, RED, (text_rect.left - 20, text_rect.centery), 10, 2)
    
    def update(self):
        """Mise à jour avec effets de vent"""
        result = super().update()
        
        # Animation du vent
        self.wind_effect = (self.wind_effect + 0.05) % (2 * math.pi)
        
        # Mise à jour des pétales de cerisier
        for petal in self.cherry_blossoms:
            petal['y'] += petal['speed']
            petal['x'] += math.sin(self.wind_effect) * 0.5
            
            # Réinitialiser si hors écran
            if petal['y'] > SCREEN_HEIGHT:
                petal['y'] = -10
                import random
                petal['x'] = random.randint(0, SCREEN_WIDTH)
        
        return result
    
    def draw(self, surface):
        """Surcharge pour ajouter des éléments visuels spécifiques"""
        super().draw(surface)
        
        # Dessiner les pétales de cerisier
        for petal in self.cherry_blossoms:
            # Pétale rose pâle
            petal_color = (255, 182, 193)
            pygame.draw.circle(surface, petal_color, 
                             (int(petal['x']), int(petal['y'])), 
                             petal['size'])
        
        self.draw_epoch_decoration(surface)
        
        # Message de bienvenue
        if self.wave == 1 and not self.wave_complete and len(self.enemies) > 0:
            font = pygame.font.Font(None, 32)
            welcome = font.render(self.welcome_message, True, RED)
            welcome_rect = welcome.get_rect(center=(SCREEN_WIDTH // 2, 150))
            
            bg_rect = welcome_rect.inflate(40, 20)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.fill(BLACK)
            bg_surface.set_alpha(200)
            surface.blit(bg_surface, bg_rect)
            
            pygame.draw.rect(surface, RED, bg_rect, 3)
            surface.blit(welcome, welcome_rect)
    
    def get_epoch_tips(self):
        """Conseils spécifiques à l'époque"""
        return [
            "⚔️ Le Katana est rapide et puissant",
            "🌟 Les Shuriken sont très rapides",
            "🎯 La précision est la clé du samouraï",
            "🌸 Restez calme face à l'adversité"
        ]