# -*- coding: utf-8 -*-
# prehistoire.py - Salle de l'époque Préhistoire

"""
ÉPOQUE: PRÉHISTOIRE
Personnage: Homme préhistorique
Armes: Caillou (distance), Os (mêlée)
Thème: Brun, environnement primitif
Difficulté: x1.0 (époque de base)
"""

from core.base_room import BaseRoom
from core.constants import *
import pygame


class PrehistoireRoom(BaseRoom):
    """
    Salle de l'époque Préhistoire
    
    Premier niveau du jeu, introduit les mécaniques de base.
    Les ennemis sont moins nombreux et moins résistants.
    """
    
    def __init__(self, game):
        super().__init__(game, "prehistoire")
        
        # Personnalisation de l'époque
        self.epoch_name_display = "ÈRE PRÉHISTORIQUE"
        self.theme_color = BROWN
        
        # Messages spécifiques à l'époque
        self.welcome_message = "Bienvenue à l'âge de pierre !"
        self.victory_message = "L'homme préhistorique évolue !"
        
        # Effets visuels spécifiques (optionnel)
        self.particles = []
    
    def on_enter(self):
        """Appelé quand le joueur entre dans cette salle"""
        print(f"🪨 {self.welcome_message}")
        # Ici vous pouvez ajouter des effets d'entrée spécifiques
    
    def on_exit(self):
        """Appelé quand le joueur quitte cette salle"""
        print(f"✅ {self.victory_message}")
        # Ici vous pouvez ajouter des effets de sortie spécifiques
    
    def draw_epoch_decoration(self, surface):
        """Dessine des décorations spécifiques à l'époque"""
        # Titre de l'époque dans le coin
        font = pygame.font.Font(None, 28)
        epoch_text = font.render(self.epoch_name_display, True, self.theme_color)
        text_rect = epoch_text.get_rect()
        text_rect.topright = (SCREEN_WIDTH - 20, 50)
        
        # Fond semi-transparent
        bg_rect = text_rect.inflate(20, 10)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.fill(BLACK)
        bg_surface.set_alpha(150)
        surface.blit(bg_surface, bg_rect)
        
        # Texte
        surface.blit(epoch_text, text_rect)
    
    def draw(self, surface):
        """Surcharge pour ajouter des éléments visuels spécifiques"""
        # Appel à la méthode de base
        super().draw(surface)
        
        # Ajout des décorations de l'époque
        self.draw_epoch_decoration(surface)
        
        # Message de bienvenue au début
        if self.wave == 1 and not self.wave_complete and len(self.enemies) > 0:
            font = pygame.font.Font(None, 32)
            welcome = font.render(self.welcome_message, True, BROWN)
            welcome_rect = welcome.get_rect(center=(SCREEN_WIDTH // 2, 150))
            
            # Fond
            bg_rect = welcome_rect.inflate(30, 15)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.fill(BLACK)
            bg_surface.set_alpha(200)
            surface.blit(bg_surface, bg_rect)
            
            surface.blit(welcome, welcome_rect)
    
    def get_epoch_tips(self):
        """Retourne des conseils spécifiques à l'époque"""
        return [
            "Utilisez le Caillou pour attaquer à distance",
            "L'Os inflige plus de dégâts en mêlée",
            "Utilisez le Dash (Espace) pour éviter les ennemis",
            "La Stamina se régénère automatiquement"
        ]