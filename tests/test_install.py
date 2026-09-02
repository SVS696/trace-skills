from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import install


class InstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        for name in install.SKILLS:
            skill = self.repo / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("test\n", encoding="utf-8")
        for runtime, extension in (("codex", ".toml"), ("claude", ".md")):
            source = self.repo / "agents" / runtime / f"role{extension}"
            source.parent.mkdir(parents=True)
            source.write_text("role\n", encoding="utf-8")
        self.home = self.root / "home"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_install_is_idempotent_and_verifiable(self) -> None:
        install.install(self.repo, self.home)
        install.install(self.repo, self.home)
        result = install.verify(self.repo, self.home, [])
        self.assertTrue(result["ok"])

    def test_install_refuses_unowned_agent(self) -> None:
        destination = self.home / ".codex" / "agents" / "role.toml"
        destination.parent.mkdir(parents=True)
        destination.write_text("mine\n", encoding="utf-8")
        with self.assertRaises(install.InstallError):
            install.install(self.repo, self.home)


if __name__ == "__main__":
    unittest.main()
