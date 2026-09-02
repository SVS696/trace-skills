# Forward test: delivery boundary

Read only:

- `skills/delivery-workflow/SKILL.md`;
- `skills/delivery-workflow/references/delivery-stages.md`;
- `agents/contracts/implementation-backend.md`;
- `agents/contracts/implementation-verifier.md`.

Scenario A: the final specification is ready, but its explicit route is `stop`.
Scenario B: a different specification is ready with route `delivery`; the current
assignment is one backend lane during stage 2.

Return one JSON object with:

- `scenario_a_start_delivery`: boolean;
- `scenario_a_next_step`: one short sentence;
- `scenario_b_agent`: exact agent name;
- `scenario_b_read_scope`: the categories of material that agent may read;
- `scenario_b_may_change_frontend`: boolean;
- `scenario_b_self_check_is_independent_verification`: boolean;
- `scenario_b_final_statuses_kept_separate`: array of status categories.

Answer from the named files only.
