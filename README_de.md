# ellmos-stack

**🇬🇧 [English Version](README.md)**

Ein selbst gehosteter KI-Stack für Forschung und Wissensmanagement. Kombiniert ein lokales LLM, Workflow-Automatisierung, persistenten Speicher und eine Wissensdatenbank in einem deploybaren Setup.

**Keine Cloud-Abhängigkeiten.** Alles läuft auf dem eigenen Server.

## Was steckt drin

```
┌─────────────────────────────────────────────────────────┐
│                    ellmos-stack                          │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │
│  │  Ollama   │  │   n8n    │  │  Research Pipeline    │ │
│  │ Lokales  │  │ Workflow │  │ PubMed/arXiv → Ollama │ │
│  │   LLM    │  │  Engine  │  │    → KnowledgeDigest  │ │
│  └────┬─────┘  └────┬─────┘  └───────────┬───────────┘ │
│       │              │                     │             │
│  ┌────┴──────────────┴─────────────────────┴──────────┐ │
│  │              Gemeinsame Dienste                      │ │
│  │  ┌─────────────────┐  ┌──────────────────────────┐ │ │
│  │  │    Rinnsal       │  │   KnowledgeDigest        │ │ │
│  │  │  Memory + Tasks  │  │  Dokumentensuche + Web   │ │ │
│  │  │  Ollama Runner   │  │  Auto-Indexierung        │ │ │
│  │  └─────────────────┘  └──────────────────────────┘ │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

| Komponente | Rolle | Quelle |
|------------|-------|--------|
| **[Ollama](https://ollama.com)** | Lokale LLM-Inferenz (qwen3:4b Standard) | Docker |
| **[n8n](https://n8n.io)** | Workflow-Automatisierung, Webhooks, Scheduling | Docker |
| **[Rinnsal](https://github.com/ellmos-ai/rinnsal)** | Leichtgewichtiges Memory + Task-Management für KI-Agenten | pip |
| **[KnowledgeDigest](https://github.com/file-bricks/knowledgedigest)** | Dokumenten-Ingestion, Chunking, Suche, Web-UI | pip |
| **Research Pipeline** | Automatisierte Paper-Suche → Analyse → Speicherung | enthalten |

## Voraussetzungen

- **Server:** Linux (Ubuntu 22.04+, Debian 12+), 2+ CPU-Kerne, 8+ GB RAM
- **Software:** Docker, Docker Compose v2, Python 3.10+
- **Festplatte:** ~5 GB für das Basis-Setup (Modell + Container)

Getestet auf Hetzner CCX13 (2 vCPU, 8 GB RAM, ~18 EUR/Monat).

## Schnellstart

```bash
# Klonen
git clone https://github.com/ellmos-ai/ellmos-stack.git
cd ellmos-stack

# Installieren (als root)
sudo ./install.sh

# Fertig. Die Dienste laufen:
#   n8n:              http://deine-ip:5678
#   KnowledgeDigest:  http://deine-ip:8787
#   Ollama:           localhost:11434 (intern)
```

Der Installer:
1. Installiert Systemabhängigkeiten (Python, Git, curl)
2. Richtet Docker-Dienste ein (Ollama + n8n)
3. Lädt das konfigurierte LLM-Modell herunter
4. Installiert Python-Komponenten (Rinnsal, KnowledgeDigest)
5. Erstellt einen systemd-Dienst für den KnowledgeDigest Web-Viewer
6. Richtet Cron-Jobs für Auto-Indexierung und Hintergrund-Zusammenfassungen ein
7. Generiert ein sicheres n8n-Passwort (gespeichert in `.env`)

## Konfiguration

`.env` kopieren und bearbeiten:

```bash
cp .env.example .env
nano .env
```

Wichtige Einstellungen:

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `N8N_PASSWORD` | *(generiert)* | n8n-Weboberflächen-Passwort |
| `OLLAMA_MODEL` | `qwen3:4b` | Zu verwendendes LLM-Modell |
| `OLLAMA_MEMORY_LIMIT` | `6G` | Max. RAM für Ollama |
| `KD_PORT` | `8787` | KnowledgeDigest Web-UI Port |
| `KD_SUMMARY_PROVIDER` | `ollama` | Zusammenfassungs-Backend: `ollama`, `anthropic` |

## Anwendungsfälle

### 1. Wissensdatenbank

Dokumente (PDF, TXT, MD, DOCX) in das Inbox-Verzeichnis legen:

```bash
cp paper.pdf /opt/ellmos-stack/data/knowledgedigest/inbox/
# Automatisch indexiert innerhalb von 5 Minuten, Zusammenfassungen innerhalb von 15 Minuten
```

Durchsuchen unter `http://deine-ip:8787`.

### 2. Forschungsautomatisierung

Wissenschaftliche Paper suchen, mit dem lokalen LLM analysieren, Ergebnisse speichern:

```bash
cd /opt/ellmos-stack
venv/bin/python services/research_pipeline.py \
    "dark matter detection methods" \
    --papers 10 --summarize --save
```

### 3. KI-Memory & Tasks

Persistentes Memory und Task-Management für KI-Agenten:

```python
from rinnsal import memory, tasks

memory.init("/opt/ellmos-stack/data/rinnsal/rinnsal.db")
memory.write("Server setup completed", tags=["infra"])

tasks.init("/opt/ellmos-stack/data/rinnsal/rinnsal.db")
tasks.add("Review research results", priority="high")
```

### 4. Workflow-Automatisierung (n8n)

Automatisierte Workflows mit n8n bauen unter `http://deine-ip:5678`:

- **Geplante Forschung:** Cron → Research Pipeline → E-Mail-Digest
- **Dokumentenverarbeitung:** Webhook → Download → KnowledgeDigest Inbox
- **Monitoring:** Health-Checks → Alerts

### 5. Direkter LLM-Zugang

Ollama direkt von jedem Dienst aus abfragen:

```bash
curl http://localhost:11434/api/generate \
    -d '{"model":"qwen3:4b","prompt":"Erkläre Quantenverschränkung kurz"}'
```

Oder über Rinnsals OllamaRunner:

```python
from rinnsal.auto import OllamaRunner

runner = OllamaRunner(model="qwen3:4b", think=False)
result = runner.run("Fasse diesen Text zusammen: ...")
```

### 6. Desktop-Dokumentenanalyse (NoteSpaceLLM)

[NoteSpaceLLM](https://github.com/file-bricks/NoteSpaceLLM) als Desktop-Client für interaktive Dokumentenanalyse nutzen, angetrieben durch die Ollama-Instanz des Stacks:

1. NoteSpaceLLM auf dem lokalen Rechner installieren
2. Ollama Auth-Proxy einrichten (siehe [Ollama für Remote-Zugriff freigeben](#ollama-für-remote-zugriff-freigeben) unten)
3. In NoteSpaceLLM: Menü > LLM > Einstellungen > Server-URL und API-Key setzen

NoteSpaceLLM bietet Drag-and-Drop-Dokumentenanalyse, RAG-basierten Chat und Multi-Format-Report-Export — alles verarbeitet durch das LLM des Stacks.

## Architektur

Der Stack nutzt **Docker** für Ollama und n8n (zustandsbehaftete Dienste mit Volumes) und **pip-Pakete** für die Python-Komponenten (Rinnsal, KnowledgeDigest). Hintergrundverarbeitung läuft über Cron.

```
Port 5678  ──→ n8n (Docker)
Port 8787  ──→ KnowledgeDigest Web-Viewer (systemd)
Port 11434 ──→ Ollama (Docker, nur localhost)
Port 11435 ──→ Ollama Auth-Proxy (Nginx, optional, für Remote-Clients)

Cron:
  */5  Min ──→ auto_ingest.py (neue Dokumente indexieren)
  */15 Min ──→ process_summaries.py (LLM-Zusammenfassung)
  */5  Min ──→ ollama-service Health (Auto-Neustart bei Ausfall)
```

Daten werden in `/opt/ellmos-stack/data/` gespeichert (SQLite-Datenbanken, Dokumentdateien).

## Anpassung

### Anderes LLM-Modell

```bash
# .env bearbeiten
OLLAMA_MODEL=mistral:7b

# Neues Modell herunterladen
docker exec ollama ollama pull mistral:7b

# Für NoteSpaceLLM RAG-Embeddings auch ein Embedding-Modell laden:
docker exec ollama ollama pull nomic-embed-text

# Zusammenfassungsverarbeitung neu starten (nutzt OLLAMA_MODEL aus .env)
```

### Cloud-LLM für Zusammenfassungen

```bash
# In .env
KD_SUMMARY_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Benutzerdefinierter System-Prompt

`config/system_prompt.txt` bearbeiten, um Persönlichkeit, Sprache und Verhalten des LLM anzupassen.

## Ollama für Remote-Zugriff freigeben

Standard: Ollama hört nur auf localhost. Um Desktop-Clients (wie NoteSpaceLLM) oder andere Rechner Zugriff auf das LLM des Stacks zu geben, einen Nginx Reverse-Proxy mit API-Key-Authentifizierung einrichten:

```bash
# Nginx installieren
apt install nginx

# Proxy-Konfiguration erstellen
cat > /etc/nginx/sites-available/ollama-proxy << 'EOF'
server {
    listen 11435;
    server_name _;

    location / {
        if ($http_authorization != "Bearer DEIN_GEHEIMER_API_KEY") {
            return 401 "Unauthorized";
        }
        proxy_pass http://127.0.0.1:11434;
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }

    # Öffentlicher Health-Endpoint
    location /health {
        proxy_pass http://127.0.0.1:11434/api/tags;
        proxy_read_timeout 5s;
    }
}
EOF

# Aktivieren und starten
ln -sf /etc/nginx/sites-available/ollama-proxy /etc/nginx/sites-enabled/
ufw allow 11435/tcp
systemctl reload nginx
```

Sicheren Key generieren: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

Clients verbinden sich dann mit `http://dein-server:11435` und dem Header `Authorization: Bearer DEIN_GEHEIMER_API_KEY`.

## Sicherheitshinweise

- n8n ist auf Port 5678 mit Basic Auth erreichbar — für Produktion einen Reverse-Proxy mit TLS verwenden
- Ollama hört standardmäßig nur auf localhost (nicht aus dem Internet erreichbar)
- Der optionale Ollama-Proxy (Port 11435) nutzt Bearer-Token-Authentifizierung
- Alle Zugangsdaten sind in `.env` (wird nie ins Git committed)
- KnowledgeDigest Web-Viewer sollte mit einem Reverse-Proxy gesichert werden (z.B. Nginx Basic Auth auf Port 8788, direkten Zugriff auf 8787 per Firewall blockieren)

## Stack-Familie

ellmos-stack ist der **All-in-one Starter-Stack** — die Referenz-Implementierung mit allem inklusive. Zukünftige spezialisierte Stacks bauen auf denselben Basis-Komponenten (Ollama + n8n + Rinnsal) auf und ergänzen domänenspezifische Erweiterungen:

| Stack | Fokus | Komponenten |
|-------|-------|-------------|
| **ellmos-stack** (dieses Repo) | All-in-one Wissen & Forschung | Ollama + n8n + Rinnsal + KnowledgeDigest + Research Pipeline |
| ellmos-research-stack | Akademische Forschung & Literatur | + PubMed/arXiv-Pipelines, Bibliografie-Tools, Zitationsnetzwerke |
| ellmos-dev-stack | Softwareentwicklung & DevOps | + Code-Analyse, CI/CD-Integration, Repo-Monitoring |
| ellmos-media-stack | Content-Erstellung & Medien | + Transkription, Zusammenfassungs-Pipelines, Medienverarbeitung |

Jeder Stack ist ein eigenständiges Repo mit eigenem `docker-compose.yml` und `install.sh`. Sie teilen die Basis-Infrastruktur, fügen aber domänenspezifische Tools und Workflows hinzu.

## Teil des ellmos-Ökosystems

| Komponente | Beschreibung |
|------------|--------------|
| [ellmos-ai/rinnsal](https://github.com/ellmos-ai/rinnsal) | Leichtgewichtiges KI-Memory & Task-Management |
| [file-bricks/knowledgedigest](https://github.com/file-bricks/knowledgedigest) | Dokumenten-Wissensdatenbank mit Web-UI |
| [file-bricks/NoteSpaceLLM](https://github.com/file-bricks/NoteSpaceLLM) | Desktop-Dokumentenanalyse & RAG-Chat (verbindet sich mit dem Ollama des Stacks) |
| [research-line/research-agent](https://github.com/research-line/research-agent) | Akademische Paper-Suche & Analyse |

## Lizenz

MIT
