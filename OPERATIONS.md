# Backup, restore, and rollback

This runbook covers the state created by `install.sh`: stack configuration and
SQLite files under `/opt/ellmos-stack`, plus the n8n and Ollama Docker volumes.
Run it on the Linux host as root. Treat every backup as sensitive because it
contains `.env`, documents, workflow credentials, and conversation data.

## Before an upgrade

Record the exact application commit, tags, and resolved OCI digests. Keep the
release-gate evidence JSON with the backup when it is available:

```bash
cd /opt/ellmos-stack
git rev-parse HEAD 2>/dev/null || true
docker inspect n8n ollama --format '{{.Name}} {{.Config.Image}} {{.Image}}'
docker image inspect "$(docker inspect n8n --format '{{.Image}}')" --format '{{index .RepoDigests 0}}'
docker image inspect "$(docker inspect ollama --format '{{.Image}}')" --format '{{index .RepoDigests 0}}'
```

The installed `/opt/ellmos-stack` directory may not be a Git checkout. In that
case, record the commit from the source checkout used for installation.

## Consistent backup

Stop every writer before copying SQLite and volume state. The cron file is
disabled first so it cannot start a new writer during the backup.

```bash
set -euo pipefail
STACK_DIR=/opt/ellmos-stack
BACKUP_DIR=/var/backups/ellmos-stack/$(date -u +%Y%m%dT%H%M%SZ)
install -d -m 0700 "$BACKUP_DIR"

if [ -f /etc/cron.d/ellmos-stack ]; then
  mv /etc/cron.d/ellmos-stack /etc/cron.d/ellmos-stack.disabled
fi
systemctl stop telegram-gateway 2>/dev/null || true
systemctl stop knowledgedigest
cd "$STACK_DIR"
docker compose stop n8n ollama

N8N_VOLUME=$(docker inspect n8n --format '{{range .Mounts}}{{if eq .Destination "/home/node/.n8n"}}{{.Name}}{{end}}{{end}}')
OLLAMA_VOLUME=$(docker inspect ollama --format '{{range .Mounts}}{{if eq .Destination "/root/.ollama"}}{{.Name}}{{end}}{{end}}')
N8N_MOUNT=$(docker volume inspect "$N8N_VOLUME" --format '{{.Mountpoint}}')
OLLAMA_MOUNT=$(docker volume inspect "$OLLAMA_VOLUME" --format '{{.Mountpoint}}')

tar --numeric-owner -czf "$BACKUP_DIR/stack-files.tgz" -C "$STACK_DIR" .env config data
tar --numeric-owner -czf "$BACKUP_DIR/n8n-volume.tgz" -C "$N8N_MOUNT" .
tar --numeric-owner -czf "$BACKUP_DIR/ollama-volume.tgz" -C "$OLLAMA_MOUNT" .
sha256sum "$BACKUP_DIR"/*.tgz > "$BACKUP_DIR/SHA256SUMS.txt"
chmod 0600 "$BACKUP_DIR"/*
```

Copy the backup to encrypted offline storage before changing the deployment.
Then resume the unchanged stack if the upgrade is not starting immediately:

```bash
cd /opt/ellmos-stack
docker compose start ollama n8n
systemctl start knowledgedigest
systemctl start telegram-gateway 2>/dev/null || true
if [ -f /etc/cron.d/ellmos-stack.disabled ]; then
  mv /etc/cron.d/ellmos-stack.disabled /etc/cron.d/ellmos-stack
fi
```

## Restore rehearsal

Rehearse on a separate host or on newly created, empty volumes. Never extract a
backup over a running service or a non-empty production volume.

1. On a separate empty host, check out the recorded stack commit. Prepare its
   user, files, Python environment, units, and disabled cron without starting
   containers, pulling a model, or starting writers:

   ```bash
   sudo ./install.sh --prepare-only /opt/ellmos-stack
   ```

2. Verify the archive checksums with `sha256sum -c SHA256SUMS.txt`.
3. Extract `stack-files.tgz` into `/opt/ellmos-stack` and restore ownership:

   ```bash
   tar --numeric-owner -xzf stack-files.tgz -C /opt/ellmos-stack
   chown -R ellmos-stack:ellmos-stack /opt/ellmos-stack/data /opt/ellmos-stack/.env
   chmod 0600 /opt/ellmos-stack/.env
   ```

4. Set the recorded concrete tags in the restored `.env`. Pull the two recorded
   digest references, verify their `sha256` values against the evidence, and tag
   those exact local images with the recorded tag names used by Compose:

   ```bash
   docker pull "$OLLAMA_IMAGE_DIGEST"
   docker pull "$N8N_IMAGE_DIGEST"
   docker tag "$OLLAMA_IMAGE_DIGEST" "ollama/ollama:$OLLAMA_IMAGE_TAG"
   docker tag "$N8N_IMAGE_DIGEST" "n8nio/n8n:$N8N_IMAGE_TAG"
   cd /opt/ellmos-stack
   docker compose create
   ```

5. Use `docker inspect` and `docker volume inspect` as in the backup section to
   obtain the two fresh volume mountpoints. Require both to be empty before
   extracting `n8n-volume.tgz` and `ollama-volume.tgz`; abort if either command
   prints a path:

   ```bash
   find "$N8N_MOUNT" -mindepth 1 -print -quit
   find "$OLLAMA_MOUNT" -mindepth 1 -print -quit
   ```

6. Start the already-created Ollama and n8n containers, then KnowledgeDigest
   and the optional generated Telegram unit. Re-enable cron only after the
   service probes, digest readback, and data checks pass:

   ```bash
   docker compose start ollama n8n
   systemctl start knowledgedigest
   systemctl start telegram-gateway 2>/dev/null || true
   ```

Minimum readback:

```bash
curl --fail http://127.0.0.1:11434/api/version
curl --fail http://127.0.0.1:5678/healthz
curl --fail http://127.0.0.1:8787/
test -r /opt/ellmos-stack/data/knowledgedigest/knowledge.db
```

Also verify the n8n owner account, one representative workflow, one document
search, and any locally created Ollama model before calling the restore green.

## Rollback decision

If the upgraded commit or images fail, stop all writers, restore the backup on
the previously recorded commit and image versions, and repeat the readback.
Do not mix a newer SQLite/n8n state with older code unless that version's own
migration notes explicitly allow it. A successful backup is not a successful
rollback until the isolated restore rehearsal has passed.
