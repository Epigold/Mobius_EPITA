# -*- coding: utf-8 -*-
# epoques/edo.py

"""
ÉPOQUE : JAPON EDO
Personnage : Samouraï
Armes     : Katana (mêlée) · Orbe Magique (distance)
Thème     : Nuit japonaise, cerisiers, lune
Difficulté: ×1.6
"""

import pygame
import math
import random
from core.base_room import BaseRoom
from core.constants  import *


class EdoRoom(BaseRoom):

    def __init__(self, game):
        super().__init__(game, "edo")
        self.epoch_name_display = "PÉRIODE EDO"
        self.theme_color = EDO_COLOR
        self._petal_timer = 0
        self._petals = []
        # Générer quelques pétales
        for _ in range(18):
            self._petals.append({
                "x": random.uniform(0, SCREEN_WIDTH),
                "y": random.uniform(0, SCREEN_HEIGHT),
                "vx": random.uniform(-0.4, -0.1),
                "vy": random.uniform(0.3, 0.8),
                "angle": random.uniform(0, 360),
                "rot_speed": random.uniform(-2, 2),
            })

    def on_enter(self):
        print("⚔ Le chemin du bushido commence !")

    def on_exit(self):
        print("🌸 L'honneur du samouraï est sauf !")

    def draw_epoch_decoration(self, surface):
        # Pétales de cerisier animés
        for p in self._petals:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["angle"] += p["rot_speed"]
            if p["y"] > SCREEN_HEIGHT + 10:
                p["y"] = -10
                p["x"] = random.uniform(0, SCREEN_WIDTH)
            if p["x"] < -10:
                p["x"] = SCREEN_WIDTH + 10

            px, py = int(p["x"]), int(p["y"])
            angle  = p["angle"]
            petal  = pygame.Surface((10, 6), pygame.SRCALPHA)
            pygame.draw.ellipse(petal, (220, 100, 140, 180), (0, 0, 10, 6))
            rot    = pygame.transform.rotate(petal, angle)
            surface.blit(rot, (px - rot.get_width() // 2,
                               py - rot.get_height() // 2))
