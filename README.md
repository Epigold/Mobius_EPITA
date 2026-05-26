# Mobius EPITA

Mobius est un roguelike 2D realise dans le cadre du projet S2 a EPITA. Le jeu propose un mode solo et un mode multijoueur en ligne, avec une progression a travers plusieurs epoques et des armes differentes selon la salle en cours.

## Apercu

- 5 classes jouables : Tank, Berserker, Vampire, Ninja, Mage
- 6 epoques : Prehistoire, Grece Antique, Edo, Ere Moderne, Guerre mondiale, Futur
- Combats en temps reel avec armes de melee, distance et hybrides
- Portails, coffres, vagues d'ennemis et boss reguliers
- Multijoueur en ligne en host/client via UDP

## Lancer le jeu

### Prerequis

- Python 3.10 ou plus recent recommande
- `pygame`

### Installation rapide

Depuis la racine du depot :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pygame
python3 mobius/main.py
```

Sous Windows :

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install pygame
py mobius/main.py
```

### Desinstallation

Si vous voulez supprimer completement le jeu et le dossier du projet :

- sous Linux/macOS : `./desinstaller.sh`
- sous Windows : `desinstaller.bat`

Les scripts demandent une confirmation explicite avant de supprimer le dossier.

## Mode de jeu

Au lancement, le menu principal permet de :

- Jouer en solo
- Heberger une partie en ligne
- Rejoindre une partie en ligne
- Choisir une classe avant le debut de la partie

### Multijoueur

Le multijoueur fonctionne en host/client :

- le host simule la partie
- le client rejoint via l'adresse IP du host
- le port UDP utilise par defaut est `55600`

Si vous jouez hors reseau local, il faut ouvrir ou rediriger le port `55600/UDP` sur la machine qui heberge.

## Controles

### Menus

- `Clic gauche` : selectionner
- `1` a `5` : choisir une classe
- `Echap` : retour ou fermeture selon l'ecran

### En partie

- `ZQSD` ou `WASD` : se deplacer
- `Clic gauche` : attaque principale
- `Clic droit` : attaque alternative, uniquement pour les armes hybrides
- `Espace` : dash
- `F` : competence de classe
- `E` : ouvrir un coffre ou activer un portail
- `1` a `9` : changer d'arme
- `Echap` : retour au menu

### Apres une defaite

- `R` : rejouer
- `M` : revenir au menu principal

## Classes

- `Tank` : 150 PV, plus lent, competence defensive qui reduit les degats recus
- `Berserker` : 80 PV, plus rapide, competence de rage qui augmente fortement les degats
- `Vampire` : stats equilibrees, competence orientee survie
- `Ninja` : plus mobile, dash plus frequent, teleportation au curseur
- `Mage` : plus de stamina, meilleure regeneration, nova de projectiles

## Tutoriel rapide

### 1. Debut de partie

- Choisissez une classe adaptee a votre style de jeu
- Deplacez-vous constamment : rester immobile est souvent fatal
- Surveillez la vie et surtout la stamina, car dash et attaques en dependent

### 2. Pendant les vagues

- Eliminez les ennemis a distance en priorite si la salle devient chargee
- Utilisez le dash pour traverser une zone dangereuse ou sortir d'un encerclement
- Gardez la competence `F` pour un moment utile, pas des que le cooldown est termine

### 3. Coffres et nouvelles armes

- Ouvrez les coffres avec `E`
- Changez d'arme avec les touches numeriques
- Testez les armes de chaque epoque : elles ne jouent pas toutes de la meme facon

### 4. Portails et progression

- Quand une vague est nettoyee, cherchez le portail
- Activez-le avec `E` pour passer a la salle suivante
- Chaque epoque augmente la pression et change votre arsenal disponible

## Focus sur la Grece Antique

La salle de Grece Antique donne acces a trois armes : l'arc, le crane et la lance.

### Bien utiliser la lance

La `lance` est une arme hybride. C'est le point important de cette periode :

- `Clic gauche` : coup de melee
- `Clic droit` : lancer de la lance a distance

En pratique :

- utilisez le `clic gauche` quand un ennemi est proche ou quand vous voulez un gros impact au corps a corps
- utilisez le `clic droit` pour toucher avant le contact, finir un ennemi qui recule, ou ouvrir un passage
- les deux modes consomment de la stamina, donc evitez de spammer lance + dash sans regarder votre reserve

Conseil simple : en Grece Antique, la lance est souvent l'arme la plus polyvalente. Ouvrez un engagement au `clic droit`, puis finissez au `clic gauche` si l'ennemi arrive au contact.

## Structure utile du projet

```text
Mobius_EPITA/
├── README.md
└── mobius/
    ├── main.py
    ├── assets/
    ├── sons/
    ├── core/
    └── epoques/
```

## Etat du projet

Le projet est jouable, mais reste un prototype de jeu realise dans un cadre pedagogique. Il peut donc encore contenir des bugs, des equilibrages incomplets ou des elements de presentation temporaires.

## Auteurs

Projet developpe par M3G_STUDIO dans le cadre du projet S2 d'EPITA.
