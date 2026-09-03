from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import smoke_break_dependency


class SmokeBreakDependencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = smoke_break_dependency.load_contract()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.codex_plugin = self.root / "marketplace" / "plugins" / "smoke-break"
        self.claude_plugin = self.root / "claude-cache" / "smoke-break"
        for runtime, plugin in (("codex", self.codex_plugin), ("claude", self.claude_plugin)):
            marker = plugin / self.contract["runtimes"][runtime]["marker_path"]
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text('const reminder = "Smoke break:";\n', encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def inventories(self, *, claude_enabled: bool = True) -> dict[str, object]:
        codex = self.contract["runtimes"]["codex"]
        claude = self.contract["runtimes"]["claude"]
        return {
            "codex": {
                "installed": [
                    {
                        "pluginId": codex["plugin_id"],
                        "installed": True,
                        "enabled": True,
                        "version": "0.1.0+local",
                        "source": {"source": "local", "path": str(self.codex_plugin)},
                    }
                ]
            },
            "claude": [
                {
                    "id": claude["plugin_id"],
                    "enabled": claude_enabled,
                    "version": claude["expected_version"],
                    "installPath": str(self.claude_plugin),
                }
            ],
        }

    def runner_for(self, payloads: dict[str, object], *, absent: set[str] | None = None):
        absent = absent or set()

        def run(command, **_kwargs):
            if command[0] in absent:
                raise FileNotFoundError(command[0])
            if command[0] == "git":
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=self.contract["runtimes"]["codex"]["source_ref"] + "\n",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps(payloads[command[0]]),
                stderr="",
            )

        return run

    def test_verify_accepts_enabled_plugins_and_recommended_interval(self) -> None:
        config = self.root / ".smoke-break.env"
        config.write_text("SMOKE_BREAK_INTERVAL_MS=900000\n", encoding="utf-8")
        result = smoke_break_dependency.verify(
            self.contract,
            config,
            ["codex", "claude"],
            runner=self.runner_for(self.inventories()),
            env={},
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["config"]["recommended"])

    def test_verify_reports_missing_runtime_plugin(self) -> None:
        payloads = self.inventories()
        payloads["claude"] = []
        result = smoke_break_dependency.verify(
            self.contract,
            self.root / "missing.env",
            ["codex", "claude"],
            runner=self.runner_for(payloads),
            env={},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["runtimes"]["claude"]["state"], "plugin_missing")

    def test_absent_runtime_is_distinct_from_missing_plugin(self) -> None:
        result = smoke_break_dependency.inspect_runtime(
            "claude",
            self.contract["runtimes"]["claude"],
            runner=self.runner_for(self.inventories(), absent={"claude"}),
        )
        self.assertEqual(result["state"], "runtime_absent")

    def test_malformed_inventory_is_distinct_from_runtime_failure(self) -> None:
        payloads = self.inventories()
        payloads["claude"] = {"unexpected": []}
        malformed = smoke_break_dependency.inspect_runtime(
            "claude",
            self.contract["runtimes"]["claude"],
            runner=self.runner_for(payloads),
        )
        self.assertEqual(malformed["state"], "inventory_error")

        def failed(command, **_kwargs):
            return subprocess.CompletedProcess(command, 2, stdout="", stderr="auth failed")

        runtime_error = smoke_break_dependency.inspect_runtime(
            "claude",
            self.contract["runtimes"]["claude"],
            runner=failed,
        )
        self.assertEqual(runtime_error["state"], "runtime_error")

    def test_disabled_plugin_is_reported_as_drift(self) -> None:
        result = smoke_break_dependency.verify(
            self.contract,
            self.root / "missing.env",
            ["claude"],
            runner=self.runner_for(self.inventories(claude_enabled=False)),
            env={},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["runtimes"]["claude"]["state"], "plugin_drift")
        self.assertFalse(result["runtimes"]["claude"]["enabled"])

    def test_unknown_install_path_is_unverified_not_drift(self) -> None:
        payloads = self.inventories()
        payloads["codex"]["installed"][0].pop("source")
        result = smoke_break_dependency.verify(
            self.contract,
            self.root / "missing.env",
            ["codex"],
            runner=self.runner_for(payloads),
            env={},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["runtimes"]["codex"]["state"], "unverified")

    def test_invalid_config_falls_back_like_the_runtime(self) -> None:
        config = self.root / ".smoke-break.env"
        config.write_text("SMOKE_BREAK_INTERVAL_MS=900_000\n", encoding="utf-8")
        result = smoke_break_dependency.configured_interval(config, self.contract, env={})
        self.assertEqual(result["source"], "plugin-default")
        self.assertEqual(result["interval_ms"], 300000)
        self.assertEqual(len(result["warnings"]), 1)

    def test_environment_fallback_matches_runtime_precedence(self) -> None:
        result = smoke_break_dependency.configured_interval(
            self.root / "missing.env",
            self.contract,
            env={"SMOKE_BREAK_INTERVAL_MS": "9e5"},
        )
        self.assertEqual(result["source"], "environment")
        self.assertEqual(result["interval_ms"], 900000)

    def test_root_marketplace_matches_dependency_contract(self) -> None:
        marketplace = json.loads(
            (smoke_break_dependency.ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        plugin = marketplace["plugins"][0]
        plugin_id = f"{plugin['name']}@{marketplace['name']}"
        self.assertEqual(plugin_id, self.contract["runtimes"]["claude"]["plugin_id"])
        source = smoke_break_dependency.ROOT / plugin["source"]
        expected = smoke_break_dependency.ROOT / self.contract["runtimes"]["claude"][
            "plugin_path"
        ]
        self.assertEqual(source.resolve(), expected.resolve())
        self.assertTrue((source / "hooks" / "hooks.json").is_file())
        plugin_manifest = json.loads(
            (source / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        package = json.loads((source / "package.json").read_text(encoding="utf-8"))
        expected_version = self.contract["runtimes"]["claude"]["expected_version"]
        self.assertEqual(plugin_manifest["version"], expected_version)
        self.assertEqual(package["version"], expected_version)
        hooks = json.loads((source / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        timeouts = [
            hook["timeout"]
            for event in hooks["hooks"].values()
            for matcher in event
            for hook in matcher["hooks"]
        ]
        self.assertEqual(timeouts, [5, 5])


if __name__ == "__main__":
    unittest.main()
