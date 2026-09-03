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

`style_profile` is required only for `humanizer`. Empty findings require `clean`;
non-empty findings require `changes-required`. Every finding must appear in the current
single diff-pool through the same `source_finding_id`.

Required checks:

- `simplicity-spec`: `minimum-core`, `seven-step-ladder`,
  `element-classification`, `rewritten-result`;
- `humanizer`: `draft-rewrite`, `anti-ai-audit`, `final-rewrite`;
- `simplicity-code`: `minimum-core`, `real-flow`, `seven-step-ladder`,
  `element-classification`, `runnable-result`.

The report is invalid when it only says that the skill was read, names the gate, or
claims `clean` without its prescribed checks. The article or code author cannot issue
the narrow reviewer report under the same `run_id`.
