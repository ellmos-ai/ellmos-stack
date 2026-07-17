# Public stack release gate

This repository is a deployable composition, not a single Python package. A release is green only when the stack-level gates below pass for one exact commit and exact container tags.

## Ownership and order

The release operator owns the gate record. Run the gates in order; do not publish a tag or update an external stack catalog from a partial result.

1. **Repository gate:** clean intended diff, MIT license, public `ellmos.stack.v2` manifest, no tracked secrets or runtime data.
2. **Offline gate:** Python compilation, unit/smoke tests, manifest, Compose structure, localhost bindings, and documentation checks.
3. **Reproducibility gate:** set full concrete version tags for `OLLAMA_IMAGE_TAG` and `N8N_IMAGE_TAG`. Floating names, branch names, partial versions, and empty values are rejected; the Linux run records the resolved OCI digests.
4. **Linux Docker/Compose gate:** on GitHub's Linux runner, render the Compose file, start both pinned images, prove the Ollama and n8n health endpoints respond, measure localhost bindings, and record resolved image digests.
5. **Security and recovery review gate:** create the n8n owner account before exposure; keep n8n, Ollama, and KnowledgeDigest on localhost unless a reviewed TLS/authentication reverse proxy is present; review `.env` without committing it; rehearse the matching [`OPERATIONS.md`](OPERATIONS.md) restore path.
6. **Release decision:** only after all evidence is green may a version tag or public catalog status be changed.

## Local/offline preflight

```bash
PYTHONIOENCODING=utf-8 python -m pip install PyYAML
PYTHONIOENCODING=utf-8 python -m compileall -q services tests tools
PYTHONIOENCODING=utf-8 python -m unittest discover -s tests -v
PYTHONIOENCODING=utf-8 python tools/check_release_gate.py
```

This proves repository structure and offline behavior. It does not claim that Docker, Linux networking, or the service startup path worked.

## Linux evidence workflow

Run the manual GitHub Actions workflow **Public stack release gate**. Its inputs are exact Ollama and n8n image tags. The workflow:

- repeats the offline checks on Linux;
- installs the exact Rinnsal and KnowledgeDigest commits from `install.sh` and smokes their real entrypoints and APIs;
- rejects floating image tags;
- runs `docker compose config` with the selected tags;
- starts Ollama and n8n, probes their local health endpoints, and records the commit and images;
- validates and uploads `release-gate-evidence.json`;
- always tears down containers and volumes.

The operator must also attest the owner-account, external-access, and restore-rehearsal checks. The uploaded evidence records the reviewer, time, resolved image digests, workflow run, and commit. Re-run the gate whenever the commit, either image, or any attested target condition changes.

## Security checklist

- [ ] `.env`, tokens, keys, databases, logs, inboxes, archives, and `.release-gate/` are untracked.
- [ ] Ollama remains bound to `127.0.0.1:11434`.
- [ ] n8n remains bound to `127.0.0.1:5678` during first start.
- [ ] The n8n owner account exists before any external route is enabled.
- [ ] External n8n, KnowledgeDigest, or Ollama access uses reviewed TLS, authentication, and firewall rules.
- [ ] The backup, isolated restore rehearsal, and rollback instructions in `OPERATIONS.md` are reviewed for the exact component versions.

## Stop states

- **Offline green:** safe to review and push; not sufficient for a release.
- **Linux green:** technical release evidence exists; publication is still a separate explicit action.
- **Blocked:** any floating image, failed probe, missing owner-account/TLS/firewall review, dirty intended release diff, or tracked private data.
