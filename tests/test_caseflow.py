from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import caseflow


class CaseFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.case_root = self.root / "case"
        self.template = self.root / "template.md"
        self.template.write_text("# Template\n", encoding="utf-8")
        self.decision = self.root / "decision.json"
        self.decision.write_text(
            json.dumps(
                {
                    "schema": 1,
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
                            "composition": "hybrid",
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
                    "schema": 1,
                    "subject_id": "CASE-1",
                    "status": "approved",
                    "decision_ref": "user-message-1",
                    "route": "specification",
                    "article_ids": ["CASE-1"],
                    "tasks": [
                        {
                            "id": "P1",
                            "title": "Prepare CASE-1",
                            "output": "Reviewed article",
                            "depends_on": [],
                        }
                    ],
                    "external_sync": {"status": "not_requested"},
                }
            ),
            encoding="utf-8",
        )
        caseflow.command_init(
            argparse.Namespace(
                case_root=self.case_root,
                template=self.template,
                decision=self.decision,
                plan=self.plan,
                article_id="CASE-1",
            )
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, text: str = "ok\n") -> Path:
        path = self.case_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def submit_stage_one(self) -> None:
        for block in ("B01", "B02"):
            self.write(f"method-basis/stage-01-{block}.md", "# Method basis\n")
            artifact = self.write(f"blocks/{block}/stage-01.md")
            caseflow.command_submit_block(
                argparse.Namespace(
                    case_root=self.case_root,
                    stage=1,
                    block=block,
                    artifact=str(artifact),
                )
            )

    def prepare_review(self) -> str:
        article = self.write("article.md", "# Article\n")
        payload = caseflow.load_case(self.case_root)
        payload["stage"] = 4
        payload["state"] = "revmux_pending"
        payload["article"] = {
            "path": "article.md",
            "sha256": caseflow.digest(article),
            "recorded_at": caseflow.now(),
        }
        caseflow.save_case(self.case_root, payload, "test_review_setup")
        return payload["article"]["sha256"]

    def test_stitch_requires_every_block(self) -> None:
        self.write("method-basis/stage-01-B01.md", "# Method basis\n")
        artifact = self.write("blocks/B01/stage-01.md")
        caseflow.command_submit_block(
            argparse.Namespace(case_root=self.case_root, stage=1, block="B01", artifact=str(artifact))
        )
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))

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
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "blocks/B01/stage-01.md",
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
        advanced = caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(advanced["stage"], 2)
        self.assertEqual(advanced["state"], "blocks")

    def test_registered_diff_pool_accepts_only_valid_appended_items(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps({"schema": 1, "stage": 1, "items": []}),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        item_file = self.write(
            "diffs/new-item.json",
            json.dumps(
                {
                    "id": "D1-002",
                    "target": "blocks/B02/stage-01.md",
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
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "blocks/B01/stage-01.md#boundary",
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
        artifact = self.write("blocks/B01/stage-01.md", "corrected\n")
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
        self.assertEqual(advanced["rebound"], ["blocks/B01/stage-01.md"])
        artifact.write_text("drift after close\n", encoding="utf-8")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "changed after registration"):
            caseflow.command_status(argparse.Namespace(case_root=self.case_root))

    def test_unpooled_stage_output_drift_blocks_advance(self) -> None:
        self.submit_stage_one()
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/stage-01.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps({"schema": 1, "stage": 1, "items": []}),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        self.write("blocks/B01/stage-01.md", "unregistered change\n")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "outside verified diff pool"):
            caseflow.command_advance(argparse.Namespace(case_root=self.case_root))

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
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "blocks/B01/stage-01.md",
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
                    "sources": {"expected": 2, "reported": 1, "degraded": ["docs"]},
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

    def test_revmux_gating_findings_require_closed_round_diff(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.root / "revmux-major.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {"expected": 2, "reported": 2, "degraded": []},
                    "findings": [{"id": "f1", "severity": "major"}],
                    "open_questions": [],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaises(caseflow.CaseFlowError):
            caseflow.command_record_review(
                argparse.Namespace(case_root=self.case_root, receipt=str(receipt), diff_pool=None)
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
        updated = caseflow.command_article_updated(
            argparse.Namespace(case_root=self.case_root, article=str(article))
        )
        self.assertEqual(updated["state"], "revmux_pending")

    def test_registered_review_pool_accepts_new_item(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.root / "review-with-finding.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {"expected": 2, "reported": 2, "degraded": []},
                    "findings": [{"id": "f1", "severity": "major"}],
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
        caseflow.command_record_review(
            argparse.Namespace(case_root=self.case_root, receipt=str(receipt), diff_pool=str(pool))
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

    def test_revmux_open_question_blocks_spec_ready_until_decided(self) -> None:
        article_sha256 = self.prepare_review()
        receipt = self.root / "revmux-question.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {"expected": 2, "reported": 2, "degraded": []},
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
            caseflow.command_init(
                argparse.Namespace(
                    case_root=self.root / "second-case",
                    template=self.template,
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
                    "sources": {"expected": 2, "reported": 2, "degraded": []},
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
                    "sources": {"expected": 2, "reported": 2, "degraded": []},
                    "findings": [
                        {"id": "same", "severity": "minor"},
                        {"id": "same", "severity": "major"},
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
                    "sources": {"expected": 2, "reported": 2, "degraded": []},
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
                    "sources": {"expected": 2, "reported": 2, "degraded": []},
                    "findings": [{"id": "f1", "severity": "major"}],
                    "open_questions": [{"id": "q1", "body": "Choose a boundary"}],
                }
            ),
            encoding="utf-8",
        )
        recorded = caseflow.command_record_review(
            argparse.Namespace(case_root=self.case_root, receipt=str(receipt), diff_pool=None)
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
        for block in ("B01", "B02"):
            self.write(f"method-basis/stage-01-{block}.md", "# Method basis\n")
            artifact = self.write(f"blocks/{block}/custom-foundation.md")
            caseflow.command_submit_block(
                argparse.Namespace(
                    case_root=self.case_root,
                    stage=1,
                    block=block,
                    artifact=str(artifact),
                )
            )
        caseflow.command_open_stitch(argparse.Namespace(case_root=self.case_root))
        report = self.write("stitches/custom-stage-one.md")
        pool = self.write(
            "diffs/stage-01-required.json",
            json.dumps({"schema": 1, "stage": 1, "items": []}),
        )
        caseflow.command_record_stitch(
            argparse.Namespace(case_root=self.case_root, report=str(report), diff_pool=str(pool))
        )
        caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        context = caseflow.command_context(
            argparse.Namespace(case_root=self.case_root, block="B01")
        )
        self.assertIn(
            str((self.case_root / "blocks/B01/custom-foundation.md").resolve()),
            context["read_set"],
        )

    def test_delivery_has_machine_backed_stage_transitions(self) -> None:
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

    def test_cli_serializes_concurrent_case_mutations(self) -> None:
        script = Path(caseflow.__file__).resolve()
        commands: list[list[str]] = []
        for block in ("B01", "B02"):
            self.write(f"method-basis/stage-01-{block}.md", "# Method basis\n")
            artifact = self.write(f"blocks/{block}/stage-01.md")
            commands.append(
                [
                    sys.executable,
                    str(script),
                    "submit-block",
                    "--case-root",
                    str(self.case_root),
                    "--stage",
                    "1",
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


if __name__ == "__main__":
    unittest.main()
