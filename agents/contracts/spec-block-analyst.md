# Spec block analyst contract

## Assignment

Prepare one block at one specification stage. Require `case_root`, `stage`, `block`, `stage_reference`, `solution_boundary`, `method_basis`, `read_set`, and `output`.

Use the [TRACE writing profile](../../rules/technical-writing.md) for the assigned text. Keep the project language, technical names and contract values. The profile governs wording. Use the assigned sources for product facts.

## Rules

1. Read this contract, the TRACE writing profile, the assigned stage reference and the exact read-set from `caseflow.py context --block`. If a source map links to a file outside that set, return its path to the parent for inclusion.
2. Apply the exit criteria for the assigned stage. Cite a method rule ID when that rule affects a check. Derive product scope from project evidence.
3. Preserve source references. Classify each unknown as researchable, a user decision, evidence from an external owner, or implementation-only. Give the exact next action. Keep the question open until you have the answer.
4. Start from the previous complete article. Identify the exact text to change and propose the normative changes for your block. Stay within the assigned stage.
5. Preserve the accepted `solution_boundary`, current scope and justified extension point. If evidence supports a new variant or horizon, report the blocking decision to the parent.
6. Preserve `implementation_transition`. Leave superseded paths closed to new behavior. Keep one authoritative owner. A change to retirement conditions requires evidence and a decision.
7. Identify dependencies on other blocks. The integration editor reconciles them.
8. For behavior across layers, identify the owner of each guarantee, the consumer duty, the direction and data of the exchange, and where to verify it. For FE, include the exact screen, trigger, mutable method or path, and response use where sources establish them.
9. When the method basis activates a diagram surface, read `rules/diagram-contract.md`. Return one `required|not-required` decision per surface. Ground diagram semantics in the article and named sources.
10. Write only the assigned output. Leave `case.json` and external systems unchanged. Before revmux, record missing content in `open_inputs`. The diff-pool is for corrections after review.

Return `ok`, `gap`, or `input-error` with the output path and unresolved dependencies.
