# Forward test: preanalysis routing

Read only:

- `skills/spec-preanalysis/SKILL.md`;
- `skills/spec-preanalysis/references/brief-contract.md`;
- `skills/spec-preanalysis/references/decision-contract.md`;
- `skills/spec-preanalysis/references/plan-contract.md`;
- `skills/spec-preanalysis/references/routing-criteria.md`;
- `agents/contracts/spec-preanalyst.md`.

Scenario: the initial request is vague and appears to contain two potentially
independent outcomes. Singularity is available, but the user has not authorized an
external write. No decomposition decision exists yet.

Return one JSON object with:

- `artifact_order`: ordered artifact filenames that must be proposed;
- `first_decision`: the decision that must precede block design;
- `composition_decision`: what is selected for every resulting article;
- `agent_may_approve`: boolean;
- `agent_may_publish_plan`: boolean;
- `parent_may_publish_without_authorization`: boolean;
- `next_gate`: the condition before specification cases may be initialized.

Do not explain general requirements engineering. Answer from the named files only.
