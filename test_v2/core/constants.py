# -*- coding: utf-8 -*-
# constants.py - Constantes du jeu Mobius Roguelike

import pygame
from pathlib import Path

# Initialisation de Pygame pour obtenir les infos d'écran
pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h

# ============= COULEURS =============
WHITE = (255, 255, 255)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
DARK_RED = (100, 0, 0)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
DARK_BLUE = (30, 80, 150)
ORANGE = (255, 165, 0)
PURPLE = (150, 50, 200)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
GOLD = (255, 215, 0)
CYAN = (0, 255, 255)
GRAY = (128, 128, 128)
SILVER = (192, 192, 192)
DARK_GREEN = (0, 100, 0)

# ============= TAILLES =============
TAILLE_PERSO = 80
TAILLE_ARME = 50
TAILLE_TANK = 120
TAILLE_RUSHER = 70
TAILLE_SNIPER = 90
TAILLE_BOSS = 200

# ============= PARAMÈTRES JOUEUR =============
DASH_SPEED = 20
DASH_TIME = 10
DASH_COOLDOWN = 30
DASH_STAMINA_COST = 15

# ============= ÉTATS DU JEU =============
MENU = 0
PLAYING = 1
GAME_OVER = 2
ROOM_TRANSITION = 3

# ============= MODE DÉVELOPPEMENT =============
PROTOTYPE_MODE = True

# ============= GESTION DES CHEMINS =============
BASE_PATH = Path(__file__).parent
ASSETS_PATH = BASE_PATH / "assets"
CHARACTERS_PATH = ASSETS_PATH / "characteres"
BACKGROUNDS_PATH = ASSETS_PATH / "backgrounds"
WEAPONS_PATH = ASSETS_PATH / "weapons"

def get_asset_path(*parts):
    """Construit un chemin d'asset de manière portable"""
    return str(BASE_PATH / "assets" / Path(*parts))

# ============= DÉFINITION DES ARMES PAR ÉPOQUE =============
WEAPONS_DATA = {
    # PRÉHISTOIRE
    "caillou": {
        "name": "Caillou",
        "epoch": "prehistoire",
        "image_path": ("weapons", "caillou_dj_1.png"),
        "type": "ranged",
        "damage": 40,
        "stamina_cost": 1,
        "cooldown": 15,
        "projectile_speed": 18,
        "size": 50
    },
    "os": {
        "name": "Os",
        "epoch": "prehistoire",
        "image_path": ("weapons", "os_dj_1.png"),
        "type": "melee",
        "damage": 80,
        "stamina_cost": 3,
        "cooldown": 25,
        "range": 120,
        "size": 60
    },
    
    # GRÈCE ANTIQUE
    "arc": {
        "name": "Arc",
        "epoch": "grece",
        "image_path": ("weapons", "caillou_dj_1.png"),
        "type": "ranged",
        "damage": 60,
        "stamina_cost": 2,
        "cooldown": 20,
        "projectile_speed": 25,
        "size": 50
    },
    "lance": {
        "name": "Lance",
        "epoch": "grece",
        "image_path": ("weapons", "os_dj_1.png"),
        "type": "melee",
        "damage": 100,
        "stamina_cost": 4,
        "cooldown": 30,
        "range": 150,
        "size": 70
    },
    
    # EDO
    "katana": {
        "name": "Katana",
        "epoch": "edo",
        "image_path": ("weapons", "os_dj_1.png"),
        "type": "melee",
        "damage": 120,
        "stamina_cost": 3,
        "cooldown": 20,
        "range": 130,
        "size": 65
    },
    "shuriken": {
        "name": "Shuriken",
        "epoch": "edo",
        "image_path": ("weapons", "caillou_dj_1.png"),
        "type": "ranged",
        "damage": 50,
        "stamina_cost": 1,
        "cooldown": 10,
        "projectile_speed": 30,
        "size": 40
    },
    
    # MODERNE
    "carabine": {
        "name": "Carabine à Baïonnette",
        "epoch": "moderne",
        "image_path": ("weapons", "os_dj_1.png"),
        "type": "melee",
        "damage": 140,
        "stamina_cost": 5,
        "cooldown": 35,
        "range": 140,
        "size": 80
    },
    "pistolet": {
        "name": "Pistolet",
        "epoch": "moderne",
        "image_path": ("weapons", "caillou_dj_1.png"),
        "type": "ranged",
        "damage": 80,
        "stamina_cost": 2,
        "cooldown": 18,
        "projectile_speed": 35,
        "size": 45
    },
    
    # CONTEMPORAIN
    "ak47": {
        "name": "AK-47",
        "epoch": "contemporain",
        "image_path": ("weapons", "caillou_dj_1.png"),
        "type": "ranged",
        "damage": 100,
        "stamina_cost": 3,
        "cooldown": 12,
        "projectile_speed": 40,
        "size": 55
    },
    "baionnette": {
        "name": "Baïonnette",
        "epoch": "contemporain",
        "image_path": ("weapons", "os_dj_1.png"),
        "type": "melee",
        "damage": 110,
        "stamina_cost": 3,
        "cooldown": 22,
        "range": 125,
        "size": 60
    },
    
    # FUTURISTIQUE
    "laser": {
        "name": "Laser",
        "epoch": "futuristique",
        "image_path": ("weapons", "caillou_dj_1.png"),
        "type": "ranged",
        "damage": 150,
        "stamina_cost": 4,
        "cooldown": 15,
        "projectile_speed": 50,
        "size": 50
    },
    "sabre_plasma": {
        "name": "Sabre Plasma",
        "epoch": "futuristique",
        "image_path": ("weapons", "os_dj_1.png"),
        "type": "melee",
        "damage": 180,
        "stamina_cost": 5,
        "cooldown": 25,
        "range": 135,
        "size": 70
    }
}

# ============= DÉFINITION DES ÉPOQUES =============
EPOCHS = {
    "prehistoire": {
        "name": "Préhistoire",
        "player_type": "homme_prehistorique",
        "weapons": ["caillou", "os"],
        "background": "decor_dj_1.jpg",
        "enemy_image": "monstre_dj_1.png",
        "color_theme": BROWN,
        "wave_multiplier": 1.0,
        "next_epoch": "grece"
    },
    "grece": {
        "name": "Grèce Antique",
        "player_type": "soldat_grec",
        "weapons": ["arc", "lance"],
        "background": "decor_dj_1.jpg",
        "enemy_image": "monstre_dj_1.png",
        "color_theme": GOLD,
        "wave_multiplier": 1.2,
        "next_epoch": "edo"
    },
    "edo": {
        "name": "Japon Edo",
        "player_type": "samurai",
        "weapons": ["katana", "shuriken"],
        "background": "decor_dj_1.jpg",
        "enemy_image": "monstre_dj_1.png",
        "color_theme": RED,
        "wave_multiplier": 1.5,
        "next_epoch": "moderne"
    },
    "moderne": {
        "name": "Époque Moderne",
        "player_type": "soldat_napoleonien",
        "weapons": ["carabine", "pistolet"],
        "background": "decor_dj_1.jpg",
        "enemy_image": "monstre_dj_1.png",
        "color_theme": BLUE,
        "wave_multiplier": 1.8,
        "next_epoch": "contemporain"
    },
    "contemporain": {
        "name": "Époque Contemporaine",
        "player_type": "soldat_ww2",
        "weapons": ["ak47", "baionnette"],
        "background": "decor_dj_1.jpg",
        "enemy_image": "monstre_dj_1.png",
        "color_theme": GRAY,
        "wave_multiplier": 2.2,
        "next_epoch": "futuristique"
    },
    "futuristique": {
        "name": "Futur",
        "player_type": "demembreur",
        "weapons": ["laser", "sabre_plasma"],
        "background": "decor_dj_1.jpg",
        "enemy_image": "monstre_dj_1.png",
        "color_theme": CYAN,
        "wave_multiplier": 2.5,
        "next_epoch": None
    }
}

# ============= COMPÉTENCES =============
SKILLS = {
    "tank": {
        "name": "Tank",
        "desc": "150 PV, -30% vitesse",
        "special": "Bouclier -50% dégâts",
        "color": BLUE
    },
    "berserker": {
        "name": "Berserker", 
        "desc": "80 PV, +30% vitesse",
        "special": "Rage x2 dégâts 5s",
        "color": RED
    },
    "vampire": {
        "name": "Vampire",
        "desc": "Stats normales",
        "special": "+10 PV par kill 10s",
        "color": PURPLE
    },
    "ninja": {
        "name": "Ninja",
        "desc": "+15% vitesse, Dash CD/2",
        "special": "Téléportation souris",
        "color": BLACK
    },
    "mage": {
        "name": "Mage",
        "desc": "150 Stamina, +50% regen",
        "special": "Nova de projectiles",
        "color": CYAN
    }
}

# ============= PARAMÈTRES DE JEU =============
WAVES_PER_EPOCH = 3  # Nombre de vagues avant de changer d'époque