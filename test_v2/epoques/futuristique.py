# -*- coding: utf-8 -*-
# futuristique.py - Salle de l'Époque Futuristique

"""
ÉPOQUE: FUTUR
Personnage: Démembreur (soldat cybernétique)
Armes: Laser (distance), Sabre Plasma (mêlée)
Thème: Cyan, technologie avancée
Difficulté: x2.5 (ÉPOQUE FINALE)
"""

from core.base_room import BaseRoom
from core.constants import *
import pygame
import random
import math


class FuturistiqueRoom(BaseRoom):
    """
    Salle de l'Époque Futuristique
    
    ÉPOQUE FINALE : Le futur de la guerre.
    Armes à énergie, ennemis surpuissants, boss final épique.
    """
    
    def __init__(self, game):
        super().__init__(game, "futuristique")
        
        # Personnalisation de l'époque
        self.epoch_name_display = "FUTUR"
        self.theme_color = CYAN
        
        # Messages spécifiques
        self.welcome_message = "Bienvenue dans le futur..."
        self.victory_message = "VICTOIRE TOTALE - VOUS AVEZ TERMINÉ LE JEU !"
        self.final_message = "🎉 FÉLICITATIONS ! MOBIUS ROGUELIKE COMPLÉTÉ ! 🎉"
        
        # Effets futuristes
        self.energy_particles = []
        self.holograms = []
        self.neon_pulse = 0
        self.grid_offset = 0
        
        # Intensité technologique
        self.tech_level = 0
        
        # Générer grille futuriste
        self._generate_grid()
    
    def _generate_grid(self):
        """Génère une grille futuriste de fond"""
        self.grid_lines = []
        spacing = 50
        for x in range(0, SCREEN_WIDTH, spacing):
            self.grid_lines.append(('v', x))  # vertical
        for y in range(0, SCREEN_HEIGHT, spacing):
            self.grid_lines.append(('h', y))  # horizontal
    
    def on_enter(self):
        """Appelé quand le joueur entre dans cette salle"""
        print(f"🚀 {self.welcome_message}")
        print("⚠️  ATTENTION: ÉPOQUE FINALE - DIFFICULTÉ MAXIMALE")
        self._generate_energy_particles()
    
    def _generate_energy_particles(self):
        """Génère des particules d'énergie"""
        for _ in range(50):
            self.energy_particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'size': random.randint(2, 4),
                'color': random.choice([CYAN, BLUE, PURPLE, WHITE])
            })
    
    def on_exit(self):
        """Appelé quand le joueur quitte cette salle (victoire finale)"""
        print(f"🏆 {self.victory_message}")
        print(f"✨ {self.final_message}")
        # Ici vous pourriez déclencher un écran de victoire finale
    
    def add_hologram_effect(self, x, y, text):
        """Ajoute un effet holographique"""
        self.holograms.append({
            'x': x,
            'y': y,
            'text': text,
            'lifetime': 60,
            'alpha': 255,
            'offset_y': 0
        })
    
    def draw_futuristic_grid(self, surface):
        """Dessine une grille futuriste animée"""
        grid_color = (*CYAN[:3], 30)
        
        for line_type, pos in self.grid_lines:
            if line_type == 'v':
                x = (pos + self.grid_offset) % SCREEN_WIDTH
                pygame.draw.line(surface, grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)
            else:
                y = (pos + self.grid_offset) % SCREEN_HEIGHT
                pygame.draw.line(surface, grid_color, (0, y), (SCREEN_WIDTH, y), 1)
    
    def draw_epoch_decoration(self, surface):
        """Dessine des décorations futuristes"""
        # Titre avec effet néon pulsant
        font = pygame.font.Font(None, 36)
        
        # Effet de pulsation
        pulse = int(abs(math.sin(self.neon_pulse) * 50))
        glow_color = (CYAN[0] + pulse, CYAN[1] + pulse, CYAN[2] + pulse)
        
        epoch_text = font.render(self.epoch_name_display, True, glow_color)
        text_rect = epoch_text.get_rect()
        text_rect.topright = (SCREEN_WIDTH - 20, 50)
        
        # Fond holographique
        bg_rect = text_rect.inflate(50, 25)
        
        # Effet de scan
        scan_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        for i in range(0, bg_rect.height, 4):
            alpha = int(100 + 50 * math.sin(self.neon_pulse + i * 0.1))
            pygame.draw.line(scan_surface, (*CYAN[:3], alpha), 
                           (0, i), (bg_rect.width, i), 2)
        surface.blit(scan_surface, bg_rect)
        
        # Bordures néon
        pygame.draw.rect(surface, CYAN, bg_rect, 3)
        pygame.draw.rect(surface, glow_color, bg_rect.inflate(-6, -6), 1)
        
        # Coins lumineux
        corner_size = 10
        corners = [
            bg_rect.topleft,
            (bg_rect.right, bg_rect.top),
            (bg_rect.left, bg_rect.bottom),
            bg_rect.bottomright
        ]
        for corner in corners:
            pygame.draw.circle(surface, glow_color, corner, corner_size // 2)
        
        surface.blit(epoch_text, text_rect)
        
        # Indicateur de niveau technologique
        tech_bar_width = 100
        tech_bar_x = text_rect.left - tech_bar_width - 20
        tech_bar_y = text_rect.centery - 5
        
        # Fond de barre
        pygame.draw.rect(surface, DARK_BLUE, (tech_bar_x, tech_bar_y, tech_bar_width, 10))
        
        # Barre de niveau
        tech_fill = int((self.tech_level / 100) * tech_bar_width)
        pygame.draw.rect(surface, CYAN, (tech_bar_x, tech_bar_y, tech_fill, 10))
        
        # Bordure
        pygame.draw.rect(surface, CYAN, (tech_bar_x, tech_bar_y, tech_bar_width, 10), 2)
    
    def update(self):
        """Mise à jour avec effets futuristes"""
        result = super().update()
        
        # Animation de pulsation néon
        self.neon_pulse = (self.neon_pulse + 0.1) % (2 * math.pi)
        
        # Animation de grille
        self.grid_offset = (self.grid_offset + 0.5) % 50
        
        # Mise à jour des particules d'énergie
        for particle in self.energy_particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            # Rebond sur les bords
            if particle['x'] < 0 or particle['x'] > SCREEN_WIDTH:
                particle['vx'] *= -1
            if particle['y'] < 0 or particle['y'] > SCREEN_HEIGHT:
                particle['vy'] *= -1
        
        # Mise à jour des hologrammes
        for holo in self.holograms[:]:
            holo['lifetime'] -= 1
            holo['offset_y'] -= 0.5
            holo['alpha'] = int((holo['lifetime'] / 60) * 255)
            
            if holo['lifetime'] <= 0:
                self.holograms.remove(holo)
        
        # Niveau technologique basé sur l'activité
        self.tech_level = min(len(self.enemies) * 2 + len(self.bullets) + len(self.enemy_bullets), 100)
        
        return result
    
    def draw(self, surface):
        """Surcharge pour ajouter des éléments visuels futuristes"""
        # Grille de fond futuriste
        self.draw_futuristic_grid(surface)
        
        super().draw(surface)
        
        # Dessiner les particules d'énergie
        for particle in self.energy_particles:
            # Effet de glow
            glow_surface = pygame.Surface((particle['size'] * 4, particle['size'] * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*particle['color'][:3], 100), 
                             (particle['size'] * 2, particle['size'] * 2), 
                             particle['size'] * 2)
            surface.blit(glow_surface, 
                        (particle['x'] - particle['size'] * 2, 
                         particle['y'] - particle['size'] * 2))
            
            # Particule centrale
            pygame.draw.circle(surface, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 
                             particle['size'])
        
        # Dessiner les hologrammes
        for holo in self.holograms:
            font = pygame.font.Font(None, 24)
            holo_text = font.render(holo['text'], True, (*CYAN[:3], holo['alpha']))
            text_rect = holo_text.get_rect(center=(holo['x'], holo['y'] + holo['offset_y']))
            surface.blit(holo_text, text_rect)
        
        self.draw_epoch_decoration(surface)
        
        # Message de bienvenue futuriste
        if self.wave == 1 and not self.wave_complete and len(self.enemies) > 0:
            font = pygame.font.Font(None, 42)
            
            # Effet de scan
            welcome = font.render(self.welcome_message, True, CYAN)
            welcome_rect = welcome.get_rect(center=(SCREEN_WIDTH // 2, 150))
            
            # Fond holographique
            bg_rect = welcome_rect.inflate(80, 40)
            
            # Scanlines
            scan_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            for i in range(0, bg_rect.height, 3):
                alpha = int(150 + 50 * math.sin(self.neon_pulse + i * 0.2))
                pygame.draw.line(scan_surf, (*CYAN[:3], alpha), (0, i), (bg_rect.width, i), 1)
            surface.blit(scan_surf, bg_rect)
            
            # Bordures néon
            pygame.draw.rect(surface, CYAN, bg_rect, 4)
            pygame.draw.rect(surface, WHITE, bg_rect.inflate(-8, -8), 1)
            
            surface.blit(welcome, welcome_rect)
            
            # Message d'avertissement
            warning_font = pygame.font.Font(None, 20)
            warning = warning_font.render("⚠️ NIVEAU DE DIFFICULTÉ MAXIMAL ⚠️", True, RED)
            warning_rect = warning.get_rect(center=(SCREEN_WIDTH // 2, 190))
            surface.blit(warning, warning_rect)
        
        # Message de victoire finale
        if self.wave > WAVES_PER_EPOCH:
            victory_font = pygame.font.Font(None, 60)
            victory_text = victory_font.render(self.final_message, True, GOLD)
            victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            # Fond de victoire
            bg_rect = victory_rect.inflate(100, 50)
            pygame.draw.rect(surface, BLACK, bg_rect)
            pygame.draw.rect(surface, GOLD, bg_rect, 5)
            
            surface.blit(victory_text, victory_rect)
    
    def spawn_enemy(self):
        """Surcharge pour ajouter des effets de téléportation"""
        # Effet de téléportation avant le spawn
        if len(self.enemies) < self.enemies_this_wave:
            super().spawn_enemy()
            
            # Ajouter hologramme au spawn
            if len(self.enemies) > 0:
                last_enemy = list(self.enemies)[-1]
                self.add_hologram_effect(last_enemy.rect.centerx, last_enemy.rect.centery, "INCOMING")
                
                # Particules de téléportation
                for _ in range(10):
                    self.energy_particles.append({
                        'x': last_enemy.rect.centerx + random.randint(-20, 20),
                        'y': last_enemy.rect.centery + random.randint(-20, 20),
                        'vx': random.uniform(-2, 2),
                        'vy': random.uniform(-2, 2),
                        'size': 3,
                        'color': CYAN
                    })
    
    def get_epoch_tips(self):
        """Conseils spécifiques à l'époque"""
        return [
            "⚡ Le Laser est l'arme ultime à distance",
            "🔥 Le Sabre Plasma détruit tout",
            "🛡️ Utilisez TOUTES vos capacités",
            "🎯 C'est le combat final - donnez tout !"
        ]