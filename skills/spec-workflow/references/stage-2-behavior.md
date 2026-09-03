# Stage 2: Behavior and contracts

**Entry:** Stage 1 diff-pool is closed and case stage is `2`.

1. Each block reads its own stage 1 artifact and the stage 1 stitch, then describes
   user/system scenarios, rules, states, data, interfaces and errors for that block.
2. Register all `stage-02.md` artifacts.
3. At the stitch barrier, compare cross-block state transitions, shared data ownership,
   terminology, interface direction, error behavior and duplicate rules.
4. Put all required corrections into the one stage 2 diff-pool.
5. If behavior depends on missing evidence or a product choice, classify it and put it
   in that pool as a blocking input. Ask the direct question instead of drafting around it.
6. When behavior crosses technical layers, record in the existing template sections:
   - a short change scope for each affected layer;
   - one authoritative owner for each guarantee and what other layers explicitly do not own;
   - contract direction, transmitted data, sender duty and receiver duty;
   - for FE calls, the exact screen/trigger, mutable method or path, and response use;
   - error, retry/read-back and stale-response behavior at the boundary.
   Do not invent a layer, endpoint or UI surface that current evidence does not support.

**Exit:** Cross-block behavior composes into one system model; no requirement-relevant
input remains unresolved outside the pool, every blocking input is verified before
advance, and every cross-layer guarantee has one owner plus an explicit consumer duty.
