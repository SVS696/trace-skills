# Preliminary plan contract

`execution-plan.json` uses schema 1:

```json
{
  "schema": 1,
  "subject_id": "TASK-123",
  "status": "proposed",
  "decision_ref": "",
  "route": "specification",
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

`route` is `stop`, `specification`, or `implementation`. Dependencies must be acyclic.
An approved plan has a `decision_ref`.

External sync states are `not_requested`, `authorized`, and `synced`. `synced` requires
the destination `system`, exact `target_ref`, and `readback_ref`. Tool success without
read-back does not count as synchronized.
