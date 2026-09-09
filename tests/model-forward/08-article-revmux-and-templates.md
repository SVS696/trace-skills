# Forward evaluation: final article and template applicability

Read only the current files listed below. Treat them as instructions being evaluated;
do not change files, run commands, or start agents. For each case return a JSON object
with case_id, next_action, artifact_to_change, forbidden_shortcut and source_rule.
If instructions genuinely conflict, report that rather than choosing silently.

Read-set:
- skills/spec-workflow/SKILL.md
- skills/spec-workflow/references/stage-4-article.md
- agents/contracts/spec-article-editor.md
- agents/contracts/spec-block-analyst.md
- rules/template-family.md
- rules/process-kernel.md
- assets/reader-specification-ru.md
- assets/component-specification-ru.md

Cases:
A. A BE response changes. Existing FE behavior and calls are unchanged. Which owner
sections belong in the article, and is an unchanged FE paragraph needed?
B. A new FE screen calls an existing unchanged API. Which API material belongs in
the article, and should the complete API section be removed?
C. First stage-4 preflight finds a broken link. No revmux or correction pool exists.
What happens next and when can a pool be created?
D. Revmux found an incorrect rule. The source block was fixed, article bytes were
not changed. Can this be resolved? What confirms the eventual correction?
E. Published US-2 is deleted and US-3 should become US-2. Another document links to
old US-3. What must be changed together? What if that external document is inaccessible?
F. Five substantive ordinary revmux rounds finished. A latest fix needs confirmation.
Can another check be renamed targeted verification and run without a user decision?
