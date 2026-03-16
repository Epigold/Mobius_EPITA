# -*- coding: utf-8 -*-
# epoques/grece.py

"""
ÉPOQUE : GRÈCE ANTIQUE
Personnage : Soldat grec · Momie égyptienne
Armes     : Arc (distance) · Crâne (distance)
Thème     : Marbre blanc, or, ciel méditerranéen
Difficulté: ×1.3
"""

import pygame
import math
from core.base_room import BaseRoom
from core.constants  import *


class GreceRoom(BaseRoom):

    def __init__(self, game):
        super().__init__(game, "grece")
        self.epoch_name_display = "GRÈCE ANTIQUE"
        self.theme_color = GRECE_COLOR
        self._sun_angle = 0

    def on_enter(self):
        print("🏛 Que les dieux vous guident !")

    def on_exit(self):
        print("⚡ La gloire de l'Olympe vous appartient !")

    def draw_epoch_decoration(self, surface):
        self._sun_angle += 0.005
        # Soleil stylisé
        cx = int(SCREEN_WIDTH * 0.85)
        cy = 80
        pygame.draw.circle(surface, (255, 230, 100), (cx, cy), 28)
        for i in range(8):
            a = self._sun_angle + i * math.pi / 4
            x1 = int(cx + math.cos(a) * 34)
            y1 = int(cy + math.sin(a) * 34)
            x2 = int(cx + math.cos(a) * 46)
            y2 = int(cy + math.sin(a) * 46)
            pygame.draw.line(surface, (255, 210, 60), (x1, y1), (x2, y2), 3)
