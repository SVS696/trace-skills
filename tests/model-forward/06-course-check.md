# Forward test: time-triggered course control

Read only:

- `rules/process-kernel.md`;
- `rules/course-check.md`;
- `docs/architecture.md`.

Scenario A: Smoke Break reports that a turn has crossed its interval. Since the previous
checkpoint, one exact diff item was verified and the next command is a narrow test that
can falsify the active hypothesis. Scenario B: this is the second consecutive reminder
with many tool calls but no new verified fact, closed item or receipt. Scenario C: the
current path now requires editing files outside the approved scope. Scenario D: one
tool call is still running for longer than the Smoke Break interval. Scenario E: five
completed review rounds have been used; the agent fixed the fifth round's findings and
wants to run a bounded post-fix revmux verification without a new user answer.

Return one JSON object with:

- `scenario_a_verdict`: exact verdict;
- `scenario_a_required_next_property`: one short phrase;
- `scenario_b_continue_allowed`: boolean;
- `scenario_b_allowed_verdicts`: ordered array of exact verdicts;
- `scenario_c_verdict`: exact verdict;
- `scenario_c_new_stage_created`: boolean;
- `scenario_d_reminder_during_tool_call`: boolean;
- `scenario_d_checkpoint_timing`: one short phrase;
- `scenario_e_verification_allowed`: boolean;
- `scenario_e_required_authority`: one short phrase.

Answer from the named files only.
