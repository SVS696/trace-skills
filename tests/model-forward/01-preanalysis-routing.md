# Forward test: preanalysis routing

Use only these files.

- `skills/spec-preanalysis/SKILL.md`
- `skills/spec-preanalysis/references/brief-contract.md`
- `skills/spec-preanalysis/references/decision-contract.md`
- `skills/spec-preanalysis/references/plan-contract.md`
- `skills/spec-preanalysis/references/routing-criteria.md`
- `agents/contracts/spec-preanalyst.md`.

## Test input

The request gives few details. It may contain two results that users can accept separately. Singularity is available. The user did not authorize any external write. The team has not decided how many articles to prepare.

Return one JSON object. Include these fields.

- `artifact_order`: ordered artifact filenames that must be proposed;
- `first_decision`: the decision that must precede block design;
- `composition_decision`: the fixed composition model for every resulting article;
- `authoring_order`: what must exist before semantic block work begins;
- `agent_may_approve`: boolean;
- `agent_may_publish_plan`: boolean;
- `parent_may_publish_without_authorization`: boolean;
- `next_gate`: the condition before specification cases may be initialized.

Use the procedure in the listed files.
