---
name: ellmos-stack
version: 0.1.1
description: "Operate, verify, and automate workflows with ellmos-stack — a self-hosted local-first AI research and knowledge stack combining Ollama, n8n, USMC, GARDENER, task-master, and KnowledgeDigest."
---

# ellmos-stack Product Skill

> Standalone product skill (P-022) for `ellmos-ai/ellmos-stack` (`v0.1.1`). Works independently of external skill registries.

## Supported Scope & Actual Status

- **Target platform:** Linux servers (Ubuntu 22.04+, Debian 12+) with Docker Compose v2 and Python `>=3.10` for full stack deployment (`install.sh` + `docker-compose.yml`).
- **Cross-platform offline scope:** Static validation, unit/smoke tests, `.env` parsing, and metadata checks run offline on Linux, Windows, and macOS without Docker, Ollama, n8n, or network access.
- **Included services (`services/`):**
  - `services/research_pipeline.py`: Search PubMed E-utilities and/or arXiv Atom API, optionally summarize via local Ollama (`--summarize`), and save markdown reports to the KnowledgeDigest inbox (`--save`).
  - `services/auto_ingest.py`: Index new documents from `data/knowledgedigest/inbox/` into `data/knowledgedigest/knowledge.db`.
  - `services/process_summaries.py`: Summarize one queued KnowledgeDigest item using `KD_SUMMARY_PROVIDER` (`ollama` default, optional `anthropic`).
  - `services/telegram_gateway.py`: Owner-filtered Telegram bot (`--test`, `--send "Text"`, or polling loop); fails closed unless both token and `TELEGRAM_OWNER_CHAT_ID` are set.
  - `services/env_config.py`: Literal, shell-free `.env` parser (`load_env_file`).
- **What it is NOT:** Not a hosted SaaS, not a Kubernetes platform, not an unauthenticated public gateway, and does not automatically write findings into USMC/GARDENER or task-master unless called explicitly via those module APIs.

## Prerequisites & Configuration

1. Clone the repository and prepare an isolated environment for offline verification or local CLI execution:
   ```bash
   python -m venv .venv
   # Linux/macOS: source .venv/bin/activate
   # Windows:     .venv\Scripts\Activate.ps1
   python -m pip install -e ".[dev]"
   ```
2. For full server deployment on Linux (`root` required only during `install.sh` setup; runtime services use unprivileged `ellmos-stack` user):
   - Copy `.env.example` to `.env` (`chmod 600 .env`) and pin `OLLAMA_IMAGE_TAG` and `N8N_IMAGE_TAG` before production use.
   - Do not expose n8n (`127.0.0.1:5678`) before creating the owner account in the web UI via SSH tunnel.

## Concrete Machine Calls

### 1. Offline Preflight & Release Gate Verification

```bash
python -m pip install --no-build-isolation --no-deps --dry-run .
ruff check .
python -m compileall -q services tests tools
python -m pytest -ra -v
python tools/check_release_gate.py
```

For production release tag verification (without Linux Compose evidence yet):

```bash
python tools/check_release_gate.py --release --preflight --ollama-tag 0.32.0 --n8n-tag 2.31.1
```

### 2. Academic Literature Search (`services/research_pipeline.py`)

```bash
python services/research_pipeline.py "local rag evaluation" --papers 5 --source arxiv
```

Optional flags:
- `--source {all,pubmed,arxiv}` (default: `all`)
- `--papers <N>` (`>= 1`, default: `10`)
- `--summarize` (requires reachable local Ollama at `OLLAMA_BASE_URL`, default `http://localhost:11434`)
- `--save` (writes a collision-safe `research_<timestamp>_<slug>_<hex>.md` file into `data/knowledgedigest/inbox/`)

### 3. Inbox Ingestion & Summary Queue (Deployed Server)

```bash
python services/auto_ingest.py
python services/process_summaries.py
```

Both scripts return exit code `0` cleanly when no inbox items or database exist yet, and exit code `1` on ingestion/summarization errors.

### 4. Telegram Gateway Check

```bash
python services/telegram_gateway.py --test
python services/telegram_gateway.py --send "Status check"
```

## Safety Boundaries & Failure Modes

- **Credentials & secrets:** Never read, print, or commit `.env`, `*.key`, `*.pem`, `*.secret`, or `*.db` files.
- **No automatic memory/task mutation:** `research_pipeline.py` only searches, summarizes, and optionally saves to KnowledgeDigest inbox. Persisting facts in USMC/GARDENER or creating tasks in `task-master` requires separate explicit calls to those packages.
- **Fail-closed gates:** `telegram_gateway.py` raises `ValueError` if `ELLMOS_TELEGRAM_TOKEN` (or fallback `RINNSAL_TELEGRAM_TOKEN`) or `TELEGRAM_OWNER_CHAT_ID` is empty. `tools/check_release_gate.py --release` exits `1` on floating image tags (`latest`) or missing security/restore attestations.

## Result Readback & Verification

- **Offline checks:** Expect `pytest` exit `0`, `ruff check .` exit `0`, and `Release gate: <N> passed, 0 failed` (exit `0`).
- **Research report (`--save`):** Confirm the printed filename (`Saved: research_...md`) exists inside `data/knowledgedigest/inbox/` and is non-empty.
- **Restore & backup verification:** Follow `OPERATIONS.md` (`sha256sum -c SHA256SUMS.txt` and localhost health probes on `127.0.0.1:11434`, `127.0.0.1:5678`, `127.0.0.1:8787`).

## Related Documents

- [llms.txt](llms.txt) — concise machine-readable repository context
- [STACK-MAP.md](STACK-MAP.md) & [stack.v2.json](stack.v2.json) — component roles and manifest
- [RELEASE_GATE.md](RELEASE_GATE.md) & [OPERATIONS.md](OPERATIONS.md) — release gate, backup, restore, and rollback runbooks
