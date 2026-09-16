#!/usr/bin/env python3
"""Read-only OpenSpec dependency and delivery-package preflight for both harnesses."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


INSTALL = "npm install -g @fission-ai/openspec@1.13.0"
CHANGE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class OpenSpecError(RuntimeError):
    """Dependency or selected delivery package is not ready."""


def run_cli(binary: str, arguments: list[str], root: Path | None = None) -> str:
    try:
        result = subprocess.run(
            [binary, *arguments], cwd=root, text=True, capture_output=True,
            timeout=30, env={**os.environ, "OPENSPEC_TELEMETRY": "0"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise OpenSpecError(f"OpenSpec could not run: {exc}") from exc
    if result.returncode:
        detail = (result.stderr.strip() or result.stdout.strip())[-3000:]
        raise OpenSpecError(f"OpenSpec {' '.join(arguments)} failed: {detail}")
    return result.stdout.strip()


def verify_dependency() -> dict[str, str]:
    binary = shutil.which("openspec")
    if not binary:
        raise OpenSpecError(f"OpenSpec is required for delivery. Install with: {INSTALL}")
    version = run_cli(binary, ["--version"])
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match or not ((1, 13, 0) <= tuple(map(int, match.groups())) < (2, 0, 0)):
        raise OpenSpecError(f"Unsupported OpenSpec {version!r}; need >=1.13.0,<2.0.0. {INSTALL}")
    return {"binary": binary, "version": version}


def cli_json(binary: str, arguments: list[str], root: Path) -> dict[str, Any]:
    try:
        value = json.loads(run_cli(binary, arguments, root))
    except json.JSONDecodeError as exc:
        raise OpenSpecError("OpenSpec returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise OpenSpecError("OpenSpec returned an unexpected JSON shape")
    return value


def check_package(root: Path, change: str, *, complete: bool = False) -> dict[str, Any]:
    """Use OpenSpec's own state/parser; do not duplicate its Markdown grammar."""
    root = root.expanduser().resolve()
    if not root.is_dir() or not CHANGE_RE.fullmatch(change):
        raise OpenSpecError("Provide an existing --openspec-root and a kebab-case --openspec-change")
    dependency = verify_dependency()
    binary = dependency["binary"]
    status = cli_json(binary, ["status", "--change", change, "--json"], root)
    planning_root = status.get("planningHome", {}).get("root")
    if not planning_root or Path(planning_root).resolve() != root:
        raise OpenSpecError("Pass the actual OpenSpec planning root explicitly (including a store's checkout)")
    artifacts = status.get("artifacts")
    if (status.get("changeName") != change or not isinstance(artifacts, list)
            or not artifacts or any(item.get("status") not in {"done", "skipped"} for item in artifacts)):
        raise OpenSpecError("OpenSpec planning artifacts are incomplete; inspect openspec status")
    validation = cli_json(binary, [
        "validate", change, "--type", "change", "--strict", "--json", "--no-interactive",
    ], root)
    items = validation.get("items", [])
    if not items or any(item.get("valid") is not True for item in items):
        raise OpenSpecError("OpenSpec strict validation did not pass")
    apply = cli_json(binary, ["instructions", "apply", "--change", change, "--json"], root)
    if apply.get("state") not in {"ready", "all_done"}:
        raise OpenSpecError("OpenSpec apply is blocked; resolve its missing artifacts/tasks")
    tasks = apply.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise OpenSpecError("OpenSpec delivery requires a nonempty tracked task list")
    if complete and (apply["state"] != "all_done" or any(t.get("done") is not True for t in tasks)):
        raise OpenSpecError("OpenSpec tasks remain unfinished; delivery handoff is not complete")
    context_files = apply.get("contextFiles")
    if not isinstance(context_files, dict) or not context_files:
        raise OpenSpecError("OpenSpec apply returned no context files")
    files: list[str] = []
    for paths in context_files.values():
        # OpenSpec versions have exposed both one path and arrays per artifact.
        if not isinstance(paths, (str, list)):
            raise OpenSpecError("OpenSpec returned invalid context paths")
        for value in ([paths] if isinstance(paths, str) else paths):
            if not isinstance(value, str):
                raise OpenSpecError("OpenSpec returned a non-string context path")
            file = Path(value)
            if not file.is_absolute() or not file.is_file():
                raise OpenSpecError(f"Missing OpenSpec context file: {value}")
            files.append(str(file.resolve()))
    if not files:
        raise OpenSpecError("OpenSpec apply context files are empty")
    return {
        "root": str(root), "change": change, "version": dependency["version"],
        "read_set": list(dict.fromkeys(files)), "progress": apply.get("progress"),
        "state": apply["state"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openspec-root", type=Path)
    parser.add_argument("--openspec-change")
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    try:
        if args.openspec_root is None and args.openspec_change is None and not args.complete:
            result = verify_dependency()
        elif args.openspec_root and args.openspec_change:
            result = check_package(args.openspec_root, args.openspec_change, complete=args.complete)
        else:
            raise OpenSpecError("Package checks require both --openspec-root and --openspec-change")
    except OpenSpecError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, "result": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
