#!/usr/bin/env python3
"""Validate a project adapter without mutating the project."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


class SetupError(RuntimeError):
    """Invalid or stale project adapter."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise SetupError("setup must use schema 1")
    root_value = payload.get("project_root")
    root_env = payload.get("project_root_env")
    if bool(root_value) == bool(root_env):
        raise SetupError("setup must define exactly one project_root or project_root_env")
    if root_env:
        if not isinstance(root_env, str) or not root_env.strip():
            raise SetupError("setup.project_root_env must be a non-empty string")
        root_value = os.environ.get(root_env)
        if not root_value:
            raise SetupError(f"environment variable is not set: {root_env}")
    root = Path(str(root_value)).expanduser()
    if not root.is_dir():
        raise SetupError(f"project root is missing: {root}")
    instructions = payload.get("instructions")
    if not isinstance(instructions, list) or not instructions:
        raise SetupError("setup.instructions must be a non-empty array")
    for relative in instructions:
        if not isinstance(relative, str) or not (root / relative).is_file():
            raise SetupError(f"project instruction is missing: {relative}")
    template = payload.get("template")
    if not isinstance(template, dict):
        raise SetupError("setup.template must be an object")
    template_path = root / str(template.get("path", ""))
    if not template_path.is_file():
        raise SetupError(f"project template is missing: {template_path}")
    actual = digest(template_path)
    if actual != template.get("sha256"):
        raise SetupError(f"project template changed: expected {template.get('sha256')}, got {actual}")
    routes = payload.get("routes")
    expected = {"method", "preanalysis", "specification", "implementation", "timer", "legacy"}
    if not isinstance(routes, dict) or set(routes) != expected:
        raise SetupError("setup.routes must define the six workflow routes exactly")
    return {"project_id": payload.get("project_id"), "template_sha256": actual}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("setup", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.setup.read_text(encoding="utf-8"))
        result = validate(payload)
    except (OSError, json.JSONDecodeError, SetupError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
