from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import openspec_bridge as bridge


class DependencyTests(unittest.TestCase):
    def test_missing_cli_gives_install_command(self):
        with patch.object(bridge.shutil, "which", return_value=None):
            with self.assertRaisesRegex(bridge.OpenSpecError, "npm install"):
                bridge.verify_dependency()

    def test_version_contract(self):
        with patch.object(bridge.shutil, "which", return_value="/bin/openspec"):
            for version in ("1.12.9", "2.0.0", "1.13.0-beta.1", "garbage"):
                with self.subTest(version=version), patch.object(bridge, "run_cli", return_value=version):
                    with self.assertRaises(bridge.OpenSpecError):
                        bridge.verify_dependency()
            with patch.object(bridge, "run_cli", return_value="1.13.0"):
                self.assertEqual(bridge.verify_dependency()["version"], "1.13.0")

    def test_timeout_and_failed_command_are_actionable(self):
        with patch.object(bridge.subprocess, "run", side_effect=subprocess.TimeoutExpired("openspec", 30)):
            with self.assertRaisesRegex(bridge.OpenSpecError, "could not run"):
                bridge.run_cli("openspec", ["--version"])
        failed = subprocess.CompletedProcess([], 1, "", "missing package")
        with patch.object(bridge.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(bridge.OpenSpecError, "missing package"):
                bridge.run_cli("openspec", ["status"])


class PackageTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.tasks = self.root / "tasks.md"
        self.tasks.write_text("- [ ] 1.1 Implement and check\n")
        self.status = {
            "planningHome": {"root": str(self.root)}, "changeName": "example",
            "artifacts": [{"id": "tasks", "status": "done"}],
        }
        self.apply = {
            "state": "ready", "tasks": [{"done": False}],
            "contextFiles": {"tasks": [str(self.tasks)]},
        }
        dep = patch.object(bridge, "verify_dependency", return_value={"binary": "openspec", "version": "1.13.0"})
        dep.start()
        self.addCleanup(dep.stop)
        cli = patch.object(bridge, "cli_json", side_effect=self.cli)
        cli.start()
        self.addCleanup(cli.stop)

    def cli(self, binary, arguments, root):
        if arguments[0] == "status":
            return self.status
        if arguments[0] == "validate":
            return {"items": [{"valid": True}]}
        return self.apply

    def test_unfinished_tasks_allow_build_but_not_handoff(self):
        self.assertEqual(bridge.check_package(self.root, "example")["read_set"], [str(self.tasks)])
        with self.assertRaisesRegex(bridge.OpenSpecError, "unfinished"):
            bridge.check_package(self.root, "example", complete=True)
        self.apply.update(state="all_done", tasks=[{"done": True}])
        self.assertEqual(bridge.check_package(self.root, "example", complete=True)["state"], "all_done")

    def test_incomplete_artifact_blocks_even_if_tasks_exist(self):
        self.status["artifacts"].append({"id": "design", "status": "ready"})
        with self.assertRaisesRegex(bridge.OpenSpecError, "incomplete"):
            bridge.check_package(self.root, "example")

    def test_skip_specs_can_use_upstream_skip_state(self):
        self.status["artifacts"].append({"id": "specs", "status": "skipped"})
        self.assertEqual(bridge.check_package(self.root, "example")["state"], "ready")

    def test_implicit_store_redirect_is_rejected(self):
        self.status["planningHome"]["root"] = str(self.root / "other-store")
        with self.assertRaisesRegex(bridge.OpenSpecError, "planning root"):
            bridge.check_package(self.root, "example")

    def test_invalid_change_and_missing_context_are_rejected(self):
        with self.assertRaises(bridge.OpenSpecError):
            bridge.check_package(self.root, "../example")
        self.tasks.unlink()
        with self.assertRaisesRegex(bridge.OpenSpecError, "context file"):
            bridge.check_package(self.root, "example")

    def test_empty_tasks_are_not_delivery(self):
        self.apply["tasks"] = []
        with self.assertRaisesRegex(bridge.OpenSpecError, "nonempty"):
            bridge.check_package(self.root, "example")


@unittest.skipUnless(os.environ.get("TRACE_TEST_OPENSPEC") == "1", "opt-in real OpenSpec contract test")
class LiveOpenSpecTests(unittest.TestCase):
    def test_both_harnesses_package_validation_and_completion(self):
        dependency = bridge.verify_dependency()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            binary = dependency["binary"]
            bridge.run_cli(binary, ["init", "--tools", "codex,claude", "--no-animation"], root)
            self.assertTrue((root / ".agents/skills/openspec-apply-change/SKILL.md").is_file())
            self.assertTrue((root / ".claude/skills/openspec-apply-change/SKILL.md").is_file())
            bridge.run_cli(binary, ["new", "change", "test-delivery"], root)
            change = root / "openspec/changes/test-delivery"
            (change / "proposal.md").write_text("# Why\nTest delivery integration.\n")
            (change / "design.md").write_text("# Decisions\nUse an isolated test fixture.\n")
            task = change / "tasks.md"
            task.write_text("## 1. Work\n\n- [ ] 1.1 Implement fixture and verify its test passes\n")
            spec = change / "specs/fixture/spec.md"
            spec.parent.mkdir(parents=True)
            spec.write_text(
                "## Purpose\n\nExercise the delivery integration with a real OpenSpec CLI fixture.\n\n"
                "## ADDED Requirements\n\n### Requirement: Check delivery\n"
                "The system SHALL check readiness before delivery.\n\n"
                "#### Scenario: Ready package\n- **WHEN** artifacts exist\n- **THEN** delivery may start\n"
            )
            self.assertEqual(bridge.check_package(root, "test-delivery")["state"], "ready")
            with self.assertRaisesRegex(bridge.OpenSpecError, "unfinished"):
                bridge.check_package(root, "test-delivery", complete=True)
            (change / "design.md").unlink()
            with self.assertRaisesRegex(bridge.OpenSpecError, "incomplete"):
                bridge.check_package(root, "test-delivery")
            (change / "design.md").write_text("# Decisions\nUse a fixture.\n")
            spec.write_text("## ADDED Requirements\n\n### Requirement: Broken\nThe system SHALL check readiness.\n")
            with self.assertRaisesRegex(bridge.OpenSpecError, "validate"):
                bridge.check_package(root, "test-delivery")
            # No behavior change: use upstream skip_specs instead of fake requirements.
            spec.unlink()
            (change / ".openspec.yaml").write_text("schema: spec-driven\nskip_specs: true\n")
            task.write_text(task.read_text().replace("[ ]", "[x]"))
            self.assertEqual(bridge.check_package(root, "test-delivery", complete=True)["state"], "all_done")
