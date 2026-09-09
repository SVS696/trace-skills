# Template family and output rules

Select the variant before authoring: main specification for an independently accepted
product outcome; component task for the assigned slice of an existing parent. A BE/FE
split alone does not create independent specifications. Global assets are defaults;
project templates and their applicability rules take precedence.

The source template is immutable during article authoring. In the output, remove
non-applicable sections and their TOC entries; keep retained sections in source order.
Keep applicability reasons in the author's report, not in the reader-facing article.
Comments and bracketed prompts instruct the author and are removed from the output.

Include only changed components. If BE changes and FE does not, omit FE. If FE changes
its use of an unchanged API, retain the changed FE behavior without restating the BE
contract. Omit the whole API section only when neither contract nor usage changes.
Do not add “no changes” paragraphs. A required compatibility boundary is a positive
requirement; define it once where it belongs.

Main: problem/goal/solution, changed components, semantic history, goal and current
scope, user stories, applicable behavior/data/interface sections, AC, DoD and links.
Component: problem/goal/solution, only the assigned changed owner, parent reference,
owned scope, applicable calls/states/dependencies, AC and DoD; no publication history.
Do not fabricate a backend section for a frontend-only task.

Define current scope once under Description / Boundaries. The later Solution boundaries
section contains only justified extension conditions/seams and links to current scope;
omit it when there is nothing additional to say.

For a changed operation, describe the semantic delta and provide a complete valid
wire example of that operation. Unchanged fields may appear in the example; they do
not become new scope. Do not enumerate unrelated unchanged operations. Use the actual
status and format (including binary or empty responses), not a hardcoded 200/JSON.

Existing UI labels/paths/ids are sourced facts. New UI labels/ids may be proposed within
the authorized design scope, marked as proposed until decided; do not search for them
as existing facts or present them as deployed. Resolve material choices before readiness.

Renumbering is allowed: prepare old heading/id → new heading/id mapping, update all
references within the article and known incoming references together, and verify no
stale or misdirected links remain. Preserve a mapping in case evidence, not reader prose.
If external incoming links cannot be updated, retain the published ID until that
boundary is resolved; do not silently redirect a different story to the old ID.
