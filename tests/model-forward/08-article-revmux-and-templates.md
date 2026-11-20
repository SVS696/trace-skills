# Test the final article and the choice of template

Read the files below. For each case, return a JSON object with `case_id`, `next_action`, `artifact_to_change`, `forbidden_shortcut`, and `source_rule`. If two instructions conflict, name both. Use read-only access. Keep files, commands, and other agents outside the test actions.

## Files

- skills/spec-workflow/SKILL.md
- skills/spec-workflow/references/stage-4-article.md
- agents/contracts/spec-article-editor.md
- agents/contracts/spec-block-analyst.md
- rules/template-family.md
- rules/process-kernel.md
- assets/reader-specification-ru.md
- assets/component-specification-ru.md

## Cases

A. A backend response changes. The frontend keeps its current behavior and calls. Which component sections belong in the article? Should the article describe the existing frontend behavior?

B. A new frontend screen calls an existing API. The API contract stays the same. Which part of that contract does the article need? What happens to the full API section?

C. The first stage 4 check finds a broken link. The first revmux round has not started. There is no correction pool. What should the author do now? When can a correction pool exist?

D. Revmux found an incorrect rule. The author fixed the source block. The article still contains the old text. Can the author close the finding? What evidence will confirm the correction?

E. An editor deletes published US-2 and plans to rename US-3 to US-2. Another document links to the old US-3. What must change together? What should the editor do if the linked document is inaccessible?

F. Five substantive revmux rounds have finished. The latest correction needs confirmation. May the agent run another check under the name of targeted verification without a user decision?
