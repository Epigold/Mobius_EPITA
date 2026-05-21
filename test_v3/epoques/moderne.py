# -*- coding: utf-8 -*-
# epoques/moderne.py

"""
EPOQUE : ERE MODERNE
Personnage : Soldat napoleonien
Armes     : Carabine (distance)  -  Couteau (melee)
Theme     : Champ de bataille, fumee, ciel plombe
Difficulte: x2.0
"""

import pygame
import math
import random
from core.base_room import BaseRoom
from core.constants  import *


class ModerneRoom(BaseRoom):

    def __init__(self, game):
        super().__init__(game, "moderne")
        self.epoch_name_display = "ERE MODERNE"
        self.theme_color = MODERNE_COLOR
        self._smoke_puffs = []
        self._smoke_timer = 0

    def on_enter(self):
        print("Pour l'Empereur !")

    def on_exit(self):
        print("La bataille est gagnee !")

    def draw_epoch_decoration(self, surface):
        self._smoke_timer += 1
        # Ajouter des volutes de fumee de canon
        if self._smoke_timer % 45 == 0:
            sx = random.randint(100, SCREEN_WIDTH - 100)
            self._smoke_puffs.append({
                "x": sx, "y": SCREEN_HEIGHT - 160,
                "vy": -0.5, "alpha": 180,
                "r": random.randint(12, 24),
            })

        # Mettre a jour et dessiner
        alive = []
        for puff in self._smoke_puffs:
            puff["y"]     += puff["vy"]
            puff["alpha"] -= 2
            puff["r"]     += 0.15
            if puff["alpha"] > 0:
                smoke = pygame.Surface((int(puff["r"] * 2), int(puff["r"] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(smoke, (120, 110, 100, int(puff["alpha"])),
                                   (int(puff["r"]), int(puff["r"])), int(puff["r"]))
                surface.blit(smoke, (int(puff["x"] - puff["r"]), int(puff["y"] - puff["r"])))
                alive.append(puff)
        self._smoke_puffs = alive
