#!/usr/bin/env python3
"""Research pipeline: PubMed/arXiv search -> optional Ollama analysis -> inbox."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from itertools import zip_longest
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.env_config import load_env_file  # noqa: E402

load_env_file(REPO_ROOT / ".env")

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")
PROMPT_FILE = REPO_ROOT / "config" / "system_prompt.txt"
DATA_DIR = REPO_ROOT / "data" / "knowledgedigest"
USER_AGENT = "ellmos-stack/1.0 (+https://github.com/ellmos-ai/ellmos-stack)"
PUBMED_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ARXIV_API = "https://export.arxiv.org/api/query"


class Paper(NamedTuple):
    title: str
    abstract: str
    source: str
    url: str


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _request_text(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return _normalize_text("".join(element.itertext()))


def search_pubmed(query: str, max_results: int) -> list[Paper]:
    """Search PubMed through NCBI ESearch + EFetch."""

    search_params = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "tool": "ellmos-stack",
        }
    )
    search_data = json.loads(_request_text(f"{PUBMED_EUTILS}/esearch.fcgi?{search_params}"))
    identifiers = search_data.get("esearchresult", {}).get("idlist", [])
    if not identifiers:
        return []

    fetch_params = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "id": ",".join(identifiers),
            "retmode": "xml",
            "tool": "ellmos-stack",
        }
    )
    root = ET.fromstring(_request_text(f"{PUBMED_EUTILS}/efetch.fcgi?{fetch_params}"))
    papers: list[Paper] = []
    for item in root.findall(".//PubmedArticle"):
        pmid = _element_text(item.find(".//PMID"))
        title = _element_text(item.find(".//Article/ArticleTitle"))
        abstract_parts = [
            _element_text(part)
            for part in item.findall(".//Article/Abstract/AbstractText")
        ]
        abstract = _normalize_text(" ".join(part for part in abstract_parts if part))
        if title:
            papers.append(
                Paper(
                    title=title,
                    abstract=abstract,
                    source="pubmed",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                )
            )
    return papers[:max_results]


def search_arxiv(query: str, max_results: int) -> list[Paper]:
    """Search arXiv through its Atom API."""

    params = urllib.parse.urlencode(
        {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    )
    root = ET.fromstring(_request_text(f"{ARXIV_API}?{params}"))
    atom = {"atom": "http://www.w3.org/2005/Atom"}
    papers: list[Paper] = []
    for entry in root.findall("atom:entry", atom):
        title = _element_text(entry.find("atom:title", atom))
        if not title:
            continue
        entry_url = _element_text(entry.find("atom:id", atom)).replace(
            "http://arxiv.org/", "https://arxiv.org/", 1
        )
        papers.append(
            Paper(
                title=title,
                abstract=_element_text(entry.find("atom:summary", atom)),
                source="arxiv",
                url=entry_url,
            )
        )
    return papers[:max_results]


def search_papers(query: str, max_results: int = 10, source: str = "all") -> list[Paper]:
    """Search selected official literature APIs and return at most max_results."""

    if source not in {"all", "pubmed", "arxiv"}:
        raise ValueError(f"unsupported source: {source}")

    by_source: dict[str, list[Paper]] = {"pubmed": [], "arxiv": []}
    searches = []
    if source in {"all", "pubmed"}:
        searches.append(("pubmed", search_pubmed))
    if source in {"all", "arxiv"}:
        searches.append(("arxiv", search_arxiv))

    for name, search in searches:
        try:
            by_source[name] = search(query, max_results)
        except (OSError, TimeoutError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
            print(f"[WARN] {name} search failed: {type(exc).__name__}", file=sys.stderr)

    if source != "all":
        return by_source[source][:max_results]

    combined: list[Paper] = []
    seen: set[tuple[str, str]] = set()
    for pair in zip_longest(by_source["pubmed"], by_source["arxiv"]):
        for paper in pair:
            if paper is None:
                continue
            key = (paper.url.lower(), paper.title.lower())
            if key in seen:
                continue
            seen.add(key)
            combined.append(paper)
            if len(combined) == max_results:
                return combined
    return combined


def ollama_generate(prompt: str, system: str = "") -> str:
    """Call the local Ollama API."""

    if not system and PROMPT_FILE.exists():
        system = PROMPT_FILE.read_text(encoding="utf-8").strip()

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"/no_think\n{prompt}" if "qwen" in OLLAMA_MODEL.lower() else prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.3},
    }
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result.get("response", "").strip()


def safe_report_filename(
    query: str, now: datetime | None = None, unique_suffix: str | None = None
) -> str:
    """Create a portable inbox filename without path separators or dot segments."""

    timestamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", query).strip("_")[:40] or "query"
    suffix = unique_suffix or secrets.token_hex(4)
    return f"research_{timestamp}_{slug}_{suffix}.md"


def save_report(report: str, inbox: Path, query: str) -> Path:
    """Create a new report atomically with respect to filename collisions."""

    inbox.mkdir(parents=True, exist_ok=True)
    destination = inbox / safe_report_filename(query)
    with destination.open("x", encoding="utf-8") as handle:
        handle.write(report)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Research Pipeline")
    parser.add_argument("query", help="Research query")
    parser.add_argument("--papers", type=int, default=10, help="Maximum papers to fetch")
    parser.add_argument(
        "--source", choices=("all", "pubmed", "arxiv"), default="all", help="Search source"
    )
    parser.add_argument("--summarize", action="store_true", help="Summarize via Ollama")
    parser.add_argument("--save", action="store_true", help="Save to KnowledgeDigest inbox")
    args = parser.parse_args()
    if args.papers < 1:
        parser.error("--papers must be at least 1")

    print(f"[1/3] Searching: {args.query}")
    papers = search_papers(args.query, args.papers, args.source)
    print(f"      Found {len(papers)} papers")

    report_lines = [
        f"# Research Report: {args.query}\n",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"Papers found: {len(papers)}\n\n",
    ]
    for index, paper in enumerate(papers, 1):
        report_lines.append(f"## {index}. {paper.title}\n")
        report_lines.append(f"Source: {paper.source}")
        if paper.url:
            report_lines.append(f" — {paper.url}")
        report_lines.append("\n\n")
        if paper.abstract:
            report_lines.append(f"{paper.abstract[:1000]}\n\n")

    if args.summarize and papers:
        print("[2/3] Analyzing with Ollama...")
        combined = "".join(report_lines)
        analysis = ollama_generate(
            "Analysiere diese Forschungsergebnisse und fasse die wichtigsten "
            f"Erkenntnisse zusammen:\n\n{combined[:6000]}"
        )
        report_lines.append(f"\n## Analysis\n{analysis}\n")
        print("      Done")
    else:
        print("[2/3] Skipping analysis")

    report = "".join(report_lines)
    if args.save:
        print("[3/3] Saving to KnowledgeDigest inbox...")
        inbox = DATA_DIR / "inbox"
        destination = save_report(report, inbox, args.query)
        print(f"      Saved: {destination.name}")
    else:
        print("[3/3] Output:")
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
