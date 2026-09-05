# Stage 2: Behavior and contracts

**Entry:** Stage 1 diff-pool is closed and case stage is `2`.

1. Each block reads the stage 1 article projection, its bounded sources and source map,
   then challenges and deepens user/system scenarios, rules, states, data, interfaces
   and errors for that semantic concern. It returns exact article targets and proposed
   normative changes, not a standalone mini-specification.
   If its materialized route activates a diagram surface, load only
   `rules/diagram-contract.md` and return an explicit diagram decision.
2. Register all `stage-02.md` artifacts.
3. The integration editor applies compatible block contributions to a new immutable
   stage 2 article projection. At the stitch barrier, compare cross-block state
   transitions, shared data ownership, terminology, interface direction, error behavior
   and duplicate rules against the whole article.
4. Put all required corrections into the one stage 2 diff-pool and register the gate
   with `record-stitch --article articles/stage-02.md`. Reusing or overwriting the stage 1
   projection is rejected.
5. If behavior depends on missing evidence or a product choice, classify it and put it
   in that pool as a blocking input. Ask the direct question instead of drafting around it.
6. When behavior crosses technical layers, record in the existing template sections:
   - a short change scope for each affected layer;
   - one authoritative owner for each guarantee and what other layers explicitly do not own;
   - contract direction, transmitted data, sender duty and receiver duty;
   - for FE calls, the exact screen/trigger, mutable method or path, and response use;
   - error, retry/read-back and stale-response behavior at the boundary.
   Do not invent a layer, endpoint or UI surface that current evidence does not support.

**Exit:** The stage 2 article projection contains the integrated behavioral depth;
cross-block behavior composes into one system model; no requirement-relevant
input remains unresolved outside the pool, every blocking input is verified before
advance, and every cross-layer guarantee has one owner plus an explicit consumer duty.
