from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import validate_setup


class SetupTests(unittest.TestCase):
    def valid_payload(self, root: Path) -> dict:
        return {
            "schema": 1,
            "project_id": "TEST",
            "project_root": str(root),
            "instructions": ["CLAUDE.md"],
            "template": {
                "path": "template.md",
                "sha256": validate_setup.digest(root / "template.md"),
            },
            "routes": {
                "method": "method-library",
                "preanalysis": "spec-preanalysis",
                "specification": "spec-workflow",
                "implementation": "delivery-workflow",
                "timer": "process-timer",
                "legacy": "legacy-case-migration",
            },
        }

    def test_template_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "CLAUDE.md").write_text("rules\n", encoding="utf-8")
            (root / "template.md").write_text("template\n", encoding="utf-8")
            payload = self.valid_payload(root)
            payload["template"]["sha256"] = "wrong"
            with self.assertRaises(validate_setup.SetupError):
                validate_setup.validate(payload)

    def test_valid_setup_and_route_values_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "CLAUDE.md").write_text("rules\n", encoding="utf-8")
            (root / "template.md").write_text("template\n", encoding="utf-8")
            payload = self.valid_payload(root)
            self.assertEqual(
                validate_setup.validate(payload)["template_sha256"],
                validate_setup.digest(root / "template.md"),
            )
            payload["routes"]["implementation"] = "spec-workflow"
            with self.assertRaises(validate_setup.SetupError):
                validate_setup.validate(payload)


if __name__ == "__main__":
    unittest.main()
