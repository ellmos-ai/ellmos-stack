#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Research Pipeline: Search -> Analyze -> Store

Combines ResearchAgent (PubMed/arXiv search) with Ollama (analysis)
and KnowledgeDigest (storage/indexing).

Usage:
    python research_pipeline.py "dark matter detection methods" --papers 10 --summarize --save
    python research_pipeline.py "CRISPR gene therapy" --source pubmed --papers 5
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

# Adjust if installed elsewhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")
PROMPT_FILE = Path(__file__).resolve().parent.parent / "config" / "system_prompt.txt"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledgedigest"


def ollama_generate(prompt: str, system: str = "") -> str:
    """Call Ollama API directly (zero-dep)."""
    if not system and PROMPT_FILE.exists():
        system = PROMPT_FILE.read_text(encoding="utf-8").strip()

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"/no_think\n{prompt}" if "qwen" in OLLAMA_MODEL.lower() else prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.3},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result.get("response", "").strip()


def search_papers(query: str, max_results: int = 10, source: str = "all"):
    """Search via ResearchAgent if available, else return empty."""
    try:
        from research_agent import ResearchAgent
        agent = ResearchAgent()
        result = agent.search(query, max_results=max_results)
        return result.top_articles if hasattr(result, 'top_articles') else []
    except ImportError:
        print("[WARN] ResearchAgent not installed. Install with: pip install research-agent")
        return []


def main():
    parser = argparse.ArgumentParser(description="Research Pipeline")
    parser.add_argument("query", help="Research query")
    parser.add_argument("--papers", type=int, default=10, help="Max papers to fetch")
    parser.add_argument("--source", default="all", help="Source: all, pubmed, arxiv")
    parser.add_argument("--summarize", action="store_true", help="Summarize via Ollama")
    parser.add_argument("--save", action="store_true", help="Save to KnowledgeDigest inbox")
    args = parser.parse_args()

    print(f"[1/3] Searching: {args.query}")
    papers = search_papers(args.query, args.papers, args.source)
    print(f"      Found {len(papers)} papers")

    report_lines = [f"# Research Report: {args.query}\n",
                    f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
                    f"Papers found: {len(papers)}\n\n"]

    for i, paper in enumerate(papers, 1):
        title = getattr(paper, 'title', str(paper))
        abstract = getattr(paper, 'abstract', '')
        report_lines.append(f"## {i}. {title}\n")
        if abstract:
            report_lines.append(f"{abstract[:500]}\n\n")

    if args.summarize and papers:
        print("[2/3] Analyzing with Ollama...")
        combined = "\n".join(report_lines)
        analysis = ollama_generate(
            f"Analysiere diese Forschungsergebnisse und fasse die wichtigsten "
            f"Erkenntnisse zusammen:\n\n{combined[:3000]}"
        )
        report_lines.append(f"\n## Analysis\n{analysis}\n")
        print("      Done")
    else:
        print("[2/3] Skipping analysis")

    report = "".join(report_lines)

    if args.save:
        print("[3/3] Saving to KnowledgeDigest inbox...")
        inbox = DATA_DIR / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        filename = f"research_{datetime.now().strftime('%Y%m%d_%H%M')}_{args.query[:30].replace(' ', '_')}.md"
        (inbox / filename).write_text(report, encoding="utf-8")
        print(f"      Saved: {filename}")
    else:
        print("[3/3] Output:")
        print(report)


if __name__ == "__main__":
    main()
