#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAME_ROOT="$PROJECT_ROOT/mobius"
BUILD_VENV="$PROJECT_ROOT/.build-venv"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build"
OUTPUT_DIR="$PROJECT_ROOT/build-output"
EXECUTABLE_NAME="Mobius"

if [[ ! -f "$GAME_ROOT/main.py" ]]; then
    echo "Erreur: point d'entree introuvable: $GAME_ROOT/main.py" >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Erreur: python3 est requis pour compiler le jeu." >&2
    exit 1
fi

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    DATA_SEP=";"
else
    DATA_SEP=":"
fi

echo "==> Preparation de l'environnement de build"
python3 -m venv "$BUILD_VENV"
# shellcheck disable=SC1091
source "$BUILD_VENV/bin/activate"

echo "==> Installation des dependances de build"
python -m pip install --upgrade pip setuptools wheel
python -m pip install pyinstaller pygame pillow typing_extensions

echo "==> Nettoyage des anciens artefacts"
rm -rf "$BUILD_DIR" "$DIST_DIR" "$OUTPUT_DIR"

echo "==> Compilation de l'executable"
pyinstaller \
    --noconfirm \
    --clean \
    --onefile \
    --name "$EXECUTABLE_NAME" \
    --paths "$GAME_ROOT" \
    --add-data "$GAME_ROOT/assets${DATA_SEP}assets" \
    --add-data "$GAME_ROOT/sons${DATA_SEP}sons" \
    --hidden-import PIL \
    --hidden-import PIL.Image \
    --hidden-import PIL.ImageChops \
    --hidden-import PIL.ImageSequence \
    --hidden-import typing_extensions \
    "$GAME_ROOT/main.py"

mkdir -p "$OUTPUT_DIR"
cp "$DIST_DIR/$EXECUTABLE_NAME" "$OUTPUT_DIR/$EXECUTABLE_NAME"
chmod +x "$OUTPUT_DIR/$EXECUTABLE_NAME"

cat <<EOF

Build terminee.
Executable : $OUTPUT_DIR/$EXECUTABLE_NAME

Lancement :
  $OUTPUT_DIR/$EXECUTABLE_NAME
EOF
