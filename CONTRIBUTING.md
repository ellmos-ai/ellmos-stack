# Contributing / Mitwirken

Thank you for your interest in contributing to **ellmos-stack**!
Vielen Dank für dein Interesse an Beiträgen zu **ellmos-stack**!

## Requirements / Voraussetzungen

- Python **3.10+** (CI matrix tests Python 3.10, 3.11, 3.12, and 3.13 across Ubuntu, Windows, and macOS)
- `PyYAML >= 6.0`, `pytest >= 7`, `ruff >= 0.4` (`pip install -e ".[dev]"`)
- Optional for Linux release gate verification: Docker, Docker Compose v2

## Development Workflow / Entwicklungsablauf

1. Fork or branch from `master` — never push directly to `master`.
2. Keep changes focused and preserve security invariants:
   - Localhost-only service bindings (`127.0.0.1`)
   - Shell-free `.env` parsing (`services/env_config.py`)
   - Pinned 40-character Git commits in `install.sh`
   - No tracked `.env`, secrets, databases (`*.db`), logs, or internal agent state
3. Update relevant documentation (`README.md`, `README_de.md`, `llms.txt`, `SKILL.md`, `CHANGELOG.md` under `## Unreleased`) when behavior or CLI flags change.

## Verification Before Opening a PR / Prüfung vor einem PR

```bash
ruff check .
python -m compileall -q services tests tools
python -m pytest -ra -v
python -m unittest discover -s tests -v
python tools/check_release_gate.py
python -m pip install --no-build-isolation --no-deps --dry-run .
```

## Standards / Standards

- Follow PEP 8 and keep `ruff check .` clean.
- Shell scripts (`install.sh`) must remain LF-normalized (`.gitattributes`).
- Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md); security disclosures follow [SECURITY.md](SECURITY.md).
