#!/usr/bin/env python3
"""Static and evidence checks for the public ellmos-stack release gate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    ".env.example",
    ".gitignore",
    "CHANGELOG.md",
    "LICENSE",
    "README.md",
    "README_de.md",
    "RELEASE_GATE.md",
    "docker-compose.yml",
    "llms.txt",
    "stack.v2.json",
)
FORBIDDEN_TRACKED_PARTS = (
    "/data/",
    "/inbox/",
    "/archive/",
    "/.release-gate/",
)
FORBIDDEN_TRACKED_SUFFIXES = (".db", ".log", ".key", ".pem", ".secret")
EVIDENCE_KEYS = (
    "platform_linux",
    "compose_config_valid",
    "services_started",
    "ollama_ready",
    "n8n_ready",
    "bindings_localhost",
)


class Gate:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.ok: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        (self.ok if condition else self.errors).append(message)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency message only
        raise RuntimeError("PyYAML is required: python -m pip install PyYAML") from exc
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def check_static(gate: Gate) -> None:
    missing = [name for name in REQUIRED_FILES if not (REPO_ROOT / name).is_file()]
    gate.require(not missing, f"required release files present (missing: {missing})")

    manifest = _load_json(REPO_ROOT / "stack.v2.json")
    gate.require(manifest.get("schema") == "ellmos.stack.v2", "manifest schema is ellmos.stack.v2")
    gate.require(manifest.get("id") == "ellmos-stack", "manifest id is ellmos-stack")
    gate.require(manifest.get("visibility") == "public", "manifest visibility is public")
    policies = manifest.get("policies", {})
    gate.require("linux" in policies.get("platforms", []), "manifest declares Linux platform")
    gate.require(policies.get("local_first") is True, "manifest declares local-first operation")
    release_gate = manifest.get("release_gate", {})
    gate.require(release_gate.get("document") == "RELEASE_GATE.md", "manifest links release gate document")
    gate.require(release_gate.get("requires_pinned_images") is True, "manifest requires pinned images")

    compose = _load_yaml(REPO_ROOT / "docker-compose.yml")
    services = compose.get("services", {})
    ollama = services.get("ollama", {})
    n8n = services.get("n8n", {})
    gate.require("${OLLAMA_IMAGE_TAG:-latest}" in ollama.get("image", ""), "Ollama tag is configurable")
    gate.require("${N8N_IMAGE_TAG:-latest}" in n8n.get("image", ""), "n8n tag is configurable")
    ollama_ports = " ".join(str(item) for item in ollama.get("ports", []))
    n8n_ports = " ".join(str(item) for item in n8n.get("ports", []))
    gate.require("127.0.0.1:11434:11434" in ollama_ports, "Ollama is bound to localhost")
    gate.require("127.0.0.1:5678:5678" in n8n_ports, "n8n is bound to localhost")

    docs = "\n".join(
        (REPO_ROOT / name).read_text(encoding="utf-8").lower()
        for name in ("README.md", "README_de.md", "RELEASE_GATE.md", "llms.txt")
    )
    for marker in ("owner account", "tls", "firewall", "latest", "release_gate.md"):
        gate.require(marker in docs, f"release/security documentation contains '{marker}'")

    tracked = [f"/{name.replace(chr(92), '/')}" for name in _tracked_files()]
    forbidden = [
        name
        for name in tracked
        if name.lower() == "/.env"
        or any(part in name.lower() for part in FORBIDDEN_TRACKED_PARTS)
        or name.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES)
    ]
    gate.require(not forbidden, f"no forbidden secrets/runtime data tracked (found: {forbidden})")


def check_release_inputs(gate: Gate, ollama_tag: str, n8n_tag: str) -> None:
    for label, tag in (("OLLAMA_IMAGE_TAG", ollama_tag), ("N8N_IMAGE_TAG", n8n_tag)):
        normalized = tag.strip().lower()
        gate.require(bool(normalized), f"{label} is set")
        gate.require(normalized not in {"latest", "stable", "nightly", "main", "master"}, f"{label} is immutable enough for a release smoke")


def check_evidence(gate: Gate, evidence_path: Path) -> None:
    evidence = _load_json(evidence_path)
    for key in EVIDENCE_KEYS:
        gate.require(evidence.get(key) is True, f"Linux evidence confirms {key}")
    gate.require(bool(evidence.get("ollama_image")), "Linux evidence records Ollama image")
    gate.require(bool(evidence.get("n8n_image")), "Linux evidence records n8n image")
    gate.require(bool(evidence.get("commit")), "Linux evidence records commit")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", action="store_true", help="also require pinned release image tags")
    parser.add_argument("--preflight", action="store_true", help="allow release checks before Linux evidence exists")
    parser.add_argument("--evidence", type=Path, help="Linux Docker/Compose evidence JSON")
    parser.add_argument("--ollama-tag", default=os.environ.get("OLLAMA_IMAGE_TAG", ""))
    parser.add_argument("--n8n-tag", default=os.environ.get("N8N_IMAGE_TAG", ""))
    args = parser.parse_args(argv)

    gate = Gate()
    try:
        check_static(gate)
        if args.release:
            check_release_inputs(gate, args.ollama_tag, args.n8n_tag)
            gate.require(args.preflight or args.evidence is not None, "release run includes Linux evidence or is explicitly preflight")
        if args.evidence:
            check_evidence(gate, args.evidence)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        gate.errors.append(str(exc))

    for message in gate.ok:
        print(f"[OK] {message}")
    for message in gate.errors:
        print(f"[ERROR] {message}", file=sys.stderr)
    print(f"Release gate: {len(gate.ok)} passed, {len(gate.errors)} failed")
    return 1 if gate.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
