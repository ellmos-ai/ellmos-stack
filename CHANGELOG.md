# Changelog

Released versions match the [Git tags](https://github.com/ellmos-ai/ellmos-stack/tags)
and the [GitHub releases](https://github.com/ellmos-ai/ellmos-stack/releases).

## [0.1.1] - 2026-09-19

- **CI Matrix & Workflow Hardening**:
  - Expanded test matrix in `.github/workflows/tests.yml` to test across `ubuntu-latest` and `windows-latest` on Python 3.10, 3.11, 3.12, and 3.13.
  - Added least-privilege `permissions: contents: read`, `timeout-minutes: 15`, and `concurrency: { group: ..., cancel-in-progress: true }`.
  - Added integrated steps for `ruff check .`, `compileall -q services tests tools`, `pytest`, `unittest`, and `python tools/check_release_gate.py`.
  - Hardened `.github/workflows/stale.yml`, `welcome.yml`, `auto-assign.yml`, `label-sync.yml`, and `release-gate.yml` with timeouts and cancellation concurrency.
  - Corrected action versions to stable `actions/checkout@v4` and `actions/setup-python@v5`.
- **PEP 621 Standardisation**:
  - Bumped version to `0.1.1` in `pyproject.toml`.
  - Added `license-files = ["LICENSE", "THIRD_PARTY_LICENSES.md"]`.
  - Added standard PyPI classifiers for Python 3.10–3.13, MIT License, AI Topic, and System Setup.
  - Standardized `[project.urls]` including Documentation, Repository, Issues, Changelog, Third-Party Licenses, Parent Organization, Umbrella Ecosystem, LLM Ready, and Security.
- **Software Bill of Materials (SBOM) & Governance**:
  - Added `THIRD_PARTY_LICENSES.md` providing Level 1 SBOM documenting orchestration engines (Ollama, n8n, PostgreSQL), pinned stack modules (USMC, GARDENER, task-master, KnowledgeDigest), runtime libraries, and public literature APIs (PubMed, arXiv).
  - Codified `RunAsInvoker` non-elevation certification and 10 governance invariants (`INV-LOCAL-01` through `INV-SLA-10`).
- **Repository Hygiene & Multi-Host Protection**:
  - Hardened `.gitignore` to prevent tracking multi-host sync conflicts (`*conflicted copy*`, `*-ASUS*`, `*-WORKSTATION*`, etc.), lock system markers (`LOCK*`), and modern build caches (`.ruff_cache/`, `uv.lock`).
- **Documentation & LLM Context Parity**:
  - Refreshed `llms.txt` verification timestamp to 2026-09-19 and updated version references.
  - Synchronized Shields.io test suite and release badges across English and German README files.
- **Contract & Metadata Test Expansion**:
  - Expanded `tests/test_metadata.py` with comprehensive assertions validating PEP 621 metadata, CI workflow safety, SBOM presence, non-elevation invariant, and cross-file version synchronization.

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
