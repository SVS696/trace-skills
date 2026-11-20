# Forward test: staged diff lifecycle

Use only these files.

- `skills/spec-workflow/SKILL.md`
- `skills/spec-workflow/references/stage-2-behavior.md`
- `skills/spec-workflow/references/diff-pool.md`
- `agents/contracts/spec-integration-editor.md`.

## Test input

A case uses the earlier stage-pool contract. All stage 2 blocks and the integration report are available. The only required correction has status `applied`. A receipt records the correction. No receipt records an independent check.

Return one JSON object. Include these fields.

- `can_advance`: boolean;
- `blocking_status`: exact current item status;
- `next_action`: the single required process action;
- `status_after_success`: exact status after that action succeeds;
- `hidden_edits_allowed`: boolean;
- `lists_allowed`: the number of stage defect pools allowed;
- `other_stage_references_to_read`: filenames, if any.

Limit the answer to the next step in this case.
