"""Small, shell-free loader for ellmos-stack ``.env`` files."""

from __future__ import annotations

import os
import re
from pathlib import Path


_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_env_file(path: Path) -> set[str]:
    """Load literal KEY=VALUE pairs without expansion or command execution.

    Existing process variables win over file values. Single or double quotes
    surrounding the complete value are removed; all other characters remain
    literal. Invalid lines are ignored so comments and empty lines are safe.
    """

    loaded: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return loaded

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, value = line.split("=", 1)
        key = key.strip()
        if not _KEY.fullmatch(key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key not in os.environ:
            os.environ[key] = value
            loaded.add(key)
    return loaded
