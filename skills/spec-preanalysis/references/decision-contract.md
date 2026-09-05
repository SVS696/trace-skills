# Decomposition decision contract

```json
{
  "schema": 2,
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
        "hotfix_exception": null
      },
      "blocks": [
        {"id": "B01", "title": "First semantic concern"},
        {"id": "B02", "title": "Second semantic concern"}
      ]
    }
  ]
}
```

New decisions use schema 2. Schema 1 remains readable only for cases already started
before solution horizons were transferred into TRACE. The `solution_boundary` object
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
