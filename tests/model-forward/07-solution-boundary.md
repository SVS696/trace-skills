# Forward test: two-sided solution boundary

Use only these files.

- `rules/process-kernel.md`
- `rules/solution-boundary.md`
- `skills/spec-preanalysis/SKILL.md`
- `skills/spec-preanalysis/references/brief-contract.md`
- `agents/contracts/spec-preanalyst.md`.

## Test input

A. The request names one channel. Current evidence identifies one owner for the shared rule and an existing place to handle channel differences. The proposal duplicates the rule in a channel branch.
B. Evidence supports one current variant. There is no roadmap, second consumer, or evidence that the decision is irreversible. The proposal adds a rule engine and an admin tool for possible future variants.
C. A production defect poses an immediate material risk. A small, reversible change contains the incident. The evidence identifies the rollback and an observable condition for returning to the system-wide solution.
D. Sources confirm two independent variants. Both need the same capability in the current scope.
E. Evidence supports one current variant. There is no urgent exception or evidence for generalization. The solution records the underlying capability, its invariants, the current scope, and a specific place to extend it.

Return one JSON object. Include these fields.

- `scenario_a_smell`: exact smell id;
- `scenario_a_copy_allowed`: boolean;
- `scenario_a_required_action`: one short sentence;
- `scenario_b_smell`: exact smell id;
- `scenario_b_generic_mechanism_allowed`: boolean;
- `scenario_b_disposition`: `remove` or `defer`
- `scenario_c_horizon`: exact horizon id;
- `scenario_c_required_exception_fields`: ordered field names from the brief contract;
- `scenario_d_horizon`: exact horizon id;
- `scenario_d_unconfirmed_variants_enter_scope`: boolean;
- `scenario_e_horizon`: exact horizon id;
- `scenario_e_empty_extension_seam_without_reason_valid`: boolean.

Select a horizon defined in the listed files.
