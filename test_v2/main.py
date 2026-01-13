"""
Mobius - Jeu Roguelike Multi-Epoques
Main.py - Orchestrateur principal du jeu
"""

import pygame
import sys
from epoques.prehistoric import PrehistoricEpoque
from epoques.medieval import MedievalEpoque
from epoques.modern import ModernEpoque
from epoques.futuristic import FuturisticEpoque
from core.player import Player
from core.constants import *

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mobius - Journey Through Time")
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_epoque = None
        self.player = None
        self.epoque_sequence = [
            PrehistoricEpoque,
            MedievalEpoque,
            ModernEpoque,
            FuturisticEpoque
        ]
        self.current_epoque_index = 0
        
    def select_class(self):
        """Menu de sélection de classe"""
        selecting = True
        selected_class = None
        
        font_title = pygame.font.Font(None, 74)
        font_text = pygame.font.Font(None, 36)
        
        classes = {
            '1': 'Tank',
            '2': 'Berserker',
            '3': 'Vampire',
            '4': 'Ninja',
            '5': 'Mage'
        }
        
        while selecting:
            self.screen.fill(BLACK)
            
            # Titre
            title = font_title.render("MOBIUS", True, GOLD)
            self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
            
            subtitle = font_text.render("Choisissez votre classe", True, WHITE)
            self.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 150))
            
            # Affichage des classes
            y = 250
            for key, class_name in classes.items():
                text = font_text.render(f"{key}. {class_name}", True, WHITE)
                self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, y))
                y += 60
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.unicode in classes:
                        selected_class = classes[event.unicode]
                        selecting = False
                        
        return selected_class
    
    def transition_screen(self, epoque_name):
        """Ecran de transition entre epoques"""
        font = pygame.font.Font(None, 74)
        transition_time = 3000
        start_time = pygame.time.get_ticks()
        
        while pygame.time.get_ticks() - start_time < transition_time:
            self.screen.fill(BLACK)
            
            text = font.render(f"Epoque: {epoque_name}", True, GOLD)
            self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))
            
            pygame.display.flip()
            self.clock.tick(FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
    
    def start_new_game(self):
        """Démarre une nouvelle partie"""
        player_class = self.select_class()
        self.player = Player(player_class)
        self.current_epoque_index = 0
        self.load_epoque()
        
    def load_epoque(self):
        """Charge l'epoque courante"""
        if self.current_epoque_index >= len(self.epoque_sequence):
            self.victory_screen()
            return
            
        EpoqueClass = self.epoque_sequence[self.current_epoque_index]
        self.current_epoque = EpoqueClass(self.player)
        self.transition_screen(self.current_epoque.name)
        
    def next_epoque(self):
        """Passe à l'epoque suivante"""
        self.current_epoque_index += 1
        if self.current_epoque_index < len(self.epoque_sequence):
            self.load_epoque()
        else:
            self.victory_screen()
            
    def game_over_screen(self):
        """Écran de fin de partie"""
        font_title = pygame.font.Font(None, 74)
        font_text = pygame.font.Font(None, 36)
        
        waiting = True
        while waiting:
            self.screen.fill(BLACK)
            
            title = font_title.render("GAME OVER", True, RED)
            self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
            
            restart = font_text.render("R - Recommencer", True, WHITE)
            menu = font_text.render("M - Menu", True, WHITE)
            quit_text = font_text.render("ESC - Quitter", True, WHITE)
            
            self.screen.blit(restart, (SCREEN_WIDTH//2 - restart.get_width()//2, 350))
            self.screen.blit(menu, (SCREEN_WIDTH//2 - menu.get_width()//2, 400))
            self.screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, 450))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.start_new_game()
                        waiting = False
                    elif event.key == pygame.K_m:
                        self.main_menu()
                        waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                        
    def victory_screen(self):
        """Écran de victoire"""
        font_title = pygame.font.Font(None, 74)
        font_text = pygame.font.Font(None, 36)
        
        waiting = True
        while waiting:
            self.screen.fill(BLACK)
            
            title = font_title.render("VICTOIRE!", True, GOLD)
            self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
            
            subtitle = font_text.render("Vous avez traverse toutes les epoques!", True, WHITE)
            self.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 300))
            
            menu = font_text.render("M - Menu", True, WHITE)
            quit_text = font_text.render("ESC - Quitter", True, WHITE)
            
            self.screen.blit(menu, (SCREEN_WIDTH//2 - menu.get_width()//2, 400))
            self.screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, 450))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        self.main_menu()
                        waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
    
    def main_menu(self):
        """Menu principal"""
        font_title = pygame.font.Font(None, 74)
        font_text = pygame.font.Font(None, 36)
        
        in_menu = True
        while in_menu:
            self.screen.fill(BLACK)
            
            title = font_title.render("MOBIUS", True, GOLD)
            subtitle = font_text.render("Journey Through Time", True, WHITE)
            
            self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
            self.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 230))
            
            start = font_text.render("Appuyez sur ESPACE pour commencer", True, WHITE)
            quit_text = font_text.render("ESC pour quitter", True, WHITE)
            
            self.screen.blit(start, (SCREEN_WIDTH//2 - start.get_width()//2, 350))
            self.screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, 400))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        in_menu = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                        
        self.start_new_game()
    
    def run(self):
        """Boucle principale du jeu"""
        self.main_menu()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.main_menu()
            
            if self.current_epoque:
                result = self.current_epoque.update()
                
                if result == "next_epoque":
                    self.next_epoque()
                elif result == "game_over":
                    self.game_over_screen()
                    
                self.current_epoque.draw(self.screen)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()