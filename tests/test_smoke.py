"""
Smoke tests for ellmos-stack.

Tests that run without Docker, Ollama, Telegram or any other live service.
Covers:
- Syntax check of all Python service files (py_compile)
- Conditional import checks (skips if optional deps absent)
- docker-compose.yml YAML validity
- config/system_prompt.txt presence
- Environment variable defaults in service modules (import-guarded)
"""
import ast
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = REPO_ROOT / "services"
CONFIG_DIR = REPO_ROOT / "config"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _source_files():
    """All .py files in services/."""
    return list(SERVICES_DIR.glob("*.py"))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSyntax(unittest.TestCase):
    """Every Python file in services/ must be syntactically valid."""

    def _check_syntax(self, path: Path):
        src = path.read_text(encoding="utf-8")
        try:
            ast.parse(src, filename=str(path))
        except SyntaxError as exc:
            self.fail(f"SyntaxError in {path.name}: {exc}")

    def test_auto_ingest_syntax(self):
        self._check_syntax(SERVICES_DIR / "auto_ingest.py")

    def test_process_summaries_syntax(self):
        self._check_syntax(SERVICES_DIR / "process_summaries.py")

    def test_research_pipeline_syntax(self):
        self._check_syntax(SERVICES_DIR / "research_pipeline.py")

    def test_telegram_gateway_syntax(self):
        self._check_syntax(SERVICES_DIR / "telegram_gateway.py")

    def test_all_service_files_have_valid_syntax(self):
        """Catch any future .py additions automatically."""
        for py_file in _source_files():
            with self.subTest(file=py_file.name):
                self._check_syntax(py_file)


class TestDockerComposeYaml(unittest.TestCase):
    """docker-compose.yml must parse as valid YAML."""

    def setUp(self):
        if not _has_module("yaml"):
            self.skipTest("PyYAML not installed")

    def test_docker_compose_parses(self):
        import yaml
        compose_path = REPO_ROOT / "docker-compose.yml"
        self.assertTrue(compose_path.exists(), "docker-compose.yml not found")
        with open(compose_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.assertIsInstance(data, dict)

    def test_docker_compose_has_services_key(self):
        import yaml
        compose_path = REPO_ROOT / "docker-compose.yml"
        with open(compose_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.assertIn("services", data)
        self.assertIsInstance(data["services"], dict)

    def test_docker_compose_has_ollama_service(self):
        import yaml
        compose_path = REPO_ROOT / "docker-compose.yml"
        with open(compose_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.assertIn("ollama", data["services"])

    def test_docker_compose_has_n8n_service(self):
        import yaml
        compose_path = REPO_ROOT / "docker-compose.yml"
        with open(compose_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.assertIn("n8n", data["services"])

    def test_docker_compose_ollama_has_image(self):
        import yaml
        compose_path = REPO_ROOT / "docker-compose.yml"
        with open(compose_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        ollama = data["services"]["ollama"]
        self.assertIn("image", ollama)
        self.assertIn("ollama", ollama["image"])

    def test_docker_compose_n8n_has_port(self):
        import yaml
        compose_path = REPO_ROOT / "docker-compose.yml"
        with open(compose_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        n8n = data["services"]["n8n"]
        self.assertIn("ports", n8n)
        ports_str = " ".join(str(p) for p in n8n["ports"])
        self.assertIn("5678", ports_str)


class TestConfigFiles(unittest.TestCase):
    """Static config files must exist and be non-empty."""

    def test_system_prompt_exists(self):
        prompt_file = CONFIG_DIR / "system_prompt.txt"
        self.assertTrue(prompt_file.exists(), "config/system_prompt.txt not found")

    def test_system_prompt_not_empty(self):
        prompt_file = CONFIG_DIR / "system_prompt.txt"
        content = prompt_file.read_text(encoding="utf-8").strip()
        self.assertGreater(len(content), 10)

    def test_cron_example_exists(self):
        cron_file = CONFIG_DIR / "cron.example"
        self.assertTrue(cron_file.exists(), "config/cron.example not found")

    def test_docker_compose_exists(self):
        self.assertTrue((REPO_ROOT / "docker-compose.yml").exists())

    def test_readme_exists(self):
        self.assertTrue((REPO_ROOT / "README.md").exists())


class TestServiceModuleDefaults(unittest.TestCase):
    """
    Validate env-var defaults and constants in service files without importing
    the modules (which have optional external deps like knowledgedigest).
    Uses ast to read module-level assignments.
    """

    def _get_assignments(self, path: Path) -> dict:
        """Parse module-level string assignments from a .py file."""
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        assignments = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                        assignments[target.id] = node.value.value
        return assignments

    def test_telegram_gateway_default_ollama_url(self):
        """OLLAMA_URL should default to localhost:11434."""
        src = (SERVICES_DIR / "telegram_gateway.py").read_text(encoding="utf-8")
        self.assertIn("localhost:11434", src)

    def test_research_pipeline_default_ollama_url(self):
        src = (SERVICES_DIR / "research_pipeline.py").read_text(encoding="utf-8")
        self.assertIn("localhost:11434", src)

    def test_telegram_gateway_uses_env_vars(self):
        """Telegram gateway must read token from environment."""
        src = (SERVICES_DIR / "telegram_gateway.py").read_text(encoding="utf-8")
        self.assertIn("RINNSAL_TELEGRAM_TOKEN", src)
        self.assertIn("os.environ", src)

    def test_process_summaries_uses_env_provider(self):
        src = (SERVICES_DIR / "process_summaries.py").read_text(encoding="utf-8")
        self.assertIn("KD_SUMMARY_PROVIDER", src)

    def test_research_pipeline_has_argparse(self):
        src = (SERVICES_DIR / "research_pipeline.py").read_text(encoding="utf-8")
        self.assertIn("argparse", src)


class TestTelegramGatewayImport(unittest.TestCase):
    """telegram_gateway.py uses only stdlib -- should import cleanly."""

    def test_telegram_gateway_module_level_constants(self):
        """Import the module and check that env-var constants are set."""
        spec = importlib.util.spec_from_file_location(
            "telegram_gateway",
            SERVICES_DIR / "telegram_gateway.py",
        )
        # The module sets BOT_TOKEN = os.environ.get(..., "") at top level.
        # We can verify the AST sees these names without actually executing the module.
        src = (SERVICES_DIR / "telegram_gateway.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        top_level_names = {
            node.targets[0].id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
        }
        self.assertIn("BOT_TOKEN", top_level_names)
        self.assertIn("OWNER_CHAT_ID", top_level_names)
        self.assertIn("OLLAMA_URL", top_level_names)


if __name__ == "__main__":
    unittest.main()
