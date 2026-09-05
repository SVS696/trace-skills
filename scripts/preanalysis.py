#!/usr/bin/env python3
"""Validate pre-analysis briefs, plans, and decomposition decisions."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$")
BLOCK_RE = re.compile(r"^[A-Z][A-Z0-9_-]{1,31}$")
UNKNOWN_DISPOSITIONS = {"researchable", "user-decision", "external-owner", "implementation-only"}
SOLUTION_HORIZONS = {"tactical", "bounded-systemic", "generalized-capability"}


class DecisionError(RuntimeError):
    """Invalid decomposition decision."""


class BriefError(RuntimeError):
    """Invalid preliminary discovery brief."""


class PlanError(RuntimeError):
    """Invalid preliminary execution plan."""


def read_decision(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise DecisionError(f"cannot read decision {path}: {exc}") from exc
    return validate_decision(payload)


def required_text(payload: dict[str, Any], field: str, label: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise DecisionError(f"{label}.{field} is required")
    return value.strip()


def detect_cycle(graph: dict[str, list[str]], noun: str = "article") -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise DecisionError(f"{noun} dependency cycle includes {node}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)


def text_array(
    payload: dict[str, Any], field: str, label: str, *, non_empty: bool = False
) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise BriefError(f"{label}.{field} must be an array of non-empty strings")
    if non_empty and not value:
        raise BriefError(f"{label}.{field} must not be empty")
    return value


def source_ref_array(
    payload: dict[str, Any],
    field: str,
    label: str,
    source_ids: set[str] | None,
    *,
    non_empty: bool = False,
) -> list[str]:
    refs = text_array(payload, field, label, non_empty=non_empty)
    unknown_refs = set(refs) - source_ids if source_ids is not None else set()
    if unknown_refs:
        raise BriefError(f"{label}.{field} has unknown source refs: {sorted(unknown_refs)}")
    return refs


def validate_solution_boundary(boundary: Any, source_ids: set[str]) -> None:
    if not isinstance(boundary, dict):
        raise BriefError("brief.solution_boundary must be an object")
    label = "solution_boundary"
    horizon = boundary.get("horizon")
    if horizon not in SOLUTION_HORIZONS:
        raise BriefError(f"{label}.horizon is invalid")
    required_text(boundary, "observed_case", label)
    required_text(boundary, "root_capability", label)
    text_array(boundary, "invariants", label, non_empty=True)
    text_array(boundary, "hypothesized_variants", label)
    text_array(boundary, "current_scope", label, non_empty=True)
    seams = text_array(boundary, "extension_seams", label)
    absence_reason = boundary.get("extension_seam_absence_reason")
    if seams:
        if absence_reason is not None:
            raise BriefError(
                f"{label}.extension_seam_absence_reason must be null when extension_seams exist"
            )
    elif not isinstance(absence_reason, str) or not absence_reason.strip():
        raise BriefError(
            f"{label}.extension_seam_absence_reason is required when extension_seams are empty"
        )
    text_array(boundary, "deferred_variants", label)
    text_array(boundary, "expansion_triggers", label, non_empty=True)

    confirmed = boundary.get("confirmed_variants")
    if not isinstance(confirmed, list) or not confirmed:
        raise BriefError(f"{label}.confirmed_variants must be a non-empty array")
    variant_names: set[str] = set()
    for index, variant in enumerate(confirmed, start=1):
        variant_label = f"{label}.confirmed_variants[{index}]"
        if not isinstance(variant, dict):
            raise BriefError(f"{variant_label} must be an object")
        variant_name = required_text(variant, "name", variant_label)
        source_ref_array(
            variant,
            "evidence_refs",
            variant_label,
            source_ids,
            non_empty=True,
        )
        if variant_name in variant_names:
            raise BriefError(f"duplicate confirmed variant: {variant_name}")
        variant_names.add(variant_name)

    horizon_evidence = boundary.get("horizon_evidence")
    if not isinstance(horizon_evidence, dict):
        raise BriefError(f"{label}.horizon_evidence must be an object")
    source_ref_array(
        horizon_evidence,
        "analogy_search_refs",
        f"{label}.horizon_evidence",
        source_ids,
    )
    roadmap_refs = source_ref_array(
        horizon_evidence, "roadmap_refs", f"{label}.horizon_evidence", source_ids
    )
    irreversibility_refs = source_ref_array(
        horizon_evidence,
        "irreversibility_refs",
        f"{label}.horizon_evidence",
        source_ids,
    )

    hotfix = boundary.get("hotfix_exception")
    if horizon == "tactical":
        if not isinstance(hotfix, dict):
            raise BriefError(f"{label}.hotfix_exception is required for tactical horizon")
        for field in ("reason", "reversibility", "return_trigger"):
            required_text(hotfix, field, f"{label}.hotfix_exception")
        source_ref_array(
            hotfix,
            "evidence_refs",
            f"{label}.hotfix_exception",
            source_ids,
            non_empty=True,
        )
    elif hotfix is not None:
        raise BriefError(f"{label}.hotfix_exception must be null outside tactical horizon")

    if (
        horizon == "generalized-capability"
        and len(confirmed) < 2
        and not roadmap_refs
        and not irreversibility_refs
    ):
        raise BriefError(
            "generalized-capability requires two confirmed variants, roadmap refs, "
            "or irreversibility refs"
        )


def validate_brief(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") not in {1, 2}:
        raise BriefError("brief must use schema 1 or 2")
    try:
        required_text(payload, "subject_id", "brief")
        sources = payload.get("sources")
        if not isinstance(sources, list):
            raise BriefError("brief.sources must be an array")
        source_ids: set[str] = set()
        for index, source in enumerate(sources, start=1):
            label = f"sources[{index}]"
            if not isinstance(source, dict):
                raise BriefError(f"{label} must be an object")
            source_id = required_text(source, "id", label)
            required_text(source, "ref", label)
            required_text(source, "kind", label)
            if source_id in source_ids:
                raise BriefError(f"duplicate source id: {source_id}")
            source_ids.add(source_id)
        for section in ("problem", "goal", "solution_hypothesis"):
            value = payload.get(section)
            if not isinstance(value, dict):
                raise BriefError(f"brief.{section} must be an object")
            required_text(value, "statement", section)
            refs = value.get("evidence_refs", [])
            if not isinstance(refs, list) or not all(isinstance(item, str) for item in refs):
                raise BriefError(f"{section}.evidence_refs must be an array of source ids")
            unknown_refs = set(refs) - source_ids
            if unknown_refs:
                raise BriefError(f"{section} has unknown evidence refs: {sorted(unknown_refs)}")
        if payload["schema"] == 2:
            validate_solution_boundary(payload.get("solution_boundary"), source_ids)
        stories = payload.get("preliminary_user_stories")
        if not isinstance(stories, list):
            raise BriefError("brief.preliminary_user_stories must be an array")
        story_ids: set[str] = set()
        for index, story in enumerate(stories, start=1):
            label = f"preliminary_user_stories[{index}]"
            if not isinstance(story, dict):
                raise BriefError(f"{label} must be an object")
            story_id = required_text(story, "id", label)
            for field in ("actor", "need", "value"):
                required_text(story, field, label)
            if story_id in story_ids:
                raise BriefError(f"duplicate user story id: {story_id}")
            story_ids.add(story_id)
        for field in ("scope_in", "scope_out", "unknowns", "assumptions", "dependencies"):
            if not isinstance(payload.get(field), list):
                raise BriefError(f"brief.{field} must be an array")
        unknown_ids: set[str] = set()
        for index, unknown in enumerate(payload["unknowns"], start=1):
            label = f"unknowns[{index}]"
            if not isinstance(unknown, dict):
                raise BriefError(f"{label} must be a classified object")
            unknown_id = required_text(unknown, "id", label)
            required_text(unknown, "statement", label)
            required_text(unknown, "reason", label)
            disposition = unknown.get("disposition")
            if disposition not in UNKNOWN_DISPOSITIONS:
                raise BriefError(f"{label}.disposition is invalid")
            blocking = unknown.get("blocks_specification")
            if not isinstance(blocking, bool):
                raise BriefError(f"{label}.blocks_specification must be boolean")
            if disposition in {"researchable", "user-decision"} and not blocking:
                raise BriefError(f"{label} {disposition} must block specification completeness")
            if disposition == "implementation-only" and blocking:
                raise BriefError(f"{label} implementation-only cannot block specification completeness")
            if disposition == "user-decision":
                required_text(unknown, "question", label)
            if disposition == "external-owner":
                required_text(unknown, "owner_ref", label)
            if unknown_id in unknown_ids:
                raise BriefError(f"duplicate unknown id: {unknown_id}")
            unknown_ids.add(unknown_id)
        estimate = payload.get("estimate")
        if not isinstance(estimate, dict):
            raise BriefError("brief.estimate must be an object")
        estimate_status = estimate.get("status")
        if estimate_status == "unavailable":
            required_text(estimate, "reason", "estimate")
        elif estimate_status == "estimated":
            minimum = estimate.get("min")
            maximum = estimate.get("max")
            if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
                raise BriefError("estimated range must contain numeric min and max")
            if minimum < 0 or maximum < minimum:
                raise BriefError("estimated range is invalid")
            required_text(estimate, "unit", "estimate")
            required_text(estimate, "confidence", "estimate")
            if not isinstance(estimate.get("basis"), list) or not estimate["basis"]:
                raise BriefError("estimated range requires a non-empty basis")
        else:
            raise BriefError("estimate.status must be estimated or unavailable")
    except DecisionError as exc:
        raise BriefError(str(exc)) from exc
    return payload


def validate_plan(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise PlanError("plan must use schema 1")
    try:
        required_text(payload, "subject_id", "plan")
        if payload.get("status") not in {"proposed", "approved"}:
            raise PlanError("plan.status must be proposed or approved")
        if payload.get("status") == "approved":
            required_text(payload, "decision_ref", "plan")
        route = payload.get("route")
        if route not in {"stop", "specification"}:
            raise PlanError("plan.route is invalid")
        tasks = payload.get("tasks")
        if not isinstance(tasks, list):
            raise PlanError("plan.tasks must be an array")
        if route != "stop" and not tasks:
            raise PlanError("non-stop plan requires at least one task")
        article_ids = payload.get("article_ids")
        if not isinstance(article_ids, list) or not all(
            isinstance(item, str) and ID_RE.fullmatch(item) for item in article_ids
        ):
            raise PlanError("plan.article_ids must be an array of article ids")
        if len(article_ids) != len(set(article_ids)):
            raise PlanError("plan.article_ids contains duplicates")
        if route != "stop" and not article_ids:
            raise PlanError("non-stop plan requires at least one article id")
        ids: set[str] = set()
        graph: dict[str, list[str]] = {}
        for index, task in enumerate(tasks, start=1):
            label = f"tasks[{index}]"
            if not isinstance(task, dict):
                raise PlanError(f"{label} must be an object")
            task_id = required_text(task, "id", label)
            for field in ("title", "output"):
                required_text(task, field, label)
            dependencies = task.get("depends_on")
            if not isinstance(dependencies, list) or not all(
                isinstance(item, str) for item in dependencies
            ):
                raise PlanError(f"{label}.depends_on must be an array of ids")
            if task_id in ids:
                raise PlanError(f"duplicate task id: {task_id}")
            ids.add(task_id)
            graph[task_id] = dependencies
        for task_id, dependencies in graph.items():
            unknown = set(dependencies) - ids
            if unknown:
                raise PlanError(f"{task_id} has unknown dependencies: {sorted(unknown)}")
            if task_id in dependencies:
                raise PlanError(f"{task_id} cannot depend on itself")
        try:
            detect_cycle(graph, "task")
        except DecisionError as exc:
            raise PlanError(str(exc)) from exc
        sync = payload.get("external_sync", {"status": "not_requested"})
        if not isinstance(sync, dict):
            raise PlanError("plan.external_sync must be an object")
        if sync.get("status") not in {"not_requested", "authorized", "synced"}:
            raise PlanError("external_sync.status is invalid")
        if sync.get("status") in {"authorized", "synced"}:
            required_text(sync, "system", "external_sync")
        if sync.get("status") == "synced":
            required_text(sync, "target_ref", "external_sync")
            required_text(sync, "readback_ref", "external_sync")
    except DecisionError as exc:
        raise PlanError(str(exc)) from exc
    return payload


def validate_decision(payload: Any, *, require_approved: bool = False) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") not in {1, 2}:
        raise DecisionError("decision must use schema 1 or 2")
    required_text(payload, "subject_id", "decision")
    status = payload.get("status")
    if status not in {"proposed", "approved"}:
        raise DecisionError("decision.status must be proposed or approved")
    if require_approved and status != "approved":
        raise DecisionError("decision must be approved before case initialization")
    if status == "approved":
        required_text(payload, "decision_ref", "decision")
    decision = payload.get("decision")
    if decision not in {"single", "split"}:
        raise DecisionError("decision.decision must be single or split")
    required_text(payload, "reason", "decision")
    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise DecisionError("decision.articles must be an array")
    if decision == "single" and len(articles) != 1:
        raise DecisionError("single decision requires exactly one article")
    if decision == "split" and len(articles) < 2:
        raise DecisionError("split decision requires at least two articles")
    ids: list[str] = []
    graph: dict[str, list[str]] = {}
    for index, article in enumerate(articles, start=1):
        label = f"articles[{index}]"
        if not isinstance(article, dict):
            raise DecisionError(f"{label} must be an object")
        article_id = required_text(article, "id", label)
        if not ID_RE.fullmatch(article_id):
            raise DecisionError(f"{label}.id is invalid: {article_id}")
        if article_id in ids:
            raise DecisionError(f"duplicate article id: {article_id}")
        ids.append(article_id)
        for field in ("title", "goal", "outcome", "acceptance_boundary"):
            required_text(article, field, label)
        dependencies = article.get("dependencies")
        if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
            raise DecisionError(f"{label}.dependencies must be an array of ids")
        graph[article_id] = dependencies
        composition = article.get("composition")
        if composition != "article-led":
            raise DecisionError(f"{label}.composition must be article-led")
        if payload["schema"] == 2:
            try:
                validate_solution_boundary(article.get("solution_boundary"), None)
            except (BriefError, DecisionError) as exc:
                raise DecisionError(f"{label}.solution_boundary is invalid: {exc}") from exc
        blocks = article.get("blocks")
        if not isinstance(blocks, list):
            raise DecisionError(f"{label}.blocks must be an array")
        block_ids: set[str] = set()
        for block_index, block in enumerate(blocks, start=1):
            block_label = f"{label}.blocks[{block_index}]"
            if not isinstance(block, dict):
                raise DecisionError(f"{block_label} must be an object")
            block_id = required_text(block, "id", block_label)
            required_text(block, "title", block_label)
            if not BLOCK_RE.fullmatch(block_id) or block_id in block_ids:
                raise DecisionError(f"invalid or duplicate block id: {block_id}")
            block_ids.add(block_id)
        if not block_ids:
            raise DecisionError(f"{label} requires at least one semantic block")
        if "ARTICLE" in block_ids:
            raise DecisionError(f"{label} ARTICLE is reserved for whole-article stages")
    known = set(ids)
    for article_id, dependencies in graph.items():
        unknown = set(dependencies) - known
        if unknown:
            raise DecisionError(f"{article_id} has unknown dependencies: {sorted(unknown)}")
        if article_id in dependencies:
            raise DecisionError(f"{article_id} cannot depend on itself")
    detect_cycle(graph)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "validate-decision", "validate-brief", "validate-plan"))
    parser.add_argument("--decision", type=Path)
    parser.add_argument("--brief", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--require-approved", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command in {"validate", "validate-decision"}:
            if args.decision is None:
                raise DecisionError("--decision is required")
            payload = json.loads(args.decision.read_text(encoding="utf-8"))
            validate_decision(payload, require_approved=args.require_approved)
            result = {"ok": True, "articles": len(payload["articles"])}
        elif args.command == "validate-brief":
            if args.brief is None:
                raise BriefError("--brief is required")
            payload = json.loads(args.brief.read_text(encoding="utf-8"))
            validate_brief(payload)
            result = {"ok": True, "sources": len(payload["sources"])}
        else:
            if args.plan is None:
                raise PlanError("--plan is required")
            payload = json.loads(args.plan.read_text(encoding="utf-8"))
            validate_plan(payload)
            result = {"ok": True, "tasks": len(payload["tasks"])}
    except (OSError, json.JSONDecodeError, DecisionError, BriefError, PlanError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
