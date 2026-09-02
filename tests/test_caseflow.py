from __future__ import annotations

import argparse
import json
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
        caseflow.command_init(
            argparse.Namespace(
                case_root=self.case_root,
                template=self.template,
                decision=self.decision,
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
            argparse.Namespace(case_root=self.case_root, item="D1-001", receipt=str(verification))
        )
        advanced = caseflow.command_advance(argparse.Namespace(case_root=self.case_root))
        self.assertEqual(advanced, {"stage": 2, "state": "blocks"})

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
        payload = caseflow.load_case(self.case_root)
        payload["stage"] = 4
        payload["state"] = "revmux_pending"
        caseflow.save_case(self.case_root, payload, "test_setup")
        receipt = self.root / "revmux.json"
        receipt.write_text(
            json.dumps({"sources": {"degraded": ["docs"]}, "findings": []}),
            encoding="utf-8",
        )
        result = caseflow.command_record_review(
            argparse.Namespace(case_root=self.case_root, receipt=str(receipt))
        )
        self.assertEqual(result["state"], "revmux_pending")

    def test_revmux_gating_findings_require_closed_round_diff(self) -> None:
        payload = caseflow.load_case(self.case_root)
        payload["stage"] = 4
        payload["state"] = "revmux_pending"
        caseflow.save_case(self.case_root, payload, "test_setup")
        receipt = self.root / "revmux-major.json"
        receipt.write_text(
            json.dumps(
                {
                    "sources": {"expected": 2, "reported": 2, "degraded": []},
                    "findings": [{"id": "f1", "severity": "major"}],
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

    def test_revmux_open_question_blocks_spec_ready_until_decided(self) -> None:
        payload = caseflow.load_case(self.case_root)
        payload["stage"] = 4
        payload["state"] = "revmux_pending"
        caseflow.save_case(self.case_root, payload, "test_setup")
        receipt = self.root / "revmux-question.json"
        receipt.write_text(
            json.dumps(
                {
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


if __name__ == "__main__":
    unittest.main()
