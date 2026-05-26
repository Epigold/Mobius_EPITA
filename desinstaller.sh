#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$PROJECT_ROOT")"

echo "Ce script va supprimer completement le dossier du projet :"
echo "  $PROJECT_ROOT"
echo
echo "Cela inclut le code source, les assets, les executables compiles et les environnements virtuels."
echo
read -r -p "Tapez SUPPRIMER pour confirmer : " CONFIRM

if [[ "$CONFIRM" != "SUPPRIMER" ]]; then
    echo "Desinstallation annulee."
    exit 0
fi

TMP_SCRIPT="$(mktemp)"
cat >"$TMP_SCRIPT" <<EOF
#!/usr/bin/env bash
sleep 1
rm -rf "$PROJECT_ROOT"
rmdir "$PARENT_DIR" 2>/dev/null || true
EOF

chmod +x "$TMP_SCRIPT"
nohup "$TMP_SCRIPT" >/dev/null 2>&1 &

echo "Desinstallation lancee."
echo "Le dossier sera supprime : $PROJECT_ROOT"
