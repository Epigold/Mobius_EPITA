# Mobius_EPITA

Jeu vidéo roguelike nommé Mobius pour le projet S2 EPITA.

## Description

Mobius est un jeu roguelike en 2D où le joueur incarne un héros combattant des vagues d'ennemis de plus en plus difficiles. Le jeu propose un système de classes avec des compétences uniques, une progression par vagues avec des boss, et un système d'inventaire pour collecter des armes et des power-ups.

## Fonctionnalités

- **Système de classes** : 5 classes disponibles (Tank, Berserker, Vampire, Ninja, Mage)
- **Combat dynamique** : Attaques à distance et au corps à corps
- **Vagues d'ennemis** : Ennemis variés (Tank, Rusher, Sniper) et boss tous les 3 vagues
- **Système d'armes** : Collecte et changement d'armes (caillou, os)
- **Power-ups** : Améliorations temporaires (dégâts, vitesse, santé, stamina)
- **Économie** : Collecte de pièces pour... (à développer)
- **Interface utilisateur** : Barres de vie, stamina, statistiques en temps réel

## Classes disponibles

### Tank
- **Santé** : 150 PV
- **Vitesse** : Réduite de 30%
- **Compétence spéciale** : Bouclier (réduit les dégâts de 50% pendant 5 secondes)

### Berserker
- **Santé** : 80 PV
- **Vitesse** : Augmentée de 30%
- **Compétence spéciale** : Rage (dégâts x2 pendant 5 secondes)

### Vampire
- **Stats** : Normales
- **Compétence spéciale** : Vol de vie (récupère 20% des dégâts infligés pendant 10 secondes)

### Ninja
- **Vitesse** : Augmentée de 15%
- **Dash** : Cooldown réduit de moitié
- **Compétence spéciale** : Téléportation vers la position de la souris

### Mage
- **Stamina** : 150
- **Régénération** : Augmentée de 50%
- **Compétence spéciale** : Nova de projectiles (tir circulaire de 12 projectiles)

## Installation

### Prérequis
- Python 3.x
- Pygame

### Installation des dépendances
```bash
pip install pygame
```

### Lancement du jeu
```bash
python prototype.py
```

## Contrôles

### Menu
- **1-5** : Sélectionner une classe
- **Clic gauche** : Sélectionner une classe

### En jeu
- **Z/Q/S/D** ou **W/A/S/D** : Déplacement
- **Clic gauche** : Attaquer
- **Espace** : Dash (consomme de la stamina)
- **F** : Utiliser la compétence spéciale
- **1/2** : Changer d'arme (si disponible)
- **E** : Ouvrir un coffre
- **Échap** : Retour au menu

### Game Over
- **R** : Rejouer
- **M** : Retour au menu

## Structure du projet

- `prototype.py` : Code principal du jeu
- `assets/` : Ressources graphiques (personnages, ennemis, etc.)
- `document_avancement/` : Documents de progression du projet
  - `Site/` : Site web de présentation avec lore, graphismes, etc.
  - `Grille evaluation EPITA ATEXE ATEXO.pdf` : Grille d'évaluation
- `Presentation/` : Présentations du projet

## État du développement

Ce projet est un prototype développé dans le cadre du projet S2 EPITA. Il inclut les mécaniques de base du jeu mais peut contenir des bugs ou des fonctionnalités incomplètes.

## Auteurs

Développé par l'équipe M3G_STUDIO de l'EPITA pour le projet S2.
