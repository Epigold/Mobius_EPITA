# -*- coding: utf-8 -*-
# epoques/futuristique.py

"""
EPOQUE : FUTURISTE
Personnage : Demembreur (robot)
Armes     : Pistolet Laser (distance)  -  Minigun (distance rapide)
Theme     : Station spatiale, grille holographique, neons cyan
Difficulte: x3.0
"""

import pygame
import math
import random
from core.base_room import BaseRoom
from core.constants  import *


class FuturistiqueRoom(BaseRoom):

    def __init__(self, game):
        super().__init__(game, "futuristique")
        self.epoch_name_display = "ERE FUTURISTE"
        self.theme_color = FUTURISTIQUE_COLOR
        self._scan_y   = 0
        self._scan_dir = 1
        self._data_particles = []
        self._dp_timer = 0

    def on_enter(self):
        print("Systeme d'armement active...")

    def on_exit(self):
        print("Reseau ennemi neutralise !")

    def draw_epoch_decoration(self, surface):
        # Ligne de scan holographique
        self._scan_y += self._scan_dir * 2
        if self._scan_y > SCREEN_HEIGHT:
            self._scan_dir = -1
        if self._scan_y < 0:
            self._scan_dir = 1

        scan_line = pygame.Surface((SCREEN_WIDTH, 3), pygame.SRCALPHA)
        scan_line.fill((0, 220, 255, 30))
        surface.blit(scan_line, (0, int(self._scan_y)))

        # Particules de donnees flottantes
        self._dp_timer += 1
        if self._dp_timer % 12 == 0:
            self._data_particles.append({
                "x": random.randint(20, SCREEN_WIDTH - 20),
                "y": SCREEN_HEIGHT + 10,
                "vy": -random.uniform(1.5, 3),
                "alpha": 200,
                "char": random.choice("01"),
            })

        font_sm = pygame.font.Font(None, 16)
        alive   = []
        for dp in self._data_particles:
            dp["y"]     += dp["vy"]
            dp["alpha"] -= 3
            if dp["alpha"] > 0:
                txt = font_sm.render(dp["char"], True, (0, 200, 255))
                txt.set_alpha(int(dp["alpha"]))
                surface.blit(txt, (int(dp["x"]), int(dp["y"])))
                alive.append(dp)
        self._data_particles = alive
