#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cron-Job: Indexiert neue Dokumente aus inbox/."""
import sys
from pathlib import Path

# Adjust if KnowledgeDigest is installed elsewhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledgedigest.ingestor import DocumentIngestor

# Paths -- adjusted by install.sh
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledgedigest"
DB = DATA_DIR / "knowledge.db"
INBOX = DATA_DIR / "inbox"
ARCHIVE = DATA_DIR / "archive"


def main():
    if not INBOX.exists() or not any(INBOX.iterdir()):
        return  # Nothing to do
    ing = DocumentIngestor(DB)
    ing.inbox_dir = INBOX
    ing.archive_dir = ARCHIVE
    stats = ing.ingest_directory(INBOX)
    if stats:
        total = stats if isinstance(stats, int) else getattr(stats, 'processed', 0)
        print(f'[AUTO-INGEST] {total} documents processed')


if __name__ == '__main__':
    main()
