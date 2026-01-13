"""
Classe Projectile - Gestion des projectiles
"""

import pygame
import math
from core.constants import *

class Projectile:
    def __init__(self, x, y, dx, dy, damage, is_player_projectile=True):
        self.x = x
        self.y = y
        self.dx = dx * PROJECTILE_SPEED
        self.dy = dy * PROJECTILE_SPEED
        self.damage = damage
        self.is_player_projectile = is_player_projectile
        self.size = PROJECTILE_SIZE
        self.active = True
        
        # Couleur selon l'origine
        if is_player_projectile:
            self.color = YELLOW
        else:
            self.color = RED
    
    def update(self):
        """Met à jour le projectile"""
        self.x += self.dx
        self.y += self.dy
        
        # Désactiver si hors écran
        if (self.x < 0 or self.x > SCREEN_WIDTH or 
            self.y < 0 or self.y > SCREEN_HEIGHT):
            self.active = False
    
    def is_active(self):
        """Vérifie si le projectile est actif"""
        return self.active
    
    def check_collision(self, entity):
        """Vérifie la collision avec une entité"""
        dx = self.x - entity.x
        dy = self.y - entity.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance < self.size + entity.size
    
    def draw(self, screen):
        """Dessine le projectile"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)