# -*- coding: utf-8 -*-
# epoques/prehistoire.py

"""
ÉPOQUE : PRÉHISTOIRE
Personnage : Homme préhistorique
Armes     : Caillou (distance) · Os (mêlée)
Thème     : Brun, grotte, feu
Difficulté: ×1.0
"""

import pygame
import math
from core.base_room import BaseRoom
from core.constants  import *


class PrehistoireRoom(BaseRoom):

    def __init__(self, game):
        super().__init__(game, "prehistoire")
        self.epoch_name_display = "ÈRE PRÉHISTORIQUE"
        self.theme_color = PREHISTOIRE_COLOR
        self._fire_timer = 0   # animation torches

    def on_enter(self):
        print("🪨 Bienvenue à l'âge de pierre !")

    def on_exit(self):
        print("✅ L'homme préhistorique évolue !")

    def draw_epoch_decoration(self, surface):
        self._fire_timer += 1
        # Petites flammes aux coins (animations)
        for fx, fy in [(80, SCREEN_HEIGHT - 160), (SCREEN_WIDTH - 80, SCREEN_HEIGHT - 160)]:
            flicker = abs(math.sin(self._fire_timer * 0.15)) * 8
            pygame.draw.polygon(surface, (255, 160, 30),
                                [(fx, fy + 22), (fx - 8, fy - 5 - flicker),
                                 (fx + 8, fy - 5 - flicker)])
            pygame.draw.polygon(surface, (255, 220, 80),
                                [(fx, fy + 14), (fx - 4, fy - 2 - flicker // 2),
                                 (fx + 4, fy - 2 - flicker // 2)])
