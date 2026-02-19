# -*- coding: utf-8 -*-
# grece.py - Salle de l'époque Grèce Antique

"""
ÉPOQUE: GRÈCE ANTIQUE
Personnage: Soldat grec (Hoplite)
Armes: Arc (distance), Lance (mêlée)
Thème: Or, architecture grecque
Difficulté: x1.2
"""

from core.base_room import BaseRoom
from core.constants import *
import pygame


class GreceRoom(BaseRoom):
    """
    Salle de l'époque Grèce Antique
    
    Deuxième époque : les armes sont plus puissantes.
    Les ennemis commencent à être plus nombreux.
    """
    
    def __init__(self, game):
        super().__init__(game, "grece")
        
        # Personnalisation de l'époque
        self.epoch_name_display = "GRÈCE ANTIQUE"
        self.theme_color = GOLD
        
        # Messages spécifiques
        self.welcome_message = "Entrez dans l'arène grecque !"
        self.victory_message = "Victoire digne d'un héros grec !"
        
        # Compteur pour effets spéciaux
        self.combat_intensity = 0
    
    def on_enter(self):
        """Appelé quand le joueur entre dans cette salle"""
        print(f"🏛️ {self.welcome_message}")
        # Effet d'entrée: peut-être un flash doré
    
    def on_exit(self):
        """Appelé quand le joueur quitte cette salle"""
        print(f"🏆 {self.victory_message}")
    
    def draw_epoch_decoration(self, surface):
        """Dessine des décorations spécifiques à l'époque"""
        # Titre de l'époque avec style grec
        font = pygame.font.Font(None, 32)
        epoch_text = font.render(self.epoch_name_display, True, self.theme_color)
        text_rect = epoch_text.get_rect()
        text_rect.topright = (SCREEN_WIDTH - 20, 50)
        
        # Fond avec bordure dorée
        bg_rect = text_rect.inflate(30, 15)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.fill(BLACK)
        bg_surface.set_alpha(150)
        surface.blit(bg_surface, bg_rect)
        
        # Bordure dorée
        pygame.draw.rect(surface, GOLD, bg_rect, 3)
        
        surface.blit(epoch_text, text_rect)
        
        # Symbole grec (Omega)
        symbol_font = pygame.font.Font(None, 24)
        omega = symbol_font.render("Ω", True, GOLD)
        surface.blit(omega, (text_rect.left - 25, text_rect.centery - 12))
    
    def draw(self, surface):
        """Surcharge pour ajouter des éléments visuels spécifiques"""
        super().draw(surface)
        self.draw_epoch_decoration(surface)
        
        # Message de bienvenue
        if self.wave == 1 and not self.wave_complete and len(self.enemies) > 0:
            font = pygame.font.Font(None, 32)
            welcome = font.render(self.welcome_message, True, GOLD)
            welcome_rect = welcome.get_rect(center=(SCREEN_WIDTH // 2, 150))
            
            bg_rect = welcome_rect.inflate(40, 20)
            pygame.draw.rect(surface, BLACK, bg_rect)
            pygame.draw.rect(surface, GOLD, bg_rect, 3)
            
            surface.blit(welcome, welcome_rect)
    
    def update(self):
        """Mise à jour avec logique spécifique"""
        result = super().update()
        
        # Intensité du combat (pour effets visuels)
        self.combat_intensity = len(self.enemies)
        
        return result
    
    def get_epoch_tips(self):
        """Conseils spécifiques à l'époque"""
        return [
            "🏹 L'Arc grec est plus puissant que le caillou",
            "🗡️ La Lance a une meilleure portée que l'os",
            "⚔️ Les ennemis sont plus résistants",
            "🛡️ Utilisez votre compétence (F) stratégiquement"
        ]