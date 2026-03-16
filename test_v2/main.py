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
#  ÉTATS ADDITIONNELS  (MENU=0, PLAYING=1, GAME_OVER=2 viennent de constants)
# ══════════════════════════════════════════════════════════════════════════════

MAIN_MENU        = 3   # écran titre avec boutons Nouvelle Partie / Quitter
CHARACTER_SELECT = 4   # sélection de classe (anciennement MENU=0)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDER VOLUME
# ══════════════════════════════════════════════════════════════════════════════

class VolumeSlider:
    W, H, X, Y, KR = 180, 8, 22, 28, 9

    def __init__(self):
        self.volume    = 0.5
        self._dragging = False
        try: pygame.mixer.music.set_volume(self.volume)
        except Exception: pass

    def handle_event(self, event):
        mx, my = pygame.mouse.get_pos()
        in_zone = (self.X - self.KR <= mx <= self.X + self.W + self.KR and
                   self.Y - 14 <= my <= self.Y + self.H + 14)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and in_zone:
            self._dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False

    def update(self):
        if self._dragging:
            mx = pygame.mouse.get_pos()[0]
            self.volume = max(0.0, min(1.0, (mx - self.X) / self.W))
            try: pygame.mixer.music.set_volume(self.volume)
            except Exception: pass

    def draw(self, surface):
        font = pygame.font.Font(None, 20)
        surface.blit(font.render("Volume", True, (170, 170, 200)), (self.X, self.Y - 18))
        pygame.draw.rect(surface, (70, 70, 90),
                         (self.X, self.Y, self.W, self.H), border_radius=4)
        fill_w = int(self.volume * self.W)
        if fill_w > 0:
            pygame.draw.rect(surface, (80, 160, 255),
                             (self.X, self.Y, fill_w, self.H), border_radius=4)
        kx, ky = self.X + fill_w, self.Y + self.H // 2
        pygame.draw.circle(surface, (220, 220, 255), (kx, ky), self.KR)
        pygame.draw.circle(surface, (80, 160, 255),  (kx, ky), self.KR, 2)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN MENU RENDERER
# ══════════════════════════════════════════════════════════════════════════════

class MainMenuRenderer:
    BTN_W, BTN_H = 300, 60

    def __init__(self, screen_w, screen_h, bg):
        self.w, self.h = screen_w, screen_h
        self.bg        = bg
        self.font_xl   = pygame.font.Font(None, 90)
        self.font_lg   = pygame.font.Font(None, 50)
        self.font_md   = pygame.font.Font(None, 34)
        self.font_sm   = pygame.font.Font(None, 22)
        self._timer    = 0
        self._particles = [
            {"x": random.uniform(0, screen_w), "y": random.uniform(0, screen_h),
             "vx": random.uniform(-0.3, 0.3),  "vy": random.uniform(-0.5, -0.1),
             "r": random.randint(2, 5),         "alpha": random.randint(50, 160)}
            for _ in range(50)
        ]

    def _btn_rect(self, i) -> pygame.Rect:
        return pygame.Rect(self.w // 2 - self.BTN_W // 2,
                           self.h // 2 + 60 + i * (self.BTN_H + 22),
                           self.BTN_W, self.BTN_H)

    def get_play_rect(self) -> pygame.Rect: return self._btn_rect(0)
    def get_quit_rect(self) -> pygame.Rect: return self._btn_rect(1)

    def _draw_button(self, surface, rect, text, hover):
        pygame.draw.rect(surface, (80, 80, 200) if hover else (40, 40, 130),
                         rect, border_radius=12)
        if hover:
            glow = pygame.Surface((rect.w + 10, rect.h + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow, (120, 140, 255, 80),
                             (0, 0, rect.w + 10, rect.h + 10), 3, border_radius=14)
            surface.blit(glow, (rect.x - 5, rect.y - 5))
        pygame.draw.rect(surface, (100, 120, 255) if hover else (60, 60, 160),
                         rect, 2, border_radius=12)
        txt = self.font_md.render(text, True, WHITE)
        surface.blit(txt, txt.get_rect(center=rect.center))

    def draw(self, surface):
        self._timer += 1
        mouse = pygame.mouse.get_pos()
        surface.blit(self.bg, (0, 0))
        ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ov.fill((0, 0, 20, 170)); surface.blit(ov, (0, 0))

        for p in self._particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            if p["y"] < -10:        p["y"] = self.h + 10
            if p["x"] < -10:        p["x"] = self.w + 10
            if p["x"] > self.w+10:  p["x"] = -10
            ps = pygame.Surface((p["r"]*2, p["r"]*2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (150, 180, 255, p["alpha"]), (p["r"], p["r"]), p["r"])
            surface.blit(ps, (int(p["x"])-p["r"], int(p["y"])-p["r"]))

        ty    = int(self.h // 2 - 180 + math.sin(self._timer * 0.02) * 5)
        title = self.font_xl.render("MOBIUS", True, WHITE)
        sub   = self.font_lg.render("R O G U E L I K E", True, (160, 200, 255))
        ref   = pygame.transform.flip(title, False, True)
        ref_s = pygame.Surface(ref.get_size(), pygame.SRCALPHA)
        ref_s.blit(ref, (0, 0)); ref_s.set_alpha(35)
        surface.blit(ref_s, (self.w//2 - title.get_width()//2, ty + title.get_height()))
        surface.blit(title, (self.w//2 - title.get_width()//2, ty))
        surface.blit(sub,   (self.w//2 - sub.get_width()//2,   ty + title.get_height() + 8))

        self._draw_button(surface, self.get_play_rect(), "Nouvelle Partie",
                          self.get_play_rect().collidepoint(mouse))
        self._draw_button(surface, self.get_quit_rect(), "Quitter",
                          self.get_quit_rect().collidepoint(mouse))

        hint = self.font_sm.render("Entrée / Espace = Jouer  ·  ESC = Quitter",
                                   True, (90, 110, 150))
        surface.blit(hint, (self.w//2 - hint.get_width()//2, self.h - 42))
        ei = self.font_sm.render(
            "6 ÉPOQUES  ·  Préhistoire → Grèce → Edo → Moderne → WW2 → Futur",
            True, (80, 100, 140))
        surface.blit(ei, (self.w//2 - ei.get_width()//2, self.h - 64))


# ══════════════════════════════════════════════════════════════════════════════
#  MENU SÉLECTION DE CLASSE
# ══════════════════════════════════════════════════════════════════════════════

class MenuRenderer:
    CARD_W, CARD_H = 210, 280

    def __init__(self, screen_w, screen_h, bg):
        self.w, self.h = screen_w, screen_h
        self.bg        = bg
        self.font_xl   = pygame.font.Font(None, 80)
        self.font_lg   = pygame.font.Font(None, 44)
        self.font_md   = pygame.font.Font(None, 28)
        self.font_sm   = pygame.font.Font(None, 22)
        self._timer    = 0
        self._particles = [
            {"x": random.uniform(0, screen_w), "y": random.uniform(0, screen_h),
             "vx": random.uniform(-0.3, 0.3),  "vy": random.uniform(-0.5, -0.1),
             "r": random.randint(2, 5),         "alpha": random.randint(60, 180)}
            for _ in range(40)
        ]
        self._card_surfs = {k: self._build_card(k, s) for k, s in SKILLS.items()}

    def _build_card(self, key, skill):
        w, h     = self.CARD_W, self.CARD_H
        surf     = pygame.Surface((w, h), pygame.SRCALPHA)
        base_col = skill["color"]
        icon_col = skill["icon_color"]
        for y in range(h):
            t = y / h
            r = int(base_col[0] * (1 - t * 0.4) + 10)
            g = int(base_col[1] * (1 - t * 0.4) + 10)
            b = int(base_col[2] * (1 - t * 0.4) + 10)
            pygame.draw.line(surf,
                (max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)), 200),
                (0, y), (w, y))
        pygame.draw.rect(surf, (*icon_col[:3], 200), surf.get_rect(), 2, border_radius=12)
        cx, cy_i = w // 2, 85
        pygame.draw.circle(surf, (*icon_col[:3], 80),  (cx, cy_i), 42)
        pygame.draw.circle(surf, (*icon_col[:3], 220), (cx, cy_i), 38, 3)
        fi = pygame.font.Font(None, 58)
        lt = fi.render(skill["name"][0], True, WHITE)
        surf.blit(lt, (cx - lt.get_width()//2, cy_i - lt.get_height()//2))
        fn = pygame.font.Font(None, 30)
        nt = fn.render(skill["name"], True, WHITE)
        surf.blit(nt, (cx - nt.get_width()//2, 145))
        fd = pygame.font.Font(None, 20)
        dt = fd.render(skill["desc"], True, (200, 200, 200))
        surf.blit(dt, (cx - dt.get_width()//2, 172))
        pygame.draw.line(surf, (*icon_col[:3], 120), (20, 196), (w-20, 196), 1)
        words = skill["special"].split()
        lines, line = [], ""
        for word in words:
            test = (line + " " + word).strip()
            if fd.size(test)[0] < w - 24: line = test
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)
        for i, l in enumerate(lines):
            lt2 = fd.render(l, True, icon_col)
            surf.blit(lt2, (cx - lt2.get_width()//2, 204 + i * 18))
        idx = list(SKILLS.keys()).index(key) if key in SKILLS else 0
        fn2 = pygame.font.Font(None, 22)
        num = fn2.render(f"[ {idx + 1} ]", True, GOLD)
        surf.blit(num, (cx - num.get_width()//2, h - 28))
        return surf

    def get_card_rects(self) -> dict:
        keys    = list(SKILLS.keys())
        spacing = 24
        total_w = len(keys) * self.CARD_W + (len(keys) - 1) * spacing
        sx      = (self.w - total_w) // 2
        y       = self.h // 2 - self.CARD_H // 2 + 20
        return {k: pygame.Rect(sx + i*(self.CARD_W+spacing), y, self.CARD_W, self.CARD_H)
                for i, k in enumerate(keys)}

    def draw(self, surface, selected_skill=None):
        self._timer += 1
        mouse = pygame.mouse.get_pos()
        surface.blit(self.bg, (0, 0))
        ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ov.fill((0, 0, 10, 160)); surface.blit(ov, (0, 0))

        for p in self._particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            if p["y"] < -10:        p["y"] = self.h + 10
            if p["x"] < -10:        p["x"] = self.w + 10
            if p["x"] > self.w+10:  p["x"] = -10
            ps = pygame.Surface((p["r"]*2, p["r"]*2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (150, 180, 255, p["alpha"]), (p["r"], p["r"]), p["r"])
            surface.blit(ps, (int(p["x"])-p["r"], int(p["y"])-p["r"]))

        title_y = int(90 + math.sin(self._timer * 0.03) * 4)
        title   = self.font_xl.render("MOBIUS", True, WHITE)
        sub     = self.font_lg.render("R O G U E L I K E", True, (160, 200, 255))
        t_x     = self.w//2 - title.get_width()//2
        s_x     = self.w//2 - sub.get_width()//2
        ref     = pygame.transform.flip(title, False, True)
        ref_s   = pygame.Surface(ref.get_size(), pygame.SRCALPHA)
        ref_s.blit(ref, (0, 0)); ref_s.set_alpha(40)
        surface.blit(ref_s, (t_x, title_y + title.get_height()))
        surface.blit(title, (t_x, title_y))
        surface.blit(sub,   (s_x, title_y + title.get_height() + 6))
        choose = self.font_md.render("Choisissez votre classe", True, (180, 180, 200))
        surface.blit(choose, (self.w//2 - choose.get_width()//2,
                               title_y + title.get_height() + sub.get_height() + 22))

        rects = self.get_card_rects()
        for key, rect in rects.items():
            is_hover = rect.collidepoint(mouse)
            is_sel   = key == selected_skill
            dy       = -8 if (is_hover or is_sel) else 0
            draw_y   = rect.y + dy
            shadow = pygame.Surface((self.CARD_W+10, self.CARD_H+10), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 80))
            surface.blit(shadow, (rect.x - 5 + 4, draw_y - 5 + 6))
            surface.blit(self._card_surfs[key], (rect.x, draw_y))
            if is_hover or is_sel:
                ic  = SKILLS[key]["icon_color"]
                ga  = int(60 + 40 * math.sin(self._timer * 0.15))
                glow = pygame.Surface((self.CARD_W+20, self.CARD_H+20), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*ic[:3], ga),
                                 (0, 0, self.CARD_W+20, self.CARD_H+20), 4, border_radius=14)
                surface.blit(glow, (rect.x - 10, draw_y - 10))
                pygame.draw.rect(surface, ic,
                                 (rect.x, draw_y, self.CARD_W, self.CARD_H), 3, border_radius=12)

        inst = self.font_sm.render(
            "Cliquez sur une carte  ·  Touches 1-5  ·  ESC = retour au menu",
            True, (140, 140, 160))
        surface.blit(inst, (self.w//2 - inst.get_width()//2, self.h - 36))
        ei = self.font_sm.render(
            "6 ÉPOQUES  ·  Préhistoire → Grèce → Edo → Moderne → WW2 → Futur",
            True, (100, 120, 160))
        surface.blit(ei, (self.w//2 - ei.get_width()//2, self.h - 60))


# ══════════════════════════════════════════════════════════════════════════════
#  GAME OVER RENDERER
# ══════════════════════════════════════════════════════════════════════════════

class GameOverRenderer:
    def __init__(self, screen_w, screen_h, bg):
        self.w, self.h = screen_w, screen_h
        self.bg        = bg
        self.font_xl   = pygame.font.Font(None, 90)
        self.font_md   = pygame.font.Font(None, 32)
        self._timer    = 0

    def draw(self, surface, player, epoch_key, victory=False):
        self._timer += 1
        surface.blit(self.bg, (0, 0))
        ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 190)); surface.blit(ov, (0, 0))
        cx, cy = self.w // 2, self.h // 2
        col, title, sub = ((GOLD, "VICTOIRE !", "Vous avez traversé toutes les époques !")
                           if victory else (RED, "GAME OVER", "L'histoire vous a rattrapé..."))
        scale  = 1.0 + 0.03 * math.sin(self._timer * 0.1)
        t_surf = self.font_xl.render(title, True, col)
        t_surf = pygame.transform.scale(
            t_surf, (int(t_surf.get_width()*scale), int(t_surf.get_height()*scale)))
        surface.blit(t_surf, (cx - t_surf.get_width()//2, cy - 200))
        s_txt = self.font_md.render(sub, True, (200, 200, 220))
        surface.blit(s_txt, (cx - s_txt.get_width()//2, cy - 120))
        sep = pygame.Surface((400, 2), pygame.SRCALPHA)
        sep.fill((*col[:3], int(150 + 80 * math.sin(self._timer * 0.05))))
        surface.blit(sep, (cx - 200, cy - 92))
        if player:
            epoch_name = EPOCHS.get(epoch_key, {}).get("name", epoch_key)
            for i, (text, color) in enumerate([
                (f"Époque : {epoch_name}", (180, 200, 255)),
                (f"Ennemis éliminés : {player.kills}", WHITE),
                (f"Pièces collectées : {player.coins}", GOLD),
                (f"PV restants : {int(player.health)}/{player.max_health}", GREEN),
            ]):
                t = self.font_md.render(text, True, color)
                surface.blit(t, (cx - t.get_width()//2, cy - 60 + i * 42))
        panel = pygame.Surface((500, 52), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 160))
        pygame.draw.rect(panel, (80, 80, 100), panel.get_rect(), 1, border_radius=8)
        surface.blit(panel, (cx - 250, cy + 130))
        x_off = cx - 220
        for label, color in [("[R]  Rejouer", WHITE), ("[M]  Menu", (160,200,255)),
                              ("[ESC]  Quitter", (160,100,100))]:
            t = self.font_md.render(label, True, color)
            surface.blit(t, (x_off, cy + 142)); x_off += 180


# ══════════════════════════════════════════════════════════════════════════════
#  TRANSITION D'ÉPOQUE
# ══════════════════════════════════════════════════════════════════════════════

class EpochTransition:
    def __init__(self, screen_w, screen_h):
        self.w, self.h = screen_w, screen_h
        self._active   = False
        self._timer    = 0
        self._duration = 120
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
    def active(self): return self._active

    def update(self):
        if not self._active: return
        self._timer += 1
        if self._timer == self._duration // 2 and self._callback:
            self._callback()
        if self._timer >= self._duration:
            self._active = False

    def draw(self, surface):
        if not self._active: return
        t     = self._timer / self._duration
        alpha = int(255 * t * 2) if t < 0.5 else int(255 * (1 - t) * 2)
        ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, alpha)); surface.blit(ov, (0, 0))
        if 0.2 < t < 0.8:
            font = pygame.font.Font(None, 72)
            txt  = font.render(self._text, True, self._color)
            txt.set_alpha(alpha)
            surface.blit(txt, (self.w//2 - txt.get_width()//2,
                                self.h//2 - txt.get_height()//2))


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

        bg_renderer  = BackgroundRenderer(sw, sh)
        self.menu_bg = bg_renderer.get("futuristique")
        try:
            img = pygame.image.load(get_asset_path("backgrounds", "decor_dj_1.jpg")).convert()
            self.menu_bg = pygame.transform.scale(img, (sw, sh))
        except Exception:
            pass

        self.main_menu_renderer = MainMenuRenderer(sw, sh, self.menu_bg)
        self.menu_renderer      = MenuRenderer(sw, sh, self.menu_bg)
        self.gameover_renderer  = GameOverRenderer(sw, sh, self.menu_bg)
        self.transition         = EpochTransition(sw, sh)
        self.volume_slider      = VolumeSlider()

        self.game_state     = MAIN_MENU
        self.selected_skill = None
        self.current_epoch  = "prehistoire"
        self.player_skill   = None

        self.rooms: dict = {
            "prehistoire":  PrehistoireRoom(self),
            "grece":        GreceRoom(self),
            "edo":          EdoRoom(self),
            "moderne":      ModerneRoom(self),
            "contemporain": ContemporainRoom(self),
            "futuristique": FuturistiqueRoom(self),
        }
        self.current_room = None

    def start_game(self, skill: str):
        self.player_skill  = skill
        self.current_epoch = "prehistoire"
        self.current_room  = self.rooms["prehistoire"]
        self.current_room.start(skill)
        self.game_state = PLAYING

    def change_epoch(self, next_epoch: str | None):
        if next_epoch and next_epoch in self.rooms and next_epoch != "None":
            p = self.current_room.player
            stats = {"skill": p.skill, "kills": p.kills, "coins": p.coins,
                     "health": p.health, "max_health": p.max_health,
                     "stamina": p.stamina, "max_stamina": p.max_stamina}
            def _do():
                self.current_epoch = next_epoch
                self.current_room  = self.rooms[next_epoch]
                self.current_room.start(stats["skill"], stats)
            self.transition.start(next_epoch, _do)
        else:
            self.game_state = GAME_OVER

    def run(self):
        running = True
        while running:
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.volume_slider.handle_event(event)

                if self.game_state == MAIN_MENU:
                    running = self._handle_main_menu_event(event, running)
                elif self.game_state == CHARACTER_SELECT:
                    running = self._handle_character_select_event(event, running)
                elif self.game_state == PLAYING and not self.transition.active:
                    result = self.current_room.handle_event(event)
                    if result == "MENU":      self.game_state = MAIN_MENU
                    elif result == "GAME_OVER": self.game_state = GAME_OVER
                elif self.game_state == GAME_OVER:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:      self.start_game(self.player_skill)
                        elif event.key == pygame.K_m:    self.game_state = MAIN_MENU
                        elif event.key == pygame.K_ESCAPE: running = False

            self.volume_slider.update()

            if self.game_state == PLAYING:
                self.transition.update()
                if not self.transition.active:
                    result = self.current_room.update()
                    if result is True:
                        self.game_state = GAME_OVER
                    elif isinstance(result, str) and result.startswith("NEXT_EPOCH:"):
                        self.change_epoch(result.split(":")[1])

            if self.game_state == MAIN_MENU:
                self.main_menu_renderer.draw(self.screen)
                self.volume_slider.draw(self.screen)
            elif self.game_state == CHARACTER_SELECT:
                self.menu_renderer.draw(self.screen, self.selected_skill)
                self.volume_slider.draw(self.screen)
            elif self.game_state == PLAYING:
                self.current_room.draw(self.screen)
                self.transition.draw(self.screen)
            elif self.game_state == GAME_OVER:
                p = self.current_room.player if self.current_room else None
                self.gameover_renderer.draw(self.screen, p, self.current_epoch)
                self.volume_slider.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _handle_main_menu_event(self, event, running) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: return False
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.game_state = CHARACTER_SELECT
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.main_menu_renderer.get_play_rect().collidepoint(mx, my):
                self.game_state = CHARACTER_SELECT
            elif self.main_menu_renderer.get_quit_rect().collidepoint(mx, my):
                pygame.quit(); sys.exit()
        return running

    def _handle_character_select_event(self, event, running) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_state = MAIN_MENU; return running
            for i, sk in enumerate(list(SKILLS.keys())):
                if event.key == pygame.K_1 + i:
                    self.start_game(sk); return running
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            for key, rect in self.menu_renderer.get_card_rects().items():
                if rect.collidepoint(mx, my):
                    self.start_game(key); return running
        elif event.type == pygame.MOUSEMOTION:
            mx, my = pygame.mouse.get_pos()
            self.selected_skill = None
            for key, rect in self.menu_renderer.get_card_rects().items():
                if rect.collidepoint(mx, my):
                    self.selected_skill = key
        return running


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    game = Game()
    game.run()