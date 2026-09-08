# Observable quality pass

Reading a peer skill is not evidence that its pass happened. A required pass produces
one JSON report bound to the exact subject bytes and the exact `SKILL.md` bytes.

```json
{
  "schema": 1,
  "gate": "simplicity-spec | humanizer | simplicity-code",
  "actor": {"role": "assigned narrow role", "run_id": "different run"},
  "subject": {"path": "artifact-or-diff", "sha256": "64 hex"},
  "skill": {"path": "/absolute/path/SKILL.md", "sha256": "64 hex"},
  "style_profile": {"path": "/absolute/path/profile.md", "sha256": "64 hex"},
  "outcome": "clean | changes-required",
  "checks": ["checks required by the selected gate"],
  "findings": [
    {"id": "stable-id", "target": "exact location", "change": "exact diff", "reason": "evidence"}
  ]
}
```

`purpose` and `dismissed_findings` are present only for
post-`revmux` adjudication. `style_profile` is required only for `humanizer`. Empty
findings require `clean`; non-empty findings require `changes-required`.

For ordinary subject passes, every reported finding must appear in the current single
diff-pool through the same `source_finding_id`. For post-`revmux` adjudication, the
subject is the exact review receipt. Confirmed findings remain in `findings` with the
smallest proposed change;
the rest are listed in `dismissed_findings` with reason and evidence and do not enter
the correction diff. The two sets must be disjoint and exhaustive.

The adjudication report adds:

```json
{
  "purpose": "revmux-finding-adjudication",
  "dismissed_findings": [
    {
      "id": "revmux-finding-id",
      "reason": "why it is dismissed",
      "evidence": "exact requirement or execution evidence"
    }
  ]
}
```

Required checks:

- `simplicity-spec`: `minimum-core`, `seven-step-ladder`,
  `element-classification`, `rewritten-result`;
- `humanizer`: `draft-rewrite`, `anti-ai-audit`, `final-rewrite`;
- `simplicity-code`: `minimum-core`, `real-flow`, `seven-step-ladder`,
  `element-classification`, `runnable-result`.

For `simplicity-spec`, `element-classification` includes the skill's change-boundary
check: identify the concrete change and requirement evidence for each technical block,
or propose `REMOVE` / `SIMPLIFY`. A catalogue of unchanged platform contracts is a
solution-scope defect, not prose cleanup; a "not changed" label does not justify it.
Retain new behaviour and contract deltas, not complete baseline request/response or
CRUD descriptions. A necessary compatibility boundary may use one short statement
or a source link. A full-article pass cannot be `clean` while that catalogue remains;
a bounded pass must limit its conclusion to its exact subject and read-set.

The report is invalid when it only says that the skill was read, names the gate, or
claims `clean` without its prescribed checks. The article or code author cannot issue
the narrow reviewer report under the same `run_id`.
