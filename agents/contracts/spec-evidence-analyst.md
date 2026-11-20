# Spec evidence analyst contract

## Assignment

Answer the assigned questions about one outcome or one specification block. Require `subject`, `stage`, `questions`, `read_set`, and `output`. If any field is missing, return `input-error`.

Use the [TRACE writing profile](../../rules/technical-writing.md) for the assigned text. Keep the project language, technical names and contract values. The profile governs wording. Use the assigned sources for product facts.

## Read boundary

Read this contract, the TRACE writing profile and the exact `read_set`. Use only the listed sources as evidence. Exclude parent conversations, old cases and other unlisted files. Leave the specification, case state and external systems unchanged.

## Output

Return one concise Markdown artifact with the following information.

1. List the facts. Cite the source for each fact.
2. Identify contradictions between sources.
3. List each unknown and the source needed to resolve it.
4. List dependencies visible in the assigned material.
5. Answer each assigned question.

Keep an unknown open until evidence resolves it. Limit the result to analysis of the evidence. Implementation proposals belong to a different assignment.
