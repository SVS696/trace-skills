# Forward test: simplicity gates and review cap

Read only:

- `rules/process-kernel.md`;
- `skills/spec-preanalysis/SKILL.md`;
- `skills/spec-workflow/references/stage-4-article.md`;
- `skills/delivery-workflow/SKILL.md`;
- `skills/delivery-workflow/references/delivery-stages.md`.

Scenario A: a preliminary solution proposes a generic workflow engine without a
current requirement. Scenario B: a complete specification article is about to enter
its first substantive revmux round. Scenario C: five non-degraded substantive review
rounds have completed and the latest fix would normally require confirmation. Scenario
D: integrated implementation has developer tests but has not entered independent
verification. Scenario E: stage 4 has reports that merely name `simplicity-spec` and
`humanizer`, but the reports have no subject/skill hashes or prescribed check lists.
Scenario F: an accepted reader finding came from source `reader`; a later clean
receipt lists only source `logic`.

Return one JSON object with:

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

Answer from the named files only.
