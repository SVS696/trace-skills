# Forward test: delivery boundary

Use only these files.

- `skills/delivery-workflow/SKILL.md`
- `skills/delivery-workflow/references/delivery-stages.md`
- `agents/contracts/implementation-backend.md`
- `agents/contracts/implementation-verifier.md`.

## Test input

A. The final specification is ready. Its selected route is `stop`.
B. A different specification is ready. Its route is `delivery`. The agent owns one backend assignment in stage 2.

Return one JSON object. Include these fields.

- `scenario_a_start_delivery`: boolean;
- `scenario_a_next_step`: one short sentence;
- `scenario_b_agent`: exact agent name;
- `scenario_b_read_scope`: the categories of material that agent may read;
- `scenario_b_may_change_frontend`: boolean;
- `scenario_b_self_check_is_independent_verification`: boolean;
- `scenario_b_final_statuses_kept_separate`: array of status categories.
