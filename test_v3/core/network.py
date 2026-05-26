# -*- coding: utf-8 -*-
# core/network.py - Module reseau pour le multijoueur en ligne (UDP)

"""
ARCHITECTURE RESEAU
===============================================================================
Le jeu utilise un modele CLIENT-SERVEUR ou :

  HOST (P1)  = serveur + joueur local
    -> Fait tourner TOUTE la simulation du jeu (physique, ennemis, collisions)
    -> Recoit les inputs de P2 via UDP
    -> Envoie l'etat complet du jeu a P2 chaque frame
    -> P1 joue normalement en local (clavier/souris)

  CLIENT (P2) = client + joueur distant
    -> N'execute AUCUNE simulation
    -> Capture ses inputs locaux (clavier/souris) et les envoie au serveur
    -> Recoit l'etat du jeu et l'affiche (rendu pur, pas de logique)
    -> Latence = aller-retour reseau (idealement < 50ms en LAN / < 100ms en WAN)

PROTOCOLE
-----------------------------------------------------------------------------
Transport : UDP (User Datagram Protocol)
  -> Choix prefere pour les jeux temps reel : latence minimale, pas de retransmission
  -> Inconvenient : paquets peuvent etre perdus -> on ignore les paquets manques
    (le prochain arrivera, et un etat legerement ancien est preferable a un freeze)

Format    : JSON encode en UTF-8
  -> Simple a deboguer (readable), suffisant pour 60 fps en LAN
  -> Pour optimiser: remplacer par msgpack ou struct binaire

Taille max paquet : 65535 bytes (limite UDP theorique)
  -> L'etat du jeu serialise depasse rarement 4096 bytes

TYPES DE MESSAGES
-----------------------------------------------------------------------------
Client -> Serveur :
  {"type": "hello"}                           # Demande de connexion initiale
  {"type": "input", "data": {...}}            # Inputs du joueur 2 chaque frame
  {"type": "bye"}                             # Deconnexion propre

Serveur -> Client :
  {"type": "welcome", "skill": "...", "epoch": "..."}  # Confirmation de connexion
  {"type": "state",   "data": {...}}          # Etat complet du jeu chaque frame
  {"type": "start",   "skill2": "..."}        # Signal que la partie commence

PORT PAR DEFAUT : 55_555
  -> Choisir un port > 1024 (pas besoin de droits admin)
  -> Ouvrir ce port dans le pare-feu Windows/macOS si necessaire
  -> Sur routeur : rediriger UDP 55555 vers l'IP locale du host pour jouer sur internet

SCHEMA DE L'ETAT SERIALISE (envoye par le serveur chaque frame)
-----------------------------------------------------------------------------
{
  "epoch"        : str,           # Epoque courante ("prehistoire", "grece", ...)
  "wave"         : int,           # Numero de vague
  "wave_complete": bool,
  "boss_wave"    : bool,
  "show_chest_hint": bool,
  "game_over"    : bool,          # True si la partie est terminee
  "next_epoch"   : str | null,    # Renseigne si transition d'epoque en cours
  "p1": {
    "x", "y"         : int,       # Position centre du sprite
    "health"         : float,
    "max_health"     : int,
    "stamina"        : float,
    "max_stamina"    : int,
    "kills"          : int,
  "facing_right"   : bool,
    "anim_state"     : str,       # "idle" / "run"
    "skill"          : str,
    "weapon"         : str,
    "inventory"      : list[str],
  },
  "p2": { ... meme structure ... } | null,
  "enemies": [
    {"id": int, "x": int, "y": int, "health": int, "max_health": int,
     "type": str, "size": int, "epoch": str}
  ],
  "bullets"      : [{"x": int, "y": int}],
  "enemy_bullets": [{"x": int, "y": int}],
  "powerups"     : [{"x": int, "y": int, "type": str}],
  "chests"       : [{"x": int, "y": int, "opened": bool}],
}

SCHEMA DES INPUTS (envoyes par le client chaque frame)
-----------------------------------------------------------------------------
{
  "dx": float,         # Direction X normalisee (-1.0 a 1.0)
  "dy": float,         # Direction Y normalisee (-1.0 a 1.0)
  "dash": bool,        # true si touche dash pressee ce frame
  "skill": bool,       # true si touche skill pressee ce frame
  "fire": bool,        # true si clic gauche presse ce frame
  "fire_tx": int,      # Coordonnee X cible du tir (position souris)
  "fire_ty": int,      # Coordonnee Y cible du tir
  "chest": bool,       # true si touche coffre pressee ce frame
  "weapon_idx": int,   # Index arme a equiper, -1 si pas de changement
}
"""

import socket
import json
import threading
import time
import math
import pygame
from .constants import EPOCHS, ENEMY_CONFIG, SKILLS, GOLD, RED, WHITE, SCREEN_WIDTH, SCREEN_HEIGHT
from .graphics import draw_weapon_in_hand, tint_surface, draw_enemy_health_bar
from .mechanics import Chest

# -- Constantes reseau ---------------------------------------------------------
DEFAULT_PORT    = 55_600   # Port UDP par defaut (a ouvrir dans le pare-feu)
RECV_BUFFER     = 65_535   # Taille du buffer de reception UDP (max theorique)
SEND_BUFFER     = 65_535   # Taille du buffer d'envoi
CONNECT_TIMEOUT = 10.0     # Secondes avant d'abandonner la tentative de connexion
PING_INTERVAL   = 1.0      # Secondes entre deux pings de maintien de connexion


# ==============================================================================
#  UTILITAIRES
# ==============================================================================

def get_local_ip() -> str:
    """
    Compatible Windows natif, WSL et Linux.
    """
    import subprocess
    import re

    # Methode 1 : ip route (Linux/WSL) - cherche l'interface utilisee pour sortir
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

    # Methode 2 : hostname -I (Linux) - liste toutes les IPs, prend la premiere LAN
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

    # Methode 3 : ipconfig (Windows natif)
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

    # Methode 4 : fallback socket
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
    """Serialise un dict Python en JSON UTF-8."""
    return json.dumps(msg, separators=(',', ':')).encode('utf-8')


def decode(data: bytes) -> dict | None:
    """
    Deserialise des bytes JSON en dict.
    Retourne None si le paquet est corrompu (plutot que de crasher).
    """
    try:
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# ==============================================================================
#  SERVEUR (HOST / P1)
# ==============================================================================

class GameServer:
    """
    Serveur UDP hebergeant la partie multijoueur.

    Le host cree une instance de GameServer, attend qu'un client se connecte,
    puis chaque frame :
      1. Appelle poll()            -> traite les paquets entrants
      2. Lit get_client_inputs()   -> recupere les derniers inputs P2
      3. Appelle send_state(state) -> envoie l'etat du jeu au client

    THREAD-SAFETY :
      Les donnees partagees (client_inputs) sont protegees par un Lock.
      poll() est appele depuis le thread principal (game loop), pas depuis un thread separe.
      -> On utilise setblocking(False) pour un polling non-bloquant.

    UTILISATION :
      server = GameServer()
      local_ip = server.local_ip   # A afficher au host pour que P2 puisse se connecter
      # Dans la boucle de jeu :
      server.poll()
      inputs = server.get_client_inputs()
      server.send_state(game_state_dict)
    """

    def __init__(self, port: int = DEFAULT_PORT):
        # -- Creation du socket UDP ---------------------------------------------
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reutiliser le port apres crash
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SEND_BUFFER)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RECV_BUFFER)
        self.sock.bind(('', port))       # Ecoute sur toutes les interfaces reseau
        self.sock.setblocking(False)     # Non-bloquant : recvfrom() leve BlockingIOError si vide

        self.port      = port
        self.local_ip  = get_local_ip()  # IP a communiquer au client

        # -- Etat connexion -----------------------------------------------------
        self.client_addr  = None   # Tuple (ip, port) du client connecte
        self.connected    = False  # True apres reception du premier "hello"
        self.p2_skill     = None   # Classe choisie par P2 (envoyee dans "hello")
        self.host_replay_vote = False
        self.client_replay_vote = False

        # -- Inputs P2 (derniere frame recue) ----------------------------------
        # Dict contenant les touches pressees par P2 au dernier poll()
        self._client_inputs = {}
        self._lock          = threading.Lock()  # Protege _client_inputs

        # -- Statistiques reseau (optionnel) -----------------------------------
        self.packets_sent     = 0
        self.packets_received = 0
        self.last_recv_time   = time.time()  # Pour detecter une deconnexion

        print(f"[SERVER] En ecoute sur {self.local_ip}:{port}")
        print(f"[SERVER] Communiquez cette IP a P2 : {self.local_ip}")

    # -- Polling (non-bloquant, a appeler chaque frame) ------------------------

    def poll(self):
        """
        Lit tous les paquets UDP recus depuis le dernier poll().
        Traite jusqu'a 10 paquets par frame pour eviter de bloquer la game loop.
        Doit etre appele UNE FOIS PAR FRAME dans la boucle principale.
        """
        for _ in range(10):  # Limite : traiter max 10 paquets par frame
            try:
                data, addr = self.sock.recvfrom(RECV_BUFFER)
            except BlockingIOError:
                break   # File vide, on arrete
            except OSError:
                break

            msg = decode(data)
            if msg is None:
                continue  # Paquet corrompu, ignorer

            msg_type = msg.get('type', '')

            # -- Demande de connexion initiale ----------------------------------
            if msg_type == 'hello':
                self.client_addr = addr
                self.connected   = True
                self.p2_skill    = msg.get('skill', 'tank')  # Classe choisie par P2
                self.last_recv_time = time.time()

                # Repondre avec "welcome" pour confirmer la connexion
                self._send({'type': 'welcome',
                            'msg':  'Connexion etablie !'}, addr)
                print(f"[SERVER] Client connecte depuis {addr[0]}:{addr[1]}")
                print(f"[SERVER] P2 joue la classe : {self.p2_skill}")

            # -- Inputs du client (chaque frame) -------------------------------
            elif msg_type == 'input' and addr == self.client_addr:
                with self._lock:
                    # On garde seulement les derniers inputs (le precedent est obsolete)
                    self._client_inputs = msg.get('data', {})
                self.last_recv_time = time.time()
                self.packets_received += 1

            elif msg_type == 'replay_vote' and addr == self.client_addr:
                self.client_replay_vote = bool(msg.get('want', False))
                self.last_recv_time = time.time()
                self.send_replay_status()

            # -- Deconnexion propre ---------------------------------------------
            elif msg_type == 'bye' and addr == self.client_addr:
                print(f"[SERVER] Client deconnecte proprement")
                self.connected   = False
                self.client_addr = None
                self.client_replay_vote = False
                self.host_replay_vote = False

    def get_client_inputs(self) -> dict:
        """
        Retourne les derniers inputs recus du client P2.
        Thread-safe grace au Lock.

        Structure retournee :
          {"dx": float, "dy": float, "dash": bool, "skill": bool,
           "fire": bool, "fire_tx": int, "fire_ty": int,
           "chest": bool, "weapon_idx": int}
        """
        with self._lock:
            return dict(self._client_inputs)  # Copie pour eviter les modifications concurrentes

    def send_state(self, state: dict):
        """
        Envoie l'etat complet du jeu au client.
        Si le client est deconnecte, ne fait rien (pas d'erreur).

        state : dict retourne par BaseRoom.serialize_state()
        """
        if self.client_addr is None:
            return
        self._send({'type': 'state', 'data': state}, self.client_addr)
        self.packets_sent += 1

    def send_start(self, p1_skill: str):
        """
        Envoie le signal de debut de partie au client.
        Inclut la classe de P1 pour que le client puisse afficher les infos correctes.
        """
        if self.client_addr:
            self._send({'type': 'start', 'p1_skill': p1_skill}, self.client_addr)

    def set_host_replay_vote(self, want: bool):
        self.host_replay_vote = bool(want)
        self.send_replay_status()

    def reset_replay_votes(self):
        self.host_replay_vote = False
        self.client_replay_vote = False

    def get_replay_votes(self) -> tuple[bool, bool]:
        return self.host_replay_vote, self.client_replay_vote

    def send_replay_status(self):
        if self.client_addr:
            self._send({
                'type': 'replay_status',
                'host_vote': self.host_replay_vote,
                'client_vote': self.client_replay_vote,
                'game_over': True,
            }, self.client_addr)

    def send_replay_begin(self, p1_skill: str):
        if self.client_addr:
            self._send({'type': 'replay_begin', 'p1_skill': p1_skill}, self.client_addr)

    def is_client_timeout(self, timeout: float = 5.0) -> bool:
        """
        Retourne True si le client n'a pas envoye de paquet depuis `timeout` secondes.
        Permet de detecter une deconnexion inattendue (crash, coupure reseau).
        """
        return self.connected and (time.time() - self.last_recv_time > timeout)

    def _send(self, msg: dict, addr: tuple):
        """Envoie un message JSON au destinataire. Ignore les erreurs reseau."""
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
        print("[SERVER] Socket ferme")


# ==============================================================================
#  CLIENT (GUEST / P2)
# ==============================================================================

class GameClient:
    """
    Client UDP se connectant au serveur host.

    P2 cree une instance de GameClient, se connecte au serveur,
    puis chaque frame :
      1. Appelle poll()            -> traite les paquets entrants (etat du jeu)
      2. Appelle send_inputs(...)  -> envoie ses inputs locaux au serveur
      3. Lit get_state()           -> recupere le dernier etat pour le rendu

    UTILISATION :
      client = GameClient('192.168.1.42')   # IP du host
      client.connect('mage')                # Envoyer hello + sa classe
      # Dans la boucle de jeu :
      client.poll()
      client.send_inputs(inputs_dict)
      state = client.get_state()
      # -> rendre state
    """

    def __init__(self, host: str, port: int = DEFAULT_PORT):
        # -- Creation du socket UDP ---------------------------------------------
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SEND_BUFFER)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RECV_BUFFER)
        self.sock.setblocking(False)   # Non-bloquant pour ne pas freezer le jeu

        self.server_addr = (host, port)
        self.connected   = False       # True apres reception de "welcome"
        self.p1_skill    = None        # Classe de P1 (recue dans "start")
        self.started     = False       # True apres reception de "start"
        self.host_replay_vote = False
        self.client_replay_vote = False
        self.replay_begin = False
        self.remote_game_over = False

        # -- Dernier etat recu -------------------------------------------------
        # Dict serialise recu du serveur, utilise pour le rendu
        self._latest_state = {}
        self._state_lock   = threading.Lock()
        self._latest_frame = -1

        self.packets_received = 0
        self.last_recv_time   = time.time()

        print(f"[CLIENT] Socket cree, serveur cible : {host}:{port}")

    # -- Connexion -------------------------------------------------------------

    def connect(self, skill: str):
        """
        Envoie un message "hello" au serveur pour initier la connexion.
        Inclut la classe choisie par P2 pour que le serveur cree le bon personnage.

        skill : str -> cle de classe ("tank", "mage", ...)
        Le serveur repondra par "welcome" qui sera capture dans poll().
        """
        self._send({'type': 'hello', 'skill': skill})
        print(f"[CLIENT] Envoi hello au serveur (classe={skill})...")

    # -- Polling (non-bloquant, a appeler chaque frame) ------------------------

    def poll(self):
        """
        Lit tous les paquets UDP disponibles depuis le dernier poll().
        A appeler UNE FOIS PAR FRAME dans la boucle de rendu.
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

            # -- Confirmation de connexion --------------------------------------
            if msg_type == 'welcome':
                self.connected = True
                print(f"[CLIENT] Connecte au serveur !")

            # -- Signal de debut de partie --------------------------------------
            elif msg_type == 'start':
                self.p1_skill = msg.get('p1_skill')
                self.started  = True
                self._latest_frame = -1
                with self._state_lock:
                    self._latest_state = {}
                print(f"[CLIENT] Partie demarree ! P1 joue : {self.p1_skill}")

            elif msg_type == 'replay_status':
                self.host_replay_vote = bool(msg.get('host_vote', False))
                self.client_replay_vote = bool(msg.get('client_vote', False))
                self.remote_game_over = bool(msg.get('game_over', False))

            elif msg_type == 'replay_begin':
                self.p1_skill = msg.get('p1_skill', self.p1_skill)
                self.replay_begin = True
                self._latest_frame = -1
                with self._state_lock:
                    self._latest_state = {}

            # -- Etat du jeu (chaque frame du serveur) --------------------------
            elif msg_type == 'state':
                state = msg.get('data', {})
                frame = int(state.get('f', state.get('frame', -1) or -1))
                with self._state_lock:
                    if frame >= self._latest_frame:
                        self._latest_state = state
                        self._latest_frame = frame
                self.last_recv_time = time.time()
                self.packets_received += 1

            # -- Deconnexion serveur --------------------------------------------
            elif msg_type == 'bye':
                self.connected = False
                print("[CLIENT] Le serveur s'est deconnecte")

    def send_inputs(self, inputs: dict):
        """
        Envoie les inputs locaux de P2 au serveur.
        Appele chaque frame, meme si rien n'a change (le serveur a toujours besoin
        d'un etat recent pour savoir que P2 est vivant).

        inputs : dict avec les cles definies dans le module (dx, dy, fire, ...)
        """
        self._send({'type': 'input', 'data': inputs})

    def send_replay_vote(self, want: bool):
        self._send({'type': 'replay_vote', 'want': bool(want)})

    def consume_replay_begin(self) -> bool:
        if not self.replay_begin:
            return False
        self.replay_begin = False
        self.host_replay_vote = False
        self.client_replay_vote = False
        self.remote_game_over = False
        return True

    def get_state(self) -> dict:
        """
        Retourne le dernier etat de jeu recu du serveur.
        Thread-safe. Retourne {} si aucun etat recu encore.
        """
        with self._state_lock:
            return dict(self._latest_state)

    def is_server_timeout(self, timeout: float = 5.0) -> bool:
        """Retourne True si le serveur n'a pas repondu depuis `timeout` secondes."""
        return self.connected and (time.time() - self.last_recv_time > timeout)

    def _send(self, msg: dict):
        """Envoie un message JSON au serveur. Ignore les erreurs reseau."""
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
        print("[CLIENT] Socket ferme")


# ==============================================================================
#  RENDU COTE CLIENT  (dessine l'etat recu du serveur)
# ==============================================================================

class ClientRenderer:
    """
    Moteur de rendu pour le client (P2).

    Le client ne fait PAS tourner la simulation du jeu. Il recoit un dict
    d'etat du serveur et le dessine chaque frame. Ce renderer reconstruit
    visuellement l'etat sans avoir besoin des groupes de sprites.

    LIMITES :
      - Les animations de particules ne sont pas synchronisees (non-critique)
      - Les effets de flash/shake ne sont pas reproduits cote client
      - Les animations de sprites sont simplifiees (une seule frame idle/run)

    Pour ameliorer : envoyer aussi les particules actives dans le state dict.
    """

    def __init__(self, screen_w: int, screen_h: int):
        from .graphics import BackgroundRenderer, HUDRenderer, SpriteCache
        self.w = screen_w
        self.h = screen_h
        self.bg_renderer = BackgroundRenderer(screen_w, screen_h)
        self.hud         = HUDRenderer(screen_w, screen_h)
        self._cache      = SpriteCache.get()

        # Pre-charger les sprites joueurs pour le rendu
        self._player_sprites = {}
        for state in ("idle", "run", "dead"):
            if state == "idle":
                name = "char_idle_one_arm"
            elif state == "run":
                name = "char_run1_one_arm"
            else:
                name = "char_dead_one_arm"
            try:
                self._player_sprites[state] = self._cache.load(
                    "sprites_final", f"{name}.png", size=(80, 80))
            except Exception:
                # Fallback : cercle colore si l'image est introuvable
                surf = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(surf, (200, 200, 255), (40, 40), 35)
                self._player_sprites[state] = surf

        self._enemy_anim_cache: dict[tuple, dict[str, list[pygame.Surface]]] = {}
        self._projectile_cache: dict[tuple, pygame.Surface] = {}
        chest = Chest(0, 0)
        self._chest_closed_frames = list(chest._portal_frames)
        self._chest_open_frames = list(chest._portal_open_frames)

        # Police pour les textes HUD client
        self._font_md = pygame.font.Font(None, 30)
        self._font_sm = pygame.font.Font(None, 22)

    def _normalize_player(self, pdata: dict | None) -> dict | None:
        if not pdata:
            return None
        if 'health' in pdata:
            return pdata
        return {
            'x': int(pdata.get('x', 0)),
            'y': int(pdata.get('y', 0)),
            'health': float(pdata.get('h', 0)),
            'max_health': int(pdata.get('mh', 1)),
            'stamina': float(pdata.get('s', 0)),
            'max_stamina': int(pdata.get('ms', 1)),
            'kills': int(pdata.get('k', 0)),
            'facing_right': bool(pdata.get('fr', 1)),
            'aim_x': int(pdata.get('ax', pdata.get('x', 0))),
            'aim_y': int(pdata.get('ay', pdata.get('y', 0))),
            'anim_state': pdata.get('an', 'idle'),
            'skill': pdata.get('sk'),
            'weapon': pdata.get('w', 'rock'),
            'inventory': list(pdata.get('i', ['rock'])),
            'is_downed': bool(pdata.get('dn', 0)),
            'revive_progress': int(pdata.get('rv', 0)),
            'render_alpha': int(pdata.get('ra', 255)),
            'skill_cooldown': int(pdata.get('sc', 0)),
            'skill_active': bool(pdata.get('sa', 0)),
            'damage_boost': float(pdata.get('db', 1.0)),
            'speed_boost': float(pdata.get('sb', 1.0)),
            'boost_timer': int(pdata.get('bt', 0)),
            'weapon_cooldown': int(pdata.get('wcd', 0)),
            'weapon_cooldown_max': int(pdata.get('wcm', 1)),
        }

    def _normalize_enemies(self, state: dict) -> list[dict]:
        enemies = state.get('enemies')
        if enemies is not None:
            return enemies
        out = []
        for edata in state.get('en', []):
            out.append({
                'id': edata.get('i', 0),
                'x': int(edata.get('x', 0)),
                'y': int(edata.get('y', 0)),
                'health': int(edata.get('h', 0)),
                'max_health': int(edata.get('m', 1)),
                'type': edata.get('t', 'rusher'),
                'size': int(edata.get('z', 40)),
                'anim_state': edata.get('an', 'idle'),
                'anim_frame': int(edata.get('af', 0)),
                'facing_right': bool(edata.get('fr', 1)),
            })
        return out

    def _normalize_points(self, values: list, key: str | None = None) -> list[dict]:
        out = []
        for entry in values:
            if isinstance(entry, dict):
                out.append(entry)
                continue
            if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                continue
            item = {'x': int(entry[0]), 'y': int(entry[1])}
            if key and len(entry) > 2:
                item[key] = entry[2]
            out.append(item)
        return out

    def _normalize_state(self, state: dict) -> dict:
        if state.get('v') != 2:
            return state
        return {
            'epoch': state.get('ep', 'prehistoire'),
            'wave': int(state.get('wv', 1)),
            'wave_complete': bool(state.get('wc', 0)),
            'boss_wave': bool(state.get('bw', 0)),
            'music_key': state.get('mk'),
            'sound_events': list(state.get('sx', [])),
            'enemies_left': int(state.get('el', 0)),
            'show_chest_hint': bool(state.get('sh', 0)),
            'objective_hint': state.get('oh', ''),
            'game_over': bool(state.get('go', 0)),
            'next_epoch': state.get('ne'),
            'p1': self._normalize_player(state.get('p1')),
            'p2': self._normalize_player(state.get('p2')),
            'enemies': self._normalize_enemies(state),
            'bullets': self._normalize_points(state.get('bu', [])),
            'enemy_bullets': self._normalize_points(state.get('eb', [])),
            'powerups': self._normalize_points(state.get('pu', []), key='type'),
            'chests': self._normalize_points(state.get('ch', []), key='opened'),
        }

    def draw(self, surface: pygame.Surface, state: dict):
        """
        Dessine l'etat complet du jeu a partir du dict recu du serveur.

        Ordre de rendu :
          1. Fond (background de l'epoque)
          2. Power-ups
          3. Coffres
          4. Projectiles joueurs (petits cercles)
          5. Balles ennemies (petits cercles colores)
          6. Ennemis (sprites proceduraux + barres de vie)
          7. Joueur 1 (P1, sprite violet)
          8. Joueur 2 (P2 = nous, sprite bleu)
          9. HUD P2 (nos propres stats en premier)
          10. HUD P1 (stats de P1)
          11. Infos de vague
          12. Hint portail
        """
        state = self._normalize_state(state)
        epoch = state.get('epoch', 'prehistoire')

        # -- 1. Fond -----------------------------------------------------------
        bg = self.bg_renderer.get(epoch)
        surface.blit(bg, (0, 0))

        # -- 2. Power-ups ------------------------------------------------------
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

        # -- 3. Coffres --------------------------------------------------------
        for chest in state.get('chests', []):
            cx, cy = chest['x'], chest['y']
            opened = bool(chest['opened'])
            frames = self._chest_open_frames if opened else self._chest_closed_frames
            frame_idx = (pygame.time.get_ticks() // 100) % len(frames)
            img = frames[frame_idx]
            rect = img.get_rect(center=(cx, cy))
            surface.blit(img, rect)

        # -- 4. Projectiles joueurs --------------------------------------------
        for b in state.get('bullets', []):
            self._draw_projectile(surface, b, enemy=False)

        # -- 5. Balles ennemies -----------------------------------------------
        for b in state.get('enemy_bullets', []):
            self._draw_projectile(surface, b, enemy=True, epoch=epoch)

        # -- 6. Ennemis --------------------------------------------------------
        for edata in state.get('enemies', []):
            self._draw_enemy(surface, edata, epoch)

        # -- 7. Joueur 1 (P1 = l'autre joueur, teinte pour le distinguer) -----
        p1 = state.get('p1')
        if p1 and (p1['health'] > 0 or p1.get('is_downed')):
            self._draw_player(surface, p1, tint=(180, 100, 255, 50))
            p1_txt = self._font_sm.render("P1", True, (220, 180, 255))
            surface.blit(p1_txt, (p1['x'] - p1_txt.get_width()//2, p1['y'] - 58))

        # -- 8. Joueur 2 (P2 = nous, rendu normal) ----------------------------
        p2 = state.get('p2')
        if p2 and (p2['health'] > 0 or p2.get('is_downed')):
            self._draw_player(surface, p2, tint=None)
            # Indicateur "VOUS" au-dessus de P2
            you_txt = self._font_sm.render("VOUS", True, (120, 200, 255))
            surface.blit(you_txt, (p2['x'] - you_txt.get_width()//2, p2['y'] - 58))
        if p1 and p1.get('is_downed') and p1.get('revive_progress', 0) > 0:
            self._draw_revive_bar(surface, p1, (180, 220, 255))
        if p2 and p2.get('is_downed') and p2.get('revive_progress', 0) > 0:
            self._draw_revive_bar(surface, p2, (120, 220, 255))
        if p1 and p1.get('is_downed') and p2 and not p2.get('is_downed'):
            prompt = self._font_sm.render("Maintenir E pour reanimer P1", True, (180, 220, 255))
            surface.blit(prompt, (10, self.h - 46))

        # -- 9. HUD P2 (notre barre de vie, en bas a gauche, en premier) -------
        if p2:
            self._draw_client_hud(surface, p2, epoch,
                                   state.get('wave', 1),
                                   state.get('wave_complete', False),
                                   state.get('boss_wave', False),
                                   state.get('enemies_left', 0))

        # -- 10. HUD P1 (stats de P1 en bas a droite) -------------------------
        if p1:
            self._draw_p1_hud_small(surface, p1)

        # -- 11. Hint portail ---------------------------------------------------
        if state.get('show_chest_hint'):
            font = pygame.font.Font(None, 32)
            hint = font.render(state.get('objective_hint', "E : Activer le portail"), True, GOLD)
            hr = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
            bg_s = pygame.Surface((hr.w+20, hr.h+10), pygame.SRCALPHA)
            bg_s.fill((0,0,0,160))
            surface.blit(bg_s, (hr.x-10, hr.y-5))
            surface.blit(hint, hr)

        # -- 12. Rappel des touches P2 ------------------------------------------
        key_hint = self._font_sm.render(
            "ZQSD:Move  -  Clic:Tir  -  ESPACE:Dash  -  F:Skill  -  E:Rea/Portail  -  1..9:Arme",
            True, (150, 200, 255))
        surface.blit(key_hint, (10, self.h - 22))

    def _draw_player(self, surface: pygame.Surface, pdata: dict, tint: tuple | None):
        """Dessine un joueur a partir de ses donnees serialisees."""
        x, y  = pdata['x'], pdata['y']
        state = pdata.get('anim_state', 'idle')
        alpha = int(pdata.get('render_alpha', 255))
        if alpha <= 0:
            return
        img   = self._player_sprites.get(state, self._player_sprites['idle']).copy()

        # Flip horizontal selon la direction regardee
        if not pdata.get('facing_right', True):
            img = pygame.transform.flip(img, True, False)

        # Teinte coloree pour distinguer l'autre joueur si demande
        if tint is not None:
            img = tint_surface(img, tint[:3], alpha=tint[3] if len(tint) > 3 else 180)
        img.set_alpha(alpha)
        draw_rect = img.get_rect(center=(x, y))
        surface.blit(img, draw_rect)
        weapon_key = pdata.get('weapon')
        if weapon_key and not pdata.get('is_downed') and alpha >= 220:
            from .mechanics import Weapon
            weapon = Weapon(weapon_key)
            aim_x = int(pdata.get('aim_x', x + (100 if pdata.get('facing_right', True) else -100)))
            aim_y = int(pdata.get('aim_y', y))
            draw_weapon_in_hand(surface, draw_rect, weapon, pdata.get('facing_right', True), aim_pos=(aim_x, aim_y))

    def _draw_revive_bar(self, surface: pygame.Surface, pdata: dict, color: tuple):
        bw = 70
        bx = pdata['x'] - bw // 2
        by = pdata['y'] - 78
        progress = max(0.0, min(1.0, pdata.get('revive_progress', 0) / 90))
        pygame.draw.rect(surface, (30, 30, 30), (bx, by, bw, 7), border_radius=3)
        pygame.draw.rect(surface, color, (bx, by, int(bw * progress), 7), border_radius=3)
        pygame.draw.rect(surface, WHITE, (bx, by, bw, 7), 1, border_radius=3)

    def _draw_enemy(self, surface: pygame.Surface, edata: dict, epoch: str):
        """Dessine un ennemi et sa barre de vie a partir de ses donnees serialisees."""
        eid   = edata['id']
        etype = edata['type']
        size  = edata['size']
        x, y  = edata['x'], edata['y']

        surf = self._get_enemy_frame(epoch, etype, size, edata.get('anim_state', 'idle'), edata.get('anim_frame', 0))
        if not edata.get('facing_right', True):
            surf = pygame.transform.flip(surf, True, False)
        surface.blit(surf, (x - size//2, y - size//2))

        # Barre de vie au-dessus
        enemy_rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
        draw_enemy_health_bar(
            surface,
            enemy_rect,
            edata['health'],
            edata['max_health'],
            EPOCHS.get(epoch, {}).get('color', RED),
            is_boss=(etype == 'boss'),
            screen_w=self.w,
        )

    def _build_enemy_surf(self, etype: str, size: int, color: tuple) -> pygame.Surface:
        """Genere un sprite procedural d'ennemi (identique a base_room.py)."""
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

    def _get_enemy_frame(self, epoch: str, etype: str, size: int, anim_state: str, anim_frame: int) -> pygame.Surface:
        key = (epoch, etype, size)
        frames = self._enemy_anim_cache.get(key)
        if frames is None:
            cfg = ENEMY_CONFIG.get(epoch, ENEMY_CONFIG["prehistoire"]).get(etype, {})
            sprite_path = cfg.get("sprite")
            if sprite_path and (cfg.get("gif_animations") or cfg.get("sheet_frames")):
                if cfg.get("gif_animations"):
                    frames = {
                        state: self._cache.load_gif_frames(*anim_path, size=(size, size))
                        for state, anim_path in cfg["gif_animations"].items()
                    }
                else:
                    trim = bool(cfg.get("sheet_trim", True))
                    common_scale = bool(cfg.get("sheet_common_scale", False))
                    bbox_anchor = bool(cfg.get("sheet_bbox_anchor", False))
                    frames = {
                        state: self._cache.load_frames(
                            *sprite_path,
                            frame_rects=rects,
                            size=(size, size),
                            trim=trim,
                            common_scale=common_scale,
                            bbox_anchor=bbox_anchor,
                        )
                        for state, rects in cfg["sheet_frames"].items()
                    }
            else:
                col = EPOCHS.get(epoch, {}).get('enemy_tint', (180, 80, 80))
                frames = {'idle': [self._build_enemy_surf(etype, size, col)]}
            self._enemy_anim_cache[key] = frames

        seq = frames.get(anim_state) or frames.get('idle') or next(iter(frames.values()))
        return seq[min(max(anim_frame, 0), len(seq) - 1)]

    def _draw_projectile(self, surface: pygame.Surface, pdata: dict, enemy: bool, epoch: str | None = None):
        x, y = pdata['x'], pdata['y']
        angle = int(pdata.get('a', 0))

        if not enemy and pdata.get('w'):
            from .mechanics import Weapon
            weapon_key = pdata['w']
            cache_key = ('player', weapon_key)
            img = self._projectile_cache.get(cache_key)
            if img is None:
                weapon = Weapon(weapon_key)
                proj_size = max(20, weapon.size // 2)
                img = pygame.transform.scale(weapon.image, (proj_size, proj_size))
                self._projectile_cache[cache_key] = img
            rotated = pygame.transform.rotate(img, angle)
            surface.blit(rotated, rotated.get_rect(center=(x, y)))
            return

        if enemy and pdata.get('sp'):
            sprite_parts = tuple(str(pdata['sp']).split('/'))
            render_size = pdata.get('sz') or (22, 22)
            if isinstance(render_size, int):
                render_size = (render_size, render_size)
            cache_key = ('enemy', sprite_parts, tuple(render_size))
            img = self._projectile_cache.get(cache_key)
            if img is None:
                img = self._cache.load(*sprite_parts, size=tuple(render_size))
                self._projectile_cache[cache_key] = img
            rotated = pygame.transform.rotate(img, angle)
            surface.blit(rotated, rotated.get_rect(center=(x, y)))
            return

        color = EPOCHS.get(epoch or 'prehistoire', {}).get('enemy_tint', (200, 0, 0)) if enemy else (255, 255, 200)
        radius = 7 if enemy else 6
        outline = (255, 255, 255) if enemy else (255, 220, 0)
        pygame.draw.circle(surface, color, (x, y), radius)
        pygame.draw.circle(surface, outline, (x, y), radius, 1)

    def _draw_client_hud(self, surface, p2, epoch, wave, wave_complete, boss_wave, enemies_left):
        """Dessine notre HUD (P2) en bas a gauche, similaire au HUD standard."""
        # Deleguer au HUDRenderer standard si possible (il attend un objet Player)
        # On cree un objet temporaire pour l'adapter
        from .mechanics import Weapon
        class _FakePlayer:
            pass
        fp = _FakePlayer()
        fp.health      = p2['health']
        fp.max_health  = p2['max_health']
        fp.stamina     = p2['stamina']
        fp.max_stamina = p2['max_stamina']
        fp.kills       = p2['kills']
        fp.skill       = p2['skill']
        fp.inventory   = p2['inventory']
        fp.current_weapon = Weapon(p2['weapon']) if p2.get('weapon') else None
        fp.skill_cooldown = int(p2.get('skill_cooldown', 0))
        fp.skill_active   = bool(p2.get('skill_active', False))
        fp.dash_cooldown  = 0
        fp.damage_boost   = float(p2.get('damage_boost', 1.0))
        fp.speed_boost    = float(p2.get('speed_boost', 1.0))
        fp.boost_timer    = int(p2.get('boost_timer', 0))
        if fp.current_weapon is not None:
            fp.current_weapon.cooldown = int(p2.get('weapon_cooldown', 0))
            fp.current_weapon.cooldown_max = max(1, int(p2.get('weapon_cooldown_max', fp.current_weapon.cooldown_max)))
        try:
            self.hud.draw(surface, fp, epoch, wave, wave_complete, boss_wave,
                          enemies_left=enemies_left)
        except Exception:
            # Fallback HUD minimal si le HUDRenderer est incompatible
            self._draw_minimal_hud(surface, p2)

    def _draw_minimal_hud(self, surface, p2):
        """HUD de secours si le HUDRenderer standard echoue."""
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
        """Affiche les stats de P1 avec le meme panneau que le HUD principal."""
        from .mechanics import Weapon
        class _FakePlayer:
            pass

        fp = _FakePlayer()
        fp.health = p1['health']
        fp.max_health = p1['max_health']
        fp.stamina = p1['stamina']
        fp.max_stamina = p1['max_stamina']
        fp.kills = p1['kills']
        fp.skill = p1['skill']
        fp.inventory = p1['inventory']
        fp.current_weapon = Weapon(p1['weapon']) if p1.get('weapon') else None
        fp.skill_cooldown = int(p1.get('skill_cooldown', 0))
        fp.skill_active = bool(p1.get('skill_active', False))
        fp.damage_boost = float(p1.get('damage_boost', 1.0))
        fp.speed_boost = float(p1.get('speed_boost', 1.0))
        fp.boost_timer = int(p1.get('boost_timer', 0))
        if fp.current_weapon is not None:
            fp.current_weapon.cooldown = int(p1.get('weapon_cooldown', 0))
            fp.current_weapon.cooldown_max = max(1, int(p1.get('weapon_cooldown_max', fp.current_weapon.cooldown_max)))

        panel_w = self.hud.BAR_W + 80
        panel_h = 190
        px = self.w - panel_w - 14
        py = self.h - panel_h - 14
        self.hud.draw_player_panel(surface, fp, px, py)
        tag = self._font_sm.render("P1", True, (220, 180, 255))
        surface.blit(tag, (px + panel_w - tag.get_width() - 10, py + 8))
