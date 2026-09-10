# Changelog

Released versions match the [Git tags](https://github.com/ellmos-ai/ellmos-stack/tags)
and the [GitHub releases](https://github.com/ellmos-ai/ellmos-stack/releases).

## Unreleased

- Enhanced repository discoverability (Pfad B), added umbrella (`open-bricks`), architecture, and security badges, introduced interactive Mermaid sequence diagrams for research ingestion pipelines, synchronized German README parity (stack catalog, liability notice), refreshed `llms.txt` verification timestamp, and added comprehensive metadata test suite [G 2026-09-10].
- Replaced the combined Rinnsal memory/task runtime with pinned USMC (`memory.curated`), GARDENER (`memory.organic`), and task-master (`tasks.default`) modules, kept KnowledgeDigest as `knowledge.search.default`, separated runtime state, retained `RINNSAL_TELEGRAM_TOKEN` only as a migration fallback, and verified 54/54 tests plus 27/27 offline release checks [2026-08-26].
- Added `pyproject.toml` configuration, harmonized code hygiene and import standards (PEP 8, ruff 0.4+), updated `llms.txt` verification timestamp (2026-08-14), and verified 52/52 pytest suite & 20/20 release gate rules [G 2026-08-14].
- Updated `llms.txt` verification timestamp (2026-07-27), verified 52/52 unittest suite passing, and completed technical hygiene check [2026-07-27].
- Updated `llms.txt` verification timestamp (2026-07-26), added Ecosystem badge to `README.md` / `README_de.md`, and performed discoverability audit [2026-07-26].
- Standardized Shields.io badges (Pytest 52 passed, LLM-Ready context, Python 3.10+), added GFM LLM Callout Notes to README and README_de, and verified `llms.txt` context index [2026-07-25].
- Added `STACK-MAP.md`, a derived composition blueprint that lists every part of the stack, its role, and its source, with the machine-readable manifest as the canonical source.
- Added a composition-at-a-glance tree to the README linking to that blueprint.
- Replaced the broken/unrelated `research-agent` dependency path with direct, tested PubMed E-utilities and arXiv Atom clients, including working source selection and safe inbox filenames.
- Made all service `.env` loading literal and shell-free, protected installed credentials with mode `0600`, and removed shell sourcing from cron and installer paths.
- Made the Telegram gateway fail closed when the owner chat ID is missing and made pre-ingestion summary cron runs exit cleanly when no database exists.
- Bound KnowledgeDigest to localhost by default and replaced the plaintext remote Ollama proxy example with a TLS-only example.
- Made the installer ignore generated service directories and fail explicitly when Ollama never becomes ready.
- Pinned Python component sources to exact commits, moved KnowledgeDigest/cron/Telegram runtime work to a restricted system user, and added a backup/restore/rollback runbook.
- Tightened release evidence with full version-tag validation, measured bindings, resolved OCI digests, and explicit security/restore attestations.
- Added a non-starting restore bootstrap, digest-based restore steps, generated custom-path Telegram units, and CI smokes against the exact pinned Rinnsal and KnowledgeDigest commits.
- Removed the remaining plain-HTTP public n8n suggestion; remote access now requires a reviewed TLS/authentication proxy, SSH tunnel, or private VPN.
- Normalized line endings via `.gitattributes` so `install.sh` and the other shell entry points always check out with LF, including in Windows clones.

## v0.1.0 — 2026-07-23

Public stack release gate baseline.

- Added a public-stack release gate with static repository/security checks, mandatory image pinning, and a manual Linux Docker Compose evidence workflow.
- Added bounded Telegram gateway context handling so long-running polling sessions keep only recent user/assistant turns.
- Hardened `install.sh` so `KD_PORT` is read only from an exact `.env` assignment.
- Ignored local `.pytest_cache/` artifacts and covered both hygiene rules in smoke tests.
- Sharpened README and `llms.txt` discovery anchors for self-hosted AI research, Ollama+n8n workflows, private local RAG, and Docker Compose knowledge-base searches.
- Added explicit disambiguation against generic n8n starter kits, Open WebUI-only deployments, Llama Stack, Eclipse LMOS, and cloud-hosted agent platforms.
