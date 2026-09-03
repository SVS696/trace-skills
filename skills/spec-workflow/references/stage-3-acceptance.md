# Stage 3: Acceptance

**Entry:** Stage 2 diff-pool is closed and case stage is `3`.

1. Each block writes measurable AC, acceptance scenarios, DoD evidence and trace links
   to the behavior it proves.
2. Register all `stage-03.md` artifacts.
3. At the stitch barrier, check end-to-end journeys, cross-block failure paths,
   duplicated or contradictory AC, missing observability and evidence ownership.
4. Record all corrections in the one stage 3 diff-pool.
5. Treat every `blocked` requirement or AC as a blocking input unless evidence proves it
   is external readiness or implementation-only and cannot change the acceptance contract.
   A named owner is not resolution. Research it, ask the user directly, or obtain the
   external evidence through the same diff item.
6. For cross-layer behavior, split proof by observable contour: direct BE/API or service
   evidence for provider guarantees, FE/UI evidence for client behavior, and E2E only
   for their composition. A hidden control on FE does not prove server authorization;
   a successful Backend response does not prove rendering, local-state or error behavior.

**Exit:** Every requirement has observable acceptance evidence and every end-to-end
scenario crosses block seams without a gap. No requirement or AC remains `blocked`
because its content is incomplete, and no layer's evidence substitutes for another's.
