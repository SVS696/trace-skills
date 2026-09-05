# Preliminary plan contract

New `execution-plan.json` files use schema 2. Schema 1 remains readable only for
started legacy cases; `caseflow init` accepts schema 2.

```json
{
  "schema": 2,
  "subject_id": "TASK-123",
  "status": "proposed",
  "decision_ref": "",
  "brief_sha256": "<sha256 of preanalysis-brief.json>",
  "route": "specification",
  "article_ids": ["TASK-123"],
  "tasks": [
    {
      "id": "P1",
      "title": "Prepare specification TASK-123",
      "output": "One reviewed article",
      "depends_on": [],
      "source_refs": ["SRC-001"],
      "exit_criteria": ["The complete stage-4 article passes its required gates"],
      "checklist": [
        {"id": "P1-C1", "action": "Prepare the whole-template baseline", "done_when": "Stage 1 diff is closed"}
      ]
    }
  ],
  "external_sync": {"status": "not_requested"}
}
```

`route` is `stop` or `specification`. Implementation-only work is outside this plan
contract and may enter `delivery-workflow` only from an existing `spec_ready` case.
`article_ids` names exactly the specification outputs approved in
`decomposition-decision.json`; dependencies must be acyclic. An approved plan has the
same `subject_id` and `decision_ref` as that decision.

`brief_sha256` binds the plan to the exact approved brief. Every task names at least one
brief `source_ref` and at least one observable `exit_criteria`. `checklist` is optional;
use it only for finer actions inside a non-atomic task and do not turn every mechanical
action into a dependency node.

External sync states are `not_requested`, `authorized`, and `synced`. `synced` requires
the destination `system`, exact `target_ref`, and `readback_ref`. Tool success without
read-back does not count as synchronized.
