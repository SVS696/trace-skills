from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import caseflow


def legacy_init(args):
    """Build the historical manifest shape for legacy compatibility tests."""
    payload = caseflow.command_init(args)
    payload.pop("review_protocol", None)
    caseflow.save_case(args.case_root, payload, "legacy_fixture")
    return payload


def solution_boundary() -> dict:
    return {
        "horizon": "bounded-systemic",
        "observed_case": "Current channel",
        "root_capability": "Apply one rule across supported channels",
        "invariants": ["The rule has one owner"],
        "confirmed_variants": [
            {"name": "Current channel", "evidence_refs": ["SRC-1"]}
        ],
        "hypothesized_variants": [],
        "current_scope": ["Current channel"],
        "extension_seams": ["Localized channel selection"],
        "extension_seam_absence_reason": None,
        "deferred_variants": [],
        "expansion_triggers": ["A second channel is confirmed"],
        "horizon_evidence": {
            "analogy_search_refs": [],
            "roadmap_refs": [],
            "irreversibility_refs": [],
        },
        "hotfix_exception": None,
        "implementation_transition": {
            "status": "selected",
            "mode": "evolve-in-place",
            "authoritative_owner": "current-rule-owner",
            "superseded_paths": [],
            "coexistence_reason": None,
            "stages": [],
            "retirement_trigger": None,
            "rollback_boundary": None,
            "evidence_refs": ["SRC-1"],
            "reason": "The existing owner remains authoritative",
        },
    }


class CaseFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.case_root = self.root / "case"
        self.template = self.root / "template.md"
        self.template.write_text("# Template\n", encoding="utf-8")
        self.brief = self.root / "preanalysis-brief.json"
        self.brief.write_text(
            json.dumps(
                {
                    "schema": 4,
                    "subject_id": "CASE-1",
                    "sources": [
                        {
                            "id": "SRC-1",
                            "kind": "request",
                            "ref": "request-1",
                            "query": "Resolve requested behavior",
                            "authority": "user-request",
                            "status": "found",
                            "checked_at": "2026-09-06T10:00:00+00:00",
                            "freshness": "current",
                        }
                    ],
                    "facts": [
                        {"id": "F-1", "statement": "Requested behavior", "evidence_refs": ["SRC-1"]}
                    ],
                    "contradictions": [],
                    "coverage": {
                        "verdict": "sufficient",
                        "surfaces": [
                            {
                                "id": "COV-1",
                                "question": "What must the article specify?",
                                "status": "covered",
                                "source_refs": ["SRC-1"],
                                "gap_refs": [],
                            }
                        ],
                    },
                    "problem": {
                        "statement": "The operator repeats the job",
                        "affected_actors": ["Operator"],
                        "negative_consequences": ["The operator loses time to repeated work"],
                        "evidence_refs": ["SRC-1"],
                    },
                    "goal": {
                        "statement": "The operator completes the job once",
                        "beneficiaries": ["Operator"],
                        "benefits": ["The operator avoids repeated work"],
                        "evidence_refs": ["SRC-1"],
                    },
                    "solution_essence": {
                        "statement": "Keep one authoritative result",
                        "behavior_changes": ["The system reuses the authoritative result"],
                        "problem_resolution": "Repeated work is no longer required",
                        "evidence_refs": ["SRC-1"],
                    },
                    "solution_boundary": solution_boundary(),
                    "architecture_gate": {
                        "status": "not-required",
                        "triggers": [],
                        "reason": "No architectural boundary changes",
                    },
                    "preliminary_user_stories": [
                        {
                            "id": "PUS-1",
                            "actor": "Operator",
                            "need": "complete the job once",
                            "value": "avoid repeated work",
                            "evidence_refs": ["SRC-1"],
                            "confidence": "high",
                        }
                    ],
                    "preliminary_definition_of_done": [],
                    "scope_in": [],
                    "scope_out": [],
                    "unknowns": [],
                    "assumptions": [],
                    "dependencies": [],
                    "estimate": {"status": "unavailable", "reason": "No implementation contour"},
                }
            ),
            encoding="utf-8",
        )
        self.decision = self.root / "decision.json"
        self.decision.write_text(
            json.dumps(
                {
                    "schema": 3,
                    "subject_id": "CASE-1",
                    "status": "approved",
                    "decision_ref": "user-message-1",
                    "decision": "single",
                    "reason": "One outcome",
                    "shared_context": [],
                    "unknowns": [],
                    "articles": [
                        {
                            "id": "CASE-1",
                            "title": "Case",
                            "goal": "Goal",
                            "outcome": "Outcome",
                            "acceptance_boundary": "Boundary",
                            "dependencies": [],
                            "composition": "article-led",
                            "solution_boundary": solution_boundary(),
                            "architecture": {
                                "status": "not-required",
                                "triggers": [],
                                "design_ref": None,
                                "design_sha256": None,
                                "design_run_id": None,
                                "reason": "No architectural boundary changes",
                            },
                            "blocks": [
                                {"id": "B01", "title": "One"},
                                {"id": "B02", "title": "Two"},
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.plan = self.root / "execution-plan.json"
        self.plan.write_text(
            json.dumps(
                {
                    "schema": 2,
                    "subject_id": "CASE-1",
                    "status": "approved",
                    "decision_ref": "user-message-1",
                    "brief_sha256": caseflow.digest(self.brief),
                    "route": "specification",
                    "article_ids": ["CASE-1"],
                    "tasks": [
                        {
                            "id": "P1",
                            "title": "Clarify the operator's scenario workflow",
                            "output": "Reviewed article",
                            "depends_on": [],
                            "source_refs": ["SRC-1"],
                            "exit_criteria": ["Reviewed article exists"],
                            "checklist": [],
                        }
                    ],
                    "external_sync": {"status": "not_requested"},
                }
            ),
            encoding="utf-8",
        )
        legacy_init(
            argparse.Namespace(
                case_root=self.case_root,
                template=self.template,
                brief=self.brief,
                decision=self.decision,
                plan=self.plan,
                article_id="CASE-1",
            )
        )
        self.write(
            "preanalysis-lineage.json",
            json.dumps(
                {
                    "schema": 1,
                    "brief_sha256": caseflow.digest(self.brief),
                    "user_stories": [
                        {
                            "preliminary_id": "PUS-1",
                            "disposition": "confirmed",
                            "final_refs": ["US-1"],
                            "reason": "The preliminary actor outcome remains valid",
                        }
                    ],
                    "definition_of_done": [],
                }
            ),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, text: str = "ok\n") -> Path:
        path = self.case_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def submit_stage_one(self) -> None:
        self.write("method-basis/stage-01-ARTICLE.md", "# Method basis\n")
        artifact = self.write(
            "articles/stage-01.md",
            "# Whole-template baseline\n\n## US-1\n\nOperator completes the job once.\n",
        )
        caseflow.command_submit_block(
            argparse.Namespace(
                case_root=self.case_root,
                stage=1,
                block="ARTICLE",
                artifact=str(artifact),
            )
        )

    def complete_stage_one(self) -> Path:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps({"schema": 1, "stage": 1, "deferred_inputs": [], "items": []}),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        return self.case_root / "articles/stage-01.md"

    def prepare_review(self) -> str:
        article = self.write("article.md", "# Article\n")
        payload = caseflow.load_case(self.case_root)
        payload["stage"] = 4
        payload["state"] = "revmux_pending"
        payload["stages"]["4"]["state"] = "complete"
        payload["stages"]["4"]["content_ready_at"] = caseflow.now()
        payload["article"] = {
            "path": "article.md",
            "sha256": caseflow.digest(article),
            "recorded_at": caseflow.now(),
        }
        caseflow.save_case(self.case_root, payload, "test_review_setup")
        return payload["article"]["sha256"]

    def write_review_adjudication(
        self,
        receipt: Path,
        *,
        accepted: set[str],
    ) -> Path:
        review = json.loads(receipt.read_text(encoding="utf-8"))
        finding_ids = [finding["id"] for finding in review["findings"]]
        skill = self.root / "skills" / "simplicity-spec" / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        if not skill.exists():
            skill.write_text("# Simplicity spec\n", encoding="utf-8")
        return self.write(
            f"reviews/{receipt.stem}-adjudication.json",
            json.dumps(
                {
                    "schema": 1,
                    "gate": "simplicity-spec",
                    "purpose": "revmux-finding-adjudication",
                    "actor": {
                        "role": "quality-pass-reviewer",
                        "run_id": f"adjudicate-{receipt.stem}",
                    },
                    "subject": {
                        "path": str(receipt),
                        "sha256": caseflow.digest(receipt),
                    },
                    "skill": {
                        "path": str(skill),
                        "sha256": caseflow.digest(skill),
                    },
                    "outcome": "changes-required" if accepted else "clean",
                    "checks": [
                        "minimum-core",
                        "seven-step-ladder",
                        "element-classification",
                        "rewritten-result",
                    ],
                    "dismissed_findings": [
                        {
                            "id": finding_id,
                            "reason": "The reported risk is not material in the current flow",
                            "evidence": "The current requirement and reachable path do not trigger it",
                        }
                        for finding_id in finding_ids
                        if finding_id not in accepted
                    ],
                    "findings": [
                        {
                            "id": finding_id,
                            "target": f"article.md#{finding_id}",
                            "change": f"Apply the smallest correction for {finding_id}",
                            "reason": f"Finding {finding_id} is reachable and material",
                        }
                        for finding_id in finding_ids
                        if finding_id in accepted
                    ],
                }
            ),
        )

    def test_revmux_rejects_a_migrated_case_without_content_readiness(self) -> None:
        article_sha256 = self.prepare_review()
        payload = caseflow.load_case(self.case_root)
        payload["stages"]["4"].pop("content_ready_at")
        caseflow.save_case(self.case_root, payload, "test_legacy_stage_four_without_readiness")
        receipt = self.write(
            "reviews/legacy-clean.json",
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["logic"],
                        "expected": 1,
                        "reported": 1,
                        "degraded": [],
                    },
                    "findings": [],
                    "open_questions": [],
                }
            ),
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "content readiness"):
            caseflow.command_record_review(
                argparse.Namespace(case_root=self.case_root, receipt=str(receipt), diff_pool=None)
            )

    def test_stitch_requires_every_block(self) -> None:
        self.complete_stage_one()
        self.write("method-basis/stage-02-B01.md", "# Method basis\n")
        artifact = self.write("blocks/B01/stage-02.md")
        caseflow.command_submit_block(
            argparse.Namespace(case_root=self.case_root, stage=2, block="B01", artifact=str(artifact))
        )
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))

    def test_article_led_case_requires_whole_template_before_semantic_blocks(self) -> None:
        status = caseflow.command_status(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(status["stage"], 1)
        self.assertEqual(status["required_blocks"], ["ARTICLE"])
        self.write("method-basis/stage-01-B01.md", "# Wrong basis\n")
        artifact = self.write("blocks/B01/stage-01.md")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "unknown block"):
            caseflow.command_submit_block(
                argparse.Namespace(
                    case_root=self.case_root,
                    stage=1,
                    block="B01",
                    artifact=str(artifact),
                )
            )

    def test_pre_article_led_case_requires_explicit_rebaseline(self) -> None:
        payload = caseflow.load_case(self.case_root)
        payload["composition"] = "hybrid"
        caseflow.atomic_json(caseflow.manifest_path(self.case_root), payload)
        with self.assertRaisesRegex(caseflow.CaseFlowError, "legacy-case-migration"):
            caseflow.command_status(argparse.Namespace(case_root=self.case_root))

    def test_block_stage_requires_a_new_integrated_article_projection(self) -> None:
        baseline = self.complete_stage_one()
        for block in ("B01", "B02"):
            self.write(f"method-basis/stage-02-{block}.md", "# Method basis\n")
            artifact = self.write(f"blocks/{block}/stage-02.md", f"# {block} delta\n")
            caseflow.command_submit_block(
                argparse.Namespace(
                    case_root=self.case_root,
                    stage=2,
                    block=block,
                    artifact=str(artifact),
                )
            )
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-02.md")
        pool = self.write(
            "diffs/stage-02-required.json",
            json.dumps({"schema": 1, "stage": 2, "deferred_inputs": [], "items": []}),
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "requires --article"):
            caseflow.command_record_stitch(
                argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
            )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "new immutable"):
            caseflow.command_record_stitch(
                argparse.Namespace(
                    case_root=self.case_root,
                    report=str(report),
                    diff_pool=str(pool),
                    article=str(baseline),
                )
            )
        projection = self.write("articles/stage-02.md", "# Integrated stage 2\n")
        recorded = caseflow.command_record_stitch(
            argparse.Namespace(
                case_root=self.case_root,
                report=str(report),
                diff_pool=str(pool),
                article=str(projection),
            )
        )
        self.assertEqual(recorded["state"], "ready")
        advanced = caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(advanced["stage"], 3)
        payload = caseflow.load_case(self.case_root)
        self.assertEqual(payload["stages"]["2"]["article_projection"]["path"], "articles/stage-02.md")
        self.assertIn("## US-1", baseline.read_text(encoding="utf-8"))

    def test_diff_pool_blocks_advance_until_correction_is_verified(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.case_root / "diffs/stage-01-required.json"
        pool.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "stage": 1,
                    "deferred_inputs": [],
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "articles/stage-01.md",
                            "change": "Add missing boundary",
                            "reason": "B02 depends on it",
                            "status": "open",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        result = caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        self.assertEqual(result["state"], "remediation")
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        receipt = self.write("receipts/D1-001.md")
        caseflow.command_resolve(
            argparse.Namespace(case_root=self.case_root, item="D1-001", receipt=str(receipt))
        )
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        verification = self.write("receipts/D1-001-verification.md")
        caseflow.command_verify(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-001",
                receipt=str(verification),
                result="pass",
            )
        )
        artifact = self.case_root / "articles/stage-01.md"
        artifact.write_text("changed after independent verification\n", encoding="utf-8")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "changed after verification"):
            caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        artifact.write_text(
            "# Whole-template baseline\n\n## US-1\n\nOperator completes the job once.\n",
            encoding="utf-8",
        )
        advanced = caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(advanced["stage"], 2)
        self.assertEqual(advanced["state"], "blocks")

    def test_stitch_requires_an_explicit_deferred_input_register(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps({"schema": 1, "stage": 1, "items": []}),
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "declare deferred_inputs"):
            caseflow.command_record_stitch(
                argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
            )

    def test_blocking_user_decision_must_be_answered_and_verified(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 1,
                    "deferred_inputs": [],
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "articles/stage-01.md",
                            "change": "Record the chosen product boundary",
                            "reason": "The scope cannot be completed without the choice",
                            "status": "open",
                            "input": {
                                "id": "U-001",
                                "disposition": "user-decision",
                                "question": "Which product boundary should the specification use?",
                            },
                        }
                    ],
                }
            ),
        )
        result = caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        self.assertEqual(result["state"], "remediation")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "cannot be waived"):
            caseflow.command_waive(
                argparse.Namespace(
                    case_root=self.case_root,
                    item="D1-001",
                    decision_ref="skip-the-question",
                )
            )
        artifact = self.write("articles/stage-01.md", "Chosen boundary\n")
        caseflow.command_resolve(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-001",
                receipt=str(self.write("receipts/D1-001-decision.md")),
            )
        )
        caseflow.command_verify(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-001",
                receipt=str(self.write("receipts/D1-001-decision-check.md")),
                result="pass",
            )
        )
        advanced = caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(advanced["stage"], 2)
        recorded = caseflow.load_case(self.case_root)["stages"]["1"]["submissions"]["ARTICLE"]
        self.assertEqual(caseflow.digest(artifact), recorded["sha256"])

    def test_implementation_only_input_can_be_explicitly_deferred(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 1,
                    "deferred_inputs": [
                        {
                            "id": "U-IMPL-001",
                            "statement": "Internal helper name is not selected",
                            "disposition": "implementation-only",
                            "reason": "It changes neither observable behavior nor acceptance",
                        }
                    ],
                    "items": [],
                }
            ),
        )
        result = caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        self.assertEqual(result["state"], "ready")
        status = caseflow.command_status(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(status["blocking_inputs"], 0)
        self.assertEqual(status["deferred_inputs"], 1)

    def test_registered_diff_pool_accepts_only_valid_appended_items(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps({"schema": 1, "stage": 1, "deferred_inputs": [], "items": []}),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        item_file = self.write(
            "diffs/new-item.json",
            json.dumps(
                {
                    "id": "D1-002",
                    "target": "articles/stage-01.md",
                    "change": "Add the newly found dependency",
                    "reason": "Found during correction",
                    "status": "open",
                }
            ),
        )
        appended = caseflow.command_append_item(
            argparse.Namespace(case_root=self.case_root, item_file=str(item_file))
        )
        self.assertEqual(appended["state"], "remediation")
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_append_item(
                argparse.Namespace(case_root=self.case_root, item_file=str(item_file))
            )

    def test_stage_output_rebind_requires_verified_target_and_then_freezes(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 1,
                    "deferred_inputs": [],
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "articles/stage-01.md#boundary",
                            "change": "Correct the boundary",
                            "reason": "Stitch found a contradiction",
                            "status": "open",
                        }
                    ],
                }
            ),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        artifact = self.write("articles/stage-01.md", "corrected\n")
        correction = self.write("receipts/D1-001.md")
        caseflow.command_resolve(
            argparse.Namespace(case_root=self.case_root, item="D1-001", receipt=str(correction))
        )
        verification = self.write("receipts/D1-001-verification.md")
        caseflow.command_verify(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-001",
                receipt=str(verification),
                result="pass",
            )
        )
        advanced = caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(advanced["rebound"], ["articles/stage-01.md"])
        artifact.write_text("drift after close\n", encoding="utf-8")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "changed after registration"):
            caseflow.command_status(argparse.Namespace(case_root=self.case_root))

    def test_shared_target_uses_the_last_closed_diff_item(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 1,
                    "deferred_inputs": [],
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "articles/stage-01.md",
                            "change": "Apply the final boundary correction",
                            "reason": "Second correction to the same artifact",
                            "status": "open",
                        },
                        {
                            "id": "D1-002",
                            "target": "articles/stage-01.md",
                            "change": "Apply the initial boundary correction",
                            "reason": "First correction to the same artifact",
                            "status": "open",
                        },
                    ],
                }
            ),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        artifact = self.write("articles/stage-01.md", "initial correction\n")
        first_receipt = self.write("receipts/D1-002.md")
        caseflow.command_resolve(
            argparse.Namespace(case_root=self.case_root, item="D1-002", receipt=str(first_receipt))
        )
        first_verification = self.write("receipts/D1-002-verification.md")
        caseflow.command_verify(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-002",
                receipt=str(first_verification),
                result="pass",
            )
        )
        artifact.write_text("final correction\n", encoding="utf-8")
        final_receipt = self.write("receipts/D1-001.md")
        caseflow.command_resolve(
            argparse.Namespace(case_root=self.case_root, item="D1-001", receipt=str(final_receipt))
        )
        final_verification = self.write("receipts/D1-001-verification.md")
        caseflow.command_verify(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-001",
                receipt=str(final_verification),
                result="pass",
            )
        )
        advanced = caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(advanced["rebound"], ["articles/stage-01.md"])
        self.assertEqual(advanced["stage"], 2)

    def test_unpooled_stage_output_drift_blocks_advance(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps({"schema": 1, "stage": 1, "deferred_inputs": [], "items": []}),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        self.write("articles/stage-01.md", "unregistered change\n")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "outside a closed diff item"):
            caseflow.command_advance(argparse.Namespace(case_root=self.case_root))

    def test_failed_correction_can_be_waived_without_wedging_advance(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 1,
                    "deferred_inputs": [],
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "articles/stage-01.md",
                            "change": "Try the proposed correction",
                            "reason": "Stitch finding",
                            "status": "open",
                        }
                    ],
                }
            ),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        artifact = self.write("articles/stage-01.md", "rejected correction\n")
        correction = self.write("receipts/D1-001.md")
        caseflow.command_resolve(
            argparse.Namespace(case_root=self.case_root, item="D1-001", receipt=str(correction))
        )
        failed = self.write("receipts/D1-001-failed.md")
        caseflow.command_verify(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-001",
                receipt=str(failed),
                result="fail",
            )
        )
        caseflow.command_waive(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-001",
                decision_ref="user-message-77",
            )
        )
        artifact.write_text("changed after waiver\n", encoding="utf-8")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "changed after verification or waiver"):
            caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        artifact.write_text("rejected correction\n", encoding="utf-8")
        advanced = caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(advanced["stage"], 2)

    def test_method_basis_can_be_corrected_through_registered_diff(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 1,
                    "deferred_inputs": [],
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "method-basis/stage-01-ARTICLE.md",
                            "change": "Select the corrected method route",
                            "reason": "Initial route did not cover the assigned surface",
                            "status": "open",
                        }
                    ],
                }
            ),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        basis = self.write("method-basis/stage-01-ARTICLE.md", "# Corrected method basis\n")
        correction = self.write("receipts/D1-001.md")
        caseflow.command_resolve(
            argparse.Namespace(case_root=self.case_root, item="D1-001", receipt=str(correction))
        )
        verification = self.write("receipts/D1-001-verification.md")
        caseflow.command_verify(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-001",
                receipt=str(verification),
                result="pass",
            )
        )
        advanced = caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        self.assertIn("method-basis/stage-01-ARTICLE.md", advanced["rebound"])
        basis.write_text("# Drift after close\n", encoding="utf-8")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "method basis changed"):
            caseflow.command_status(argparse.Namespace(case_root=self.case_root))

    def test_failed_verification_reopens_same_diff_item(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.case_root / "diffs/stage-01-required.json"
        pool.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "stage": 1,
                    "deferred_inputs": [],
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "articles/stage-01.md",
                            "change": "Add missing boundary",
                            "reason": "B02 depends on it",
                            "status": "open",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        first_fix = self.write("receipts/D1-001-first.md")
        caseflow.command_resolve(
            argparse.Namespace(case_root=self.case_root, item="D1-001", receipt=str(first_fix))
        )
        failed_check = self.write("receipts/D1-001-failed-check.md")
        reopened = caseflow.command_verify(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-001",
                receipt=str(failed_check),
                result="fail",
            )
        )
        self.assertEqual(reopened["status"], "open")
        second_fix = self.write("receipts/D1-001-second.md")
        caseflow.command_resolve(
            argparse.Namespace(case_root=self.case_root, item="D1-001", receipt=str(second_fix))
        )
        passed_check = self.write("receipts/D1-001-passed-check.md")
        caseflow.command_verify(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-001",
                receipt=str(passed_check),
                result="pass",
            )
        )
        saved = json.loads(pool.read_text(encoding="utf-8"))["items"][0]
        self.assertEqual(saved["status"], "verified")
        self.assertEqual(len(saved["correction_attempts"]), 2)
        self.assertEqual(len(saved["verification_attempts"]), 2)

    def test_revmux_degraded_cannot_close_article(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.root / "revmux.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["source-1"],
                        "expected": 2,
                        "reported": 1,
                        "degraded": ["docs"],
                    },
                    "findings": [],
                    "open_questions": [],
                }
            ),
            encoding="utf-8",
        )
        result = caseflow.command_record_review(
            argparse.Namespace(case_root=self.case_root, receipt=str(receipt))
        )
        self.assertEqual(result["state"], "revmux_pending")

    def test_revmux_five_round_cap_requires_explicit_user_decision(self) -> None:
        article_sha256 = self.prepare_review()
        degraded_receipt = self.root / "revmux-degraded-retry.json"
        degraded_receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["source-1"],
                        "expected": 2,
                        "reported": 1,
                        "degraded": ["adversarial"],
                    },
                    "findings": [],
                    "open_questions": [],
                }
            ),
            encoding="utf-8",
        )
        caseflow.command_record_review(
            argparse.Namespace(case_root=self.case_root, receipt=str(degraded_receipt))
        )

        for index in range(1, 6):
            payload = caseflow.load_case(self.case_root)
            payload["state"] = "revmux_pending"
            caseflow.save_case(self.case_root, payload, f"prepare_review_round_{index}")
            receipt = self.root / f"revmux-clean-{index}.json"
            receipt.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "article_sha256": article_sha256,
                        "sources": {
                            "ids": ["source-1", "source-2"],
                            "expected": 2,
                            "reported": 2,
                            "degraded": [],
                        },
                        "findings": [],
                        "open_questions": [],
                    }
                ),
                encoding="utf-8",
            )
            caseflow.command_record_review(
                argparse.Namespace(case_root=self.case_root, receipt=str(receipt))
            )

        status = caseflow.command_status(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(status["review_cycles_used"], 5)
        self.assertEqual(status["review_cycles_remaining"], 0)

        payload = caseflow.load_case(self.case_root)
        payload["state"] = "revmux_pending"
        caseflow.save_case(self.case_root, payload, "prepare_review_round_6")
        retry = caseflow.command_record_review(
            argparse.Namespace(case_root=self.case_root, receipt=str(degraded_receipt))
        )
        self.assertEqual(retry["review_cycles_used"], 5)
        self.assertEqual(retry["state"], "revmux_pending")
        receipt = self.root / "revmux-clean-6.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["source-1", "source-2"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [],
                    "open_questions": [],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "review cycle cap reached"):
            caseflow.command_record_review(
                argparse.Namespace(case_root=self.case_root, receipt=str(receipt))
            )

        recorded = caseflow.command_record_review(
            argparse.Namespace(
                case_root=self.case_root,
                receipt=str(receipt),
                cap_decision_ref="user-message-override",
            )
        )
        self.assertEqual(recorded["review_cycles_used"], 6)
        self.assertEqual(recorded["review_cycles_remaining"], 0)

    def test_revmux_gating_findings_require_closed_round_diff(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.root / "revmux-major.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["source-1", "source-2"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [
                        {"id": "f1", "severity": "major", "sources": ["source-1"]}
                    ],
                    "open_questions": [],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "adjudication-report"):
            caseflow.command_record_review(
                argparse.Namespace(case_root=self.case_root, receipt=str(receipt), diff_pool=None)
            )
        adjudication = self.write_review_adjudication(receipt, accepted={"f1"})
        with self.assertRaisesRegex(caseflow.CaseFlowError, "accepted revmux findings"):
            caseflow.command_record_review(
                argparse.Namespace(
                    case_root=self.case_root,
                    receipt=str(receipt),
                    adjudication_report=str(adjudication),
                    diff_pool=None,
                )
            )
        pool = self.write(
            "article-diffs/round-01.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 4,
                    "items": [
                        {
                            "id": "D4-001",
                            "source_finding_id": "f1",
                            "target": "article.md#section",
                            "change": "Fix the confirmed contradiction",
                            "reason": "revmux finding f1",
                            "status": "open",
                        }
                    ],
                }
            ),
        )
        recorded = caseflow.command_record_review(
            argparse.Namespace(
                case_root=self.case_root,
                receipt=str(receipt),
                adjudication_report=str(adjudication),
                diff_pool=str(pool),
            )
        )
        self.assertEqual(recorded["state"], "revmux_remediation")
        article = self.write("article.md", "# Fixed article\n")
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_article_updated(
                argparse.Namespace(case_root=self.case_root, article=str(article))
            )
        correction = self.write("receipts/D4-001.md")
        caseflow.command_resolve_review(
            argparse.Namespace(case_root=self.case_root, item="D4-001", receipt=str(correction))
        )
        verification = self.write("receipts/D4-001-verification.md")
        caseflow.command_verify_review(
            argparse.Namespace(
                case_root=self.case_root,
                item="D4-001",
                receipt=str(verification),
                result="pass",
            )
        )
        article.write_text("# Changed after review verification\n", encoding="utf-8")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "changed after verification"):
            caseflow.command_article_updated(
                argparse.Namespace(case_root=self.case_root, article=str(article))
            )
        article.write_text("# Fixed article\n", encoding="utf-8")
        alternate = self.write("article-renamed.md", "# Fixed article\n")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "cannot change the registered article path"):
            caseflow.command_article_updated(
                argparse.Namespace(case_root=self.case_root, article=str(alternate))
            )
        updated = caseflow.command_article_updated(
            argparse.Namespace(case_root=self.case_root, article=str(article))
        )
        self.assertEqual(updated["state"], "revmux_pending")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "cannot change the registered article path"):
            caseflow.command_article_updated(
                argparse.Namespace(case_root=self.case_root, article=str(alternate))
            )

    def test_registered_review_pool_accepts_new_item(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.root / "review-with-finding.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["source-1", "source-2"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [
                        {"id": "f1", "severity": "major", "sources": ["source-1"]}
                    ],
                    "open_questions": [],
                }
            ),
            encoding="utf-8",
        )
        pool = self.write(
            "article-diffs/round-append.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 4,
                    "items": [
                        {
                            "id": "D4-001",
                            "source_finding_id": "f1",
                            "target": "article.md#one",
                            "change": "Fix the gating finding",
                            "reason": "revmux finding f1",
                            "status": "open",
                        }
                    ],
                }
            ),
        )
        adjudication = self.write_review_adjudication(receipt, accepted={"f1"})
        caseflow.command_record_review(
            argparse.Namespace(
                case_root=self.case_root,
                receipt=str(receipt),
                adjudication_report=str(adjudication),
                diff_pool=str(pool),
            )
        )
        item = self.write(
            "article-diffs/new-item.json",
            json.dumps(
                {
                    "id": "D4-002",
                    "target": "article.md#two",
                    "change": "Fix the defect discovered during correction",
                    "reason": "Correction exposed a second contradiction",
                    "status": "open",
                }
            ),
        )
        appended = caseflow.command_append_review_item(
            argparse.Namespace(case_root=self.case_root, item_file=str(item))
        )
        self.assertEqual(appended["state"], "revmux_remediation")

    def test_revmux_simplicity_adjudication_can_dismiss_model_paranoia(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.write(
            "reviews/speculative-major.json",
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["source-1", "source-2"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [
                        {"id": "f-paranoia", "severity": "major", "sources": ["source-1"]}
                    ],
                    "open_questions": [],
                }
            ),
        )
        adjudication = self.write_review_adjudication(receipt, accepted=set())

        recorded = caseflow.command_record_review(
            argparse.Namespace(
                case_root=self.case_root,
                receipt=str(receipt),
                adjudication_report=str(adjudication),
                diff_pool=None,
            )
        )

        self.assertEqual(recorded["state"], "spec_ready")
        self.assertEqual(recorded["accepted_finding_ids"], [])
        self.assertEqual(recorded["dismissed_finding_ids"], ["f-paranoia"])

    def test_minor_pause_requires_user_disposition_and_cannot_route(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.write("minor-receipt.json", json.dumps({
            "schema": 1, "article_sha256": article_sha256,
            "sources": {"ids": ["reader"], "expected": 1, "reported": 1, "degraded": []},
            "findings": [{"id": "m1", "severity": "minor", "sources": ["reader"]}],
            "open_questions": [],
        }))
        adjudication = self.write_review_adjudication(receipt, accepted={"m1"})
        result = caseflow.command_record_review(argparse.Namespace(
            case_root=self.case_root, receipt=str(receipt),
            adjudication_report=str(adjudication), stop_at_minor=True,
        ))
        self.assertEqual(result["state"], "revmux_minor_pending")
        self.assertEqual(result["accepted_finding_ids"], ["m1"])
        self.assertEqual(result["review_cycles_used"], 1)
        status = caseflow.command_status(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(status["state"], "revmux_minor_pending")
        self.assertEqual(status["review_cycles_used"], 1)
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_article_updated(argparse.Namespace(case_root=self.case_root))
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_route(argparse.Namespace(
                case_root=self.case_root, decision="stop",
            ))
        with self.assertRaisesRegex(caseflow.CaseFlowError, "exact review diff pool"):
            caseflow.command_record_review_decisions(argparse.Namespace(
                case_root=self.case_root, decision_ref="user-1", diff_pool=None,
            ))
        pool = self.write("minor-pool.json", json.dumps({
            "schema": 1, "stage": 4, "items": [{
                "id": "D4-001", "source_finding_id": "m1", "target": "article.md",
                "change": "Clarify the label", "reason": "m1", "status": "open",
            }],
        }))
        resumed = caseflow.command_record_review_decisions(argparse.Namespace(
            case_root=self.case_root, decision_ref="user-1", diff_pool=str(pool),
        ))
        self.assertEqual(resumed["state"], "revmux_remediation")

    def test_minor_pause_rejects_major_findings(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.write("major-receipt.json", json.dumps({
            "schema": 1, "article_sha256": article_sha256,
            "sources": {"ids": ["reader"], "expected": 1, "reported": 1, "degraded": []},
            "findings": [{"id": "m1", "severity": "major", "sources": ["reader"]}],
            "open_questions": [],
        }))
        adjudication = self.write_review_adjudication(receipt, accepted={"m1"})
        with self.assertRaisesRegex(caseflow.CaseFlowError, "only accepted minor"):
            caseflow.command_record_review(argparse.Namespace(
                case_root=self.case_root, receipt=str(receipt),
                adjudication_report=str(adjudication), stop_at_minor=True,
            ))

    def test_revmux_recheck_keeps_sources_that_raised_accepted_findings(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.write(
            "reviews/round-01.json",
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["logic", "reader"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [
                        {
                            "id": "reader-1",
                            "severity": "minor",
                            "sources": ["reader"],
                        }
                    ],
                    "open_questions": [],
                }
            ),
        )
        pool = self.write(
            "article-diffs/round-source-continuity.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 4,
                    "items": [
                        {
                            "id": "D4-001",
                            "source_finding_id": "reader-1",
                            "target": "article.md#reader",
                            "change": "Rewrite the unreadable passage",
                            "reason": "reader-1",
                            "status": "open",
                        }
                    ],
                }
            ),
        )
        adjudication = self.write_review_adjudication(receipt, accepted={"reader-1"})
        caseflow.command_record_review(
            argparse.Namespace(
                case_root=self.case_root,
                receipt=str(receipt),
                adjudication_report=str(adjudication),
                diff_pool=str(pool),
            )
        )
        article = self.write("article.md", "# Readable article\n")
        caseflow.command_resolve_review(
            argparse.Namespace(
                case_root=self.case_root,
                item="D4-001",
                receipt=str(self.write("receipts/D4-001-source-continuity.md")),
            )
        )
        caseflow.command_verify_review(
            argparse.Namespace(
                case_root=self.case_root,
                item="D4-001",
                receipt=str(self.write("receipts/D4-001-source-continuity-verification.md")),
                result="pass",
            )
        )
        updated = caseflow.command_article_updated(
            argparse.Namespace(case_root=self.case_root, article=str(article))
        )
        narrowed = self.write(
            "reviews/round-02-narrowed.json",
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": updated["article"]["sha256"],
                    "sources": {
                        "ids": ["logic"],
                        "expected": 1,
                        "reported": 1,
                        "degraded": [],
                    },
                    "findings": [],
                    "open_questions": [],
                }
            ),
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "without sources: reader"):
            caseflow.command_record_review(
                argparse.Namespace(case_root=self.case_root, receipt=str(narrowed), diff_pool=None)
            )

        complete = self.write(
            "reviews/round-02-complete.json",
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": updated["article"]["sha256"],
                    "sources": {
                        "ids": ["logic", "reader"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [],
                    "open_questions": [],
                }
            ),
        )
        result = caseflow.command_record_review(
            argparse.Namespace(case_root=self.case_root, receipt=str(complete), diff_pool=None)
        )
        self.assertEqual(result["state"], "spec_ready")
        self.assertEqual(result["required_source_ids"], ["reader"])

    def test_revmux_open_question_blocks_spec_ready_until_decided(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.root / "revmux-question.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["source-1", "source-2"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [],
                    "open_questions": [{"id": "q1", "body": "Which owner is canonical?"}],
                }
            ),
            encoding="utf-8",
        )
        result = caseflow.command_record_review(
            argparse.Namespace(case_root=self.case_root, receipt=str(receipt), diff_pool=None)
        )
        self.assertEqual(result["state"], "revmux_decision_pending")
        decided = caseflow.command_record_review_decisions(
            argparse.Namespace(
                case_root=self.case_root,
                decision_ref="user-message-42",
                diff_pool=None,
            )
        )
        self.assertEqual(decided["state"], "revmux_pending")

    def test_template_drift_fails_every_case_command_closed(self) -> None:
        self.template.write_text("# Changed template\n", encoding="utf-8")
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_status(argparse.Namespace(case_root=self.case_root))

    def test_init_requires_matching_approved_execution_plan(self) -> None:
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        plan["decision_ref"] = "another-decision"
        mismatched = self.root / "mismatched-plan.json"
        mismatched.write_text(json.dumps(plan), encoding="utf-8")
        with self.assertRaises(caseflow.CaseFlowError):
            legacy_init(
                argparse.Namespace(
                    case_root=self.root / "second-case",
                    template=self.template,
                    brief=self.brief,
                    decision=self.decision,
                    plan=mismatched,
                    article_id="CASE-1",
                )
            )

    def test_initial_diff_pool_cannot_arrive_closed(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 1,
                    "deferred_inputs": [],
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "x",
                            "change": "y",
                            "reason": "z",
                            "status": "verified",
                            "receipt": "fabricated",
                            "verification_receipt": "fabricated",
                        }
                    ],
                }
            ),
        )
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_record_stitch(
                argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
            )

    def test_revmux_receipt_requires_schema_sources_and_current_article_sha(self) -> None:
        article_sha256 = self.prepare_review()
        malformed = self.root / "malformed-review.json"
        malformed.write_text(json.dumps({"schema": 1, "findings": []}), encoding="utf-8")
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_record_review(
                argparse.Namespace(case_root=self.case_root, receipt=str(malformed), diff_pool=None)
            )
        wrong_article = self.root / "wrong-article-review.json"
        wrong_article.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": "0" * len(article_sha256),
                    "sources": {
                        "ids": ["source-1", "source-2"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [],
                    "open_questions": [],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_record_review(
                argparse.Namespace(case_root=self.case_root, receipt=str(wrong_article), diff_pool=None)
            )

    def test_revmux_receipt_rejects_duplicate_ids(self) -> None:
        article_sha256 = self.prepare_review()
        duplicate = self.root / "duplicate-review.json"
        duplicate.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["source-1", "source-2"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [
                        {"id": "same", "severity": "minor", "sources": ["source-1"]},
                        {"id": "same", "severity": "major", "sources": ["source-2"]},
                    ],
                    "open_questions": [],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "duplicate revmux finding id"):
            caseflow.command_record_review(
                argparse.Namespace(case_root=self.case_root, receipt=str(duplicate), diff_pool=None)
            )

    def test_article_can_be_rebound_before_review_and_freezes_after_clean_receipt(self) -> None:
        self.prepare_review()
        article = self.write("article.md", "# Deterministically corrected article\n")
        updated = caseflow.command_article_updated(
            argparse.Namespace(case_root=self.case_root, article=str(article))
        )
        receipt = self.root / "clean-review.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": updated["article"]["sha256"],
                    "sources": {
                        "ids": ["source-1", "source-2"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [],
                    "open_questions": [],
                }
            ),
            encoding="utf-8",
        )
        result = caseflow.command_record_review(
            argparse.Namespace(case_root=self.case_root, receipt=str(receipt), diff_pool=None)
        )
        self.assertEqual(result["state"], "spec_ready")
        article.write_text("# Unreviewed drift\n", encoding="utf-8")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "final reviewed article changed"):
            caseflow.command_status(argparse.Namespace(case_root=self.case_root))

    def test_revmux_gating_and_question_flow_through_decision_state(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.root / "combined-review.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {
                        "ids": ["source-1", "source-2"],
                        "expected": 2,
                        "reported": 2,
                        "degraded": [],
                    },
                    "findings": [
                        {"id": "f1", "severity": "major", "sources": ["source-1"]}
                    ],
                    "open_questions": [{"id": "q1", "body": "Choose a boundary"}],
                }
            ),
            encoding="utf-8",
        )
        recorded = caseflow.command_record_review(
            argparse.Namespace(
                case_root=self.case_root,
                receipt=str(receipt),
                adjudication_report=str(
                    self.write_review_adjudication(receipt, accepted={"f1"})
                ),
                diff_pool=None,
            )
        )
        self.assertEqual(recorded["state"], "revmux_decision_pending")
        pool = self.write(
            "article-diffs/combined.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 4,
                    "items": [
                        {
                            "id": "D4-001",
                            "source_finding_id": "f1",
                            "target": "article.md",
                            "change": "Fix gating issue",
                            "reason": "finding f1",
                            "status": "open",
                        }
                    ],
                }
            ),
        )
        decided = caseflow.command_record_review_decisions(
            argparse.Namespace(
                case_root=self.case_root,
                decision_ref="user-message-99",
                diff_pool=str(pool),
            )
        )
        self.assertEqual(decided["state"], "revmux_remediation")

    def test_context_uses_recorded_submission_path(self) -> None:
        baseline = self.complete_stage_one()
        context = caseflow.command_context(
            argparse.Namespace(case_root=self.case_root, block="B01")
        )
        self.assertIn(str(baseline.resolve()), context["read_set"])
        self.assertNotIn(
            str((self.case_root / "blocks/B02/stage-02.md").resolve()),
            context["read_set"],
        )

    def test_stage_one_context_keeps_the_bound_preanalysis_brief(self) -> None:
        context = caseflow.command_context(
            argparse.Namespace(case_root=self.case_root, block="ARTICLE", lane=None)
        )
        self.assertIn(str(self.brief.resolve()), context["read_set"])

    def test_stage_one_stitch_requires_complete_preanalysis_lineage(self) -> None:
        (self.case_root / "preanalysis-lineage.json").unlink()
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps({"schema": 1, "stage": 1, "deferred_inputs": [], "items": []}),
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "missing file"):
            caseflow.command_record_stitch(
                argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
            )

    def test_preanalysis_lineage_accounts_for_every_preliminary_item_once(self) -> None:
        brief = json.loads(self.brief.read_text(encoding="utf-8"))
        brief["preliminary_user_stories"] = [{"id": "PUS-1"}]
        lineage = {
            "schema": 1,
            "brief_sha256": "b" * 64,
            "user_stories": [],
            "definition_of_done": [],
        }
        with self.assertRaisesRegex(caseflow.CaseFlowError, r"missing=\['PUS-1'\]"):
            caseflow.validate_preanalysis_lineage(lineage, brief, "b" * 64)

    def test_architecture_report_binds_design_and_article_bytes(self) -> None:
        article = self.write("articles/architecture-subject.md", "# Article\n")
        report = self.write(
            "architecture/conformance.json",
            json.dumps(
                {
                    "schema": 1,
                    "mode": "conformance",
                    "actor": {"role": "spec-solution-architect", "run_id": "arch-run-1"},
                    "subject": {
                        "path": "articles/architecture-subject.md",
                        "sha256": caseflow.digest(article),
                    },
                    "design_sha256": "a" * 64,
                    "status": "conform",
                    "findings": [],
                }
            ),
        )
        validated, _ = caseflow.validate_architecture_report(
            self.case_root,
            report,
            article,
            {"design_sha256": "a" * 64, "design_run_id": "design-run-1"},
        )
        self.assertEqual(validated["status"], "conform")

    def test_architecture_design_binds_the_assigned_run_and_triggers(self) -> None:
        design = self.write(
            "architecture/design.json",
            json.dumps(
                {
                    "schema": 1,
                    "mode": "design",
                    "actor": {"role": "spec-solution-architect", "run_id": "design-run-1"},
                    "status": "designed",
                    "triggers": ["component-boundary"],
                    "decisions": [
                        {
                            "id": "AD-1",
                            "surface": "component-boundary",
                            "decision": "Keep one owner",
                            "reason": "The existing component owns the invariant",
                        }
                    ],
                    "gaps": [],
                }
            ),
        )
        validated = caseflow.validate_architecture_design(
            design,
            {"design_run_id": "design-run-1", "triggers": ["component-boundary"]},
        )
        self.assertEqual(validated["status"], "designed")

    def test_solution_boundary_survives_case_initialization_and_context(self) -> None:
        boundary = solution_boundary()
        decision_payload = json.loads(self.decision.read_text(encoding="utf-8"))
        decision_payload["schema"] = 3
        decision_payload["articles"][0]["solution_boundary"] = boundary
        decision_path = self.root / "decision-v2.json"
        decision_path.write_text(json.dumps(decision_payload), encoding="utf-8")
        case_root = self.root / "case-v2"

        initialized = legacy_init(
            argparse.Namespace(
                case_root=case_root,
                template=self.template,
                brief=self.brief,
                decision=decision_path,
                plan=self.plan,
                article_id="CASE-1",
            )
        )

        self.assertEqual(initialized["solution_boundary"], boundary)
        status = caseflow.command_status(argparse.Namespace(case_root=case_root))
        self.assertEqual(status["solution_horizon"], "bounded-systemic")
        context = caseflow.command_context(
            argparse.Namespace(case_root=case_root, block=None, lane=None)
        )
        self.assertEqual(context["solution_boundary"], boundary)

    def test_delivery_has_machine_backed_stage_transitions(self) -> None:
        payload = caseflow.load_case(self.case_root)
        payload["solution_boundary"] = solution_boundary()
        payload["stage"] = 4
        payload["state"] = "spec_ready"
        article = self.write("article.md", "# Reviewed article\n")
        payload["article"] = {
            "path": "article.md",
            "sha256": caseflow.digest(article),
            "recorded_at": caseflow.now(),
        }
        caseflow.save_case(self.case_root, payload, "test_spec_ready")
        routed = caseflow.command_route(
            argparse.Namespace(
                case_root=self.case_root,
                decision="delivery",
                lane=["BACKEND", "TEST"],
            )
        )
        self.assertEqual(routed["delivery"]["stage"], 1)
        for lane in ("BACKEND", "TEST"):
            artifact = self.write(f"delivery/stage-01-{lane}.md")
            basis = self.write(f"delivery/method-{lane}.md")
            caseflow.command_delivery_submit(
                argparse.Namespace(
                    case_root=self.case_root,
                    stage=1,
                    lane=lane,
                    artifact=str(artifact),
                    method_basis=str(basis),
                )
            )
        caseflow.command_delivery_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("delivery/stitch-01.md")
        pool = self.write(
            "delivery/diff-01.json",
            json.dumps({"schema": 1, "stage": 1, "items": []}),
        )
        caseflow.command_delivery_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        advanced = caseflow.command_delivery_advance(
            argparse.Namespace(case_root=self.case_root)
        )
        self.assertEqual(advanced["delivery_stage"], 2)
        status = caseflow.command_status(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(status["delivery_state"], "lanes")
        context = caseflow.command_context(
            argparse.Namespace(case_root=self.case_root, block=None, lane="BACKEND")
        )
        self.assertEqual(context["mode"], "delivery")
        self.assertEqual(context["delivery_stage"], 2)
        self.assertEqual(context["solution_boundary"]["horizon"], "bounded-systemic")
        self.assertIn(str(article.resolve()), context["read_set"])
        self.assertIn(
            str((self.case_root / "delivery/stage-01-BACKEND.md").resolve()),
            context["read_set"],
        )
        self.assertNotIn(
            str((self.case_root / "blocks/B01/stage-01.md").resolve()),
            context["read_set"],
        )

    def test_stage_four_projection_can_share_the_mutable_review_article_path(self) -> None:
        article_case = self.root / "article-led-case"
        decision_payload = json.loads(self.decision.read_text(encoding="utf-8"))
        decision = self.root / "article-led-decision.json"
        decision.write_text(json.dumps(decision_payload), encoding="utf-8")
        initialized = legacy_init(
            argparse.Namespace(
                case_root=article_case,
                template=self.template,
                brief=self.brief,
                decision=decision,
                plan=self.plan,
                article_id="CASE-1",
            )
        )
        self.assertEqual(initialized["stage"], 1)

        def write(relative: str, text: str = "ok\n") -> Path:
            path = article_case / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            return path

        payload = caseflow.load_case(article_case)
        for stage in (1, 2, 3):
            projection = write(f"articles/stage-{stage:02d}.md", f"# Stage {stage}\n")
            payload["stages"][str(stage)]["state"] = "complete"
            payload["stages"][str(stage)]["article_projection"] = {
                "path": f"articles/stage-{stage:02d}.md",
                "sha256": caseflow.digest(projection),
                "recorded_at": caseflow.now(),
            }
        payload["stage"] = 4
        payload["state"] = "blocks"
        payload["stages"]["4"]["state"] = "blocks"
        caseflow.save_case(article_case, payload, "test_stage_four_setup")

        write("method-basis/stage-04-ARTICLE.md", "# Method basis\n")
        article = write("article.md", "# Initial article\n")
        caseflow.command_submit_block(
            argparse.Namespace(
                case_root=article_case,
                stage=4,
                block="ARTICLE",
                artifact=str(article),
            )
        )
        caseflow.command_open_stitch(argparse.Namespace(case_root=article_case))
        report = write("stitches/stage-04.md")
        pool = write(
            "diffs/stage-04-required.json",
            json.dumps({"schema": 1, "stage": 4, "deferred_inputs": [], "items": []}),
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "requires simplicity-spec"):
            caseflow.command_record_stitch(
                argparse.Namespace(case_root=article_case, report=str(report), diff_pool=str(pool))
            )
        simplicity_skill = write("quality/simplicity-spec/SKILL.md")
        humanizer_skill = write("quality/humanizer/SKILL.md")
        style_profile = write("quality/svs-work.md")
        label_only = write(
            "quality/label-only.json",
            json.dumps({"schema": 1, "gate": "simplicity-spec", "outcome": "clean"}),
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "assigned role/run_id"):
            caseflow.validate_quality_pass(article_case, label_only, "simplicity-spec")
        subject = {"path": "article.md", "sha256": caseflow.digest(article)}
        simplicity_report = write(
            "quality/simplicity-spec.json",
            json.dumps(
                {
                    "schema": 1,
                    "gate": "simplicity-spec",
                    "actor": {"role": "quality-pass-reviewer", "run_id": "simplicity-run"},
                    "subject": subject,
                    "skill": {
                        "path": str(simplicity_skill),
                        "sha256": caseflow.digest(simplicity_skill),
                    },
                    "outcome": "clean",
                    "checks": [
                        "minimum-core",
                        "seven-step-ladder",
                        "element-classification",
                        "rewritten-result",
                    ],
                    "findings": [],
                }
            ),
        )
        humanizer_report = write(
            "quality/humanizer.json",
            json.dumps(
                {
                    "schema": 1,
                    "gate": "humanizer",
                    "actor": {"role": "quality-pass-reviewer", "run_id": "reader-run"},
                    "subject": subject,
                    "skill": {
                        "path": str(humanizer_skill),
                        "sha256": caseflow.digest(humanizer_skill),
                    },
                    "style_profile": {
                        "path": str(style_profile),
                        "sha256": caseflow.digest(style_profile),
                    },
                    "outcome": "clean",
                    "checks": ["draft-rewrite", "anti-ai-audit", "final-rewrite"],
                    "findings": [],
                }
            ),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(
                case_root=article_case,
                report=str(report),
                diff_pool=str(pool),
                simplicity_report=str(simplicity_report),
                humanizer_report=str(humanizer_report),
            )
        )
        caseflow.command_advance(argparse.Namespace(case_root=article_case))
        self.assertTrue(
            caseflow.command_status(argparse.Namespace(case_root=article_case))[
                "content_ready_for_review"
            ]
        )
        caseflow.command_finalize_article(
            argparse.Namespace(case_root=article_case, article=str(article))
        )
        article.write_text("# Deterministic check correction\n", encoding="utf-8")
        updated = caseflow.command_article_updated(
            argparse.Namespace(case_root=article_case, article=str(article))
        )
        receipt = write(
            "review-round-1.json",
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": updated["article"]["sha256"],
                    "sources": {
                        "ids": ["source-1"],
                        "expected": 1,
                        "reported": 1,
                        "degraded": [],
                    },
                    "findings": [
                        {"id": "f1", "severity": "major", "sources": ["source-1"]}
                    ],
                    "open_questions": [],
                }
            ),
        )
        pool = write(
            "article-diffs/round-1.json",
            json.dumps(
                {
                    "schema": 1,
                    "stage": 4,
                    "items": [
                        {
                            "id": "D4-001",
                            "source_finding_id": "f1",
                            "target": "article.md#finding",
                            "change": "Correct the review finding",
                            "reason": "revmux finding f1",
                            "status": "open",
                        }
                    ],
                }
            ),
        )
        caseflow.command_record_review(
            argparse.Namespace(
                case_root=article_case,
                receipt=str(receipt),
                adjudication_report=str(
                    self.write_review_adjudication(receipt, accepted={"f1"})
                ),
                diff_pool=str(pool),
            )
        )
        article.write_text("# Review correction\n", encoding="utf-8")
        correction = write("receipts/D4-001.md")
        caseflow.command_resolve_review(
            argparse.Namespace(case_root=article_case, item="D4-001", receipt=str(correction))
        )
        verification = write("receipts/D4-001-verification.md")
        caseflow.command_verify_review(
            argparse.Namespace(
                case_root=article_case,
                item="D4-001",
                receipt=str(verification),
                result="pass",
            )
        )
        reviewed = caseflow.command_article_updated(
            argparse.Namespace(case_root=article_case, article=str(article))
        )
        clean = write(
            "clean-review.json",
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": reviewed["article"]["sha256"],
                    "sources": {
                        "ids": ["source-1"],
                        "expected": 1,
                        "reported": 1,
                        "degraded": [],
                    },
                    "findings": [],
                    "open_questions": [],
                }
            ),
        )
        result = caseflow.command_record_review(
            argparse.Namespace(case_root=article_case, receipt=str(clean), diff_pool=None)
        )
        self.assertEqual(result["state"], "spec_ready")
        self.assertEqual(
            caseflow.command_status(argparse.Namespace(case_root=article_case))["state"],
            "spec_ready",
        )

    def test_delivery_stage_two_requires_bound_simplicity_code_report(self) -> None:
        payload = caseflow.load_case(self.case_root)
        payload["stage"] = 4
        payload["state"] = "spec_ready"
        article = self.write("article.md", "# Reviewed article\n")
        payload["article"] = {
            "path": "article.md",
            "sha256": caseflow.digest(article),
            "recorded_at": caseflow.now(),
        }
        caseflow.save_case(self.case_root, payload, "test_spec_ready_for_delivery_quality")
        caseflow.command_route(
            argparse.Namespace(case_root=self.case_root, decision="delivery", lane=["BACKEND"])
        )
        payload = caseflow.load_case(self.case_root)
        payload["delivery"]["stage"] = 2
        payload["delivery"]["state"] = "stitching"
        payload["delivery"]["stages"]["1"]["state"] = "complete"
        payload["delivery"]["stages"]["2"]["state"] = "stitching"
        caseflow.save_case(self.case_root, payload, "test_delivery_stage_two_stitching")

        stitch = self.write("delivery/stitch-02.md")
        pool = self.write(
            "delivery/diff-02.json",
            json.dumps({"schema": 1, "stage": 2, "items": []}),
        )
        with self.assertRaisesRegex(caseflow.CaseFlowError, "requires a simplicity-code"):
            caseflow.command_delivery_record_stitch(
                argparse.Namespace(case_root=self.case_root, report=str(stitch), diff_pool=str(pool))
            )

        diff_snapshot = self.write("delivery/integrated.diff", "diff --git a/a b/a\n")
        skill = self.write("delivery/simplicity-code/SKILL.md")
        quality = self.write(
            "delivery/simplicity-code.json",
            json.dumps(
                {
                    "schema": 1,
                    "gate": "simplicity-code",
                    "actor": {
                        "role": "quality-pass-reviewer",
                        "run_id": "code-simplicity-run",
                    },
                    "subject": {
                        "path": "delivery/integrated.diff",
                        "sha256": caseflow.digest(diff_snapshot),
                    },
                    "skill": {"path": str(skill), "sha256": caseflow.digest(skill)},
                    "outcome": "clean",
                    "checks": [
                        "minimum-core",
                        "real-flow",
                        "seven-step-ladder",
                        "element-classification",
                        "runnable-result",
                    ],
                    "findings": [],
                }
            ),
        )
        result = caseflow.command_delivery_record_stitch(
            argparse.Namespace(
                case_root=self.case_root,
                report=str(stitch),
                diff_pool=str(pool),
                simplicity_report=str(quality),
            )
        )
        self.assertEqual(result["delivery_state"], "ready")
        recorded = caseflow.load_case(self.case_root)["delivery"]["stages"]["2"]
        self.assertEqual(recorded["quality_gates"]["simplicity-code"]["outcome"], "clean")

    def test_delivery_registered_pool_accepts_new_item(self) -> None:
        payload = caseflow.load_case(self.case_root)
        payload["stage"] = 4
        payload["state"] = "spec_ready"
        article = self.write("article.md", "# Reviewed article\n")
        payload["article"] = {
            "path": "article.md",
            "sha256": caseflow.digest(article),
            "recorded_at": caseflow.now(),
        }
        caseflow.save_case(self.case_root, payload, "test_spec_ready")
        caseflow.command_route(
            argparse.Namespace(case_root=self.case_root, decision="delivery", lane=["BACKEND"])
        )
        artifact = self.write("delivery/stage-01-BACKEND.md")
        basis = self.write("delivery/method-BACKEND.md")
        caseflow.command_delivery_submit(
            argparse.Namespace(
                case_root=self.case_root,
                stage=1,
                lane="BACKEND",
                artifact=str(artifact),
                method_basis=str(basis),
            )
        )
        caseflow.command_delivery_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("delivery/stitch-01.md")
        pool = self.write(
            "delivery/diff-01.json",
            json.dumps({"schema": 1, "stage": 1, "items": []}),
        )
        caseflow.command_delivery_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        item = self.write(
            "delivery/new-item.json",
            json.dumps(
                {
                    "id": "D1-002",
                    "target": "delivery/stage-01-BACKEND.md",
                    "change": "Add the newly found contract case",
                    "reason": "Found during delivery correction",
                    "status": "open",
                }
            ),
        )
        appended = caseflow.command_delivery_append_item(
            argparse.Namespace(case_root=self.case_root, item_file=str(item))
        )
        self.assertEqual(appended["delivery_state"], "remediation")
        artifact.write_text("rejected delivery correction\n", encoding="utf-8")
        correction = self.write("delivery/D1-002-correction.md")
        caseflow.command_delivery_resolve(
            argparse.Namespace(case_root=self.case_root, item="D1-002", receipt=str(correction))
        )
        failed = self.write("delivery/D1-002-failed.md")
        caseflow.command_delivery_verify(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-002",
                receipt=str(failed),
                result="fail",
            )
        )
        caseflow.command_delivery_waive(
            argparse.Namespace(
                case_root=self.case_root,
                item="D1-002",
                decision_ref="user-message-88",
            )
        )
        advanced = caseflow.command_delivery_advance(
            argparse.Namespace(case_root=self.case_root)
        )
        self.assertEqual(advanced["delivery_stage"], 2)

    def test_cli_serializes_concurrent_case_mutations(self) -> None:
        self.complete_stage_one()
        script = Path(caseflow.__file__).resolve()
        commands: list[list[str]] = []
        for block in ("B01", "B02"):
            self.write(f"method-basis/stage-02-{block}.md", "# Method basis\n")
            artifact = self.write(f"blocks/{block}/stage-02.md")
            commands.append(
                [
                    sys.executable,
                    str(script),
                    "submit-block",
                    "--case-root",
                    str(self.case_root),
                    "--stage",
                    "2",
                    "--block",
                    block,
                    "--artifact",
                    str(artifact),
                ]
            )
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for command in commands]
        outputs = [process.communicate(timeout=10) for process in processes]
        self.assertEqual([process.returncode for process in processes], [0, 0], outputs)
        payload = caseflow.load_case(self.case_root)
        self.assertEqual(set(caseflow.stage_record(payload)["submissions"]), {"B01", "B02"})

    def test_read_only_status_does_not_create_missing_case_path(self) -> None:
        missing = self.root / "typo" / "case"
        result = subprocess.run(
            [
                sys.executable,
                str(Path(caseflow.__file__).resolve()),
                "status",
                "--case-root",
                str(missing),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("case does not exist", result.stdout)
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
