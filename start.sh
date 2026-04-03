#!/bin/bash
# Avvia backend e frontend di Minipack.
# Uso: ./start.sh [--stop]
#
# Cron (avvio ogni giorno alle 06:00):
#   0 6 * * 1-5 /path/to/Minipack/start.sh >> /path/to/Minipack/logs/cron.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Carica configurazione porte da .env (se presente)
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    # shellcheck source=.env
    source "$SCRIPT_DIR/.env"
    set +a
fi

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

PID_BACKEND="$SCRIPT_DIR/logs/backend.pid"
PID_FRONTEND="$SCRIPT_DIR/logs/frontend.pid"
LOG_BACKEND="$SCRIPT_DIR/logs/backend.log"
LOG_FRONTEND="$SCRIPT_DIR/logs/frontend.log"

mkdir -p "$SCRIPT_DIR/logs"

# ── Funzione stop ────────────────────────────────────────────────────────────

stop_service() {
    local name="$1"
    local pidfile="$2"
    if [ -f "$pidfile" ]; then
        local pid
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo "[$(date '+%H:%M:%S')] Arresto $name (PID $pid)..."
            kill "$pid"
        fi
        rm -f "$pidfile"
    fi
}

if [ "${1:-}" = "--stop" ]; then
    stop_service "backend"  "$PID_BACKEND"
    stop_service "frontend" "$PID_FRONTEND"
    echo "[$(date '+%H:%M:%S')] Servizi arrestati."
    exit 0
fi

# ── Evita avvii duplicati ────────────────────────────────────────────────────

is_running() {
    local pidfile="$1"
    [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null
}

# ── Backend ──────────────────────────────────────────────────────────────────

if is_running "$PID_BACKEND"; then
    echo "[$(date '+%H:%M:%S')] Backend già in esecuzione (PID $(cat "$PID_BACKEND")), skip."
else
    echo "[$(date '+%H:%M:%S')] Avvio backend su porta $BACKEND_PORT..."
    cd "$SCRIPT_DIR/backend"
    BACKEND_PORT="$BACKEND_PORT" \
        python -m uvicorn app:app \
            --host 0.0.0.0 \
            --port "$BACKEND_PORT" \
            >> "$LOG_BACKEND" 2>&1 &
    echo $! > "$PID_BACKEND"
    echo "[$(date '+%H:%M:%S')] Backend avviato (PID $(cat "$PID_BACKEND"))."
fi

# ── Frontend ─────────────────────────────────────────────────────────────────

if is_running "$PID_FRONTEND"; then
    echo "[$(date '+%H:%M:%S')] Frontend già in esecuzione (PID $(cat "$PID_FRONTEND")), skip."
else
    echo "[$(date '+%H:%M:%S')] Avvio frontend su porta $FRONTEND_PORT..."
    cd "$SCRIPT_DIR/frontend"
    BACKEND_PORT="$BACKEND_PORT" \
        npm run dev -- --port "$FRONTEND_PORT" \
            >> "$LOG_FRONTEND" 2>&1 &
    echo $! > "$PID_FRONTEND"
    echo "[$(date '+%H:%M:%S')] Frontend avviato (PID $(cat "$PID_FRONTEND"))."
fi

echo "[$(date '+%H:%M:%S')] Minipack attivo — backend :$BACKEND_PORT  frontend :$FRONTEND_PORT"
