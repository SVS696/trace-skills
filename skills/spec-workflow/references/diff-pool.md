# Required diff pool

`required-diff.json` is an array under `items`:

```json
{
  "schema": 1,
  "stage": 2,
  "items": [
    {
      "id": "D2-001",
      "target": "blocks/B02/stage-02.md#Rule-4",
      "change": "Define the missing transition from pending to cancelled",
      "reason": "B01 emits cancellation but B02 has no receiving state",
      "status": "open"
    }
  ]
}
```

Rules:

- One file per stage; append new findings to it instead of opening side lists.
- `target`, `change` and `reason` must be exact enough to verify independently.
- `applied` requires a correction receipt path and fingerprint, but does not close the item.
- `verified` requires a separate verification receipt and closes the item.
- A failed verification returns the same item to `open`; correction and verification
  attempts remain in its history. Do not create a replacement item just to retry a fix.
- `waived` requires a user or project decision reference.
- A correction batch may edit only targets named by open items.
- If verification discovers another defect, append a new id to the same pool.
- A stage may advance only when every item is `verified` or `waived`.

Commands:

```bash
python3 scripts/caseflow.py resolve --case-root CASE --item D2-001 --receipt RECEIPT
python3 scripts/caseflow.py verify --case-root CASE --item D2-001 --receipt CHECK --result pass
python3 scripts/caseflow.py verify --case-root CASE --item D2-001 --receipt CHECK --result fail
python3 scripts/caseflow.py waive --case-root CASE --item D2-001 --decision-ref "<decision>"
```
