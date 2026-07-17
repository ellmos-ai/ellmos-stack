#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cron-Job: Processes 1 pending item from the KnowledgeDigest queue via Ollama."""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.env_config import load_env_file

load_env_file(REPO_ROOT / ".env")

DATA_DIR = REPO_ROOT / "data" / "knowledgedigest"
DB = DATA_DIR / "knowledge.db"

# Provider config from environment (defaults to local Ollama)
PROVIDER = os.environ.get("KD_SUMMARY_PROVIDER", "ollama")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")
BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

def main() -> int:
    """Process one queue item; stay silent before the first database exists."""

    if not DB.is_file():
        return 0

    from KnowledgeDigest.summarizer import Summarizer

    summarizer = Summarizer(
        DB,
        provider=PROVIDER,
        model=MODEL,
        base_url=BASE_URL,
    )
    try:
        stats = summarizer.summarize_queue(limit=1, delay=0)
        if stats.get("processed", 0) > 0:
            item = stats["items"][0]
            print(
                f"[OK] {item['source_type']}#{item['source_id']}: "
                f"{item['chunks_summarized']} Chunks, {stats['duration_ms']}ms"
            )
        elif stats.get("errors", 0) > 0:
            print(f"[ERR] {stats['errors']} errors")
            return 1
        return 0
    finally:
        summarizer.close()


if __name__ == "__main__":
    raise SystemExit(main())
