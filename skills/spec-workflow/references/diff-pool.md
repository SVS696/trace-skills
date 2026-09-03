# Required diff pool

`required-diff.json` is an array under `items`:

```json
{
  "schema": 1,
  "stage": 2,
  "deferred_inputs": [],
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

- One file per stage; append new findings through `caseflow.py append-item` instead of
  editing the registered pool by hand or opening side lists.
- Every specification-stage pool contains `deferred_inputs`, even when empty. It may
  contain only `external-owner` or `implementation-only` inputs proven not to affect
  observable requirements, scenarios or AC. Each entry has `id`, `statement`,
  `disposition` and `reason`; `external-owner` also has `owner_ref`.
- A missing input that can affect specification content is a normal diff item with an
  `input` object, never a deferred note. The diff item's normal `change` and `reason`
  describe the missing content; `input` adds only `id`, `disposition` and, for
  `user-decision`, the exact `question`, or for `external-owner`, `owner_ref`.
  `researchable`, `user-decision` and blocking `external-owner` are the allowed
  dispositions.
- A diff item with `input` cannot be waived. Research, a user answer or external
  evidence must first be incorporated into its target and then independently verified.
- `target`, `change` and `reason` must be exact enough to verify independently.
- `applied` requires a correction receipt path and fingerprint, but does not close the item.
- `verified` requires a separate verification receipt, fingerprints the target bytes
  that were checked, and closes the item.
- A failed verification returns the same item to `open`; correction and verification
  attempts remain in its history. Do not create a replacement item just to retry a fix.
- `waived` requires a user or project decision reference and fingerprints the target
  bytes accepted by that decision.
- A correction batch may edit only targets named by open items.
- If verification discovers another defect, append a new id to the same pool.
- A stage may advance only when every item is `verified` or `waived`.
- Any edit after verification or waiver requires another appended item and another
  check; `advance` rejects bytes different from the last closed item for that target.

Commands:

```bash
python3 scripts/caseflow.py append-item --case-root CASE --item-file NEW-ITEM.json
python3 scripts/caseflow.py resolve --case-root CASE --item D2-001 --receipt RECEIPT
python3 scripts/caseflow.py verify --case-root CASE --item D2-001 --receipt CHECK --result pass
python3 scripts/caseflow.py verify --case-root CASE --item D2-001 --receipt CHECK --result fail
python3 scripts/caseflow.py waive --case-root CASE --item D2-001 --decision-ref "<decision>"
```

`NEW-ITEM.json` contains one item object with `id`, `target`, `change`, `reason` and
`status: open`. When the new item resolves a content input, it also contains the
`input` object above. The command validates the item, rejects duplicate ids, updates
the registered pool fingerprint and returns the stage to `remediation`.

For the article review pool use `append-review-item`; for a delivery-stage pool use
`delivery-append-item`. They accept the same `--item-file` contract and update their
own registered fingerprints.
