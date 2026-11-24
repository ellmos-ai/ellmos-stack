"""
Metadata and documentation consistency tests for ellmos-stack.

Verifies:
- README.md and README_de.md (plus all 11 locale editions) existence and parity
- Required badges present (tests, release, license, python, ecosystem, umbrella)
- Mermaid diagrams syntax & quotation guardrails
- llms.txt, llm.txt, and SKILL.md (P-022) presence, canonical links, and headers
- PEP 621/639 pyproject.toml configuration consistency (no conflicting OSI license classifier)
- CI matrix hardening and pytest basetemp CWD safety (T-20261114-932985855)
"""
import re
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
README_EN = REPO_ROOT / "README.md"
README_DE = REPO_ROOT / "README_de.md"
LLMS_TXT = REPO_ROOT / "llms.txt"
LLM_TXT = REPO_ROOT / "llm.txt"
SKILL_MD = REPO_ROOT / "SKILL.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
ALL_READMES = (
    "README.md",
    "README_de.md",
    "README_ar.md",
    "README_bn.md",
    "README_es.md",
    "README_fr.md",
    "README_hi.md",
    "README_ja.md",
    "README_pt.md",
    "README_ru.md",
    "README_zh.md",
)


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
            for block in blocks:
                for line in block.splitlines():
                    line = line.strip()
                    if not line or line.startswith("%%"):
                        continue
                    if any(line.startswith(k) for k in ["participant ", "actor "]):
                        if "(" in line or ")" in line or ":" in line:
                            self.assertIn('"', line, f"Unquoted special chars in mermaid line in {path.name}: {line}")

    def test_all_eleven_readmes_sync_validation_and_test_badge(self):
        """All 11 README editions must exist, show the current badge, and include Python 3.13."""
        for filename in ALL_READMES:
            path = REPO_ROOT / filename
            with self.subTest(readme=filename):
                self.assertTrue(path.is_file(), f"{filename} missing")
                text = path.read_text(encoding="utf-8")
                self.assertRegex(
                    text,
                    r"badge/[^)\s]+-72%20",
                    f"{filename} test badge must reflect 72 tests",
                )
                self.assertIn("3.13", text, f"{filename} must document Python 3.13 support")


class TestLlmsTxtAndMetadata(unittest.TestCase):
    """Verify machine-readable context files (P-022) and pyproject.toml."""

    def test_llms_txt_exists_and_valid(self):
        self.assertTrue(LLMS_TXT.exists(), "llms.txt missing")
        content = LLMS_TXT.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("# ellmos-stack"), "llms.txt must start with H1 title")
        self.assertIn("## Canonical Links", content)
        self.assertIn("https://github.com/ellmos-ai/ellmos-stack", content)
        self.assertIn("https://github.com/ellmos-ai/stacks", content)
        self.assertIn("https://github.com/ellmos-ai/agent-ops-stack", content)
        self.assertIn("SKILL.md", content)
        self.assertIn("Last checked:", content)

    def test_p022_llm_entrypoints_present(self):
        self.assertTrue(SKILL_MD.is_file(), "SKILL.md missing")
        self.assertTrue(LLM_TXT.is_file(), "llm.txt missing")
        skill_text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("name: ellmos-stack", skill_text)
        self.assertIn("services/research_pipeline.py", skill_text)
        self.assertIn("tools/check_release_gate.py", skill_text)

        llm_text = LLM_TXT.read_text(encoding="utf-8")
        self.assertIn("llms.txt", llm_text)
        self.assertIn("SKILL.md", llm_text)

        en_text = README_EN.read_text(encoding="utf-8")
        de_text = README_DE.read_text(encoding="utf-8")
        self.assertIn("Install with your LLM", en_text)
        self.assertIn("Mit deinem LLM installieren", de_text)
        self.assertIn("```text", en_text)
        self.assertIn("```text", de_text)
        self.assertIn("SKILL.md", en_text)
        self.assertIn("SKILL.md", de_text)

    def test_pyproject_contains_required_keywords(self):
        self.assertTrue(PYPROJECT.exists(), "pyproject.toml missing")
        content = PYPROJECT.read_text(encoding="utf-8")
        self.assertIn('name = "ellmos-stack"', content)
        self.assertIn('"ellmos"', content)
        self.assertIn('"local-first"', content)
        self.assertIn('"docker-compose"', content)


class TestPEP621AndSBOM(unittest.TestCase):
    """Verify PEP 621/639 metadata standards, SBOM, governance docs, and RunAsInvoker."""

    def test_pep621_specification(self):
        content = PYPROJECT.read_text(encoding="utf-8")
        data = tomllib.loads(content)
        project = data["project"]
        self.assertEqual(project["version"], "0.1.1")
        self.assertEqual(project["license"], "MIT")
        self.assertEqual(project["license-files"], ["LICENSE", "THIRD_PARTY_LICENSES.md"])
        self.assertIn("Programming Language :: Python :: 3.10", project["classifiers"])
        self.assertIn("Programming Language :: Python :: 3.13", project["classifiers"])
        self.assertFalse(
            any(c.startswith("License :: OSI Approved ::") for c in project["classifiers"]),
            "PEP 639 string license must not be paired with an OSI License classifier",
        )
        self.assertIn("services*", data["tool"]["setuptools"]["packages"]["find"]["include"])

        required_urls = [
            "Homepage",
            "Repository",
            "Issues",
            "Documentation",
            "Changelog",
            "Contributing",
            "Code of Conduct",
            "Third-Party Licenses",
            "Parent Organization",
            "Umbrella Ecosystem",
            "LLM Ready",
            "Security",
        ]
        for url_key in required_urls:
            with self.subTest(url_key=url_key):
                self.assertIn(url_key, project["urls"])

    def test_no_relative_basetemp_in_pytest_config(self):
        data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        pytest_cfg = data["tool"]["pytest"]["ini_options"]
        addopts = pytest_cfg.get("addopts", "")
        self.assertNotIn("--basetemp=.", addopts)
        self.assertNotIn("--basetemp .", addopts)
        self.assertEqual(pytest_cfg.get("asyncio_default_fixture_loop_scope"), "function")
        self.assertIn(".pytest_temp", pytest_cfg.get("norecursedirs", []))

    def test_third_party_licenses_sbom_exists(self):
        sbom_file = REPO_ROOT / "THIRD_PARTY_LICENSES.md"
        self.assertTrue(sbom_file.exists(), "THIRD_PARTY_LICENSES.md missing")
        content = sbom_file.read_text(encoding="utf-8")
        self.assertIn("Level 1 SBOM", content)
        self.assertIn("RunAsInvoker", content)
        self.assertIn("Ollama", content)
        self.assertIn("n8n", content)
        self.assertIn("USMC", content)
        self.assertIn("GARDENER", content)
        self.assertIn("task-master", content)
        self.assertIn("KnowledgeDigest", content)
        for i in range(1, 11):
            inv_id = f"INV-LOCAL-{i:02d}" if i <= 9 else "INV-SLA-10"
            with self.subTest(invariant=inv_id):
                self.assertIn(inv_id, content, f"Invariant {inv_id} missing in SBOM")

    def test_governance_docs_and_templates_present(self):
        for rel in (
            "CODE_OF_CONDUCT.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "MANIFEST.in",
            ".github/dependabot.yml",
            ".github/ISSUE_TEMPLATE/config.yml",
            ".github/ISSUE_TEMPLATE/bug_report.md",
            ".github/ISSUE_TEMPLATE/feature_request.md",
        ):
            with self.subTest(path=rel):
                self.assertTrue((REPO_ROOT / rel).is_file(), f"Missing {rel}")
        coc = (REPO_ROOT / "CODE_OF_CONDUCT.md").read_text(encoding="utf-8")
        self.assertNotIn("lukas@geiger.sh", coc)

    def test_gitignore_patterns(self):
        gitignore_file = REPO_ROOT / ".gitignore"
        self.assertTrue(gitignore_file.exists(), ".gitignore missing")
        content = gitignore_file.read_text(encoding="utf-8")
        required_patterns = [
            "LOCK",
            "LOCK.*",
            "LOCK*.txt",
            "LOCK.user.*",
            "*conflicted copy*",
            "*-ASUS*",
            "*-WORKSTATION*",
            ".pytest_cache/",
            ".pytest_temp/",
            ".ruff_cache/",
            "*MARKETING-LOG.txt",
            "TO-DECIDE-USER*",
            "TASKPLAN_*.md",
            "uv.lock",
        ]
        for pattern in required_patterns:
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, content, f"Pattern {pattern} missing in .gitignore")

    def test_bilingual_liability_disclaimer(self):
        """Both README files must feature § 521 BGB statutory liability exclusion."""
        en_content = README_EN.read_text(encoding="utf-8")
        de_content = README_DE.read_text(encoding="utf-8")
        self.assertIn("521 BGB", en_content)
        self.assertIn("521 BGB", de_content)

    def test_version_cross_file_consistency(self):
        pyproject_content = PYPROJECT.read_text(encoding="utf-8")
        changelog_content = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        llms_content = LLMS_TXT.read_text(encoding="utf-8")

        self.assertIn('version = "0.1.1"', pyproject_content)
        self.assertIn("## [0.1.1] - 2026-09-19", changelog_content)
        self.assertIn("v0.1.1 (2026-09-19)", llms_content)
        self.assertIn("Last checked: 2026-11-24", llms_content)


class TestCIWorkflowHardening(unittest.TestCase):
    """Verify GitHub Actions CI workflows are hardened with timeouts, concurrency, and permissions."""

    def test_tests_workflow_hardened(self):
        tests_yml = REPO_ROOT / ".github" / "workflows" / "tests.yml"
        self.assertTrue(tests_yml.exists(), "tests.yml missing")
        content = tests_yml.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", content)
        self.assertIn("concurrency:", content)
        self.assertIn("cancel-in-progress: true", content)
        self.assertIn("timeout-minutes: 15", content)
        self.assertIn("ubuntu-latest", content)
        self.assertIn("windows-latest", content)
        self.assertIn("macos-latest", content)
        self.assertIn("'3.13'", content)
        self.assertIn("pip install --no-build-isolation --no-deps --dry-run .", content)
        self.assertIn("pip check", content)
        self.assertIn("ruff check .", content)
        self.assertIn("pytest", content)
        self.assertIn("check_release_gate.py", content)

    def test_all_workflows_have_concurrency_and_timeout(self):
        workflows_dir = REPO_ROOT / ".github" / "workflows"
        self.assertTrue(workflows_dir.exists(), "workflows directory missing")
        for yml_file in workflows_dir.glob("*.yml"):
            with self.subTest(workflow=yml_file.name):
                content = yml_file.read_text(encoding="utf-8")
                self.assertIn("concurrency:", content, f"Missing concurrency in {yml_file.name}")
                self.assertIn("timeout-minutes:", content, f"Missing timeout-minutes in {yml_file.name}")


if __name__ == "__main__":
    unittest.main()
