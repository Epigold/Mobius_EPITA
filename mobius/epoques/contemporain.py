# -*- coding: utf-8 -*-
# epoques/contemporain.py

"""
EPOQUE : CONTEMPORAIN (WW2)
Personnage : Soldat WW2
Armes     : AK-47 (distance)  -  Grenade (distance AOE)
Theme     : Jungle, bunker, vert militaire
Difficulte: x2.5
"""

import pygame
import math
import random
from core.base_room import BaseRoom
from core.constants  import *


class ContemporainRoom(BaseRoom):

    def __init__(self, game):
        super().__init__(game, "contemporain")
        self.epoch_name_display = "GUERRE MONDIALE"
        self.theme_color = CONTEMPORAIN_COLOR
        self._rain_drops = [
            {"x": random.randint(0, SCREEN_WIDTH),
             "y": random.randint(0, SCREEN_HEIGHT),
             "speed": random.uniform(8, 14)}
            for _ in range(60)
        ]

    def on_enter(self):
        print("En avant soldats !")

    def on_exit(self):
        print("Victoire ! L'ennemi est vaincu !")

    def draw_epoch_decoration(self, surface):
        # Pluie legere
        for drop in self._rain_drops:
            drop["y"] += drop["speed"]
            if drop["y"] > SCREEN_HEIGHT:
                drop["y"] = -5
                drop["x"] = random.randint(0, SCREEN_WIDTH)
            x1, y1 = int(drop["x"]), int(drop["y"])
            x2, y2 = x1 + 2, int(drop["y"] + 8)
            pygame.draw.line(surface, (120, 140, 160, 120), (x1, y1), (x2, y2), 1)
