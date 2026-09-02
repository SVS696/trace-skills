# Forward test: preserved method library

Read only:

- `skills/method-library/SKILL.md`;
- `rules/process-kernel.md`;
- `library/requirements/README.md`;
- `library/delivery/README.md`;
- `library/route-overrides.json`.
- `docs/rule-preservation.md`.

Scenario A: a specification block must model actor, trigger, main flow, alternatives
and exceptions. Scenario B: a backend lane changes an HTTP endpoint and its status-code
semantics.

Return one JSON object with:

- `scenario_a_domain`;
- `scenario_a_route`;
- `scenario_b_domain`;
- `scenario_b_routes`: ordered routes that the materialized basis must contain;
- `may_read_full_vigers_extract_by_default`: boolean;
- `may_load_other_lane_basis`: boolean;
- `project_canon_priority`: `higher` or `lower` than general literature;
- `route_creates_product_scope`: boolean;
- `native_rule_coverage_gate`: the exact requirements and delivery counts checked by
  the release validator.

Answer from the named files only.
