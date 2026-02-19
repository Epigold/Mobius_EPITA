# -*- coding: utf-8 -*-
# base_room.py - Classe de base pour toutes les salles d'époque

import pygame
import random
from .constants import *
from .mechanics import *


class BaseRoom:
    """Classe de base pour toutes les salles d'époque"""
    
    def __init__(self, game, epoch_key):
        self.game = game
        self.epoch_key = epoch_key
        self.epoch_data = EPOCHS[epoch_key]
        
        # Groupes de sprites
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.melee_attacks = pygame.sprite.Group()
        self.chests = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        
        self.player = None
        
        # Variables de vagues
        self.wave = 1
        self.enemies_this_wave = 10
        self.enemies_spawned = 0
        self.wave_complete = False
        self.boss_wave = False
        self.boss_spawned = False
        self.spawn_timer = 0
        self.show_chest_hint = False
        
        # Chargement du fond
        self.background = self._load_background()
        
        # Fonts
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
    
    def _load_background(self):
        """Charge le fond d'écran de l'époque"""
        try:
            bg = pygame.image.load(get_asset_path("backgrounds", self.epoch_data["background"])).convert()
            return pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            bg.fill(self.epoch_data["color_theme"])
            return bg
    
    def start(self, skill, player_stats=None):
        """Démarre la salle"""
        # Réinitialisation des groupes
        for group in [self.all_sprites, self.enemies, self.bullets, self.enemy_bullets, 
                      self.melee_attacks, self.chests, self.powerups]:
            group.empty()
        
        # Création du joueur
        self.player = Player(skill, self.epoch_key)
        
        # Restauration des stats si transition d'époque
        if player_stats:
            for stat in ["kills", "coins", "health", "max_health", "stamina", "max_stamina"]:
                if stat in player_stats:
                    setattr(self.player, stat, player_stats[stat])
        
        self.all_sprites.add(self.player)
        
        # Réinitialisation des variables
        self.wave = 1
        self.enemies_this_wave = 10
        self.enemies_spawned = 0
        self.wave_complete = False
        self.boss_wave = False
        self.boss_spawned = False
        self.spawn_timer = 0
        self.show_chest_hint = False
    
    def spawn_enemy(self):
        """Spawn un ennemi aléatoire"""
        multiplier = self.epoch_data["wave_multiplier"]
        enemy_type = random.choices([Tank, Rusher, Sniper], weights=[20, 40, 40])[0]
        enemy = enemy_type(self.player, multiplier)
        
        if isinstance(enemy, Sniper):
            enemy.set_bullet_group(self.enemy_bullets, self.all_sprites)
        
        self.enemies.add(enemy)
        self.all_sprites.add(enemy)
    
    def spawn_boss(self):
        """Spawn le boss"""
        multiplier = self.epoch_data["wave_multiplier"]
        boss = Boss(self.player, self.wave, multiplier)
        boss.set_bullet_group(self.enemy_bullets, self.all_sprites)
        self.enemies.add(boss)
        self.all_sprites.add(boss)
    
    def spawn_powerup(self, x, y):
        """Spawn un power-up"""
        if random.random() < 0.3:
            powerup_type = random.choice(["damage", "speed", "health", "stamina"])
            powerup = PowerUp(x, y, powerup_type)
            self.powerups.add(powerup)
            self.all_sprites.add(powerup)
    
    def start_new_wave(self):
        """Démarre une nouvelle vague"""
        self.wave += 1
        self.wave_complete = False
        self.boss_spawned = False
        
        # Vérifier si on a terminé toutes les vagues de cette époque
        if self.wave > WAVES_PER_EPOCH:
            return f"NEXT_EPOCH:{self.epoch_data['next_epoch']}"
        
        # Boss tous les 3 vagues
        if self.wave % 3 == 0:
            self.boss_wave = True
            self.enemies_this_wave = 0
        else:
            self.boss_wave = False
            self.enemies_this_wave = int((10 + self.wave * 3) * self.epoch_data["wave_multiplier"])
            self.enemies_spawned = 0
        
        return None
    
    def handle_event(self, event):
        """Gère les événements de la salle"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "MENU"
            
            # Changement d'arme
            elif event.key == pygame.K_1 and len(self.epoch_data["weapons"]) > 0:
                if self.epoch_data["weapons"][0] in self.player.inventory:
                    self.player.change_weapon(self.epoch_data["weapons"][0])
            
            elif event.key == pygame.K_2 and len(self.epoch_data["weapons"]) > 1:
                if self.epoch_data["weapons"][1] in self.player.inventory:
                    self.player.change_weapon(self.epoch_data["weapons"][1])
            
            # Compétence
            elif event.key == pygame.K_f:
                self.player.use_skill(self.bullets, self.all_sprites)
            
            # Interaction coffre
            elif event.key == pygame.K_e:
                for chest in self.chests:
                    if chest.check_interaction(self.player.rect):
                        if chest.open(self.player):
                            self.show_chest_hint = False
        
        # Attaque
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.player.attack(mouse_x, mouse_y, self.bullets, self.melee_attacks, self.all_sprites)
        
        return None
    
    def update(self):
        """Met à jour la salle"""
        self.spawn_timer += 1
        
        # Spawn des ennemis normaux
        if not self.wave_complete and not self.boss_wave:
            if self.spawn_timer >= 60 and self.enemies_spawned < self.enemies_this_wave:
                self.spawn_enemy()
                self.enemies_spawned += 1
                self.spawn_timer = 0
        
        # Spawn du boss
        if self.boss_wave and not self.boss_spawned:
            self.spawn_boss()
            self.boss_spawned = True
        
        # Vérifier fin de vague
        if len(self.enemies) == 0 and not self.wave_complete:
            if self.boss_wave or self.enemies_spawned >= self.enemies_this_wave:
                self.wave_complete = True
                self.player.coins += 5
                
                # Coffre après boss
                if self.boss_wave and len(self.epoch_data["weapons"]) > 1:
                    chest = Chest(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, self.epoch_data["weapons"][1])
                    self.chests.add(chest)
                    self.all_sprites.add(chest)
                    self.player.coins += 10
        
        # Mise à jour
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.bullets, self.melee_attacks, self.all_sprites)
        
        # Mise à jour des autres sprites
        for sprite in self.all_sprites:
            if sprite != self.player:
                sprite.update()
        
        # Collisions projectiles joueur / ennemis
        hits = pygame.sprite.groupcollide(self.bullets, self.enemies, True, False)
        for bullet, hit_enemies in hits.items():
            for enemy in hit_enemies:
                enemy.health -= bullet.damage
                if enemy.health <= 0:
                    self.spawn_powerup(enemy.rect.centerx, enemy.rect.centery)
                    self.player.add_kill()
                    enemy.kill()
        
        # Collisions melee / ennemis
        for melee in self.melee_attacks:
            hits = pygame.sprite.spritecollide(melee, self.enemies, False)
            for enemy in hits:
                if enemy not in melee.hit_enemies:
                    melee.hit_enemies.add(enemy)
                    enemy.health -= melee.damage
                    if enemy.health <= 0:
                        self.spawn_powerup(enemy.rect.centerx, enemy.rect.centery)
                        self.player.add_kill()
                        enemy.kill()
        
        # Collisions projectiles ennemis / joueur
        for bullet in self.enemy_bullets:
            if bullet.rect.colliderect(self.player.hitbox):
                self.player.take_damage(bullet.damage)
                bullet.kill()
        
        # Collisions powerups / joueur
        powerup_hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for powerup in powerup_hits:
            self.player.apply_powerup(powerup.type)
        
        # Vérifier interaction coffre
        self.show_chest_hint = any(chest.check_interaction(self.player.rect) and not chest.opened for chest in self.chests)
        
        # Transition de vague
        if self.wave_complete and self.spawn_timer >= 180:
            result = self.start_new_wave()
            if result:
                return result
            self.spawn_timer = 0
        
        # Game over
        return self.player.health <= 0
    
    def draw(self, surface):
        """Dessine la salle"""
        # Fond
        surface.blit(self.background, (0, 0))
        
        # Sprites
        self.all_sprites.draw(surface)
        self.player.draw_weapon_in_hand(surface)
        
        # Barres de vie des ennemis
        for enemy in self.enemies:
            enemy.draw_health_bar(surface)
        
        # Interface joueur
        self.player.draw_health_bar(surface)
        self.player.draw_stamina_bar(surface)
        self.player.draw_stats(surface, self.epoch_data["name"])
        
        # Indicateurs
        if len(self.player.inventory) > 1:
            hint = self.font_small.render("1/2: Changer d'arme | F: Compétence", True, WHITE)
            surface.blit(hint, (10, 205))
        
        # Affichage de la vague
        if not self.wave_complete:
            wave_color = PURPLE if self.boss_wave else WHITE
            wave_text = f"VAGUE {self.wave} - BOSS" if self.boss_wave else f"Vague {self.wave}/{WAVES_PER_EPOCH} - Ennemis: {len(self.enemies)}"
            text = self.font_medium.render(wave_text, True, wave_color)
            text_rect = text.get_rect(topright=(SCREEN_WIDTH - 20, 10))
            surface.blit(text, text_rect)
        else:
            text = self.font_medium.render("Vague terminée ! Prochaine vague...", True, GREEN)
            surface.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 100)))
        
        # Hint coffre
        if self.show_chest_hint:
            text = self.font_medium.render("Appuyez sur E pour ouvrir", True, YELLOW)
            surface.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)))