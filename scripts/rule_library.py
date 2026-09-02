#!/usr/bin/env python3
"""Validate and materialize bounded method-library routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "library" / "manifest.json"
OVERRIDES = ROOT / "library" / "route-overrides.json"
MARKERS = {
    "requirements": "<!-- vigers:routes -->",
    "delivery": "<!-- delivery-engineering:routes -->",
}
RULE_HEADING = {
    "requirements": re.compile(r"^(?:C|T|D)\d{2}\. "),
    "delivery": re.compile(r"^(?:E|B|F|T|S)\d{2}\. "),
}


class LibraryError(RuntimeError):
    """Invalid method library or route request."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise LibraryError(f"cannot read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise LibraryError(f"JSON root must be an object: {path}")
    return payload


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_embedded_json(path: Path, marker: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    marker_at = text.find(marker)
    if marker_at < 0:
        raise LibraryError(f"route marker is missing in {path}")
    match = re.search(r"```json\s*(\{.*?\})\s*```", text[marker_at:], re.DOTALL)
    if not match:
        raise LibraryError(f"route JSON is missing after marker in {path}")
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise LibraryError(f"invalid route JSON in {path}: {exc}") from exc
    return payload


def domain_root(domain: str) -> Path:
    return ROOT / "library" / domain


def load_routes(domain: str) -> dict[str, Any]:
    manifest = read_json(MANIFEST)
    domains = manifest.get("domains", {})
    if domain not in domains:
        raise LibraryError(f"unknown domain: {domain}")
    router = ROOT / domains[domain]["router"]
    payload = extract_embedded_json(router, MARKERS[domain])
    routes = payload.get("routes")
    if not isinstance(routes, list):
        raise LibraryError(f"routes must be an array for {domain}")
    overlay = read_json(OVERRIDES).get("domains", {}).get(domain, {})
    by_id = {route.get("id"): route for route in routes if isinstance(route, dict)}
    for route_id, additions in overlay.get("extend", {}).items():
        if route_id not in by_id:
            raise LibraryError(f"override targets unknown route: {domain}/{route_id}")
        by_id[route_id].setdefault("distilled", []).extend(additions)
    routes.extend(overlay.get("add", []))
    return {
        "default_route": payload.get("default_route"),
        "routes": routes,
        "source": str(router.relative_to(ROOT)),
    }


def headings(path: Path) -> list[tuple[int, str, int]]:
    result: list[tuple[int, str, int]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            result.append((len(match.group(1)), match.group(2), index))
    return result


def extract_heading(path: Path, title: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    candidates = [entry for entry in headings(path) if entry[1] == title]
    if len(candidates) != 1:
        raise LibraryError(f"expected one heading {title!r} in {path}, found {len(candidates)}")
    level, _, start = candidates[0]
    end = len(lines)
    for next_level, _, next_start in headings(path):
        if next_start > start and next_level <= level:
            end = next_start
            break
    return "\n".join(lines[start:end]).rstrip() + "\n"


def route_by_id(domain: str, route_id: str) -> dict[str, Any]:
    matches = [route for route in load_routes(domain)["routes"] if route.get("id") == route_id]
    if len(matches) != 1:
        raise LibraryError(f"expected one route {domain}/{route_id}, found {len(matches)}")
    return matches[0]


def resolve_section(domain: str, item: dict[str, Any]) -> tuple[Path, str]:
    file_value = item.get("file")
    title = item.get("heading")
    if not isinstance(file_value, str) or not isinstance(title, str):
        raise LibraryError(f"invalid section reference in {domain}: {item}")
    path = (domain_root(domain) / file_value).resolve()
    try:
        path.relative_to(domain_root(domain).resolve())
    except ValueError as exc:
        raise LibraryError(f"section escapes library root: {file_value}") from exc
    if not path.is_file():
        raise LibraryError(f"section file is missing: {path}")
    extract_heading(path, title)
    return path, title


def all_referenced_sections(domain: str) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for route in load_routes(domain)["routes"]:
        for item in route.get("distilled", []):
            path, title = resolve_section(domain, item)
            result.add((str(path.relative_to(domain_root(domain))), title))
    return result


def validate() -> dict[str, Any]:
    manifest = read_json(MANIFEST)
    if manifest.get("schema") != 1:
        raise LibraryError("library manifest must use schema 1")
    checked_files = 0
    route_counts: dict[str, int] = {}
    rule_counts: dict[str, int] = {}
    for domain, config in manifest["domains"].items():
        for mirror in config.get("mirrors", []):
            path = ROOT / mirror["path"]
            if not path.is_file():
                raise LibraryError(f"mirrored source is missing: {path}")
            actual = digest(path)
            if actual != mirror["sha256"]:
                raise LibraryError(f"mirrored source drift: {path} expected {mirror['sha256']} got {actual}")
            checked_files += 1
        route_payload = load_routes(domain)
        ids = [route.get("id") for route in route_payload["routes"]]
        if len(ids) != len(set(ids)) or None in ids:
            raise LibraryError(f"duplicate or missing route id in {domain}")
        for route in route_payload["routes"]:
            for title in route.get("core", []):
                if domain != "requirements":
                    raise LibraryError(f"core headings are unsupported for {domain}")
                extract_heading(domain_root(domain) / "references" / "requirements-method.md", title)
            for item in route.get("distilled", []):
                resolve_section(domain, item)
        referenced = all_referenced_sections(domain)
        defined: set[tuple[str, str]] = set()
        pattern = RULE_HEADING[domain]
        for path in (domain_root(domain) / "references").glob("native-*.md"):
            for _, title, _ in headings(path):
                if pattern.match(title):
                    defined.add((str(path.relative_to(domain_root(domain))), title))
        missing = sorted(defined - referenced)
        if missing:
            rendered = ", ".join(f"{path}#{title}" for path, title in missing)
            raise LibraryError(f"unrouted native rules in {domain}: {rendered}")
        route_counts[domain] = len(ids)
        rule_counts[domain] = len(defined)
    return {
        "ok": True,
        "mirrored_files": checked_files,
        "routes": route_counts,
        "native_rules": rule_counts,
    }


def choose_route(domain: str, task: str) -> dict[str, Any]:
    payload = load_routes(domain)
    normalized = task.casefold()
    scored: list[tuple[int, int, dict[str, Any], list[str]]] = []
    for index, route in enumerate(payload["routes"]):
        signals = [signal for signal in route.get("signals", []) if signal.casefold() in normalized]
        scored.append((len(signals), -index, route, signals))
    best = max(scored, key=lambda value: (value[0], value[1])) if scored else None
    if not best or best[0] == 0:
        route = route_by_id(domain, payload["default_route"])
        signals: list[str] = []
    else:
        route = best[2]
        signals = best[3]
    return {
        "domain": domain,
        "route": route["id"],
        "matched_signals": signals,
        "when": route.get("when"),
    }


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def materialize(domain: str, route_ids: list[str], output: Path) -> dict[str, Any]:
    if not route_ids:
        raise LibraryError("at least one --route is required")
    if len(route_ids) > 2:
        raise LibraryError("at most two routes may be materialized together")
    if domain == "delivery" and len([item for item in route_ids if item != "core-change"]) > 1:
        raise LibraryError("delivery materialization allows core-change plus one specialized route")
    selected = list(route_ids)
    if domain == "delivery" and "core-change" not in selected:
        selected.insert(0, "core-change")
    sections: list[tuple[Path, str]] = []
    fallbacks: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for route_id in selected:
        route = route_by_id(domain, route_id)
        if domain == "requirements":
            method = domain_root(domain) / "references" / "requirements-method.md"
            for title in route.get("core", []):
                key = (str(method), title)
                if key not in seen:
                    sections.append((method, title))
                    seen.add(key)
        for item in route.get("distilled", []):
            path, title = resolve_section(domain, item)
            key = (str(path), title)
            if key not in seen:
                sections.append((path, title))
                seen.add(key)
        fallbacks.extend(route.get("fallback", []))
    manifest = read_json(MANIFEST)["domains"][domain]
    chunks = [
        f"# Method basis: {domain}\n",
        f"- routes: `{', '.join(selected)}`\n",
        f"- source commit: `{manifest['source_commit']}`\n",
        f"- process kernel: `rules/process-kernel.md`\n",
        "\n",
    ]
    for path, title in sections:
        chunks.append(f"<!-- source: {path.relative_to(ROOT)}#{title} -->\n")
        chunks.append(extract_heading(path, title))
        chunks.append("\n")
    if fallbacks:
        chunks.append("## Fallbacks not loaded\n\n")
        chunks.append("Open these only when the distilled sections do not answer the exact question.\n\n")
        for fallback in fallbacks:
            chunks.append(f"- `{json.dumps(fallback, ensure_ascii=False)}`\n")
    atomic_text(output.resolve(), "".join(chunks))
    return {
        "ok": True,
        "domain": domain,
        "routes": selected,
        "sections": len(sections),
        "output": str(output.resolve()),
        "sha256": digest(output.resolve()),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate")

    listing = subparsers.add_parser("list")
    listing.add_argument("--domain", choices=tuple(MARKERS), required=True)

    route = subparsers.add_parser("route")
    route.add_argument("--domain", choices=tuple(MARKERS), required=True)
    route.add_argument("--task", required=True)

    render = subparsers.add_parser("materialize")
    render.add_argument("--domain", choices=tuple(MARKERS), required=True)
    render.add_argument("--route", action="append", required=True)
    render.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "validate":
            result = validate()
        elif args.command == "list":
            payload = load_routes(args.domain)
            result = {
                "domain": args.domain,
                "default_route": payload["default_route"],
                "routes": [route["id"] for route in payload["routes"]],
            }
        elif args.command == "route":
            result = choose_route(args.domain, args.task)
        else:
            result = materialize(args.domain, args.route, args.output)
    except (OSError, LibraryError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
