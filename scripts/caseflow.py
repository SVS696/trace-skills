#!/usr/bin/env python3
"""Deterministic state for the Workflow Skills specification process."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .preanalysis import DecisionError, validate_decision
except ImportError:  # Direct script execution.
    from preanalysis import DecisionError, validate_decision


SCHEMA = 1
STAGES = (1, 2, 3, 4)
ITEM_STATUSES = {"open", "applied", "verified", "waived"}
GATING_SEVERITIES = {"critical", "major"}
BLOCK_RE = re.compile(r"^[A-Z][A-Z0-9_-]{1,31}$")
ITEM_RE = re.compile(r"^D([1-4])-\d{3}$")
PROCESS_KERNEL = Path(__file__).resolve().parent.parent / "rules" / "process-kernel.md"


class CaseFlowError(RuntimeError):
    """Invalid command, case state, or artifact."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseFlowError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaseFlowError(f"invalid JSON in {path}: {exc}") from exc


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


def digest(path: Path) -> str:
    if not path.is_file():
        raise CaseFlowError(f"artifact is not a file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_artifact(case_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = case_root / path
    return path.resolve()


def relative_or_absolute(case_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(case_root))
    except ValueError:
        return str(path)


def manifest_path(case_root: Path) -> Path:
    return case_root / "case.json"


def load_case(case_root: Path) -> dict[str, Any]:
    payload = read_json(manifest_path(case_root))
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise CaseFlowError("unsupported case schema")
    if payload.get("stage") not in STAGES:
        raise CaseFlowError("case stage is invalid")
    if not isinstance(payload.get("blocks"), list) or not payload["blocks"]:
        raise CaseFlowError("case has no blocks")
    return payload


def save_case(case_root: Path, payload: dict[str, Any], event: str) -> None:
    payload["updated_at"] = now()
    payload.setdefault("events", []).append({"at": payload["updated_at"], "event": event})
    atomic_json(manifest_path(case_root), payload)


def stage_record(payload: dict[str, Any], stage: int | None = None) -> dict[str, Any]:
    stage = stage or int(payload["stage"])
    return payload["stages"][str(stage)]


def parse_block(value: str) -> dict[str, str]:
    block_id, separator, title = value.partition(":")
    if not separator or not BLOCK_RE.fullmatch(block_id) or not title.strip():
        raise argparse.ArgumentTypeError("block must be ID:Title with a stable uppercase ID")
    return {"id": block_id, "title": title.strip()}


def validate_diff_pool(path: Path, stage: int) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise CaseFlowError("required diff must use schema 1")
    if payload.get("stage") != stage:
        raise CaseFlowError(f"required diff stage must be {stage}")
    items = payload.get("items")
    if not isinstance(items, list):
        raise CaseFlowError("required diff items must be an array")
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise CaseFlowError("every diff item must be an object")
        item_id = item.get("id")
        match = ITEM_RE.fullmatch(str(item_id))
        if not match or int(match.group(1)) != stage:
            raise CaseFlowError(f"invalid diff item id for stage {stage}: {item_id}")
        if item_id in seen:
            raise CaseFlowError(f"duplicate diff item id: {item_id}")
        seen.add(item_id)
        for field in ("target", "change", "reason"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise CaseFlowError(f"{item_id}.{field} is required")
        status = item.get("status")
        if status not in ITEM_STATUSES:
            raise CaseFlowError(f"{item_id}.status is invalid")
        if status in {"applied", "verified"} and not item.get("receipt"):
            raise CaseFlowError(f"{item_id} {status} without correction receipt")
        if status == "verified" and not item.get("verification_receipt"):
            raise CaseFlowError(f"{item_id} verified without verification receipt")
        if status == "waived" and not item.get("decision_ref"):
            raise CaseFlowError(f"{item_id} waived without decision_ref")
    return payload


def require_state(payload: dict[str, Any], *states: str) -> None:
    if payload.get("state") not in states:
        expected = ", ".join(states)
        raise CaseFlowError(f"state must be one of [{expected}], got {payload.get('state')}")


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    if manifest_path(case_root).exists():
        raise CaseFlowError(f"case already exists: {case_root}")
    template = args.template.expanduser().resolve()
    if not template.is_file():
        raise CaseFlowError(f"template does not exist: {template}")
    decision_path = args.decision.expanduser().resolve()
    try:
        decision = validate_decision(read_json(decision_path), require_approved=True)
    except DecisionError as exc:
        raise CaseFlowError(str(exc)) from exc
    matches = [article for article in decision["articles"] if article["id"] == args.article_id]
    if not matches:
        raise CaseFlowError(f"article id is not present in decision: {args.article_id}")
    article = matches[0]
    blocks = article["blocks"]
    ids = [block["id"] for block in blocks]
    case_root.mkdir(parents=True, exist_ok=True)
    for block_id in ids:
        (case_root / "blocks" / block_id).mkdir(parents=True, exist_ok=True)
    (case_root / "stitches").mkdir(exist_ok=True)
    (case_root / "diffs").mkdir(exist_ok=True)
    (case_root / "method-basis").mkdir(exist_ok=True)
    created = now()
    stages = {
        str(stage): {
            "state": "pending" if stage > 1 else "blocks",
            "submissions": {},
            "stitch": None,
            "diff_pool": None,
        }
        for stage in STAGES
    }
    payload = {
        "schema": SCHEMA,
        "case_id": article["id"],
        "title": article["title"],
        "composition": article["composition"],
        "decomposition_decision": {
            "path": str(decision_path),
            "sha256": digest(decision_path),
            "decision_ref": decision["decision_ref"],
        },
        "template": str(template),
        "template_sha256": digest(template),
        "stage": 1,
        "state": "blocks",
        "route": None,
        "article": None,
        "review_rounds": [],
        "blocks": blocks,
        "stages": stages,
        "created_at": created,
        "updated_at": created,
        "events": [{"at": created, "event": "case_initialized"}],
    }
    atomic_json(manifest_path(case_root), payload)
    return payload


def command_status(args: argparse.Namespace) -> dict[str, Any]:
    payload = load_case(args.case_root.resolve())
    current = stage_record(payload)
    open_count = None
    if current.get("diff_pool"):
        pool_path = resolve_artifact(args.case_root.resolve(), current["diff_pool"]["path"])
        pool = validate_diff_pool(pool_path, int(payload["stage"]))
        open_count = sum(item["status"] in {"open", "applied"} for item in pool["items"])
    return {
        "case_id": payload["case_id"],
        "stage": payload["stage"],
        "state": payload["state"],
        "route": payload["route"],
        "submitted_blocks": sorted(current["submissions"]),
        "required_blocks": [block["id"] for block in payload["blocks"]],
        "open_diff_items": open_count,
        "next_skill": "delivery-workflow" if payload["route"] == "delivery" else "spec-workflow",
    }


def command_context(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    stage = int(payload["stage"])
    if args.block and args.block not in {item["id"] for item in payload["blocks"]}:
        raise CaseFlowError(f"unknown block: {args.block}")
    read_set: list[str] = [str(PROCESS_KERNEL), payload["template"]]
    if args.block:
        read_set.append(str(case_root / "method-basis" / f"stage-{stage:02d}-{args.block}.md"))
    source_index = case_root / "sources.md"
    if stage == 1:
        if source_index.exists():
            read_set.append(str(source_index))
        if args.block:
            source_map = case_root / "blocks" / args.block / "source-map.md"
            if source_map.exists():
                read_set.append(str(source_map))
    elif stage in (2, 3):
        previous = stage - 1
        if args.block:
            read_set.append(str(case_root / "blocks" / args.block / f"stage-{previous:02d}.md"))
        else:
            read_set.extend(
                str(case_root / "blocks" / item["id"] / f"stage-{previous:02d}.md")
                for item in payload["blocks"]
            )
        read_set.append(str(case_root / "stitches" / f"stage-{previous:02d}.md"))
    else:
        read_set.extend(
            str(case_root / "blocks" / item["id"] / "stage-03.md")
            for item in payload["blocks"]
        )
        read_set.append(str(case_root / "stitches" / "stage-03.md"))
    existing = [path for path in read_set if Path(path).exists()]
    missing = [path for path in read_set if not Path(path).exists()]
    return {
        "stage": stage,
        "state": payload["state"],
        "block": args.block,
        "read_set": existing,
        "missing_required": missing,
        "rule": "read only the current stage reference and this read_set",
    }


def command_submit_block(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "blocks")
    stage = int(payload["stage"])
    if args.stage != stage:
        raise CaseFlowError(f"current stage is {stage}")
    known = {item["id"] for item in payload["blocks"]}
    if args.block not in known:
        raise CaseFlowError(f"unknown block: {args.block}")
    method_basis = case_root / "method-basis" / f"stage-{stage:02d}-{args.block}.md"
    if not method_basis.is_file():
        raise CaseFlowError(f"method basis is missing for {args.block}: {method_basis}")
    artifact = resolve_artifact(case_root, args.artifact)
    record = {
        "path": relative_or_absolute(case_root, artifact),
        "sha256": digest(artifact),
        "method_basis": {
            "path": relative_or_absolute(case_root, method_basis),
            "sha256": digest(method_basis),
        },
        "submitted_at": now(),
    }
    stage_record(payload)["submissions"][args.block] = record
    save_case(case_root, payload, f"stage_{stage}_block_{args.block}_submitted")
    return record


def command_open_stitch(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "blocks")
    record = stage_record(payload)
    required = {item["id"] for item in payload["blocks"]}
    submitted = set(record["submissions"])
    missing = sorted(required - submitted)
    if missing:
        raise CaseFlowError(f"blocks missing submissions: {', '.join(missing)}")
    payload["state"] = "stitching"
    record["state"] = "stitching"
    save_case(case_root, payload, f"stage_{payload['stage']}_stitch_opened")
    return {"stage": payload["stage"], "state": payload["state"]}


def command_record_stitch(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "stitching")
    stage = int(payload["stage"])
    report = resolve_artifact(case_root, args.report)
    pool_path = resolve_artifact(case_root, args.diff_pool)
    pool = validate_diff_pool(pool_path, stage)
    record = stage_record(payload)
    record["stitch"] = {
        "path": relative_or_absolute(case_root, report),
        "sha256": digest(report),
        "recorded_at": now(),
    }
    record["diff_pool"] = {
        "path": relative_or_absolute(case_root, pool_path),
        "sha256": digest(pool_path),
    }
    unresolved_items = [
        item["id"] for item in pool["items"] if item["status"] in {"open", "applied"}
    ]
    payload["state"] = "remediation" if unresolved_items else "ready"
    record["state"] = payload["state"]
    save_case(case_root, payload, f"stage_{stage}_stitch_recorded")
    return {"stage": stage, "state": payload["state"], "unresolved_items": unresolved_items}


def mutate_pool_item(
    case_root: Path,
    payload: dict[str, Any],
    item_id: str,
    status: str,
    evidence_field: str,
    evidence: str,
) -> dict[str, Any]:
    require_state(payload, "remediation", "ready")
    stage = int(payload["stage"])
    record = stage_record(payload)
    if not record.get("diff_pool"):
        raise CaseFlowError("stage has no diff pool")
    pool_path = resolve_artifact(case_root, record["diff_pool"]["path"])
    pool = validate_diff_pool(pool_path, stage)
    matching = [item for item in pool["items"] if item["id"] == item_id]
    if not matching:
        raise CaseFlowError(f"diff item not found: {item_id}")
    item = matching[0]
    if item["status"] != "open":
        raise CaseFlowError(f"diff item is already {item['status']}: {item_id}")
    if evidence_field == "receipt":
        receipt = resolve_artifact(case_root, evidence)
        receipt_record = {
            "path": relative_or_absolute(case_root, receipt),
            "sha256": digest(receipt),
            "recorded_at": now(),
        }
        item["receipt"] = receipt_record
        item.setdefault("correction_attempts", []).append(receipt_record)
    else:
        if not evidence.strip():
            raise CaseFlowError("decision_ref cannot be empty")
        item["decision_ref"] = evidence.strip()
    item["status"] = status
    item["resolved_at"] = now()
    atomic_json(pool_path, pool)
    record["diff_pool"]["sha256"] = digest(pool_path)
    unresolved_items = [
        entry["id"] for entry in pool["items"] if entry["status"] in {"open", "applied"}
    ]
    payload["state"] = "remediation" if unresolved_items else "ready"
    record["state"] = payload["state"]
    save_case(case_root, payload, f"stage_{stage}_diff_{item_id}_{status}")
    return {"item": item_id, "status": status, "remaining_unresolved": unresolved_items}


def command_resolve(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    return mutate_pool_item(
        case_root,
        load_case(case_root),
        args.item,
        "applied",
        "receipt",
        args.receipt,
    )


def command_verify(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "remediation", "ready")
    stage = int(payload["stage"])
    record = stage_record(payload)
    if not record.get("diff_pool"):
        raise CaseFlowError("stage has no diff pool")
    pool_path = resolve_artifact(case_root, record["diff_pool"]["path"])
    pool = validate_diff_pool(pool_path, stage)
    matching = [item for item in pool["items"] if item["id"] == args.item]
    if not matching:
        raise CaseFlowError(f"diff item not found: {args.item}")
    item = matching[0]
    if item["status"] != "applied":
        raise CaseFlowError(f"diff item must be applied before verification: {args.item}")
    receipt = resolve_artifact(case_root, args.receipt)
    result = getattr(args, "result", "pass")
    verification_record = {
        "path": relative_or_absolute(case_root, receipt),
        "sha256": digest(receipt),
        "result": result,
        "recorded_at": now(),
    }
    item.setdefault("verification_attempts", []).append(verification_record)
    if result == "pass":
        item["verification_receipt"] = verification_record
        item["status"] = "verified"
        item["verified_at"] = now()
    else:
        item.pop("verification_receipt", None)
        item["status"] = "open"
        item["reopened_at"] = now()
    atomic_json(pool_path, pool)
    record["diff_pool"]["sha256"] = digest(pool_path)
    unresolved = [
        entry["id"] for entry in pool["items"] if entry["status"] in {"open", "applied"}
    ]
    payload["state"] = "remediation" if unresolved else "ready"
    record["state"] = payload["state"]
    save_case(case_root, payload, f"stage_{stage}_diff_{args.item}_verification_{result}")
    return {"item": args.item, "status": item["status"], "remaining_unresolved": unresolved}


def command_waive(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    return mutate_pool_item(
        case_root,
        load_case(case_root),
        args.item,
        "waived",
        "decision_ref",
        args.decision_ref,
    )


def command_advance(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "ready")
    stage = int(payload["stage"])
    record = stage_record(payload)
    pool_path = resolve_artifact(case_root, record["diff_pool"]["path"])
    pool = validate_diff_pool(pool_path, stage)
    unresolved = [item["id"] for item in pool["items"] if item["status"] in {"open", "applied"}]
    if unresolved:
        raise CaseFlowError(f"unverified diff items remain: {', '.join(unresolved)}")
    record["state"] = "complete"
    if stage < 4:
        payload["stage"] = stage + 1
        payload["state"] = "blocks"
        stage_record(payload)["state"] = "blocks"
        event = f"stage_{stage}_completed_stage_{stage + 1}_opened"
    else:
        payload["state"] = "article_pending"
        event = "stage_4_completed_article_pending"
    save_case(case_root, payload, event)
    return {"stage": payload["stage"], "state": payload["state"]}


def command_finalize_article(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "article_pending")
    article = resolve_artifact(case_root, args.article)
    payload["article"] = {
        "path": relative_or_absolute(case_root, article),
        "sha256": digest(article),
        "recorded_at": now(),
    }
    payload["state"] = "revmux_pending"
    save_case(case_root, payload, "article_finalized_revmux_pending")
    return {"article": payload["article"], "state": payload["state"]}


def command_article_updated(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "revmux_remediation")
    if not payload["review_rounds"] or not payload["review_rounds"][-1].get("diff_pool"):
        raise CaseFlowError("current revmux round has no registered diff pool")
    pool_path = resolve_artifact(case_root, payload["review_rounds"][-1]["diff_pool"]["path"])
    pool = validate_diff_pool(pool_path, 4)
    unresolved = [
        item["id"] for item in pool["items"] if item["status"] in {"open", "applied"}
    ]
    if unresolved:
        raise CaseFlowError(f"unverified review diff items remain: {', '.join(unresolved)}")
    article = resolve_artifact(case_root, args.article)
    payload["article"] = {
        "path": relative_or_absolute(case_root, article),
        "sha256": digest(article),
        "recorded_at": now(),
    }
    payload["state"] = "revmux_pending"
    save_case(case_root, payload, "article_updated_revmux_pending")
    return {"article": payload["article"], "state": payload["state"]}


def command_record_review(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "revmux_pending")
    receipt_path = resolve_artifact(case_root, args.receipt)
    receipt = read_json(receipt_path)
    if not isinstance(receipt, dict):
        raise CaseFlowError("revmux receipt must be a JSON object")
    sources = receipt.get("sources", {})
    degraded = sources.get("degraded", []) if isinstance(sources, dict) else []
    expected = sources.get("expected") if isinstance(sources, dict) else None
    reported = sources.get("reported") if isinstance(sources, dict) else None
    source_count_mismatch = (
        isinstance(expected, int) and isinstance(reported, int) and expected != reported
    )
    findings = receipt.get("findings", [])
    open_questions = receipt.get("open_questions", [])
    if (
        not isinstance(degraded, list)
        or not isinstance(findings, list)
        or not isinstance(open_questions, list)
    ):
        raise CaseFlowError("revmux receipt has invalid sources/findings/open_questions")
    gating = [
        finding
        for finding in findings
        if isinstance(finding, dict) and finding.get("severity") in GATING_SEVERITIES
    ]
    diff_pool_arg = getattr(args, "diff_pool", None)
    diff_pool_record = None
    if open_questions and diff_pool_arg:
        raise CaseFlowError("answer revmux open questions before forming a review diff pool")
    if degraded or source_count_mismatch:
        if diff_pool_arg:
            raise CaseFlowError("degraded revmux round must be rerun before forming a diff pool")
    elif diff_pool_arg:
        pool_path = resolve_artifact(case_root, diff_pool_arg)
        pool = validate_diff_pool(pool_path, 4)
        if not pool["items"]:
            raise CaseFlowError("review diff pool cannot be empty")
        finding_ids = {
            finding.get("id") for finding in findings if isinstance(finding, dict)
        }
        covered_ids = {item.get("source_finding_id") for item in pool["items"]}
        if None in covered_ids:
            raise CaseFlowError("every review diff item requires source_finding_id")
        unknown_ids = covered_ids - finding_ids
        if unknown_ids:
            raise CaseFlowError(f"review diff has unknown finding ids: {sorted(unknown_ids)}")
        gating_ids = {finding.get("id") for finding in gating}
        missing_gating = gating_ids - covered_ids
        if missing_gating:
            raise CaseFlowError(f"review diff does not cover gating findings: {sorted(missing_gating)}")
        diff_pool_record = {
            "path": relative_or_absolute(case_root, pool_path),
            "sha256": digest(pool_path),
        }
    elif gating:
        raise CaseFlowError("gating revmux findings require an exact review diff pool")

    round_record = {
        "path": relative_or_absolute(case_root, receipt_path),
        "sha256": digest(receipt_path),
        "degraded": degraded,
        "source_count_mismatch": source_count_mismatch,
        "gating_findings": len(gating),
        "findings": len(findings),
        "open_questions": len(open_questions),
        "recorded_at": now(),
    }
    if diff_pool_record:
        round_record["diff_pool"] = diff_pool_record
    payload["review_rounds"].append(round_record)
    if degraded or source_count_mismatch:
        payload["state"] = "revmux_pending"
    elif open_questions:
        payload["state"] = "revmux_decision_pending"
    elif diff_pool_record:
        payload["state"] = "revmux_remediation"
    else:
        payload["state"] = "spec_ready"
    save_case(case_root, payload, f"revmux_round_{len(payload['review_rounds'])}_recorded")
    return {
        "state": payload["state"],
        "degraded": degraded,
        "source_count_mismatch": source_count_mismatch,
        "gating_findings": gating,
    }


def command_record_review_decisions(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "revmux_decision_pending")
    if not args.decision_ref.strip():
        raise CaseFlowError("decision_ref cannot be empty")
    round_record = payload["review_rounds"][-1]
    receipt = read_json(resolve_artifact(case_root, round_record["path"]))
    findings = receipt.get("findings", [])
    questions = receipt.get("open_questions", [])
    gating = [
        finding
        for finding in findings
        if isinstance(finding, dict) and finding.get("severity") in GATING_SEVERITIES
    ]
    diff_pool_arg = getattr(args, "diff_pool", None)
    if gating and not diff_pool_arg:
        raise CaseFlowError("gating findings still require an exact review diff pool")
    if diff_pool_arg:
        pool_path = resolve_artifact(case_root, diff_pool_arg)
        pool = validate_diff_pool(pool_path, 4)
        if not pool["items"]:
            raise CaseFlowError("review decision diff pool cannot be empty")
        finding_ids = {
            finding.get("id") for finding in findings if isinstance(finding, dict)
        }
        question_ids = {
            question.get("id") for question in questions if isinstance(question, dict)
        }
        covered_findings: set[Any] = set()
        for item in pool["items"]:
            finding_id = item.get("source_finding_id")
            question_id = item.get("source_question_id")
            if bool(finding_id) == bool(question_id):
                raise CaseFlowError(
                    "review decision diff item requires exactly one source_finding_id or source_question_id"
                )
            if finding_id:
                if finding_id not in finding_ids:
                    raise CaseFlowError(f"review diff has unknown finding id: {finding_id}")
                covered_findings.add(finding_id)
            elif question_id not in question_ids:
                raise CaseFlowError(f"review diff has unknown question id: {question_id}")
        missing_gating = {finding.get("id") for finding in gating} - covered_findings
        if missing_gating:
            raise CaseFlowError(f"review diff does not cover gating findings: {sorted(missing_gating)}")
        round_record["diff_pool"] = {
            "path": relative_or_absolute(case_root, pool_path),
            "sha256": digest(pool_path),
        }
        payload["state"] = "revmux_remediation"
    else:
        payload["state"] = "revmux_pending"
    round_record["decision_ref"] = args.decision_ref.strip()
    save_case(case_root, payload, "revmux_open_questions_decided")
    return {"state": payload["state"], "decision_ref": round_record["decision_ref"]}


def current_review_pool(case_root: Path, payload: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    require_state(payload, "revmux_remediation")
    if not payload["review_rounds"] or not payload["review_rounds"][-1].get("diff_pool"):
        raise CaseFlowError("current revmux round has no registered diff pool")
    pool_path = resolve_artifact(case_root, payload["review_rounds"][-1]["diff_pool"]["path"])
    return pool_path, validate_diff_pool(pool_path, 4)


def command_resolve_review(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    pool_path, pool = current_review_pool(case_root, payload)
    matching = [item for item in pool["items"] if item["id"] == args.item]
    if not matching:
        raise CaseFlowError(f"review diff item not found: {args.item}")
    item = matching[0]
    if item["status"] != "open":
        raise CaseFlowError(f"review diff item is already {item['status']}: {args.item}")
    receipt = resolve_artifact(case_root, args.receipt)
    receipt_record = {
        "path": relative_or_absolute(case_root, receipt),
        "sha256": digest(receipt),
        "recorded_at": now(),
    }
    item["receipt"] = receipt_record
    item.setdefault("correction_attempts", []).append(receipt_record)
    item["status"] = "applied"
    atomic_json(pool_path, pool)
    payload["review_rounds"][-1]["diff_pool"]["sha256"] = digest(pool_path)
    save_case(case_root, payload, f"revmux_diff_{args.item}_applied")
    return {"item": args.item, "status": "applied"}


def command_verify_review(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    pool_path, pool = current_review_pool(case_root, payload)
    matching = [item for item in pool["items"] if item["id"] == args.item]
    if not matching:
        raise CaseFlowError(f"review diff item not found: {args.item}")
    item = matching[0]
    if item["status"] != "applied":
        raise CaseFlowError(f"review diff item must be applied before verification: {args.item}")
    receipt = resolve_artifact(case_root, args.receipt)
    verification_record = {
        "path": relative_or_absolute(case_root, receipt),
        "sha256": digest(receipt),
        "result": args.result,
        "recorded_at": now(),
    }
    item.setdefault("verification_attempts", []).append(verification_record)
    if args.result == "pass":
        item["verification_receipt"] = verification_record
        item["status"] = "verified"
        item["verified_at"] = now()
    else:
        item.pop("verification_receipt", None)
        item["status"] = "open"
        item["reopened_at"] = now()
    atomic_json(pool_path, pool)
    payload["review_rounds"][-1]["diff_pool"]["sha256"] = digest(pool_path)
    save_case(case_root, payload, f"revmux_diff_{args.item}_verification_{args.result}")
    return {"item": args.item, "status": item["status"]}


def command_waive_review(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    pool_path, pool = current_review_pool(case_root, payload)
    matching = [item for item in pool["items"] if item["id"] == args.item]
    if not matching:
        raise CaseFlowError(f"review diff item not found: {args.item}")
    item = matching[0]
    if item["status"] != "open":
        raise CaseFlowError(f"review diff item is already {item['status']}: {args.item}")
    if not args.decision_ref.strip():
        raise CaseFlowError("decision_ref cannot be empty")
    item["decision_ref"] = args.decision_ref.strip()
    item["status"] = "waived"
    item["resolved_at"] = now()
    atomic_json(pool_path, pool)
    payload["review_rounds"][-1]["diff_pool"]["sha256"] = digest(pool_path)
    save_case(case_root, payload, f"revmux_diff_{args.item}_waived")
    return {"item": args.item, "status": "waived"}


def command_route(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "spec_ready")
    payload["route"] = args.decision
    payload["state"] = "delivery_active" if args.decision == "delivery" else "stopped_after_spec"
    save_case(case_root, payload, f"route_{args.decision}_selected")
    return {"route": payload["route"], "state": payload["state"]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--case-root", type=Path, required=True)
    init.add_argument("--template", type=Path, required=True)
    init.add_argument("--decision", type=Path, required=True)
    init.add_argument("--article-id", required=True)
    init.set_defaults(handler=command_init)

    for name, handler in (("status", command_status), ("context", command_context)):
        command = subparsers.add_parser(name)
        command.add_argument("--case-root", type=Path, required=True)
        if name == "context":
            command.add_argument("--block")
        command.set_defaults(handler=handler)

    submit = subparsers.add_parser("submit-block")
    submit.add_argument("--case-root", type=Path, required=True)
    submit.add_argument("--stage", type=int, choices=STAGES, required=True)
    submit.add_argument("--block", required=True)
    submit.add_argument("--artifact", required=True)
    submit.set_defaults(handler=command_submit_block)

    stitch = subparsers.add_parser("open-stitch")
    stitch.add_argument("--case-root", type=Path, required=True)
    stitch.set_defaults(handler=command_open_stitch)

    record = subparsers.add_parser("record-stitch")
    record.add_argument("--case-root", type=Path, required=True)
    record.add_argument("--report", required=True)
    record.add_argument("--diff-pool", required=True)
    record.set_defaults(handler=command_record_stitch)

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("--case-root", type=Path, required=True)
    resolve.add_argument("--item", required=True)
    resolve.add_argument("--receipt", required=True)
    resolve.set_defaults(handler=command_resolve)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--case-root", type=Path, required=True)
    verify.add_argument("--item", required=True)
    verify.add_argument("--receipt", required=True)
    verify.add_argument("--result", choices=("pass", "fail"), default="pass")
    verify.set_defaults(handler=command_verify)

    waive = subparsers.add_parser("waive")
    waive.add_argument("--case-root", type=Path, required=True)
    waive.add_argument("--item", required=True)
    waive.add_argument("--decision-ref", required=True)
    waive.set_defaults(handler=command_waive)

    advance = subparsers.add_parser("advance")
    advance.add_argument("--case-root", type=Path, required=True)
    advance.set_defaults(handler=command_advance)

    finalize = subparsers.add_parser("finalize-article")
    finalize.add_argument("--case-root", type=Path, required=True)
    finalize.add_argument("--article", required=True)
    finalize.set_defaults(handler=command_finalize_article)

    updated = subparsers.add_parser("article-updated")
    updated.add_argument("--case-root", type=Path, required=True)
    updated.add_argument("--article", required=True)
    updated.set_defaults(handler=command_article_updated)

    review = subparsers.add_parser("record-review")
    review.add_argument("--case-root", type=Path, required=True)
    review.add_argument("--receipt", required=True)
    review.add_argument("--diff-pool")
    review.set_defaults(handler=command_record_review)

    review_decisions = subparsers.add_parser("record-review-decisions")
    review_decisions.add_argument("--case-root", type=Path, required=True)
    review_decisions.add_argument("--decision-ref", required=True)
    review_decisions.add_argument("--diff-pool")
    review_decisions.set_defaults(handler=command_record_review_decisions)

    resolve_review = subparsers.add_parser("resolve-review")
    resolve_review.add_argument("--case-root", type=Path, required=True)
    resolve_review.add_argument("--item", required=True)
    resolve_review.add_argument("--receipt", required=True)
    resolve_review.set_defaults(handler=command_resolve_review)

    verify_review = subparsers.add_parser("verify-review")
    verify_review.add_argument("--case-root", type=Path, required=True)
    verify_review.add_argument("--item", required=True)
    verify_review.add_argument("--receipt", required=True)
    verify_review.add_argument("--result", choices=("pass", "fail"), required=True)
    verify_review.set_defaults(handler=command_verify_review)

    waive_review = subparsers.add_parser("waive-review")
    waive_review.add_argument("--case-root", type=Path, required=True)
    waive_review.add_argument("--item", required=True)
    waive_review.add_argument("--decision-ref", required=True)
    waive_review.set_defaults(handler=command_waive_review)

    route = subparsers.add_parser("route")
    route.add_argument("--case-root", type=Path, required=True)
    route.add_argument("--decision", choices=("stop", "delivery"), required=True)
    route.set_defaults(handler=command_route)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = args.handler(args)
    except CaseFlowError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
