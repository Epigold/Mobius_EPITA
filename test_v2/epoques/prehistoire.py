# -*- coding: utf-8 -*-
# epoques/prehistoire.py

"""
ÉPOQUE : PRÉHISTOIRE
Personnage : Homme préhistorique
Armes     : Caillou (distance) · Os (mêlée)
Thème     : Brun, grotte, feu
Difficulté: ×1.0

Graphismes :
  • Sprites PNG propres (fond transparent) depuis assets/sprites_prehistoire/
  • AnimController : idle 4f · walk 4f · run 6f interpolées · dash · hurt
  • Personnage toujours orienté vers la souris (flip horizontal)
  • Arme rotative pointée vers le curseur
"""

import pygame
import math
from core.base_room  import BaseRoom
from core.constants  import *
from core.player_anim import (patch_player_for_prehistoire,
                               draw_weapon_hand,
                               PrehistoireSprites)


class PrehistoireRoom(BaseRoom):

    def __init__(self, game):
        super().__init__(game, "prehistoire")
        self.epoch_name_display = "ÈRE PRÉHISTORIQUE"
        self.theme_color        = PREHISTOIRE_COLOR
        self._fire_timer        = 0
        # Pré-charge les sprites au démarrage
        self._prehist_sprites   = None   # chargé au premier start()

    # ── Hooks ────────────────────────────────────────────────────────────────

    def on_enter(self):
        print("🪨 Bienvenue à l'âge de pierre !")

    def on_exit(self):
        print("✅ L'homme préhistorique évolue !")

    # ── Surcharge start() pour patcher le joueur ─────────────────────────────

    def start(self, skill_or_data, player_stats=None):
        super().start(skill_or_data, player_stats)
        # Charger sprites (une seule fois grâce au singleton)
        self._prehist_sprites = PrehistoireSprites.get()
        # Patcher le joueur avec le système d'animation
        patch_player_for_prehistoire(self.player)

    # ── Surcharge draw() pour le rendu de l'arme ────────────────────────────

    def draw(self, surface):
        # Rendu de base (background, sprites, HUD…)
        super().draw(surface)

        # Arme dans la main (par-dessus le HUD, juste devant le perso)
        if self.player and self._prehist_sprites:
            wk = self.player.current_weapon.key if self.player.current_weapon else "rock"
            draw_weapon_hand(
                surface,
                self.player.rect,
                wk,
                self.player.facing_right,
                self._prehist_sprites,
            )

    # ── Décorations époque ───────────────────────────────────────────────────

    def draw_epoch_decoration(self, surface):
        self._fire_timer += 1
        for fx, fy in [(80, SCREEN_HEIGHT - 160), (SCREEN_WIDTH - 80, SCREEN_HEIGHT - 160)]:
            flicker = abs(math.sin(self._fire_timer * 0.15)) * 8
            pygame.draw.polygon(surface, (255, 160, 30),
                                [(fx, fy + 22), (fx - 8, fy - 5 - flicker),
                                 (fx + 8, fy - 5 - flicker)])
            pygame.draw.polygon(surface, (255, 220, 80),
                                [(fx, fy + 14), (fx - 4, fy - 2 - flicker // 2),
                                 (fx + 4, fy - 2 - flicker // 2)])
