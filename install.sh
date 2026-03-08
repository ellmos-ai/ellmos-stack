#!/bin/bash
# ellmos-stack Installer
# Tested on: Ubuntu 22.04+, Debian 12+
# Usage: ./install.sh [--install-dir /opt/ellmos-stack]
set -euo pipefail

# === Configuration ===
INSTALL_DIR="${1:-/opt/ellmos-stack}"
VENV_DIR="$INSTALL_DIR/venv"
DATA_DIR="$INSTALL_DIR/data"

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

if ! command -v docker compose &> /dev/null; then
    echo "[ERROR] Docker Compose not found (docker compose v2 required)"
    exit 1
fi

# === System dependencies ===
echo "[1/7] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl > /dev/null

# === Directory structure ===
echo "[2/7] Creating directories..."
mkdir -p "$INSTALL_DIR"/{config,services,data}
mkdir -p "$DATA_DIR"/{knowledgedigest/{inbox,archive},rinnsal}

# === Copy files ===
echo "[3/7] Copying stack files..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/docker-compose.yml" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/config/"* "$INSTALL_DIR/config/"
cp "$SCRIPT_DIR/services/"* "$INSTALL_DIR/services/"
chmod +x "$INSTALL_DIR/services/"*.py

# === .env ===
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/.env"
    # Generate random n8n password
    N8N_PW=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
    sed -i "s/CHANGE_ME_TO_A_SECURE_PASSWORD/$N8N_PW/" "$INSTALL_DIR/.env"
    echo "[INFO] Generated n8n password: $N8N_PW"
    echo "[INFO] Saved in $INSTALL_DIR/.env -- keep this safe!"
else
    echo "[INFO] .env already exists, keeping it"
fi

# === Python venv ===
echo "[4/7] Setting up Python environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip

# Install components
echo "  Installing Rinnsal..."
"$VENV_DIR/bin/pip" install --quiet rinnsal 2>/dev/null || \
    "$VENV_DIR/bin/pip" install --quiet git+https://github.com/ellmos-ai/rinnsal.git

echo "  Installing KnowledgeDigest..."
"$VENV_DIR/bin/pip" install --quiet knowledgedigest 2>/dev/null || \
    "$VENV_DIR/bin/pip" install --quiet git+https://github.com/file-bricks/knowledgedigest.git

echo "  Installing ResearchAgent..."
"$VENV_DIR/bin/pip" install --quiet research-agent 2>/dev/null || \
    "$VENV_DIR/bin/pip" install --quiet git+https://github.com/research-line/research-agent.git 2>/dev/null || \
    echo "  [WARN] ResearchAgent not available -- research pipeline will work without it"

# === Docker services ===
echo "[5/7] Starting Docker services..."
cd "$INSTALL_DIR"
docker compose up -d

# Wait for Ollama to be ready
echo "  Waiting for Ollama..."
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Pull the configured model
source "$INSTALL_DIR/.env"
MODEL="${OLLAMA_MODEL:-qwen3:4b}"
echo "  Pulling model: $MODEL (this may take a few minutes)..."
docker exec ollama ollama pull "$MODEL"

# === KnowledgeDigest Web Viewer ===
echo "[6/7] Starting KnowledgeDigest web viewer..."
KD_PORT=$(grep KD_PORT "$INSTALL_DIR/.env" 2>/dev/null | cut -d= -f2 || echo 8787)
KD_PORT="${KD_PORT:-8787}"

cat > /etc/systemd/system/knowledgedigest.service << EOF
[Unit]
Description=KnowledgeDigest Web Viewer
After=network.target docker.service

[Service]
Type=simple
Environment=PYTHONIOENCODING=utf-8
WorkingDirectory=$DATA_DIR/knowledgedigest
ExecStart=$VENV_DIR/bin/python -m knowledgedigest.web_viewer --db $DATA_DIR/knowledgedigest/knowledge.db --port $KD_PORT --host 0.0.0.0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now knowledgedigest

# === Cron jobs ===
echo "[7/7] Installing cron jobs..."
cat > /etc/cron.d/ellmos-stack << EOF
SHELL=/bin/bash
PYTHONIOENCODING=utf-8

# Index new documents from inbox/ every 5 minutes
*/5 * * * * root cd $DATA_DIR/knowledgedigest && $VENV_DIR/bin/python $INSTALL_DIR/services/auto_ingest.py >> /var/log/ellmos-stack-ingest.log 2>&1

# Process 1 summary queue item every 15 minutes via Ollama
*/15 * * * * root cd $DATA_DIR/knowledgedigest && $VENV_DIR/bin/python $INSTALL_DIR/services/process_summaries.py >> /var/log/ellmos-stack-summaries.log 2>&1
EOF

# === Done ===
echo ""
echo "============================================="
echo "  ellmos-stack installed successfully!"
echo "============================================="
echo ""
echo "Services:"
echo "  n8n:              http://$(hostname -I | awk '{print $1}'):5678"
echo "  KnowledgeDigest:  http://$(hostname -I | awk '{print $1}'):$KD_PORT"
echo "  Ollama:           http://localhost:11434 (local only)"
echo ""
echo "Credentials:"
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
