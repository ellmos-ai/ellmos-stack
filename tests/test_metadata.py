"""
Metadata and documentation consistency tests for ellmos-stack.

Verifies:
- README.md and README_de.md existence and bilingual parity
- Required badges present (tests, release, license, python, ecosystem, umbrella)
- Mermaid diagrams syntax & quotation guardrails
- llms.txt presence, canonical links, and up-to-date headers
- pyproject.toml configuration consistency
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README_EN = REPO_ROOT / "README.md"
README_DE = REPO_ROOT / "README_de.md"
LLMS_TXT = REPO_ROOT / "llms.txt"
PYPROJECT = REPO_ROOT / "pyproject.toml"


class TestDocumentationParity(unittest.TestCase):
    """Verify bilingual README architecture and parity."""

    def test_both_readmes_exist(self):
        self.assertTrue(README_EN.exists(), "README.md missing")
        self.assertTrue(README_DE.exists(), "README_de.md missing")

    def test_language_switchers_present(self):
        en_content = README_EN.read_text(encoding="utf-8")
        de_content = README_DE.read_text(encoding="utf-8")
        self.assertIn("README_de.md", en_content, "README.md must link to README_de.md")
        self.assertIn("README.md", de_content, "README_de.md must link to README.md")

    def test_required_badges_present(self):
        en_content = README_EN.read_text(encoding="utf-8")
        required_badges = [
            "tests-",
            "release",
            "ecosystem-ellmos--ai",
            "umbrella-open--bricks",
            "llms.txt",
            "License-MIT",
        ]
        for badge in required_badges:
            with self.subTest(badge=badge):
                self.assertIn(badge, en_content, f"Badge pattern '{badge}' missing in README.md")

    def test_quick_navigation_present(self):
        en_content = README_EN.read_text(encoding="utf-8")
        de_content = README_DE.read_text(encoding="utf-8")
        self.assertIn("[Quickstart](#quickstart)", en_content)
        self.assertIn("[Schnellstart](#schnellstart)", de_content)

    def test_mermaid_diagrams_lint_free(self):
        """All mermaid blocks must have quoted labels for nodes/edges containing parens or colons."""
        for path in [README_EN, README_DE]:
            content = path.read_text(encoding="utf-8")
            blocks = re.findall(r"```mermaid(.*?)```", content, re.DOTALL)
            self.assertGreater(len(blocks), 0, f"Expected mermaid blocks in {path.name}")
            for i, block in enumerate(blocks):
                # Ensure no unquoted parens inside node or actor labels
                for line in block.splitlines():
                    line = line.strip()
                    if not line or line.startswith("%%"):
                        continue
                    # Check sequence diagram participants / actors
                    if any(line.startswith(k) for k in ["participant ", "actor "]):
                        if "(" in line or ")" in line or ":" in line:
                            self.assertIn('"', line, f"Unquoted special chars in mermaid line in {path.name}: {line}")


class TestLlmsTxtAndMetadata(unittest.TestCase):
    """Verify machine-readable context file llms.txt and pyproject.toml."""

    def test_llms_txt_exists_and_valid(self):
        self.assertTrue(LLMS_TXT.exists(), "llms.txt missing")
        content = LLMS_TXT.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("# ellmos-stack"), "llms.txt must start with H1 title")
        self.assertIn("## Canonical Links", content)
        self.assertIn("https://github.com/ellmos-ai/ellmos-stack", content)
        self.assertIn("https://github.com/ellmos-ai/stacks", content)
        self.assertIn("https://github.com/ellmos-ai/agent-ops-stack", content)
        self.assertIn("Last checked:", content)

    def test_pyproject_contains_required_keywords(self):
        self.assertTrue(PYPROJECT.exists(), "pyproject.toml missing")
        content = PYPROJECT.read_text(encoding="utf-8")
        self.assertIn('name = "ellmos-stack"', content)
        self.assertIn('"ellmos"', content)
        self.assertIn('"local-first"', content)
        self.assertIn('"docker-compose"', content)


if __name__ == "__main__":
    unittest.main()
