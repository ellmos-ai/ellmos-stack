# ellmos-stack

<img src="assets/banner_v2.png" width="100%" alt="ellmos-stack Banner">

**🇬🇧 [English Version](README.md)**

[![ellmos-stack tests](https://github.com/ellmos-ai/ellmos-stack/actions/workflows/tests.yml/badge.svg)](https://github.com/ellmos-ai/ellmos-stack/actions/workflows/tests.yml)
[![Tests bestanden](https://img.shields.io/badge/Tests-61%20bestanden-brightgreen.svg)](tests)
[![Neuestes Release](https://img.shields.io/github/v/release/ellmos-ai/ellmos-stack?label=release)](https://github.com/ellmos-ai/ellmos-stack/releases)
[![ellmos ecosystem](https://img.shields.io/badge/ecosystem-ellmos--ai-blue.svg)](https://github.com/ellmos-ai)
[![open-bricks umbrella](https://img.shields.io/badge/umbrella-open--bricks-blueviolet.svg)](https://github.com/open-bricks)
[![Architektur: Docker Compose](https://img.shields.io/badge/architecture-Docker%20Compose-2496ED.svg?logo=docker&logoColor=white)](#architektur)
[![Sicherheit: Local-First](https://img.shields.io/badge/security-local--first-success.svg)](#sicherheitshinweise)
[![LLM-Ready Context](https://img.shields.io/badge/LLM--Ready-llms.txt-blue.svg)](llms.txt)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Lizenz: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Schnellstart](#schnellstart) • [Architektur](#architektur) • [Workflows & Sequenz](#workflows--sequenz) • [Stack-Familie](#stack-familie) • [Sicherheitshinweise](#sicherheitshinweise) • [llms.txt](llms.txt)

Ein selbst gehosteter KI-Stack für Forschung und Wissensmanagement. Kombiniert ein lokales LLM, Workflow-Automatisierung, persistenten Speicher und eine Wissensdatenbank in einem deploybaren Setup.

> [!NOTE]
> **Maschinenlesbarer Kontext für KI-Agenten:**
> Für eine strukturierte Übersicht der Architektur-Grenzen, primären Schnittstellen, Sicherheits-Policies und Local-First-Inferenzregeln siehe [`llms.txt`](llms.txt) oder [`STACK-MAP.md`](STACK-MAP.md).

**Standardmäßig keine Abhängigkeit von einem gehosteten Modell.** Inferenz, Workflow-Zustand, Memory und Dokumente bleiben auf dem eigenen Server. Paper-Suche (PubMed/arXiv), Telegram, Paket-/Image-Downloads und das optionale Anthropic-Backend benötigen Netzwerkzugriff.

Maschinenlesbarer Kontext für LLMs und Coding-Agenten: [`llms.txt`](llms.txt).

## Einstieg

| Wenn du brauchst... | Starte mit | Warum |
|---------------------|------------|-------|
| Einen lokalen KI-Forschungsserver | [`install.sh`](install.sh) | Installiert Ollama, n8n, USMC, GARDENER, task-master und KnowledgeDigest unter `/opt/ellmos-stack`. |
| Workflow-Automatisierung mit lokalem Modell | [`docker-compose.yml`](docker-compose.yml) | Startet n8n und Ollama mit persistenten Volumes. |
| Einen durchsuchbaren Dokumenten-Eingang | [`services/auto_ingest.py`](services/auto_ingest.py) | Übergibt neue Dokumente an die KnowledgeDigest-Indexierung. |
| Paper-Suche und Zusammenfassungspipelines | [`services/research_pipeline.py`](services/research_pipeline.py) | Sucht Paper, fasst sie zusammen und kann Ergebnisse in der Wissensdatenbank speichern. |
| Agenten-Memory und Task-Zustand | [`stack.v2.json`](stack.v2.json) | Trennt kuratiertes Memory, organisches Memory und Tasks in spezialisierte Module. |

ellmos-stack ist ein **local-first KI-Stack für Forschungsautomatisierung und private Wissensarbeit**. Er ist kein gehostetes SaaS-Produkt, kein Cloud-LLM-Gateway und keine Kubernetes-Plattform.

Wichtige Suchanker: `ellmos-stack`, `self-hosted AI research stack`, `Ollama n8n KnowledgeDigest`, `private local RAG server` und `Docker Compose AI knowledge base`.

## Was steckt drin

```mermaid
flowchart TD
  subgraph STACK["ellmos-stack"]
    OLLAMA["Ollama<br/>Lokales LLM (qwen3)"]
    N8N["n8n<br/>Workflow Engine"]
    RESEARCH["Research Pipeline<br/>PubMed/arXiv → Ollama → KnowledgeDigest"]
    subgraph SHARED["Gemeinsame Dienste"]
      MEMORY["USMC + GARDENER<br/>Kuratiertes + organisches Memory"]
      TASKS["task-master<br/>Task-Zustand"]
      KD["KnowledgeDigest<br/>Dokumentensuche + Web · Auto-Indexierung"]
    end
  end
  OLLAMA --- SHARED
  N8N --- SHARED
  RESEARCH --- SHARED
```

| Komponente | Rolle | Quelle |
|------------|-------|--------|
| **[Ollama](https://ollama.com)** | Lokale LLM-Inferenz (qwen3:4b Standard) | Docker |
| **[n8n](https://n8n.io)** | Workflow-Automatisierung, Webhooks, Scheduling | Docker |
| **[USMC](https://github.com/ellmos-ai/usmc)** | Kuratierte Fakten, Working Memory und Lessons (`memory.curated`) | gepinnter Git-Commit |
| **[GARDENER](https://github.com/ellmos-ai/gardener)** | Organisches lokales Memory und Wissenssubstrat (`memory.organic`) | gepinnter Git-Commit |
| **[task-master](https://github.com/ellmos-ai/task-master)** | Getrennter Task-Zustand (`tasks.default`) | gepinnter Git-Commit |
| **[KnowledgeDigest](https://github.com/file-bricks/knowledgedigest)** | Dokumenten-Ingestion, Chunking, Suche, Web-UI | gepinnter Git-Commit |
| **Research Pipeline** | PubMed-/arXiv-API-Suche → Analyse → Speicherung | enthalten |
| **Telegram Gateway** *(optional)* | Owner-gefilterter Telegram-Bot, antwortet über das lokale LLM | enthalten |

## Komposition auf einen Blick

```
ellmos-stack (Docker Compose)
├── Inferenz         Ollama            lokales LLM (qwen3:4b)
├── Automatisierung  n8n               Workflows, Webhooks, Scheduling
├── Wissen/RAG       KnowledgeDigest   Ingest → Chunking → FTS5 → Summary
├── Kuratiertes Mem. USMC              Fakten, Working Memory, Lessons (pinned-git)
├── Organisches Mem. GARDENER          lokales Memory/Wissenssubstrat (pinned-git)
├── Tasks            task-master       getrennter Task-Zustand (pinned-git)
├── services/        research_pipeline, auto_ingest, process_summaries,
│                    telegram_gateway, env_config
└── Externe APIs     PubMed · arXiv    Paper-Suche (https)
```

Vollständiger Kompositions-Bauplan — Komponenten, Rollen, Quellen, Policies: **[STACK-MAP.md](STACK-MAP.md)**.

## Voraussetzungen

- **Server:** Linux (Ubuntu 22.04+, Debian 12+), 2+ CPU-Kerne, 8+ GB RAM
- **Software:** Docker, Docker Compose v2, Python 3.10+
- **Festplatte:** ~5 GB für das Basis-Setup (Modell + Container)

## Validierung

Das Repository enthält Smoke-Tests, die ohne Docker, Ollama, n8n, Telegram oder Live-Netzwerkdienste laufen:

```bash
PYTHONIOENCODING=utf-8 python -m unittest discover -s tests -v
PYTHONIOENCODING=utf-8 python -m compileall -q services tests tools
PYTHONIOENCODING=utf-8 python tools/check_release_gate.py
```

Diese Prüfungen sind ein Offline-Preflight und kein Linux-Deployment-Nachweis. Öffentliche Releases verwenden das getrennte [Stack-Release-Gate](RELEASE_GATE.md): exakte Container-Tags, einen echten Linux-Docker-Compose-Start mit Probes, Localhost-Bindings sowie eine Owner-Account-/TLS-/Firewall-Prüfung. Gleitende `latest`-Tags scheitern dort.

Der Standard-Workflow in GitHub Actions führt Kompilierung und die vollständige Unit-Suite mit Python 3.10, 3.11 und 3.12 aus. Der manuelle Release-Workflow ergänzt den statischen Release-Checker und Linux-Compose-Probes.

## Schnellstart

```bash
# Klonen
git clone https://github.com/ellmos-ai/ellmos-stack.git
cd ellmos-stack

# Installieren (als root)
sudo ./install.sh

# Fertig. Die Dienste laufen:
#   n8n:              http://127.0.0.1:5678 (nur localhost -- siehe unten)
#   KnowledgeDigest:  http://127.0.0.1:8787 (nur localhost -- siehe unten)
#   Ollama:           localhost:11434 (intern)
```

Der Installer:
1. Installiert Systemabhängigkeiten (Python, Git, curl)
2. Richtet Docker-Dienste ein (Ollama + n8n)
3. Lädt das konfigurierte LLM-Modell herunter
4. Installiert gepinnte USMC-, GARDENER-, task-master- und KnowledgeDigest-Commits in ein Python-Venv
5. Erstellt den eingeschränkten Systemnutzer `ellmos-stack` und den KnowledgeDigest-systemd-Dienst
6. Richtet Cron-Jobs ohne Root-Rechte für Auto-Indexierung und Hintergrund-Zusammenfassungen ein

**Erster n8n-Start -- Owner-Account anlegen:** n8n 1.0+ hat kein Basic Auth mehr. Die Authentifizierung übernimmt der Owner-Account, der beim ersten Start in der Weboberfläche angelegt wird. Da der Port nur auf localhost gebunden ist, per SSH-Tunnel öffnen und das Setup abschließen, bevor irgendetwas freigegeben wird:

```bash
ssh -L 5678:127.0.0.1:5678 -L 8787:127.0.0.1:8787 root@dein-server
# dann http://localhost:5678 für n8n und http://localhost:8787 für KnowledgeDigest öffnen
```

## Konfiguration

`.env` kopieren und bearbeiten:

```bash
cp .env.example .env
nano .env
```

Wichtige Einstellungen:

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `OLLAMA_MODEL` | `qwen3:4b` | Zu verwendendes LLM-Modell |
| `OLLAMA_MEMORY_LIMIT` | `6G` | Max. RAM für Ollama |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama-Endpoint für die Service-Skripte |
| `OLLAMA_IMAGE_TAG` | `latest` | Ollama-Docker-Image-Tag -- vor Produktivbetrieb pinnen |
| `N8N_IMAGE_TAG` | `latest` | n8n-Docker-Image-Tag -- vor Produktivbetrieb pinnen |
| `KD_PORT` | `8787` | KnowledgeDigest Web-UI Port |
| `KD_SUMMARY_PROVIDER` | `ollama` | Zusammenfassungs-Backend: `ollama`, `anthropic` |
| `ELLMOS_TELEGRAM_TOKEN` | leer | Bevorzugtes Telegram-Bot-Token; `RINNSAL_TELEGRAM_TOKEN` bleibt nur als Migrations-Fallback |

**Image-Versionen für Produktion pinnen:** Die Compose-Datei nutzt für beide Docker-Images standardmäßig `latest` -- bequem zum Ausprobieren, aber nicht reproduzierbar und holt ggf. ungetestete Breaking Changes (n8n veröffentlicht regelmäßig Major-Releases). Vor Produktivbetrieb `OLLAMA_IMAGE_TAG` und `N8N_IMAGE_TAG` in der `.env` auf die konkret getesteten Versionen setzen.

## Anwendungsfälle

### 1. Wissensdatenbank

Dokumente (PDF, TXT, MD, DOCX) in das Inbox-Verzeichnis legen:

```bash
cp paper.pdf /opt/ellmos-stack/data/knowledgedigest/inbox/
# Automatisch indexiert innerhalb von 5 Minuten, Zusammenfassungen innerhalb von 15 Minuten
```

Durchsuchen unter `http://localhost:8787` über den SSH-Tunnel aus dem Schnellstart. Der Dienst bleibt auf localhost, solange kein geprüfter TLS-/Auth-Reverse-Proxy samt Firewall-Regel eingerichtet ist.

### 2. Forschungsautomatisierung

Wissenschaftliche Paper suchen, mit dem lokalen LLM analysieren, Ergebnisse speichern:

```bash
cd /opt/ellmos-stack
venv/bin/python services/research_pipeline.py \
    "dark matter detection methods" \
    --papers 10 --summarize --save
```

Der eingebaute, abhängigkeitsfreie Suchclient nutzt [NCBI E-utilities für PubMed](https://www.ncbi.nlm.nih.gov/home/develop/api/) und die [arXiv-API](https://info.arxiv.org/help/api/index.html). Mit `--source pubmed` oder `--source arxiv` lässt sich eine Quelle auswählen; die Paper-Suche benötigt ausgehenden Netzwerkzugriff.

### 3. KI-Memory & Tasks

Kuratiertes Memory und Task-Zustand verwenden bewusst getrennte Datenbanken.
Das organische Memory von GARDENER nutzt das eigene Verzeichnis
`/opt/ellmos-stack/data/gardener/`.

```python
from pathlib import Path

from gardener import Gardener
from usmc import api as memory
from taskplan import api as tasks

memory_db = "/opt/ellmos-stack/data/usmc/usmc_memory.db"
task_db = "/opt/ellmos-stack/data/task-master/taskplan.db"
memory.init(db_path=memory_db, agent_id="ellmos-stack")
memory.remember("server_setup", "completed", category="project")

tasks.init(db_path=task_db, agent_id="ellmos-stack")
tasks.add("Review research results", priority="high")

organic = Gardener(
    home=Path("/opt/ellmos-stack/data/gardener/home"),
    data_dir=Path("/opt/ellmos-stack/data/gardener"),
)
organic.put("research-note", content="Neue Evidenz prüfen", type="memory")
```

### 4. Workflow-Automatisierung (n8n)

Automatisierte Workflows mit n8n bauen unter `http://localhost:5678` (per SSH-Tunnel, siehe Schnellstart):

- **Geplante Forschung:** Cron → Research Pipeline → E-Mail-Digest
- **Dokumentenverarbeitung:** Webhook → Download → KnowledgeDigest Inbox
- **Monitoring:** Health-Checks → Alerts

### 5. Direkter LLM-Zugang

Ollama direkt von jedem Dienst aus abfragen:

```bash
curl http://localhost:11434/api/generate \
    -d '{"model":"qwen3:4b","prompt":"Erkläre Quantenverschränkung kurz"}'
```

### 6. Desktop-Dokumentenanalyse (NoteSpaceLLM)

[NoteSpaceLLM](https://github.com/file-bricks/NoteSpaceLLM) als Desktop-Client für interaktive Dokumentenanalyse nutzen, angetrieben durch die Ollama-Instanz des Stacks:

1. NoteSpaceLLM auf dem lokalen Rechner installieren
2. Ollama Auth-Proxy einrichten (siehe [Ollama für Remote-Zugriff freigeben](#ollama-für-remote-zugriff-freigeben) unten)
3. In NoteSpaceLLM: Menü > LLM > Einstellungen > Server-URL und API-Key setzen

NoteSpaceLLM bietet Drag-and-Drop-Dokumentenanalyse, RAG-basierten Chat und Multi-Format-Report-Export — alles verarbeitet durch das LLM des Stacks.

### 7. Telegram Gateway (optional)

`services/telegram_gateway.py` ist ein Owner-gefilterter Telegram-Bot: Nur die konfigurierte Owner-Chat-ID darf mit ihm sprechen. Eingehende Nachrichten beantwortet das lokale LLM des Stacks mit optionalem USMC-Kontext; `/tasks` liest die getrennte task-master-Datenbank. Eine BACH-Weiterleitung gibt es nicht. Das Gateway nutzt ausschließlich die Python-Standardbibliothek.

Einrichtung:

```bash
# 1. Bot-Token von @BotFather und Chat-ID von @userinfobot holen,
#    dann ELLMOS_TELEGRAM_TOKEN und TELEGRAM_OWNER_CHAT_ID in .env setzen

# 2. Verbindung testen
/opt/ellmos-stack/venv/bin/python /opt/ellmos-stack/services/telegram_gateway.py --test

# 3. Als systemd-Dienst installieren (Unit-Datei liegt bei)
cp /opt/ellmos-stack/config/telegram-gateway.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now telegram-gateway
```

## Architektur

Der Stack nutzt **Docker** für Ollama und n8n (zustandsbehaftete Dienste mit Volumes) und installiert USMC, GARDENER, task-master und KnowledgeDigest aus gepinnten Git-Commits in ein Venv. Ihre Laufzeitdaten bleiben in getrennten Pfaden. KnowledgeDigest und die Cron-Hintergrundverarbeitung laufen als eingeschränkter Nutzer `ellmos-stack`.

```
Port 5678  ──→ n8n (Docker, nur localhost -- SSH-Tunnel oder Reverse-Proxy)
Port 8787  ──→ KnowledgeDigest Web-Viewer (systemd, nur localhost)
Port 11434 ──→ Ollama (Docker, nur localhost)
Port 443   ──→ TLS-Ollama-Reverse-Proxy (optional, für Remote-Clients)

Cron:
  */5  Min ──→ auto_ingest.py (neue Dokumente indexieren)
  */15 Min ──→ process_summaries.py (LLM-Zusammenfassung)
```

Daten werden in `/opt/ellmos-stack/data/` gespeichert (SQLite-Datenbanken, Dokumentdateien).

## Workflows & Sequenz

Das nachfolgende Sequenzdiagramm veranschaulicht das Zusammenspiel von automatisierter Paper-Recherche, Dokumenten-Ingestion, lokaler Modell-Inferenz und Wissenssicherung:

```mermaid
sequenceDiagram
  autonumber
  actor User as "Operator / Forscher"
  participant Pipeline as "research_pipeline.py"
  participant Ingest as "auto_ingest.py"
  participant LLM as "Ollama LLM (qwen3)"
  participant KD as "KnowledgeDigest (Port 8787)"
  participant Memory as "USMC & GARDENER"
  participant Tasks as "task-master"

  Note over User,Tasks: "Paper-Recherche- und Ingestion-Workflow"
  User->>Pipeline: "Suchanfrage ausführen (z. B. PubMed / arXiv)"
  Pipeline->>Pipeline: "Paper-Metadaten und Abstracts abrufen"
  Pipeline->>LLM: "Synthese und strukturierte Zusammenfassung anfordern"
  LLM-->>Pipeline: "Extrahierte Kernaussagen zurückgeben"
  Pipeline->>KD: "Markdown-Bericht im Inbox-Verzeichnis ablegen"
  Ingest->>KD: "Inbox-Dateien automatisch in SQLite FTS5 indexieren"
  Pipeline->>Memory: "Wichtige Erkenntnisse sichern (kuratierte Fakten & organische Notizen)"
  Pipeline->>Tasks: "Follow-up-Forschungsaufgaben eintragen"
  User->>KD: "Recherche und Volltextsuche via Web-UI (localhost:8787)"
```

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

Standard: Ollama hört nur auf localhost. Für Remote-Clients bleibt dieses Binding bestehen; davor kommt ein TLS-Reverse-Proxy mit Bearer-Token. Vorher ein Zertifikat für `ollama.example.com` beschaffen; den Token niemals über Klartext-HTTP senden.

```bash
# Nginx installieren
apt install nginx

# Proxy-Konfiguration erstellen
cat > /etc/nginx/sites-available/ollama-proxy << 'EOF'
server {
    listen 443 ssl;
    server_name ollama.example.com;

    ssl_certificate /etc/letsencrypt/live/ollama.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ollama.example.com/privkey.pem;

    location / {
        if ($http_authorization != "Bearer DEIN_GEHEIMER_API_KEY") {
            return 401 "Unauthorized";
        }
        proxy_pass http://127.0.0.1:11434;
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }

}
EOF

# Aktivieren und starten
chmod 600 /etc/nginx/sites-available/ollama-proxy
ln -sf /etc/nginx/sites-available/ollama-proxy /etc/nginx/sites-enabled/
nginx -t
ufw allow 443/tcp
systemctl reload nginx
```

Sicheren Key generieren: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

Clients verbinden sich dann mit `https://ollama.example.com` und dem Header `Authorization: Bearer DEIN_GEHEIMER_API_KEY`.

## Sicherheitshinweise

- n8n ist standardmäßig auf `127.0.0.1:5678` gebunden und von außen **nicht** erreichbar. n8n 1.0+ hat Basic Auth entfernt; die Authentifizierung übernimmt der n8n-Owner-Account, der beim ersten Start in der Weboberfläche angelegt werden muss (per SSH-Tunnel, siehe Schnellstart). **Niemals eine n8n-Instanz freigeben, bevor der Owner-Account existiert** — sonst wird der erste Besucher zum Owner.
- Für entfernten n8n-Zugriff das Localhost-Binding beibehalten und einen geprüften TLS-/Auth-Reverse-Proxy, SSH-Tunnel oder ein privates VPN verwenden. Den unverschlüsselten HTTP-Port 5678 niemals direkt ins öffentliche Internet stellen, auch nicht nach Einrichtung des Owner-Accounts
- Ollama hört standardmäßig nur auf localhost (nicht aus dem Internet erreichbar)
- Der optionale Ollama-Proxy nutzt TLS plus Bearer-Token; ein Bearer-Token über Klartext-HTTP ist nicht sicher
- Alle Zugangsdaten sind in `.env` (wird nie ins Git committed); der Installer beschränkt die Datei auf den Eigentümer (`0600`)
- KnowledgeDigest bindet standardmäßig an localhost; externer Zugriff braucht einen geprüften TLS-/Auth-Reverse-Proxy samt Firewall-Regel
- Das Telegram-Gateway startet nur, wenn Bot-Token und Owner-Chat-ID gesetzt sind
- USMC, GARDENER, task-master und KnowledgeDigest sind im Installer auf exakte Commits gepinnt; Upgrades sind bewusste Quelländerungen
- Vor Upgrade oder Release [`OPERATIONS.md`](OPERATIONS.md) prüfen und einen Restore proben

## Suche und Abgrenzung

Mit **ellmos-stack** ist der selbst gehostete lokale KI-Forschungsstack von `ellmos-ai` gemeint: Ollama für Inferenz, n8n für Workflow-Automatisierung, spezialisiertes USMC-/GARDENER-Memory, task-master für Tasks sowie KnowledgeDigest für Dokumentensuche. Sinnvolle Suchphrasen:

- `ellmos-stack self-hosted AI research stack`
- `ellmos stack Ollama n8n USMC GARDENER task-master KnowledgeDigest`
- `local-first AI knowledge stack Docker Compose`
- `self-hosted research automation Ollama n8n`
- `private local RAG server with Ollama and n8n`
- `Docker Compose AI knowledge base with document search`
- `self-hosted AI starter stack for research workflows`

Das Projekt ist nicht mit Eclipse LMOS, Llama Stack, LLemonStack, generischen n8n-AI-Starter-Kits, reinen Open-WebUI-Deployments, allgemeinen LLMOps-Stacks oder cloud-gehosteten AI-Agent-Plattformen verbunden. Für eindeutige Suchergebnisse sollte der kanonische Repo-Pfad `ellmos-ai/ellmos-stack` verwendet werden.

## Stack-Familie

> **Kanonischer Katalog:** Die vollständige, aktuelle Übersicht aller ellmos-Stacks liegt unter
> **[ellmos-ai/stacks](https://github.com/ellmos-ai/stacks)** — dem Stacks-Übersichts-Repository
> (Katalog, gemeinsames Manifest-Schema, Dokumentation). Die nachfolgende Tabelle ist ein
> praktischer Auszug; im Zweifelsfall ist der Katalog maßgeblich.

ellmos-stack ist der **All-in-one Starter-Stack** — die Referenz-Implementierung mit allem inklusive. Schwester-Stacks bauen auf denselben Kompositionsprinzipien mit domänenspezifischem Fokus auf:

| Stack | Fokus | Komponenten |
|-------|-------|-------------|
| **ellmos-stack** (dieses Repo) | All-in-one Wissen & Forschung | Ollama + n8n + USMC + GARDENER + task-master + KnowledgeDigest + Research Pipeline |
| [agent-ops-stack](https://github.com/ellmos-ai/agent-ops-stack) | Multi-Agent-Operations (Locks, Tickets, Decision-Avatar, Memory) | ticket-master + lock-master + build-your-users-mind + skills + controlcenter-mcp + homebase-mcp |
| ellmos-research-stack *(geplant)* | Akademische Forschung & Literatur | + PubMed/arXiv-Pipelines, Bibliografie-Tools, Zitationsnetzwerke |
| ellmos-dev-stack *(geplant)* | Softwareentwicklung & DevOps | + Code-Analyse, CI/CD-Integration, Repo-Monitoring |
| ellmos-media-stack *(geplant)* | Content-Erstellung & Medien | + Transkription, Zusammenfassungs-Pipelines, Medienverarbeitung |

Jeder Stack ist ein eigenständiges Repo mit eigenem `docker-compose.yml` und `install.sh`. Sie teilen das Kompositionsprinzip („Installation IST der Bauplan"), fügen aber domänenspezifische Tools und Workflows hinzu.

## Teil des ellmos-Ökosystems

| Komponente | Beschreibung |
|------------|--------------|
| [ellmos-ai/usmc](https://github.com/ellmos-ai/usmc) | Kuratiertes Agenten-Memory |
| [ellmos-ai/gardener](https://github.com/ellmos-ai/gardener) | Organisches lokales Memory und Wissenssubstrat |
| [ellmos-ai/task-master](https://github.com/ellmos-ai/task-master) | Getrennter Task-Zustand |
| [ellmos-ai/n8n-workflow-manager](https://github.com/ellmos-ai/n8n-workflow-manager) | Prüft und versioniert die Workflows im n8n dieses Stacks: Graph-Viewer, Entscheidungsprotokoll, Rollback |
| [file-bricks/knowledgedigest](https://github.com/file-bricks/knowledgedigest) | Dokumenten-Wissensdatenbank mit Web-UI |
| [file-bricks/NoteSpaceLLM](https://github.com/file-bricks/NoteSpaceLLM) | Desktop-Dokumentenanalyse & RAG-Chat (verbindet sich mit dem Ollama des Stacks) |
| [PubMed E-utilities](https://www.ncbi.nlm.nih.gov/home/develop/api/) und [arXiv-API](https://info.arxiv.org/help/api/index.html) | Live-Suche nach wissenschaftlichen Metadaten für die enthaltene Research Pipeline |

## Lizenz

MIT

---

## Haftung / Liability

Dieses Projekt ist eine **unentgeltliche Open-Source-Schenkung** im Sinne der §§ 516 ff. BGB. Die Haftung des Urhebers ist gemäß **§ 521 BGB** auf **Vorsatz und grobe Fahrlässigkeit** beschränkt. Ergänzend gelten die Haftungsausschlüsse aus GPL-3.0 / MIT / Apache-2.0 §§ 15–16 (je nach gewählter Lizenz).

Nutzung auf eigenes Risiko. Keine Wartungszusage, keine Verfügbarkeitsgarantie, keine Gewähr für Fehlerfreiheit oder Eignung für einen bestimmten Zweck.

This project is an unpaid open-source donation. Liability is limited to intent and gross negligence (§ 521 German Civil Code). Use at your own risk. No warranty, no maintenance guarantee, no fitness-for-purpose assumed.
