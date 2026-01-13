"""
Classe Enemy - Gestion des ennemis
"""

import pygame
import math
from core.constants import *

class Enemy:
    def __init__(self, x, y, enemy_type, wave):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.size = ENEMY_SIZE
        
        # Stats basées sur le type
        stats = ENEMY_TYPES[enemy_type]
        self.health = ENEMY_BASE_HEALTH * stats['health_modifier'] + (wave - 1) * HEALTH_INCREASE_PER_WAVE
        self.max_health = self.health
        self.speed = ENEMY_BASE_SPEED * stats['speed_modifier']
        self.damage = ENEMY_DAMAGE * stats['damage_modifier']
        self.color = stats['color']
        
        # Cooldown d'attaque
        self.last_attack = 0
        self.attack_cooldown = 1000  # millisecondes
        
    def update(self, player, current_time):
        """Met à jour l'ennemi"""
        # Mouvement vers le joueur
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Normaliser
            dx /= distance
            dy /= distance
            
            # Se déplacer
            if self.enemy_type != 'Sniper' or distance > 300:
                self.x += dx * self.speed
                self.y += dy * self.speed
    
    def can_attack(self, player, current_time):
        """Vérifie si l'ennemi peut attaquer"""
        if current_time - self.last_attack < self.attack_cooldown:
            return False
        
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if self.enemy_type == 'Sniper':
            # Attaque à distance
            if distance < 400:
                self.last_attack = current_time
                return True
        else:
            # Attaque au corps à corps
            if distance < ENEMY_ATTACK_RANGE + player.size:
                self.last_attack = current_time
                return True
        
        return False
    
    def take_damage(self, damage):
        """Reçoit des dégâts"""
        self.health -= damage
        return self.health <= 0
    
    def draw(self, screen):
        """Dessine l'ennemi"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        
        # Barre de vie
        bar_width = self.size * 2
        bar_height = 5
        health_ratio = self.health / self.max_health
        
        # Fond rouge
        pygame.draw.rect(screen, RED, 
            (int(self.x - bar_width/2), int(self.y - self.size - 10), 
             bar_width, bar_height))
        
        # Vie verte
        pygame.draw.rect(screen, GREEN,
            (int(self.x - bar_width/2), int(self.y - self.size - 10),
             bar_width * health_ratio, bar_height))