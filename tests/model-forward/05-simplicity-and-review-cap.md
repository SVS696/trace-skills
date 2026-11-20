# Forward test: simplicity gates and review cap

Use only these files.

- `rules/process-kernel.md`
- `skills/spec-preanalysis/SKILL.md`
- `skills/spec-workflow/references/stage-4-article.md`
- `skills/delivery-workflow/SKILL.md`
- `skills/delivery-workflow/references/delivery-stages.md`.

## Test input

A. The proposed solution adds a general workflow engine. No current requirement supports it.
B. The complete article is ready for its first substantive revmux round.
C. Five substantive rounds have finished with complete results. The latest correction still needs confirmation.
D. The developers tested the integrated implementation. Independent verification has not started.
E. Two stage 4 reports name `simplicity-spec` and `humanizer`. They omit the hashes of the subject and skill. They also omit the prescribed checks.
F. The reviewer with source ID `reader` reported an accepted finding. A later clean receipt lists only `logic`.

Return one JSON object. Include these fields.

- `scenario_a_gate`: exact skill name that runs before the preliminary brief is final;
- `scenario_a_default_disposition`: disposition for the unsupported generic mechanism;
- `scenario_b_gate_before_revmux`: exact skill name;
- `scenario_b_finding_destination`: where accepted simplicity changes are recorded;
- `scenario_c_start_round_six_without_user_decision`: boolean;
- `scenario_c_retry_counts`: whether a degraded or failed technical retry consumes the cap;
- `scenario_c_required_action`: one short sentence;
- `scenario_d_gate_before_independent_verification`: exact skill name;
- `scenario_d_hidden_cleanup_allowed`: boolean.
- `scenario_e_stage_four_may_close`: boolean;
- `scenario_e_missing_evidence`: one short sentence;
- `scenario_f_clean_round_may_close`: boolean;
- `scenario_f_required_source`: exact source id.
