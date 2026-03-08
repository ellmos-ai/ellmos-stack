#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cron-Job: Processes 1 pending item from the KnowledgeDigest queue via Ollama."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledgedigest.summarizer import Summarizer

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledgedigest"
DB = DATA_DIR / "knowledge.db"

# Provider config from environment (defaults to local Ollama)
PROVIDER = os.environ.get("KD_SUMMARY_PROVIDER", "ollama")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")
BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

s = Summarizer(
    DB,
    provider=PROVIDER,
    model=MODEL,
    base_url=BASE_URL,
)

stats = s.summarize_queue(limit=1, delay=0)
if stats.get('processed', 0) > 0:
    item = stats['items'][0]
    print(f"[OK] {item['source_type']}#{item['source_id']}: "
          f"{item['chunks_summarized']} Chunks, "
          f"{stats['duration_ms']}ms")
elif stats.get('errors', 0) > 0:
    print(f"[ERR] {stats['errors']} errors")
# No output when queue is empty (silent cron execution)
s.close()
