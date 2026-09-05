# Decomposition decision contract

```json
{
  "schema": 3,
  "subject_id": "TASK-123",
  "status": "proposed",
  "decision_ref": "",
  "decision": "single",
  "reason": "One independently acceptable product outcome",
  "shared_context": [],
  "unknowns": [],
  "articles": [
    {
      "id": "TASK-123",
      "title": "Reader-facing title",
      "goal": "One goal",
      "outcome": "Observable result",
      "acceptance_boundary": "What can be accepted independently",
      "dependencies": [],
      "composition": "article-led",
      "solution_boundary": {
        "horizon": "bounded-systemic",
        "observed_case": "Current evidence-backed request",
        "root_capability": "Stable capability behind this article",
        "invariants": ["One authoritative owner for the rule"],
        "confirmed_variants": [
          {"name": "Current variant", "evidence_refs": ["SRC-001"]}
        ],
        "hypothesized_variants": [],
        "current_scope": ["Behavior accepted with this article"],
        "extension_seams": ["Localized point for a confirmed next variant"],
        "extension_seam_absence_reason": null,
        "deferred_variants": [],
        "expansion_triggers": ["A second consumer is confirmed"],
        "horizon_evidence": {
          "analogy_search_refs": ["SRC-001"],
          "roadmap_refs": [],
          "irreversibility_refs": []
        },
        "hotfix_exception": null,
        "implementation_transition": {
          "status": "selected",
          "mode": "evolve-in-place",
          "authoritative_owner": "current-capability-owner",
          "superseded_paths": [],
          "coexistence_reason": null,
          "stages": [],
          "retirement_trigger": null,
          "rollback_boundary": null,
          "evidence_refs": ["SRC-001"],
          "reason": "The current owner remains authoritative"
        }
      },
      "architecture": {
        "status": "not-required",
        "triggers": [],
        "design_ref": null,
        "design_sha256": null,
        "design_run_id": null,
        "reason": "No architecture trigger is present"
      },
      "blocks": [
        {"id": "B01", "title": "First semantic concern"},
        {"id": "B02", "title": "Second semantic concern"}
      ]
    }
  ]
}
```

New decisions use schema 3. Schemas 1 and 2 remain readable only for cases already
started before the current preanalysis contract. The `solution_boundary` object
uses the exact shape and horizon rules from [brief-contract.md](brief-contract.md).
It is stored per article because independently accepted outcomes can have different
horizons.

The preanalysis agent always emits `proposed` with an empty `decision_ref`. Only the
parent records `approved` and the real user or project decision reference after the
user has chosen the decomposition.

`single` requires exactly one article; `split` requires at least two. Every article uses
`article-led` composition and has at least one semantic block for the focused depth
passes. `ARTICLE` is reserved by `caseflow` for the whole-template stages and cannot be
a semantic block id. Dependencies refer to article ids and must be acyclic. Case
initialization copies the selected article boundary into `case.json`; later spec and
delivery contexts receive it without reopening the whole preanalysis corpus.

Every article also records `architecture.status=designed|not-required`. A required
design names triggers, path, SHA-256 and authoring `design_run_id` of the artifact produced under
`rules/architecture-analysis.md`. A not-required entry has null design binding and an
explicit reason. `caseflow init` verifies required design bytes before creating a case;
stage 4 later requires a separate conformance run against those bytes.
