from __future__ import annotations

import copy
import unittest

from scripts import preanalysis


def decision() -> dict:
    return {
        "schema": 1,
        "subject_id": "TASK-1",
        "status": "approved",
        "decision_ref": "user-message-1",
        "decision": "single",
        "reason": "One outcome",
        "shared_context": [],
        "unknowns": [],
        "articles": [
            {
                "id": "TASK-1",
                "title": "Title",
                "goal": "Goal",
                "outcome": "Outcome",
                "acceptance_boundary": "Boundary",
                "dependencies": [],
                "composition": "article-led",
                "blocks": [{"id": "B01", "title": "Primary semantic concern"}],
            }
        ],
    }


def boundary_brief() -> dict:
    return {
        "schema": 2,
        "subject_id": "TASK-1",
        "sources": [
            {"id": "SRC-1", "kind": "request", "ref": "request-1"},
            {"id": "SRC-2", "kind": "existing-flow", "ref": "flow-2"},
        ],
        "problem": {"statement": "Problem", "evidence_refs": ["SRC-1"]},
        "goal": {"statement": "Goal", "evidence_refs": ["SRC-1"]},
        "solution_hypothesis": {"statement": "Hypothesis", "evidence_refs": ["SRC-1"]},
        "solution_boundary": {
            "horizon": "bounded-systemic",
            "observed_case": "Current channel needs the rule",
            "root_capability": "Apply the rule consistently across supported channels",
            "invariants": ["The rule has one semantic owner"],
            "confirmed_variants": [
                {"name": "Current channel", "evidence_refs": ["SRC-1"]}
            ],
            "hypothesized_variants": [],
            "current_scope": ["Support the current channel"],
            "extension_seams": ["Keep channel selection outside the rule owner"],
            "extension_seam_absence_reason": None,
            "deferred_variants": [],
            "expansion_triggers": ["Another channel is confirmed"],
            "horizon_evidence": {
                "analogy_search_refs": ["SRC-2"],
                "roadmap_refs": [],
                "irreversibility_refs": [],
            },
            "hotfix_exception": None,
        },
        "preliminary_user_stories": [],
        "scope_in": [],
        "scope_out": [],
        "unknowns": [],
        "assumptions": [],
        "dependencies": [],
        "estimate": {"status": "unavailable", "reason": "No implementation contour"},
    }


class PreanalysisTests(unittest.TestCase):
    def test_schema_two_decision_requires_boundary_per_article(self) -> None:
        payload = decision()
        payload["schema"] = 2
        with self.assertRaisesRegex(preanalysis.DecisionError, "solution_boundary"):
            preanalysis.validate_decision(payload, require_approved=True)
        payload["articles"][0]["solution_boundary"] = copy.deepcopy(
            boundary_brief()["solution_boundary"]
        )
        self.assertEqual(
            preanalysis.validate_decision(payload, require_approved=True)["schema"], 2
        )

    def test_bounded_systemic_requires_extension_seam_or_absence_reason(self) -> None:
        brief = boundary_brief()
        brief["solution_boundary"]["extension_seams"] = []
        brief["solution_boundary"]["extension_seam_absence_reason"] = None
        with self.assertRaisesRegex(preanalysis.BriefError, "absence_reason is required"):
            preanalysis.validate_brief(brief)
        brief["solution_boundary"]["extension_seam_absence_reason"] = (
            "No variable behavior exists outside the authoritative rule owner"
        )
        self.assertEqual(preanalysis.validate_brief(brief)["schema"], 2)

    def test_generalized_capability_requires_confirmed_expansion_evidence(self) -> None:
        brief = boundary_brief()
        brief["solution_boundary"]["horizon"] = "generalized-capability"
        with self.assertRaisesRegex(preanalysis.BriefError, "two confirmed variants"):
            preanalysis.validate_brief(brief)
        brief["solution_boundary"]["confirmed_variants"].append(
            {"name": "Second channel", "evidence_refs": ["SRC-2"]}
        )
        self.assertEqual(
            preanalysis.validate_brief(brief)["solution_boundary"]["horizon"],
            "generalized-capability",
        )

    def test_tactical_horizon_requires_reversible_hotfix_exception(self) -> None:
        brief = boundary_brief()
        brief["solution_boundary"]["horizon"] = "tactical"
        with self.assertRaisesRegex(preanalysis.BriefError, "hotfix_exception is required"):
            preanalysis.validate_brief(brief)
        brief["solution_boundary"]["hotfix_exception"] = {
            "reason": "Immediate material risk",
            "reversibility": "Remove the narrow branch",
            "return_trigger": "The incident is contained",
            "evidence_refs": ["SRC-1"],
        }
        self.assertEqual(
            preanalysis.validate_brief(brief)["solution_boundary"]["horizon"],
            "tactical",
        )

    def test_article_led_reserves_article_for_whole_document_stages(self) -> None:
        payload = decision()
        payload["articles"][0]["blocks"] = [{"id": "ARTICLE", "title": "Wrong"}]
        with self.assertRaisesRegex(preanalysis.DecisionError, "reserved"):
            preanalysis.validate_decision(payload, require_approved=True)

    def test_article_led_requires_a_semantic_depth_block(self) -> None:
        payload = decision()
        payload["articles"][0]["blocks"] = []
        with self.assertRaisesRegex(preanalysis.DecisionError, "at least one semantic block"):
            preanalysis.validate_decision(payload, require_approved=True)

    def test_split_dependencies_must_be_acyclic(self) -> None:
        payload = decision()
        payload["decision"] = "split"
        second = copy.deepcopy(payload["articles"][0])
        payload["articles"][0]["id"] = "A"
        payload["articles"][0]["dependencies"] = ["B"]
        second["id"] = "B"
        second["dependencies"] = ["A"]
        payload["articles"].append(second)
        with self.assertRaises(preanalysis.DecisionError):
            preanalysis.validate_decision(payload, require_approved=True)

    def test_approved_single_is_valid(self) -> None:
        self.assertEqual(
            preanalysis.validate_decision(decision(), require_approved=True)["decision"],
            "single",
        )

    def test_estimate_requires_range_or_explicit_unavailability(self) -> None:
        brief = {
            "schema": 1,
            "subject_id": "TASK-1",
            "sources": [],
            "problem": {"statement": "Problem", "evidence_refs": []},
            "goal": {"statement": "Goal", "evidence_refs": []},
            "solution_hypothesis": {"statement": "Hypothesis", "evidence_refs": []},
            "preliminary_user_stories": [],
            "scope_in": [],
            "scope_out": [],
            "unknowns": [],
            "assumptions": [],
            "dependencies": [],
            "estimate": {"status": "estimated", "min": 2, "max": 1, "unit": "days", "confidence": "low", "basis": ["expert"]},
        }
        with self.assertRaises(preanalysis.BriefError):
            preanalysis.validate_brief(brief)
        brief["estimate"] = {"status": "unavailable", "reason": "No implementation contour"}
        self.assertEqual(preanalysis.validate_brief(brief)["subject_id"], "TASK-1")

    def test_unknowns_require_disposition_and_direct_user_question(self) -> None:
        brief = {
            "schema": 1,
            "subject_id": "TASK-1",
            "sources": [],
            "problem": {"statement": "Problem", "evidence_refs": []},
            "goal": {"statement": "Goal", "evidence_refs": []},
            "solution_hypothesis": {"statement": "Hypothesis", "evidence_refs": []},
            "preliminary_user_stories": [],
            "scope_in": [],
            "scope_out": [],
            "unknowns": ["Which boundary?"],
            "assumptions": [],
            "dependencies": [],
            "estimate": {"status": "unavailable", "reason": "No implementation contour"},
        }
        with self.assertRaisesRegex(preanalysis.BriefError, "classified object"):
            preanalysis.validate_brief(brief)
        brief["unknowns"] = [
            {
                "id": "U-001",
                "statement": "The product boundary is unknown",
                "disposition": "user-decision",
                "blocks_specification": True,
                "reason": "Evidence cannot choose a product policy",
            }
        ]
        with self.assertRaisesRegex(preanalysis.BriefError, "question is required"):
            preanalysis.validate_brief(brief)
        brief["unknowns"][0]["question"] = "Which product boundary should be used?"
        self.assertEqual(preanalysis.validate_brief(brief)["unknowns"][0]["id"], "U-001")

    def test_plan_requires_acyclic_tasks_and_sync_readback(self) -> None:
        plan = {
            "schema": 1,
            "subject_id": "TASK-1",
            "status": "approved",
            "decision_ref": "user-message-1",
            "route": "specification",
            "article_ids": ["TASK-1"],
            "tasks": [
                {"id": "P1", "title": "Analyze", "output": "brief", "depends_on": []}
            ],
            "external_sync": {
                "status": "synced",
                "system": "singularity",
                "target_ref": "TASK-1",
            },
        }
        with self.assertRaises(preanalysis.PlanError):
            preanalysis.validate_plan(plan)
        plan["external_sync"]["readback_ref"] = "receipt-1"
        self.assertEqual(preanalysis.validate_plan(plan)["route"], "specification")

    def test_plan_rejects_implementation_route(self) -> None:
        plan = {
            "schema": 1,
            "subject_id": "TASK-1",
            "status": "approved",
            "decision_ref": "user-message-1",
            "route": "implementation",
            "article_ids": ["TASK-1"],
            "tasks": [{"id": "P1", "title": "Build", "output": "code", "depends_on": []}],
            "external_sync": {"status": "not_requested"},
        }
        with self.assertRaisesRegex(preanalysis.PlanError, "route is invalid"):
            preanalysis.validate_plan(plan)

    def test_task_cycle_error_preserves_ids_containing_article(self) -> None:
        plan = {
            "schema": 1,
            "subject_id": "TASK-1",
            "status": "approved",
            "decision_ref": "user-message-1",
            "route": "specification",
            "article_ids": ["TASK-1"],
            "tasks": [
                {
                    "id": "article-work",
                    "title": "One",
                    "output": "one",
                    "depends_on": ["other"],
                },
                {
                    "id": "other",
                    "title": "Two",
                    "output": "two",
                    "depends_on": ["article-work"],
                },
            ],
            "external_sync": {"status": "not_requested"},
        }
        with self.assertRaisesRegex(preanalysis.PlanError, "article-work"):
            preanalysis.validate_plan(plan)


if __name__ == "__main__":
    unittest.main()
