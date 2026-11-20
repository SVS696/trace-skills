# Quality pass reviewer contract

## Assignment

Run one assigned check. The allowed checks are `simplicity-spec`, `humanizer`, and `simplicity-code`. Require the subject, its SHA-256, the peer skill entry point, applicable project rules, required checks from `rules/quality-pass.md`, and `report_output`. For `humanizer`, require the style profile. For `simplicity-code`, require the commands to run.

For `purpose: revmux-finding-adjudication`, use the assigned `revmux` receipt as the subject. Use only the evidence needed to check each finding against the current requirement or actual execution path. Apply `simplicity-spec` to article findings. Apply `simplicity-code` to implementation findings.

Use the [TRACE writing profile](../../rules/technical-writing.md) for the report. For a style check, also apply the assigned style profile. Check whether the intended reader can use the rule in its normal case and at a boundary. Keep the original scope, terms, obligations, exceptions, and reasons when you propose an edit. Keep quoted evidence exact.

## Rules

1. Read and run the assigned peer skill. Inspect the actual subject. Keep it unchanged. Propose exact edits for the current diff-pool.
2. Preserve safety, evidence, public contract compatibility, traceability, and tested edge cases.
3. Run all checks for the selected skill. For `humanizer`, complete its style cycle. For `simplicity-code`, check the actual execution path. For `simplicity-spec`, check the change boundary in `element-classification` as specified by the skill and `rules/quality-pass.md`. Describe existing contract behavior as work only when the approved change affects it. Limit each verdict to the available sources.
4. For each finding, give a stable ID, the exact target, the required change, and the reason.
5. When checking a receipt, account for each finding exactly once. For a confirmed finding, add the smallest sufficient correction to `findings`. For a speculative, unreachable or disproportionate finding, add an object to `dismissed_findings` with `id`, `reason`, and `evidence`. Limit this pass to the findings in the receipt.

Return one schema-1 quality report with observable evidence. Set the result to `clean`, `changes-required`, or `input-error`.
