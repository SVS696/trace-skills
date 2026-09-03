#!/usr/bin/env python3
"""Verify the Smoke Break runtime dependency used by TRACE P23."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "integrations" / "smoke-break" / "dependency.json"
Runner = Callable[..., subprocess.CompletedProcess[str]]


class DependencyError(RuntimeError):
    """The dependency contract is invalid."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DependencyError(f"cannot read dependency contract: {path}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise DependencyError("unsupported Smoke Break dependency contract")
    runtimes = payload.get("runtimes")
    if not isinstance(runtimes, dict):
        raise DependencyError("dependency contract has no runtimes")
    for runtime in ("codex", "claude"):
        entry = runtimes.get(runtime)
        required = ("plugin_id", "marker_path", "reminder_prefix")
        if not isinstance(entry, dict) or not all(
            isinstance(entry.get(field), str) and entry[field] for field in required
        ):
            raise DependencyError(f"dependency contract has incomplete {runtime} metadata")
    return payload


def parse_env(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, raw_value = line.partition("=")
        if not separator or not key.strip():
            continue
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def positive_safe_integer(raw: str | None) -> int | None:
    if raw is None or not raw.strip():
        return None
    if "_" in raw:
        return None
    try:
        number = float(raw.strip())
    except ValueError:
        return None
    if not math.isfinite(number) or number <= 0 or not number.is_integer():
        return None
    value = int(number)
    return value if value <= 9_007_199_254_740_991 else None


def configured_interval(
    config_path: Path,
    contract: dict[str, Any],
    *,
    env: Mapping[str, str] = os.environ,
) -> dict[str, Any]:
    default = contract.get("default_interval_ms")
    recommended = contract.get("recommended_interval_ms")
    if not isinstance(default, int) or default <= 0:
        raise DependencyError("dependency contract has invalid default interval")
    if not isinstance(recommended, int) or recommended <= 0:
        raise DependencyError("dependency contract has invalid recommended interval")

    warnings: list[str] = []
    file_value: str | None = None
    try:
        file_value = parse_env(config_path.read_text(encoding="utf-8")).get(
            "SMOKE_BREAK_INTERVAL_MS"
        )
    except FileNotFoundError:
        pass
    except OSError as exc:
        warnings.append(f"cannot read config: {exc}")

    candidates = (
        ("config", file_value),
        ("environment", env.get("SMOKE_BREAK_INTERVAL_MS")),
    )
    for source, raw in candidates:
        if raw is None:
            continue
        interval = positive_safe_integer(raw)
        if interval is not None:
            return {
                "path": str(config_path),
                "source": source,
                "interval_ms": interval,
                "recommended": interval == recommended,
                "warnings": warnings,
            }
        warnings.append(f"ignored invalid {source} SMOKE_BREAK_INTERVAL_MS")

    return {
        "path": str(config_path),
        "source": "plugin-default",
        "interval_ms": default,
        "recommended": default == recommended,
        "warnings": warnings,
    }


def plugin_entries(runtime: str, payload: Any) -> list[dict[str, Any]]:
    if runtime == "codex":
        if not isinstance(payload, dict) or not isinstance(payload.get("installed"), list):
            raise DependencyError("unexpected Codex plugin inventory")
        entries = payload["installed"]
    elif runtime == "claude":
        if not isinstance(payload, list):
            raise DependencyError("unexpected Claude plugin inventory")
        entries = payload
    else:
        raise DependencyError(f"unsupported runtime: {runtime}")
    return [entry for entry in entries if isinstance(entry, dict)]


def plugin_source(runtime: str, entry: dict[str, Any]) -> Path | None:
    if runtime == "codex":
        source = entry.get("source")
        value = source.get("path") if isinstance(source, dict) else None
    else:
        value = entry.get("installPath")
    return Path(value) if isinstance(value, str) and value else None


def inspect_runtime(
    runtime: str,
    contract: dict[str, Any],
    *,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    plugin_id = contract["plugin_id"]
    command = [runtime, "plugin", "list", "--json"]
    try:
        result = runner(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        return {
            "state": "runtime_absent",
            "plugin_id": plugin_id,
            "installed": False,
            "enabled": False,
            "error": str(exc),
        }
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return {
            "state": "runtime_error",
            "plugin_id": plugin_id,
            "installed": False,
            "enabled": False,
            "error": detail or f"{runtime} plugin list failed",
        }
    try:
        entries = plugin_entries(runtime, json.loads(result.stdout))
    except (json.JSONDecodeError, DependencyError) as exc:
        return {
            "state": "inventory_error",
            "plugin_id": plugin_id,
            "installed": False,
            "enabled": False,
            "error": str(exc),
        }
    key = "pluginId" if runtime == "codex" else "id"
    match = next((entry for entry in entries if entry.get(key) == plugin_id), None)
    if match is None:
        return {
            "state": "plugin_missing",
            "plugin_id": plugin_id,
            "installed": False,
            "enabled": False,
        }

    installed = bool(match.get("installed", True))
    enabled = bool(match.get("enabled"))
    version = match.get("version")
    expected_version = contract.get("expected_version")
    expected_prefix = contract.get("expected_version_prefix")
    if isinstance(expected_version, str):
        version_matches = version == expected_version
    else:
        version_matches = (
            isinstance(version, str)
            and isinstance(expected_prefix, str)
            and version.startswith(expected_prefix)
        )

    source = plugin_source(runtime, match)
    marker_matches: bool | None = None
    marker_error: str | None = None
    if source is None:
        marker_error = "plugin inventory has no install path"
    else:
        marker = source / contract["marker_path"]
        try:
            marker_matches = contract["reminder_prefix"] in marker.read_text(encoding="utf-8")
        except OSError as exc:
            marker_error = str(exc)

    source_ref_matches: bool | None = True
    source_ref = contract.get("source_ref")
    actual_source_ref: str | None = None
    if isinstance(source_ref, str):
        if source is None:
            source_ref_matches = None
        else:
            marketplace_root = source.parent.parent
            try:
                revision = runner(
                    ["git", "-C", str(marketplace_root), "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                actual_source_ref = revision.stdout.strip() if revision.returncode == 0 else None
            except OSError:
                actual_source_ref = None
            source_ref_matches = actual_source_ref == source_ref if actual_source_ref else None

    unknown = version is None or marker_matches is None or source_ref_matches is None
    mismatch = (
        not installed
        or not enabled
        or (version is not None and not version_matches)
        or marker_matches is False
        or source_ref_matches is False
    )
    state = "plugin_drift" if mismatch else "unverified" if unknown else "ok"
    status = {
        "state": state,
        "plugin_id": plugin_id,
        "installed": installed,
        "enabled": enabled,
        "version": version,
        "version_matches": version_matches,
        "marker_matches": marker_matches,
        "source_ref_matches": source_ref_matches,
    }
    if actual_source_ref is not None:
        status["source_ref"] = actual_source_ref
    if marker_error is not None:
        status["marker_error"] = marker_error
    return status


def verify(
    contract: dict[str, Any],
    config_path: Path,
    runtimes: list[str],
    *,
    runner: Runner = subprocess.run,
    env: Mapping[str, str] = os.environ,
) -> dict[str, Any]:
    interval = configured_interval(config_path, contract, env=env)
    status = {
        runtime: inspect_runtime(runtime, contract["runtimes"][runtime], runner=runner)
        for runtime in runtimes
    }
    ok = all(item["state"] == "ok" for item in status.values())
    return {"ok": ok, "config": interval, "runtimes": status}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify",))
    parser.add_argument("--runtime", action="append", choices=("codex", "claude"), default=[])
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--config", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        contract = load_contract(args.contract)
        detected = [runtime for runtime in ("codex", "claude") if shutil.which(runtime)]
        runtimes = list(dict.fromkeys(args.runtime or detected))
        if not runtimes:
            raise DependencyError("no supported runtime CLI found; pass --runtime after installation")
        config = args.config
        if config is None:
            config = Path(
                os.environ.get("SMOKE_BREAK_CONFIG_FILE", Path.home() / ".smoke-break.env")
            ).expanduser()
        result = verify(contract, config, runtimes)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    except DependencyError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
