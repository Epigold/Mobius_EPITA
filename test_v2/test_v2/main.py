# -*- coding: utf-8 -*-
# main.py - Mobius Roguelike  —  Fichier principal

import pygame
import sys
import math
import random
from core.constants import *
from core.graphics  import SpriteCache, BackgroundRenderer, ScreenEffects

from epoques.prehistoire   import PrehistoireRoom
from epoques.grece         import GreceRoom
from epoques.edo           import EdoRoom
from epoques.moderne       import ModerneRoom
from epoques.contemporain  import ContemporainRoom
from epoques.futuristique  import FuturistiqueRoom


# ══════════════════════════════════════════════════════════════════════════════
#  MENU RENDERER
# ══════════════════════════════════════════════════════════════════════════════

class MenuRenderer:
    """Rendu du menu de sélection de classe avec cartes animées."""

    CARD_W = 210
    CARD_H = 280

    def __init__(self, screen_w, screen_h, bg):
        self.w, self.h = screen_w, screen_h
        self.bg        = bg
        self.font_xl   = pygame.font.Font(None, 80)
        self.font_lg   = pygame.font.Font(None, 44)
        self.font_md   = pygame.font.Font(None, 28)
        self.font_sm   = pygame.font.Font(None, 22)
        self._timer    = 0
        self._particles = []

        # Pré-build les cartes
        self._card_surfs = {}
        for key, skill in SKILLS.items():
            self._card_surfs[key] = self._build_card(skill)

        # Particules de fond
        for _ in range(40):
            self._particles.append({
                "x": random.uniform(0, screen_w),
                "y": random.uniform(0, screen_h),
                "vx": random.uniform(-0.3, 0.3),
                "vy": random.uniform(-0.5, -0.1),
                "r":  random.randint(2, 5),
                "alpha": random.randint(60, 180),
            })

    def _build_card(self, skill):
        w, h = self.CARD_W, self.CARD_H
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        base_col = skill["color"]
        icon_col = skill["icon_color"]

        # Fond carte avec dégradé simulé
        for y in range(h):
            t = y / h
            r = int(base_col[0] * (1 - t * 0.4) + 10)
            g = int(base_col[1] * (1 - t * 0.4) + 10)
            b = int(base_col[2] * (1 - t * 0.4) + 10)
            pygame.draw.line(surf, (max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)), 200),
                             (0, y), (w, y))

        # Bordure
        pygame.draw.rect(surf, (*icon_col[:3], 200), surf.get_rect(), 2, border_radius=12)

        # Icône centrale (cercle coloré)
        cx, cy_icon = w // 2, 85
        pygame.draw.circle(surf, (*icon_col[:3], 80), (cx, cy_icon), 42)
        pygame.draw.circle(surf, (*icon_col[:3], 220), (cx, cy_icon), 38, 3)

        # Initiale classe
        font_icon = pygame.font.Font(None, 58)
        letter    = font_icon.render(skill["name"][0], True, WHITE)
        surf.blit(letter, (cx - letter.get_width() // 2,
                           cy_icon - letter.get_height() // 2))

        # Nom
        font_name = pygame.font.Font(None, 30)
        name_txt  = font_name.render(skill["name"], True, WHITE)
        surf.blit(name_txt, (cx - name_txt.get_width() // 2, 145))

        # Desc
        font_desc = pygame.font.Font(None, 20)
        desc_txt  = font_desc.render(skill["desc"], True, (200, 200, 200))
        surf.blit(desc_txt, (cx - desc_txt.get_width() // 2, 172))

        # Séparateur
        pygame.draw.line(surf, (*icon_col[:3], 120), (20, 196), (w - 20, 196), 1)

        # Spécial
        special_words = skill["special"].split()
        lines         = []
        line          = ""
        for word in special_words:
            test = (line + " " + word).strip()
            if font_desc.size(test)[0] < w - 24:
                line = test
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)

        for i, l in enumerate(lines):
            lt = font_desc.render(l, True, icon_col)
            surf.blit(lt, (cx - lt.get_width() // 2, 204 + i * 18))

        return surf

    def get_card_rects(self) -> dict:
        """Retourne {skill_key: pygame.Rect} pour la détection des clics."""
        keys    = list(SKILLS.keys())
        spacing = 24
        total_w = len(keys) * self.CARD_W + (len(keys) - 1) * spacing
        sx      = (self.w - total_w) // 2
        y       = self.h // 2 - self.CARD_H // 2 + 20
        rects   = {}
        for i, key in enumerate(keys):
            rects[key] = pygame.Rect(sx + i * (self.CARD_W + spacing), y,
                                     self.CARD_W, self.CARD_H)
        return rects

    def draw(self, surface, selected_skill=None):
        self._timer += 1

        # Fond
        surface.blit(self.bg, (0, 0))

        # Overlay sombre
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 10, 160))
        surface.blit(overlay, (0, 0))

        # Particules flottantes
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["y"] < -10: p["y"] = self.h + 10
            if p["x"] < -10: p["x"] = self.w + 10
            if p["x"] > self.w + 10: p["x"] = -10
            s = pygame.Surface((p["r"] * 2, p["r"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (150, 180, 255, p["alpha"]),
                               (p["r"], p["r"]), p["r"])
            surface.blit(s, (int(p["x"]) - p["r"], int(p["y"]) - p["r"]))

        # Titre avec reflet
        title_y  = int(90 + math.sin(self._timer * 0.03) * 4)
        title    = self.font_xl.render("MOBIUS", True, WHITE)
        sub      = self.font_lg.render("R O G U E L I K E", True, (160, 200, 255))
        t_x      = self.w // 2 - title.get_width() // 2
        s_x      = self.w // 2 - sub.get_width() // 2

        # Reflet atténué
        ref   = pygame.transform.flip(title, False, True)
        ref_s = pygame.Surface(ref.get_size(), pygame.SRCALPHA)
        ref_s.fill((0, 0, 0, 0))
        ref_s.blit(ref, (0, 0))
        ref_s.set_alpha(40)
        surface.blit(ref_s, (t_x, title_y + title.get_height()))

        surface.blit(title, (t_x, title_y))
        surface.blit(sub,   (s_x, title_y + title.get_height() + 6))

        # Sous-titre
        choose = self.font_md.render("Choisissez votre classe", True, (180, 180, 200))
        surface.blit(choose, (self.w // 2 - choose.get_width() // 2,
                               title_y + title.get_height() + sub.get_height() + 22))

        # Cartes
        rects = self.get_card_rects()
        mouse = pygame.mouse.get_pos()

        for key, rect in rects.items():
            is_hover = rect.collidepoint(mouse)
            is_sel   = key == selected_skill

            # Effet hover : carte monte légèrement
            dy = -8 if (is_hover or is_sel) else 0
            draw_y = rect.y + dy

            # Ombre portée
            shadow = pygame.Surface((self.CARD_W + 10, self.CARD_H + 10), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 80))
            surface.blit(shadow, (rect.x - 5 + 4, draw_y - 5 + 6))

            # Carte
            surface.blit(self._card_surfs[key], (rect.x, draw_y))

            # Bordure hover / sélectionnée
            if is_hover or is_sel:
                icon_col = SKILLS[key]["icon_color"]
                pygame.draw.rect(surface, icon_col,
                                 (rect.x, draw_y, self.CARD_W, self.CARD_H),
                                 3, border_radius=12)
                # Glow pulsant
                glow_alpha = int(60 + 40 * math.sin(self._timer * 0.15))
                glow = pygame.Surface((self.CARD_W + 20, self.CARD_H + 20), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*icon_col[:3], glow_alpha),
                                 (0, 0, self.CARD_W + 20, self.CARD_H + 20),
                                 4, border_radius=14)
                surface.blit(glow, (rect.x - 10, draw_y - 10))

            # Numéro
            num = self.font_sm.render(f"[ {list(SKILLS.keys()).index(key) + 1} ]",
                                       True, GOLD if (is_hover or is_sel) else GRAY)
            surface.blit(num, (rect.x + self.CARD_W // 2 - num.get_width() // 2,
                                draw_y + self.CARD_H + 6))

        # Instructions
        inst = self.font_sm.render(
            "Cliquez sur une carte  ·  Touche 1-5  ·  ESC pour quitter",
            True, (140, 140, 160))
        surface.blit(inst, (self.w // 2 - inst.get_width() // 2, self.h - 36))

        # Époque du jeu
        epoch_info = self.font_sm.render(
            "6 ÉPOQUES  ·  Préhistoire → Grèce → Edo → Moderne → WW2 → Futur",
            True, (100, 120, 160))
        surface.blit(epoch_info, (self.w // 2 - epoch_info.get_width() // 2, self.h - 60))


# ══════════════════════════════════════════════════════════════════════════════
#  GAME OVER RENDERER
# ══════════════════════════════════════════════════════════════════════════════

class GameOverRenderer:

    def __init__(self, screen_w, screen_h, bg):
        self.w, self.h = screen_w, screen_h
        self.bg        = bg
        self.font_xl   = pygame.font.Font(None, 90)
        self.font_lg   = pygame.font.Font(None, 46)
        self.font_md   = pygame.font.Font(None, 32)
        self.font_sm   = pygame.font.Font(None, 24)
        self._timer    = 0

    def draw(self, surface, player, epoch_key, victory=False):
        self._timer += 1
        surface.blit(self.bg, (0, 0))

        # Overlay
        ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 190))
        surface.blit(ov, (0, 0))

        cx = self.w // 2
        cy = self.h // 2

        if victory:
            col   = GOLD
            title = "VICTOIRE !"
            sub   = "Vous avez traversé toutes les époques !"
        else:
            col   = RED
            title = "GAME OVER"
            sub   = "L'histoire vous a rattrapé..."

        # Titre avec pulsation
        scale  = 1.0 + 0.03 * math.sin(self._timer * 0.1)
        t_surf = self.font_xl.render(title, True, col)
        t_surf = pygame.transform.scale(
            t_surf, (int(t_surf.get_width() * scale), int(t_surf.get_height() * scale)))
        surface.blit(t_surf, (cx - t_surf.get_width() // 2, cy - 200))

        # Sous-titre
        s_txt = self.font_md.render(sub, True, (200, 200, 220))
        surface.blit(s_txt, (cx - s_txt.get_width() // 2, cy - 120))

        # Séparateur
        sep_alpha = int(150 + 80 * math.sin(self._timer * 0.05))
        sep_col   = (*col[:3], sep_alpha)
        sep_surf  = pygame.Surface((400, 2), pygame.SRCALPHA)
        sep_surf.fill(sep_col)
        surface.blit(sep_surf, (cx - 200, cy - 92))

        # Stats
        if player:
            epoch_name = EPOCHS.get(epoch_key, {}).get("name", epoch_key)
            stats = [
                (f"Époque : {epoch_name}",        (180, 200, 255)),
                (f"Ennemis éliminés : {player.kills}",  WHITE),
                (f"Pièces collectées : {player.coins}",  GOLD),
                (f"PV restants : {int(player.health)}/{player.max_health}", GREEN),
            ]
            for i, (text, color) in enumerate(stats):
                t = self.font_md.render(text, True, color)
                surface.blit(t, (cx - t.get_width() // 2, cy - 60 + i * 42))

        # Panneau instructions
        panel = pygame.Surface((500, 52), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 160))
        pygame.draw.rect(panel, (80, 80, 100), panel.get_rect(), 1, border_radius=8)
        surface.blit(panel, (cx - 250, cy + 130))

        instructions = [
            ("[R]  Rejouer",   WHITE),
            ("[M]  Menu",      (160, 200, 255)),
            ("[ESC]  Quitter", (160, 100, 100)),
        ]
        x_off = cx - 220
        for label, color in instructions:
            t = self.font_md.render(label, True, color)
            surface.blit(t, (x_off, cy + 142))
            x_off += 180


# ══════════════════════════════════════════════════════════════════════════════
#  TRANSITION D'ÉPOQUE
# ══════════════════════════════════════════════════════════════════════════════

class EpochTransition:
    """Fondu + texte lors du passage à une nouvelle époque."""

    def __init__(self, screen_w, screen_h):
        self.w, self.h = screen_w, screen_h
        self._active   = False
        self._timer    = 0
        self._duration = 120  # frames
        self._text     = ""
        self._color    = WHITE
        self._callback = None

    def start(self, epoch_key, callback):
        self._active   = True
        self._timer    = 0
        epoch          = EPOCHS.get(epoch_key, {})
        self._text     = epoch.get("display", "")
        self._color    = epoch.get("color", WHITE)
        self._callback = callback

    @property
    def active(self):
        return self._active

    def update(self):
        if not self._active:
            return
        self._timer += 1
        if self._timer == self._duration // 2 and self._callback:
            self._callback()
        if self._timer >= self._duration:
            self._active = False

    def draw(self, surface):
        if not self._active:
            return
        t       = self._timer / self._duration
        # Fade in → out
        if t < 0.5:
            alpha = int(255 * t * 2)
        else:
            alpha = int(255 * (1 - t) * 2)

        ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, alpha))
        surface.blit(ov, (0, 0))

        if 0.2 < t < 0.8:
            font  = pygame.font.Font(None, 72)
            txt   = font.render(self._text, True, self._color)
            txt.set_alpha(alpha)
            surface.blit(txt, (self.w // 2 - txt.get_width() // 2,
                                self.h // 2 - txt.get_height() // 2))


# ══════════════════════════════════════════════════════════════════════════════
#  CLASSE GAME
# ══════════════════════════════════════════════════════════════════════════════

class Game:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Mobius Roguelike")
        self.clock  = pygame.time.Clock()

        sw, sh = SCREEN_WIDTH, SCREEN_HEIGHT

        # Fond menu
        bg_renderer = BackgroundRenderer(sw, sh)
        self.menu_bg = bg_renderer.get("futuristique")   # fond futuriste pour le menu
        try:
            img = pygame.image.load(get_asset_path("backgrounds", "decor_dj_1.jpg")).convert()
            self.menu_bg = pygame.transform.scale(img, (sw, sh))
        except Exception:
            pass

        # Renderers
        self.menu_renderer    = MenuRenderer(sw, sh, self.menu_bg)
        self.gameover_renderer = GameOverRenderer(sw, sh, self.menu_bg)
        self.transition        = EpochTransition(sw, sh)

        # État
        self.game_state    = MENU
        self.selected_skill = None
        self.current_epoch = "prehistoire"
        self.player_skill  = None

        # Salles
        self.rooms: dict = {
            "prehistoire":  PrehistoireRoom(self),
            "grece":        GreceRoom(self),
            "edo":          EdoRoom(self),
            "moderne":      ModerneRoom(self),
            "contemporain": ContemporainRoom(self),
            "futuristique": FuturistiqueRoom(self),
        }
        self.current_room = None

    # ── Démarrage ─────────────────────────────────────────────────────────────

    def start_game(self, skill: str):
        self.player_skill  = skill
        self.current_epoch = "prehistoire"
        self.current_room  = self.rooms["prehistoire"]
        self.current_room.start(skill)
        self.game_state = PLAYING

    def change_epoch(self, next_epoch: str | None):
        if next_epoch and next_epoch in self.rooms and next_epoch != "None":
            # Sauvegarder stats
            p = self.current_room.player
            stats = {
                "skill":       p.skill,
                "kills":       p.kills,
                "coins":       p.coins,
                "health":      p.health,
                "max_health":  p.max_health,
                "stamina":     p.stamina,
                "max_stamina": p.max_stamina,
            }
            # Transition animée
            def _do_change():
                self.current_epoch = next_epoch
                self.current_room  = self.rooms[next_epoch]
                self.current_room.start(stats["skill"], stats)

            self.transition.start(next_epoch, _do_change)
        else:
            # Victoire finale
            self.game_state = GAME_OVER

    # ── Boucle principale ─────────────────────────────────────────────────────

    def run(self):
        running = True

        while running:
            self.clock.tick(60)

            # ── EVENTS ──────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif self.game_state == MENU:
                    running = self._handle_menu_event(event, running)

                elif self.game_state == PLAYING and not self.transition.active:
                    result = self.current_room.handle_event(event)
                    if result == "MENU":
                        self.game_state = MENU
                    elif result == "GAME_OVER":
                        self.game_state = GAME_OVER

                elif self.game_state == GAME_OVER:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self.start_game(self.player_skill)
                        elif event.key == pygame.K_m:
                            self.game_state = MENU
                        elif event.key == pygame.K_ESCAPE:
                            running = False

            # ── UPDATE ──────────────────────────────────────────────────────
            if self.game_state == PLAYING:
                self.transition.update()

                if not self.transition.active:
                    result = self.current_room.update()
                    if result is True:
                        self.game_state = GAME_OVER
                    elif isinstance(result, str) and result.startswith("NEXT_EPOCH:"):
                        next_ep = result.split(":")[1]
                        self.change_epoch(next_ep)

            # ── DRAW ────────────────────────────────────────────────────────
            if self.game_state == MENU:
                self.menu_renderer.draw(self.screen, self.selected_skill)

            elif self.game_state == PLAYING:
                self.current_room.draw(self.screen)
                self.transition.draw(self.screen)

            elif self.game_state == GAME_OVER:
                p = self.current_room.player if self.current_room else None
                self.gameover_renderer.draw(self.screen, p, self.current_epoch)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # ── Gestion events menu ──────────────────────────────────────────────────

    def _handle_menu_event(self, event, running) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            keys_list = list(SKILLS.keys())
            for i, sk in enumerate(keys_list):
                if event.key == pygame.K_1 + i:
                    self.start_game(sk)
                    return running

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = self.menu_renderer.get_card_rects()
            mx, my = pygame.mouse.get_pos()
            for key, rect in rects.items():
                if rect.collidepoint(mx, my):
                    self.start_game(key)
                    return running

        elif event.type == pygame.MOUSEMOTION:
            rects = self.menu_renderer.get_card_rects()
            mx, my = pygame.mouse.get_pos()
            self.selected_skill = None
            for key, rect in rects.items():
                if rect.collidepoint(mx, my):
                    self.selected_skill = key

        return running


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    game = Game()
    game.run()
