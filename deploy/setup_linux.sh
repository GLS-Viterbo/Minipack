#!/bin/bash
# =============================================================================
# Script di installazione Minipack su server Linux
#
# PREREQUISITI sul server:
#   sudo apt install python3 python3-pip python3-venv nodejs npm git
#
# USO:
#   1. Copia la repo sul server:
#      git clone <url-repo> /opt/minipack-src
#      oppure: scp -r ./Minipack user@server:/opt/minipack-src
#
#   2. Esegui questo script dalla cartella della repo:
#      cd /opt/minipack-src
#      sudo bash deploy/setup_linux.sh
# =============================================================================

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"  # cartella root della repo
INSTALL_DIR="/opt/minipack"
APP_USER="minipack"
BACKEND_PORT=10001

echo "=== Setup Minipack Torre ==="
echo "Repo sorgente: $REPO_DIR"
echo "Installazione in: $INSTALL_DIR"
echo ""

# 1. Installa dipendenze di sistema (Ubuntu/Debian)
echo "[1/6] Verifico dipendenze di sistema..."
which python3 || { echo "ERRORE: python3 non trovato. Esegui: sudo apt install python3 python3-venv"; exit 1; }
which node   || { echo "ERRORE: nodejs non trovato. Esegui: sudo apt install nodejs npm"; exit 1; }

# 2. Crea utente di sistema dedicato
echo "[2/6] Creo utente sistema '$APP_USER'..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /bin/false "$APP_USER"
fi

# 3. Build del frontend
echo "[3/6] Compilazione frontend React..."
cd "$REPO_DIR/frontend"
npm install
npm run build
echo "Frontend compilato in: $REPO_DIR/frontend/dist"

# 4. Prepara cartella installazione
echo "[4/6] Copio i file..."
mkdir -p "$INSTALL_DIR"
cp -r "$REPO_DIR/backend/." "$INSTALL_DIR/"
cp -r "$REPO_DIR/frontend/dist" "$INSTALL_DIR/frontend_dist"

# 5. Virtual environment Python
echo "[5/6] Installo dipendenze Python..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

# Permessi
chown -R "$APP_USER:$APP_USER" "$INSTALL_DIR"
chmod 770 "$INSTALL_DIR"
# Il db SQLite deve essere scrivibile dall'utente minipack
[ -f "$INSTALL_DIR/minipack_monitoring.db" ] && chmod 660 "$INSTALL_DIR/minipack_monitoring.db"

# 6. Installa service systemd
echo "[6/6] Installo servizio systemd..."
cp "$REPO_DIR/deploy/minipack.service" /etc/systemd/system/minipack.service
systemctl daemon-reload

echo ""
echo "======================================"
echo " Installazione completata!"
echo "======================================"
echo ""
echo "Comandi utili:"
echo "  Avvia ora:          sudo systemctl start minipack"
echo "  Ferma:              sudo systemctl stop minipack"
echo "  Log in tempo reale: sudo journalctl -u minipack -f"
echo "  Stato:              sudo systemctl status minipack"
echo ""
echo "Per avvio automatico mattutino (es. 06:30 lun-ven):"
echo "  sudo crontab -e"
echo "  Aggiungi: 30 6 * * 1-5 /bin/systemctl start minipack"
echo ""
echo "Dashboard disponibile su: http://$(hostname -I | awk '{print $1}'):$BACKEND_PORT"
