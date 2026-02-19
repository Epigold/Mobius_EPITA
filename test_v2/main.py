# -*- coding: utf-8 -*-
# main.py - Fichier principal - Mobius Roguelike

import pygame
import sys
from core.constants import *

# Import des salles
from epoques.prehistoire import PrehistoireRoom
from epoques.grece import GreceRoom
from epoques.edo import EdoRoom
from epoques.moderne import ModerneRoom
from epoques.contemporain import ContemporainRoom
from epoques.futuristique import FuturistiqueRoom


class Game:
    """Classe principale du jeu"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Mobius Roguelike")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        # États
        self.game_state = MENU
        self.selected_skill = None
        self.current_epoch = "prehistoire"
        
        # Salles
        self.rooms = {
            "prehistoire": PrehistoireRoom(self),
            "grece": GreceRoom(self),
            "edo": EdoRoom(self),
            "moderne": ModerneRoom(self),
            "contemporain": ContemporainRoom(self),
            "futuristique": FuturistiqueRoom(self)
        }
        
        self.current_room = None
        self.player_skill = None
        
        # Background menu
        try:
            self.menu_background = pygame.image.load(get_asset_path("backgrounds", "decor_dj_1.jpg")).convert()
            self.menu_background = pygame.transform.scale(self.menu_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.menu_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.menu_background.fill(BLACK)
    
    def draw_menu(self):
        """Affiche le menu de sélection de compétences"""
        self.screen.blit(self.menu_background, (0, 0))
        
        # Titre
        title = self.font_large.render("MOBIUS ROGUELIKE", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 100)))
        
        subtitle = self.font_medium.render("Choisissez votre classe", True, WHITE)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 160)))
        
        # Cartes de compétences
        skill_keys = list(SKILLS.keys())
        card_width, card_height = 200, 250
        spacing = 30
        total_width = len(skill_keys) * card_width + (len(skill_keys) - 1) * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2
        y = 250
        
        mouse_pos = pygame.mouse.get_pos()
        
        for i, skill_key in enumerate(skill_keys):
            skill = SKILLS[skill_key]
            x = start_x + i * (card_width + spacing)
            card_rect = pygame.Rect(x, y, card_width, card_height)
            
            # Hover effect
            is_hover = card_rect.collidepoint(mouse_pos)
            
            # Fond
            card_surface = pygame.Surface((card_width, card_height))
            card_surface.fill(skill["color"])
            card_surface.set_alpha(150)
            self.screen.blit(card_surface, (x, y))
            
            # Bordure
            pygame.draw.rect(self.screen, GOLD if is_hover else WHITE, card_rect, 4 if is_hover else 2)
            
            # Nom
            name = self.font_medium.render(skill["name"], True, WHITE)
            self.screen.blit(name, name.get_rect(center=(x + card_width // 2, y + 30)))
            
            # Description
            y_offset = 70
            for line in [skill["desc"], "", skill["special"]]:
                if line:
                    text = self.font_small.render(line, True, WHITE)
                    self.screen.blit(text, text.get_rect(center=(x + card_width // 2, y + y_offset)))
                y_offset += 25
            
            # Numéro
            num = self.font_small.render(f"Appuyez sur {i+1}", True, YELLOW)
            self.screen.blit(num, num.get_rect(center=(x + card_width // 2, y + card_height - 30)))
            
            if is_hover:
                self.selected_skill = skill_key
        
        # Instructions
        instructions = self.font_small.render("Cliquez sur une carte ou utilisez les touches 1-5", True, WHITE)
        self.screen.blit(instructions, instructions.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)))
    
    def start_game(self, skill):
        """Démarre le jeu avec la compétence choisie"""
        self.player_skill = skill
        self.current_epoch = "prehistoire"
        self.current_room = self.rooms[self.current_epoch]
        self.current_room.start(skill)
        self.game_state = PLAYING
    
    def change_epoch(self, next_epoch):
        """Change d'époque (salle)"""
        if next_epoch and next_epoch in self.rooms:
            # Sauvegarder stats du joueur
            player_stats = {
                "skill": self.current_room.player.skill,
                "kills": self.current_room.player.kills,
                "coins": self.current_room.player.coins,
                "health": self.current_room.player.health,
                "max_health": self.current_room.player.max_health,
                "stamina": self.current_room.player.stamina,
                "max_stamina": self.current_room.player.max_stamina
            }
            
            # Changer de salle
            self.current_epoch = next_epoch
            self.current_room = self.rooms[next_epoch]
            self.current_room.start(player_stats["skill"], player_stats)
        else:
            # Victoire finale !
            self.game_state = GAME_OVER
    
    def handle_menu_events(self, event):
        """Gère les événements du menu"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            skill_keys = list(SKILLS.keys())
            for i, skill in enumerate(skill_keys):
                if event.key == pygame.K_1 + i:
                    self.start_game(skill)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.selected_skill:
                self.start_game(self.selected_skill)
        return True
    
    def draw_game_over(self):
        """Affiche l'écran de game over"""
        self.screen.blit(self.menu_background, (0, 0))
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Titre
        title = self.font_large.render("GAME OVER", True, RED)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)))
        
        # Stats
        if self.current_room and self.current_room.player:
            y = SCREEN_HEIGHT // 2 - 30
            stats = [
                (f"Époque atteinte: {EPOCHS[self.current_epoch]['name']}", WHITE),
                (f"Ennemis tués: {self.current_room.player.kills}", WHITE),
                (f"Pièces collectées: {self.current_room.player.coins}", GOLD)
            ]
            
            for text, color in stats:
                rendered = self.font_medium.render(text, True, color)
                self.screen.blit(rendered, rendered.get_rect(center=(SCREEN_WIDTH // 2, y)))
                y += 40
        
        # Instructions
        restart = self.font_medium.render("R: Rejouer | M: Menu | ESC: Quitter", True, WHITE)
        self.screen.blit(restart, restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120)))
    
    def run(self):
        """Boucle principale du jeu"""
        running = True
        
        while running:
            self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.game_state == MENU:
                    running = self.handle_menu_events(event)
                
                elif self.game_state == PLAYING:
                    result = self.current_room.handle_event(event)
                    if result == "MENU":
                        self.game_state = MENU
                    elif result == "GAME_OVER":
                        self.game_state = GAME_OVER
                    elif result and result.startswith("NEXT_EPOCH:"):
                        next_epoch = result.split(":")[1]
                        self.change_epoch(next_epoch)
                
                elif self.game_state == GAME_OVER:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self.start_game(self.player_skill)
                        elif event.key == pygame.K_m:
                            self.game_state = MENU
                        elif event.key == pygame.K_ESCAPE:
                            running = False
            
            # Mise à jour
            if self.game_state == PLAYING:
                result = self.current_room.update()
                if result == True:  # Game over
                    self.game_state = GAME_OVER
                elif result and isinstance(result, str) and result.startswith("NEXT_EPOCH:"):
                    next_epoch = result.split(":")[1]
                    self.change_epoch(next_epoch)
            
            # Affichage
            if self.game_state == MENU:
                self.draw_menu()
            elif self.game_state == PLAYING:
                self.current_room.draw(self.screen)
            elif self.game_state == GAME_OVER:
                self.draw_game_over()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()