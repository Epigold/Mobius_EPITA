# **🎮 Mobius_EPITA**

Jeu vidéo roguelike développé dans le cadre du **projet S2 – EPITA**.

---

## **📋 Description**

**Mobius** est un jeu roguelike en 2D dans lequel le joueur incarne un héros affrontant des vagues d’ennemis de plus en plus difficiles.
Le jeu propose un **système de classes** avec des compétences uniques, une **progression par vagues** incluant des boss réguliers, ainsi qu’un **système d’inventaire** permettant de collecter des armes et des power-ups.

---

## **✨ Fonctionnalités**

* **Système de classes** : 5 classes jouables (Tank, Berserker, Vampire, Ninja, Mage)
* **Combat dynamique** : attaques à distance et au corps à corps
* **Vagues d’ennemis** : ennemis variés (Tank, Rusher, Sniper)
* **Boss** : apparition d’un boss toutes les 3 vagues
* **Système d’armes** : collecte et changement d’armes (caillou, os)
* **Power-ups** : améliorations temporaires (dégâts, vitesse, santé, stamina)
* **Économie** : collecte de pièces pour de futurs échanges avec des PNJ
* **Interface utilisateur** : affichage de la vie, stamina et statistiques en temps réel

---

## **🎮 Classes disponibles**

### **🛡️ Tank**

* **Santé** : 150 PV
* **Vitesse** : −30 %
* **Compétence spéciale** : Bouclier (réduction des dégâts de 50 % pendant 5 secondes)

### **⚔️ Berserker**

* **Santé** : 80 PV
  -- **Vitesse** : +30 %
* **Compétence spéciale** : Rage (dégâts x2 pendant 5 secondes)

### **🧛 Vampire**

* **Stats** : normales
* **Compétence spéciale** : Vol de vie (récupère 20 % des dégâts infligés pendant 10 secondes)

### **👤 Ninja**

* **Vitesse** : +15 %
* **Dash** : cooldown réduit de moitié
* **Compétence spéciale** : Téléportation vers la position de la souris

### **🧙 Mage**

* **Stamina** : 150
* **Régénération** : +50 %
* **Compétence spéciale** : Nova de projectiles (tir circulaire de 12 projectiles)

---

## **🚀 Installation (Cross-platform)**

### **📦 Prérequis**

* **Git**
* **Python 3.9 ou supérieur**
* Un terminal (Bash, Zsh, PowerShell, Git Bash)

---

## **🐧 Linux (Ubuntu / Debian / Fedora / Arch)**

### **1️⃣ Installation des prérequis**

```bash
sudo apt update
sudo apt install git
```

### **2️⃣ Cloner le projet**

```bash
git clone https://github.com/Epigold/Mobius_EPITA.git
cd Mobius_EPITA
```

### **3️⃣ Lancer le script de setup**

```bash
chmod +x setup.sh
./setup.sh
```

👉 Ce script :

* installe **Python 3** et **pip** si nécessaire
* crée un **environnement virtuel (`venv`)**
* installe **Pygame** dans le venv
* génère un script de lancement `run.sh`

### **4️⃣ Lancer le jeu**

```bash
./run.sh
```

---

## **🍎 macOS**

### **1️⃣ Installer Homebrew (si nécessaire)**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### **2️⃣ Installer Git**

```bash
brew install git
```

### **3️⃣ Cloner le projet**

```bash
git clone https://github.com/Epigold/Mobius_EPITA.git
cd Mobius_EPITA
```

### **4️⃣ Lancer le setup**

```bash
chmod +x setup.sh
./setup.sh
```

### **5️⃣ Lancer le jeu**

```bash
./run.sh
```

---

## **🪟 Windows**

⚠️ **Le script `setup.sh` n’est pas nativement compatible Windows**

### **Solutions possibles**

* Utiliser **WSL (Windows Subsystem for Linux)** ✅ *(recommandé)*
* Utiliser **Git Bash**
* Installer Python et Pygame manuellement

### **Installation manuelle**

```powershell
winget install Python.Python.3
pip install pygame
```

Puis lancer le jeu :

```powershell
python prototype.py
```

---

## **🎯 Contrôles**

### **Menu principal**

* **1 – 5** : sélectionner une classe
* **Clic gauche** : sélectionner une classe

### **En jeu**

* **Z/Q/S/D** ou **W/A/S/D** : déplacement
* **Clic gauche** : attaquer
* **Espace** : dash (consomme de la stamina)
* **F** : compétence spéciale
* **1 / 2** : changer d’arme
* **E** : ouvrir un coffre
* **Échap** : retour au menu

### **Game Over**

* **R** : rejouer avec la même classe
* **M** : retour au menu principal

---

## **📁 Structure du projet**

```
Mobius_EPITA/
├── prototype.py      # Code principal du jeu
├── assets/           # Ressources graphiques
├── setup.sh          # Script de setup (Linux / macOS)
├── run.sh            # Script de lancement avec venv
├── venv/             # Environnement virtuel Python
└── README.md
```

---

## **🧪 État du développement**

Ce projet est un **prototype** développé dans le cadre du **projet S2 de l’EPITA**.
Il implémente les mécaniques principales du jeu mais peut contenir des bugs ou des fonctionnalités incomplètes.

---

## **👥 Auteurs**

Projet développé par **M3G_STUDIO**, étudiants à l’EPITA, dans le cadre du projet S2.

---

## **📄 Licence**

Projet développé dans un **cadre éducatif**.
**Tous droits réservés.**
