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


def current_brief() -> dict:
    payload = boundary_brief()
    payload["schema"] = 3
    for source in payload["sources"]:
        source.update(
            {
                "query": f"Resolve {source['id']}",
                "authority": "project-source",
                "status": "found",
                "checked_at": "2026-09-06T10:00:00+00:00",
                "freshness": "current",
            }
        )
    payload["facts"] = [
        {"id": "F-1", "statement": "Observed fact", "evidence_refs": ["SRC-1"]}
    ]
    payload["contradictions"] = []
    payload["coverage"] = {
        "verdict": "sufficient",
        "surfaces": [
            {
                "id": "COV-1",
                "question": "What behavior is required?",
                "status": "covered",
                "source_refs": ["SRC-1"],
                "gap_refs": [],
            }
        ],
    }
    payload["preliminary_user_stories"] = [
        {
            "id": "PUS-1",
            "actor": "Operator",
            "need": "Run the behavior",
            "value": "Complete the job",
            "evidence_refs": ["SRC-1"],
            "confidence": "high",
        }
    ]
    payload["preliminary_definition_of_done"] = [
        {
            "id": "PDOD-1",
            "criterion": "The behavior is observable",
            "evidence": "Acceptance result",
            "evidence_refs": ["SRC-1"],
            "confidence": "medium",
        }
    ]
    payload["solution_boundary"]["implementation_transition"] = {
        "status": "selected",
        "mode": "evolve-in-place",
        "authoritative_owner": "current-rule-owner",
        "superseded_paths": [],
        "coexistence_reason": None,
        "stages": [],
        "retirement_trigger": None,
        "rollback_boundary": None,
        "evidence_refs": ["SRC-2"],
        "reason": "The current owner remains authoritative",
    }
    payload["architecture_gate"] = {
        "status": "not-required",
        "triggers": [],
        "reason": "No architectural boundary changes",
    }
    return payload


def framed_brief() -> dict:
    payload = current_brief()
    payload["schema"] = 4
    payload["problem"].update(
        {
            "affected_actors": ["Operator"],
            "negative_consequences": ["The operator must repeat the job"],
        }
    )
    payload["goal"].update(
        {
            "beneficiaries": ["Operator"],
            "benefits": ["The job completes without repeated work"],
        }
    )
    payload["solution_essence"] = {
        "statement": "Keep one authoritative result for the job",
        "behavior_changes": ["The system reuses the authoritative result"],
        "problem_resolution": "Repeated work is no longer required",
        "evidence_refs": ["SRC-1"],
    }
    del payload["solution_hypothesis"]
    return payload


class PreanalysisTests(unittest.TestCase):
    def test_schema_four_accepts_complete_template_independent_framing(self) -> None:
        self.assertEqual(preanalysis.validate_brief(framed_brief())["schema"], 4)

    def test_schema_four_requires_negative_problem_consequences(self) -> None:
        brief = framed_brief()
        brief["problem"]["negative_consequences"] = []
        with self.assertRaisesRegex(preanalysis.BriefError, "negative_consequences must not be empty"):
            preanalysis.validate_brief(brief)

    def test_schema_four_requires_goal_benefits(self) -> None:
        brief = framed_brief()
        brief["goal"]["benefits"] = []
        with self.assertRaisesRegex(preanalysis.BriefError, "benefits must not be empty"):
            preanalysis.validate_brief(brief)

    def test_schema_four_requires_solution_to_explain_problem_resolution(self) -> None:
        brief = framed_brief()
        brief["solution_essence"]["problem_resolution"] = ""
        with self.assertRaisesRegex(preanalysis.BriefError, "problem_resolution is required"):
            preanalysis.validate_brief(brief)

    def test_schema_four_requires_at_least_one_preliminary_user_story(self) -> None:
        brief = framed_brief()
        brief["preliminary_user_stories"] = []
        with self.assertRaisesRegex(preanalysis.BriefError, "preliminary_user_stories must not be empty"):
            preanalysis.validate_brief(brief)

    def test_schema_four_requires_evidence_for_each_framing_answer(self) -> None:
        brief = framed_brief()
        brief["solution_essence"]["evidence_refs"] = []
        with self.assertRaisesRegex(preanalysis.BriefError, "evidence_refs must not be empty"):
            preanalysis.validate_brief(brief)

    def test_schema_four_keeps_schema_three_coverage_and_transition_guards(self) -> None:
        brief = framed_brief()
        del brief["solution_boundary"]["implementation_transition"]
        with self.assertRaisesRegex(preanalysis.BriefError, "implementation_transition must be an object"):
            preanalysis.validate_brief(brief)

    def test_schema_three_binds_source_coverage_and_preliminary_lineage_inputs(self) -> None:
        brief = current_brief()
        self.assertEqual(preanalysis.validate_brief(brief)["schema"], 3)
        del brief["sources"][0]["query"]
        with self.assertRaisesRegex(preanalysis.BriefError, "query is required"):
            preanalysis.validate_brief(brief)

    def test_schema_three_requires_evidence_for_pus_and_preliminary_dod(self) -> None:
        brief = current_brief()
        brief["preliminary_user_stories"][0]["evidence_refs"] = []
        with self.assertRaisesRegex(preanalysis.BriefError, "evidence_refs must not be empty"):
            preanalysis.validate_brief(brief)
        brief = current_brief()
        brief["preliminary_definition_of_done"][0]["confidence"] = "certain"
        with self.assertRaisesRegex(preanalysis.BriefError, "confidence is invalid"):
            preanalysis.validate_brief(brief)

    def test_staged_transition_requires_retirement_and_authoritative_stages(self) -> None:
        brief = current_brief()
        transition = brief["solution_boundary"]["implementation_transition"]
        transition.update(
            {
                "mode": "staged-migration",
                "superseded_paths": ["legacy-handler"],
                "coexistence_reason": "Consumers migrate independently",
                "stages": [],
                "retirement_trigger": "All consumers use the new path",
                "rollback_boundary": "Restore the legacy handler",
            }
        )
        with self.assertRaisesRegex(preanalysis.BriefError, "stages must not be empty"):
            preanalysis.validate_brief(brief)

    def test_current_plan_binds_brief_sources_and_exit_criteria(self) -> None:
        plan = {
            "schema": 2,
            "subject_id": "TASK-1",
            "status": "approved",
            "decision_ref": "user-message-1",
            "brief_sha256": "a" * 64,
            "route": "specification",
            "article_ids": ["TASK-1"],
            "tasks": [
                {
                    "id": "P1",
                    "title": "Analyze",
                    "output": "article",
                    "depends_on": [],
                    "source_refs": ["SRC-1"],
                    "exit_criteria": ["Article passes its stage gate"],
                }
            ],
            "external_sync": {"status": "not_requested"},
        }
        self.assertEqual(preanalysis.validate_plan(plan)["schema"], 2)
        plan["tasks"][0]["exit_criteria"] = []
        with self.assertRaisesRegex(preanalysis.PlanError, "exit_criteria must not be empty"):
            preanalysis.validate_plan(plan)

    def test_sufficient_coverage_rejects_an_open_contradiction(self) -> None:
        brief = current_brief()
        brief["contradictions"] = [
            {
                "id": "CON-1",
                "statement": "Sources disagree",
                "source_refs": ["SRC-1", "SRC-2"],
                "status": "open",
            }
        ]
        with self.assertRaisesRegex(preanalysis.BriefError, "open contradiction"):
            preanalysis.validate_brief(brief)

    def test_schema_three_decision_requires_architecture_binding_by_horizon(self) -> None:
        payload = decision()
        payload["schema"] = 3
        payload["articles"][0]["solution_boundary"] = copy.deepcopy(
            current_brief()["solution_boundary"]
        )
        payload["articles"][0]["solution_boundary"]["horizon"] = "generalized-capability"
        payload["articles"][0]["solution_boundary"]["confirmed_variants"].append(
            {"name": "Second channel", "evidence_refs": ["SRC-2"]}
        )
        payload["articles"][0]["architecture"] = {
            "status": "not-required",
            "triggers": [],
            "design_ref": None,
            "design_sha256": None,
            "design_run_id": None,
            "reason": "No architecture changes",
        }
        with self.assertRaisesRegex(preanalysis.DecisionError, "requires architecture design"):
            preanalysis.validate_decision(payload, require_approved=True)
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
