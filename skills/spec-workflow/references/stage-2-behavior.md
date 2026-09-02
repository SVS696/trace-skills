# Stage 2: Behavior and contracts

**Entry:** Stage 1 diff-pool is closed and case stage is `2`.

1. Each block reads its own stage 1 artifact and the stage 1 stitch, then describes
   user/system scenarios, rules, states, data, interfaces and errors for that block.
2. Register all `stage-02.md` artifacts.
3. At the stitch barrier, compare cross-block state transitions, shared data ownership,
   terminology, interface direction, error behavior and duplicate rules.
4. Put all required corrections into the one stage 2 diff-pool.

**Exit:** Cross-block behavior composes into one system model, or remaining conflicts
are explicit open diff items.
