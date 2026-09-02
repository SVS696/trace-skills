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
        artifact = self.case_root / "blocks/B01/stage-01.md"
        artifact.write_text("changed after independent verification\n", encoding="utf-8")
        with self.assertRaisesRegex(caseflow.CaseFlowError, "changed after verification"):
            caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        artifact.write_text("ok\n", encoding="utf-8")
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
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "blocks/B01/stage-01.md",
                            "change": "Apply the final boundary correction",
                            "reason": "Second correction to the same artifact",
                            "status": "open",
                        },
                        {
                            "id": "D1-002",
                            "target": "blocks/B01/stage-01.md",
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
        artifact = self.write("blocks/B01/stage-01.md", "initial correction\n")
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
        self.assertEqual(advanced["rebound"], ["blocks/B01/stage-01.md"])
        self.assertEqual(advanced["stage"], 2)

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
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "blocks/B01/stage-01.md",
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
        artifact = self.write("blocks/B01/stage-01.md", "rejected correction\n")
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
                    "items": [
                        {
                            "id": "D1-001",
                            "target": "method-basis/stage-01-B01.md",
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
        basis = self.write("method-basis/stage-01-B01.md", "# Corrected method basis\n")
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
        self.assertIn("method-basis/stage-01-B01.md", advanced["rebound"])
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

    def test_revmux_five_round_cap_requires_explicit_user_decision(self) -> None:
        article_sha256 = self.prepare_review()
        degraded_receipt = self.root / "revmux-degraded-retry.json"
        degraded_receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {"expected": 2, "reported": 1, "degraded": ["adversarial"]},
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
                        "sources": {"expected": 2, "reported": 2, "degraded": []},
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
        receipt = self.root / "revmux-clean-6.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "article_sha256": article_sha256,
                    "sources": {"expected": 2, "reported": 2, "degraded": []},
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
        context = caseflow.command_context(
            argparse.Namespace(case_root=self.case_root, block=None, lane="BACKEND")
        )
        self.assertEqual(context["mode"], "delivery")
        self.assertEqual(context["delivery_stage"], 2)
        self.assertIn(str(article.resolve()), context["read_set"])
        self.assertIn(
            str((self.case_root / "delivery/stage-01-BACKEND.md").resolve()),
            context["read_set"],
        )
        self.assertNotIn(
            str((self.case_root / "blocks/B01/stage-01.md").resolve()),
            context["read_set"],
        )

    def test_article_first_stage_four_can_share_the_mutable_article_path(self) -> None:
        article_case = self.root / "article-first-case"
        decision_payload = json.loads(self.decision.read_text(encoding="utf-8"))
        decision_payload["articles"][0]["composition"] = "article-first"
        decision_payload["articles"][0]["blocks"] = [{"id": "ARTICLE", "title": "Article"}]
        decision = self.root / "article-first-decision.json"
        decision.write_text(json.dumps(decision_payload), encoding="utf-8")
        caseflow.command_init(
            argparse.Namespace(
                case_root=article_case,
                template=self.template,
                decision=decision,
                plan=self.plan,
                article_id="CASE-1",
            )
        )

        def write(relative: str, text: str = "ok\n") -> Path:
            path = article_case / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            return path

        article = article_case / "article.md"
        for stage in caseflow.STAGES:
            write(f"method-basis/stage-{stage:02d}-ARTICLE.md", "# Method basis\n")
            artifact = (
                write("article.md", "# Initial article\n")
                if stage == 4
                else write(f"blocks/ARTICLE/stage-{stage:02d}.md")
            )
            caseflow.command_submit_block(
                argparse.Namespace(
                    case_root=article_case,
                    stage=stage,
                    block="ARTICLE",
                    artifact=str(artifact),
                )
            )
            caseflow.command_open_stitch(argparse.Namespace(case_root=article_case))
            report = write(f"stitches/stage-{stage:02d}.md")
            pool = write(
                f"diffs/stage-{stage:02d}-required.json",
                json.dumps({"schema": 1, "stage": stage, "items": []}),
            )
            caseflow.command_record_stitch(
                argparse.Namespace(case_root=article_case, report=str(report), diff_pool=str(pool))
            )
            caseflow.command_advance(argparse.Namespace(case_root=article_case))
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
                    "sources": {"expected": 1, "reported": 1, "degraded": []},
                    "findings": [{"id": "f1", "severity": "major"}],
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
            argparse.Namespace(case_root=article_case, receipt=str(receipt), diff_pool=str(pool))
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
                    "sources": {"expected": 1, "reported": 1, "degraded": []},
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
