#!/usr/bin/env python3
"""Deterministic state for the TRACE specification process."""

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
    from .preanalysis import (
        BriefError,
        DecisionError,
        PlanError,
        validate_article_architecture,
        validate_brief,
        validate_decision,
        validate_plan,
        validate_solution_boundary,
    )
except ImportError:  # Direct script execution.
    from preanalysis import (
        BriefError,
        DecisionError,
        PlanError,
        validate_article_architecture,
        validate_brief,
        validate_decision,
        validate_plan,
        validate_solution_boundary,
    )


SCHEMA = 1
STAGES = (1, 2, 3, 4)
ARTICLE_SUBJECT = "ARTICLE"
ITEM_STATUSES = {"open", "applied", "verified", "waived"}
GATING_SEVERITIES = {"critical", "major"}
MAX_REVIEW_CYCLES = 5
QUALITY_PASS_CHECKS = {
    "simplicity-spec": {
        "minimum-core",
        "seven-step-ladder",
        "element-classification",
        "rewritten-result",
    },
    "humanizer": {
        "draft-rewrite",
        "anti-ai-audit",
        "final-rewrite",
    },
    "simplicity-code": {
        "minimum-core",
        "real-flow",
        "seven-step-ladder",
        "element-classification",
        "runnable-result",
    },
}
QUALITY_PASS_ROLE = "quality-pass-reviewer"
BLOCKING_INPUT_DISPOSITIONS = {"researchable", "user-decision", "external-owner"}
DEFERRED_INPUT_DISPOSITIONS = {"external-owner", "implementation-only"}
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
    if payload.get("preanalysis_brief"):
        verify_record(case_root, payload["preanalysis_brief"], "preanalysis brief")
    architecture = payload.get("architecture")
    if isinstance(architecture, dict) and architecture.get("status") == "designed":
        design_path = Path(architecture["design_ref"]).expanduser().resolve()
        if digest(design_path) != architecture.get("design_sha256"):
            raise CaseFlowError("approved architecture design changed after case initialization")
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
        if record.get("state") == "complete" and record.get("article_projection"):
            projection_path = resolve_artifact(case_root, record["article_projection"]["path"])
            shared_review_path = stage == "4" and projection_path == article_path
            if not shared_review_path:
                verify_record(
                    case_root,
                    record["article_projection"],
                    f"stage {stage} article projection",
                )
        for gate, quality_record in record.get("quality_gates", {}).items():
            verify_record(case_root, quality_record, f"stage {stage} {gate} report")
        if record.get("preanalysis_lineage"):
            verify_record(
                case_root,
                record["preanalysis_lineage"],
                f"stage {stage} preanalysis lineage",
            )
        if record.get("architecture_conformance"):
            verify_record(
                case_root,
                record["architecture_conformance"],
                f"stage {stage} architecture conformance",
            )
        if record.get("diff_pool"):
            verify_record(case_root, record["diff_pool"], f"stage {stage} diff pool")
    for index, round_record in enumerate(payload.get("review_rounds", []), start=1):
        verify_record(case_root, round_record, f"review round {index}")
        if round_record.get("adjudication"):
            verify_record(
                case_root,
                round_record["adjudication"],
                f"review round {index} finding adjudication",
            )
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
            for gate, quality_record in record.get("quality_gates", {}).items():
                verify_record(case_root, quality_record, f"delivery stage {stage} {gate} report")
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
    boundary = payload.get("solution_boundary")
    if boundary is not None:
        try:
            current_contract = bool(payload.get("preanalysis_brief"))
            validate_solution_boundary(boundary, None, require_transition=current_contract)
            if current_contract:
                validate_article_architecture(
                    payload.get("architecture"), boundary["horizon"], "case"
                )
        except (BriefError, DecisionError) as exc:
            raise CaseFlowError(f"case solution boundary is invalid: {exc}") from exc
    if payload.get("composition") != "article-led":
        raise CaseFlowError(
            "case uses the pre-article-led TRACE process; re-baseline it with legacy-case-migration"
        )
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


def required_spec_subjects(payload: dict[str, Any], stage: int | None = None) -> list[str]:
    """Return the subjects authored at one article-led specification stage."""
    stage = stage or int(payload["stage"])
    if stage in {1, 4}:
        return [ARTICLE_SUBJECT]
    return [block["id"] for block in payload["blocks"]]


def validate_input(
    value: Any,
    label: str,
    *,
    allowed_dispositions: set[str],
    require_description: bool = False,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CaseFlowError(f"{label} must be an object")
    fields = ("id", "statement", "reason") if require_description else ("id",)
    for field in fields:
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise CaseFlowError(f"{label}.{field} is required")
    disposition = value.get("disposition")
    if disposition not in allowed_dispositions:
        raise CaseFlowError(f"{label}.disposition is invalid")
    if disposition == "user-decision":
        question = value.get("question")
        if not isinstance(question, str) or not question.strip():
            raise CaseFlowError(f"{label}.question is required for user-decision")
    if disposition == "external-owner":
        owner_ref = value.get("owner_ref")
        if not isinstance(owner_ref, str) or not owner_ref.strip():
            raise CaseFlowError(f"{label}.owner_ref is required for external-owner")
    return value


def validate_diff_payload(
    payload: Any,
    stage: int,
    *,
    initial: bool = False,
    require_readiness: bool = False,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise CaseFlowError("required diff must use schema 1")
    if payload.get("stage") != stage:
        raise CaseFlowError(f"required diff stage must be {stage}")
    items = payload.get("items")
    if not isinstance(items, list):
        raise CaseFlowError("required diff items must be an array")
    deferred_inputs = payload.get("deferred_inputs")
    if require_readiness and not isinstance(deferred_inputs, list):
        raise CaseFlowError("specification stage diff must declare deferred_inputs")
    if deferred_inputs is not None and not isinstance(deferred_inputs, list):
        raise CaseFlowError("required diff deferred_inputs must be an array")
    input_ids: set[str] = set()
    for index, deferred_input in enumerate(deferred_inputs or [], start=1):
        validated = validate_input(
            deferred_input,
            f"deferred_inputs[{index}]",
            allowed_dispositions=DEFERRED_INPUT_DISPOSITIONS,
            require_description=True,
        )
        input_id = validated["id"]
        if input_id in input_ids:
            raise CaseFlowError(f"duplicate input id: {input_id}")
        input_ids.add(input_id)
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
        if status == "verified" and not item.get("verified_at"):
            raise CaseFlowError(f"{item_id} verified without closure timestamp")
        if status == "waived" and not item.get("decision_ref"):
            raise CaseFlowError(f"{item_id} waived without decision_ref")
        if status == "waived" and not SHA256_RE.fullmatch(
            str(item.get("waiver_target_sha256", ""))
        ):
            raise CaseFlowError(f"{item_id} waived without target fingerprint")
        if status == "waived" and not item.get("resolved_at"):
            raise CaseFlowError(f"{item_id} waived without closure timestamp")
        input_value = item.get("input")
        if input_value is not None:
            validated = validate_input(
                input_value,
                f"{item_id}.input",
                allowed_dispositions=BLOCKING_INPUT_DISPOSITIONS,
            )
            input_id = validated["id"]
            if input_id in input_ids:
                raise CaseFlowError(f"duplicate input id: {input_id}")
            input_ids.add(input_id)
            if status == "waived":
                raise CaseFlowError(
                    f"{item_id} blocks specification completeness and cannot be waived"
                )
    return payload


def validate_diff_pool(
    path: Path,
    stage: int,
    *,
    initial: bool = False,
    require_readiness: bool = False,
) -> dict[str, Any]:
    return validate_diff_payload(
        read_json(path),
        stage,
        initial=initial,
        require_readiness=require_readiness,
    )


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
    validate_diff_payload(pool, stage)
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
    source_ids = sources.get("ids")
    if (
        not isinstance(expected, int)
        or isinstance(expected, bool)
        or expected < 1
        or not isinstance(reported, int)
        or isinstance(reported, bool)
        or reported < 0
        or not isinstance(degraded, list)
        or not all(isinstance(item, str) and item.strip() for item in degraded)
        or not isinstance(source_ids, list)
        or len(source_ids) != reported
        or len(set(source_ids)) != len(source_ids)
        or not all(isinstance(item, str) and item.strip() for item in source_ids)
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
        finding_sources = finding.get("sources")
        if (
            not isinstance(finding_sources, list)
            or not finding_sources
            or len(set(finding_sources)) != len(finding_sources)
            or not all(source in source_ids for source in finding_sources)
        ):
            raise CaseFlowError(f"revmux finding has invalid sources: {finding['id']}")
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


def required_review_sources(case_root: Path, payload: dict[str, Any]) -> set[str]:
    """Keep sources of all corrections still awaiting an ordinary review."""
    sources: set[str] = set()
    for round_record in reversed(payload.get("review_rounds", [])):
        diff_pool = round_record.get("diff_pool")
        if not diff_pool:
            continue
        receipt = validate_review_receipt(
            read_json(resolve_artifact(case_root, round_record["path"])),
            round_record["article_sha256"],
        )
        pool = validate_diff_pool(resolve_artifact(case_root, diff_pool["path"]), 4)
        accepted = {item.get("source_finding_id") for item in pool["items"]}
        sources.update(source for finding in receipt["findings"]
                       if finding["id"] in accepted for source in finding["sources"])
        if payload.get("review_protocol") != "article-revmux":
            break
    return sources


def validate_quality_pass(
    case_root: Path,
    report_path: Path,
    gate: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    report = read_json(report_path)
    if not isinstance(report, dict) or report.get("schema") != 1:
        raise CaseFlowError(f"{gate} report must be a schema 1 JSON object")
    if report.get("gate") != gate:
        raise CaseFlowError(f"quality report gate must be {gate}")
    actor = report.get("actor")
    if (
        not isinstance(actor, dict)
        or actor.get("role") != QUALITY_PASS_ROLE
        or not isinstance(actor.get("run_id"), str)
        or not actor["run_id"].strip()
    ):
        raise CaseFlowError(f"{gate} report has no independent assigned role/run_id")
    subject = report.get("subject")
    if (
        not isinstance(subject, dict)
        or not isinstance(subject.get("path"), str)
        or not SHA256_RE.fullmatch(str(subject.get("sha256", "")))
    ):
        raise CaseFlowError(f"{gate} report subject is invalid")
    subject_path = resolve_artifact(case_root, subject["path"])
    if digest(subject_path) != subject["sha256"]:
        raise CaseFlowError(f"{gate} report is not bound to current subject bytes")
    skill = report.get("skill")
    if (
        not isinstance(skill, dict)
        or not isinstance(skill.get("path"), str)
        or not SHA256_RE.fullmatch(str(skill.get("sha256", "")))
    ):
        raise CaseFlowError(f"{gate} report skill fingerprint is invalid")
    skill_path = Path(skill["path"]).expanduser().resolve()
    if skill_path.name != "SKILL.md" or skill_path.parent.name != gate:
        raise CaseFlowError(f"{gate} report does not name the selected skill entrypoint")
    if digest(skill_path) != skill["sha256"]:
        raise CaseFlowError(f"{gate} report skill fingerprint does not match")
    checks = report.get("checks")
    if not isinstance(checks, list) or not all(isinstance(item, str) for item in checks):
        raise CaseFlowError(f"{gate} report checks must be an array of strings")
    missing_checks = sorted(QUALITY_PASS_CHECKS[gate] - set(checks))
    if missing_checks:
        raise CaseFlowError(f"{gate} report missing checks: {', '.join(missing_checks)}")
    findings = report.get("findings")
    if not isinstance(findings, list):
        raise CaseFlowError(f"{gate} report findings must be an array")
    finding_ids: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise CaseFlowError(f"{gate} report contains an invalid finding")
        for field in ("id", "target", "change", "reason"):
            if not isinstance(finding.get(field), str) or not finding[field].strip():
                raise CaseFlowError(f"{gate} finding.{field} is required")
        if finding["id"] in finding_ids:
            raise CaseFlowError(f"duplicate {gate} finding id: {finding['id']}")
        finding_ids.add(finding["id"])
    expected_outcome = "changes-required" if findings else "clean"
    if report.get("outcome") != expected_outcome:
        raise CaseFlowError(f"{gate} report outcome must be {expected_outcome}")
    if gate == "humanizer":
        profile = report.get("style_profile")
        if (
            not isinstance(profile, dict)
            or not isinstance(profile.get("path"), str)
            or not SHA256_RE.fullmatch(str(profile.get("sha256", "")))
        ):
            raise CaseFlowError("humanizer report style_profile is invalid")
        profile_path = Path(profile["path"]).expanduser().resolve()
        if digest(profile_path) != profile["sha256"]:
            raise CaseFlowError("humanizer report style_profile fingerprint does not match")
    record = {
        "path": relative_or_absolute(case_root, report_path),
        "sha256": digest(report_path),
        "subject": subject,
        "actor": actor,
        "outcome": report["outcome"],
        "recorded_at": now(),
    }
    return report, record


def validate_review_adjudication(
    case_root: Path,
    report_path: Path,
    receipt_path: Path,
    receipt: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], set[str], set[str]]:
    report, record = validate_quality_pass(case_root, report_path, "simplicity-spec")
    if report.get("purpose") != "revmux-finding-adjudication":
        raise CaseFlowError("simplicity report purpose must be revmux-finding-adjudication")
    subject_path = resolve_artifact(case_root, report["subject"]["path"])
    if subject_path != receipt_path.resolve():
        raise CaseFlowError("revmux finding adjudication must target the exact review receipt")

    receipt_ids = {finding["id"] for finding in receipt["findings"]}
    dismissed_findings = report.get("dismissed_findings")
    if (
        not isinstance(dismissed_findings, list)
        or not all(
            isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item["id"].strip()
            and isinstance(item.get("reason"), str)
            and item["reason"].strip()
            and isinstance(item.get("evidence"), str)
            and item["evidence"].strip()
            for item in dismissed_findings
        )
    ):
        raise CaseFlowError("revmux finding adjudication dismissed_findings is invalid")

    accepted_ids = {finding["id"] for finding in report["findings"]}
    dismissed = {finding["id"] for finding in dismissed_findings}
    if len(dismissed) != len(dismissed_findings):
        raise CaseFlowError("revmux finding adjudication has duplicate dismissed finding ids")
    if accepted_ids & dismissed:
        raise CaseFlowError("revmux finding cannot be both accepted and dismissed")
    if accepted_ids | dismissed != receipt_ids:
        raise CaseFlowError("revmux finding adjudication must accept or dismiss every finding")
    if not accepted_ids <= receipt_ids:
        raise CaseFlowError("revmux finding adjudication contains an unknown finding id")
    return report, record, accepted_ids, dismissed


def require_quality_findings_in_pool(
    reports: list[dict[str, Any]],
    pool: dict[str, Any],
) -> None:
    covered = {
        item.get("source_finding_id")
        for item in pool["items"]
        if isinstance(item.get("source_finding_id"), str)
    }
    missing = sorted(
        finding["id"]
        for report in reports
        for finding in report["findings"]
        if finding["id"] not in covered
    )
    if missing:
        raise CaseFlowError(f"quality findings missing from required diff: {', '.join(missing)}")


def validate_preanalysis_lineage(
    payload: Any,
    brief: dict[str, Any],
    brief_sha256: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise CaseFlowError("preanalysis lineage must use schema 1")
    if payload.get("brief_sha256") != brief_sha256:
        raise CaseFlowError("preanalysis lineage is not bound to the approved brief")
    dispositions = {"confirmed", "changed", "split", "rejected"}
    for field, brief_field in (
        ("user_stories", "preliminary_user_stories"),
        ("definition_of_done", "preliminary_definition_of_done"),
    ):
        entries = payload.get(field)
        if not isinstance(entries, list):
            raise CaseFlowError(f"preanalysis lineage {field} must be an array")
        expected = {item["id"] for item in brief.get(brief_field, [])}
        seen: set[str] = set()
        for index, entry in enumerate(entries, start=1):
            label = f"{field}[{index}]"
            if not isinstance(entry, dict):
                raise CaseFlowError(f"preanalysis lineage {label} must be an object")
            preliminary_id = entry.get("preliminary_id")
            if not isinstance(preliminary_id, str) or not preliminary_id.strip():
                raise CaseFlowError(f"preanalysis lineage {label}.preliminary_id is required")
            disposition = entry.get("disposition")
            if disposition not in dispositions:
                raise CaseFlowError(f"preanalysis lineage {label}.disposition is invalid")
            final_refs = entry.get("final_refs")
            if not isinstance(final_refs, list) or not all(
                isinstance(item, str) and item.strip() for item in final_refs
            ):
                raise CaseFlowError(f"preanalysis lineage {label}.final_refs is invalid")
            reason = entry.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise CaseFlowError(f"preanalysis lineage {label}.reason is required")
            if disposition == "confirmed" and len(final_refs) != 1:
                raise CaseFlowError(f"preanalysis lineage {label} confirmed requires one final ref")
            if disposition == "changed" and len(final_refs) != 1:
                raise CaseFlowError(f"preanalysis lineage {label} changed requires one final ref")
            if disposition == "split" and len(final_refs) < 2:
                raise CaseFlowError(f"preanalysis lineage {label} split requires at least two final refs")
            if disposition == "rejected" and final_refs:
                raise CaseFlowError(f"preanalysis lineage {label} rejected cannot have final refs")
            if preliminary_id in seen:
                raise CaseFlowError(f"duplicate preanalysis lineage id: {preliminary_id}")
            seen.add(preliminary_id)
        if seen != expected:
            missing = sorted(expected - seen)
            extra = sorted(seen - expected)
            raise CaseFlowError(
                f"preanalysis lineage {field} mismatch; missing={missing}, extra={extra}"
            )
    return payload


def validate_architecture_report(
    case_root: Path,
    report_path: Path,
    article_path: Path,
    architecture: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    article_path = article_path.resolve()
    report = read_json(report_path)
    if not isinstance(report, dict) or report.get("schema") != 1:
        raise CaseFlowError("architecture conformance report must use schema 1")
    if report.get("mode") != "conformance":
        raise CaseFlowError("architecture report mode must be conformance")
    actor = report.get("actor")
    if (
        not isinstance(actor, dict)
        or actor.get("role") != "spec-solution-architect"
        or not isinstance(actor.get("run_id"), str)
        or not actor["run_id"].strip()
    ):
        raise CaseFlowError("architecture report has no assigned architect run")
    subject = report.get("subject")
    if (
        not isinstance(subject, dict)
        or not isinstance(subject.get("path"), str)
        or subject.get("sha256") != digest(article_path)
        or resolve_artifact(case_root, subject["path"]) != article_path
    ):
        raise CaseFlowError("architecture report is not bound to the submitted article")
    if report.get("design_sha256") != architecture.get("design_sha256"):
        raise CaseFlowError("architecture report is not bound to the approved design")
    if actor["run_id"] == architecture.get("design_run_id"):
        raise CaseFlowError("architecture design and conformance require separate runs")
    findings = report.get("findings")
    if not isinstance(findings, list):
        raise CaseFlowError("architecture report findings must be an array")
    finding_ids: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise CaseFlowError("architecture report contains an invalid finding")
        for field in ("id", "target", "change", "reason"):
            if not isinstance(finding.get(field), str) or not finding[field].strip():
                raise CaseFlowError(f"architecture finding.{field} is required")
        if finding["id"] in finding_ids:
            raise CaseFlowError(f"duplicate architecture finding id: {finding['id']}")
        finding_ids.add(finding["id"])
    expected_status = "changes-required" if findings else "conform"
    if report.get("status") != expected_status:
        raise CaseFlowError(f"architecture report status must be {expected_status}")
    record = {
        "path": relative_or_absolute(case_root, report_path),
        "sha256": digest(report_path),
        "subject": subject,
        "actor": actor,
        "status": report["status"],
        "recorded_at": now(),
    }
    return report, record


def validate_architecture_design(
    design_path: Path,
    architecture: dict[str, Any],
) -> dict[str, Any]:
    design = read_json(design_path)
    if not isinstance(design, dict) or design.get("schema") != 1:
        raise CaseFlowError("architecture design must use schema 1")
    if design.get("mode") != "design" or design.get("status") != "designed":
        raise CaseFlowError("architecture design must be a completed design result")
    actor = design.get("actor")
    if (
        not isinstance(actor, dict)
        or actor.get("role") != "spec-solution-architect"
        or actor.get("run_id") != architecture.get("design_run_id")
    ):
        raise CaseFlowError("architecture design does not match its assigned architect run")
    triggers = design.get("triggers")
    if (
        not isinstance(triggers, list)
        or not all(isinstance(item, str) and item.strip() for item in triggers)
        or not set(architecture["triggers"]).issubset(set(triggers))
    ):
        raise CaseFlowError("architecture design does not cover every approved trigger")
    decisions = design.get("decisions")
    gaps = design.get("gaps")
    if not isinstance(decisions, list) or not decisions or not all(
        isinstance(item, dict)
        and all(isinstance(item.get(field), str) and item[field].strip() for field in (
            "id", "surface", "decision", "reason"
        ))
        for item in decisions
    ):
        raise CaseFlowError("architecture design decisions are invalid")
    if gaps != []:
        raise CaseFlowError("approved architecture design cannot contain unresolved gaps")
    return design


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    if manifest_path(case_root).exists():
        raise CaseFlowError(f"case already exists: {case_root}")
    template = args.template.expanduser().resolve()
    if not template.is_file():
        raise CaseFlowError(f"template does not exist: {template}")
    brief_arg = getattr(args, "brief", None)
    if brief_arg is None:
        raise CaseFlowError("current case initialization requires --brief")
    brief_path = brief_arg.expanduser().resolve()
    try:
        brief = validate_brief(read_json(brief_path))
    except BriefError as exc:
        raise CaseFlowError(str(exc)) from exc
    if brief.get("schema") != 4:
        raise CaseFlowError("new cases require preanalysis brief schema 4")
    decision_path = args.decision.expanduser().resolve()
    try:
        decision = validate_decision(read_json(decision_path), require_approved=True)
    except DecisionError as exc:
        raise CaseFlowError(str(exc)) from exc
    if decision.get("schema") != 3:
        raise CaseFlowError("new cases require decomposition decision schema 3")
    plan_path = args.plan.expanduser().resolve()
    try:
        plan = validate_plan(read_json(plan_path))
    except PlanError as exc:
        raise CaseFlowError(str(exc)) from exc
    if plan.get("schema") != 2:
        raise CaseFlowError("new cases require execution plan schema 2")
    if plan.get("status") != "approved":
        raise CaseFlowError("execution plan must be approved before case initialization")
    if plan["subject_id"] != decision["subject_id"]:
        raise CaseFlowError("execution plan and decomposition decision have different subjects")
    if brief["subject_id"] != decision["subject_id"]:
        raise CaseFlowError("preanalysis brief and decomposition decision have different subjects")
    brief_sha256 = digest(brief_path)
    if plan["brief_sha256"] != brief_sha256:
        raise CaseFlowError("execution plan is not bound to the approved brief")
    brief_source_ids = {source["id"] for source in brief["sources"]}
    for task in plan["tasks"]:
        unknown_refs = set(task["source_refs"]) - brief_source_ids
        if unknown_refs:
            raise CaseFlowError(
                f"execution plan task {task['id']} has unknown source refs: {sorted(unknown_refs)}"
            )
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
    if (
        decision["decision"] == "single"
        and article["solution_boundary"] != brief["solution_boundary"]
    ):
        raise CaseFlowError("single-article decision changed the approved solution boundary")
    architecture = dict(article["architecture"])
    expected_architecture_status = (
        "designed" if brief["architecture_gate"]["status"] == "required" else "not-required"
    )
    if decision["decision"] == "single" and architecture["status"] != expected_architecture_status:
        raise CaseFlowError("single-article decision changed the approved architecture gate")
    if (
        decision["decision"] == "single"
        and brief["architecture_gate"]["status"] == "required"
        and not set(brief["architecture_gate"]["triggers"]).issubset(
            set(architecture["triggers"])
        )
    ):
        raise CaseFlowError("approved architecture design does not cover every brief trigger")
    if architecture["status"] == "designed":
        design_path = Path(architecture["design_ref"]).expanduser()
        if not design_path.is_absolute():
            design_path = decision_path.parent / design_path
        design_path = design_path.resolve()
        if digest(design_path) != architecture["design_sha256"]:
            raise CaseFlowError("approved architecture design fingerprint does not match")
        validate_architecture_design(design_path, architecture)
        architecture["design_ref"] = str(design_path)
    blocks = article["blocks"]
    ids = [block["id"] for block in blocks]
    case_root.mkdir(parents=True, exist_ok=True)
    (case_root / ".caseflow.lock").touch(exist_ok=True)
    for block_id in ids:
        (case_root / "blocks" / block_id).mkdir(parents=True, exist_ok=True)
    (case_root / "articles").mkdir(exist_ok=True)
    (case_root / "stitches").mkdir(exist_ok=True)
    (case_root / "diffs").mkdir(exist_ok=True)
    (case_root / "method-basis").mkdir(exist_ok=True)
    created = now()
    stages = {
        str(stage): {
            "state": "blocks" if stage == 1 else "pending",
            "submissions": {},
            "stitch": None,
            "article_projection": None,
            "diff_pool": None,
        }
        for stage in STAGES
    }
    payload = {
        "schema": SCHEMA,
        "case_id": article["id"],
        "title": article["title"],
        "composition": article["composition"],
        "solution_boundary": article.get("solution_boundary"),
        "architecture": architecture,
        "preanalysis_brief": {
            "path": str(brief_path),
            "sha256": brief_sha256,
        },
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
        "review_protocol": "article-revmux",
        "route": None,
        "article": None,
        "review_rounds": [],
        "blocks": blocks,
        "stages": stages,
        "created_at": created,
        "updated_at": created,
        "events": [{"at": created, "event": "case_initialized_article_led"}],
    }
    atomic_json(manifest_path(case_root), payload)
    return payload


def command_status(args: argparse.Namespace) -> dict[str, Any]:
    payload = load_case(args.case_root.resolve())
    review_cycles = review_cycles_used(payload)
    delivery = payload.get("delivery")
    current = delivery_stage_record(payload) if delivery else stage_record(payload)
    current_stage = delivery["stage"] if delivery else payload["stage"]
    open_count = None
    blocking_input_count = None
    deferred_input_count = None
    if current.get("diff_pool"):
        pool_path = resolve_artifact(args.case_root.resolve(), current["diff_pool"]["path"])
        pool = validate_diff_pool(pool_path, int(current_stage))
        open_count = sum(item["status"] in {"open", "applied"} for item in pool["items"])
        blocking_input_count = sum(item.get("input") is not None for item in pool["items"])
        deferred_input_count = len(pool.get("deferred_inputs", []))
    result = {
        "case_id": payload["case_id"],
        "solution_horizon": (
            payload["solution_boundary"]["horizon"]
            if isinstance(payload.get("solution_boundary"), dict)
            else None
        ),
        "architecture_status": payload.get("architecture", {}).get("status"),
        "preanalysis_lineage_recorded": bool(
            stage_record(payload, 1).get("preanalysis_lineage")
        ),
        "stage": payload["stage"],
        "state": payload["state"],
        "route": payload["route"],
        "submitted_blocks": sorted(current["submissions"]),
        "required_blocks": delivery["lanes"] if delivery else required_spec_subjects(payload),
        "open_diff_items": open_count,
        "blocking_inputs": blocking_input_count,
        "deferred_inputs": deferred_input_count,
        "content_ready_for_review": bool(stage_record(payload, 4).get("content_ready_at")),
        "next_skill": "delivery-workflow" if payload["route"] == "delivery" else "spec-workflow",
        "review_cycles_used": review_cycles,
        "review_cycles_remaining": max(0, MAX_REVIEW_CYCLES - review_cycles),
    }
    if payload.get("delivery"):
        result["delivery_stage"] = payload["delivery"]["stage"]
        result["delivery_state"] = payload["delivery"]["state"]
        result["delivery_lanes"] = payload["delivery"]["lanes"]
    return result


def review_cycles_used(payload: dict[str, Any]) -> int:
    return sum(
        1
        for round_record in payload.get("review_rounds", [])
        if not round_record.get("degraded")
        and not round_record.get("source_count_mismatch")
    )


def command_context(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    assignment_paths = [str(Path(value).expanduser().resolve())
                        for field in ("project_rule", "source")
                        for value in (getattr(args, field, None) or [])]
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
        read_set = list(dict.fromkeys(read_set + assignment_paths))
        return {
            "mode": "delivery",
            "delivery_stage": stage,
            "delivery_state": delivery["state"],
            "lane": lane,
            "solution_boundary": payload.get("solution_boundary"),
            "read_set": [path for path in read_set if Path(path).exists()],
            "missing_required": [path for path in read_set if not Path(path).exists()],
            "rule": "read only the current delivery stage reference and this read_set",
        }
    stage = int(payload["stage"])
    if lane:
        raise CaseFlowError("specification context uses --block, not --lane")
    required_subjects = set(required_spec_subjects(payload, stage))
    if args.block and args.block not in required_subjects:
        raise CaseFlowError(f"unknown block: {args.block}")
    read_set: list[str] = [str(PROCESS_KERNEL), payload["template"]]
    if args.block:
        read_set.append(str(case_root / "method-basis" / f"stage-{stage:02d}-{args.block}.md"))
    source_index = case_root / "sources.md"
    if stage == 1:
        read_set.extend(
            [
                str(resolve_artifact(case_root, payload["preanalysis_brief"]["path"])),
                str(resolve_artifact(case_root, payload["decomposition_decision"]["path"])),
                str(resolve_artifact(case_root, payload["execution_plan"]["path"])),
            ]
        )
        if source_index.exists():
            read_set.append(str(source_index))
        if payload.get("architecture", {}).get("status") == "designed":
            read_set.append(str(Path(payload["architecture"]["design_ref"])))
    elif stage in (2, 3):
        previous = stage_record(payload, stage - 1)
        previous_article = previous.get("article_projection")
        if previous_article:
            read_set.append(str(resolve_artifact(case_root, previous_article["path"])))
        if args.block:
            source_map = case_root / "blocks" / args.block / "source-map.md"
            if source_map.exists():
                read_set.append(str(source_map))
        if stage == 3 and args.block:
            submission = stage_record(payload, 2)["submissions"].get(args.block)
            if submission:
                read_set.append(str(resolve_artifact(case_root, submission["path"])))
        previous_stitch = previous.get("stitch")
        if previous_stitch:
            read_set.append(str(resolve_artifact(case_root, previous_stitch["path"])))
    else:
        previous = stage_record(payload, 3)
        previous_article = previous.get("article_projection")
        if previous_article:
            read_set.append(str(resolve_artifact(case_root, previous_article["path"])))
        previous_stitch = previous.get("stitch")
        if previous_stitch:
            read_set.append(str(resolve_artifact(case_root, previous_stitch["path"])))
        if payload.get("architecture", {}).get("status") == "designed":
            read_set.append(str(Path(payload["architecture"]["design_ref"])))
    if not args.block:
        for submission in stage_record(payload)["submissions"].values():
            read_set.append(str(resolve_artifact(case_root, submission["path"])))
    read_set = list(dict.fromkeys(read_set + assignment_paths))
    existing = [path for path in read_set if Path(path).exists()]
    missing = [path for path in read_set if not Path(path).exists()]
    return {
        "stage": stage,
        "mode": "specification",
        "state": payload["state"],
        "block": args.block,
        "solution_boundary": payload.get("solution_boundary"),
        "architecture": payload.get("architecture"),
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
    known = set(required_spec_subjects(payload, stage))
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
    required = set(required_spec_subjects(payload))
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
    pool_arg = getattr(args, "diff_pool", None)
    if payload.get("review_protocol") == "article-revmux" and pool_arg:
        raise CaseFlowError("specification diff pools are created only from revmux findings")
    pool_path = resolve_artifact(case_root, pool_arg) if pool_arg else None
    pool = (validate_diff_pool(pool_path, stage, initial=True, require_readiness=True)
            if pool_path else {"items": [], "deferred_inputs": []})
    if not pool_path:
        readiness = read_json(report)
        if (not isinstance(readiness, dict) or readiness.get("schema") != 1
                or readiness.get("stage") != stage
                or readiness.get("status") != "ready"
                or readiness.get("open_inputs") != []):
            raise CaseFlowError("stitch report requires schema 1, matching stage, status ready and open_inputs []")
        payload["review_protocol"] = "article-revmux"
    record = stage_record(payload)
    article_arg = getattr(args, "article", None)
    if stage in {1, 4}:
        article_submission = record["submissions"].get(ARTICLE_SUBJECT)
        if not article_submission:
            raise CaseFlowError(f"stage {stage} requires the ARTICLE submission")
        article_path = resolve_artifact(case_root, article_submission["path"])
        if article_arg and resolve_artifact(case_root, article_arg) != article_path:
            raise CaseFlowError(f"stage {stage} article must match the ARTICLE submission")
    else:
        if not article_arg:
            raise CaseFlowError(f"stage {stage} stitch requires --article")
        article_path = resolve_artifact(case_root, article_arg)
        previous_projection = stage_record(payload, stage - 1).get("article_projection")
        if not previous_projection:
            raise CaseFlowError(f"stage {stage - 1} has no article projection")
    template_path = Path(payload["template"]).expanduser().resolve()
    prior_projection_paths = {
        resolve_artifact(case_root, prior["article_projection"]["path"])
        for prior_stage in range(1, stage)
        if (prior := stage_record(payload, prior_stage)).get("article_projection")
    }
    if article_path == template_path or article_path in prior_projection_paths:
        raise CaseFlowError("each stage must write a new immutable article projection")
    if stage == 1:
        lineage_path = (case_root / "preanalysis-lineage.json").resolve()
        brief_record = payload.get("preanalysis_brief")
        if not isinstance(brief_record, dict):
            raise CaseFlowError("stage 1 requires a bound preanalysis brief")
        try:
            brief = validate_brief(read_json(resolve_artifact(case_root, brief_record["path"])))
        except BriefError as exc:
            raise CaseFlowError(str(exc)) from exc
        lineage = validate_preanalysis_lineage(
            read_json(lineage_path), brief, brief_record["sha256"]
        )
        article_text = article_path.read_text(encoding="utf-8")
        missing_final_refs = sorted(
            final_ref
            for field in ("user_stories", "definition_of_done")
            for entry in lineage[field]
            for final_ref in entry["final_refs"]
            if final_ref not in article_text
        )
        if missing_final_refs:
            raise CaseFlowError(
                "preanalysis lineage final refs are missing from the article: "
                + ", ".join(missing_final_refs)
            )
        record["preanalysis_lineage"] = {
            "path": relative_or_absolute(case_root, lineage_path),
            "sha256": digest(lineage_path),
            "user_stories": len(lineage["user_stories"]),
            "definition_of_done": len(lineage["definition_of_done"]),
            "recorded_at": now(),
        }
    if stage == 4 and pool_path:
        simplicity_arg = getattr(args, "simplicity_report", None)
        humanizer_arg = getattr(args, "humanizer_report", None)
        if not simplicity_arg or not humanizer_arg:
            raise CaseFlowError("stage 4 requires simplicity-spec and humanizer reports")
        simplicity_path = resolve_artifact(case_root, simplicity_arg)
        humanizer_path = resolve_artifact(case_root, humanizer_arg)
        simplicity, simplicity_record = validate_quality_pass(
            case_root, simplicity_path, "simplicity-spec"
        )
        humanizer, humanizer_record = validate_quality_pass(case_root, humanizer_path, "humanizer")
        if simplicity["actor"]["run_id"] == humanizer["actor"]["run_id"]:
            raise CaseFlowError("simplicity-spec and humanizer require separate assigned runs")
        simplicity_subject = (
            resolve_artifact(case_root, simplicity["subject"]["path"]),
            simplicity["subject"]["sha256"],
        )
        humanizer_subject = (
            resolve_artifact(case_root, humanizer["subject"]["path"]),
            humanizer["subject"]["sha256"],
        )
        if simplicity_subject != humanizer_subject:
            raise CaseFlowError("stage 4 quality reports must inspect the same article bytes")
        submitted = {
            (resolve_artifact(case_root, entry["path"]), entry["sha256"])
            for entry in record["submissions"].values()
        }
        if simplicity_subject not in submitted:
            raise CaseFlowError("stage 4 quality reports do not target a submitted article")
        require_quality_findings_in_pool([simplicity, humanizer], pool)
        record["quality_gates"] = {
            "simplicity-spec": simplicity_record,
            "humanizer": humanizer_record,
        }
        architecture = payload.get("architecture", {})
        if architecture.get("status") == "designed":
            architecture_arg = getattr(args, "architecture_report", None)
            if not architecture_arg:
                raise CaseFlowError("stage 4 requires architecture conformance report")
            architecture_report, architecture_record = validate_architecture_report(
                case_root,
                resolve_artifact(case_root, architecture_arg),
                article_path,
                architecture,
            )
            require_quality_findings_in_pool([architecture_report], pool)
            record["architecture_conformance"] = architecture_record
    record["stitch"] = {
        "path": relative_or_absolute(case_root, report),
        "sha256": digest(report),
        "recorded_at": now(),
    }
    record["article_projection"] = {
        "path": relative_or_absolute(case_root, article_path),
        "sha256": digest(article_path),
        "recorded_at": now(),
    }
    record["diff_pool"] = {
        "path": relative_or_absolute(case_root, pool_path),
        "sha256": digest(pool_path),
    } if pool_path else None
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
    if status == "waived" and item.get("input") is not None:
        raise CaseFlowError(f"{item_id} blocks specification completeness and cannot be waived")
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
    ordered: dict[Path, tuple[datetime, int, str]] = {}
    for index, item in enumerate(pool["items"]):
        if item["status"] == "verified":
            expected_hash = item["verification_receipt"]["target_sha256"]
            closed_at = item["verified_at"]
        elif item["status"] == "waived":
            expected_hash = item["waiver_target_sha256"]
            closed_at = item["resolved_at"]
        else:
            continue
        try:
            closed_moment = datetime.fromisoformat(str(closed_at))
        except ValueError as exc:
            raise CaseFlowError(f"diff item has invalid closure timestamp: {item['id']}") from exc
        if closed_moment.tzinfo is None:
            raise CaseFlowError(f"diff item closure timestamp has no timezone: {item['id']}")
        path = normalized_target_path(case_root, item["target"])
        candidate = (closed_moment.astimezone(timezone.utc), index, expected_hash)
        if path not in ordered or candidate[:2] > ordered[path][:2]:
            ordered[path] = candidate
    expected = {path: candidate[2] for path, candidate in ordered.items()}
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
    if record.get("article_projection"):
        records.append(record["article_projection"])
    processed_paths: set[Path] = set()
    for artifact_record in records:
        path = resolve_artifact(case_root, artifact_record["path"])
        if path in processed_paths:
            artifact_record["sha256"] = digest(path)
            continue
        processed_paths.add(path)
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
    pool_record = record.get("diff_pool")
    pool = (validate_diff_pool(resolve_artifact(case_root, pool_record["path"]), stage)
            if pool_record else {"items": []})
    unresolved = [item["id"] for item in pool["items"] if item["status"] in {"open", "applied"}]
    if unresolved:
        raise CaseFlowError(f"unverified diff items remain: {', '.join(unresolved)}")
    incomplete_inputs = [
        item["id"]
        for item in pool["items"]
        if item.get("input") is not None and item["status"] != "verified"
    ]
    if incomplete_inputs:
        raise CaseFlowError(
            "specification-blocking inputs are not verified: " + ", ".join(incomplete_inputs)
        )
    if pool_record:
        rebound = rebind_stage_outputs(case_root, record, pool, label=f"stage {stage}")
    else:
        verify_record(case_root, record["article_projection"], f"stage {stage} article")
        verify_record(case_root, record["stitch"], f"stage {stage} stitch")
        for submission in record["submissions"].values():
            verify_record(case_root, submission, f"stage {stage} submission")
            verify_record(case_root, submission["method_basis"], f"stage {stage} method basis")
        rebound = []
    if not record.get("article_projection"):
        raise CaseFlowError(f"stage {stage} has no article projection")
    record["state"] = "complete"
    if stage < 4:
        payload["stage"] = stage + 1
        payload["state"] = "blocks"
        stage_record(payload)["state"] = "blocks"
        event = f"stage_{stage}_completed_stage_{stage + 1}_opened"
    else:
        record["content_ready_at"] = now()
        payload["state"] = "article_pending"
        event = "stage_4_completed_article_pending"
    save_case(case_root, payload, event)
    return {"stage": payload["stage"], "state": payload["state"], "rebound": rebound}


def command_finalize_article(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "article_pending")
    if not stage_record(payload, 4).get("content_ready_at"):
        raise CaseFlowError("stage 4 has no verified content-readiness marker")
    article = resolve_artifact(case_root, args.article)
    projection = stage_record(payload, 4).get("article_projection")
    if not projection:
        raise CaseFlowError("stage 4 has no article projection")
    projection_path = resolve_artifact(case_root, projection["path"])
    if article != projection_path or digest(article) != projection["sha256"]:
        raise CaseFlowError("final article must be the verified stage 4 projection")
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
    current_article = resolve_artifact(case_root, payload["article"]["path"])
    article = resolve_artifact(case_root, args.article)
    if article != current_article:
        raise CaseFlowError("article-updated cannot change the registered article path")
    if payload.get("review_protocol") == "article-revmux":
        if payload["state"] == "revmux_remediation":
            _, pool = current_review_pool(case_root, payload)
            for item in pool["items"]:
                if item["status"] == "waived":
                    continue
                if item["status"] != "applied":
                    raise CaseFlowError("apply every review finding to the article before the next revmux")
                if item["receipt"].get("article_sha256") != digest(article):
                    raise CaseFlowError("correction receipt does not match the updated article bytes")
            if any(item["status"] == "applied" for item in pool["items"]):
                if digest(article) == payload["article"]["sha256"]:
                    raise CaseFlowError("an intermediate-only fix does not change the reviewed article")
        elif payload["review_rounds"] and digest(article) != payload["article"]["sha256"]:
            raise CaseFlowError("after revmux, article changes require its findings pool")
        payload["article"]["sha256"] = digest(article)
        payload["article"]["recorded_at"] = now()
        payload["state"] = "revmux_pending"
        save_case(case_root, payload, "article_updated_revmux_pending")
        return {"article": payload["article"], "state": payload["state"]}
    closed_targets: dict[Path, str] = {}
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
        closed_targets = closed_target_expectations(case_root, pool)
    if payload["state"] == "revmux_remediation":
        if article not in closed_targets and digest(article) != payload["article"]["sha256"]:
            raise CaseFlowError("article changed without a closed review diff target")
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
    if not stage_record(payload, 4).get("content_ready_at"):
        raise CaseFlowError(
            "revmux cannot start before verified stage 4 content readiness"
        )
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
    required_sources = required_review_sources(case_root, payload)
    missing_required_sources = required_sources - set(sources["ids"])
    if not degraded and not source_count_mismatch and missing_required_sources:
        raise CaseFlowError(
            "revmux round cannot close accepted finding classes without sources: "
            + ", ".join(sorted(missing_required_sources))
        )
    cap_decision_ref = getattr(args, "cap_decision_ref", None)
    if (
        not degraded
        and not source_count_mismatch
        and review_cycles_used(payload) >= MAX_REVIEW_CYCLES
        and not (isinstance(cap_decision_ref, str) and cap_decision_ref.strip())
    ):
        raise CaseFlowError(
            "review cycle cap reached; another substantive round requires --cap-decision-ref"
        )
    findings = receipt["findings"]
    open_questions = receipt["open_questions"]
    accepted_ids = {finding["id"] for finding in findings}
    dismissed_ids: set[str] = set()
    adjudication_record = None
    adjudication_arg = getattr(args, "adjudication_report", None)
    if degraded or source_count_mismatch:
        if adjudication_arg:
            raise CaseFlowError("degraded revmux round must be rerun before finding adjudication")
    elif findings:
        if not adjudication_arg:
            raise CaseFlowError(
                "complete revmux round with findings requires --adjudication-report"
            )
        adjudication_path = resolve_artifact(case_root, adjudication_arg)
        _, adjudication_record, accepted_ids, dismissed_ids = validate_review_adjudication(
            case_root,
            adjudication_path,
            receipt_path,
            receipt,
        )
    elif adjudication_arg:
        raise CaseFlowError("finding adjudication is unnecessary when revmux reported no findings")
    accepted_findings = [finding for finding in findings if finding["id"] in accepted_ids]
    gating = [
        finding
        for finding in accepted_findings
        if isinstance(finding, dict) and finding.get("severity") in GATING_SEVERITIES
    ]
    stop_at_minor = getattr(args, "stop_at_minor", False)
    if stop_at_minor and (
        degraded or source_count_mismatch or open_questions
        or not accepted_findings or gating
    ):
        raise CaseFlowError("--stop-at-minor requires only accepted minor findings and complete sources")
    diff_pool_arg = getattr(args, "diff_pool", None)
    if stop_at_minor and diff_pool_arg:
        raise CaseFlowError("--stop-at-minor pauses before forming a correction diff pool")
    diff_pool_record = None
    if open_questions and diff_pool_arg:
        raise CaseFlowError("answer revmux open questions before forming a review diff pool")
    if degraded or source_count_mismatch:
        if diff_pool_arg:
            raise CaseFlowError("degraded revmux round must be rerun before forming a diff pool")
    elif diff_pool_arg:
        pool_path = resolve_artifact(case_root, diff_pool_arg)
        pool = validate_diff_pool(pool_path, 4, initial=True)
        if payload.get("review_protocol") == "article-revmux":
            article = resolve_artifact(case_root, payload["article"]["path"])
            if any(normalized_target_path(case_root, item["target"]) != article for item in pool["items"]):
                raise CaseFlowError("every revmux correction must target the final article")
        if not pool["items"]:
            raise CaseFlowError("review diff pool cannot be empty")
        finding_ids = set(accepted_ids)
        covered_ids = {item.get("source_finding_id") for item in pool["items"]}
        if None in covered_ids:
            raise CaseFlowError("every review diff item requires source_finding_id")
        unknown_ids = covered_ids - finding_ids
        if unknown_ids:
            raise CaseFlowError(
                f"review diff has unaccepted or unknown finding ids: {sorted(unknown_ids)}"
            )
        missing_accepted = finding_ids - covered_ids
        if missing_accepted:
            raise CaseFlowError(
                f"review diff does not cover accepted findings: {sorted(missing_accepted)}"
            )
        diff_pool_record = {
            "path": relative_or_absolute(case_root, pool_path),
            "sha256": digest(pool_path),
        }
    elif accepted_findings and not open_questions and not stop_at_minor:
        raise CaseFlowError("accepted revmux findings require an exact review diff pool")

    round_record = {
        "path": relative_or_absolute(case_root, receipt_path),
        "sha256": digest(receipt_path),
        "article_sha256": payload["article"]["sha256"],
        "degraded": degraded,
        "source_count_mismatch": source_count_mismatch,
        "source_ids": sources["ids"],
        "required_source_ids": sorted(required_sources),
        "gating_findings": len(gating),
        "findings": len(findings),
        "accepted_finding_ids": sorted(accepted_ids),
        "dismissed_finding_ids": sorted(dismissed_ids),
        "open_questions": len(open_questions),
        "recorded_at": now(),
    }
    if adjudication_record:
        round_record["adjudication"] = adjudication_record
    if diff_pool_record:
        round_record["diff_pool"] = diff_pool_record
    if isinstance(cap_decision_ref, str) and cap_decision_ref.strip():
        round_record["cap_decision_ref"] = cap_decision_ref.strip()
    payload["review_rounds"].append(round_record)
    if degraded or source_count_mismatch:
        payload["state"] = "revmux_pending"
    elif stop_at_minor:
        payload["state"] = "revmux_minor_pending"
    elif open_questions:
        payload["state"] = "revmux_decision_pending"
    elif diff_pool_record:
        payload["state"] = "revmux_remediation"
    else:
        payload["state"] = "spec_ready"
    if payload.get("review_protocol") == "article-revmux" and payload["state"] == "spec_ready":
        for previous in payload["review_rounds"][:-1]:
            if not previous.get("diff_pool"):
                continue
            previous_path = resolve_artifact(case_root, previous["diff_pool"]["path"])
            previous_pool = validate_diff_pool(previous_path, 4)
            for item in previous_pool["items"]:
                if item["status"] == "applied":
                    item["status"] = "verified"
                    item["verification_receipt"] = {
                        "path": relative_or_absolute(case_root, receipt_path),
                        "sha256": digest(receipt_path),
                        "article_sha256": payload["article"]["sha256"],
                        "kind": "ordinary-revmux",
                        "recorded_at": now(),
                    }
            atomic_json(previous_path, previous_pool)
            previous["diff_pool"]["sha256"] = digest(previous_path)
    save_case(case_root, payload, f"revmux_round_{len(payload['review_rounds'])}_recorded")
    return {
        "state": payload["state"],
        "degraded": degraded,
        "source_count_mismatch": source_count_mismatch,
        "required_source_ids": sorted(required_sources),
        "gating_findings": gating,
        "accepted_finding_ids": sorted(accepted_ids),
        "dismissed_finding_ids": sorted(dismissed_ids),
        "review_cycles_used": review_cycles_used(payload),
        "review_cycles_remaining": max(0, MAX_REVIEW_CYCLES - review_cycles_used(payload)),
    }


def command_record_review_decisions(args: argparse.Namespace) -> dict[str, Any]:
    case_root = args.case_root.resolve()
    payload = load_case(case_root)
    require_state(payload, "revmux_decision_pending", "revmux_minor_pending")
    if not args.decision_ref.strip():
        raise CaseFlowError("decision_ref cannot be empty")
    round_record = payload["review_rounds"][-1]
    receipt = validate_review_receipt(
        read_json(resolve_artifact(case_root, round_record["path"])),
        payload["article"]["sha256"],
    )
    questions = receipt["open_questions"]
    if "accepted_finding_ids" not in round_record:
        raise CaseFlowError("review round has no recorded finding adjudication")
    accepted_ids = set(round_record["accepted_finding_ids"])
    diff_pool_arg = getattr(args, "diff_pool", None)
    if accepted_ids and not diff_pool_arg:
        raise CaseFlowError("accepted findings still require an exact review diff pool")
    if diff_pool_arg:
        pool_path = resolve_artifact(case_root, diff_pool_arg)
        pool = validate_diff_pool(pool_path, 4, initial=True)
        if payload.get("review_protocol") == "article-revmux":
            article = resolve_artifact(case_root, payload["article"]["path"])
            if any(normalized_target_path(case_root, item["target"]) != article for item in pool["items"]):
                raise CaseFlowError("every revmux correction must target the final article")
        if not pool["items"]:
            raise CaseFlowError("review decision diff pool cannot be empty")
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
                if finding_id not in accepted_ids:
                    raise CaseFlowError(
                        f"review diff has unaccepted or unknown finding id: {finding_id}"
                    )
                covered_findings.add(finding_id)
            elif question_id not in question_ids:
                raise CaseFlowError(f"review diff has unknown question id: {question_id}")
        missing_accepted = accepted_ids - covered_findings
        if missing_accepted:
            raise CaseFlowError(
                f"review diff does not cover accepted findings: {sorted(missing_accepted)}"
            )
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
    if payload.get("review_protocol") == "article-revmux":
        raise CaseFlowError("new findings must come from the next ordinary revmux round")
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
    if payload.get("review_protocol") == "article-revmux":
        article = resolve_artifact(case_root, payload["article"]["path"])
        if normalized_target_path(case_root, item["target"]) != article:
            raise CaseFlowError("revmux fixes must target the final article; synchronize sources additionally")
        if digest(article) == payload["article"]["sha256"]:
            raise CaseFlowError("an intermediate-only fix does not change the reviewed article")
        receipt_record["article_sha256"] = digest(article)
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
    if payload.get("review_protocol") == "article-revmux":
        raise CaseFlowError("use the next ordinary revmux round, not targeted verification")
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
    if stage == 2:
        simplicity_arg = getattr(args, "simplicity_report", None)
        if not simplicity_arg:
            raise CaseFlowError("delivery stage 2 requires a simplicity-code report")
        simplicity_path = resolve_artifact(case_root, simplicity_arg)
        simplicity, simplicity_record = validate_quality_pass(
            case_root, simplicity_path, "simplicity-code"
        )
        require_quality_findings_in_pool([simplicity], pool)
        record["quality_gates"] = {"simplicity-code": simplicity_record}
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
        item["verified_at"] = now()
    else:
        item.pop("verification_receipt", None)
        item["status"] = "open"
        item["reopened_at"] = now()
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
    item["resolved_at"] = now()
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
    init.add_argument("--brief", type=Path, required=True)
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
            command.add_argument("--project-rule", action="append", default=[])
            command.add_argument("--source", action="append", default=[])
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
    record.add_argument("--diff-pool", help="Compatibility only: legacy stage pool")
    record.add_argument("--article")
    record.add_argument("--simplicity-report")
    record.add_argument("--humanizer-report")
    record.add_argument("--architecture-report")
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
    review.add_argument("--adjudication-report")
    review.add_argument("--diff-pool")
    review.add_argument("--cap-decision-ref")
    review.add_argument("--stop-at-minor", action="store_true")
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
    delivery_record.add_argument("--simplicity-report")
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
