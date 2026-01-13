"""
Classe Chest - Gestion des coffres
"""

import pygame
import math
from core.constants import *

class Chest:
    def __init__(self, x, y, item):
        self.x = x
        self.y = y
        self.item = item
        self.size = CHEST_SIZE
        self.opened = False
        self.color = GOLD
    
    def check_collision(self, player):
        """Vérifie si le joueur est proche"""
        dx = self.x - player.x
        dy = self.y - player.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance < CHEST_INTERACTION_RANGE + player.size
    
    def open(self, player):
        """Ouvre le coffre"""
        if not self.opened:
            self.opened = True
            player.add_item(self.item)
            self.color = (100, 100, 100)  # Gris quand ouvert
    
    def draw(self, screen):
        """Dessine le coffre"""
        pygame.draw.rect(screen, self.color, 
            (int(self.x - self.size/2), int(self.y - self.size/2), 
             self.size, self.size))
        
        if not self.opened:
            # Indication "E" pour ouvrir
            font = pygame.font.Font(None, 24)
            text = font.render("E", True, WHITE)
            screen.blit(text, (int(self.x - 8), int(self.y - 50)))