from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import rule_library


class RuleLibraryTests(unittest.TestCase):
    def test_every_native_rule_is_routed_and_mirrors_are_intact(self) -> None:
        result = rule_library.validate()
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(result["native_rules"]["requirements"], 70)
        self.assertGreaterEqual(result["native_rules"]["delivery"], 25)

    def test_requirements_route_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "basis.md"
            result = rule_library.materialize("requirements", ["scenarios"], output)
            text = output.read_text(encoding="utf-8")
            self.assertEqual(result["routes"], ["scenarios"])
            self.assertIn("C02. Поиск вариантов использования", text)
            self.assertIn("D07. Варианты использования", text)
            self.assertNotIn("C03. Доступность", text)

    def test_delivery_route_includes_core_but_not_other_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "basis.md"
            result = rule_library.materialize("delivery", ["backend-http"], output)
            text = output.read_text(encoding="utf-8")
            self.assertEqual(result["routes"], ["core-change", "backend-http"])
            self.assertIn("E01. Минимальный проверяемый change", text)
            self.assertIn("B01. Ресурс, метод", text)
            self.assertNotIn("F01. Наблюдаемое поведение", text)

    def test_route_uses_signals(self) -> None:
        result = rule_library.choose_route("delivery", "Изменить REST endpoint и status code")
        self.assertEqual(result["route"], "backend-http")


if __name__ == "__main__":
    unittest.main()
