"""
Constantes globales du jeu Mobius
"""

import pygame

# Paramètres d'écran
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Résolution de référence (pour le scaling des assets)
REFERENCE_WIDTH = 1280
REFERENCE_HEIGHT = 720

# Calcul du facteur d'échelle basé sur la résolution
# Ce facteur sera utilisé pour adapter tous les assets à la taille de l'écran
SCALE_FACTOR = min(SCREEN_WIDTH / REFERENCE_WIDTH, SCREEN_HEIGHT / REFERENCE_HEIGHT)

# Couleurs
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GOLD = (255, 215, 0)
PURPLE = (128, 0, 128)
DARK_RED = (139, 0, 0)
ORANGE = (255, 165, 0)

# Fonction utilitaire pour adapter les tailles aux résolutions
def scale_size(size):
    """Adapte une taille en fonction de la résolution de l'écran"""
    return int(size * SCALE_FACTOR)

# Paramètres du joueur
PLAYER_SIZE = scale_size(40)
PLAYER_BASE_SPEED = 5
PLAYER_BASE_HEALTH = 100
PLAYER_BASE_STAMINA = 100
STAMINA_REGEN = 1
DASH_COST = 30
DASH_COOLDOWN = 1000  # millisecondes
DASH_SPEED = 15

# Paramètres des projectiles
PROJECTILE_SPEED = 10
PROJECTILE_DAMAGE = 10
PROJECTILE_SIZE = scale_size(8)

# Paramètres des ennemis
ENEMY_SIZE = scale_size(35)
ENEMY_BASE_SPEED = 2
ENEMY_BASE_HEALTH = 50
ENEMY_DAMAGE = 10
ENEMY_ATTACK_RANGE = scale_size(50)

# Paramètres de spawn
SPAWN_MARGIN = scale_size(100)
MIN_SPAWN_DISTANCE = scale_size(150)

# Paramètres des vagues
WAVES_PER_EPOQUE = 5
BOSS_WAVE = 3
ENEMY_INCREASE_PER_WAVE = 2
HEALTH_INCREASE_PER_WAVE = 10

# Paramètres des power-ups
POWERUP_SIZE = scale_size(30)
POWERUP_DURATION = 5000  # millisecondes
POWERUP_SPAWN_CHANCE = 0.15

# Paramètres des coffres
CHEST_SIZE = scale_size(40)
CHEST_INTERACTION_RANGE = scale_size(60)

# Paramètres des armes
WEAPON_RANGE = 50  # pour armes de mêlée
WEAPON_COOLDOWN = 500  # millisecondes

# Stats des classes
CLASS_STATS = {
    'Tank': {
        'health': 150,
        'speed_modifier': 0.7,
        'stamina': 100,
        'special_cooldown': 10000
    },
    'Berserker': {
        'health': 80,
        'speed_modifier': 1.3,
        'stamina': 100,
        'special_cooldown': 8000
    },
    'Vampire': {
        'health': 100,
        'speed_modifier': 1.0,
        'stamina': 100,
        'special_cooldown': 15000
    },
    'Ninja': {
        'health': 100,
        'speed_modifier': 1.15,
        'stamina': 100,
        'special_cooldown': 5000
    },
    'Mage': {
        'health': 100,
        'speed_modifier': 1.0,
        'stamina': 150,
        'special_cooldown': 12000
    }
}

# Types d'ennemis
ENEMY_TYPES = {
    'Tank': {
        'health_modifier': 2.0,
        'speed_modifier': 0.5,
        'damage_modifier': 1.5,
        'color': BLUE
    },
    'Rusher': {
        'health_modifier': 0.7,
        'speed_modifier': 2.0,
        'damage_modifier': 0.8,
        'color': ORANGE
    },
    'Sniper': {
        'health_modifier': 0.8,
        'speed_modifier': 0.8,
        'damage_modifier': 1.2,
        'color': PURPLE
    }
}

# Types de power-ups
POWERUP_TYPES = {
    'damage': {
        'color': RED,
        'multiplier': 2.0
    },
    'speed': {
        'color': GREEN,
        'multiplier': 1.5
    },
    'health': {
        'color': (255, 100, 100),
        'amount': 30
    },
    'stamina': {
        'color': YELLOW,
        'multiplier': 2.0
    }
}