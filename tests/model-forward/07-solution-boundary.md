# Forward test: two-sided solution boundary

Read only:

- `rules/process-kernel.md`;
- `rules/solution-boundary.md`;
- `skills/spec-preanalysis/SKILL.md`;
- `skills/spec-preanalysis/references/brief-contract.md`;
- `agents/contracts/spec-preanalyst.md`.

Scenario A: the current request names one channel. Current product evidence shows that
the same root rule already has one authoritative owner and a localized channel seam.
The proposed change instead copies the rule into a channel-specific branch.

Scenario B: one current variant is confirmed. There is no roadmap, second consumer or
irreversibility evidence, but the proposal adds a generic rule engine and admin
configurator for possible future variants.

Scenario C: a production defect creates immediate material risk. A narrow reversible
branch contains the incident, and the evidence names both rollback and the observable
event for returning to the systemic solution.

Scenario D: two independent current variants are source-confirmed and both must be
delivered through one shared capability in the present scope.

Scenario E: one ordinary current variant is confirmed. No urgent exception and no
generalization evidence exists; the solution still records the root capability,
invariants, current scope and a small localized seam.

Return one JSON object with:

- `scenario_a_smell`: exact smell id;
- `scenario_a_copy_allowed`: boolean;
- `scenario_a_required_action`: one short sentence;
- `scenario_b_smell`: exact smell id;
- `scenario_b_generic_mechanism_allowed`: boolean;
- `scenario_b_disposition`: `remove` or `defer`;
- `scenario_c_horizon`: exact horizon id;
- `scenario_c_required_exception_fields`: ordered field names from the brief contract;
- `scenario_d_horizon`: exact horizon id;
- `scenario_d_unconfirmed_variants_enter_scope`: boolean;
- `scenario_e_horizon`: exact horizon id;
- `scenario_e_empty_extension_seam_without_reason_valid`: boolean.

Do not invent product requirements or a fourth horizon. Answer from the named files only.
