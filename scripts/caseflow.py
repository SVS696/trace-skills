#!/usr/bin/env python3
"""Deterministic state for the Workflow Skills specification process."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .preanalysis import DecisionError, PlanError, validate_decision, validate_plan
except ImportError:  # Direct script execution.
    from preanalysis import DecisionError, PlanError, validate_decision, validate_plan


SCHEMA = 1
STAGES = (1, 2, 3, 4)
ITEM_STATUSES = {"open", "applied", "verified", "waived"}
GATING_SEVERITIES = {"critical", "major"}
ITEM_RE = re.compile(r"^D([1-4])-\d{3}$")
LANE_RE = re.compile(r"^[A-Z][A-Z0-9_-]{1,31}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
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


@contextmanager
def case_lock(case_root: Path, *, create: bool = False):
    if create:
        case_root.mkdir(parents=True, exist_ok=True)
    elif not manifest_path(case_root).is_file():
        raise CaseFlowError(f"case does not exist: {case_root}")
    lock_path = case_root / ".caseflow.lock"
    if not create and not lock_path.is_file():
        raise CaseFlowError(f"case lock is missing: {lock_path}")
    with lock_path.open("a+" if create else "r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


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


def normalized_target_path(case_root: Path, target: str) -> Path:
    return resolve_artifact(case_root, target.split("#", 1)[0])


def target_snapshot(case_root: Path, item: dict[str, Any]) -> dict[str, str]:
    path = normalized_target_path(case_root, item["target"])
    return {
        "target_path": relative_or_absolute(case_root, path),
        "target_sha256": digest(path),
    }


def manifest_path(case_root: Path) -> Path:
    return case_root / "case.json"


def verify_record(case_root: Path, record: dict[str, Any], label: str) -> None:
    path_value = record.get("path")
    expected = record.get("sha256")
    if not isinstance(path_value, str) or not isinstance(expected, str):
        raise CaseFlowError(f"{label} fingerprint record is invalid")
    path = resolve_artifact(case_root, path_value)
    if digest(path) != expected:
        raise CaseFlowError(f"{label} changed after registration: {path}")


def verify_case_integrity(case_root: Path, payload: dict[str, Any]) -> None:
    template = Path(str(payload.get("template", ""))).expanduser().resolve()
    if digest(template) != payload.get("template_sha256"):
        raise CaseFlowError(f"project template changed after case initialization: {template}")
    for key, label in (
        ("decomposition_decision", "decomposition decision"),
        ("execution_plan", "execution plan"),
    ):
        record = payload.get(key)
        if not isinstance(record, dict):
            raise CaseFlowError(f"case has no {label} fingerprint")
        verify_record(case_root, record, label)
    article_path = None
    if payload.get("article"):
        article_path = resolve_artifact(case_root, payload["article"]["path"])
    for stage, record in payload.get("stages", {}).items():
        for block, submission in record.get("submissions", {}).items():
            if record.get("state") == "complete":
                verify_record(
                    case_root,
                    submission.get("method_basis", {}),
                    f"stage {stage} block {block} method basis",
                )
                submission_path = resolve_artifact(case_root, submission["path"])
                shared_article_path = stage == "4" and submission_path == article_path
                if not shared_article_path:
                    verify_record(case_root, submission, f"stage {stage} block {block}")
        if record.get("state") == "complete" and record.get("stitch"):
            verify_record(case_root, record["stitch"], f"stage {stage} stitch")
        if record.get("diff_pool"):
            verify_record(case_root, record["diff_pool"], f"stage {stage} diff pool")
    for index, round_record in enumerate(payload.get("review_rounds", []), start=1):
        verify_record(case_root, round_record, f"review round {index}")
        if round_record.get("diff_pool"):
            verify_record(case_root, round_record["diff_pool"], f"review round {index} diff pool")
    delivery = payload.get("delivery")
    if delivery:
        for stage, record in delivery.get("stages", {}).items():
            for lane, submission in record.get("submissions", {}).items():
                if record.get("state") == "complete":
                    verify_record(
                        case_root,
                        submission.get("method_basis", {}),
                        f"delivery stage {stage} lane {lane} method basis",
                    )
                    verify_record(case_root, submission, f"delivery stage {stage} lane {lane}")
            if record.get("state") == "complete" and record.get("stitch"):
                verify_record(case_root, record["stitch"], f"delivery stage {stage} stitch")
            if record.get("diff_pool"):
                verify_record(case_root, record["diff_pool"], f"delivery stage {stage} diff pool")
    if payload.get("article") and payload.get("state") in {
        "spec_ready",
        "delivery_active",
        "delivery_ready",
        "stopped_after_spec",
    }:
        verify_record(case_root, payload["article"], "final reviewed article")


def load_case(case_root: Path) -> dict[str, Any]:
    payload = read_json(manifest_path(case_root))
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise CaseFlowError("unsupported case schema")
    if payload.get("stage") not in STAGES:
        raise CaseFlowError("case stage is invalid")
    if not isinstance(payload.get("blocks"), list) or not payload["blocks"]:
        raise CaseFlowError("case has no blocks")
    verify_case_integrity(case_root, payload)
    return payload


def save_case(case_root: Path, payload: dict[str, Any], event: str) -> None:
    payload["updated_at"] = now()
    payload.setdefault("events", []).append({"at": payload["updated_at"], "event": event})
    atomic_json(manifest_path(case_root), payload)


def stage_record(payload: dict[str, Any], stage: int | None = None) -> dict[str, Any]:
    stage = stage or int(payload["stage"])
    return payload["stages"][str(stage)]


def validate_diff_payload(payload: Any, stage: int, *, initial: bool = False) -> dict[str, Any]:
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
        if initial and status != "open":
            raise CaseFlowError(f"new diff item must start open: {item_id}")
        if status in {"applied", "verified"} and not item.get("receipt"):
            raise CaseFlowError(f"{item_id} {status} without correction receipt")
        if status == "verified" and not item.get("verification_receipt"):
            raise CaseFlowError(f"{item_id} verified without verification receipt")
        if status == "verified" and not SHA256_RE.fullmatch(
            str(item["verification_receipt"].get("target_sha256", ""))
        ):
            raise CaseFlowError(f"{item_id} verified without target fingerprint")
        if status == "waived" and not item.get("decision_ref"):
            raise CaseFlowError(f"{item_id} waived without decision_ref")
        if status == "waived" and not SHA256_RE.fullmatch(
            str(item.get("waiver_target_sha256", ""))
        ):
            raise CaseFlowError(f"{item_id} waived without target fingerprint")
    return payload


def validate_diff_pool(path: Path, stage: int, *, initial: bool = False) -> dict[str, Any]:
    return validate_diff_payload(read_json(path), stage, initial=initial)


def append_open_item(pool: dict[str, Any], item_payload: Any, stage: int) -> dict[str, Any]:
    candidate = validate_diff_payload(
        {"schema": 1, "stage": stage, "items": [item_payload]},
        stage,
        initial=True,
    )["items"][0]
    existing = {item["id"] for item in pool["items"]}
    if candidate["id"] in existing:
        raise CaseFlowError(f"duplicate diff item id: {candidate['id']}")
    pool["items"].append(candidate)
    return candidate


def require_state(payload: dict[str, Any], *states: str) -> None:
    if payload.get("state") not in states:
        expected = ", ".join(states)
        raise CaseFlowError(f"state must be one of [{expected}], got {payload.get('state')}")


def validate_review_receipt(receipt: Any, article_sha256: str) -> dict[str, Any]:
    if not isinstance(receipt, dict) or receipt.get("schema") != 1:
        raise CaseFlowError("revmux receipt must be a schema 1 JSON object")
    if receipt.get("article_sha256") != article_sha256:
        raise CaseFlowError("revmux receipt is not bound to the current article sha256")
    sources = receipt.get("sources")
    if not isinstance(sources, dict):
        raise CaseFlowError("revmux receipt.sources must be an object")
    expected = sources.get("expected")
    reported = sources.get("reported")
    degraded = sources.get("degraded")
    if (
        not isinstance(expected, int)
        or isinstance(expected, bool)
        or expected < 1
        or not isinstance(reported, int)
        or isinstance(reported, bool)
        or reported < 0
        or not isinstance(degraded, list)
        or not all(isinstance(item, str) and item.strip() for item in degraded)
    ):
        raise CaseFlowError("revmux receipt source accounting is invalid")
    findings = receipt.get("findings")
    questions = receipt.get("open_questions")
    if not isinstance(findings, list) or not isinstance(questions, list):
        raise CaseFlowError("revmux receipt findings and open_questions must be arrays")
    finding_ids: set[str] = set()
    for finding in findings:
        if (
            not isinstance(finding, dict)
            or not isinstance(finding.get("id"), str)
            or not finding["id"].strip()
            or finding.get("severity") not in {"critical", "major", "minor"}
        ):
            raise CaseFlowError("revmux receipt contains an invalid finding")
        if finding["id"] in finding_ids:
            raise CaseFlowError(f"duplicate revmux finding id: {finding['id']}")
        finding_ids.add(finding["id"])
    question_ids: set[str] = set()
    for question in questions:
        if (
            not isinstance(question, dict)
            or not isinstance(question.get("id"), str)
            or not question["id"].strip()
        ):
            raise CaseFlowError("revmux receipt contains an invalid open question")
        if question["id"] in question_ids:
            raise CaseFlowError(f"duplicate revmux open question id: {question['id']}")
        question_ids.add(question["id"])
    return receipt


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
    plan_path = args.plan.expanduser().resolve()
    try:
        plan = validate_plan(read_json(plan_path))
    except PlanError as exc:
        raise CaseFlowError(str(exc)) from exc
    if plan.get("status") != "approved":
        raise CaseFlowError("execution plan must be approved before case initialization")
    if plan["subject_id"] != decision["subject_id"]:
        raise CaseFlowError("execution plan and decomposition decision have different subjects")
    if plan["decision_ref"] != decision["decision_ref"]:
        raise CaseFlowError("execution plan and decomposition decision have different decision_ref")
    article_ids = {article["id"] for article in decision["articles"]}
    if set(plan["article_ids"]) != article_ids:
        raise CaseFlowError("execution plan article_ids do not match decomposition outputs")
    if plan["route"] != "specification":
        raise CaseFlowError("only a specification plan can initialize a specification case")
    matches = [article for article in decision["articles"] if article["id"] == args.article_id]
    if not matches:
        raise CaseFlowError(f"article id is not present in decision: {args.article_id}")
    article = matches[0]
    blocks = article["blocks"]
    ids = [block["id"] for block in blocks]
    case_root.mkdir(parents=True, exist_ok=True)
    (case_root / ".caseflow.lock").touch(exist_ok=True)
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
        "execution_plan": {
            "path": str(plan_path),
            "sha256": digest(plan_path),
            "decision_ref": plan["decision_ref"],
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
    delivery = payload.get("delivery")
    current = delivery_stage_record(payload) if delivery else stage_record(payload)
    current_stage = delivery["stage"] if delivery else payload["stage"]
    open_count = None
    if current.get("diff_pool"):
        pool_path = resolve_artifact(args.case_root.resolve(), current["diff_pool"]["path"])
        pool = validate_diff_pool(pool_path, int(current_stage))
        open_count = sum(item["status"] in {"open", "applied"} for item in pool["items"])
    result = {
        "case_id": payload["case_id"],
        "stage": payload["stage"],
        "state": payload["state"],
        "route": payload["route"],
        "submitted_blocks": sorted(current["submissions"]),
        "required_blocks": delivery["lanes"] if delivery else [block["id"] for block in payload["blocks"]],
        "open_diff_items": open_count,
        "next_skill": "delivery-workflow" if payload["route"] == "delivery" else "spec-workflow",
    }
    if payload.get("delivery"):
        result["delivery_stage"] = payload["delivery"]["stage"]
        result["delivery_state"] = payload["delivery"]["state"]
        result["delivery_lanes"] = payload["delivery"]["lanes"]
    return result


def command_context(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    delivery = payload.get("delivery")
    lane = getattr(args, "lane", None)
    if delivery:
        if getattr(args, "block", None):
            raise CaseFlowError("delivery context uses --lane, not --block")
        if lane and lane not in delivery["lanes"]:
            raise CaseFlowError(f"unknown delivery lane: {lane}")
        stage = int(delivery["stage"])
        read_set = [str(PROCESS_KERNEL)]
        if payload.get("article"):
            read_set.append(str(resolve_artifact(case_root, payload["article"]["path"])))
        current = delivery_stage_record(payload)
        selected_lanes = [lane] if lane else delivery["lanes"]
        for selected_lane in selected_lanes:
            submission = current["submissions"].get(selected_lane)
            if submission:
                read_set.extend(
                    [
                        str(resolve_artifact(case_root, submission["method_basis"]["path"])),
                        str(resolve_artifact(case_root, submission["path"])),
                    ]
                )
        if stage > 1:
            previous = delivery["stages"][str(stage - 1)]
            for selected_lane in selected_lanes:
                submission = previous["submissions"].get(selected_lane)
                if submission:
                    read_set.append(str(resolve_artifact(case_root, submission["path"])))
            if previous.get("stitch"):
                read_set.append(str(resolve_artifact(case_root, previous["stitch"]["path"])))
        read_set = list(dict.fromkeys(read_set))
        return {
            "mode": "delivery",
            "delivery_stage": stage,
            "delivery_state": delivery["state"],
            "lane": lane,
            "read_set": [path for path in read_set if Path(path).exists()],
            "missing_required": [path for path in read_set if not Path(path).exists()],
            "rule": "read only the current delivery stage reference and this read_set",
        }
    stage = int(payload["stage"])
    if lane:
        raise CaseFlowError("specification context uses --block, not --lane")
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
            submission = stage_record(payload, previous)["submissions"].get(args.block)
            if submission:
                read_set.append(str(resolve_artifact(case_root, submission["path"])))
        else:
            for item in payload["blocks"]:
                submission = stage_record(payload, previous)["submissions"].get(item["id"])
                if submission:
                    read_set.append(str(resolve_artifact(case_root, submission["path"])))
        previous_stitch = stage_record(payload, previous).get("stitch")
        if previous_stitch:
            read_set.append(str(resolve_artifact(case_root, previous_stitch["path"])))
    else:
        for item in payload["blocks"]:
            submission = stage_record(payload, 3)["submissions"].get(item["id"])
            if submission:
                read_set.append(str(resolve_artifact(case_root, submission["path"])))
        previous_stitch = stage_record(payload, 3).get("stitch")
        if previous_stitch:
            read_set.append(str(resolve_artifact(case_root, previous_stitch["path"])))
    existing = [path for path in read_set if Path(path).exists()]
    missing = [path for path in read_set if not Path(path).exists()]
    return {
        "stage": stage,
        "mode": "specification",
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
    pool = validate_diff_pool(pool_path, stage, initial=True)
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
        item["waiver_target_sha256"] = target_snapshot(case_root, item)["target_sha256"]
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
    result = args.result
    verification_record = {
        "path": relative_or_absolute(case_root, receipt),
        "sha256": digest(receipt),
        "result": result,
        "recorded_at": now(),
        **target_snapshot(case_root, item),
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


def command_append_item(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "remediation", "ready")
    stage = int(payload["stage"])
    record = stage_record(payload)
    pool_path = resolve_artifact(case_root, record["diff_pool"]["path"])
    pool = validate_diff_pool(pool_path, stage)
    item = append_open_item(pool, read_json(resolve_artifact(case_root, args.item_file)), stage)
    atomic_json(pool_path, pool)
    record["diff_pool"]["sha256"] = digest(pool_path)
    payload["state"] = "remediation"
    record["state"] = "remediation"
    save_case(case_root, payload, f"stage_{stage}_diff_{item['id']}_appended")
    return {"item": item["id"], "status": "open", "state": payload["state"]}


def closed_target_expectations(case_root: Path, pool: dict[str, Any]) -> dict[Path, str]:
    expected: dict[Path, str] = {}
    for item in pool["items"]:
        if item["status"] == "verified":
            expected_hash = item["verification_receipt"]["target_sha256"]
        elif item["status"] == "waived":
            expected_hash = item["waiver_target_sha256"]
        else:
            continue
        expected[normalized_target_path(case_root, item["target"])] = expected_hash
    for path, expected_hash in expected.items():
        if digest(path) != expected_hash:
            raise CaseFlowError(f"diff target changed after verification or waiver: {path}")
    return expected


def rebind_stage_outputs(
    case_root: Path,
    record: dict[str, Any],
    pool: dict[str, Any],
    *,
    label: str,
) -> list[str]:
    allowed = closed_target_expectations(case_root, pool)
    rebound: list[str] = []
    records = list(record.get("submissions", {}).values())
    records.extend(
        submission["method_basis"]
        for submission in record.get("submissions", {}).values()
        if submission.get("method_basis")
    )
    if record.get("stitch"):
        records.append(record["stitch"])
    for artifact_record in records:
        path = resolve_artifact(case_root, artifact_record["path"])
        current = digest(path)
        if current == artifact_record["sha256"]:
            continue
        if path not in allowed:
            raise CaseFlowError(f"{label} artifact changed outside a closed diff item: {path}")
        artifact_record["sha256"] = current
        artifact_record["rebound_at"] = now()
        rebound.append(relative_or_absolute(case_root, path))
    return rebound


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
    rebound = rebind_stage_outputs(case_root, record, pool, label=f"stage {stage}")
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
    return {"stage": payload["stage"], "state": payload["state"], "rebound": rebound}


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
    require_state(payload, "revmux_remediation", "revmux_pending")
    if payload["state"] == "revmux_remediation":
        if not payload["review_rounds"] or not payload["review_rounds"][-1].get("diff_pool"):
            raise CaseFlowError("current revmux round has no registered diff pool")
        pool_path = resolve_artifact(case_root, payload["review_rounds"][-1]["diff_pool"]["path"])
        pool = validate_diff_pool(pool_path, 4)
        unresolved = [
            item["id"] for item in pool["items"] if item["status"] in {"open", "applied"}
        ]
        if unresolved:
            raise CaseFlowError(f"unverified review diff items remain: {', '.join(unresolved)}")
        closed_target_expectations(case_root, pool)
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
    if not payload.get("article"):
        raise CaseFlowError("case has no finalized article")
    verify_record(case_root, payload["article"], "current article")
    receipt = validate_review_receipt(read_json(receipt_path), payload["article"]["sha256"])
    sources = receipt["sources"]
    degraded = sources["degraded"]
    expected = sources["expected"]
    reported = sources["reported"]
    source_count_mismatch = expected != reported
    findings = receipt["findings"]
    open_questions = receipt["open_questions"]
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
        pool = validate_diff_pool(pool_path, 4, initial=True)
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
    elif gating and not open_questions:
        raise CaseFlowError("gating revmux findings require an exact review diff pool")

    round_record = {
        "path": relative_or_absolute(case_root, receipt_path),
        "sha256": digest(receipt_path),
        "article_sha256": payload["article"]["sha256"],
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
    receipt = validate_review_receipt(
        read_json(resolve_artifact(case_root, round_record["path"])),
        payload["article"]["sha256"],
    )
    findings = receipt["findings"]
    questions = receipt["open_questions"]
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
        pool = validate_diff_pool(pool_path, 4, initial=True)
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


def command_append_review_item(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    pool_path, pool = current_review_pool(case_root, payload)
    item = append_open_item(pool, read_json(resolve_artifact(case_root, args.item_file)), 4)
    atomic_json(pool_path, pool)
    payload["review_rounds"][-1]["diff_pool"]["sha256"] = digest(pool_path)
    save_case(case_root, payload, f"revmux_diff_{item['id']}_appended")
    return {"item": item["id"], "status": "open", "state": payload["state"]}


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
        **target_snapshot(case_root, item),
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
    item["waiver_target_sha256"] = target_snapshot(case_root, item)["target_sha256"]
    item["status"] = "waived"
    item["resolved_at"] = now()
    atomic_json(pool_path, pool)
    payload["review_rounds"][-1]["diff_pool"]["sha256"] = digest(pool_path)
    save_case(case_root, payload, f"revmux_diff_{args.item}_waived")
    return {"item": args.item, "status": "waived"}


def delivery_stage_record(payload: dict[str, Any]) -> dict[str, Any]:
    delivery = payload.get("delivery")
    if not isinstance(delivery, dict):
        raise CaseFlowError("delivery has not been initialized")
    return delivery["stages"][str(delivery["stage"])]


def require_delivery_state(payload: dict[str, Any], *states: str) -> dict[str, Any]:
    require_state(payload, "delivery_active")
    delivery = payload.get("delivery")
    if not isinstance(delivery, dict) or delivery.get("state") not in states:
        expected = ", ".join(states)
        actual = delivery.get("state") if isinstance(delivery, dict) else None
        raise CaseFlowError(f"delivery state must be one of [{expected}], got {actual}")
    return delivery


def command_delivery_submit(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    delivery = require_delivery_state(payload, "lanes")
    if args.stage != delivery["stage"]:
        raise CaseFlowError(f"current delivery stage is {delivery['stage']}")
    if args.lane not in delivery["lanes"]:
        raise CaseFlowError(f"unknown delivery lane: {args.lane}")
    artifact = resolve_artifact(case_root, args.artifact)
    method_basis = resolve_artifact(case_root, args.method_basis)
    record = {
        "path": relative_or_absolute(case_root, artifact),
        "sha256": digest(artifact),
        "method_basis": {
            "path": relative_or_absolute(case_root, method_basis),
            "sha256": digest(method_basis),
        },
        "submitted_at": now(),
    }
    delivery_stage_record(payload)["submissions"][args.lane] = record
    save_case(case_root, payload, f"delivery_stage_{delivery['stage']}_lane_{args.lane}_submitted")
    return record


def command_delivery_open_stitch(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    delivery = require_delivery_state(payload, "lanes")
    record = delivery_stage_record(payload)
    missing = sorted(set(delivery["lanes"]) - set(record["submissions"]))
    if missing:
        raise CaseFlowError(f"delivery lanes missing submissions: {', '.join(missing)}")
    delivery["state"] = "stitching"
    record["state"] = "stitching"
    save_case(case_root, payload, f"delivery_stage_{delivery['stage']}_stitch_opened")
    return {"delivery_stage": delivery["stage"], "delivery_state": delivery["state"]}


def command_delivery_record_stitch(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    delivery = require_delivery_state(payload, "stitching")
    stage = int(delivery["stage"])
    report = resolve_artifact(case_root, args.report)
    pool_path = resolve_artifact(case_root, args.diff_pool)
    pool = validate_diff_pool(pool_path, stage, initial=True)
    record = delivery_stage_record(payload)
    record["stitch"] = {
        "path": relative_or_absolute(case_root, report),
        "sha256": digest(report),
        "recorded_at": now(),
    }
    record["diff_pool"] = {
        "path": relative_or_absolute(case_root, pool_path),
        "sha256": digest(pool_path),
    }
    unresolved = [item["id"] for item in pool["items"]]
    delivery["state"] = "remediation" if unresolved else "ready"
    record["state"] = delivery["state"]
    save_case(case_root, payload, f"delivery_stage_{stage}_stitch_recorded")
    return {"delivery_stage": stage, "delivery_state": delivery["state"], "unresolved_items": unresolved}


def delivery_pool(case_root: Path, payload: dict[str, Any]) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    delivery = require_delivery_state(payload, "remediation", "ready")
    record = delivery_stage_record(payload)
    if not record.get("diff_pool"):
        raise CaseFlowError("delivery stage has no diff pool")
    path = resolve_artifact(case_root, record["diff_pool"]["path"])
    return delivery, path, validate_diff_pool(path, int(delivery["stage"]))


def command_delivery_append_item(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    delivery, pool_path, pool = delivery_pool(case_root, payload)
    stage = int(delivery["stage"])
    item = append_open_item(pool, read_json(resolve_artifact(case_root, args.item_file)), stage)
    atomic_json(pool_path, pool)
    record = delivery_stage_record(payload)
    record["diff_pool"]["sha256"] = digest(pool_path)
    delivery["state"] = "remediation"
    record["state"] = "remediation"
    save_case(case_root, payload, f"delivery_diff_{item['id']}_appended")
    return {"item": item["id"], "status": "open", "delivery_state": delivery["state"]}


def command_delivery_resolve(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    delivery, pool_path, pool = delivery_pool(case_root, payload)
    matching = [item for item in pool["items"] if item["id"] == args.item]
    if not matching or matching[0]["status"] != "open":
        raise CaseFlowError(f"delivery diff item must be open: {args.item}")
    receipt = resolve_artifact(case_root, args.receipt)
    receipt_record = {
        "path": relative_or_absolute(case_root, receipt),
        "sha256": digest(receipt),
        "recorded_at": now(),
    }
    item = matching[0]
    item["receipt"] = receipt_record
    item.setdefault("correction_attempts", []).append(receipt_record)
    item["status"] = "applied"
    atomic_json(pool_path, pool)
    delivery_stage_record(payload)["diff_pool"]["sha256"] = digest(pool_path)
    save_case(case_root, payload, f"delivery_diff_{args.item}_applied")
    return {"item": args.item, "status": "applied"}


def command_delivery_verify(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    delivery, pool_path, pool = delivery_pool(case_root, payload)
    matching = [item for item in pool["items"] if item["id"] == args.item]
    if not matching or matching[0]["status"] != "applied":
        raise CaseFlowError(f"delivery diff item must be applied: {args.item}")
    receipt = resolve_artifact(case_root, args.receipt)
    verification = {
        "path": relative_or_absolute(case_root, receipt),
        "sha256": digest(receipt),
        "result": args.result,
        "recorded_at": now(),
        **target_snapshot(case_root, matching[0]),
    }
    item = matching[0]
    item.setdefault("verification_attempts", []).append(verification)
    if args.result == "pass":
        item["verification_receipt"] = verification
        item["status"] = "verified"
    else:
        item.pop("verification_receipt", None)
        item["status"] = "open"
    atomic_json(pool_path, pool)
    record = delivery_stage_record(payload)
    record["diff_pool"]["sha256"] = digest(pool_path)
    unresolved = [entry["id"] for entry in pool["items"] if entry["status"] in {"open", "applied"}]
    delivery["state"] = "remediation" if unresolved else "ready"
    record["state"] = delivery["state"]
    save_case(case_root, payload, f"delivery_diff_{args.item}_verification_{args.result}")
    return {"item": args.item, "status": item["status"], "remaining_unresolved": unresolved}


def command_delivery_waive(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    delivery, pool_path, pool = delivery_pool(case_root, payload)
    matching = [item for item in pool["items"] if item["id"] == args.item]
    if not matching or matching[0]["status"] != "open":
        raise CaseFlowError(f"delivery diff item must be open: {args.item}")
    if not args.decision_ref.strip():
        raise CaseFlowError("decision_ref cannot be empty")
    item = matching[0]
    item["decision_ref"] = args.decision_ref.strip()
    item["waiver_target_sha256"] = target_snapshot(case_root, item)["target_sha256"]
    item["status"] = "waived"
    atomic_json(pool_path, pool)
    record = delivery_stage_record(payload)
    record["diff_pool"]["sha256"] = digest(pool_path)
    unresolved = [entry["id"] for entry in pool["items"] if entry["status"] in {"open", "applied"}]
    delivery["state"] = "remediation" if unresolved else "ready"
    record["state"] = delivery["state"]
    save_case(case_root, payload, f"delivery_diff_{args.item}_waived")
    return {"item": args.item, "status": "waived", "remaining_unresolved": unresolved}


def command_delivery_advance(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    delivery, _, pool = delivery_pool(case_root, payload)
    if delivery["state"] != "ready":
        raise CaseFlowError("delivery stage is not ready")
    unresolved = [item["id"] for item in pool["items"] if item["status"] in {"open", "applied"}]
    if unresolved:
        raise CaseFlowError(f"unverified delivery diff items remain: {', '.join(unresolved)}")
    stage = int(delivery["stage"])
    record = delivery_stage_record(payload)
    rebound = rebind_stage_outputs(
        case_root,
        record,
        pool,
        label=f"delivery stage {stage}",
    )
    record["state"] = "complete"
    if stage < 4:
        delivery["stage"] = stage + 1
        delivery["state"] = "lanes"
        delivery_stage_record(payload)["state"] = "lanes"
    else:
        delivery["state"] = "complete"
        payload["state"] = "delivery_ready"
    save_case(case_root, payload, f"delivery_stage_{stage}_completed")
    return {
        "delivery_stage": delivery["stage"],
        "delivery_state": delivery["state"],
        "state": payload["state"],
        "rebound": rebound,
    }


def command_route(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "spec_ready")
    verify_record(case_root, payload["article"], "final reviewed article")
    lanes = getattr(args, "lane", []) or []
    if args.decision == "delivery":
        if not lanes or any(not LANE_RE.fullmatch(lane) for lane in lanes):
            raise CaseFlowError("delivery route requires stable uppercase --lane ids")
        if len(lanes) != len(set(lanes)):
            raise CaseFlowError("delivery lanes must be unique")
        payload["delivery"] = {
            "stage": 1,
            "state": "lanes",
            "lanes": lanes,
            "stages": {
                str(stage): {
                    "state": "lanes" if stage == 1 else "pending",
                    "submissions": {},
                    "stitch": None,
                    "diff_pool": None,
                }
                for stage in STAGES
            },
        }
        payload["state"] = "delivery_active"
    else:
        if lanes:
            raise CaseFlowError("stop route does not accept delivery lanes")
        payload["state"] = "stopped_after_spec"
    payload["route"] = args.decision
    save_case(case_root, payload, f"route_{args.decision}_selected")
    return {
        "route": payload["route"],
        "state": payload["state"],
        "delivery": payload.get("delivery"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--case-root", type=Path, required=True)
    init.add_argument("--template", type=Path, required=True)
    init.add_argument("--decision", type=Path, required=True)
    init.add_argument("--plan", type=Path, required=True)
    init.add_argument("--article-id", required=True)
    init.set_defaults(handler=command_init)

    for name, handler in (("status", command_status), ("context", command_context)):
        command = subparsers.add_parser(name)
        command.add_argument("--case-root", type=Path, required=True)
        if name == "context":
            command.add_argument("--block")
            command.add_argument("--lane")
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

    append_item = subparsers.add_parser("append-item")
    append_item.add_argument("--case-root", type=Path, required=True)
    append_item.add_argument("--item-file", required=True)
    append_item.set_defaults(handler=command_append_item)

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("--case-root", type=Path, required=True)
    resolve.add_argument("--item", required=True)
    resolve.add_argument("--receipt", required=True)
    resolve.set_defaults(handler=command_resolve)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--case-root", type=Path, required=True)
    verify.add_argument("--item", required=True)
    verify.add_argument("--receipt", required=True)
    verify.add_argument("--result", choices=("pass", "fail"), required=True)
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

    append_review = subparsers.add_parser("append-review-item")
    append_review.add_argument("--case-root", type=Path, required=True)
    append_review.add_argument("--item-file", required=True)
    append_review.set_defaults(handler=command_append_review_item)

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

    delivery_submit = subparsers.add_parser("delivery-submit")
    delivery_submit.add_argument("--case-root", type=Path, required=True)
    delivery_submit.add_argument("--stage", type=int, choices=STAGES, required=True)
    delivery_submit.add_argument("--lane", required=True)
    delivery_submit.add_argument("--artifact", required=True)
    delivery_submit.add_argument("--method-basis", required=True)
    delivery_submit.set_defaults(handler=command_delivery_submit)

    delivery_stitch = subparsers.add_parser("delivery-open-stitch")
    delivery_stitch.add_argument("--case-root", type=Path, required=True)
    delivery_stitch.set_defaults(handler=command_delivery_open_stitch)

    delivery_record = subparsers.add_parser("delivery-record-stitch")
    delivery_record.add_argument("--case-root", type=Path, required=True)
    delivery_record.add_argument("--report", required=True)
    delivery_record.add_argument("--diff-pool", required=True)
    delivery_record.set_defaults(handler=command_delivery_record_stitch)

    delivery_append = subparsers.add_parser("delivery-append-item")
    delivery_append.add_argument("--case-root", type=Path, required=True)
    delivery_append.add_argument("--item-file", required=True)
    delivery_append.set_defaults(handler=command_delivery_append_item)

    for name, handler in (
        ("delivery-resolve", command_delivery_resolve),
        ("delivery-verify", command_delivery_verify),
    ):
        command = subparsers.add_parser(name)
        command.add_argument("--case-root", type=Path, required=True)
        command.add_argument("--item", required=True)
        command.add_argument("--receipt", required=True)
        if name == "delivery-verify":
            command.add_argument("--result", choices=("pass", "fail"), required=True)
        command.set_defaults(handler=handler)

    delivery_waive = subparsers.add_parser("delivery-waive")
    delivery_waive.add_argument("--case-root", type=Path, required=True)
    delivery_waive.add_argument("--item", required=True)
    delivery_waive.add_argument("--decision-ref", required=True)
    delivery_waive.set_defaults(handler=command_delivery_waive)

    delivery_advance = subparsers.add_parser("delivery-advance")
    delivery_advance.add_argument("--case-root", type=Path, required=True)
    delivery_advance.set_defaults(handler=command_delivery_advance)

    route = subparsers.add_parser("route")
    route.add_argument("--case-root", type=Path, required=True)
    route.add_argument("--decision", choices=("stop", "delivery"), required=True)
    route.add_argument("--lane", action="append", default=[])
    route.set_defaults(handler=command_route)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if hasattr(args, "case_root"):
            with case_lock(args.case_root.resolve(), create=args.command == "init"):
                result = args.handler(args)
        else:
            result = args.handler(args)
    except CaseFlowError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
