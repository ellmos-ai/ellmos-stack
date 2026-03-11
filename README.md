# ellmos-stack

A self-hosted AI research and knowledge management stack. Combines a local LLM, workflow automation, persistent memory, and a knowledge base into one deployable setup.

**Zero cloud dependencies.** Everything runs on your own server.

## What's inside

```
┌─────────────────────────────────────────────────────────┐
│                    ellmos-stack                          │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │
│  │  Ollama   │  │   n8n    │  │  Research Pipeline    │ │
│  │ Local LLM │  │ Workflow │  │ PubMed/arXiv → Ollama │ │
│  │ (qwen3)  │  │  Engine  │  │    → KnowledgeDigest  │ │
│  └────┬─────┘  └────┬─────┘  └───────────┬───────────┘ │
│       │              │                     │             │
│  ┌────┴──────────────┴─────────────────────┴──────────┐ │
│  │              Shared Services                        │ │
│  │  ┌─────────────────┐  ┌──────────────────────────┐ │ │
│  │  │    Rinnsal       │  │   KnowledgeDigest        │ │ │
│  │  │  Memory + Tasks  │  │  Document Search + Web   │ │ │
│  │  │  Ollama Runner   │  │  Auto-Indexing + Summary │ │ │
│  │  └─────────────────┘  └──────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

| Component | Role | Source |
|-----------|------|--------|
| **[Ollama](https://ollama.com)** | Local LLM inference (qwen3:4b default) | Docker |
| **[n8n](https://n8n.io)** | Workflow automation, webhooks, scheduling | Docker |
| **[Rinnsal](https://github.com/ellmos-ai/rinnsal)** | Lightweight memory + task management for AI agents | pip |
| **[KnowledgeDigest](https://github.com/file-bricks/knowledgedigest)** | Document ingestion, chunking, search, web UI | pip |
| **Research Pipeline** | Automated paper search → analysis → storage | included |

## Requirements

- **Server:** Linux (Ubuntu 22.04+, Debian 12+), 2+ CPU cores, 8+ GB RAM
- **Software:** Docker, Docker Compose v2, Python 3.10+
- **Disk:** ~5 GB for base setup (model + containers)

Tested on Hetzner CCX13 (2 vCPU, 8 GB RAM, ~18 EUR/month).

## Quickstart

```bash
# Clone
git clone https://github.com/ellmos-ai/ellmos-stack.git
cd ellmos-stack

# Install (as root)
sudo ./install.sh

# That's it. Services are running:
#   n8n:              http://your-ip:5678
#   KnowledgeDigest:  http://your-ip:8787
#   Ollama:           localhost:11434 (internal)
```

The installer:
1. Installs system dependencies (Python, Git, curl)
2. Sets up Docker services (Ollama + n8n)
3. Pulls the configured LLM model
4. Installs Python components (Rinnsal, KnowledgeDigest)
5. Creates systemd service for KnowledgeDigest web viewer
6. Sets up cron jobs for auto-indexing and background summarization
7. Generates a secure n8n password (saved in `.env`)

## Configuration

Copy and edit `.env`:

```bash
cp .env.example .env
nano .env
```

Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `N8N_PASSWORD` | *(generated)* | n8n web interface password |
| `OLLAMA_MODEL` | `qwen3:4b` | LLM model to use |
| `OLLAMA_MEMORY_LIMIT` | `6G` | Max RAM for Ollama |
| `KD_PORT` | `8787` | KnowledgeDigest web UI port |
| `KD_SUMMARY_PROVIDER` | `ollama` | Summary backend: `ollama`, `anthropic` |

## Use Cases

### 1. Knowledge Base

Drop documents (PDF, TXT, MD, DOCX) into the inbox directory:

```bash
cp paper.pdf /opt/ellmos-stack/data/knowledgedigest/inbox/
# Auto-indexed within 5 minutes, summaries generated within 15 minutes
```

Browse and search at `http://your-ip:8787`.

### 2. Research Automation

Search academic papers, analyze with your local LLM, store results:

```bash
cd /opt/ellmos-stack
venv/bin/python services/research_pipeline.py \
    "dark matter detection methods" \
    --papers 10 --summarize --save
```

### 3. AI Memory & Tasks

Persistent memory and task management for AI agents:

```python
from rinnsal import memory, tasks

memory.init("/opt/ellmos-stack/data/rinnsal/rinnsal.db")
memory.write("Server setup completed", tags=["infra"])

tasks.init("/opt/ellmos-stack/data/rinnsal/rinnsal.db")
tasks.add("Review research results", priority="high")
```

### 4. Workflow Automation (n8n)

Build automated workflows with n8n at `http://your-ip:5678`:

- **Scheduled research:** Cron → Research Pipeline → Email digest
- **Document processing:** Webhook → Download → KnowledgeDigest inbox
- **Monitoring:** Health checks → Alerts

### 5. Direct LLM Access

Query Ollama directly from any service:

```bash
curl http://localhost:11434/api/generate \
    -d '{"model":"qwen3:4b","prompt":"Explain quantum entanglement briefly"}'
```

Or via Rinnsal's OllamaRunner:

```python
from rinnsal.auto import OllamaRunner

runner = OllamaRunner(model="qwen3:4b", think=False)
result = runner.run("Summarize this text: ...")
```

### 6. Desktop Document Analysis (NoteSpaceLLM)

Use [NoteSpaceLLM](https://github.com/file-bricks/NoteSpaceLLM) as a desktop client for interactive document analysis, powered by the stack's Ollama instance:

1. Install NoteSpaceLLM on your local machine
2. Set up an Ollama auth proxy (see [Exposing Ollama](#exposing-ollama-for-remote-access) below)
3. In NoteSpaceLLM: Menu > LLM > Settings > set your server URL and API key

NoteSpaceLLM provides drag-and-drop document analysis, RAG-based chat, and multi-format report export -- all processed by the stack's LLM.

## Architecture

The stack uses **Docker** for Ollama and n8n (stateful services with volumes), and **pip packages** for the Python components (Rinnsal, KnowledgeDigest). Background processing runs via cron.

```
Port 5678  ──→ n8n (Docker)
Port 8787  ──→ KnowledgeDigest Web Viewer (systemd)
Port 11434 ──→ Ollama (Docker, localhost only)
Port 11435 ──→ Ollama Auth Proxy (Nginx, optional, for remote clients)

Cron:
  */5  min ──→ auto_ingest.py (index new documents)
  */15 min ──→ process_summaries.py (LLM summarization)
  */5  min ──→ ollama-service health (auto-restart if down)
```

Data is stored in `/opt/ellmos-stack/data/` (SQLite databases, document files).

## Customization

### Different LLM model

```bash
# Edit .env
OLLAMA_MODEL=mistral:7b

# Pull the new model
docker exec ollama ollama pull mistral:7b

# For NoteSpaceLLM RAG embeddings, also pull an embedding model:
docker exec ollama ollama pull nomic-embed-text

# Restart summary processing (uses OLLAMA_MODEL from .env)
```

### Cloud LLM for summaries

```bash
# In .env
KD_SUMMARY_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Custom system prompt

Edit `config/system_prompt.txt` to adjust the LLM's personality, language, and behavior.

## Exposing Ollama for Remote Access

By default, Ollama only listens on localhost. To allow desktop clients (like NoteSpaceLLM) or other machines to use your stack's LLM, set up an Nginx reverse proxy with API key authentication:

```bash
# Install Nginx
apt install nginx

# Create proxy config
cat > /etc/nginx/sites-available/ollama-proxy << 'EOF'
server {
    listen 11435;
    server_name _;

    location / {
        if ($http_authorization != "Bearer YOUR_SECRET_API_KEY") {
            return 401 "Unauthorized";
        }
        proxy_pass http://127.0.0.1:11434;
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }

    # Unauthenticated health endpoint
    location /health {
        proxy_pass http://127.0.0.1:11434/api/tags;
        proxy_read_timeout 5s;
    }
}
EOF

# Enable and start
ln -sf /etc/nginx/sites-available/ollama-proxy /etc/nginx/sites-enabled/
ufw allow 11435/tcp
systemctl reload nginx
```

Generate a secure key: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

Clients then connect to `http://your-server:11435` with the header `Authorization: Bearer YOUR_SECRET_API_KEY`.

## Security Notes

- n8n is exposed on port 5678 with Basic Auth -- consider adding a reverse proxy with TLS for production
- Ollama listens on localhost only by default (not exposed to the internet)
- The optional Ollama proxy (port 11435) uses Bearer token authentication
- All credentials are in `.env` (never committed to git)
- KnowledgeDigest web viewer should be secured with a reverse proxy (e.g., Nginx Basic Auth on port 8788, block direct access to 8787 via firewall)

## Part of the ellmos ecosystem

| Component | Description |
|-----------|-------------|
| [ellmos-ai/rinnsal](https://github.com/ellmos-ai/rinnsal) | Lightweight AI memory & task management |
| [file-bricks/knowledgedigest](https://github.com/file-bricks/knowledgedigest) | Document knowledge base with web UI |
| [file-bricks/NoteSpaceLLM](https://github.com/file-bricks/NoteSpaceLLM) | Desktop document analysis & RAG chat (connects to stack's Ollama) |
| [research-line/research-agent](https://github.com/research-line/research-agent) | Academic paper search & analysis |

## License

MIT
