# Forward test: staged diff lifecycle

Read only:

- `skills/spec-workflow/SKILL.md`;
- `skills/spec-workflow/references/stage-2-behavior.md`;
- `skills/spec-workflow/references/diff-pool.md`;
- `agents/contracts/spec-integration-editor.md`.

Scenario: stage 2 has all block artifacts and a stitch report. Its only required-diff
item has status `applied` and a correction receipt, but there is no independent
verification receipt.

Return one JSON object with:

- `can_advance`: boolean;
- `blocking_status`: exact current item status;
- `next_action`: the single required process action;
- `status_after_success`: exact status after that action succeeds;
- `hidden_edits_allowed`: boolean;
- `lists_allowed`: the number of stage defect pools allowed;
- `other_stage_references_to_read`: filenames, if any.

Do not propose implementation changes. Answer from the named files only.
