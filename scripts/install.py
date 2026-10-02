#!/usr/bin/env python3
"""Install and verify TRACE without overwriting unrelated entries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


SKILLS = (
    "method-library",
    "analysis-workflow",
    "spec-preanalysis",
    "spec-workflow",
    "delivery-workflow",
    "process-timer",
    "legacy-case-migration",
)
MANIFEST_NAME = ".workflow-skills-agent-copies.json"


class InstallError(RuntimeError):
    """Installation would be ambiguous or destructive."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": 1, "files": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InstallError(f"invalid ownership manifest: {path}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise InstallError(f"unsupported ownership manifest: {path}")
    return payload


def ensure_symlink(link: Path, target: Path, *, repair: bool = False) -> None:
    target = target.resolve()
    if link.is_symlink():
        current = (link.parent / os.readlink(link)).resolve()
        if current == target:
            return
        if not repair:
            raise InstallError(f"refusing to replace unrelated symlink: {link} -> {current}")
        link.unlink()
    if link.exists():
        raise InstallError(f"refusing to replace unrelated path: {link}")
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target, target_is_directory=target.is_dir())


def copy_owned(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def accepted_hashes(record: Any) -> set[str]:
    if not isinstance(record, dict):
        return set()
    return {
        value
        for value in (record.get("sha256"), record.get("pending_sha256"))
        if isinstance(value, str)
    }


def planned_copies(
    repo_root: Path, user_home: Path
) -> tuple[
    list[tuple[Path, Path, Path, dict[str, Any]]],
    dict[Path, dict[str, Any]],
    list[tuple[Path, Path, dict[str, Any]]],
]:
    planned: list[tuple[Path, Path, Path, dict[str, Any]]] = []
    manifests: dict[Path, dict[str, Any]] = {}
    orphaned: list[tuple[Path, Path, dict[str, Any]]] = []
    for runtime, extension in (("codex", ".toml"), ("claude", ".md")):
        destination_root = user_home / f".{runtime}" / "agents"
        manifest_path = destination_root / MANIFEST_NAME
        manifest = load_manifest(manifest_path)
        manifests[manifest_path] = manifest
        sources = sorted((repo_root / "agents" / runtime).glob(f"*{extension}"))
        expected_sources = {str(source) for source in sources}
        for source in sources:
            destination = destination_root / source.name
            owned = manifest.setdefault("files", {}).get(str(destination))
            if destination.exists() and owned is None:
                raise InstallError(f"refusing to overwrite unowned agent entry: {destination}")
            if destination.exists() and sha256(destination) not in accepted_hashes(owned):
                raise InstallError(f"owned agent entry was modified locally: {destination}")
            planned.append((source, destination, manifest_path, manifest))
        for path_text, record in manifest.get("files", {}).items():
            path = Path(path_text)
            if path.parent.resolve() != destination_root.resolve():
                raise InstallError(f"ownership record escapes agent directory: {path}")
            if not isinstance(record, dict):
                raise InstallError(f"invalid ownership record: {path}")
            if record.get("source") in expected_sources:
                continue
            if path.exists() and (not path.is_file() or sha256(path) not in accepted_hashes(record)):
                raise InstallError(f"refusing to remove modified orphan agent entry: {path}")
            orphaned.append((path, manifest_path, manifest))
    return planned, manifests, orphaned


def install(repo_root: Path, user_home: Path, *, repair_links: bool = False) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    planned, manifests, orphaned = planned_copies(repo_root, user_home)
    current = user_home / ".workflow-skills" / "current"
    ensure_symlink(current, repo_root, repair=repair_links)
    links: list[str] = [str(current)]
    for base in (user_home / ".agents" / "skills", user_home / ".claude" / "skills"):
        for name in SKILLS:
            link = base / name
            ensure_symlink(link, repo_root / "skills" / name, repair=repair_links)
            links.append(str(link))

    removed: list[str] = []
    for path, _, manifest in orphaned:
        if path.exists():
            path.unlink()
            removed.append(str(path))
        manifest["files"].pop(str(path), None)

    copied: list[str] = []
    for source, destination, manifest_path, manifest in planned:
        manifest["repo_root"] = str(repo_root)
        target_hash = sha256(source)
        manifest["files"][str(destination)] = {
            "source": str(source),
            "sha256": sha256(destination) if destination.exists() else target_hash,
            "pending_sha256": target_hash,
        }
        manifests[manifest_path] = manifest
    for manifest_path, manifest in manifests.items():
        atomic_json(manifest_path, manifest)
    for source, destination, _, manifest in planned:
        copy_owned(source, destination)
        manifest["files"][str(destination)] = {
            "source": str(source),
            "sha256": sha256(destination),
        }
        copied.append(str(destination))
    for manifest_path, manifest in manifests.items():
        atomic_json(manifest_path, manifest)
    return {"links": links, "agent_copies": copied, "removed_agent_copies": removed}


def install_project(
    repo_root: Path, project_root: Path, *, repair_links: bool = False
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    project_root = project_root.resolve()
    if not project_root.is_dir():
        raise InstallError(f"project root does not exist: {project_root}")
    links: list[str] = []
    for base in (project_root / ".agents" / "skills", project_root / ".claude" / "skills"):
        for name in SKILLS:
            link = base / name
            ensure_symlink(link, repo_root / "skills" / name, repair=repair_links)
            links.append(str(link))
    return {"project_root": str(project_root), "links": links}


def verify(repo_root: Path, user_home: Path, project_roots: list[Path]) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    problems: list[str] = []
    expected_links: list[tuple[Path, Path]] = [
        (user_home / ".workflow-skills" / "current", repo_root)
    ]
    for base in (user_home / ".agents" / "skills", user_home / ".claude" / "skills"):
        expected_links.extend((base / name, repo_root / "skills" / name) for name in SKILLS)
    for project_root in project_roots:
        for base in (project_root / ".agents" / "skills", project_root / ".claude" / "skills"):
            expected_links.extend((base / name, repo_root / "skills" / name) for name in SKILLS)
    for link, expected_target in expected_links:
        if not link.is_symlink():
            problems.append(f"missing symlink: {link}")
            continue
        actual_target = (link.parent / os.readlink(link)).resolve()
        if not actual_target.exists():
            problems.append(f"dangling symlink: {link} -> {actual_target}")
        elif actual_target != expected_target.resolve():
            problems.append(f"symlink points elsewhere: {link} -> {actual_target}")
    for runtime in ("codex", "claude"):
        root = user_home / f".{runtime}" / "agents"
        manifest = load_manifest(root / MANIFEST_NAME)
        extension = ".toml" if runtime == "codex" else ".md"
        expected_sources = sorted((repo_root / "agents" / runtime).glob(f"*{extension}"))
        expected_source_texts = {str(source) for source in expected_sources}
        for source in expected_sources:
            destination = root / source.name
            record = manifest.get("files", {}).get(str(destination))
            if not isinstance(record, dict):
                problems.append(f"missing ownership record: {destination}")
            elif record.get("source") != str(source):
                problems.append(f"agent copy points to another source: {destination}")
            elif record.get("pending_sha256") is not None:
                problems.append(f"incomplete agent install: {destination}")
            elif record.get("sha256") != sha256(source):
                problems.append(f"agent source changed after install: {source}")
            elif not destination.is_file():
                problems.append(f"missing agent copy: {destination}")
            elif sha256(destination) != sha256(source):
                problems.append(f"agent copy drift: {destination}")
        for path_text, record in manifest.get("files", {}).items():
            path = Path(path_text)
            if not isinstance(record, dict):
                problems.append(f"invalid ownership record: {path}")
            elif record.get("source") not in expected_source_texts:
                problems.append(f"orphaned agent copy: {path}")
    if problems:
        raise InstallError("; ".join(problems))
    return {"ok": True, "repo_root": str(repo_root), "projects": [str(p) for p in project_roots]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("install", "install-project", "verify"))
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--project-root", type=Path, action="append", default=[])
    parser.add_argument("--repair-links", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "install":
            result = install(args.repo_root, args.home, repair_links=args.repair_links)
        elif args.command == "install-project":
            if len(args.project_root) != 1:
                raise InstallError("install-project requires exactly one --project-root")
            result = install_project(
                args.repo_root, args.project_root[0], repair_links=args.repair_links
            )
        else:
            result = verify(args.repo_root, args.home, args.project_root)
    except InstallError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
