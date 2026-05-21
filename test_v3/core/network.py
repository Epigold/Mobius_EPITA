# -*- coding: utf-8 -*-
# core/network.py - Module réseau pour le multijoueur en ligne (UDP)

"""
ARCHITECTURE RÉSEAU
═══════════════════════════════════════════════════════════════════════════════
Le jeu utilise un modèle CLIENT-SERVEUR où :

  HOST (P1)  = serveur + joueur local
    → Fait tourner TOUTE la simulation du jeu (physique, ennemis, collisions)
    → Reçoit les inputs de P2 via UDP
    → Envoie l'état complet du jeu à P2 chaque frame
    → P1 joue normalement en local (clavier/souris)

  CLIENT (P2) = client + joueur distant
    → N'exécute AUCUNE simulation
    → Capture ses inputs locaux (clavier/souris) et les envoie au serveur
    → Reçoit l'état du jeu et l'affiche (rendu pur, pas de logique)
    → Latence = aller-retour réseau (idéalement < 50ms en LAN / < 100ms en WAN)

PROTOCOLE
─────────────────────────────────────────────────────────────────────────────
Transport : UDP (User Datagram Protocol)
  → Choix préféré pour les jeux temps réel : latence minimale, pas de retransmission
  → Inconvénient : paquets peuvent être perdus → on ignore les paquets manqués
    (le prochain arrivera, et un état légèrement ancien est préférable à un freeze)

Format    : JSON encodé en UTF-8
  → Simple à déboguer (readable), suffisant pour 60 fps en LAN
  → Pour optimiser: remplacer par msgpack ou struct binaire

Taille max paquet : 65535 bytes (limite UDP théorique)
  → L'état du jeu sérialisé dépasse rarement 4096 bytes

TYPES DE MESSAGES
─────────────────────────────────────────────────────────────────────────────
Client → Serveur :
  {"type": "hello"}                           # Demande de connexion initiale
  {"type": "input", "data": {...}}            # Inputs du joueur 2 chaque frame
  {"type": "bye"}                             # Déconnexion propre

Serveur → Client :
  {"type": "welcome", "skill": "...", "epoch": "..."}  # Confirmation de connexion
  {"type": "state",   "data": {...}}          # État complet du jeu chaque frame
  {"type": "start",   "skill2": "..."}        # Signal que la partie commence

PORT PAR DÉFAUT : 55_555
  → Choisir un port > 1024 (pas besoin de droits admin)
  → Ouvrir ce port dans le pare-feu Windows/macOS si nécessaire
  → Sur routeur : rediriger UDP 55555 vers l'IP locale du host pour jouer sur internet

SCHÉMA DE L'ÉTAT SÉRIALISÉ (envoyé par le serveur chaque frame)
─────────────────────────────────────────────────────────────────────────────
{
  "epoch"        : str,           # Époque courante ("prehistoire", "grece", ...)
  "wave"         : int,           # Numéro de vague
  "wave_complete": bool,
  "boss_wave"    : bool,
  "show_chest_hint": bool,
  "game_over"    : bool,          # True si la partie est terminée
  "next_epoch"   : str | null,    # Renseigné si transition d'époque en cours
  "p1": {
    "x", "y"         : int,       # Position centre du sprite
    "health"         : float,
    "max_health"     : int,
    "stamina"        : float,
    "max_stamina"    : int,
    "kills"          : int,
    "coins"          : int,
    "facing_right"   : bool,
    "anim_state"     : str,       # "idle" / "run"
    "skill"          : str,
    "weapon"         : str,
    "inventory"      : list[str],
  },
  "p2": { ... même structure ... } | null,
  "enemies": [
    {"id": int, "x": int, "y": int, "health": int, "max_health": int,
     "type": str, "size": int, "epoch": str}
  ],
  "bullets"      : [{"x": int, "y": int}],
  "enemy_bullets": [{"x": int, "y": int}],
  "powerups"     : [{"x": int, "y": int, "type": str}],
  "chests"       : [{"x": int, "y": int, "opened": bool}],
}

SCHÉMA DES INPUTS (envoyés par le client chaque frame)
─────────────────────────────────────────────────────────────────────────────
{
  "dx": float,         # Direction X normalisée (-1.0 à 1.0)
  "dy": float,         # Direction Y normalisée (-1.0 à 1.0)
  "dash": bool,        # true si touche dash pressée ce frame
  "skill": bool,       # true si touche skill pressée ce frame
  "fire": bool,        # true si clic gauche pressé ce frame
  "fire_tx": int,      # Coordonnée X cible du tir (position souris)
  "fire_ty": int,      # Coordonnée Y cible du tir
  "chest": bool,       # true si touche coffre pressée ce frame
  "weapon_idx": int,   # Index arme à équiper, -1 si pas de changement
}
"""

import socket
import json
import threading
import time
import math
import pygame
from .constants import EPOCHS, SKILLS, GOLD, RED, WHITE, SCREEN_WIDTH, SCREEN_HEIGHT

# ── Constantes réseau ─────────────────────────────────────────────────────────
DEFAULT_PORT    = 55_600   # Port UDP par défaut (à ouvrir dans le pare-feu)
RECV_BUFFER     = 65_535   # Taille du buffer de réception UDP (max théorique)
SEND_BUFFER     = 65_535   # Taille du buffer d'envoi
CONNECT_TIMEOUT = 10.0     # Secondes avant d'abandonner la tentative de connexion
PING_INTERVAL   = 1.0      # Secondes entre deux pings de maintien de connexion


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════

def get_local_ip() -> str:
    """
    Compatible Windows natif, WSL et Linux.
    """
    import subprocess
    import re

    # Méthode 1 : ip route (Linux/WSL) — cherche l'interface utilisée pour sortir
    try:
        output = subprocess.check_output(
            ["ip", "route", "get", "8.8.8.8"],
            encoding="utf-8", errors="ignore"
        )
        match = re.search(r'src\s+([\d.]+)', output)
        if match:
            ip = match.group(1)
            if not ip.startswith('172.24.') and not ip.startswith('127.'):
                return ip
    except Exception:
        pass

    # Méthode 2 : hostname -I (Linux) — liste toutes les IPs, prend la première LAN
    try:
        output = subprocess.check_output(
            ["hostname", "-I"],
            encoding="utf-8", errors="ignore"
        ).strip()
        for ip in output.split():
            if ip.startswith('192.168.') or ip.startswith('10.'):
                return ip
            parts = ip.split('.')
            if parts[0] == '172' and 16 <= int(parts[1]) <= 31 \
                    and not ip.startswith('172.24.'):
                return ip
    except Exception:
        pass

    # Méthode 3 : ipconfig (Windows natif)
    try:
        output = subprocess.check_output(
            ["ipconfig"], encoding="cp850", errors="ignore"
        )
        ips = re.findall(r'Adresse IPv4.*?:\s*([\d.]+)', output)
        if not ips:
            ips = re.findall(r'IPv4 Address.*?:\s*([\d.]+)', output)
        for ip in ips:
            if ip.startswith('192.168.') or ip.startswith('10.'):
                return ip
    except Exception:
        pass

    # Méthode 4 : fallback socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        pass

    return '127.0.0.1'


def encode(msg: dict) -> bytes:
    """Sérialise un dict Python en JSON UTF-8."""
    return json.dumps(msg, separators=(',', ':')).encode('utf-8')


def decode(data: bytes) -> dict | None:
    """
    Désérialise des bytes JSON en dict.
    Retourne None si le paquet est corrompu (plutôt que de crasher).
    """
    try:
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  SERVEUR (HOST / P1)
# ══════════════════════════════════════════════════════════════════════════════

class GameServer:
    """
    Serveur UDP hébergeant la partie multijoueur.

    Le host crée une instance de GameServer, attend qu'un client se connecte,
    puis chaque frame :
      1. Appelle poll()            → traite les paquets entrants
      2. Lit get_client_inputs()   → récupère les derniers inputs P2
      3. Appelle send_state(state) → envoie l'état du jeu au client

    THREAD-SAFETY :
      Les données partagées (client_inputs) sont protégées par un Lock.
      poll() est appelé depuis le thread principal (game loop), pas depuis un thread séparé.
      → On utilise setblocking(False) pour un polling non-bloquant.

    UTILISATION :
      server = GameServer()
      local_ip = server.local_ip   # À afficher au host pour que P2 puisse se connecter
      # Dans la boucle de jeu :
      server.poll()
      inputs = server.get_client_inputs()
      server.send_state(game_state_dict)
    """

    def __init__(self, port: int = DEFAULT_PORT):
        # ── Création du socket UDP ─────────────────────────────────────────────
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Réutiliser le port après crash
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SEND_BUFFER)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RECV_BUFFER)
        self.sock.bind(('', port))       # Écoute sur toutes les interfaces réseau
        self.sock.setblocking(False)     # Non-bloquant : recvfrom() lève BlockingIOError si vide

        self.port      = port
        self.local_ip  = get_local_ip()  # IP à communiquer au client

        # ── État connexion ─────────────────────────────────────────────────────
        self.client_addr  = None   # Tuple (ip, port) du client connecté
        self.connected    = False  # True après réception du premier "hello"
        self.p2_skill     = None   # Classe choisie par P2 (envoyée dans "hello")

        # ── Inputs P2 (dernière frame reçue) ──────────────────────────────────
        # Dict contenant les touches pressées par P2 au dernier poll()
        self._client_inputs = {}
        self._lock          = threading.Lock()  # Protège _client_inputs

        # ── Statistiques réseau (optionnel) ───────────────────────────────────
        self.packets_sent     = 0
        self.packets_received = 0
        self.last_recv_time   = time.time()  # Pour détecter une déconnexion

        print(f"[SERVER] En écoute sur {self.local_ip}:{port}")
        print(f"[SERVER] Communiquez cette IP à P2 : {self.local_ip}")

    # ── Polling (non-bloquant, à appeler chaque frame) ────────────────────────

    def poll(self):
        """
        Lit tous les paquets UDP reçus depuis le dernier poll().
        Traite jusqu'à 10 paquets par frame pour éviter de bloquer la game loop.
        Doit être appelé UNE FOIS PAR FRAME dans la boucle principale.
        """
        for _ in range(10):  # Limite : traiter max 10 paquets par frame
            try:
                data, addr = self.sock.recvfrom(RECV_BUFFER)
            except BlockingIOError:
                break   # File vide, on arrête
            except OSError:
                break

            msg = decode(data)
            if msg is None:
                continue  # Paquet corrompu, ignorer

            msg_type = msg.get('type', '')

            # ── Demande de connexion initiale ──────────────────────────────────
            if msg_type == 'hello':
                self.client_addr = addr
                self.connected   = True
                self.p2_skill    = msg.get('skill', 'tank')  # Classe choisie par P2
                self.last_recv_time = time.time()

                # Répondre avec "welcome" pour confirmer la connexion
                self._send({'type': 'welcome',
                            'msg':  'Connexion établie !'}, addr)
                print(f"[SERVER] Client connecté depuis {addr[0]}:{addr[1]}")
                print(f"[SERVER] P2 joue la classe : {self.p2_skill}")

            # ── Inputs du client (chaque frame) ───────────────────────────────
            elif msg_type == 'input' and addr == self.client_addr:
                with self._lock:
                    # On garde seulement les derniers inputs (le précédent est obsolète)
                    self._client_inputs = msg.get('data', {})
                self.last_recv_time = time.time()
                self.packets_received += 1

            # ── Déconnexion propre ─────────────────────────────────────────────
            elif msg_type == 'bye' and addr == self.client_addr:
                print(f"[SERVER] Client déconnecté proprement")
                self.connected   = False
                self.client_addr = None

    def get_client_inputs(self) -> dict:
        """
        Retourne les derniers inputs reçus du client P2.
        Thread-safe grâce au Lock.

        Structure retournée :
          {"dx": float, "dy": float, "dash": bool, "skill": bool,
           "fire": bool, "fire_tx": int, "fire_ty": int,
           "chest": bool, "weapon_idx": int}
        """
        with self._lock:
            return dict(self._client_inputs)  # Copie pour éviter les modifications concurrentes

    def send_state(self, state: dict):
        """
        Envoie l'état complet du jeu au client.
        Si le client est déconnecté, ne fait rien (pas d'erreur).

        state : dict retourné par BaseRoom.serialize_state()
        """
        if self.client_addr is None:
            return
        self._send({'type': 'state', 'data': state}, self.client_addr)
        self.packets_sent += 1

    def send_start(self, p1_skill: str):
        """
        Envoie le signal de début de partie au client.
        Inclut la classe de P1 pour que le client puisse afficher les infos correctes.
        """
        if self.client_addr:
            self._send({'type': 'start', 'p1_skill': p1_skill}, self.client_addr)

    def is_client_timeout(self, timeout: float = 5.0) -> bool:
        """
        Retourne True si le client n'a pas envoyé de paquet depuis `timeout` secondes.
        Permet de détecter une déconnexion inattendue (crash, coupure réseau).
        """
        return self.connected and (time.time() - self.last_recv_time > timeout)

    def _send(self, msg: dict, addr: tuple):
        """Envoie un message JSON au destinataire. Ignore les erreurs réseau."""
        try:
            self.sock.sendto(encode(msg), addr)
        except OSError:
            pass

    def close(self):
        """Ferme le socket proprement."""
        try:
            if self.client_addr:
                self._send({'type': 'bye'}, self.client_addr)
            self.sock.close()
        except OSError:
            pass
        print("[SERVER] Socket fermé")


# ══════════════════════════════════════════════════════════════════════════════
#  CLIENT (GUEST / P2)
# ══════════════════════════════════════════════════════════════════════════════

class GameClient:
    """
    Client UDP se connectant au serveur host.

    P2 crée une instance de GameClient, se connecte au serveur,
    puis chaque frame :
      1. Appelle poll()            → traite les paquets entrants (état du jeu)
      2. Appelle send_inputs(...)  → envoie ses inputs locaux au serveur
      3. Lit get_state()           → récupère le dernier état pour le rendu

    UTILISATION :
      client = GameClient('192.168.1.42')   # IP du host
      client.connect('mage')                # Envoyer hello + sa classe
      # Dans la boucle de jeu :
      client.poll()
      client.send_inputs(inputs_dict)
      state = client.get_state()
      # → rendre state
    """

    def __init__(self, host: str, port: int = DEFAULT_PORT):
        # ── Création du socket UDP ─────────────────────────────────────────────
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SEND_BUFFER)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RECV_BUFFER)
        self.sock.setblocking(False)   # Non-bloquant pour ne pas freezer le jeu

        self.server_addr = (host, port)
        self.connected   = False       # True après réception de "welcome"
        self.p1_skill    = None        # Classe de P1 (reçue dans "start")
        self.started     = False       # True après réception de "start"

        # ── Dernier état reçu ─────────────────────────────────────────────────
        # Dict sérialisé reçu du serveur, utilisé pour le rendu
        self._latest_state = {}
        self._state_lock   = threading.Lock()

        self.packets_received = 0
        self.last_recv_time   = time.time()

        print(f"[CLIENT] Socket créé, serveur cible : {host}:{port}")

    # ── Connexion ─────────────────────────────────────────────────────────────

    def connect(self, skill: str):
        """
        Envoie un message "hello" au serveur pour initier la connexion.
        Inclut la classe choisie par P2 pour que le serveur crée le bon personnage.

        skill : str → clé de classe ("tank", "mage", ...)
        Le serveur répondra par "welcome" qui sera capturé dans poll().
        """
        self._send({'type': 'hello', 'skill': skill})
        print(f"[CLIENT] Envoi hello au serveur (classe={skill})...")

    # ── Polling (non-bloquant, à appeler chaque frame) ────────────────────────

    def poll(self):
        """
        Lit tous les paquets UDP disponibles depuis le dernier poll().
        À appeler UNE FOIS PAR FRAME dans la boucle de rendu.
        """
        for _ in range(10):
            try:
                data, _ = self.sock.recvfrom(RECV_BUFFER)
            except BlockingIOError:
                break
            except OSError:
                break

            msg = decode(data)
            if msg is None:
                continue

            msg_type = msg.get('type', '')

            # ── Confirmation de connexion ──────────────────────────────────────
            if msg_type == 'welcome':
                self.connected = True
                print(f"[CLIENT] Connecté au serveur !")

            # ── Signal de début de partie ──────────────────────────────────────
            elif msg_type == 'start':
                self.p1_skill = msg.get('p1_skill')
                self.started  = True
                print(f"[CLIENT] Partie démarrée ! P1 joue : {self.p1_skill}")

            # ── État du jeu (chaque frame du serveur) ──────────────────────────
            elif msg_type == 'state':
                with self._state_lock:
                    self._latest_state = msg.get('data', {})
                self.last_recv_time = time.time()
                self.packets_received += 1

            # ── Déconnexion serveur ────────────────────────────────────────────
            elif msg_type == 'bye':
                self.connected = False
                print("[CLIENT] Le serveur s'est déconnecté")

    def send_inputs(self, inputs: dict):
        """
        Envoie les inputs locaux de P2 au serveur.
        Appelé chaque frame, même si rien n'a changé (le serveur a toujours besoin
        d'un état récent pour savoir que P2 est vivant).

        inputs : dict avec les clés définies dans le module (dx, dy, fire, ...)
        """
        self._send({'type': 'input', 'data': inputs})

    def get_state(self) -> dict:
        """
        Retourne le dernier état de jeu reçu du serveur.
        Thread-safe. Retourne {} si aucun état reçu encore.
        """
        with self._state_lock:
            return dict(self._latest_state)

    def is_server_timeout(self, timeout: float = 5.0) -> bool:
        """Retourne True si le serveur n'a pas répondu depuis `timeout` secondes."""
        return self.connected and (time.time() - self.last_recv_time > timeout)

    def _send(self, msg: dict):
        """Envoie un message JSON au serveur. Ignore les erreurs réseau."""
        try:
            self.sock.sendto(encode(msg), self.server_addr)
        except OSError:
            pass

    def close(self):
        """Ferme le socket proprement."""
        try:
            self._send({'type': 'bye'})
            self.sock.close()
        except OSError:
            pass
        print("[CLIENT] Socket fermé")


# ══════════════════════════════════════════════════════════════════════════════
#  RENDU CÔTÉ CLIENT  (dessine l'état reçu du serveur)
# ══════════════════════════════════════════════════════════════════════════════

class ClientRenderer:
    """
    Moteur de rendu pour le client (P2).

    Le client ne fait PAS tourner la simulation du jeu. Il reçoit un dict
    d'état du serveur et le dessine chaque frame. Ce renderer reconstruit
    visuellement l'état sans avoir besoin des groupes de sprites.

    LIMITES :
      - Les animations de particules ne sont pas synchronisées (non-critique)
      - Les effets de flash/shake ne sont pas reproduits côté client
      - Les animations de sprites sont simplifiées (une seule frame idle/run)

    Pour améliorer : envoyer aussi les particules actives dans le state dict.
    """

    def __init__(self, screen_w: int, screen_h: int):
        from .graphics import BackgroundRenderer, HUDRenderer, SpriteCache
        self.w = screen_w
        self.h = screen_h
        self.bg_renderer = BackgroundRenderer(screen_w, screen_h)
        self.hud         = HUDRenderer(screen_w, screen_h)
        self._cache      = SpriteCache.get()

        # Pré-charger les sprites joueurs pour le rendu
        self._player_sprites = {}
        for state in ("idle", "run"):
            name = "char_idle_one_arm" if state == "idle" else "char_run1_one_arm"
            try:
                self._player_sprites[state] = self._cache.load(
                    "sprites_final", f"{name}.png", size=(80, 80))
            except Exception:
                # Fallback : cercle coloré si l'image est introuvable
                surf = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(surf, (200, 200, 255), (40, 40), 35)
                self._player_sprites[state] = surf

        # Cache des surfaces d'ennemis procéduraux (id ennemi → surface)
        # Évite de régénérer le sprite à chaque frame
        self._enemy_surf_cache: dict[int, pygame.Surface] = {}

        # Police pour les textes HUD client
        self._font_md = pygame.font.Font(None, 30)
        self._font_sm = pygame.font.Font(None, 22)

    def draw(self, surface: pygame.Surface, state: dict):
        """
        Dessine l'état complet du jeu à partir du dict reçu du serveur.

        Ordre de rendu :
          1. Fond (background de l'époque)
          2. Power-ups
          3. Coffres
          4. Projectiles joueurs (petits cercles)
          5. Balles ennemies (petits cercles colorés)
          6. Ennemis (sprites procéduraux + barres de vie)
          7. Joueur 1 (P1, sprite violet)
          8. Joueur 2 (P2 = nous, sprite bleu)
          9. HUD P2 (nos propres stats en premier)
          10. HUD P1 (stats de P1)
          11. Infos de vague
          12. Hint coffre
        """
        epoch = state.get('epoch', 'prehistoire')

        # ── 1. Fond ───────────────────────────────────────────────────────────
        bg = self.bg_renderer.get(epoch)
        surface.blit(bg, (0, 0))

        # ── 2. Power-ups ──────────────────────────────────────────────────────
        POWERUP_COLORS = {
            "damage":  (220, 60,  60),
            "speed":   (60,  200, 220),
            "health":  (60,  200, 80),
            "stamina": (80,  120, 255),
        }
        POWERUP_LABELS = {"damage": "DMG", "speed": "SPD", "health": "HP", "stamina": "STA"}
        font_pu = pygame.font.Font(None, 18)
        for pu in state.get('powerups', []):
            col = POWERUP_COLORS.get(pu['type'], (180, 180, 180))
            pygame.draw.circle(surface, col, (pu['x'], pu['y']), 17)
            pygame.draw.circle(surface, (255,255,255), (pu['x'], pu['y']), 17, 2)
            lbl = font_pu.render(POWERUP_LABELS.get(pu['type'], '?'), True, (255,255,255))
            surface.blit(lbl, (pu['x'] - lbl.get_width()//2, pu['y'] - lbl.get_height()//2))

        # ── 3. Coffres ────────────────────────────────────────────────────────
        for chest in state.get('chests', []):
            cx, cy = chest['x'], chest['y']
            col = (80, 140, 80) if chest['opened'] else (180, 120, 30)
            pygame.draw.rect(surface, col, (cx-32, cy-26, 64, 52), border_radius=5)
            pygame.draw.rect(surface, (255, 215, 0), (cx-32, cy-26, 64, 52), 2, border_radius=5)
            if not chest['opened']:
                # Serrure
                pygame.draw.rect(surface, (255, 215, 0), (cx-6, cy-8, 12, 10), border_radius=2)

        # ── 4. Projectiles joueurs (petits cercles blancs) ────────────────────
        for b in state.get('bullets', []):
            pygame.draw.circle(surface, (255, 255, 200), (b['x'], b['y']), 6)
            pygame.draw.circle(surface, (255, 220, 0),   (b['x'], b['y']), 6, 1)

        # ── 5. Balles ennemies (petits cercles rouges) ────────────────────────
        enemy_col = EPOCHS.get(epoch, {}).get('enemy_tint', (200, 0, 0))
        for b in state.get('enemy_bullets', []):
            pygame.draw.circle(surface, enemy_col, (b['x'], b['y']), 7)
            pygame.draw.circle(surface, (255,255,255), (b['x'], b['y']), 7, 1)

        # ── 6. Ennemis ────────────────────────────────────────────────────────
        for edata in state.get('enemies', []):
            self._draw_enemy(surface, edata, epoch)

        # ── 7. Joueur 1 (P1 = l'autre joueur, teinté pour le distinguer) ─────
        p1 = state.get('p1')
        if p1 and p1['health'] > 0:
            self._draw_player(surface, p1, tint=(180, 100, 255, 50))

        # ── 8. Joueur 2 (P2 = nous, rendu normal) ────────────────────────────
        p2 = state.get('p2')
        if p2 and p2['health'] > 0:
            self._draw_player(surface, p2, tint=None)
            # Indicateur "VOUS" au-dessus de P2
            you_txt = self._font_sm.render("▼ VOUS", True, (120, 200, 255))
            surface.blit(you_txt, (p2['x'] - you_txt.get_width()//2, p2['y'] - 58))

        # ── 9. HUD P2 (notre barre de vie, en bas à gauche, en premier) ───────
        if p2:
            self._draw_client_hud(surface, p2, epoch,
                                   state.get('wave', 1),
                                   state.get('wave_complete', False),
                                   state.get('boss_wave', False),
                                   state.get('enemies_left', 0))

        # ── 10. HUD P1 (stats de P1 en bas à droite) ─────────────────────────
        if p1:
            self._draw_p1_hud_small(surface, p1)

        # ── 11. Hint coffre ───────────────────────────────────────────────────
        if state.get('show_chest_hint'):
            font = pygame.font.Font(None, 32)
            hint = font.render(state.get('objective_hint', "E : Ouvrir le coffre"), True, GOLD)
            hr = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
            bg_s = pygame.Surface((hr.w+20, hr.h+10), pygame.SRCALPHA)
            bg_s.fill((0,0,0,160))
            surface.blit(bg_s, (hr.x-10, hr.y-5))
            surface.blit(hint, hr)

        # ── 12. Rappel des touches P2 ──────────────────────────────────────────
        key_hint = self._font_sm.render(
            "ZQSD:Move · Clic:Tir · ESPACE:Dash · F:Skill · E:Coffre · 1/2:Arme",
            True, (150, 200, 255))
        surface.blit(key_hint, (10, self.h - 22))

    def _draw_player(self, surface: pygame.Surface, pdata: dict, tint: tuple | None):
        """Dessine un joueur à partir de ses données sérialisées."""
        x, y  = pdata['x'], pdata['y']
        state = pdata.get('anim_state', 'idle')
        img   = self._player_sprites.get(state, self._player_sprites['idle']).copy()

        # Flip horizontal selon la direction regardée
        if not pdata.get('facing_right', True):
            img = pygame.transform.flip(img, True, False)

        # Teinte colorée pour distinguer l'autre joueur si demandé
        if tint is not None:
            overlay = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            overlay.fill(tint)
            img.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        surface.blit(img, (x - img.get_width()//2, y - img.get_height()//2))

    def _draw_enemy(self, surface: pygame.Surface, edata: dict, epoch: str):
        """Dessine un ennemi et sa barre de vie à partir de ses données sérialisées."""
        eid   = edata['id']
        etype = edata['type']
        size  = edata['size']
        x, y  = edata['x'], edata['y']

        # Récupérer ou créer le sprite procédural en cache
        if eid not in self._enemy_surf_cache:
            col  = EPOCHS.get(epoch, {}).get('enemy_tint', (180, 80, 80))
            surf = self._build_enemy_surf(etype, size, col)
            self._enemy_surf_cache[eid] = surf

            # Nettoyer le cache si trop grand (ennemis morts pas retirés)
            if len(self._enemy_surf_cache) > 200:
                # Garder seulement les 100 plus récents
                keys = list(self._enemy_surf_cache.keys())
                for k in keys[:100]:
                    del self._enemy_surf_cache[k]

        surf = self._enemy_surf_cache[eid]
        surface.blit(surf, (x - size//2, y - size//2))

        # Barre de vie au-dessus
        hp_ratio = max(0, edata['health'] / max(1, edata['max_health']))
        bar_w = size
        bar_h = 6 if etype != 'boss' else 14
        bar_x = x - bar_w//2
        bar_y = y - size//2 - bar_h - 4

        pygame.draw.rect(surface, (60, 20, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        if hp_ratio > 0:
            hp_col = EPOCHS.get(epoch, {}).get('color', (200, 0, 0))
            pygame.draw.rect(surface, hp_col,
                             (bar_x, bar_y, int(bar_w * hp_ratio), bar_h), border_radius=2)
        pygame.draw.rect(surface, (200, 200, 200),
                         (bar_x, bar_y, bar_w, bar_h), 1, border_radius=2)

    def _build_enemy_surf(self, etype: str, size: int, color: tuple) -> pygame.Surface:
        """Génère un sprite procédural d'ennemi (identique à base_room.py)."""
        s    = size
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        r, g, b = color[:3]

        if etype == 'tank':
            pygame.draw.ellipse(surf, (r, g, b), (2, 10, s-4, s-12))
            pygame.draw.circle(surf, (r, g, b), (s//2, s//4), s//5)
            pygame.draw.circle(surf, (200, 0, 0), (s//2-5, s//4), 4)
            pygame.draw.circle(surf, (200, 0, 0), (s//2+5, s//4), 4)
            pygame.draw.ellipse(surf, (255,255,255), (2, 10, s-4, s-12), 2)
        elif etype == 'rusher':
            pygame.draw.ellipse(surf, (r, g, b), (6, 8, s-12, s-10))
            pygame.draw.circle(surf, (min(255,r+30), g, b), (s//2, s//5), s//6)
            pygame.draw.circle(surf, (255, 255, 0), (s//2-4, s//5), 3)
            pygame.draw.circle(surf, (255, 255, 0), (s//2+4, s//5), 3)
        elif etype == 'sniper':
            pygame.draw.polygon(surf, (r, g, b), [(s//2,4),(s-6,s-6),(6,s-6)])
            pygame.draw.circle(surf, (min(255,r+50),min(255,g+50),min(255,b+50)), (s//2,s//3), s//6)
        elif etype == 'boss':
            pygame.draw.ellipse(surf, (r//2, g//2, b//2), (0,0,s,s))
            pygame.draw.ellipse(surf, (r, g, b), (4,4,s-8,s-8))
            for i in range(8):
                angle = math.radians(i*45)
                px = int(s//2 + math.cos(angle)*(s//2-2))
                py = int(s//2 + math.sin(angle)*(s//2-2))
                pygame.draw.circle(surf, (min(255,r+60),min(255,g+40),b), (px,py), 5)
            pygame.draw.circle(surf, (255,0,0), (s//3,s//3), 8)
            pygame.draw.circle(surf, (255,0,0), (s*2//3,s//3), 8)
            pygame.draw.ellipse(surf, (255,255,255), (0,0,s,s), 3)
        else:
            pygame.draw.circle(surf, (r, g, b), (s//2, s//2), s//2-2)
        return surf

    def _draw_client_hud(self, surface, p2, epoch, wave, wave_complete, boss_wave, enemies_left):
        """Dessine notre HUD (P2) en bas à gauche, similaire au HUD standard."""
        # Déléguer au HUDRenderer standard si possible (il attend un objet Player)
        # On crée un objet temporaire pour l'adapter
        class _FakePlayer:
            pass
        fp = _FakePlayer()
        fp.health      = p2['health']
        fp.max_health  = p2['max_health']
        fp.stamina     = p2['stamina']
        fp.max_stamina = p2['max_stamina']
        fp.kills       = p2['kills']
        fp.coins       = p2['coins']
        fp.skill       = p2['skill']
        fp.inventory   = p2['inventory']
        fp.current_weapon = type('W', (), {'key': p2['weapon']})()
        fp.skill_cooldown = 0
        fp.skill_active   = False
        fp.dash_cooldown  = 0
        fp.damage_boost   = 1.0
        fp.speed_boost    = 1.0
        try:
            self.hud.draw(surface, fp, epoch, wave, wave_complete, boss_wave,
                          enemies_left=enemies_left)
        except Exception:
            # Fallback HUD minimal si le HUDRenderer est incompatible
            self._draw_minimal_hud(surface, p2)

    def _draw_minimal_hud(self, surface, p2):
        """HUD de secours si le HUDRenderer standard échoue."""
        BAR_W, BAR_H = 200, 16
        x, y = 20, self.h - 60

        # Fond
        bg = pygame.Surface((BAR_W + 80, 50), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        surface.blit(bg, (x - 5, y - 5))

        # Barre de vie
        pygame.draw.rect(surface, (80, 20, 20), (x, y, BAR_W, BAR_H), border_radius=4)
        ratio = max(0, p2['health'] / max(1, p2['max_health']))
        pygame.draw.rect(surface, (220, 60, 60),
                         (x, y, int(BAR_W * ratio), BAR_H), border_radius=4)
        pygame.draw.rect(surface, (255,255,255), (x, y, BAR_W, BAR_H), 1, border_radius=4)
        hp_txt = self._font_sm.render(f"HP {int(p2['health'])}/{p2['max_health']}", True, (255,255,255))
        surface.blit(hp_txt, (x + BAR_W + 6, y))

        # Barre de stamina
        pygame.draw.rect(surface, (20, 20, 80),
                         (x, y + BAR_H + 4, BAR_W, BAR_H - 4), border_radius=4)
        sta_ratio = max(0, p2['stamina'] / max(1, p2['max_stamina']))
        pygame.draw.rect(surface, (60, 120, 255),
                         (x, y + BAR_H + 4, int(BAR_W * sta_ratio), BAR_H - 4), border_radius=4)

    def _draw_p1_hud_small(self, surface, p1):
        """Affiche les stats de P1 en petit en bas à droite (informations seulement)."""
        font = self._font_sm
        skill_name = SKILLS.get(p1['skill'], {}).get('name', 'P1') if p1['skill'] else 'P1'

        lines = [
            (f"P1 — {skill_name}", (200, 180, 255)),
            (f"HP: {int(p1['health'])}/{p1['max_health']}", (220, 100, 100)),
            (f"Kills: {p1['kills']}  Pièces: {p1['coins']}", GOLD),
        ]
        panel_h = len(lines) * 20 + 12
        panel_w = 220
        px = self.w - panel_w - 14
        py = self.h - panel_h - 14

        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill((10, 10, 30, 170))
        pygame.draw.rect(bg, (80, 60, 140), bg.get_rect(), 1, border_radius=6)
        surface.blit(bg, (px, py))

        for i, (text, col) in enumerate(lines):
            t = font.render(text, True, col)
            surface.blit(t, (px + 8, py + 6 + i * 20))
