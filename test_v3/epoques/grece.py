# -*- coding: utf-8 -*-
# epoques/grece.py — GRÈCE ANTIQUE (soleil supprimé)
import pygame
import math
from core.base_room import BaseRoom
from core.constants  import *

class GreceRoom(BaseRoom):
    """Salle Grèce Antique. Soleil animé désactivé — draw_epoch_decoration vide."""
    def __init__(self, game):
        super().__init__(game, "grece")
        self.epoch_name_display = "GRÈCE ANTIQUE"
        self.theme_color        = GRECE_COLOR

    def on_enter(self):  print("🏛 Que les dieux vous guident !")
    def on_exit(self):   print("⚡ La gloire de l'Olympe vous appartient !")

    def draw_epoch_decoration(self, surface):
        """
        Aucune décoration active.
        Pour remettre le soleil, décommenter ce qui suit :

        self._sun_angle = getattr(self, '_sun_angle', 0) + 0.005
        cx, cy = int(SCREEN_WIDTH*0.85), 80
        pygame.draw.circle(surface, (255,230,100), (cx,cy), 28)
        for i in range(8):
            a = self._sun_angle + i * math.pi / 4
            x1,y1 = int(cx+math.cos(a)*34), int(cy+math.sin(a)*34)
            x2,y2 = int(cx+math.cos(a)*46), int(cy+math.sin(a)*46)
            pygame.draw.line(surface, (255,210,60), (x1,y1), (x2,y2), 3)
        """
        pass
