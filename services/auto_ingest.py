#!/usr/bin/env python3
"""Cron job: index new documents from inbox/."""
import sys
from pathlib import Path

# Adjust if KnowledgeDigest is installed elsewhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Paths -- adjusted by install.sh
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledgedigest"
DB = DATA_DIR / "knowledge.db"
INBOX = DATA_DIR / "inbox"
ARCHIVE = DATA_DIR / "archive"


def main() -> int:
    if not INBOX.exists() or not any(INBOX.iterdir()):
        return 0

    from KnowledgeDigest.ingestor import DocumentIngestor

    ingestor = DocumentIngestor(DB)
    ingestor.inbox_dir = INBOX
    ingestor.archive_dir = ARCHIVE
    try:
        stats = ingestor.ingest_directory(INBOX)
        if stats.get("error"):
            print(f"[AUTO-INGEST ERROR] {stats['error']}", file=sys.stderr)
            return 1
        ingested = int(stats.get("ingested", 0))
        errors = int(stats.get("errors", 0))
        if ingested:
            print(f"[AUTO-INGEST] {ingested} documents processed")
        if errors:
            print(f"[AUTO-INGEST ERROR] {errors} documents failed", file=sys.stderr)
            return 1
        return 0
    finally:
        ingestor.close()


if __name__ == '__main__':
    raise SystemExit(main())
