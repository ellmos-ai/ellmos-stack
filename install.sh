#!/bin/bash
# ellmos-stack Installer
# Tested on: Ubuntu 22.04+, Debian 12+
# Usage: ./install.sh [--prepare-only] [INSTALL_DIR]   (default: /opt/ellmos-stack)
set -euo pipefail

# === Configuration ===
PREPARE_ONLY=false
INSTALL_DIR=""
for arg in "$@"; do
    case "$arg" in
        --prepare-only) PREPARE_ONLY=true ;;
        -*) echo "[ERROR] Unknown option: $arg" >&2; exit 2 ;;
        *)
            if [ -n "$INSTALL_DIR" ]; then
                echo "[ERROR] Specify at most one INSTALL_DIR" >&2
                exit 2
            fi
            INSTALL_DIR="$arg"
            ;;
    esac
done
INSTALL_DIR="${INSTALL_DIR:-/opt/ellmos-stack}"
if [[ ! "$INSTALL_DIR" =~ ^/[A-Za-z0-9._/-]+$ ]]; then
    echo "[ERROR] INSTALL_DIR must be an absolute path using only letters, digits, ., _, -, and /" >&2
    exit 2
fi
VENV_DIR="$INSTALL_DIR/venv"
DATA_DIR="$INSTALL_DIR/data"
STACK_USER="ellmos-stack"
RINNSAL_COMMIT="2ac63310ddf74afbcdae170967effa95be5ca9e0"
KNOWLEDGEDIGEST_COMMIT="176e304ab64c55cbe02fdb998e663bc7e64ebf74"

echo "============================================="
echo "  ellmos-stack Installer"
echo "============================================="
echo "Install directory: $INSTALL_DIR"
echo ""

# === Pre-checks ===
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] Please run as root (sudo ./install.sh)"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker not found. Install Docker first:"
    echo "  curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Detect Docker Compose: v2 plugin ("docker compose") or v1 binary ("docker-compose")
if docker compose version > /dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    echo "[ERROR] Docker Compose not found. Install the Compose v2 plugin:"
    echo "  apt-get install docker-compose-plugin"
    exit 1
fi

# === System dependencies ===
echo "[1/7] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl > /dev/null

# === Directory structure ===
echo "[2/7] Creating directories..."
if ! id -u "$STACK_USER" > /dev/null 2>&1; then
    useradd --system --home-dir "$DATA_DIR" --shell /usr/sbin/nologin "$STACK_USER"
fi
mkdir -p "$INSTALL_DIR"/{config,services,data}
mkdir -p "$DATA_DIR"/{knowledgedigest/{inbox,archive},rinnsal,logs}
chown -R "$STACK_USER:$STACK_USER" "$DATA_DIR"

# === Copy files ===
echo "[3/7] Copying stack files..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/docker-compose.yml" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/config/"* "$INSTALL_DIR/config/"
cp "$SCRIPT_DIR/services/"*.py "$INSTALL_DIR/services/"
chmod +x "$INSTALL_DIR/services/"*.py
sed -i "s|/opt/ellmos-stack|$INSTALL_DIR|g" \
    "$INSTALL_DIR/config/telegram-gateway.service"

# === .env ===
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/.env"
    echo "[INFO] Created $INSTALL_DIR/.env from .env.example -- review the settings"
else
    echo "[INFO] .env already exists, keeping it"
fi
chmod 600 "$INSTALL_DIR/.env"
chown "$STACK_USER:$STACK_USER" "$INSTALL_DIR/.env"

# === Python venv ===
echo "[4/7] Setting up Python environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip --version > /dev/null

# Install components
echo "  Installing Rinnsal..."
"$VENV_DIR/bin/pip" install --quiet \
    "git+https://github.com/ellmos-ai/rinnsal.git@$RINNSAL_COMMIT"

echo "  Installing KnowledgeDigest..."
"$VENV_DIR/bin/pip" install --quiet \
    "git+https://github.com/file-bricks/knowledgedigest.git@$KNOWLEDGEDIGEST_COMMIT"

# === Docker services ===
if [ "$PREPARE_ONLY" = true ]; then
    echo "[5/7] Prepare-only: Docker services and model pull skipped"
else
    echo "[5/7] Starting Docker services..."
    cd "$INSTALL_DIR"
    $COMPOSE up -d

    # Wait for Ollama to be ready
    echo "  Waiting for Ollama..."
    OLLAMA_READY=false
    for i in $(seq 1 30); do
        if curl --fail --silent --show-error http://localhost:11434/api/version > /dev/null 2>&1; then
            OLLAMA_READY=true
            break
        fi
        sleep 2
    done
    if [ "$OLLAMA_READY" != true ]; then
        echo "[ERROR] Ollama did not become ready within 60 seconds"
        $COMPOSE logs --no-color --tail=100 ollama || true
        exit 1
    fi

    # Pull the configured model
    MODEL=$(grep -E '^OLLAMA_MODEL=' "$INSTALL_DIR/.env" 2>/dev/null | tail -n 1 | cut -d= -f2- || true)
    MODEL="${MODEL%$'\r'}"
    MODEL="${MODEL:-qwen3:4b}"
    echo "  Pulling model: $MODEL (this may take a few minutes)..."
    docker exec ollama ollama pull "$MODEL"
fi

# === KnowledgeDigest Web Viewer ===
echo "[6/7] Starting KnowledgeDigest web viewer..."
KD_PORT=$(grep -E '^KD_PORT=' "$INSTALL_DIR/.env" 2>/dev/null | tail -n 1 | cut -d= -f2- || echo 8787)
KD_PORT="${KD_PORT:-8787}"

cat > /etc/systemd/system/knowledgedigest.service << EOF
[Unit]
Description=KnowledgeDigest Web Viewer
After=network.target docker.service

[Service]
Type=simple
User=$STACK_USER
Group=$STACK_USER
Environment=PYTHONIOENCODING=utf-8
Environment=PYTHONDONTWRITEBYTECODE=1
WorkingDirectory=$DATA_DIR/knowledgedigest
ExecStart=$VENV_DIR/bin/python -m KnowledgeDigest --web --db $DATA_DIR/knowledgedigest/knowledge.db --port $KD_PORT --no-browser
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=$DATA_DIR
UMask=0077

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
if [ "$PREPARE_ONLY" = true ]; then
    systemctl enable knowledgedigest
else
    systemctl enable --now knowledgedigest
fi

# === Cron jobs ===
echo "[7/7] Installing cron jobs..."
CRON_FILE=/etc/cron.d/ellmos-stack
if [ "$PREPARE_ONLY" = true ]; then
    if [ -f "$CRON_FILE" ]; then
        mv "$CRON_FILE" "$CRON_FILE.disabled"
    fi
    CRON_FILE="$CRON_FILE.disabled"
fi
cat > "$CRON_FILE" << EOF
SHELL=/bin/bash
PYTHONIOENCODING=utf-8
PYTHONDONTWRITEBYTECODE=1

# Index new documents from inbox/ every 5 minutes
*/5 * * * * $STACK_USER umask 077; cd $DATA_DIR/knowledgedigest && $VENV_DIR/bin/python $INSTALL_DIR/services/auto_ingest.py >> $DATA_DIR/logs/ingest.log 2>&1

# Process 1 summary queue item every 15 minutes via Ollama
# The service script loads literal values from $INSTALL_DIR/.env without shell evaluation
*/15 * * * * $STACK_USER umask 077; cd $DATA_DIR/knowledgedigest && $VENV_DIR/bin/python $INSTALL_DIR/services/process_summaries.py >> $DATA_DIR/logs/summaries.log 2>&1
EOF

# === Done ===
echo ""
echo "============================================="
if [ "$PREPARE_ONLY" = true ]; then
    echo "  ellmos-stack prepared; services remain stopped for restore"
else
    echo "  ellmos-stack installed successfully!"
fi
echo "============================================="
echo ""
echo "Services:"
echo "  n8n:              http://127.0.0.1:5678 (localhost only)"
echo "  KnowledgeDigest:  http://127.0.0.1:$KD_PORT (localhost only)"
echo "  Ollama:           http://localhost:11434 (local only)"
echo "  SSH tunnel:       ssh -L 5678:127.0.0.1:5678 -L $KD_PORT:127.0.0.1:$KD_PORT root@your-server"
echo ""
echo "IMPORTANT: Open n8n via the SSH tunnel and create the owner account"
echo "           BEFORE exposing the port publicly (n8n >= 1.0 has no Basic Auth;"
echo "           the first visitor becomes the owner)."
echo ""
echo "Configuration:"
echo "  Stored in: $INSTALL_DIR/.env"
echo ""
echo "Data directories:"
echo "  KnowledgeDigest:  $DATA_DIR/knowledgedigest/"
echo "  Document inbox:   $DATA_DIR/knowledgedigest/inbox/"
echo "  Rinnsal:          $DATA_DIR/rinnsal/"
echo ""
echo "Next steps:"
echo "  1. Open n8n and set up your first workflow"
echo "  2. Drop documents into $DATA_DIR/knowledgedigest/inbox/"
echo "  3. Try: $VENV_DIR/bin/python $INSTALL_DIR/services/research_pipeline.py \"your topic\" --summarize --save"
echo ""
