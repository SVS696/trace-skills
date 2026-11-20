# Forward test: time-triggered course control

Use only these files.

- `rules/process-kernel.md`
- `rules/course-check.md`
- `docs/architecture.md`.

## Test input

A. Smoke Break reports that the interval has elapsed. Since the last checkpoint, a reviewer verified one change. The next test can disprove the current hypothesis.
B. For the second consecutive interval, the agent made many tool calls. It obtained no new verified fact, closed item, or receipt.
C. The next step requires a change outside the approved scope.
D. One tool call takes longer than the Smoke Break interval.
E. Five review rounds have finished. The agent applied the fifth round of corrections and wants to start another revmux check. The user has given no new decision.

Return one JSON object. Include these fields.

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
