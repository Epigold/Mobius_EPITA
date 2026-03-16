# -*- coding: utf-8 -*-
# core/constants.py - Constantes globales du jeu Mobius Roguelike

import pygame
from pathlib import Path

# ──────────────────────────────────────────────────
#  CHEMINS
# ──────────────────────────────────────────────────
BASE_PATH   = Path(__file__).parent.parent
ASSETS_PATH = BASE_PATH / "assets"

def get_asset_path(*parts):
    return str(ASSETS_PATH / Path(*parts))

# ──────────────────────────────────────────────────
#  RÉSOLUTION  (récupérée dynamiquement)
# ──────────────────────────────────────────────────
_info = None
def _get_info():
    global _info
    if _info is None:
        pygame.display.init()
        _info = pygame.display.Info()
    return _info

def _w():  return _get_info().current_w
def _h():  return _get_info().current_h

# Accès direct (résolu à l'import si pygame déjà init, sinon appelé plus tard)
try:
    pygame.display.init()
    _di = pygame.display.Info()
    SCREEN_WIDTH  = _di.current_w
    SCREEN_HEIGHT = _di.current_h
except Exception:
    SCREEN_WIDTH  = 1920
    SCREEN_HEIGHT = 1080

# ──────────────────────────────────────────────────
#  COULEURS
# ──────────────────────────────────────────────────
WHITE        = (255, 255, 255)
BLACK        = (  0,   0,   0)
RED          = (200,   0,   0)
DARK_RED     = (100,   0,   0)
GREEN        = (  0, 200,   0)
DARK_GREEN   = (  0, 100,   0)
BLUE         = ( 50, 150, 255)
DARK_BLUE    = ( 20,  60, 130)
ORANGE       = (255, 165,   0)
PURPLE       = (150,  50, 200)
YELLOW       = (255, 255,   0)
BROWN        = (139,  69,  19)
DARK_BROWN   = ( 80,  40,  10)
GOLD         = (255, 215,   0)
CYAN         = (  0, 255, 255)
TEAL         = (  0, 180, 160)
GRAY         = (128, 128, 128)
DARK_GRAY    = ( 50,  50,  50)
LIGHT_GRAY   = (200, 200, 200)
PINK         = (255, 100, 150)

# Couleurs d'époque
PREHISTOIRE_COLOR = (139,  69,  19)   # Brun
GRECE_COLOR       = (200, 180,  80)   # Or grec
EDO_COLOR         = (180,  30,  30)   # Rouge samourai
MODERNE_COLOR     = (  0,  80, 160)   # Bleu napoléonien
CONTEMPORAIN_COLOR= ( 60,  80,  40)   # Vert militaire
FUTURISTIQUE_COLOR= (  0, 220, 255)   # Cyan néon

# ──────────────────────────────────────────────────
#  ÉTATS DU JEU
# ──────────────────────────────────────────────────
MENU      = 0
PLAYING   = 1
GAME_OVER = 2

# ──────────────────────────────────────────────────
#  PARAMÈTRES JOUEUR
# ──────────────────────────────────────────────────
PLAYER_SIZE       = 80
DASH_SPEED        = 20
DASH_TIME         = 10
DASH_COOLDOWN     = 30
DASH_STAMINA_COST = 15

# Tailles ennemis
SIZE_TANK   = 100
SIZE_RUSHER = 65
SIZE_SNIPER = 85
SIZE_BOSS   = 180

# ──────────────────────────────────────────────────
#  COMPÉTENCES (CLASSES)
# ──────────────────────────────────────────────────
SKILLS = {
    "tank": {
        "name": "Tank",
        "desc": "150 PV · Vitesse -30%",
        "special": "⚡ Bouclier -50% dégâts",
        "color": DARK_BLUE,
        "icon_color": BLUE,
    },
    "berserker": {
        "name": "Berserker",
        "desc": "80 PV · Vitesse +30%",
        "special": "⚡ Rage ×2 dégâts 5s",
        "color": DARK_RED,
        "icon_color": RED,
    },
    "vampire": {
        "name": "Vampire",
        "desc": "Stats normales",
        "special": "⚡ +10 PV/kill (10s)",
        "color": (60, 0, 80),
        "icon_color": PURPLE,
    },
    "ninja": {
        "name": "Ninja",
        "desc": "Vitesse +15% · Dash CD/2",
        "special": "⚡ Téléportation curseur",
        "color": (20, 20, 20),
        "icon_color": CYAN,
    },
    "mage": {
        "name": "Mage",
        "desc": "150 Stamina · +50% regen",
        "special": "⚡ Nova de projectiles",
        "color": (10, 40, 70),
        "icon_color": CYAN,
    },
}

# ──────────────────────────────────────────────────
#  ÉPOQUES
# ──────────────────────────────────────────────────
EPOCH_ORDER = ["prehistoire", "grece", "edo", "moderne", "contemporain", "futuristique"]

EPOCHS = {
    "prehistoire": {
        "name":        "Préhistoire",
        "display":     "ÈRE PRÉHISTORIQUE",
        "color":       PREHISTOIRE_COLOR,
        "bg_tint":     (80, 50, 20),
        "difficulty":  1.0,
        "next":        "grece",
        "weapons":     ["rock", "bone"],
        "enemy_tint":  (180, 120, 60),
        "description": "L'ère des premiers hommes",
    },
    "grece": {
        "name":        "Grèce Antique",
        "display":     "GRÈCE ANTIQUE",
        "color":       GRECE_COLOR,
        "bg_tint":     (200, 180, 100),
        "difficulty":  1.3,
        "next":        "edo",
        "weapons":     ["bow_shoot", "skull"],
        "enemy_tint":  (220, 200, 140),
        "description": "Soldats et mythes de l'Olympe",
    },
    "edo": {
        "name":        "Japon Edo",
        "display":     "PÉRIODE EDO",
        "color":       EDO_COLOR,
        "bg_tint":     (120, 20, 20),
        "difficulty":  1.6,
        "next":        "moderne",
        "weapons":     ["katana", "magic_orb"],
        "enemy_tint":  (200, 100, 80),
        "description": "L'art du sabre et de la magie",
    },
    "moderne": {
        "name":        "Ère Moderne",
        "display":     "ÈRE MODERNE",
        "color":       MODERNE_COLOR,
        "bg_tint":     (30, 60, 120),
        "difficulty":  2.0,
        "next":        "contemporain",
        "weapons":     ["rifle", "dagger"],
        "enemy_tint":  (80, 100, 180),
        "description": "Guerres napoléoniennes",
    },
    "contemporain": {
        "name":        "Époque Contemporaine",
        "display":     "GUERRE MONDIALE",
        "color":       CONTEMPORAIN_COLOR,
        "bg_tint":     (40, 60, 30),
        "difficulty":  2.5,
        "next":        "futuristique",
        "weapons":     ["ak47", "grenade"],
        "enemy_tint":  (80, 110, 60),
        "description": "Conflit mondial, armes lourdes",
    },
    "futuristique": {
        "name":        "Futur",
        "display":     "ÈRE FUTURISTE",
        "color":       FUTURISTIQUE_COLOR,
        "bg_tint":     (0, 40, 80),
        "difficulty":  3.0,
        "next":        None,
        "weapons":     ["laser_pistol", "minigun"],
        "enemy_tint":  (0, 180, 220),
        "description": "Robots et technologies avancées",
    },
}

# ──────────────────────────────────────────────────
#  DONNÉES DES ARMES
# ──────────────────────────────────────────────────
WEAPONS_DATA = {
    # ── Préhistoire ──────────────────────────────
    "rock": {
        "name":              "Caillou",
        "sprite":            ("sprites_final", "rock.png"),
        "fallback_color":    GRAY,
        "type":              "ranged",
        "damage":            35,
        "stamina_cost":      1,
        "cooldown":          18,
        "projectile_speed":  16,
        "size":              42,
    },
    "bone": {
        "name":              "Os",
        "sprite":            ("sprites_final", "bone.png"),
        "fallback_color":    (230, 210, 180),
        "type":              "melee",
        "damage":            75,
        "stamina_cost":      3,
        "cooldown":          25,
        "range":             110,
        "size":              55,
    },
    # ── Grèce ────────────────────────────────────
    "bow_shoot": {
        "name":              "Arc",
        "sprite":            ("sprites_final", "bow_shoot.png"),
        "fallback_color":    BROWN,
        "type":              "ranged",
        "damage":            55,
        "stamina_cost":      2,
        "cooldown":          22,
        "projectile_speed":  22,
        "size":              60,
    },
    "skull": {
        "name":              "Crâne",
        "sprite":            ("sprites_final", "skull.png"),
        "fallback_color":    (220, 200, 180),
        "type":              "ranged",
        "damage":            45,
        "stamina_cost":      2,
        "cooldown":          20,
        "projectile_speed":  14,
        "size":              48,
    },
    # ── Edo ──────────────────────────────────────
    "katana": {
        "name":              "Katana",
        "sprite":            ("sprites_final", "katana.png"),
        "fallback_color":    LIGHT_GRAY,
        "type":              "melee",
        "damage":            95,
        "stamina_cost":      4,
        "cooldown":          20,
        "range":             130,
        "size":              70,
    },
    "magic_orb": {
        "name":              "Orbe Magique",
        "sprite":            ("sprites_final", "magic_orb.png"),
        "fallback_color":    TEAL,
        "type":              "ranged",
        "damage":            70,
        "stamina_cost":      5,
        "cooldown":          30,
        "projectile_speed":  18,
        "size":              50,
    },
    # ── Moderne ──────────────────────────────────
    "rifle": {
        "name":              "Carabine",
        "sprite":            ("sprites_final", "rifle.png"),
        "fallback_color":    BROWN,
        "type":              "ranged",
        "damage":            80,
        "stamina_cost":      2,
        "cooldown":          20,
        "projectile_speed":  28,
        "size":              75,
    },
    "dagger": {
        "name":              "Couteau",
        "sprite":            ("sprites_final", "dagger.png"),
        "fallback_color":    LIGHT_GRAY,
        "type":              "melee",
        "damage":            60,
        "stamina_cost":      2,
        "cooldown":          15,
        "range":             100,
        "size":              50,
    },
    # ── Contemporain ─────────────────────────────
    "ak47": {
        "name":              "AK-47",
        "sprite":            ("sprites_final", "ak47.png"),
        "fallback_color":    DARK_GRAY,
        "type":              "ranged",
        "damage":            65,
        "stamina_cost":      1,
        "cooldown":          8,
        "projectile_speed":  32,
        "size":              75,
    },
    "grenade": {
        "name":              "Grenade",
        "sprite":            ("sprites_final", "grenade.png"),
        "fallback_color":    DARK_GREEN,
        "type":              "ranged",
        "damage":            150,
        "stamina_cost":      8,
        "cooldown":          60,
        "projectile_speed":  12,
        "size":              40,
    },
    # ── Futuristique ─────────────────────────────
    "laser_pistol": {
        "name":              "Pistolet Laser",
        "sprite":            ("sprites_final", "laser_pistol.png"),
        "fallback_color":    CYAN,
        "type":              "ranged",
        "damage":            90,
        "stamina_cost":      2,
        "cooldown":          12,
        "projectile_speed":  38,
        "size":              55,
    },
    "minigun": {
        "name":              "Minigun",
        "sprite":            ("sprites_final", "minigun.png"),
        "fallback_color":    TEAL,
        "type":              "ranged",
        "damage":            50,
        "stamina_cost":      1,
        "cooldown":          4,
        "projectile_speed":  35,
        "size":              85,
    },
}

# ──────────────────────────────────────────────────
#  DONNÉES DES ENNEMIS PAR ÉPOQUE
# ──────────────────────────────────────────────────
ENEMY_CONFIG = {
    "prehistoire": {
        "tank":   {"health": 200, "speed": 2.5, "damage": 15, "size": 95},
        "rusher": {"health":  55, "speed": 7.5, "damage":  8, "size": 60},
        "sniper": {"health":  90, "speed": 3.5, "damage": 10, "size": 75},
        "boss":   {"health": 900, "speed": 4,   "damage": 22, "size": 170},
    },
    "grece": {
        "tank":   {"health": 280, "speed": 3,   "damage": 18, "size": 100},
        "rusher": {"health":  70, "speed": 8.5, "damage": 10, "size": 62},
        "sniper": {"health": 110, "speed": 4,   "damage": 13, "size": 80},
        "boss":   {"health":1200, "speed": 5,   "damage": 26, "size": 180},
    },
    "edo": {
        "tank":   {"health": 350, "speed": 3,   "damage": 22, "size": 100},
        "rusher": {"health":  85, "speed": 10,  "damage": 12, "size": 62},
        "sniper": {"health": 130, "speed": 4.5, "damage": 16, "size": 80},
        "boss":   {"health":1500, "speed": 6,   "damage": 30, "size": 185},
    },
    "moderne": {
        "tank":   {"health": 450, "speed": 3.5, "damage": 25, "size": 100},
        "rusher": {"health": 100, "speed": 11,  "damage": 14, "size": 62},
        "sniper": {"health": 150, "speed": 5,   "damage": 20, "size": 80},
        "boss":   {"health":1800, "speed": 6,   "damage": 35, "size": 185},
    },
    "contemporain": {
        "tank":   {"health": 550, "speed": 4,   "damage": 30, "size": 105},
        "rusher": {"health": 120, "speed": 12,  "damage": 18, "size": 65},
        "sniper": {"health": 180, "speed": 5.5, "damage": 24, "size": 82},
        "boss":   {"health":2200, "speed": 7,   "damage": 40, "size": 190},
    },
    "futuristique": {
        "tank":   {"health": 700, "speed": 4.5, "damage": 38, "size": 110},
        "rusher": {"health": 150, "speed": 14,  "damage": 22, "size": 68},
        "sniper": {"health": 220, "speed": 6,   "damage": 30, "size": 85},
        "boss":   {"health":3000, "speed": 8,   "damage": 50, "size": 200},
    },
}
