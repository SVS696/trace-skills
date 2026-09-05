# Routing criteria

## Split into several specifications when

- outcomes can be accepted, handed off or stopped independently;
- different user groups have independent journeys and business rules;
- lifecycle and data ownership boundaries are stable;
- one article would require several unrelated goals or acceptance decisions;
- dependencies can be expressed as a small acyclic graph.

Do not split only because work has backend/frontend parts, several screens, several
agents, many requirements, or different implementation repositories.

## Design the later block descent

Every article starts with a complete working pass through the unchanged template.
There is no `article-first | hybrid` route choice.

Use one semantic block when the article has one dominant journey and one tightly coupled
rule set. Use several only when they expose genuinely different analysis surfaces, for
example:

- bounded source sets or actors;
- independent business-rule clusters;
- distinct data lifecycles or state machines;
- interfaces whose provider and consumer duties can be checked separately.

Do not create blocks from template headings, BE/FE layers, screens, repositories or
agent count alone. Blocks deepen and challenge the already visible whole article. Their
results are integrated into a new article projection at every block stage; a final-only
stitch is not supported.
