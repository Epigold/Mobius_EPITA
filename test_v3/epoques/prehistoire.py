# -*- coding: utf-8 -*-
# epoques/prehistoire.py - ERE PREHISTORIQUE (flammes supprimees)
import pygame
import math
from core.base_room import BaseRoom
from core.constants  import *

class PrehistoireRoom(BaseRoom):
    """Salle prehistorique. Flammes desactivees - draw_epoch_decoration vide."""
    def __init__(self, game):
        super().__init__(game, "prehistoire")
        self.epoch_name_display = "ERE PREHISTORIQUE"
        self.theme_color        = PREHISTOIRE_COLOR

    def on_enter(self):  print("Bienvenue a l'age de pierre !")
    def on_exit(self):   print("L'homme prehistorique evolue !")

    def draw_epoch_decoration(self, surface):
        """
        Aucune decoration active.
        Pour remettre les flammes, decommenter ce qui suit :

        self._fire_timer = getattr(self, '_fire_timer', 0) + 1
        for fx, fy in [(80, SCREEN_HEIGHT-160), (SCREEN_WIDTH-80, SCREEN_HEIGHT-160)]:
            flicker = abs(math.sin(self._fire_timer * 0.15)) * 8
            pygame.draw.polygon(surface, (255,160,30),
                [(fx,fy+22),(fx-8,fy-5-flicker),(fx+8,fy-5-flicker)])
            pygame.draw.polygon(surface, (255,220,80),
                [(fx,fy+14),(fx-4,fy-2-flicker//2),(fx+4,fy-2-flicker//2)])
        """
        pass
