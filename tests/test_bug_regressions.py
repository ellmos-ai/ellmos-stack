"""Regression coverage for the 2026-07-17 ellmos-stack bugsweep."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = REPO_ROOT / "services"


def _load_service(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, SERVICES_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, payload: str):
        self._payload = payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self._payload


class TestSafeEnvironmentLoading(unittest.TestCase):
    def test_env_file_is_parsed_without_shell_execution(self):
        module = _load_service("env_config.py", "env_config_regression")
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "must-not-exist"
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "PLAIN=value with spaces\n"
                "QUOTED=\"hello world\"\n"
                f"LITERAL=$(New-Item {marker})\n"
                "INVALID-KEY=ignored\n",
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {}, clear=True):
                loaded = module.load_env_file(env_file)
                self.assertEqual(os.environ["PLAIN"], "value with spaces")
                self.assertEqual(os.environ["QUOTED"], "hello world")
                self.assertEqual(os.environ["LITERAL"], f"$(New-Item {marker})")
                self.assertNotIn("INVALID-KEY", os.environ)
                self.assertFalse(marker.exists())
                self.assertEqual(loaded, {"PLAIN", "QUOTED", "LITERAL"})


class TestTelegramOwnerBoundary(unittest.TestCase):
    def test_gateway_fails_closed_without_owner_chat_id(self):
        module = _load_service("telegram_gateway.py", "telegram_owner_regression")
        with mock.patch.object(module, "BOT_TOKEN", "test-token"), mock.patch.object(
            module, "OWNER_CHAT_ID", ""
        ):
            with self.assertRaisesRegex(ValueError, "TELEGRAM_OWNER_CHAT_ID"):
                module.validate_config()


class TestSummaryDatabaseLifecycle(unittest.TestCase):
    def test_missing_database_is_a_clean_noop(self):
        module = _load_service("process_summaries.py", "summary_db_regression")
        with tempfile.TemporaryDirectory() as tmp:
            module.DB = Path(tmp) / "knowledge.db"
            self.assertEqual(module.main(), 0)


class TestKnowledgeDigestContract(unittest.TestCase):
    def test_auto_ingest_uses_linux_package_name_and_closes_connection(self):
        module = _load_service("auto_ingest.py", "auto_ingest_contract_regression")

        class FakeIngestor:
            instance = None

            def __init__(self, db):
                self.closed = False
                FakeIngestor.instance = self

            def ingest_directory(self, inbox):
                return {"ingested": 2, "errors": 0}

            def close(self):
                self.closed = True

        package = types.ModuleType("KnowledgeDigest")
        package.__path__ = []
        ingestor_module = types.ModuleType("KnowledgeDigest.ingestor")
        ingestor_module.DocumentIngestor = FakeIngestor
        with tempfile.TemporaryDirectory() as tmp:
            module.INBOX = Path(tmp) / "inbox"
            module.ARCHIVE = Path(tmp) / "archive"
            module.DB = Path(tmp) / "knowledge.db"
            module.INBOX.mkdir()
            (module.INBOX / "paper.txt").write_text("content", encoding="utf-8")
            output = StringIO()
            with mock.patch.dict(
                sys.modules,
                {"KnowledgeDigest": package, "KnowledgeDigest.ingestor": ingestor_module},
            ), redirect_stdout(output):
                self.assertEqual(module.main(), 0)
        self.assertTrue(FakeIngestor.instance.closed)
        self.assertIn("2 documents processed", output.getvalue())

    def test_installer_uses_supported_web_viewer_entrypoint(self):
        installer = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn("-m KnowledgeDigest --web", installer)
        self.assertIn("--no-browser", installer)
        self.assertNotIn("-m knowledgedigest.web_viewer", installer)
        self.assertNotIn("--host 127.0.0.1", installer)
        self.assertNotIn("--host 0.0.0.0", installer)

        summaries = (SERVICES_DIR / "process_summaries.py").read_text(encoding="utf-8")
        ingest = (SERVICES_DIR / "auto_ingest.py").read_text(encoding="utf-8")
        self.assertIn("from KnowledgeDigest.summarizer import Summarizer", summaries)
        self.assertIn("from KnowledgeDigest.ingestor import DocumentIngestor", ingest)


class TestResearchPipeline(unittest.TestCase):
    def test_pubmed_source_does_not_call_arxiv(self):
        module = _load_service("research_pipeline.py", "research_source_regression")
        paper = module.Paper("Title", "Abstract", "pubmed", "https://example.test/1")
        with mock.patch.object(module, "search_pubmed", return_value=[paper]) as pubmed, mock.patch.object(
            module, "search_arxiv", return_value=[]
        ) as arxiv:
            self.assertEqual(module.search_papers("query", 5, "pubmed"), [paper])
            pubmed.assert_called_once_with("query", 5)
            arxiv.assert_not_called()

    def test_arxiv_atom_response_is_parsed(self):
        module = _load_service("research_pipeline.py", "research_arxiv_regression")
        atom = """<?xml version='1.0' encoding='UTF-8'?>
        <feed xmlns='http://www.w3.org/2005/Atom'>
          <entry>
            <id>https://arxiv.org/abs/1234.5678</id>
            <title>  A useful\n title  </title>
            <summary>  A compact abstract. </summary>
          </entry>
        </feed>"""
        with mock.patch("urllib.request.urlopen", return_value=_Response(atom)):
            papers = module.search_arxiv("useful", 1)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].title, "A useful title")
        self.assertEqual(papers[0].source, "arxiv")

    def test_pubmed_search_and_fetch_responses_are_parsed(self):
        module = _load_service("research_pipeline.py", "research_pubmed_regression")
        search_json = '{"esearchresult": {"idlist": ["12345"]}}'
        article_xml = """<?xml version='1.0'?>
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <PMID>12345</PMID>
              <Article>
                <ArticleTitle>A <i>nested</i> title</ArticleTitle>
                <Abstract><AbstractText>Useful abstract.</AbstractText></Abstract>
              </Article>
            </MedlineCitation>
          </PubmedArticle>
        </PubmedArticleSet>"""
        with mock.patch(
            "urllib.request.urlopen",
            side_effect=[_Response(search_json), _Response(article_xml)],
        ):
            papers = module.search_pubmed("useful", 1)
        self.assertEqual(papers[0].title, "A nested title")
        self.assertEqual(papers[0].url, "https://pubmed.ncbi.nlm.nih.gov/12345/")

    def test_report_filename_cannot_escape_inbox(self):
        module = _load_service("research_pipeline.py", "research_filename_regression")
        filename = module.safe_report_filename(
            "../../outside\\also:bad",
            now=datetime(2026, 7, 17, 3, 0, 0),
            unique_suffix="fixed123",
        )
        self.assertEqual(Path(filename).name, filename)
        self.assertNotIn("..", filename)
        self.assertTrue(filename.startswith("research_"))
        self.assertTrue(filename.endswith(".md"))

    def test_existing_report_is_never_overwritten(self):
        module = _load_service("research_pipeline.py", "research_overwrite_regression")
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp)
            existing = inbox / "fixed.md"
            existing.write_text("sentinel", encoding="utf-8")
            with mock.patch.object(module, "safe_report_filename", return_value="fixed.md"):
                with self.assertRaises(FileExistsError):
                    module.save_report("replacement", inbox, "query")
            self.assertEqual(existing.read_text(encoding="utf-8"), "sentinel")


class TestInstallerAndExposure(unittest.TestCase):
    def test_installer_does_not_install_unrelated_research_agent_package(self):
        installer = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertNotIn("pip\" install --quiet research-agent", installer)
        self.assertNotIn("research-line/research-agent", installer)

    def test_installer_protects_env_and_does_not_source_it(self):
        installer = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
        cron = (REPO_ROOT / "config" / "cron.example").read_text(encoding="utf-8")
        self.assertIn('chmod 600 "$INSTALL_DIR/.env"', installer)
        self.assertNotIn('source "$INSTALL_DIR/.env"', installer)
        self.assertNotIn(". /opt/ellmos-stack/.env", cron)

    def test_installer_ignores_generated_service_directories(self):
        installer = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn('cp "$SCRIPT_DIR/services/"*.py "$INSTALL_DIR/services/"', installer)
        self.assertNotIn('cp "$SCRIPT_DIR/services/"* "$INSTALL_DIR/services/"', installer)

    def test_installer_stops_if_ollama_never_becomes_ready(self):
        installer = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn("OLLAMA_READY=false", installer)
        self.assertIn('if [ "$OLLAMA_READY" != true ]', installer)
        self.assertIn("Ollama did not become ready", installer)

    def test_prepare_only_restore_and_custom_service_path_are_supported(self):
        installer = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
        operations = (REPO_ROOT / "OPERATIONS.md").read_text(encoding="utf-8")
        self.assertIn("--prepare-only", installer)
        self.assertIn('if [ "$PREPARE_ONLY" = true ]', installer)
        self.assertIn('sed -i "s|/opt/ellmos-stack|$INSTALL_DIR|g"', installer)
        self.assertIn("./install.sh --prepare-only", operations)
        self.assertIn("docker compose create", operations)
        self.assertNotIn("docker compose create --no-start", operations)

    def test_python_components_are_pinned_to_commits(self):
        installer = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertRegex(installer, r'USMC_COMMIT="[0-9a-f]{40}"')
        self.assertRegex(installer, r'GARDENER_COMMIT="[0-9a-f]{40}"')
        self.assertRegex(installer, r'TASK_MASTER_COMMIT="[0-9a-f]{40}"')
        self.assertRegex(installer, r'KNOWLEDGEDIGEST_COMMIT="[0-9a-f]{40}"')
        self.assertIn("usmc.git@$USMC_COMMIT", installer)
        self.assertIn("gardener.git@$GARDENER_COMMIT", installer)
        self.assertIn("task-master.git@$TASK_MASTER_COMMIT", installer)
        self.assertIn("knowledgedigest.git@$KNOWLEDGEDIGEST_COMMIT", installer)
        self.assertNotIn("RINNSAL_COMMIT", installer)
        self.assertNotRegex(
            installer,
            r'pip" install --quiet (usmc|gardener-os|taskplan|knowledgedigest)(?:\s|$)',
        )

    def test_runtime_services_do_not_run_as_root(self):
        installer = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
        cron = (REPO_ROOT / "config" / "cron.example").read_text(encoding="utf-8")
        telegram_unit = (REPO_ROOT / "config" / "telegram-gateway.service").read_text(
            encoding="utf-8"
        )
        self.assertIn("User=$STACK_USER", installer)
        self.assertIn("Group=$STACK_USER", installer)
        self.assertNotRegex(cron, r"^\*/(?:5|15).*\sroot\s", re.MULTILINE)
        self.assertIn("User=ellmos-stack", telegram_unit)
        self.assertIn("NoNewPrivileges=true", telegram_unit)
        self.assertIn("UMask=0077", telegram_unit)
        self.assertIn("umask 077", cron)

    def test_installer_is_executable_in_git(self):
        result = subprocess.run(
            ["git", "ls-files", "--stage", "install.sh"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertTrue(result.stdout.startswith("100755 "), result.stdout)

    def test_remote_ollama_example_requires_tls(self):
        for readme_name in ("README.md", "README_de.md"):
            readme = (REPO_ROOT / readme_name).read_text(encoding="utf-8")
            with self.subTest(readme=readme_name):
                self.assertIn("listen 443 ssl", readme)
                self.assertNotIn("listen 11435;", readme)
                self.assertNotIn("ufw allow 11435/tcp", readme)
                self.assertNotIn("Unauthenticated health endpoint", readme)
                self.assertNotIn("Öffentlicher Health-Endpoint", readme)

    def test_remote_n8n_never_advertises_public_plain_http(self):
        for readme_name in ("README.md", "README_de.md"):
            readme = (REPO_ROOT / readme_name).read_text(encoding="utf-8")
            with self.subTest(readme=readme_name):
                self.assertNotIn("0.0.0.0:5678", readme)
                self.assertIn("VPN", readme)

    def test_unimplemented_bach_routing_is_not_advertised(self):
        gateway = (SERVICES_DIR / "telegram_gateway.py").read_text(encoding="utf-8")
        env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertNotIn("BACH_HEARTBEAT_URL", gateway)
        self.assertNotIn("Prueft ob BACH", gateway)
        self.assertNotIn("Leitet an BACH", gateway)
        self.assertNotIn("BACH_HEARTBEAT_URL", env_example)
        for readme_name in ("README.md", "README_de.md"):
            self.assertNotIn(
                "BACH_HEARTBEAT_URL",
                (REPO_ROOT / readme_name).read_text(encoding="utf-8"),
            )

    def test_memory_and_task_apis_have_separate_state(self):
        gateway = (SERVICES_DIR / "telegram_gateway.py").read_text(encoding="utf-8")
        self.assertIn("from usmc import api as memory_api", gateway)
        self.assertIn("from taskplan import api as tasks_api", gateway)
        self.assertIn('agent_id="telegram-gateway"', gateway)
        self.assertIn("memory_api.context(max_items=3)", gateway)
        self.assertIn('USMC_DB = DATA_DIR / "usmc" / "usmc_memory.db"', gateway)
        self.assertIn('TASKPLAN_DB = DATA_DIR / "task-master" / "taskplan.db"', gateway)
        self.assertIn("db_path=str(USMC_DB)", gateway)
        self.assertIn("db_path=str(TASKPLAN_DB)", gateway)
        self.assertNotIn("from rinnsal", gateway)

        for readme_name in ("README.md", "README_de.md"):
            readme = (REPO_ROOT / readme_name).read_text(encoding="utf-8")
            with self.subTest(readme=readme_name):
                self.assertIn("from usmc import api as memory", readme)
                self.assertIn("from taskplan import api as tasks", readme)
                self.assertIn("data/usmc/usmc_memory.db", readme)
                self.assertIn("data/gardener", readme)
                self.assertIn("data/task-master/taskplan.db", readme)

    def test_manifest_resolves_specialized_roles_without_rinnsal(self):
        manifest = json.loads((REPO_ROOT / "stack.v2.json").read_text(encoding="utf-8"))
        roles = {item["id"]: item["role"] for item in manifest["components"]}
        self.assertEqual(roles["USMC"], "memory.curated")
        self.assertEqual(roles["GARDENER"], "memory.organic")
        self.assertEqual(roles["task-master"], "tasks.default")
        self.assertEqual(roles["KnowledgeDigest"], "knowledge.search.default")
        self.assertEqual(set(manifest["required_roles"]), set(roles.values()))
        self.assertNotIn("rinnsal", json.dumps(manifest).lower())

    def test_telegram_token_prefers_new_name_and_accepts_legacy_fallback(self):
        with mock.patch.dict(
            os.environ,
            {
                "ELLMOS_TELEGRAM_TOKEN": "preferred-token",
                "RINNSAL_TELEGRAM_TOKEN": "legacy-token",
            },
        ):
            preferred = _load_service("telegram_gateway.py", "telegram_preferred_token")
        self.assertEqual(preferred.BOT_TOKEN, "preferred-token")

        with mock.patch.dict(
            os.environ,
            {"RINNSAL_TELEGRAM_TOKEN": "legacy-token"},
            clear=True,
        ):
            legacy = _load_service("telegram_gateway.py", "telegram_legacy_token")
        self.assertEqual(legacy.BOT_TOKEN, "legacy-token")


class TestReleaseEvidence(unittest.TestCase):
    def test_partial_or_branch_like_image_tags_are_rejected(self):
        module = _load_path(
            REPO_ROOT / "tools" / "check_release_gate.py", "release_tag_regression"
        )
        gate = module.Gate()
        module.check_release_inputs(gate, "1", "feature-branch")
        self.assertEqual(len(gate.errors), 2)

        green = module.Gate()
        module.check_release_inputs(green, "0.32.0", "2.31.1")
        self.assertFalse(green.errors)

    def test_security_attestations_and_resolved_digests_are_required(self):
        module = _load_path(
            REPO_ROOT / "tools" / "check_release_gate.py", "release_evidence_regression"
        )
        evidence = {
            "platform_linux": True,
            "compose_config_valid": True,
            "services_started": True,
            "ollama_ready": True,
            "n8n_ready": True,
            "bindings_localhost": True,
            "owner_account_confirmed": False,
            "external_access_reviewed": False,
            "restore_rehearsed": False,
            "ollama_image": "ollama/ollama:0.32.0",
            "n8n_image": "n8nio/n8n:2.31.1",
            "commit": "a" * 40,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.json"
            path.write_text(__import__("json").dumps(evidence), encoding="utf-8")
            gate = module.Gate()
            module.check_evidence(gate, path)
        self.assertTrue(any("owner_account_confirmed" in error for error in gate.errors))
        self.assertTrue(any("image digest" in error for error in gate.errors))

    def test_workflow_measures_bindings_and_records_reviewer(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "release-gate.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("docker port ollama 11434/tcp", workflow)
        self.assertIn("OLLAMA_IMAGE_DIGEST", workflow)
        self.assertIn('"security_reviewer": os.environ["GITHUB_ACTOR"]', workflow)
        self.assertIn("python -m KnowledgeDigest --web --help", workflow)
        self.assertIn("from usmc import api as memory", workflow)
        self.assertIn("from gardener import Gardener", workflow)
        self.assertIn("from taskplan import api as tasks", workflow)
        self.assertNotIn("from rinnsal", workflow)


if __name__ == "__main__":
    unittest.main()
