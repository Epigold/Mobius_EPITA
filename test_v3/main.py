# -*- coding: utf-8 -*-
# main.py - Mobius Roguelike - Orchestrateur principal + menus multijoueur EN LIGNE

"""
FLUX DU JEU (etats)
===============================================================================
  MAIN_MENU         -> Titre : Jouer / Quitter
        v "Jouer"
  MODE_SELECT       -> Solo / Multijoueur en ligne
        |-- Solo           -> CHARACTER_SELECT  -> PLAYING
        `-- Multijoueur    -> ONLINE_MENU
                               |-- Heberger  -> WAITING_CLIENT -> CHARACTER_SELECT -> PLAYING (host)
                               `-- Rejoindre -> IP_INPUT       -> CONNECTING       -> PLAYING (client)

CONTROLES
  P1 (host) : ZQSD  -  Clic gauche/droit  -  ESPACE (dash)  -  F (skill)  -  E (portail)  -  1..9 (arme)
  P2 (client) : MEMES touches que P1 (chacun joue sur son propre PC)

RESEAU (voir core/network.py pour les details)
  - Protocole UDP, port 55 600 par defaut
  - Le HOST est le serveur autoritaire : il simule tout et envoie l'etat au client
  - Le CLIENT envoie ses inputs et recoit l'etat complet pour l'afficher
  - Ouvrir le port 55600 UDP dans le pare-feu et sur le routeur pour jouer sur internet
"""

import pygame
import sys
import math
import random
import threading
import time
from pathlib import Path

MIXER_FREQUENCY = 44100
MIXER_SIZE = -16
MIXER_CHANNELS = 2
MIXER_BUFFER = 2048

pygame.mixer.pre_init(MIXER_FREQUENCY, MIXER_SIZE, MIXER_CHANNELS, MIXER_BUFFER)

from core.constants import *
from core.graphics  import SpriteCache, BackgroundRenderer, ScreenEffects
from core.network   import GameServer, GameClient, ClientRenderer, DEFAULT_PORT, get_local_ip

from epoques.prehistoire   import PrehistoireRoom
from epoques.grece         import GreceRoom
from epoques.edo           import EdoRoom
from epoques.moderne       import ModerneRoom
from epoques.contemporain  import ContemporainRoom
from epoques.futuristique  import FuturistiqueRoom


# ==============================================================================
#  ETATS ADDITIONNELS DU JEU
# ==============================================================================

MAIN_MENU        = 3   # Ecran titre
MODE_SELECT      = 5   # Solo ou Multijoueur en ligne
ONLINE_MENU      = 6   # Heberger ou Rejoindre
IP_INPUT         = 7   # Saisie de l'adresse IP du host
WAITING_CLIENT   = 8   # Host attend la connexion de P2
CONNECTING       = 9   # Client tente de se connecter au host
CHARACTER_SELECT = 4   # Selection de classe

SONS_PATH = Path(__file__).parent / "sons"


class MusicManager:
    """Gestion simple des musiques de fond par contexte de jeu."""

    TRACKS = {
        "menu": SONS_PATH / "menu.mp3",
        "game_normal": SONS_PATH / "game_normal.mp3",
        "game_boss": SONS_PATH / "game_boss.mp3",
        "defeat": SONS_PATH / "defeat.mp3",
    }

    def __init__(self):
        self.current_key = None
        self.pending_key = None
        self._switch_at = 0.0
        self.fade_ms = 700
        self.volume = 0.5
        self.available = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=MIXER_FREQUENCY,
                    size=MIXER_SIZE,
                    channels=MIXER_CHANNELS,
                    buffer=MIXER_BUFFER,
                )
        except Exception:
            self.available = False

    def play(self, key):
        if not self.available:
            return
        if key == self.current_key and self.pending_key is None:
            return
        if key == self.pending_key:
            return
        path = self.TRACKS.get(key)
        if not path or not path.exists():
            return
        try:
            if self.current_key is None or not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.play(-1, fade_ms=self.fade_ms)
                pygame.mixer.music.set_volume(self.volume)
                self.current_key = key
                self.pending_key = None
                self._switch_at = 0.0
            else:
                pygame.mixer.music.fadeout(self.fade_ms)
                self.pending_key = key
                self._switch_at = time.monotonic() + (self.fade_ms / 1000.0)
        except Exception:
            self.available = False

    def update(self):
        if not self.available or not self.pending_key:
            return
        if time.monotonic() < self._switch_at:
            return
        path = self.TRACKS.get(self.pending_key)
        if not path or not path.exists():
            self.pending_key = None
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play(-1, fade_ms=self.fade_ms)
            pygame.mixer.music.set_volume(self.volume)
            self.current_key = self.pending_key
        except Exception:
            self.available = False
        finally:
            self.pending_key = None
            self._switch_at = 0.0

    def set_volume(self, volume):
        self.volume = volume
        if not self.available:
            return
        try:
            pygame.mixer.music.set_volume(volume)
        except Exception:
            pass

    def stop(self):
        if not self.available:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.current_key = None
        self.pending_key = None
        self._switch_at = 0.0


class SoundManager:
    """Gestion simple des bruitages superposes a la musique."""

    TRACKS = {
        "berserker_power": SONS_PATH / "effets" / "berserker_power.mp3",
        "dash": SONS_PATH / "effets" / "dash.mp3",
        "degats_monstres": SONS_PATH / "effets" / "degats_monstres.mp3",
        "ninja_tp": SONS_PATH / "effets" / "ninja_tp.mp3",
        "ouverture_coffre": SONS_PATH / "effets" / "ouverture_coffre.mp3",
        "pouvoir_mage": SONS_PATH / "effets" / "pouvoir_mage.mp3",
        "pouvoir_tank": SONS_PATH / "effets" / "pouvoir_tank.mp3",
        "pouvoir_vampire": SONS_PATH / "effets" / "pouvoir_vampire.mp3",
        "powerup": SONS_PATH / "effets" / "powerup.mp3",
    }
    SOUND_CONFIG = {
        "dash": {"volume": 0.42, "min_interval": 0.10, "max_instances": 1},
        "degats_monstres": {"volume": 0.22, "min_interval": 0.08, "max_instances": 2},
        "ouverture_coffre": {"volume": 0.35, "min_interval": 0.20, "max_instances": 1},
        "powerup": {"volume": 0.30, "min_interval": 0.12, "max_instances": 1},
        "pouvoir_mage": {"volume": 0.26, "min_interval": 0.15, "max_instances": 1},
        "pouvoir_tank": {"volume": 0.28, "min_interval": 0.15, "max_instances": 1},
        "pouvoir_vampire": {"volume": 0.28, "min_interval": 0.15, "max_instances": 1},
        "berserker_power": {"volume": 0.30, "min_interval": 0.15, "max_instances": 1},
        "ninja_tp": {"volume": 0.44, "min_interval": 0.12, "max_instances": 1},
    }

    def __init__(self):
        self.available = True
        self.volume = 0.5
        self._sounds = {}
        self._last_play_times = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=MIXER_FREQUENCY,
                    size=MIXER_SIZE,
                    channels=MIXER_CHANNELS,
                    buffer=MIXER_BUFFER,
                )
            pygame.mixer.set_num_channels(max(24, pygame.mixer.get_num_channels()))
            for key, path in self.TRACKS.items():
                if path.exists():
                    snd = pygame.mixer.Sound(str(path))
                    snd.set_volume(self.volume * self._relative_volume(key))
                    self._sounds[key] = snd
        except Exception:
            self.available = False

    def set_volume(self, volume):
        self.volume = volume
        if not self.available:
            return
        for key, snd in self._sounds.items():
            snd.set_volume(volume * self._relative_volume(key))

    def play(self, key, min_interval=0.0):
        if not self.available:
            return
        snd = self._sounds.get(key)
        if snd is None:
            return
        cfg = self.SOUND_CONFIG.get(key, {})
        now = time.monotonic()
        last = self._last_play_times.get(key, 0.0)
        effective_min_interval = max(float(min_interval or 0.0), float(cfg.get("min_interval", 0.0)))
        if effective_min_interval > 0 and (now - last) < effective_min_interval:
            return
        max_instances = int(cfg.get("max_instances", 0))
        if max_instances > 0 and snd.get_num_channels() >= max_instances:
            return
        self._last_play_times[key] = now
        try:
            snd.play()
        except Exception:
            self.available = False

    def _relative_volume(self, key):
        return float(self.SOUND_CONFIG.get(key, {}).get("volume", 1.0))


# ==============================================================================
#  SLIDER VOLUME
# ==============================================================================

class VolumeSlider:
    """Slider de volume glissable affiche en haut a gauche de tous les menus."""
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
        pygame.draw.rect(surface, (70, 70, 90), (self.X, self.Y, self.W, self.H), border_radius=4)
        fill_w = int(self.volume * self.W)
        if fill_w > 0:
            pygame.draw.rect(surface, (80, 160, 255), (self.X, self.Y, fill_w, self.H), border_radius=4)
        kx, ky = self.X + fill_w, self.Y + self.H // 2
        pygame.draw.circle(surface, (220, 220, 255), (kx, ky), self.KR)
        pygame.draw.circle(surface, (80, 160, 255),  (kx, ky), self.KR, 2)


# ==============================================================================
#  HELPERS DE DESSIN (boutons reutilisables)
# ==============================================================================

def draw_button(surface, rect, text, hover, font,
                col_hover=(80,80,200), col_norm=(40,40,130)):
    """Dessine un bouton rectangulaire avec effet de glow au survol."""
    pygame.draw.rect(surface, col_hover if hover else col_norm, rect, border_radius=12)
    if hover:
        glow = pygame.Surface((rect.w+10, rect.h+10), pygame.SRCALPHA)
        pygame.draw.rect(glow, (120,140,255,80), (0,0,rect.w+10,rect.h+10), 3, border_radius=14)
        surface.blit(glow, (rect.x-5, rect.y-5))
    border = (100,120,255) if hover else (60,60,160)
    pygame.draw.rect(surface, border, rect, 2, border_radius=12)
    txt = font.render(text, True, WHITE)
    surface.blit(txt, txt.get_rect(center=rect.center))

def draw_bg_overlay(surface, bg, w, h, alpha=170):
    """Fond + overlay sombre semi-transparent."""
    surface.blit(bg, (0, 0))
    ov = pygame.Surface((w, h), pygame.SRCALPHA)
    ov.fill((0, 0, 20, alpha))
    surface.blit(ov, (0, 0))

def draw_particles(surface, particles, w, h):
    """Anime et dessine les particules de fond flottantes."""
    for p in particles:
        p["x"] += p["vx"]; p["y"] += p["vy"]
        if p["y"] < -10: p["y"] = h + 10
        if p["x"] < -10: p["x"] = w + 10
        if p["x"] > w+10: p["x"] = -10
        ps = pygame.Surface((p["r"]*2, p["r"]*2), pygame.SRCALPHA)
        pygame.draw.circle(ps, (150,180,255,p["alpha"]), (p["r"],p["r"]), p["r"])
        surface.blit(ps, (int(p["x"])-p["r"], int(p["y"])-p["r"]))

def make_particles(n, w, h):
    """Genere n particules flottantes aleatoires."""
    return [{"x": random.uniform(0,w), "y": random.uniform(0,h),
             "vx": random.uniform(-0.3,0.3), "vy": random.uniform(-0.5,-0.1),
             "r": random.randint(2,5), "alpha": random.randint(50,160)}
            for _ in range(n)]


def load_optional_scaled_image(path_parts, size=None, alpha=True):
    """Charge une image optionnelle sans interrompre le jeu si elle est absente."""
    try:
        img = pygame.image.load(get_asset_path(*path_parts))
        img = img.convert_alpha() if alpha else img.convert()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    except Exception:
        return None


# ==============================================================================
#  ECRAN TITRE PRINCIPAL
# ==============================================================================

class MainMenuRenderer:
    """Ecran titre avec logo MOBIUS anime + boutons Nouvelle Partie / Quitter."""
    BTN_W, BTN_H = scale_int(300), scale_int(60)

    def __init__(self, w, h, bg):
        self.w, self.h   = w, h
        self.bg          = bg
        self.font_xl     = pygame.font.Font(None, scale_int(90))
        self.font_lg     = pygame.font.Font(None, scale_int(50))
        self.font_md     = pygame.font.Font(None, scale_int(34))
        self.font_sm     = pygame.font.Font(None, scale_int(22))
        self._timer      = 0
        self._particles  = make_particles(50, w, h)
        self.logo        = load_optional_scaled_image(
            ("ui", "logo", "mobius_violet.png"), size=scale_tuple((360, 240))
        )

    def _btn(self, i):
        return pygame.Rect(self.w//2 - self.BTN_W//2,
                           self.h//2 + scale_int(60) + i*(self.BTN_H+scale_int(22)), self.BTN_W, self.BTN_H)

    def get_play_rect(self): return self._btn(0)
    def get_quit_rect(self): return self._btn(1)

    def draw(self, surface):
        self._timer += 1
        mouse = pygame.mouse.get_pos()
        draw_bg_overlay(surface, self.bg, self.w, self.h)
        draw_particles(surface, self._particles, self.w, self.h)

        # Logo anime
        ty = int(self.h//2 - scale_int(220) + math.sin(self._timer*0.02)*scale_int(5))
        sub = self.font_lg.render("R O G U E L I K E", True, (160,200,255))
        if self.logo:
            lx = self.w//2 - self.logo.get_width()//2
            shadow = self.logo.copy()
            shadow.fill((0, 0, 0, 60), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(shadow, (lx + scale_int(12), ty + scale_int(18)))
            surface.blit(self.logo, (lx, ty))
            sub_y = ty + self.logo.get_height() - scale_int(8)
        else:
            title = self.font_xl.render("MOBIUS", True, WHITE)
            ref   = pygame.transform.flip(title, False, True)
            ref_s = pygame.Surface(ref.get_size(), pygame.SRCALPHA)
            ref_s.blit(ref, (0,0)); ref_s.set_alpha(35)
            surface.blit(ref_s, (self.w//2 - title.get_width()//2, ty+title.get_height()))
            surface.blit(title,  (self.w//2 - title.get_width()//2, ty))
            sub_y = ty + title.get_height() + scale_int(8)
        surface.blit(sub, (self.w//2 - sub.get_width()//2, sub_y))

        draw_button(surface, self.get_play_rect(), "Jouer",
                    self.get_play_rect().collidepoint(mouse), self.font_md)
        draw_button(surface, self.get_quit_rect(), "Quitter",
                    self.get_quit_rect().collidepoint(mouse), self.font_md)

        hint = self.font_sm.render("Entree = Jouer   -   ESC = Quitter", True, (90,110,150))
        surface.blit(hint, (self.w//2-hint.get_width()//2, self.h-scale_int(42)))
        ei = self.font_sm.render(
            "6 EPOQUES   -   Prehistoire -> Grece Antique -> Edo -> Moderne -> WW2 -> Futur",
            True, (80,100,140))
        surface.blit(ei, (self.w//2-ei.get_width()//2, self.h-scale_int(64)))


# ==============================================================================
#  ECRAN SELECTION DU MODE (Solo / Multijoueur en ligne)
# ==============================================================================

class ModeSelectRenderer:
    """
    Deux grandes cartes cliquables :
      - SOLO         -> mode classique un joueur
      - EN LIGNE     -> multijoueur via reseau (Host ou Join)
    """
    CARD_W, CARD_H = scale_int(320), scale_int(360)
    SPACING        = scale_int(80)

    def __init__(self, w, h, bg):
        self.w, self.h  = w, h
        self.bg         = bg
        self.font_xl    = pygame.font.Font(None, scale_int(80))
        self.font_lg    = pygame.font.Font(None, scale_int(48))
        self.font_md    = pygame.font.Font(None, scale_int(30))
        self.font_sm    = pygame.font.Font(None, scale_int(22))
        self._timer     = 0
        self._particles = make_particles(40, w, h)
        self._c_solo    = self._build_card_solo()
        self._c_online  = self._build_card_online()

    def _card_base(self, grad_a, grad_b, border_col):
        """Surface de base pour une carte avec degrade."""
        w, h = self.CARD_W, self.CARD_H
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            t  = y / h
            r  = int(grad_a[0]*(1-t) + grad_b[0]*t)
            g  = int(grad_a[1]*(1-t) + grad_b[1]*t)
            b  = int(grad_a[2]*(1-t) + grad_b[2]*t)
            pygame.draw.line(surf, (r, g, b, 210), (0, y), (w, y))
        pygame.draw.rect(surf, border_col, surf.get_rect(), 3, border_radius=16)
        return surf

    def _build_card_solo(self):
        surf = self._card_base((60,20,120), (20,10,60), (120,80,255))
        cx   = self.CARD_W // 2
        # Icone joueur
        pygame.draw.circle(surf, (180,140,255), (cx, scale_int(110)), scale_int(45))
        pygame.draw.circle(surf, (120,80,220),  (cx, scale_int(110)), scale_int(45), 3)
        fi = pygame.font.Font(None, scale_int(70))
        lt = fi.render("1", True, WHITE)
        surf.blit(lt, (cx-lt.get_width()//2, scale_int(110)-lt.get_height()//2))
        # Textes
        fn = pygame.font.Font(None, scale_int(42))
        nt = fn.render("SOLO", True, WHITE)
        surf.blit(nt, (cx-nt.get_width()//2, scale_int(172)))
        fd = pygame.font.Font(None, scale_int(22))
        sub = fd.render("Un joueur  -  Clavier + Souris", True, (200,180,255))
        surf.blit(sub, (cx-sub.get_width()//2, scale_int(210)))
        pygame.draw.line(surf, (120,80,200,150), (scale_int(30),scale_int(240)), (self.CARD_W-scale_int(30),scale_int(240)), 1)
        for i, line in enumerate(["ZQSD : Deplacement",
                                   "Clic gauche : Attaque",
                                   "Clic droit : Attaque secondaire",
                                   "ESPACE : Dash",
                                   "F : Competence / E : Portail"]):
            t = fd.render(line, True, (200,200,220))
            surf.blit(t, (cx-t.get_width()//2, scale_int(252)+i*scale_int(20)))
        fk = pygame.font.Font(None, scale_int(20))
        k = fk.render("[ 1 ]", True, GOLD)
        surf.blit(k, (cx-k.get_width()//2, self.CARD_H-scale_int(28)))
        return surf

    def _build_card_online(self):
        surf = self._card_base((10,60,140), (5,20,60), (60,160,255))
        cx   = self.CARD_W // 2
        # Icone reseau (deux cercles + ligne)
        pygame.draw.circle(surf, (180,100,255), (cx-scale_int(30), scale_int(110)), scale_int(28))
        pygame.draw.circle(surf, (60,160,255),  (cx+scale_int(30), scale_int(110)), scale_int(28))
        pygame.draw.line(surf, (200,200,255), (cx-scale_int(2),scale_int(110)), (cx+scale_int(2),scale_int(110)), 3)
        # Antennes
        for ox2, col in [(-scale_int(30),(180,100,255)),(scale_int(30),(60,160,255))]:
            pygame.draw.line(surf, col, (cx+ox2,scale_int(82)), (cx+ox2,scale_int(60)), 2)
            pygame.draw.circle(surf, col, (cx+ox2, scale_int(56)), scale_int(5))
        fi = pygame.font.Font(None, scale_int(40))
        lt1 = fi.render("H", True, WHITE)
        lt2 = fi.render("C", True, WHITE)
        surf.blit(lt1, (cx-scale_int(30)-lt1.get_width()//2, scale_int(110)-lt1.get_height()//2))
        surf.blit(lt2, (cx+scale_int(30)-lt2.get_width()//2, scale_int(110)-lt2.get_height()//2))
        fn = pygame.font.Font(None, scale_int(42))
        nt = fn.render("EN LIGNE", True, WHITE)
        surf.blit(nt, (cx-nt.get_width()//2, scale_int(172)))
        fd = pygame.font.Font(None, scale_int(22))
        sub = fd.render("Co-op 2 joueurs  -  Reseau local ou internet", True, (160,220,255))
        surf.blit(sub, (cx-sub.get_width()//2, scale_int(210)))
        pygame.draw.line(surf, (60,140,200,150), (scale_int(30),scale_int(240)), (self.CARD_W-scale_int(30),scale_int(240)), 1)
        for i, line in enumerate(["Heberger : vous etes le serveur",
                                   "Rejoindre : entrez l'IP du host",
                                   f"Port UDP {DEFAULT_PORT} (ouvrir le pare-feu)",
                                   "Fonctionne en LAN et sur internet"]):
            t = fd.render(line, True, (200,230,255))
            surf.blit(t, (cx-t.get_width()//2, scale_int(252)+i*scale_int(20)))
        fk = pygame.font.Font(None, scale_int(20))
        k = fk.render("[ 2 ]", True, GOLD)
        surf.blit(k, (cx-k.get_width()//2, self.CARD_H-scale_int(28)))
        return surf

    def _card_y(self):
        return self.h//2 - self.CARD_H//2 + scale_int(30)

    def get_solo_rect(self):
        total = self.CARD_W*2 + self.SPACING
        sx = (self.w - total) // 2
        return pygame.Rect(sx, self._card_y(), self.CARD_W, self.CARD_H)

    def get_online_rect(self):
        total = self.CARD_W*2 + self.SPACING
        sx = (self.w - total) // 2
        return pygame.Rect(sx + self.CARD_W + self.SPACING, self._card_y(),
                           self.CARD_W, self.CARD_H)

    def draw(self, surface):
        self._timer += 1
        mouse = pygame.mouse.get_pos()
        draw_bg_overlay(surface, self.bg, self.w, self.h)
        draw_particles(surface, self._particles, self.w, self.h)

        ty    = int(scale_int(80) + math.sin(self._timer*0.03)*scale_int(4))
        title = self.font_xl.render("MOBIUS", True, WHITE)
        sub   = self.font_lg.render("Choisissez votre mode", True, (160,200,255))
        surface.blit(title, (self.w//2-title.get_width()//2, ty))
        surface.blit(sub,   (self.w//2-sub.get_width()//2,   ty+title.get_height()+scale_int(6)))

        for card, rect in [(self._c_solo, self.get_solo_rect()),
                            (self._c_online, self.get_online_rect())]:
            hover  = rect.collidepoint(mouse)
            draw_y = rect.y - 8 if hover else rect.y
            sh = pygame.Surface((self.CARD_W+10, self.CARD_H+10), pygame.SRCALPHA)
            sh.fill((0,0,0,80))
            surface.blit(sh, (rect.x-5+4, draw_y-5+8))
            surface.blit(card, (rect.x, draw_y))
            if hover:
                ga   = int(60 + 40*math.sin(self._timer*0.15))
                glow = pygame.Surface((self.CARD_W+20, self.CARD_H+20), pygame.SRCALPHA)
                pygame.draw.rect(glow, (120,180,255,ga),
                                 (0,0,self.CARD_W+20,self.CARD_H+20), 4, border_radius=18)
                surface.blit(glow, (rect.x-10, draw_y-10))
                pygame.draw.rect(surface, (100,180,255),
                                 (rect.x, draw_y, self.CARD_W, self.CARD_H), 3, border_radius=16)

        inst = self.font_sm.render("1=Solo  -  2=En ligne  -  ESC=retour", True, (140,140,160))
        surface.blit(inst, (self.w//2-inst.get_width()//2, self.h-scale_int(36)))


# ==============================================================================
#  ECRAN MULTIJOUEUR EN LIGNE (Heberger / Rejoindre)
# ==============================================================================

class OnlineMenuRenderer:
    """
    Sous-menu multijoueur avec deux options :
      - Heberger  : cree le serveur, affiche l'IP locale a communiquer a P2
      - Rejoindre : passe a l'ecran de saisie d'IP
    """
    BTN_W, BTN_H = scale_int(340), scale_int(64)

    def __init__(self, w, h, bg):
        self.w, self.h  = w, h
        self.bg         = bg
        self.font_xl    = pygame.font.Font(None, scale_int(80))
        self.font_lg    = pygame.font.Font(None, scale_int(44))
        self.font_md    = pygame.font.Font(None, scale_int(32))
        self.font_sm    = pygame.font.Font(None, scale_int(22))
        self._timer     = 0
        self._particles = make_particles(35, w, h)
        # IP locale recuperee une seule fois (appel reseau rapide)
        self._local_ip  = get_local_ip()

    def _btn(self, i):
        return pygame.Rect(self.w//2 - self.BTN_W//2,
                           self.h//2 + scale_int(20) + i*(self.BTN_H+scale_int(26)), self.BTN_W, self.BTN_H)

    def get_host_rect(self):  return self._btn(0)
    def get_join_rect(self):  return self._btn(1)
    def get_back_rect(self):  return self._btn(2)

    def draw(self, surface):
        self._timer += 1
        mouse = pygame.mouse.get_pos()
        draw_bg_overlay(surface, self.bg, self.w, self.h, alpha=180)
        draw_particles(surface, self._particles, self.w, self.h)

        # Titre
        ty    = int(scale_int(80) + math.sin(self._timer*0.03)*scale_int(4))
        title = self.font_xl.render("EN LIGNE", True, (80,200,255))
        sub   = self.font_lg.render("Multijoueur co-op 2 joueurs", True, (160,220,255))
        surface.blit(title, (self.w//2-title.get_width()//2, ty))
        surface.blit(sub,   (self.w//2-sub.get_width()//2,   ty+title.get_height()+scale_int(6)))

        # IP locale (utile si on heberge)
        ip_txt = self.font_sm.render(
            f"Votre IP locale : {self._local_ip}  (a communiquer a P2 si vous hebergez)",
            True, (140,200,140))
        surface.blit(ip_txt, (self.w//2-ip_txt.get_width()//2, ty+title.get_height()+sub.get_height()+scale_int(18)))

        # Boutons
        draw_button(surface, self.get_host_rect(), "Heberger la partie",
                    self.get_host_rect().collidepoint(mouse), self.font_md,
                    col_hover=(40,120,60), col_norm=(20,60,30))
        draw_button(surface, self.get_join_rect(), "Rejoindre une partie",
                    self.get_join_rect().collidepoint(mouse), self.font_md,
                    col_hover=(30,80,160), col_norm=(15,40,80))
        draw_button(surface, self.get_back_rect(), "Retour",
                    self.get_back_rect().collidepoint(mouse), self.font_md,
                    col_hover=(80,40,40), col_norm=(50,25,25))

        # Note pare-feu
        note = self.font_sm.render(
            f"Sur internet : ouvrir le port UDP {DEFAULT_PORT} dans le pare-feu et le routeur",
            True, (180,160,80))
        surface.blit(note, (self.w//2-note.get_width()//2, self.h-scale_int(42)))
        port_note = self.font_sm.render(
            f"Port par defaut : {DEFAULT_PORT}",
            True, (120,120,140))
        surface.blit(port_note, (self.w//2-port_note.get_width()//2, self.h-scale_int(22)))


# ==============================================================================
#  ECRAN SAISIE D'IP (pour rejoindre)
# ==============================================================================

class IPInputRenderer:
    """
    Ecran de saisie de l'adresse IP du serveur host.
    Gere la saisie clavier (chiffres, points, backspace).
    Affiche les erreurs de format.
    """
    BTN_W, BTN_H = scale_int(240), scale_int(56)

    def __init__(self, w, h, bg):
        self.w, self.h  = w, h
        self.bg         = bg
        self.font_xl    = pygame.font.Font(None, scale_int(72))
        self.font_lg    = pygame.font.Font(None, scale_int(44))
        self.font_md    = pygame.font.Font(None, scale_int(32))
        self.font_ip    = pygame.font.Font(None, scale_int(52))
        self.font_sm    = pygame.font.Font(None, scale_int(22))
        self._timer     = 0
        self._particles = make_particles(30, w, h)

        self.ip_text    = ""    # Texte saisi par l'utilisateur
        self.error_msg  = ""    # Message d'erreur affiche sous le champ

    def get_connect_rect(self):
        return pygame.Rect(self.w//2 - self.BTN_W//2,
                           self.h//2 + scale_int(80), self.BTN_W, self.BTN_H)

    def get_back_rect(self):
        return pygame.Rect(self.w//2 - self.BTN_W//2,
                           self.h//2 + scale_int(80) + self.BTN_H + scale_int(20), self.BTN_W, self.BTN_H)

    def handle_keydown(self, event) -> str | None:
        """
        Traite un evenement KEYDOWN pour la saisie d'IP.
        Retourne :
          "connect" si ENTREE est pressee (IP potentiellement valide)
          "back"    si ECHAP est presse
          None      sinon
        """
        if event.key == pygame.K_ESCAPE:
            return "back"
        elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            return "connect"
        elif event.key == pygame.K_BACKSPACE:
            self.ip_text = self.ip_text[:-1]
            self.error_msg = ""
        elif len(self.ip_text) < 21:
            # N'autoriser que les chiffres et les points (IPv4)
            if event.unicode in "0123456789.":
                self.ip_text += event.unicode
                self.error_msg = ""
        return None

    def validate_ip(self) -> bool:
        """
        Verifie que l'IP saisie a un format IPv4 basique.
        Ne valide pas la joignabilite (ca sera detecte a la connexion).
        """
        parts = self.ip_text.strip().split(".")
        if len(parts) != 4:
            self.error_msg = "Format invalide - exemple : 192.168.1.42"
            return False
        for p in parts:
            try:
                v = int(p)
                if not (0 <= v <= 255):
                    self.error_msg = "Chaque partie doit etre entre 0 et 255"
                    return False
            except ValueError:
                self.error_msg = "Chiffres uniquement separes par des points"
                return False
        return True

    def draw(self, surface):
        self._timer += 1
        mouse = pygame.mouse.get_pos()
        draw_bg_overlay(surface, self.bg, self.w, self.h)
        draw_particles(surface, self._particles, self.w, self.h)

        # Titre
        ty = int(scale_int(80) + math.sin(self._timer*0.03)*scale_int(4))
        title = self.font_xl.render("REJOINDRE", True, (80,200,255))
        sub   = self.font_lg.render("Entrez l'IP du host", True, (160,220,255))
        surface.blit(title, (self.w//2-title.get_width()//2, ty))
        surface.blit(sub,   (self.w//2-sub.get_width()//2,   ty+title.get_height()+scale_int(6)))

        # Champ de saisie IP
        FIELD_W, FIELD_H = scale_int(420), scale_int(60)
        field_rect = pygame.Rect(self.w//2 - FIELD_W//2, self.h//2 - FIELD_H//2 - scale_int(20),
                                 FIELD_W, FIELD_H)
        # Fond du champ
        pygame.draw.rect(surface, (20,30,60), field_rect, border_radius=10)
        # Bordure pulsante (blanc si vide, bleu si texte, vert si valide)
        blink = int(self._timer * 0.05) % 2 == 0
        border_col = (100,200,100) if len(self.ip_text.split(".")) == 4 else (80,160,255)
        pygame.draw.rect(surface, border_col, field_rect, 2, border_radius=10)

        # Texte saisi + curseur clignotant
        display_text = self.ip_text + ("|" if blink else " ")
        ip_surf = self.font_ip.render(display_text if self.ip_text else "ex: 192.168.1.42",
                                      True,
                                      WHITE if self.ip_text else (80,100,120))
        surface.blit(ip_surf, ip_surf.get_rect(center=field_rect.center))

        # Message d'erreur
        if self.error_msg:
            err = self.font_sm.render(self.error_msg, True, (220,80,80))
            surface.blit(err, (self.w//2-err.get_width()//2, field_rect.bottom+scale_int(8)))

        # Boutons
        draw_button(surface, self.get_connect_rect(), "Connexion",
                    self.get_connect_rect().collidepoint(mouse), self.font_md,
                    col_hover=(30,100,180), col_norm=(15,50,90))
        draw_button(surface, self.get_back_rect(), "Retour",
                    self.get_back_rect().collidepoint(mouse), self.font_md,
                    col_hover=(80,40,40), col_norm=(50,25,25))

        # Aide saisie
        note = self.font_sm.render(
            "Tapez l'adresse IP du host - Entree pour valider - ESC pour annuler",
            True, (120,140,160))
        surface.blit(note, (self.w//2-note.get_width()//2, self.h-scale_int(36)))


# ==============================================================================
#  ECRAN D'ATTENTE / CONNEXION (Host attend P2, Client se connecte)
# ==============================================================================

class WaitingRenderer:
    """
    Ecran generique d'attente/connexion affiche :
      - Cote host   : "En attente de P2..."
      - Cote client : "Connexion en cours..."
    Affiche un spinner anime + l'IP concernee.
    Bouton Annuler pour interrompre.
    """
    BTN_W, BTN_H = scale_int(200), scale_int(50)

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.bg        = bg
        self.font_xl   = pygame.font.Font(None, scale_int(66))
        self.font_md   = pygame.font.Font(None, scale_int(30))
        self.font_sm   = pygame.font.Font(None, scale_int(22))
        self._timer    = 0

    def get_cancel_rect(self, info_count=3):
        info_count = max(1, info_count)
        y = self.h//2 + scale_int(110) + info_count * scale_int(34)
        return pygame.Rect(self.w//2-self.BTN_W//2, y, self.BTN_W, self.BTN_H)

    def draw(self, surface, title_text: str, info_lines: list[str]):
        """
        title_text : str -> titre principal (ex: "En attente de P2...")
        info_lines : list[str] -> lignes d'info sous le titre
        """
        self._timer += 1
        mouse = pygame.mouse.get_pos()
        draw_bg_overlay(surface, self.bg, self.w, self.h, alpha=190)

        # Spinner anime (arc tournant)
        cx, cy = self.w//2, self.h//2 - scale_int(20)
        angle  = self._timer * 6   # Tourne de 6 deg par frame
        pygame.draw.arc(surface, (80, 160, 255),
                        (cx-scale_int(40), cy-scale_int(40), scale_int(80), scale_int(80)),
                        math.radians(angle), math.radians(angle+270), scale_int(5))
        pygame.draw.arc(surface, (40, 80, 130),
                        (cx-scale_int(40), cy-scale_int(40), scale_int(80), scale_int(80)),
                        math.radians(angle+270), math.radians(angle+360), scale_int(5))

        # Titre
        title = self.font_xl.render(title_text, True, WHITE)
        surface.blit(title, (self.w//2-title.get_width()//2, cy-scale_int(130)))

        # Lignes d'info
        for i, line in enumerate(info_lines):
            t = self.font_md.render(line, True, (180,220,255))
            surface.blit(t, (self.w//2-t.get_width()//2, cy+scale_int(60)+i*scale_int(30)))

        # Bouton Annuler
        cancel_rect = self.get_cancel_rect(len(info_lines))
        draw_button(surface, cancel_rect, "Annuler",
                    cancel_rect.collidepoint(mouse), self.font_md,
                    col_hover=(140,40,40), col_norm=(80,20,20))


# ==============================================================================
#  ECRAN SELECTION DE CLASSE
# ==============================================================================

class MenuRenderer:
    """
    Selection de classe pour un joueur (solo ou reseau).
    Identique a l'original - pas de selection double ici
    (chaque PC choisit sa propre classe dans le menu multijoueur).
    """
    CARD_W, CARD_H = scale_int(210), scale_int(280)

    def __init__(self, w, h, bg):
        self.w, self.h  = w, h
        self.bg         = bg
        self.font_xl    = pygame.font.Font(None, scale_int(80))
        self.font_lg    = pygame.font.Font(None, scale_int(44))
        self.font_md    = pygame.font.Font(None, scale_int(28))
        self.font_sm    = pygame.font.Font(None, scale_int(22))
        self._timer     = 0
        self._particles = make_particles(40, w, h)
        self._card_surfs= {k: self._build_card(k, s) for k, s in SKILLS.items()}

    def _build_card(self, key, skill):
        w, h     = self.CARD_W, self.CARD_H
        surf     = pygame.Surface((w, h), pygame.SRCALPHA)
        base_col = skill["color"]
        icon_col = skill["icon_color"]
        for y in range(h):
            t = y / h
            r = int(base_col[0]*(1-t*0.4)+10)
            g = int(base_col[1]*(1-t*0.4)+10)
            b = int(base_col[2]*(1-t*0.4)+10)
            pygame.draw.line(surf, (max(0,min(255,r)),max(0,min(255,g)),max(0,min(255,b)),200),
                             (0,y),(w,y))
        pygame.draw.rect(surf, (*icon_col[:3],200), surf.get_rect(), 2, border_radius=12)
        cx, cy_i = w//2, scale_int(85)
        pygame.draw.circle(surf, (*icon_col[:3],80),  (cx,cy_i), scale_int(42))
        pygame.draw.circle(surf, (*icon_col[:3],220), (cx,cy_i), scale_int(38), 3)
        fi = pygame.font.Font(None, scale_int(58))
        lt = fi.render(skill["name"][0], True, WHITE)
        surf.blit(lt, (cx-lt.get_width()//2, cy_i-lt.get_height()//2))
        fn = pygame.font.Font(None, scale_int(30))
        nt = fn.render(skill["name"], True, WHITE)
        surf.blit(nt, (cx-nt.get_width()//2, scale_int(145)))
        fd = pygame.font.Font(None, scale_int(20))
        dt = fd.render(skill["desc"], True, (200,200,200))
        surf.blit(dt, (cx-dt.get_width()//2, scale_int(172)))
        pygame.draw.line(surf, (*icon_col[:3],120), (scale_int(20),scale_int(196)), (w-scale_int(20),scale_int(196)), 1)
        words = skill["special"].split()
        lines, line = [], ""
        for word in words:
            test = (line+" "+word).strip()
            if fd.size(test)[0] < w-24: line = test
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)
        for i, l in enumerate(lines):
            lt2 = fd.render(l, True, icon_col)
            surf.blit(lt2, (cx-lt2.get_width()//2, scale_int(204)+i*scale_int(18)))
        idx = list(SKILLS.keys()).index(key) if key in SKILLS else 0
        fn2 = pygame.font.Font(None, scale_int(22))
        num = fn2.render(f"[ {idx+1} ]", True, GOLD)
        surf.blit(num, (cx-num.get_width()//2, h-scale_int(28)))
        return surf

    def get_card_rects(self) -> dict:
        keys    = list(SKILLS.keys())
        # Espacement entre les cartes augmente (24 -> 44) pour aerer le menu.
        # Le calcul centre automatiquement l'ensemble sur la largeur de l'ecran.
        spacing = scale_int(44)
        total_w = len(keys)*self.CARD_W + (len(keys)-1)*spacing
        sx      = (self.w - total_w) // 2
        # Legerement plus bas (+40 -> +60) pour laisser respirer le titre
        y       = self.h//2 - self.CARD_H//2 + scale_int(60)
        return {k: pygame.Rect(sx+i*(self.CARD_W+spacing), y, self.CARD_W, self.CARD_H)
                for i, k in enumerate(keys)}

    def draw(self, surface, selected_skill=None, mode_label=""):
        """
        mode_label : str -> texte optionnel affiche sous le titre
                           ex: "HOST - Choisissez votre classe" ou "CLIENT"
        """
        self._timer += 1
        mouse = pygame.mouse.get_pos()
        draw_bg_overlay(surface, self.bg, self.w, self.h, alpha=160)
        draw_particles(surface, self._particles, self.w, self.h)

        title_y = int(scale_int(90) + math.sin(self._timer*0.03)*scale_int(4))
        title   = self.font_xl.render("MOBIUS", True, WHITE)
        sub     = self.font_lg.render("R O G U E L I K E", True, (160,200,255))
        surface.blit(title, (self.w//2-title.get_width()//2, title_y))
        surface.blit(sub,   (self.w//2-sub.get_width()//2,   title_y+title.get_height()+scale_int(6)))

        if mode_label:
            lbl = self.font_md.render(mode_label, True, (120,200,255))
            bg_lbl = pygame.Surface((lbl.get_width()+scale_int(30), lbl.get_height()+scale_int(12)), pygame.SRCALPHA)
            bg_lbl.fill((20,60,120,180))
            pygame.draw.rect(bg_lbl, (80,160,255), bg_lbl.get_rect(), 2, border_radius=8)
            lbl_y = title_y+title.get_height()+sub.get_height()+scale_int(22)
            surface.blit(bg_lbl, (self.w//2-bg_lbl.get_width()//2, lbl_y-scale_int(6)))
            surface.blit(lbl,    (self.w//2-lbl.get_width()//2,     lbl_y))
        else:
            choose = self.font_md.render("Choisissez votre classe", True, (180,180,200))
            surface.blit(choose, (self.w//2-choose.get_width()//2,
                                   title_y+title.get_height()+sub.get_height()+scale_int(22)))

        rects = self.get_card_rects()
        for key, rect in rects.items():
            is_hover = rect.collidepoint(mouse)
            is_sel   = key == selected_skill
            dy       = -scale_int(8) if (is_hover or is_sel) else 0
            draw_y   = rect.y + dy
            sh = pygame.Surface((self.CARD_W+10, self.CARD_H+10), pygame.SRCALPHA)
            sh.fill((0,0,0,80))
            surface.blit(sh, (rect.x-5+4, draw_y-5+6))
            surface.blit(self._card_surfs[key], (rect.x, draw_y))
            if is_hover or is_sel:
                ic   = SKILLS[key]["icon_color"]
                ga   = int(60+40*math.sin(self._timer*0.15))
                glow = pygame.Surface((self.CARD_W+20, self.CARD_H+20), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*ic[:3],ga),
                                 (0,0,self.CARD_W+20,self.CARD_H+20), 4, border_radius=14)
                surface.blit(glow, (rect.x-10, draw_y-10))
                pygame.draw.rect(surface, ic,
                                 (rect.x,draw_y,self.CARD_W,self.CARD_H), 3, border_radius=12)

        inst = self.font_sm.render(
            "Cliquez ou appuyez sur 1-5  --  ESC = retour", True, (140,140,160))
        surface.blit(inst, (self.w//2-inst.get_width()//2, self.h-scale_int(36)))


# ==============================================================================
#  GAME OVER
# ==============================================================================

class GameOverRenderer:
    """Ecran de fin de partie avec stats (supporte solo et multijoueur)."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.bg        = bg
        self.font_xl   = pygame.font.Font(None, scale_int(90))
        self.font_md   = pygame.font.Font(None, scale_int(32))
        self._timer    = 0
        self.victory_art = load_optional_scaled_image(
            ("ui", "game_over", "victory.png"), size=scale_tuple((560, 390))
        )
        self.defeat_art = load_optional_scaled_image(
            ("ui", "game_over", "defeat.png"), size=scale_tuple((560, 390))
        )

    def draw(self, surface, player, epoch_key, victory=False, replay_status=None, online=False):
        self._timer += 1
        surface.blit(self.bg, (0,0))
        ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ov.fill((0,0,0,190)); surface.blit(ov, (0,0))
        cx, cy = self.w//2, self.h//2
        col, title_txt, sub_txt = (
            (GOLD, "VICTOIRE !", "Vous avez traverse toutes les epoques !")
            if victory else (RED, "GAME OVER", "oh, oh... l'histoire s'arrete ici"))
        scale  = 1.0 + 0.03*math.sin(self._timer*0.1)
        art = self.victory_art if victory else self.defeat_art
        title_y = cy - 200

        if art:
            art_rect = art.get_rect(center=(cx, cy - 125))
            frame = pygame.Surface((art_rect.w + 24, art_rect.h + 24), pygame.SRCALPHA)
            pygame.draw.rect(frame, (0, 0, 0, 140), frame.get_rect(), border_radius=18)
            pygame.draw.rect(frame, col, frame.get_rect(), 3, border_radius=18)
            surface.blit(frame, (art_rect.x - 12, art_rect.y - 12))
            surface.blit(art, art_rect)
            title_y = cy + 100

        t_surf = self.font_xl.render(title_txt, True, col)
        t_surf = pygame.transform.scale(t_surf,
            (int(t_surf.get_width()*scale), int(t_surf.get_height()*scale)))
        surface.blit(t_surf, (cx-t_surf.get_width()//2, title_y))
        s_txt = self.font_md.render(sub_txt, True, (200,200,220))
        surface.blit(s_txt, (cx-s_txt.get_width()//2, title_y + 80))
        sep = pygame.Surface((400,2), pygame.SRCALPHA)
        sep.fill((*col[:3], int(150+80*math.sin(self._timer*0.05))))
        surface.blit(sep, (cx-200, title_y + 108))
        if player:
            epoch_name = EPOCHS.get(epoch_key, {}).get("name", epoch_key)
            for i, (text, color) in enumerate([
                (f"Epoque : {epoch_name}", (180,200,255)),
                (f"Ennemis elimines : {player.kills}", WHITE),
            ]):
                t = self.font_md.render(text, True, color)
                surface.blit(t, (cx-t.get_width()//2, title_y + 140 + i*42))
        panel_h = 150 if online else 104
        panel = pygame.Surface((620, panel_h), pygame.SRCALPHA)
        panel.fill((20,20,20,160))
        pygame.draw.rect(panel, (80,80,100), panel.get_rect(), 1, border_radius=8)
        panel_y = min(self.h - (188 if online else 126), title_y + 280)
        panel_x = cx - panel.get_width() // 2
        surface.blit(panel, (panel_x, panel_y))
        replay_label = "[R] Voter pour rejouer" if online else "[R] Rejouer"
        control_lines = [
            (replay_label, WHITE),
            ("[M] Menu", (160,200,255)),
            ("[ESC] Quitter", (160,100,100)),
        ]
        for i, (label, color) in enumerate(control_lines):
            t = self.font_md.render(label, True, color)
            surface.blit(t, (panel_x + 22, panel_y + 10 + i * 30))
        if online and replay_status:
            status_y = panel_y + 14
            host_ok = replay_status.get("host_vote", False)
            client_ok = replay_status.get("client_vote", False)
            lines = [
                (f"P1: {'PRET' if host_ok else 'EN ATTENTE'}", GOLD if host_ok else WHITE),
                (f"P2: {'PRET' if client_ok else 'EN ATTENTE'}", CYAN if client_ok else WHITE),
                ("La partie redemarre quand les 2 joueurs ont vote.", (200, 200, 220)),
            ]
            for i, (text, color) in enumerate(lines):
                t = self.font_md.render(text, True, color)
                surface.blit(t, (panel_x + 280, status_y + i * 30))


# ==============================================================================
#  TRANSITION D'EPOQUE
# ==============================================================================

class EpochTransition:
    """Fondu noir entre deux epoques avec affichage du nom."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self._active   = False
        self._timer    = 0
        self._duration = 120
        self._text     = ""
        self._color    = WHITE
        self._callback = None

    @property
    def active(self): return self._active

    def start(self, epoch_key, callback):
        self._active   = True
        self._timer    = 0
        epoch          = EPOCHS.get(epoch_key, {})
        self._text     = epoch.get("display", "")
        self._color    = epoch.get("color", WHITE)
        self._callback = callback

    def update(self):
        if not self._active: return
        self._timer += 1
        if self._timer == self._duration//2 and self._callback:
            self._callback()
        if self._timer >= self._duration:
            self._active = False

    def draw(self, surface):
        if not self._active: return
        t     = self._timer / self._duration
        alpha = int(255*t*2) if t < 0.5 else int(255*(1-t)*2)
        ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ov.fill((0,0,0,alpha)); surface.blit(ov, (0,0))
        if 0.2 < t < 0.8:
            font = pygame.font.Font(None, 72)
            txt  = font.render(self._text, True, self._color)
            txt.set_alpha(alpha)
            surface.blit(txt, (self.w//2-txt.get_width()//2,
                                self.h//2-txt.get_height()//2))


# ==============================================================================
#  CLASSE GAME - ORCHESTRATEUR PRINCIPAL
# ==============================================================================

class Game:
    """
    Orchestre le jeu : etats, evenements, boucle, transitions.

    MODES DE JEU
    -------------------------------------------------------------------------
    Solo   : self.net_mode = "solo"
             current_room.start(skill, mode="solo")
             rendu et logique 100% locaux

    Host   : self.net_mode = "host"
             self.server = GameServer()  (socket UDP ouvert)
             current_room.start(skill, mode="server")
             Chaque frame : server.poll() -> apply_p2_inputs -> update -> serialize -> server.send_state

    Client : self.net_mode = "client"
             self.client = GameClient(ip)
             Chaque frame : client.poll() -> client.send_inputs -> client_renderer.draw(state)
             (pas de simulation locale, rendu pur a partir de l'etat recu)
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        pygame.display.set_caption("Mobius Roguelike")
        self.clock  = pygame.time.Clock()
        sw, sh = SCREEN_WIDTH, SCREEN_HEIGHT

        # -- Fond des menus -----------------------------------------------------
        bg_renderer  = BackgroundRenderer(sw, sh)
        self.menu_bg = bg_renderer.get("futuristique")
        menu_bg = load_optional_scaled_image(
            ("backgrounds", "decor_dj_1.jpg"), size=(sw, sh), alpha=False
        )
        if menu_bg:
            self.menu_bg = menu_bg

        # -- Renderers ---------------------------------------------------------
        self.main_menu_r   = MainMenuRenderer(sw, sh, self.menu_bg)
        self.mode_select_r = ModeSelectRenderer(sw, sh, self.menu_bg)
        self.online_menu_r = OnlineMenuRenderer(sw, sh, self.menu_bg)
        self.ip_input_r    = IPInputRenderer(sw, sh, self.menu_bg)
        self.waiting_r     = WaitingRenderer(sw, sh, self.menu_bg)
        self.menu_r        = MenuRenderer(sw, sh, self.menu_bg)
        self.gameover_r    = GameOverRenderer(sw, sh, self.menu_bg)
        self.transition    = EpochTransition(sw, sh)
        self.volume_slider = VolumeSlider()
        self.music         = MusicManager()
        self.sfx           = SoundManager()
        # Renderer client (cree quand on joue cote client)
        self.client_renderer: ClientRenderer | None = None

        # -- Etat courant -------------------------------------------------------
        self.game_state     = MAIN_MENU
        self.selected_skill = None
        self.current_epoch  = "prehistoire"
        self.player_skill   = None

        # -- Reseau ------------------------------------------------------------
        # net_mode : "solo" | "host" | "client"
        self.net_mode: str       = "solo"
        self.server:   GameServer | None = None   # Instance du serveur (host)
        self.client:   GameClient | None = None   # Instance du client

        # Thread de connexion (utilise pour connect sans bloquer l'UI)
        self._conn_thread: threading.Thread | None = None
        self._conn_error:  str = ""   # Message d'erreur de connexion
        self._conn_success: bool = False
        self._pending_skill: str = ""
        self._pending_ip:   str = ""
        self._conn_deadline: float = 0.0
        self._local_ip_cache: str = get_local_ip()   # calcule une seule fois
        self._host_replay_vote = False
        self._client_replay_vote = False
        self._client_prev_buttons = {"dash": False, "skill": False, "fire": False, "alt_fire": False, "chest": False}
        self._last_client_sfx_frame = -1

        # -- Salles -------------------------------------------------------------
        self.rooms: dict = {
            "prehistoire":  PrehistoireRoom(self),
            "grece":        GreceRoom(self),
            "edo":          EdoRoom(self),
            "moderne":      ModerneRoom(self),
            "contemporain": ContemporainRoom(self),
            "futuristique": FuturistiqueRoom(self),
        }
        self.current_room = None

    # -- Demarrage -------------------------------------------------------------

    def start_game(self, skill: str):
        """
        Lance la partie dans le mode reseau courant (self.net_mode).

        Solo   : demarre normalement
        Host   : demarre en mode "server", signal start au client
        Client : ne demarre PAS de simulation locale (rendu pur via client_renderer)
        """
        self.player_skill  = skill
        self.current_epoch = "prehistoire"
        self.current_room  = self.rooms["prehistoire"]
        self._host_replay_vote = False
        self._client_replay_vote = False
        self._client_prev_buttons = {"dash": False, "skill": False, "fire": False, "alt_fire": False, "chest": False}
        self._last_client_sfx_frame = -1

        if self.net_mode == "solo":
            # -- Solo : mode classique ------------------------------------------
            self.current_room.start(skill, mode="solo")

        elif self.net_mode == "host":
            # -- Host : demarrer le serveur et la simulation --------------------
            p2_skill = self.server.p2_skill if self.server else "tank"
            self.current_room.start(skill, mode="server", skill2=p2_skill)
            # Signaler au client que la partie commence (lui envoyer la classe P1)
            if self.server:
                self.server.reset_replay_votes()
                self.server.send_start(skill)

        elif self.net_mode == "client":
            # -- Client : pas de simulation, juste le renderer -----------------
            # Le client n'appelle pas current_room.start() - tout vient du serveur
            if self.client_renderer is None:
                self.client_renderer = ClientRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.game_state = PLAYING

    def change_epoch(self, next_epoch: str | None):
        """Transition vers l'epoque suivante (host uniquement)."""
        if next_epoch and next_epoch in self.rooms and next_epoch != "None":
            p = self.current_room.player
            stats = {"skill": p.skill, "kills": p.kills,
                     "health": p.health, "max_health": p.max_health,
                     "stamina": p.stamina, "max_stamina": p.max_stamina}

            # Stats P2 reseau (si present cote host)
            p2_stats = None
            if self.net_mode == "host" and self.current_room.player2:
                p2 = self.current_room.player2
                p2_stats = {"skill": p2.skill, "kills": p2.kills,
                            "health": p2.health, "max_health": p2.max_health,
                            "stamina": p2.stamina, "max_stamina": p2.max_stamina}

            def _do():
                self.current_epoch = next_epoch
                self.current_room  = self.rooms[next_epoch]
                p2_skill = p2_stats["skill"] if p2_stats else None
                room_mode = "server" if self.net_mode == "host" else "solo"
                self.current_room.start(stats["skill"], player_stats=stats,
                                        mode=room_mode,
                                        skill2=p2_skill,
                                        player2_stats=p2_stats)
                if self.server:
                    self.server.send_start(stats["skill"])
            self.transition.start(next_epoch, _do)
        else:
            self.game_state = GAME_OVER

    # -- Fermeture propre du reseau ---------------------------------------------

    def _close_network(self):
        """Ferme les sockets reseau proprement."""
        if self.server:
            self.server.close()
            self.server = None
        if self.client:
            self.client.close()
            self.client = None
        self.net_mode = "solo"
        self._conn_error = ""
        self._conn_success = False
        self._pending_skill = ""
        self._host_replay_vote = False
        self._client_replay_vote = False
        self._pending_ip = ""
        self._conn_deadline = 0.0
        self._client_prev_buttons = {"dash": False, "skill": False, "fire": False, "alt_fire": False, "chest": False}
        self._last_client_sfx_frame = -1

    def _update_music(self):
        if self.game_state in (MAIN_MENU, MODE_SELECT, ONLINE_MENU, IP_INPUT, WAITING_CLIENT, CONNECTING, CHARACTER_SELECT):
            self.music.play("menu")
            return
        if self.game_state == GAME_OVER:
            self.music.play("defeat")
            return
        if self.game_state == PLAYING:
            if self.net_mode == "client" and self.client:
                state = self.client.get_state()
                music_key = state.get("music_key") or state.get("mk")
                if music_key in MusicManager.TRACKS:
                    self.music.play(music_key)
                    return
                is_boss = bool(state.get("boss_wave") or state.get("bw"))
                self.music.play("game_boss" if is_boss else "game_normal")
                return
            if self.current_room:
                self.music.play("game_boss" if self.current_room.boss_wave else "game_normal")

    def _sync_audio_volume(self):
        vol = self.volume_slider.volume
        self.music.set_volume(vol)
        self.sfx.set_volume(vol)

    def _play_client_sound_events(self):
        if self.net_mode != "client" or not self.client:
            return
        state = self.client.get_state()
        frame = int(state.get("f", -1) or -1)
        if frame <= self._last_client_sfx_frame:
            return
        self._last_client_sfx_frame = frame
        for key in state.get("sound_events", []) or state.get("sx", []):
            self.sfx.play(key)

    # -- Boucle principale -----------------------------------------------------

    def run(self):
        running = True
        while running:
            self.clock.tick(60)
            self.music.update()
            self._update_music()
            self._sync_audio_volume()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.volume_slider.handle_event(event)

                if self.game_state == MAIN_MENU:
                    running = self._handle_main_menu(event, running)
                elif self.game_state == MODE_SELECT:
                    running = self._handle_mode_select(event, running)
                elif self.game_state == ONLINE_MENU:
                    running = self._handle_online_menu(event, running)
                elif self.game_state == IP_INPUT:
                    running = self._handle_ip_input(event, running)
                elif self.game_state == WAITING_CLIENT:
                    running = self._handle_waiting(event, running)
                elif self.game_state == CONNECTING:
                    running = self._handle_connecting(event, running)
                elif self.game_state == CHARACTER_SELECT:
                    running = self._handle_character_select(event, running)
                elif self.game_state == PLAYING and not self.transition.active:
                    if self.net_mode != "client":
                        result = self.current_room.handle_event(event)
                        if result == "MENU":
                            self._close_network()
                            self.game_state = MAIN_MENU
                        elif result == "GAME_OVER":
                            self.game_state = GAME_OVER
                    else:
                        # Client : ESC = quitter
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                            self._close_network()
                            self.game_state = MAIN_MENU
                elif self.game_state == GAME_OVER:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            if self.net_mode == "host" and self.server:
                                self._host_replay_vote = True
                                self.server.set_host_replay_vote(True)
                            elif self.net_mode == "client" and self.client:
                                self._client_replay_vote = True
                                self.client.send_replay_vote(True)
                            else:
                                self._close_network()
                                self.start_game(self.player_skill)
                        elif event.key == pygame.K_m:
                            self._close_network()
                            self.game_state = MAIN_MENU
                        elif event.key == pygame.K_ESCAPE:
                            running = False

            self.volume_slider.update()

            # -- CONNECTING : detecter connexion reussie ------------------------
            if self.game_state == CONNECTING:
                if self.client:
                    self.client.poll()
                    if self.client.connected:
                        self._conn_success = False
                        self.start_game(self._pending_skill)
                    elif time.time() > self._conn_deadline:
                        self._conn_error = "ERREUR : Impossible de joindre le serveur (timeout)"
                        self.game_state = IP_INPUT

            if self.game_state == GAME_OVER:
                if self.net_mode == "host" and self.server:
                    self.server.poll()
                    self._host_replay_vote, self._client_replay_vote = self.server.get_replay_votes()
                    if self.server.connected:
                        self.server.send_replay_status()
                    if self.server.connected and self._host_replay_vote and self._client_replay_vote:
                        self.server.send_replay_begin(self.player_skill)
                        self.start_game(self.player_skill)
                elif self.net_mode == "client" and self.client:
                    self.client.poll()
                    self._host_replay_vote = self.client.host_replay_vote
                    self._client_replay_vote = self.client.client_replay_vote
                    if self.client.consume_replay_begin():
                        self.start_game(self.player_skill)

            # -- PLAYING : logique reseau + update ------------------------------
            if self.game_state == PLAYING:
                self.transition.update()

                if self.net_mode == "host" and self.server:
                    # 1. Lire les paquets entrants du client
                    self.server.poll()
                    # 2. Appliquer les inputs P2 recus avant la simulation
                    inputs = self.server.get_client_inputs()
                    if self.current_room and self.current_room.player2:
                        self.current_room.apply_p2_network_inputs(inputs)
                    # 3. Verifier deconnexion client
                    if self.server.is_client_timeout(8.0):
                        print("[HOST] Client deconnecte (timeout)")
                        self._close_network()
                        self.game_state = GAME_OVER

                elif self.net_mode == "client" and self.client:
                    # 1. Lire les paquets entrants (etat du jeu)
                    self.client.poll()
                    self._play_client_sound_events()
                    # 2. Envoyer nos inputs au serveur
                    inputs = self._collect_client_inputs()
                    self.client.send_inputs(inputs)
                    # 3. Verifier si le serveur a signale game over ou epoch change
                    state = self.client.get_state()
                    if state.get("game_over") or state.get("go") or self.client.remote_game_over:
                        self.game_state = GAME_OVER
                    if self.client.is_server_timeout(8.0):
                        print("[CLIENT] Serveur deconnecte (timeout)")
                        self._close_network()
                        self.game_state = MAIN_MENU

                if (not self.transition.active and self.net_mode != "client"
                        and self.current_room and self.current_room.player is not None):
                    result = self.current_room.update()
                    if result is True:
                        self.game_state = GAME_OVER
                    elif isinstance(result, str) and result.startswith("NEXT_EPOCH:"):
                        self.change_epoch(result.split(":")[1])
                    # Cote host : envoyer l'etat apres update
                    if self.net_mode == "host" and self.server and self.server.connected:
                        state = self.current_room.serialize_state()
                        self.server.send_state(state)

            # -- Rendu ---------------------------------------------------------
            if self.game_state == MAIN_MENU:
                self.main_menu_r.draw(self.screen)
                self.volume_slider.draw(self.screen)
            elif self.game_state == MODE_SELECT:
                self.mode_select_r.draw(self.screen)
                self.volume_slider.draw(self.screen)
            elif self.game_state == ONLINE_MENU:
                self.online_menu_r.draw(self.screen)
                self.volume_slider.draw(self.screen)
            elif self.game_state == IP_INPUT:
                self.ip_input_r.draw(self.screen)
                self.volume_slider.draw(self.screen)
            elif self.game_state == WAITING_CLIENT:
                # poll() ici pour recevoir le hello de P2
                if self.server:
                    self.server.poll()
                status = "Connecte !" if (self.server and self.server.connected) else "En attente..."
                self.waiting_r.draw(self.screen,
                    "En attente de P2...",
                    [f"Votre IP : {self._local_ip_cache}",
                     f"Port UDP : {DEFAULT_PORT}",
                     f"Etat : {status}",
                     "Communiquez votre IP a P2"])
                self.volume_slider.draw(self.screen)
                if self.server and self.server.connected:
                    self.game_state = CHARACTER_SELECT
            elif self.game_state == CONNECTING:
                err = self._conn_error or "Tentative de connexion..."
                self.waiting_r.draw(self.screen,
                    "Connexion...",
                    [f"Serveur : {self.ip_input_r.ip_text}:{DEFAULT_PORT}",
                     err])
                self.volume_slider.draw(self.screen)
                if self._conn_error and self._conn_error.startswith("ERREUR"):
                    self.game_state = IP_INPUT
            elif self.game_state == CHARACTER_SELECT:
                lbl = ""
                if self.net_mode == "host":
                    lbl = "HOST - Choisissez votre classe (P1)"
                elif self.net_mode == "client":
                    lbl = "CLIENT - Choisissez votre classe (P2)"
                self.menu_r.draw(self.screen, self.selected_skill, mode_label=lbl)
                self.volume_slider.draw(self.screen)
            elif self.game_state == PLAYING:
                if self.net_mode == "client" and self.client:
                    state = self.client.get_state()
                    if state and self.client_renderer:
                        self.client_renderer.draw(self.screen, state)
                    else:
                        draw_bg_overlay(self.screen, self.menu_bg, SCREEN_WIDTH, SCREEN_HEIGHT, 200)
                        f = pygame.font.Font(None, 42)
                        t = f.render("En attente de donnees du serveur...", True, WHITE)
                        self.screen.blit(t, (SCREEN_WIDTH//2-t.get_width()//2, SCREEN_HEIGHT//2))
                else:
                    self.current_room.draw(self.screen)
                    self.transition.draw(self.screen)
            elif self.game_state == GAME_OVER:
                p = None
                replay_status = None
                if self.net_mode == "client" and self.client:
                    state = self.client.get_state()
                    # Pas d'objet Player cote client : afficher l'ecran sans stats
                elif self.current_room:
                    p = self.current_room.player
                if self.net_mode in ("host", "client"):
                    replay_status = {
                        "host_vote": self._host_replay_vote,
                        "client_vote": self._client_replay_vote,
                    }
                self.gameover_r.draw(self.screen, p, self.current_epoch,
                                     replay_status=replay_status,
                                     online=(self.net_mode in ("host", "client")))
                self.volume_slider.draw(self.screen)

            pygame.display.flip()

        self._close_network()
        pygame.quit()
        sys.exit()

    # -- Collecte des inputs P2 cote client ------------------------------------

    def _collect_client_inputs(self) -> dict:
        """
        Capture les inputs locaux du client (P2) et les formate pour l'envoi.
        Appele chaque frame cote client.

        Les controles de P2 (client) sont identiques a P1 (ZQSD + souris)
        car chaque joueur joue sur son propre PC.
        """
        keys = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_pos()
        mouse  = pygame.mouse.get_pressed()

        # Direction de deplacement normalisee
        dx = dy = 0.0
        if keys[pygame.K_d]: dx += 1
        if keys[pygame.K_q] or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_s]: dy += 1
        if keys[pygame.K_z] or keys[pygame.K_w]: dy -= 1
        norm = math.hypot(dx, dy) or 1
        if dx or dy:
            dx /= norm; dy /= norm

        dash_pressed = bool(keys[pygame.K_SPACE])
        skill_pressed = bool(keys[pygame.K_f])
        fire_pressed = bool(mouse[0])
        alt_fire_pressed = bool(mouse[2])
        chest_pressed = bool(keys[pygame.K_e])

        dash_edge = dash_pressed and not self._client_prev_buttons["dash"]
        skill_edge = skill_pressed and not self._client_prev_buttons["skill"]
        fire_edge = fire_pressed and not self._client_prev_buttons["fire"]
        alt_fire_edge = alt_fire_pressed and not self._client_prev_buttons["alt_fire"]
        self._client_prev_buttons = {
            "dash": dash_pressed,
            "skill": skill_pressed,
            "fire": fire_pressed,
            "alt_fire": alt_fire_pressed,
            "chest": chest_pressed,
        }

        weapon_idx = -1
        for i in range(9):
            if keys[getattr(pygame, f"K_{i + 1}")]:
                weapon_idx = i
                break

        return {
            "dx":        dx,
            "dy":        dy,
            "aim_x":     mx,
            "aim_y":     my,
            "dash":      dash_edge,
            "skill":     skill_edge,
            "fire":      fire_edge,
            "alt_fire":  alt_fire_edge,
            "fire_tx":   mx,
            "fire_ty":   my,
            "chest":     chest_pressed,
            "weapon_idx": weapon_idx,
        }

    # -- Gestionnaires d'evenements --------------------------------------------

    def _handle_main_menu(self, event, running) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: return False
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.game_state = MODE_SELECT
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.main_menu_r.get_play_rect().collidepoint(mx, my):
                self.game_state = MODE_SELECT
            elif self.main_menu_r.get_quit_rect().collidepoint(mx, my):
                pygame.quit(); sys.exit()
        return running

    def _handle_mode_select(self, event, running) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_state = MAIN_MENU
            elif event.key == pygame.K_1:
                self.net_mode = "solo"
                self.game_state = CHARACTER_SELECT
            elif event.key == pygame.K_2:
                self.game_state = ONLINE_MENU
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.mode_select_r.get_solo_rect().collidepoint(mx, my):
                self.net_mode = "solo"
                self.game_state = CHARACTER_SELECT
            elif self.mode_select_r.get_online_rect().collidepoint(mx, my):
                self.game_state = ONLINE_MENU
        return running

    def _handle_online_menu(self, event, running) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game_state = MODE_SELECT
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            r = self.online_menu_r
            if r.get_host_rect().collidepoint(mx, my):
                # -- Creer le serveur UDP ---------------------------------------
                try:
                    self.server   = GameServer(DEFAULT_PORT)
                    self.net_mode = "host"
                    self.game_state = WAITING_CLIENT
                except OSError as e:
                    print(f"[HOST] Erreur creation serveur : {e}")
                    # Afficher l'erreur dans l'ecran waiting (provisoire)
                    self._conn_error = f"Erreur : {e}"
            elif r.get_join_rect().collidepoint(mx, my):
                self.ip_input_r.ip_text  = ""
                self.ip_input_r.error_msg= ""
                self.game_state = IP_INPUT
            elif r.get_back_rect().collidepoint(mx, my):
                self.game_state = MODE_SELECT
        return running

    def _handle_ip_input(self, event, running) -> bool:
        if event.type == pygame.KEYDOWN:
            action = self.ip_input_r.handle_keydown(event)
            if action == "back":
                self.game_state = ONLINE_MENU
            elif action == "connect":
                if self.ip_input_r.validate_ip():
                    self._pending_ip = self.ip_input_r.ip_text.strip()
                    self.net_mode = "client"
                    self.game_state = CHARACTER_SELECT
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.ip_input_r.get_connect_rect().collidepoint(mx, my):
                if self.ip_input_r.validate_ip():
                    self._pending_ip = self.ip_input_r.ip_text.strip()
                    self.net_mode = "client"
                    self.game_state = CHARACTER_SELECT
            elif self.ip_input_r.get_back_rect().collidepoint(mx, my):
                self.game_state = ONLINE_MENU
        return running

    def _start_connection(self, ip: str, skill: str):
        if self.client:
            self.client.close()
            self.client = None
        self._conn_error   = ""
        self._conn_success = False
        self._pending_skill = skill
        self._conn_deadline = time.time() + 10.0
        self.client = GameClient(ip, DEFAULT_PORT)
        self.client.connect(skill)
        self.game_state = CONNECTING

    def _handle_waiting(self, event, running) -> bool:
        """Host : annuler l'attente de P2."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close_network()
            self.game_state = ONLINE_MENU
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.waiting_r.get_cancel_rect().collidepoint(*event.pos):
                self._close_network()
                self.game_state = ONLINE_MENU
        return running

    def _handle_connecting(self, event, running) -> bool:
        """Client : annuler la tentative de connexion."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close_network()
            self.game_state = ONLINE_MENU
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.waiting_r.get_cancel_rect().collidepoint(*event.pos):
                self._close_network()
                self.game_state = ONLINE_MENU
        return running

    def _handle_character_select(self, event, running) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.net_mode != "solo":
                    self._close_network()
                    self.game_state = ONLINE_MENU
                else:
                    self.game_state = MODE_SELECT
                return running
            for i, sk in enumerate(list(SKILLS.keys())):
                if event.key == pygame.K_1 + i:
                    if self.net_mode == "client":
                        self._start_connection(self._pending_ip, sk)
                    else:
                        self.start_game(sk)
                    return running
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.menu_r.get_card_rects().items():
                if rect.collidepoint(*event.pos):
                    if self.net_mode == "client":
                        self._start_connection(self._pending_ip, key)
                    else:
                        self.start_game(key)
                    return running
        elif event.type == pygame.MOUSEMOTION:
            self.selected_skill = None
            for key, rect in self.menu_r.get_card_rects().items():
                if rect.collidepoint(*event.pos):
                    self.selected_skill = key
        return running


# ==============================================================================
if __name__ == "__main__":
    game = Game()
    game.run()
