# Forward test: preserved method library

Use only these files.

- `skills/method-library/SKILL.md`
- `rules/process-kernel.md`
- `library/requirements/README.md`
- `library/delivery/README.md`
- `library/route-overrides.json`.
- `docs/rule-preservation.md`.

## Test input

A. A specification block must identify the actor and trigger. It must describe the main flow, alternatives, and exceptions.
B. A backend change affects an HTTP endpoint and the meaning of its response status codes.

Return one JSON object. Include these fields.

- `scenario_a_domain`
- `scenario_a_route`
- `scenario_b_domain`
- `scenario_b_routes`: ordered routes that the materialized basis must contain;
- `may_read_full_vigers_extract_by_default`: boolean;
- `may_load_other_lane_basis`: boolean;
- `project_canon_priority`: `higher` or `lower` than general literature;
- `route_creates_product_scope`: boolean;
- `native_rule_coverage_gate`: the exact requirements and delivery counts checked by
  the release validator.
