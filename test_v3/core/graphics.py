# -*- coding: utf-8 -*-
# core/graphics.py - Systeme graphique centralise pour Mobius Roguelike

"""
Gere :
   -  Chargement & cache des sprites
   -  Generation procedurale des backgrounds par epoque
   -  Rendu HUD (barres HP/Stamina, vague, stats)
   -  Systeme de particules (sang, explosion, magie)
   -  Effets visuels (flash, screen-shake, degats flottants)
"""

import pygame
import math
import random
from .constants import *

EPOCH_BACKGROUND_ASSETS = {
    "prehistoire": ("backgrounds", "decor_dj_1.jpg"),
    "grece": ("backgrounds", "decor_dj_2.jpg"),
    "edo": ("backgrounds", "decor_dj_3.jpg"),
    "futuristique": ("backgrounds", "decor_dj_6.jpg"),
}


# ==============================================================================
#  CACHE DE SPRITES
# ==============================================================================

class SpriteCache:
    """Charge et met en cache tous les sprites du jeu."""

    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._cache = {}

    def asset_exists(self, *path_parts) -> bool:
        """Retourne True si l'asset existe sur disque pour ce client/host local."""
        try:
            return Path(get_asset_path(*path_parts)).is_file()
        except Exception:
            return False

    def load(self, *path_parts, size=None, alpha=True):
        """Charge un sprite (avec cache). size=(w,h) optionnel."""
        key = (path_parts, size)
        if key in self._cache:
            return self._cache[key]

        full_path = get_asset_path(*path_parts)
        try:
            if alpha:
                img = pygame.image.load(full_path).convert_alpha()
            else:
                img = pygame.image.load(full_path).convert()
            if size:
                img = pygame.transform.scale(img, size)
        except Exception:
            img = self._make_fallback(size or (64, 64), path_parts)

        self._cache[key] = img
        return img

    def load_sheet(self, *path_parts, cols=3, rows=3, size=None, alpha=True, trim=True):
        """Charge et decoupe une sprite sheet en grille reguliere."""
        key = ("sheet", path_parts, cols, rows, size, alpha, trim)
        if key in self._cache:
            return self._cache[key]

        full_path = get_asset_path(*path_parts)
        try:
            if alpha:
                sheet = pygame.image.load(full_path).convert_alpha()
            else:
                sheet = pygame.image.load(full_path).convert()
        except Exception:
            fallback = [[self._make_fallback(size or (64, 64), path_parts) for _ in range(cols)]
                        for _ in range(rows)]
            self._cache[key] = fallback
            return fallback

        sheet_w, sheet_h = sheet.get_size()
        frames = []
        for row in range(rows):
            row_frames = []
            top = round(row * sheet_h / rows)
            bottom = round((row + 1) * sheet_h / rows)
            for col in range(cols):
                left = round(col * sheet_w / cols)
                right = round((col + 1) * sheet_w / cols)
                cell_rect = pygame.Rect(left, top, right - left, bottom - top)
                cell = pygame.Surface(cell_rect.size, pygame.SRCALPHA)
                cell.blit(sheet, (0, 0), cell_rect)

                if trim:
                    bbox = cell.get_bounding_rect(min_alpha=1)
                    if bbox.width > 0 and bbox.height > 0:
                        trimmed = pygame.Surface((bbox.width, bbox.height), pygame.SRCALPHA)
                        trimmed.blit(cell, (0, 0), bbox)
                    else:
                        trimmed = cell
                else:
                    trimmed = cell

                if size:
                    max_w = max(1, size[0] - 4)
                    max_h = max(1, size[1] - 4)
                    ratio = min(max_w / trimmed.get_width(), max_h / trimmed.get_height())
                    scaled_size = (
                        max(1, int(trimmed.get_width() * ratio)),
                        max(1, int(trimmed.get_height() * ratio)),
                    )
                    trimmed = pygame.transform.scale(trimmed, scaled_size)
                    frame = pygame.Surface(size, pygame.SRCALPHA)
                    frame.blit(
                        trimmed,
                        ((size[0] - trimmed.get_width()) // 2, size[1] - trimmed.get_height()),
                    )
                else:
                    frame = trimmed
                row_frames.append(frame)
            frames.append(row_frames)

        self._cache[key] = frames
        return frames

    def load_frames(self, *path_parts, frame_rects, size=None, alpha=True, trim=True, common_scale=False,
                    bbox_anchor=False):
        """Charge une sprite sheet et extrait une liste de frames explicites."""
        key = ("frames", path_parts, tuple(tuple(r) for r in frame_rects), size, alpha, trim, common_scale, bbox_anchor)
        if key in self._cache:
            return self._cache[key]

        full_path = get_asset_path(*path_parts)
        try:
            if alpha:
                sheet = pygame.image.load(full_path).convert_alpha()
            else:
                sheet = pygame.image.load(full_path).convert()
        except Exception:
            fallback = [self._make_fallback(size or (64, 64), path_parts) for _ in frame_rects]
            self._cache[key] = fallback
            return fallback

        prepared = []
        common_w = max((rect[2] for rect in frame_rects), default=1)
        common_h = max((rect[3] for rect in frame_rects), default=1)
        common_ratio = None
        if size and common_scale:
            max_w = max(1, size[0] - 4)
            max_h = max(1, size[1] - 4)
            common_ratio = min(max_w / common_w, max_h / common_h)
        for left, top, width, height in frame_rects:
            cell = pygame.Surface((width, height), pygame.SRCALPHA)
            cell.blit(sheet, (0, 0), pygame.Rect(left, top, width, height))
            bbox = cell.get_bounding_rect(min_alpha=1)
            prepared.append((cell, bbox, width, height))

        ref_center_x = None
        ref_bottom_y = None
        if size and bbox_anchor and prepared:
            centers = []
            bottoms = []
            for _, bbox, width, height in prepared:
                ratio = common_ratio if common_ratio is not None else min(
                    max(1, size[0] - 4) / max(1, width),
                    max(1, size[1] - 4) / max(1, height),
                )
                base_x = (size[0] - width * ratio) / 2
                base_y = size[1] - height * ratio
                centers.append(base_x + ((bbox.left + bbox.right) / 2) * ratio)
                bottoms.append(base_y + bbox.bottom * ratio)
            ref_center_x = sum(centers) / len(centers)
            ref_bottom_y = max(bottoms)

        frames = []
        for cell, bbox, width, height in prepared:
            if trim:
                if bbox.width > 0 and bbox.height > 0:
                    trimmed = pygame.Surface((bbox.width, bbox.height), pygame.SRCALPHA)
                    trimmed.blit(cell, (0, 0), bbox)
                else:
                    trimmed = cell
            else:
                trimmed = cell

            if size:
                if common_ratio is not None:
                    ratio = common_ratio
                else:
                    max_w = max(1, size[0] - 4)
                    max_h = max(1, size[1] - 4)
                    ratio = min(max_w / trimmed.get_width(), max_h / trimmed.get_height())
                scaled_size = (
                    max(1, int(trimmed.get_width() * ratio)),
                    max(1, int(trimmed.get_height() * ratio)),
                )
                trimmed = pygame.transform.scale(trimmed, scaled_size)
                frame = pygame.Surface(size, pygame.SRCALPHA)
                if bbox_anchor and not trim and ref_center_x is not None and ref_bottom_y is not None:
                    target_x = ref_center_x - ((bbox.left + bbox.right) / 2) * ratio
                    target_y = ref_bottom_y - bbox.bottom * ratio
                    frame.blit(trimmed, (int(round(target_x)), int(round(target_y))))
                else:
                    frame.blit(
                        trimmed,
                        ((size[0] - trimmed.get_width()) // 2, size[1] - trimmed.get_height()),
                    )
            else:
                frame = trimmed
            frames.append(frame)

        self._cache[key] = frames
        return frames

    def load_gif_frames(self, *path_parts, size=None, trim=True, bg_key_from_corner=True):
        """Charge toutes les frames d'un GIF en surfaces pygame."""
        key = ("gif_frames", path_parts, size, trim, bg_key_from_corner)
        if key in self._cache:
            return self._cache[key]

        try:
            from PIL import Image, ImageChops, ImageSequence
        except Exception:
            fallback = [self._make_fallback(size or (64, 64), path_parts)]
            self._cache[key] = fallback
            return fallback

        full_path = get_asset_path(*path_parts)
        try:
            gif = Image.open(full_path)
        except Exception:
            fallback = [self._make_fallback(size or (64, 64), path_parts)]
            self._cache[key] = fallback
            return fallback

        frames = []
        for frame in ImageSequence.Iterator(gif):
            rgba = frame.convert("RGBA")
            if bg_key_from_corner:
                bg = rgba.getpixel((0, 0))
                bg_rgb = Image.new("RGB", rgba.size, bg[:3])
                diff = ImageChops.difference(rgba.convert("RGB"), bg_rgb)
                mask = diff.convert("L").point(lambda v: 0 if v == 0 else 255)
                rgba.putalpha(mask)

            mode = rgba.mode
            data = rgba.tobytes()
            surf = pygame.image.fromstring(data, rgba.size, mode).convert_alpha()

            if trim:
                bbox = surf.get_bounding_rect(min_alpha=1)
                if bbox.width > 0 and bbox.height > 0:
                    trimmed = pygame.Surface((bbox.width, bbox.height), pygame.SRCALPHA)
                    trimmed.blit(surf, (0, 0), bbox)
                else:
                    trimmed = surf
            else:
                trimmed = surf

            if size:
                max_w = max(1, size[0] - 4)
                max_h = max(1, size[1] - 4)
                ratio = min(max_w / trimmed.get_width(), max_h / trimmed.get_height())
                scaled_size = (
                    max(1, int(trimmed.get_width() * ratio)),
                    max(1, int(trimmed.get_height() * ratio)),
                )
                trimmed = pygame.transform.scale(trimmed, scaled_size)
                canvas = pygame.Surface(size, pygame.SRCALPHA)
                canvas.blit(
                    trimmed,
                    ((size[0] - trimmed.get_width()) // 2, size[1] - trimmed.get_height()),
                )
                surf = canvas
            else:
                surf = trimmed

            frames.append(surf)

        if not frames:
            frames = [self._make_fallback(size or (64, 64), path_parts)]

        self._cache[key] = frames
        return frames

    def load_gif_frames_optional(self, *path_parts, size=None, trim=True, bg_key_from_corner=True):
        """
        Variante stricte : retourne None si le GIF n'est pas reellement chargeable.
        Permet aux appelants d'utiliser un vrai fallback PNG/sheet.
        """
        try:
            from PIL import Image, ImageChops, ImageSequence
        except Exception:
            return None

        full_path = get_asset_path(*path_parts)
        try:
            gif = Image.open(full_path)
        except Exception:
            return None

        frames = []
        for frame in ImageSequence.Iterator(gif):
            rgba = frame.convert("RGBA")
            if bg_key_from_corner:
                bg = rgba.getpixel((0, 0))
                bg_rgb = Image.new("RGB", rgba.size, bg[:3])
                diff = ImageChops.difference(rgba.convert("RGB"), bg_rgb)
                mask = diff.convert("L").point(lambda v: 0 if v == 0 else 255)
                rgba.putalpha(mask)

            mode = rgba.mode
            data = rgba.tobytes()
            surf = pygame.image.fromstring(data, rgba.size, mode).convert_alpha()

            if trim:
                bbox = surf.get_bounding_rect(min_alpha=1)
                if bbox.width > 0 and bbox.height > 0:
                    trimmed = pygame.Surface((bbox.width, bbox.height), pygame.SRCALPHA)
                    trimmed.blit(surf, (0, 0), bbox)
                else:
                    trimmed = surf
            else:
                trimmed = surf

            if size:
                max_w = max(1, size[0] - 4)
                max_h = max(1, size[1] - 4)
                ratio = min(max_w / trimmed.get_width(), max_h / trimmed.get_height())
                scaled_size = (
                    max(1, int(trimmed.get_width() * ratio)),
                    max(1, int(trimmed.get_height() * ratio)),
                )
                trimmed = pygame.transform.scale(trimmed, scaled_size)
                canvas = pygame.Surface(size, pygame.SRCALPHA)
                canvas.blit(
                    trimmed,
                    ((size[0] - trimmed.get_width()) // 2, size[1] - trimmed.get_height()),
                )
                surf = canvas
            else:
                surf = trimmed

            frames.append(surf)

        return frames or None

    def load_strip_frames(self, *path_parts, size=None, alpha=True, trim=True, frame_width=None):
        """Charge une bande horizontale de frames de taille reguliere."""
        key = ("strip_frames", path_parts, size, alpha, trim, frame_width)
        if key in self._cache:
            return self._cache[key]

        full_path = get_asset_path(*path_parts)
        try:
            if alpha:
                sheet = pygame.image.load(full_path).convert_alpha()
            else:
                sheet = pygame.image.load(full_path).convert()
        except Exception:
            fallback = [self._make_fallback(size or (64, 64), path_parts)]
            self._cache[key] = fallback
            return fallback

        sheet_w, sheet_h = sheet.get_size()
        cell_w = frame_width or sheet_h
        if cell_w <= 0:
            cell_w = sheet_h or 1
        frame_count = max(1, sheet_w // cell_w)
        frames = []
        for index in range(frame_count):
            left = index * cell_w
            width = min(cell_w, sheet_w - left)
            cell_rect = pygame.Rect(left, 0, width, sheet_h)
            cell = pygame.Surface(cell_rect.size, pygame.SRCALPHA)
            cell.blit(sheet, (0, 0), cell_rect)

            if trim:
                bbox = cell.get_bounding_rect(min_alpha=1)
                if bbox.width > 0 and bbox.height > 0:
                    trimmed = pygame.Surface((bbox.width, bbox.height), pygame.SRCALPHA)
                    trimmed.blit(cell, (0, 0), bbox)
                else:
                    trimmed = cell
            else:
                trimmed = cell

            if size:
                max_w = max(1, size[0] - 4)
                max_h = max(1, size[1] - 4)
                ratio = min(max_w / trimmed.get_width(), max_h / trimmed.get_height())
                scaled_size = (
                    max(1, int(trimmed.get_width() * ratio)),
                    max(1, int(trimmed.get_height() * ratio)),
                )
                trimmed = pygame.transform.scale(trimmed, scaled_size)
                frame = pygame.Surface(size, pygame.SRCALPHA)
                frame.blit(
                    trimmed,
                    ((size[0] - trimmed.get_width()) // 2, size[1] - trimmed.get_height()),
                )
            else:
                frame = trimmed
            frames.append(frame)

        self._cache[key] = frames
        return frames

    def load_weapon(self, weapon_key, size=None):
        data = WEAPONS_DATA.get(weapon_key, {})
        sprite_path = data.get("sprite")
        fallback_color = data.get("fallback_color", GRAY)
        target_size = size or (data.get("size", 50), data.get("size", 50))

        if sprite_path:
            try:
                img = pygame.image.load(get_asset_path(*sprite_path)).convert_alpha()
                img = pygame.transform.scale(img, target_size)
                return img
            except Exception:
                pass

        # Fallback dessine
        surf = pygame.Surface(target_size, pygame.SRCALPHA)
        pygame.draw.ellipse(surf, fallback_color, (0, 0, *target_size))
        pygame.draw.ellipse(surf, WHITE, (0, 0, *target_size), 2)
        label = data.get("name", weapon_key).upper()[:3]
        font = pygame.font.Font(None, max(12, target_size[1] // 3))
        txt = font.render(label, True, WHITE)
        surf.blit(txt, (target_size[0] // 2 - txt.get_width() // 2,
                        target_size[1] // 2 - txt.get_height() // 2))
        return surf

    @staticmethod
    def _make_fallback(size, path_parts):
        """Surface placeholder coloree si le fichier est absent."""
        surf = pygame.Surface(size, pygame.SRCALPHA)
        color = (random.randint(80, 200), random.randint(80, 200), random.randint(80, 200), 200)
        pygame.draw.rect(surf, color, surf.get_rect(), border_radius=6)
        font = pygame.font.Font(None, max(12, size[1] // 4))
        txt = font.render(str(path_parts[-1])[:8], True, WHITE)
        surf.blit(txt, (2, size[1] // 2 - txt.get_height() // 2))
        return surf


# ==============================================================================
#  BACKGROUNDS PROCEDURAUX PAR EPOQUE
# ==============================================================================

class BackgroundRenderer:
    """Genere et rend les backgrounds thematiques de chaque epoque."""

    def __init__(self, screen_w, screen_h):
        self.w = screen_w
        self.h = screen_h
        self._surfaces = {}

    # -- API publique --------------------------------------------------------

    def get(self, epoch_key):
        """Retourne (et genere si besoin) la surface de fond pour l'epoque."""
        if epoch_key not in self._surfaces:
            self._surfaces[epoch_key] = self._build(epoch_key)
        return self._surfaces[epoch_key]

    def _build(self, epoch_key):
        """Charge un fond dedie a l'epoque si disponible, sinon genere proceduralement."""
        asset_parts = EPOCH_BACKGROUND_ASSETS.get(epoch_key)
        if asset_parts:
            try:
                img = pygame.image.load(get_asset_path(*asset_parts)).convert()
                img = pygame.transform.scale(img, (self.w, self.h))
                tint = EPOCHS[epoch_key]["bg_tint"]
                overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
                overlay.fill((*tint, 45))
                img.blit(overlay, (0, 0))
                return img
            except Exception:
                pass
        return self._generate(epoch_key)

    def _generate(self, epoch_key):
        surf = pygame.Surface((self.w, self.h))
        epoch = EPOCHS.get(epoch_key, EPOCHS["prehistoire"])
        tint  = epoch["bg_tint"]

        if epoch_key == "prehistoire":
            self._draw_prehistoric(surf, tint)
        elif epoch_key == "grece":
            self._draw_greece(surf, tint)
        elif epoch_key == "edo":
            self._draw_edo(surf, tint)
        elif epoch_key == "moderne":
            self._draw_moderne(surf, tint)
        elif epoch_key == "contemporain":
            self._draw_contemporain(surf, tint)
        elif epoch_key == "futuristique":
            self._draw_future(surf, tint)
        else:
            surf.fill(tint)
        return surf

    # -- Dessin --------------------------------------------------------------

    def _draw_prehistoric(self, surf, tint):
        """Sol terreux, grotte, stalactites."""
        # Ciel brun-orange
        for y in range(self.h):
            t = y / self.h
            r = int(tint[0] * (1 - t * 0.4))
            g = int(tint[1] * (1 - t * 0.3))
            b = int(tint[2] * (1 - t * 0.5))
            pygame.draw.line(surf, (max(0,r), max(0,g), max(0,b)), (0, y), (self.w, y))
        # Sol
        pygame.draw.rect(surf, (60, 35, 10), (0, self.h - 120, self.w, 120))
        pygame.draw.rect(surf, (80, 48, 18), (0, self.h - 122, self.w, 6))
        # Rochers
        rng = random.Random(42)
        for _ in range(12):
            rx = rng.randint(0, self.w)
            ry = self.h - 120 + rng.randint(-20, 10)
            rs = rng.randint(25, 70)
            pygame.draw.ellipse(surf, (70, 45, 20), (rx - rs, ry - rs // 2, rs * 2, rs))
        # Stalactites
        for i in range(0, self.w, 90):
            pts = [(i, 0), (i + 40, 0), (i + 20, rng.randint(60, 160))]
            pygame.draw.polygon(surf, (50, 30, 10), pts)
        # Torches (cercles lumineux)
        for tx in [self.w // 5, self.w * 2 // 5, self.w * 3 // 5, self.w * 4 // 5]:
            pygame.draw.circle(surf, (200, 120, 40), (tx, self.h - 180), 30)
            pygame.draw.circle(surf, (255, 180, 80), (tx, self.h - 185), 12)

    def _draw_greece(self, surf, tint):
        """Ciel bleu mediterraneen, colonnes."""
        # Ciel degrade
        for y in range(self.h):
            t = y / self.h
            r = int(120 * (1 - t) + 200 * t)
            g = int(180 * (1 - t) + 160 * t)
            b = int(255 * (1 - t) + 120 * t)
            pygame.draw.line(surf, (min(255,r), min(255,g), min(255,b)), (0, y), (self.w, y))
        # Sol marbre
        pygame.draw.rect(surf, (220, 210, 180), (0, self.h - 140, self.w, 140))
        for x in range(0, self.w, 80):
            pygame.draw.line(surf, (200, 190, 160), (x, self.h - 140), (x, self.h), 1)
        # Colonnes
        for cx in range(60, self.w, 160):
            col_h = random.Random(cx).randint(200, 400)
            pygame.draw.rect(surf, (240, 230, 200), (cx - 18, self.h - 140 - col_h, 36, col_h))
            pygame.draw.rect(surf, (220, 210, 180), (cx - 22, self.h - 140 - col_h, 44, 20))
            pygame.draw.rect(surf, (220, 210, 180), (cx - 22, self.h - 140, 44, 18))
        # Mer en fond
        pygame.draw.rect(surf, (60, 120, 200), (0, 0, self.w, 80))

    def _draw_edo(self, surf, tint):
        """Nuit japonaise, cerisiers, pagode."""
        surf.fill((15, 5, 30))
        # Lune
        pygame.draw.circle(surf, (240, 230, 180), (self.w - 150, 100), 60)
        pygame.draw.circle(surf, (15, 5, 30), (self.w - 130, 90), 55)  # ombre
        # Etoiles
        rng = random.Random(99)
        for _ in range(120):
            sx, sy = rng.randint(0, self.w), rng.randint(0, self.h // 2)
            r = rng.randint(1, 3)
            pygame.draw.circle(surf, (255, 255, 200), (sx, sy), r)
        # Sol herbe sombre
        pygame.draw.rect(surf, (20, 40, 15), (0, self.h - 120, self.w, 120))
        # Cerisiers
        for tx in [self.w // 6, self.w // 2, self.w * 5 // 6]:
            pygame.draw.rect(surf, (60, 40, 20), (tx - 8, self.h - 280, 16, 160))
            for branch in range(5):
                bx = tx + rng.randint(-60, 60)
                by = self.h - 280 + rng.randint(-80, 20)
                pygame.draw.circle(surf, (180, 60, 100), (bx, by), rng.randint(25, 50))
        # Pagode silhouette
        base_x, base_y = self.w // 2 - 50, self.h - 300
        for tier in range(4):
            w = 100 - tier * 18
            h = 30
            y = base_y + tier * 32
            pygame.draw.rect(surf, (40, 20, 10), (base_x + tier * 9, y, w, h))
            pts = [(base_x + tier * 9 - 15, y), (base_x + tier * 9 + w + 15, y),
                   (base_x + tier * 9 + w // 2, y - 20)]
            pygame.draw.polygon(surf, (120, 20, 20), pts)

    def _draw_moderne(self, surf, tint):
        """Champ de bataille napoleonien, fumee."""
        for y in range(self.h):
            t = y / self.h
            r = int(80 * (1 - t) + 120 * t)
            g = int(90 * (1 - t) + 100 * t)
            b = int(130 * (1 - t) + 80 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.w, y))
        pygame.draw.rect(surf, (50, 60, 30), (0, self.h - 130, self.w, 130))
        rng = random.Random(77)
        # Canons
        for cx in [self.w // 5, self.w * 4 // 5]:
            pygame.draw.ellipse(surf, (30, 30, 30), (cx - 10, self.h - 200, 80, 25))
            pygame.draw.rect(surf, (25, 25, 25), (cx - 5, self.h - 215, 30, 20), border_radius=4)
        # Fumee
        for _ in range(20):
            sx = rng.randint(0, self.w)
            sy = rng.randint(0, self.h // 2)
            rad = rng.randint(20, 80)
            pygame.draw.circle(surf, (100, 95, 90), (sx, sy), rad)

    def _draw_contemporain(self, surf, tint):
        """Jungle/foret WW2, bunker."""
        surf.fill((20, 30, 15))
        rng = random.Random(55)
        # Feuillage
        for _ in range(30):
            fx = rng.randint(0, self.w)
            fy = rng.randint(0, self.h * 2 // 3)
            fr = rng.randint(40, 120)
            pygame.draw.circle(surf, (20, rng.randint(60, 120), 20), (fx, fy), fr)
        # Sol
        pygame.draw.rect(surf, (30, 45, 20), (0, self.h - 110, self.w, 110))
        # Barbeles
        for x in range(0, self.w, 60):
            pygame.draw.line(surf, (80, 80, 80), (x, self.h - 130), (x + 50, self.h - 120), 2)
        # Bunker
        pygame.draw.rect(surf, (60, 60, 50),
                         (self.w // 2 - 100, self.h - 240, 200, 110), border_radius=4)
        pygame.draw.rect(surf, (40, 40, 35),
                         (self.w // 2 - 15, self.h - 200, 30, 60))  # entree

    def _draw_future(self, surf, tint):
        """Station spatiale, neons cyan."""
        surf.fill((0, 5, 20))
        rng = random.Random(11)
        # Grille holographique
        grid_col = (0, 40, 80)
        for x in range(0, self.w, 80):
            pygame.draw.line(surf, grid_col, (x, 0), (x, self.h), 1)
        for y in range(0, self.h, 80):
            pygame.draw.line(surf, grid_col, (0, y), (self.w, y), 1)
        # Etoiles
        for _ in range(200):
            sx, sy = rng.randint(0, self.w), rng.randint(0, self.h)
            pygame.draw.circle(surf, (200, 220, 255), (sx, sy), rng.randint(1, 2))
        # Sol metallique
        pygame.draw.rect(surf, (15, 25, 40), (0, self.h - 120, self.w, 120))
        for x in range(0, self.w, 60):
            pygame.draw.line(surf, (0, 80, 120), (x, self.h - 120), (x, self.h), 1)
        # Neons
        for nx in range(0, self.w, 200):
            pygame.draw.rect(surf, (0, 220, 255),
                             (nx, self.h - 125, 80, 4), border_radius=2)
        # Pilliers metal
        for px in range(80, self.w, 250):
            pygame.draw.rect(surf, (20, 40, 60), (px - 10, 0, 20, self.h - 120))
            pygame.draw.line(surf, (0, 200, 255), (px, 0), (px, self.h - 120), 2)


# ==============================================================================
#  HUD RENDERER
# ==============================================================================

class HUDRenderer:
    """Dessine toute l'interface (barres, stats, vague, armes, competences)."""

    def __init__(self, screen_w, screen_h):
        self.w = screen_w
        self.h = screen_h
        self.BAR_W = scale_int(220)
        self.BAR_H_HP = scale_int(22)
        self.BAR_H_STA = scale_int(14)
        self.BAR_X = scale_int(14)
        self.HP_Y = scale_int(14)
        self.STA_Y = scale_int(40)
        self.CORNER_R = scale_int(6)
        self.font_lg  = pygame.font.Font(None, scale_int(36))
        self.font_md  = pygame.font.Font(None, scale_int(26))
        self.font_sm  = pygame.font.Font(None, scale_int(20))
        # Cache de surfaces fixes
        self._bar_bg_hp  = None
        self._bar_bg_sta = None
        self._build_static()

    def _build_static(self):
        # Fond de la barre HP
        self._bar_bg_hp = pygame.Surface((self.BAR_W, self.BAR_H_HP), pygame.SRCALPHA)
        self._bar_bg_hp.fill((0, 0, 0, 160))
        pygame.draw.rect(self._bar_bg_hp, (180, 0, 0), self._bar_bg_hp.get_rect(),
                         border_radius=self.CORNER_R)

    # -- Public --------------------------------------------------------------

    def draw(self, surface, player, epoch_key, wave, wave_complete,
             boss_wave=False, enemies_left=0):
        self._draw_panel_bg(surface)
        self._draw_hp_bar(surface, player)
        self._draw_stamina_bar(surface, player)
        self._draw_weapon_info(surface, player)
        self._draw_stats(surface, player)
        self._draw_skill_indicator(surface, player)
        self._draw_wave_info(surface, epoch_key, wave, wave_complete, boss_wave, enemies_left)
        self._draw_epoch_badge(surface, epoch_key)

    def draw_player_panel(self, surface, player, x, y):
        """Dessine le panneau HUD principal d'un joueur a une position libre."""
        panel = pygame.Surface((self.BAR_W + 80, 190), pygame.SRCALPHA)
        self._draw_panel_bg(panel)
        self._draw_hp_bar(panel, player)
        self._draw_stamina_bar(panel, player)
        self._draw_weapon_info(panel, player)
        self._draw_stats(panel, player)
        self._draw_skill_indicator(panel, player)
        surface.blit(panel, (x, y))

    # -- Prive ----------------------------------------------------------------

    def _draw_panel_bg(self, surface):
        panel = pygame.Surface((self.BAR_W + scale_int(80), scale_int(190)), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 110))
        pygame.draw.rect(panel, (255, 255, 255, 30),
                         panel.get_rect(), 1, border_radius=10)
        surface.blit(panel, (4, 4))

    def _draw_hp_bar(self, surface, player):
        x, y = self.BAR_X, self.HP_Y
        w, h = self.BAR_W, self.BAR_H_HP
        ratio = max(0, player.health / player.max_health)

        # Fond
        pygame.draw.rect(surface, (80, 0, 0), (x, y, w, h), border_radius=self.CORNER_R)
        # Remplissage couleur -> vert si > 60%, orange si > 30%, rouge sinon
        if ratio > 0.6:
            bar_col = (30, 200, 60)
        elif ratio > 0.3:
            bar_col = (230, 150, 20)
        else:
            bar_col = (220, 30, 30)
        fill_w = max(0, int(ratio * w))
        if fill_w > 0:
            pygame.draw.rect(surface, bar_col, (x, y, fill_w, h),
                             border_radius=self.CORNER_R)
        # Bordure
        pygame.draw.rect(surface, WHITE, (x, y, w, h), 2, border_radius=self.CORNER_R)
        # Texte
        txt = self.font_sm.render(f"HP {int(player.health)} / {player.max_health}", True, WHITE)
        surface.blit(txt, (x + 6, y + h // 2 - txt.get_height() // 2))

    def _draw_stamina_bar(self, surface, player):
        x, y = self.BAR_X, self.STA_Y
        w, h = self.BAR_W, self.BAR_H_STA
        ratio = max(0, player.stamina / player.max_stamina)

        pygame.draw.rect(surface, (20, 40, 100), (x, y, w, h), border_radius=self.CORNER_R)
        fill_w = max(0, int(ratio * w))
        if fill_w > 0:
            pygame.draw.rect(surface, (80, 160, 255), (x, y, fill_w, h),
                             border_radius=self.CORNER_R)
        pygame.draw.rect(surface, (150, 190, 255), (x, y, w, h), 1, border_radius=self.CORNER_R)
        txt = self.font_sm.render(f"STA {int(player.stamina)}/{player.max_stamina}", True, (180, 210, 255))
        surface.blit(txt, (x + 4, y + h // 2 - txt.get_height() // 2))

    def _draw_weapon_info(self, surface, player):
        y = scale_int(62)
        wname = player.current_weapon.name if player.current_weapon else "-"
        wtype = player.current_weapon.type if player.current_weapon else ""
        icon  = "RNG" if wtype == "ranged" else "MEL" if wtype == "melee" else "HYB"

        # Cooldown
        cd     = player.current_weapon.cooldown if player.current_weapon else 0
        cd_max = player.current_weapon.cooldown_max if player.current_weapon else 1
        ratio  = 1 - (cd / cd_max if cd_max else 0)

        txt = self.font_sm.render(f"{icon} {wname}", True, GOLD)
        surface.blit(txt, (self.BAR_X, y))

        # Mini barre de cooldown
        pygame.draw.rect(surface, (60, 40, 0), (self.BAR_X, y + scale_int(16), self.BAR_W, scale_int(6)),
                         border_radius=3)
        if ratio > 0:
            col = GOLD if ratio >= 1.0 else ORANGE
            pygame.draw.rect(surface, col,
                             (self.BAR_X, y + scale_int(16), int(ratio * self.BAR_W), scale_int(6)),
                             border_radius=3)

        # Inventaire armes (slots)
        for i, wk in enumerate(player.inventory):
            sx = self.BAR_X + i * scale_int(30)
            sy = y + scale_int(28)
            slot_col = GOLD if wk == (player.current_weapon.key if player.current_weapon else "") else GRAY
            pygame.draw.rect(surface, slot_col, (sx, sy, scale_int(24), scale_int(24)), 2, border_radius=4)
            num = self.font_sm.render(str(i + 1), True, slot_col)
            surface.blit(num, (sx + scale_int(7), sy + scale_int(5)))

    def _draw_stats(self, surface, player):
        y = scale_int(122)
        kills_txt = self.font_sm.render(f"Kills {player.kills}", True, GOLD)
        surface.blit(kills_txt, (self.BAR_X, y))

        # Boosts actifs
        boost_y = y + scale_int(18)
        if player.boost_timer > 0:
            if player.damage_boost > 1.0:
                b = self.font_sm.render("DMG x1.5", True, (255, 120, 60))
                surface.blit(b, (self.BAR_X, boost_y))
            if player.speed_boost > 1.0:
                b = self.font_sm.render("SPD x1.5", True, CYAN)
                surface.blit(b, (self.BAR_X + scale_int(80), boost_y))

        # Bouclier tank
        if getattr(player, "skill", None) == "tank" and player.skill_active:
            b = self.font_sm.render("BOUCLIER", True, BLUE)
            surface.blit(b, (self.BAR_X, boost_y))

    def _draw_skill_indicator(self, surface, player):
        y = scale_int(150)
        if not getattr(player, "skill", None):
            return
        if player.skill_cooldown > 0:
            secs = player.skill_cooldown // 60
            txt = self.font_sm.render(f"F  -  {secs}s", True, (200, 80, 80))
        else:
            txt = self.font_sm.render("F  -  Prete!", True, (80, 255, 80))
        surface.blit(txt, (self.BAR_X, y))

    def _draw_wave_info(self, surface, epoch_key, wave, wave_complete,
                        boss_wave, enemies_left):
        if wave_complete:
            txt = self.font_md.render("Vague terminee - Preparez-vous...", True, GOLD)
        elif boss_wave:
            txt = self.font_md.render(f"VAGUE {wave} - BOSS", True, PURPLE)
        else:
            txt = self.font_md.render(f"Vague {wave}   -   {enemies_left} ennemi(s)", True, WHITE)
        r = txt.get_rect()
        r.topright = (self.w - scale_int(16), scale_int(12))

        bg = pygame.Surface((r.w + scale_int(20), r.h + scale_int(8)), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surface.blit(bg, (r.x - scale_int(10), r.y - scale_int(4)))
        surface.blit(txt, r)

    def _draw_epoch_badge(self, surface, epoch_key):
        epoch = EPOCHS.get(epoch_key, {})
        name  = epoch.get("display", "")
        color = epoch.get("color", WHITE)
        txt = self.font_sm.render(name, True, color)
        r = txt.get_rect()
        r.topright = (self.w - scale_int(16), scale_int(42))

        bg = pygame.Surface((r.w + scale_int(16), r.h + scale_int(6)), pygame.SRCALPHA)
        bg.fill((*color[:3], 40))
        pygame.draw.rect(bg, (*color[:3], 180), bg.get_rect(), 1, border_radius=4)
        surface.blit(bg, (r.x - scale_int(8), r.y - scale_int(3)))
        surface.blit(txt, r)


# ==============================================================================
#  SYSTEME DE PARTICULES
# ==============================================================================

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "r", "color", "life", "max_life", "gravity")

    def __init__(self, x, y, color, vx=0.0, vy=0.0, r=4, life=30, gravity=0.0):
        self.x, self.y   = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.r           = r
        self.color       = color
        self.life        = life
        self.max_life    = life
        self.gravity     = gravity

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += self.gravity
        self.vx *= 0.96
        self.vy *= 0.96
        self.life -= 1

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int(255 * self.life / self.max_life)
        radius = max(1, int(self.r * self.life / self.max_life))
        # Dessin simple (pas de Surface SRCALPHA pour la perf)
        c = (*self.color[:3],)
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), radius)

    @property
    def alive(self):
        return self.life > 0


class ParticleSystem:
    """Gere toutes les particules actives."""

    def __init__(self):
        self._particles: list[Particle] = []

    def update(self):
        self._particles = [p for p in self._particles if p.alive]
        for p in self._particles:
            p.update()

    def draw(self, surface):
        for p in self._particles:
            p.draw(surface)

    # -- Emetteurs predefinis ------------------------------------------------

    def emit_blood(self, x, y, count=8):
        for _ in range(count):
            angle  = random.uniform(0, math.tau)
            speed  = random.uniform(2, 7)
            vx     = math.cos(angle) * speed
            vy     = math.sin(angle) * speed - random.uniform(1, 3)
            life   = random.randint(18, 40)
            r_col  = (random.randint(160, 220), random.randint(0, 30), 0)
            self._particles.append(Particle(x, y, r_col, vx, vy, r=random.randint(2, 5),
                                             life=life, gravity=0.25))

    def emit_hit_spark(self, x, y, color=YELLOW, count=6):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(3, 9)
            vx    = math.cos(angle) * speed
            vy    = math.sin(angle) * speed
            self._particles.append(Particle(x, y, color, vx, vy,
                                             r=random.randint(2, 4), life=random.randint(10, 25)))

    def emit_magic(self, x, y, color=TEAL, count=12):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1, 5)
            vx    = math.cos(angle) * speed
            vy    = math.sin(angle) * speed
            self._particles.append(Particle(x, y, color, vx, vy,
                                             r=random.randint(3, 6), life=random.randint(25, 50)))

    def emit_explosion(self, x, y, count=20):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(4, 12)
            vx    = math.cos(angle) * speed
            vy    = math.sin(angle) * speed - random.uniform(2, 4)
            col   = random.choice([(255, 120, 0), (255, 200, 50), (255, 60, 0)])
            self._particles.append(Particle(x, y, col, vx, vy,
                                             r=random.randint(4, 9),
                                             life=random.randint(20, 50), gravity=0.3))

    def emit_smoke(self, x, y, count=5):
        for _ in range(count):
            vx  = random.uniform(-1, 1)
            vy  = random.uniform(-3, -1)
            col = random.choice([(140, 140, 140), (160, 160, 150), (110, 110, 110)])
            self._particles.append(Particle(x, y, col, vx, vy,
                                             r=random.randint(6, 14), life=random.randint(30, 60)))

    def emit_laser(self, x, y, count=4):
        for _ in range(count):
            vx  = random.uniform(-2, 2)
            vy  = random.uniform(-2, 2)
            col = random.choice([CYAN, (0, 255, 200), (100, 255, 255)])
            self._particles.append(Particle(x, y, col, vx, vy,
                                             r=random.randint(2, 5), life=random.randint(10, 20)))

    def emit_death(self, x, y, color, count=15):
        """Explosion de mort d'ennemi."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(3, 10)
            vx    = math.cos(angle) * speed
            vy    = math.sin(angle) * speed - 2
            self._particles.append(Particle(x, y, color, vx, vy,
                                             r=random.randint(3, 8),
                                             life=random.randint(20, 45), gravity=0.2))


# ==============================================================================
#  EFFETS VISUELS (FLOATING DAMAGE, SCREEN SHAKE)
# ==============================================================================

class FloatingText:
    """Texte de degats qui monte et disparait."""

    def __init__(self, x, y, text, color=WHITE, font_size=26):
        self.x, self.y = float(x), float(y)
        self.text  = text
        self.color = color
        self.font  = pygame.font.Font(None, font_size)
        self.life  = 50
        self.vy    = -1.5

    def update(self):
        self.y    += self.vy
        self.vy   *= 0.97
        self.life -= 1

    def draw(self, surface):
        alpha = int(255 * self.life / 50)
        surf  = self.font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        surface.blit(surf, (int(self.x) - surf.get_width() // 2, int(self.y)))

    @property
    def alive(self):
        return self.life > 0


class FloatingTextSystem:
    def __init__(self):
        self._texts: list[FloatingText] = []

    def add(self, x, y, text, color=WHITE, font_size=26):
        self._texts.append(FloatingText(x, y, text, color, font_size))

    def add_damage(self, x, y, dmg):
        col = (255, 80, 80) if dmg >= 80 else (255, 160, 60) if dmg >= 40 else WHITE
        self._texts.append(FloatingText(x, y - 20, f"-{dmg}", col, 28 + min(dmg // 20, 12)))

    def add_heal(self, x, y, amount):
        self._texts.append(FloatingText(x, y, f"+{amount}", (60, 230, 80), 24))

    def update(self):
        self._texts = [t for t in self._texts if t.alive]
        for t in self._texts:
            t.update()

    def draw(self, surface):
        for t in self._texts:
            t.draw(surface)


class ScreenEffects:
    """Flash rouge a l'impact, screen-shake."""

    def __init__(self, screen_w, screen_h):
        self.w, self.h    = screen_w, screen_h
        self._flash_timer = 0
        self._flash_color = RED
        self._shake_timer = 0
        self._shake_mag   = 0
        self._offset      = (0, 0)

    def flash(self, color=RED, duration=8):
        self._flash_timer = duration
        self._flash_color = color

    def shake(self, magnitude=8, duration=12):
        self._shake_timer = duration
        self._shake_mag   = magnitude

    def update(self):
        if self._flash_timer > 0:
            self._flash_timer -= 1
        if self._shake_timer > 0:
            self._shake_timer -= 1
            x = random.randint(-self._shake_mag, self._shake_mag)
            y = random.randint(-self._shake_mag, self._shake_mag)
            self._offset = (x, y)
        else:
            self._offset = (0, 0)

    def draw_flash(self, surface):
        if self._flash_timer > 0:
            alpha  = int(90 * self._flash_timer / 8)
            flash  = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            flash.fill((*self._flash_color[:3], alpha))
            surface.blit(flash, (0, 0))

    @property
    def offset(self):
        return self._offset


# ==============================================================================
#  RENDU DE L'ARME DANS LA MAIN DU JOUEUR
# ==============================================================================

def draw_weapon_in_hand(surface, player_rect, weapon, facing_right=True, aim_pos=None):
    """
    Dessine le sprite de l'arme rotatif autour du personnage,
    oriente vers la souris.
    """
    if weapon is None:
        return

    cx, cy = player_rect.centerx, player_rect.centery
    if aim_pos is None:
        mx, my = pygame.mouse.get_pos()
    else:
        mx, my = aim_pos

    dx = mx - cx
    dy = my - cy
    angle = math.degrees(math.atan2(-dy, dx))

    # Flip horizontal si le joueur regarde a gauche
    img = weapon.original_image
    if not facing_right:
        img = pygame.transform.flip(img, False, True)

    rotated = pygame.transform.rotate(img, angle)

    offset  = max(30, player_rect.width // 2 + 5)
    wx = cx + math.cos(math.radians(angle)) * offset
    wy = cy - math.sin(math.radians(angle)) * offset

    wr = rotated.get_rect(center=(wx, wy))
    surface.blit(rotated, wr)


# ==============================================================================
#  RENDU DES ENNEMIS PAR EPOQUE (couleur, bordure, effets)
# ==============================================================================

def tint_surface(surface, color, alpha=180):
    """Applique une teinte coloree a une Surface (copie)."""
    result = surface.copy()
    tint   = pygame.Surface(result.get_size(), pygame.SRCALPHA)
    tint.fill((*color[:3], alpha))
    result.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return result


def draw_enemy_health_bar(surface, enemy_rect, health, max_health,
                          epoch_color=RED, is_boss=False, screen_w=1920):
    if is_boss:
        bar_w = scale_int(400)
        bar_h = scale_int(24)
        bx = screen_w // 2 - bar_w // 2
        by = scale_int(54)
        pygame.draw.rect(surface, (60, 0, 0), (bx, by, bar_w, bar_h), border_radius=6)
        fill = max(0, int(health / max_health * bar_w))
        pygame.draw.rect(surface, PURPLE, (bx, by, fill, bar_h), border_radius=6)
        pygame.draw.rect(surface, WHITE, (bx, by, bar_w, bar_h), 2, border_radius=6)
        font = pygame.font.Font(None, scale_int(28))
        txt = font.render("BOSS", True, WHITE)
        surface.blit(txt, (bx + bar_w // 2 - txt.get_width() // 2, by + scale_int(3)))
    else:
        bar_w = max(scale_int(40), enemy_rect.width)
        bar_h = scale_int(5)
        bx = enemy_rect.centerx - bar_w // 2
        by = enemy_rect.top - scale_int(9)
        pygame.draw.rect(surface, (60, 0, 0), (bx, by, bar_w, bar_h), border_radius=3)
        fill = max(0, int(health / max_health * bar_w))
        ratio = health / max_health
        col   = (30, 200, 60) if ratio > 0.5 else (220, 140, 20) if ratio > 0.25 else RED
        if fill > 0:
            pygame.draw.rect(surface, col, (bx, by, fill, bar_h), border_radius=3)
        pygame.draw.rect(surface, (180, 180, 180), (bx, by, bar_w, bar_h), 1, border_radius=3)
