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

    def test_preflight_collision_leaves_no_partial_agent_copy(self) -> None:
        second = self.repo / "agents" / "codex" / "zzz.toml"
        second.write_text("second\n", encoding="utf-8")
        collision = self.home / ".codex" / "agents" / "zzz.toml"
        collision.parent.mkdir(parents=True)
        collision.write_text("mine\n", encoding="utf-8")
        with self.assertRaises(install.InstallError):
            install.install(self.repo, self.home)
        self.assertFalse((self.home / ".codex" / "agents" / "role.toml").exists())

    def test_verify_rejects_foreign_and_dangling_links_and_repair_is_explicit(self) -> None:
        install.install(self.repo, self.home)
        link = self.home / ".agents" / "skills" / install.SKILLS[0]
        link.unlink()
        foreign = self.root / "foreign"
        foreign.mkdir()
        link.symlink_to(foreign, target_is_directory=True)
        with self.assertRaises(install.InstallError):
            install.verify(self.repo, self.home, [])
        with self.assertRaises(install.InstallError):
            install.install(self.repo, self.home)
        install.install(self.repo, self.home, repair_links=True)
        self.assertTrue(install.verify(self.repo, self.home, [])["ok"])
        current = self.home / ".workflow-skills" / "current"
        current.unlink()
        current.symlink_to(self.root / "missing", target_is_directory=True)
        with self.assertRaises(install.InstallError):
            install.verify(self.repo, self.home, [])

    def test_verify_rejects_source_changed_after_install(self) -> None:
        install.install(self.repo, self.home)
        source = self.repo / "agents" / "codex" / "role.toml"
        source.write_text("new role\n", encoding="utf-8")
        with self.assertRaisesRegex(install.InstallError, "source changed"):
            install.verify(self.repo, self.home, [])
        install.install(self.repo, self.home)
        self.assertTrue(install.verify(self.repo, self.home, [])["ok"])

    def test_install_removes_only_owned_orphan_agent_copy(self) -> None:
        install.install(self.repo, self.home)
        old_source = self.repo / "agents" / "codex" / "role.toml"
        new_source = old_source.with_name("renamed.toml")
        old_source.rename(new_source)
        result = install.install(self.repo, self.home)
        old_copy = self.home / ".codex" / "agents" / "role.toml"
        new_copy = self.home / ".codex" / "agents" / "renamed.toml"
        self.assertFalse(old_copy.exists())
        self.assertTrue(new_copy.exists())
        self.assertIn(str(old_copy), result["removed_agent_copies"])
        self.assertTrue(install.verify(self.repo, self.home, [])["ok"])

    def test_install_recovers_pending_manifest(self) -> None:
        install.install(self.repo, self.home)
        source = self.repo / "agents" / "codex" / "role.toml"
        destination = self.home / ".codex" / "agents" / "role.toml"
        old_hash = install.sha256(destination)
        source.write_text("new role\n", encoding="utf-8")
        manifest_path = destination.parent / install.MANIFEST_NAME
        manifest = install.load_manifest(manifest_path)
        manifest["files"][str(destination)] = {
            "source": str(source.resolve()),
            "sha256": old_hash,
            "pending_sha256": install.sha256(source),
        }
        install.atomic_json(manifest_path, manifest)
        with self.assertRaisesRegex(install.InstallError, "incomplete agent install"):
            install.verify(self.repo, self.home, [])
        install.install(self.repo, self.home)
        self.assertEqual(destination.read_text(encoding="utf-8"), "new role\n")
        self.assertTrue(install.verify(self.repo, self.home, [])["ok"])

    def test_project_repair_link_is_explicit(self) -> None:
        project = self.root / "project"
        project.mkdir()
        install.install_project(self.repo, project)
        link = project / ".agents" / "skills" / install.SKILLS[0]
        link.unlink()
        foreign = self.root / "project-foreign"
        foreign.mkdir()
        link.symlink_to(foreign, target_is_directory=True)
        with self.assertRaises(install.InstallError):
            install.install_project(self.repo, project)
        install.install_project(self.repo, project, repair_links=True)
        self.assertEqual(link.resolve(), (self.repo / "skills" / install.SKILLS[0]).resolve())


if __name__ == "__main__":
    unittest.main()
