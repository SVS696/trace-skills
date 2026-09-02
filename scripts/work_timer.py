#!/usr/bin/env python3
"""Record observable process events and export a Work Metrics source."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = 1
MARKERS = {
    "work_started",
    "pause_started",
    "limit_exhausted",
    "deferred",
    "resume",
    "work_finished",
    "ready_for_handoff",
    "handoff",
    "user_stopped",
    "guard_stopped",
    "cancelled",
    "external_failure",
}
TERMINAL = {"work_finished", "handoff", "user_stopped", "guard_stopped", "cancelled", "external_failure"}
PAUSED = {"pause_started", "limit_exhausted", "deferred"}


class TimerError(RuntimeError):
    """Invalid ledger or lifecycle transition."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str | None) -> str:
    if value is None:
        return now()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TimerError(f"invalid timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise TimerError("timestamp must include a timezone")
    return parsed.isoformat()


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


def load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise TimerError(f"cannot read ledger {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise TimerError("unsupported ledger schema")
    if not isinstance(payload.get("events"), list):
        raise TimerError("ledger events must be an array")
    return payload


def latest_marker(payload: dict[str, Any]) -> str | None:
    markers = [event["state"] for event in payload["events"] if event.get("type") == "state_marker"]
    return markers[-1] if markers else None


def next_id(payload: dict[str, Any], prefix: str) -> str:
    return f"{prefix}-{len(payload['events']) + 1:04d}"


def validate_transition(previous: str | None, current: str) -> None:
    if previous is None and current != "work_started":
        raise TimerError("first marker must be work_started")
    if previous in TERMINAL:
        raise TimerError(f"terminal state {previous} cannot continue in the same work item")
    if current == "work_started" and previous is not None:
        raise TimerError("work_started can occur only once")
    if current == "resume" and previous not in PAUSED | {"ready_for_handoff"}:
        raise TimerError("resume requires an explicit paused or ready state")
    if previous in PAUSED and current not in {"resume"} | TERMINAL:
        raise TimerError(f"{previous} requires resume or terminal stop")
    if previous == "ready_for_handoff" and current not in {"handoff", "resume"} | TERMINAL:
        raise TimerError("ready_for_handoff requires handoff, resume, or terminal stop")


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    ledger = args.ledger.resolve()
    if ledger.exists():
        raise TimerError(f"ledger already exists: {ledger}")
    payload = {
        "schema": SCHEMA,
        "work_item_id": args.work_item,
        "source_id": args.source_id,
        "source_kind": args.source_kind,
        "created_at": now(),
        "events": [],
    }
    atomic_json(ledger, payload)
    return payload


def command_mark(args: argparse.Namespace) -> dict[str, Any]:
    ledger = args.ledger.resolve()
    payload = load(ledger)
    validate_transition(latest_marker(payload), args.state)
    event = {
        "id": next_id(payload, "marker"),
        "type": "state_marker",
        "at": parse_time(args.at),
        "state": args.state,
    }
    if args.reason:
        event["attributes"] = {"reason": args.reason}
    payload["events"].append(event)
    atomic_json(ledger, payload)
    return event


def command_pulse(args: argparse.Namespace) -> dict[str, Any]:
    ledger = args.ledger.resolve()
    payload = load(ledger)
    previous = latest_marker(payload)
    if previous is None or previous in TERMINAL | PAUSED:
        raise TimerError("activity pulse requires an active lifecycle")
    event = {
        "id": next_id(payload, "pulse"),
        "type": "activity_pulse",
        "at": parse_time(args.at),
        "category": args.category,
        "attributes": {},
    }
    payload["events"].append(event)
    atomic_json(ledger, payload)
    return event


def command_export(args: argparse.Namespace) -> dict[str, Any]:
    payload = load(args.ledger.resolve())
    if latest_marker(payload) is None:
        raise TimerError("cannot export a source without work_started")
    times = [event["at"] for event in payload["events"]]
    terminal = latest_marker(payload) in TERMINAL
    source = {
        "id": payload["source_id"],
        "kind": payload["source_kind"],
        "required_for_coverage": True,
        "coverage": {
            "status": "complete" if terminal else "partial",
            "started_at": min(times),
            "ended_at": max(times),
            "reason": None if terminal else "lifecycle_active",
        },
        "events": payload["events"],
    }
    if args.output:
        atomic_json(args.output.resolve(), source)
    return source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--ledger", type=Path, required=True)
    init.add_argument("--work-item", required=True)
    init.add_argument("--source-id", required=True)
    init.add_argument("--source-kind", default="harness")
    init.set_defaults(handler=command_init)

    mark = subparsers.add_parser("mark")
    mark.add_argument("--ledger", type=Path, required=True)
    mark.add_argument("--state", choices=sorted(MARKERS), required=True)
    mark.add_argument("--at")
    mark.add_argument("--reason")
    mark.set_defaults(handler=command_mark)

    pulse = subparsers.add_parser("pulse")
    pulse.add_argument("--ledger", type=Path, required=True)
    pulse.add_argument("--at")
    pulse.add_argument("--category", default="model")
    pulse.set_defaults(handler=command_pulse)

    export = subparsers.add_parser("export-source")
    export.add_argument("--ledger", type=Path, required=True)
    export.add_argument("--output", type=Path)
    export.set_defaults(handler=command_export)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = args.handler(args)
    except TimerError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
