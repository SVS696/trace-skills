# Preliminary plan contract

`execution-plan.json` uses schema 1:

```json
{
  "schema": 1,
  "subject_id": "TASK-123",
  "status": "proposed",
  "decision_ref": "",
  "route": "specification",
  "article_ids": ["TASK-123"],
  "tasks": [
    {
      "id": "P1",
      "title": "Prepare specification TASK-123",
      "output": "One reviewed article",
      "depends_on": []
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

External sync states are `not_requested`, `authorized`, and `synced`. `synced` requires
the destination `system`, exact `target_ref`, and `readback_ref`. Tool success without
read-back does not count as synchronized.
