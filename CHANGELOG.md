# Changelog

## Unreleased

- Added a public-stack release gate with static repository/security checks, mandatory image pinning, and a manual Linux Docker Compose evidence workflow.
- Added bounded Telegram gateway context handling so long-running polling sessions keep only recent user/assistant turns.
- Hardened `install.sh` so `KD_PORT` is read only from an exact `.env` assignment.
- Ignored local `.pytest_cache/` artifacts and covered both hygiene rules in smoke tests.
- Sharpened README and `llms.txt` discovery anchors for self-hosted AI research, Ollama+n8n workflows, private local RAG, and Docker Compose knowledge-base searches.
- Added explicit disambiguation against generic n8n starter kits, Open WebUI-only deployments, Llama Stack, Eclipse LMOS, and cloud-hosted agent platforms.
