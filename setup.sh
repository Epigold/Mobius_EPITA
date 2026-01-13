#!/bin/bash

# Script de setup pour installer Python 3 et Pygame
# Compatible avec Linux (Ubuntu/Debian, CentOS/RHEL/Fedora)
# Pour Windows, exécutez ce script dans WSL, Git Bash, ou adaptez-le

set -e  # Arrêter le script en cas d'erreur

echo "Détection du système d'exploitation..."
OS=$(uname -s)

if [ "$OS" = "Linux" ]; then
    echo "Système Linux détecté."
    # Détection du gestionnaire de paquets
    if command -v apt >/dev/null 2>&1; then
        echo "Utilisation d'apt (Ubuntu/Debian)."
        sudo apt update || echo "Warning: apt update encountered errors, but continuing..."
        sudo apt install -y python3 python3-pip python3-venv
    elif command -v yum >/dev/null 2>&1; then
        echo "Utilisation de yum (CentOS/RHEL)."
        sudo yum install -y python3 python3-pip
    elif command -v dnf >/dev/null 2>&1; then
        echo "Utilisation de dnf (Fedora)."
        sudo dnf install -y python3 python3-pip
    elif command -v pacman >/dev/null 2>&1; then
        echo "Utilisation de pacman (Arch Linux)."
        sudo pacman -S --noconfirm python python-pip
    else
        echo "Gestionnaire de paquets non reconnu. Veuillez installer Python 3 manuellement."
        exit 1
    fi

elif [ "$OS" = "Darwin" ]; then
    echo "Système macOS détecté."
    # Pour macOS, utiliser Homebrew si disponible
    if command -v brew >/dev/null 2>&1; then
        brew install python3
    else
        echo "Homebrew non trouvé. Veuillez installer Python 3 via https://www.python.org/"
        exit 1
    fi

elif [ "$OS" = "MINGW64_NT" ] || [ "$OS" = "MSYS_NT" ]; then
    echo "Système Windows détecté (via Git Bash ou similaire)."
    echo "Pour Windows, veuillez installer Python 3 manuellement depuis https://www.python.org/"
    echo "Ou utiliser Chocolatey : choco install python3"
    echo "Ou Winget : winget install Python.Python.3"
    exit 1

else
    echo "Système d'exploitation non supporté : $OS"
    echo "Veuillez installer Python 3 manuellement."
    exit 1
fi

# Vérifier l'installation de Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "Erreur : Python 3 n'a pas pu être installé."
    exit 1
fi

echo "Python 3 installé avec succès."
python3 --version

# Installer pip si pas présent
if ! command -v pip3 >/dev/null 2>&1; then
    echo "Installation de pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3
fi

echo "Mise à jour de pip..."
pip3 install --upgrade pip

# Installer Pygame
echo "Installation de Pygame..."
pip3 install pygame

# Vérifier l'installation
if python3 -c "import pygame; print('Pygame version:', pygame.version.ver)" >/dev/null 2>&1; then
    echo "Pygame installé avec succès."
    python3 -c "import pygame; print('Pygame version:', pygame.version.ver)"
else
    echo "Erreur lors de l'installation de Pygame."
    exit 1
fi

# Créer un environnement virtuel
echo "Création d'un environnement virtuel..."
python3 -m venv venv

# Activer l'environnement virtuel et installer Pygame dedans
echo "Activation du venv et installation de Pygame dans l'environnement virtuel..."
source venv/bin/activate
pip install --upgrade pip
pip install pygame

# Vérifier dans le venv
if python -c "import pygame; print('Pygame dans venv:', pygame.version.ver)" >/dev/null 2>&1; then
    echo "Pygame installé dans le venv avec succès."
else
    echo "Erreur lors de l'installation de Pygame dans le venv."
    exit 1
fi

# Créer un script de lancement
echo "Création du script de lancement run.sh..."
cat > run.sh << 'EOF'
#!/bin/bash
# Script pour lancer le jeu dans l'environnement virtuel

# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le jeu
python3 prototype.py
EOF

# Rendre run.sh exécutable
chmod +x run.sh

echo ""
echo "Installation terminée !"
echo "Pour lancer le jeu, utilisez : ./run.sh"
echo "Cela activera automatiquement l'environnement virtuel et lancera prototype.py"