# Security Policy / Sicherheitsrichtlinie

## Reporting a Vulnerability / Sicherheitslücke melden

**Please do not report security vulnerabilities in public GitHub issues.**
**Bitte melde Sicherheitslücken niemals in öffentlichen GitHub-Issues.**

Use GitHub's private vulnerability reporting via the repository's **Security** tab (<https://github.com/ellmos-ai/ellmos-stack/security/advisories/new>).

### What to Include / Was in die Meldung gehört

1. Affected component (`install.sh`, `docker-compose.yml`, `services/*.py`, `tools/check_release_gate.py`, or pinned stack module).
2. Clear reproduction steps or proof of concept.
3. Expected security invariant vs. observed behavior (see `THIRD_PARTY_LICENSES.md` and `RELEASE_GATE.md`).

### Response Target / Reaktionszeit

- Initial acknowledgment and triage target: within **48 hours** (`INV-LOCAL-10`).
- Please allow reasonable time for verification and coordinated remediation before public disclosure.

## Security Design Boundaries / Sicherheitsgrenzen

- **Localhost by default:** Ollama (`127.0.0.1:11434`), n8n (`127.0.0.1:5678`), and KnowledgeDigest (`127.0.0.1:8787`) bind exclusively to loopback interfaces unless an operator explicitly fronts them with a reviewed TLS/authentication reverse proxy or SSH tunnel.
- **No n8n Basic Auth:** n8n >= 1.0 uses an interactive owner account created on first start. Never expose port 5678 before creating the owner account.
- **Shell-free `.env` loading:** Python services parse `.env` literally (`services/env_config.py`) without shell expansion; installed `.env` files are restricted to mode `0600`.
- **Fail-closed Telegram gateway:** `services/telegram_gateway.py` refuses to start unless both bot token and `TELEGRAM_OWNER_CHAT_ID` are set.
- **Non-elevation (`RunAsInvoker`):** Offline checks, tests, and runtime Python services run under standard user privileges (`ellmos-stack` service user in Linux deployments).
