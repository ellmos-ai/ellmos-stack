# TODO: ellmos-stack

Stand: 2026-06-12 (Audit ergänzt, Altbestand vom 2026-06-01 unverändert erhalten)

## STATUS

| Category | Status | Notes |
|---|---|---|
| Release gate | open | Final Gate Check muss vor Veröffentlichung erneut grün laufen. |
| Runtime data | watched | `.env`, lokale Datenbanken, Inbox, Archive und Logs dürfen nicht getrackt werden. |
| Security | open | n8n ist seit 2026-06-12 auf `127.0.0.1` gebunden (Owner-Account-Setup dokumentiert); für produktive Internet-Nutzung brauchen n8n und KnowledgeDigest weiterhin Reverse Proxy, TLS und Firewall. |
| Documentation | open | README-Diagramme und deutschsprachige Texte später auf Encoding-Artefakte und öffentliche Lesbarkeit prüfen. |
| Tests | active | Lokaler Smoke-Test läuft ohne Docker, Ollama, Telegram oder Live-Dienste. |

## Nächste überschaubare Schritte

- [x] `README.md` und `README_de.md` gegen Mojibake-/Box-Zeichen-Artefakte prüfen und bei Bedarf mit ASCII-Diagrammen ersetzen. *(Geprüft im Audit 2026-06-12: keine Mojibake-Artefakte, UTF-8 sauber. Nur leichte Box-Zeichen-Versätze im Diagramm, siehe Audit → Änderungen.)*
- [ ] Eine kurze `RELEASE_GATE.md` anlegen, sobald der Final Gate Check ohne Fehler läuft. *(Stand 2026-06-12: existiert noch nicht.)*
- [ ] Produktive Exposition von n8n, KnowledgeDigest und optionalem Ollama-Proxy mit TLS-/Firewall-Hinweisen konkretisieren. *(Weiterhin offen, verschärft durch Basic-Auth-Befund im Audit 2026-06-12 → Fixes.)*
- [ ] Optionalen Docker-/Compose-Smoke-Test dokumentieren, der nur auf einem echten Linux-Zielserver läuft. *(Stand 2026-06-12: nicht vorhanden.)*

## Audit 2026-06-12

Vollaudit aller Root-Dateien, `services/`, `config/`, `tests/`, `docs/`, `examples/`, `.github/`. Keine Code-Änderungen vorgenommen, nur Befunde.

### Fixes

- [x] **[hoch] `docker-compose.yml` (Z. 33–35): n8n Basic Auth wirkungslos.** Die Variablen `N8N_BASIC_AUTH_ACTIVE/_USER/_PASSWORD` wurden in n8n v1.0 entfernt; mit `n8nio/n8n:latest` sind sie ohne Funktion. Folge: n8n ist auf `0.0.0.0:5678` OHNE Auth exponiert, bis jemand den Owner-Account anlegt — der Erstbesucher wird Owner. README (Abschnitt „Security Notes") und `llms.txt` behaupten fälschlich Basic-Auth-Schutz. *(erledigt 2026-06-12: tote Variablen entfernt, Port auf `127.0.0.1:5678` gebunden, Owner-Account-Setup via SSH-Tunnel in README/README_de dokumentiert inkl. Anleitung zum bewussten Öffnen, llms.txt korrigiert, Passwort-Generierung aus install.sh entfernt, `N8N_USER/N8N_PASSWORD` aus `.env.example` entfernt.)*
- [x] **[hoch] `install.sh` (Z. 30): Docker-Compose-Check fehlerhaft.** `command -v docker compose` prüft die zwei Befehle `docker` und `compose` einzeln; das Plugin-Subkommando `compose` existiert nie als Binary → Check schlägt auch bei korrekt installiertem Compose v2 fehl und bricht die Installation ab. *(erledigt 2026-06-12: `docker compose version`-Probe mit Fallback auf `docker-compose` v1, klare Fehlermeldung, Aufruf via `$COMPOSE up -d`.)*
- [x] **[hoch] Cron-Jobs laden `.env` nicht** (`install.sh` Z. 131–140, `config/cron.example`): `process_summaries.py` liest `KD_SUMMARY_PROVIDER`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, ggf. `ANTHROPIC_API_KEY` aus der Umgebung — die Cron-Umgebung enthält die `.env`-Werte aber nicht. *(erledigt 2026-06-12: `set -a; . <install-dir>/.env; set +a;` der `process_summaries.py`-Cron-Zeile in install.sh UND config/cron.example vorangestellt; `auto_ingest.py` liest keine Env-Variablen und braucht es nicht; `telegram_gateway.py` lädt `.env` bereits via systemd `EnvironmentFile`.)*
- [x] **[mittel] `install.sh` (Z. 4 vs. Z. 8): Usage-Doku widerspricht Implementierung.** Kommentar nennt `--install-dir /opt/ellmos-stack`, der Code nimmt aber `$1` positional. *(erledigt 2026-06-12: Kommentar auf `./install.sh [INSTALL_DIR]` geändert — kleinere, konsistente Lösung.)*
- [x] **[mittel] README.md (Z. 181) / README_de.md (Z. 181): Phantom-Cron-Job.** Architektur-Diagramm verspricht „*/5 min → ollama-service health (auto-restart if down)" — weder `install.sh` noch `config/cron.example` installieren einen Health-Check-Cron. *(erledigt 2026-06-12: Zeile aus beiden READMEs entfernt — Doku an Realität angeglichen; Compose-Healthchecks bleiben als Upgrade-Idee offen.)*
- **[mittel] `install.sh` (Z. 106): `grep KD_PORT .env`** matcht auch Kommentarzeilen und andere Variablen, die `KD_PORT` enthalten (z. B. künftiges `KD_PORT_INTERNAL`). Robuster: `grep -E '^KD_PORT=' …`.
- **[niedrig] `install.sh` (Z. 59): generiertes n8n-Passwort wird im Klartext auf stdout ausgegeben** und landet damit ggf. in Session-Logs/CI-Logs. Besser nur auf den Speicherort `.env` verweisen.
- **[niedrig] `install.sh` (Z. 99): `source .env`** bricht bei Werten mit Leerzeichen/Sonderzeichen ohne Quotes; mindestens in `.env.example` dokumentieren, dass Werte shell-safe sein müssen.
- **[niedrig] `services/telegram_gateway.py` (Z. 48, 287–289): unbegrenztes Wachstum von `_context`.** Die Liste wird nie beschnitten (nur beim Prompt-Bau auf `MAX_CONTEXT` begrenzt) — Memory-Leak im Dauerbetrieb des Daemons. Nach Append auf `_context = _context[-2*MAX_CONTEXT:]` kürzen.
- **[niedrig] `.gitignore`: `.pytest_cache/` fehlt.** Der Ordner existiert lokal bereits. Eintrag ergänzen.

### Upgrades

- [x] **[hoch] `docker-compose.yml`: Image-Tags pinnen.** `ollama/ollama:latest` und `n8nio/n8n:latest` sind nicht reproduzierbar und holen ungetestete Breaking Changes (n8n-Major-Releases!). *(erledigt 2026-06-12: Pinning per `OLLAMA_IMAGE_TAG`/`N8N_IMAGE_TAG` in `.env` steuerbar, Default `latest`; README/README_de/llms.txt dokumentieren, dass vor Produktivbetrieb auf getestete Versionen gepinnt werden soll. Bewusst keine konkreten Versionsnummern erfunden.)*
- [x] **[hoch] CI-Workflow für Tests fehlt.** *(erledigt 2026-06-12: war bereits remote gelöst — `origin/master` Commit `a0bda88` bringt `.github/workflows/tests.yml` (Python 3.10/3.11/3.12, unittest + compileall); per Fast-Forward übernommen.)*
- **[mittel] `docker-compose.yml`: Healthchecks ergänzen.** Weder ollama (`/api/version`) noch n8n (`/healthz`) haben einen `healthcheck:`; `depends_on` (Z. 37) könnte dann mit `condition: service_healthy` arbeiten. Ersetzt zugleich den im README versprochenen Health-Cron sauberer. *(Hinweis 2026-06-12: Phantom-Health-Cron-Zeile wurde aus den READMEs entfernt; Healthchecks bleiben sinnvolles Upgrade.)*
- [x] **[mittel] `.env.example`: `OLLAMA_BASE_URL` dokumentieren.** Wird von `research_pipeline.py`, `process_summaries.py` und `telegram_gateway.py` ausgewertet, fehlt aber in `.env.example` und der README-Konfigtabelle. *(erledigt 2026-06-12: in `.env.example` (auskommentiert mit Default) und in beiden README-Konfigtabellen ergänzt.)*
- [x] **[mittel] Telegram-Gateway in README aufnehmen.** `services/telegram_gateway.py` (13 KB, eigenes systemd-Unit `config/telegram-gateway.service`, eigene `.env`-Variablen) ist nur in `llms.txt` erwähnt. *(erledigt 2026-06-12: Komponententabelle + Use Case 7 mit Setup-Anleitung (Test, systemd-Unit-Installation) in README.md und README_de.md; `install.sh` installiert das Unit weiterhin bewusst nicht automatisch — optionaler manueller Schritt, da Token nötig.)*
- **[niedrig] `services/process_summaries.py`: fehlende DB abfangen.** Vor erster Ingestion existiert `knowledge.db` nicht → der 15-Minuten-Cron schreibt bis dahin alle 15 Min einen Traceback ins Log. Early-Exit wenn DB fehlt.
- **[niedrig] `tests/test_smoke.py` erweitern:** Konsistenz `.env.example` ↔ in Services genutzte Env-Variablen, `install.sh`-Syntaxcheck (`bash -n`), Vorhandensein von `config/telegram-gateway.service`, kein `N8N_BASIC_AUTH_*` mehr in compose (nach Fix).

### Änderungen

- **[hoch] Uncommittete Änderungen im Repo:** `services/telegram_gateway.py` und `.gitignore` sind modifiziert, `TODO.md` ist untracked (Stand 2026-06-12). Sichten, committen oder verwerfen — Release-Gate setzt sauberen Tree voraus. *(Teilstand 2026-06-12: TODO.md ist jetzt getrackt/committet; `.gitignore` (+`data/`) und `telegram_gateway.py` (1 Zeile) bewusst NICHT mitcommittet — bitte sichten. Lokaler Branch wurde per Fast-Forward auf `origin/master` gebracht.)*
- **[mittel] Leere Verzeichnisse `docs/` und `examples/n8n-workflows/`:** Beide sind leer (und damit auch nicht in Git). README-Use-Case 4 bewirbt n8n-Workflows — mindestens 1–2 Beispiel-Workflows (JSON-Export) nach `examples/n8n-workflows/` legen oder die Ordner entfernen.
- [x] **[mittel] README ↔ Realität „Basic Auth":** Sicherheitsabschnitte in README.md (Z. 259), README_de.md (Z. 259) und llms.txt (Z. 39) nach dem n8n-Auth-Fix (siehe Fixes) anpassen. *(erledigt 2026-06-12: alle drei Dateien beschreiben jetzt localhost-Binding + Owner-Account statt Basic Auth.)*
- **[niedrig] Stack-Familien-Tabelle (README „Stack Family"):** ellmos-research-stack / dev-stack / media-stack existieren nicht; explizit als „geplant/nicht verfügbar" markieren, damit keine toten Erwartungen entstehen.
- **[niedrig] Box-Diagramm-Ausrichtung:** In README.md/README_de.md (Z. 13–32) sind einzelne Rahmenlinien versetzt (z. B. Z. 22, 30). Kosmetisch; bei Gelegenheit nachziehen oder durch schlichtes ASCII ersetzen (deckt den Alt-Eintrag „Box-Zeichen-Artefakte" final ab).
- **[niedrig] `services/auto_ingest.py` (Z. 3) hat deutschen Docstring,** Rest der Service-Docstrings englisch — vereinheitlichen (öffentliches Repo, englisch bevorzugt).
