"""
Classe PowerUp - Gestion des power-ups
"""

import pygame
import math
from core.constants import *

class PowerUp:
    def __init__(self, x, y, powerup_type):
        self.x = x
        self.y = y
        self.powerup_type = powerup_type
        self.size = POWERUP_SIZE
        self.color = POWERUP_TYPES[powerup_type]['color']
        
        # Animation
        self.angle = 0
        self.pulse = 0
    
    def check_collision(self, player):
        """Vérifie la collision avec le joueur"""
        dx = self.x - player.x
        dy = self.y - player.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance < self.size + player.size
    
    def draw(self, screen):
        """Dessine le power-up avec animation"""
        self.angle += 5
        self.pulse = abs(math.sin(self.angle * 0.1)) * 5
        
        size = self.size + self.pulse
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(size))
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(size), 2)