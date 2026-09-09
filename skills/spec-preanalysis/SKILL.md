---
name: spec-preanalysis
description: >-
  Use before specification authoring to collect preliminary evidence, frame the
  problem, goal and solution essence, draft user stories, estimate a range, build
  a plan, decide one or several specifications, and design semantic analysis blocks.
  Not for writing the final specification or implementing it.
allowed-tools: Read Glob Grep Write Bash Task AskUserQuestion
---

# Specification pre-analysis

## Essential principles

Read [the process kernel](../../rules/process-kernel.md) once for the task. Use
`method-library` to materialize only the applicable requirements route; never preload
the Vigers reference corpus.

1. **Discover before routing.** Build a compact evidence-backed brief before deciding
   how many specifications or blocks exist.
2. **Frame independently of the template.** Problem, goal, solution essence and
   preliminary user stories are mandatory preanalysis answers even when the selected
   article template has no matching headings. The template consumes the answers; it
   does not define whether they exist.
3. **Decide deliverables before blocks.** First determine whether the subject produces
   one independently acceptable result or several. Blocks cannot answer that question.
4. **Split by outcome, not implementation layer.** Backend/frontend, screens, teams or
   convenient agent assignments are not enough to create separate specifications.
5. **Start from the whole, then descend.** Every specification first gets a complete
   working pass through the unchanged template. Semantic blocks are chosen only as
   later depth lenses; they never become the starting deliverables.
6. **Keep the template unchanged.** The decision maps work to the existing template;
   it does not redesign it.
7. **Separate forecast from fact.** Estimates are ranges with basis and confidence;
   observed time remains owned by `process-timer`.
8. **The user owns scope and external writes.** Produce recommendations first. Publish
   a plan to Singularity or another system only when authorized, then read it back.

## When to use

- A new task may contain several independent product outcomes.
- A large proposed specification may need to be split into several articles.
- It is unclear whether block work will help or only add integration overhead.
- An old case is re-baselined and its original decomposition may no longer be valid.

## When not to use

- A decision file is already approved and the subject has not changed.
- The request is a tiny local edit to one known article.
- The user asks only for implementation: use `delivery-workflow` from an existing
  `spec_ready` case.
- The task is old-process migration: inventory it with `legacy-case-migration`, then return here.

## Workflow

### Phase 1: Collect preliminary evidence

**Entry:** A task brief and current template are available.

1. Build a source index. For every search record the exact query, authority, result
   (`found|negative|unavailable`), timestamp and freshness. Classify facts,
   contradictions and assumptions. Maintain explicit coverage surfaces and stop broad
   discovery when their verdict is `sufficient`; reopen research only for an exact gap
   or falsifying question. For every unknown,
   choose exactly one disposition: continue research, ask the user a direct question,
   request evidence from a named external owner, or prove that it is implementation-only.
2. Materialize the applicable requirements method route, normally `scope-users` or
   `elicitation`, and pass its path/hash to `spec-preanalyst`.
3. Before routing or using template headings as a content checklist, read the framing
   section of [brief-contract.md](references/brief-contract.md). Explicitly ask and
   answer its four template-independent questions: problem and negative consequence;
   goal and benefit; solution essence, behavior change and why it removes the problem;
   preliminary user stories with actor, need and value. Answer from evidence when
   possible. If an answer that can change scope is missing, classify the gap and return
   the exact direct question instead of inventing or decorating an answer.
4. Draft evidence-linked preliminary DoD with confidence. Preliminary status means the
   answers may be revised by full analysis; it does not make any of the four answers
   optional.
5. Read [the solution-boundary contract](../../rules/solution-boundary.md). Classify the
   hypothesis as `tactical`, `bounded-systemic` or `generalized-capability`; record the
   root capability, invariants, confirmed and hypothesized variants, current scope,
   extension seams or their absence reason, deferred variants and expansion triggers.
   Treat `bounded-systemic` as the default, not as a compromise chosen without analysis.
   Select the implementation transition (`evolve-in-place|replace-and-remove|staged-migration`)
   or explicitly mark it not applicable, and pass the contract path/hash to
   `spec-preanalyst`.
6. Evaluate the triggers in `rules/architecture-analysis.md`. If triggered, assign a
   fresh `spec-solution-architect` design run before decomposition approval and bind its
   output path/hash to each affected article. Otherwise record `not-required` with reason.
7. Run `simplicity-spec` on the solution essence and candidate decomposition.
   Remove or defer every mechanism that lacks a current requirement; preserve its
   protected minimum, including an evidence-backed extension seam. This is a semantic
   solution pass, not prose cleanup.
8. Write the already simplified schema-4 `preanalysis-brief.json` using
   [brief-contract.md](references/brief-contract.md).
9. Record an estimate range with basis and confidence, or explicitly mark it unavailable.
10. Validate with `scripts/preanalysis.py validate-brief`.

**Exit:** A validated preliminary brief exists; facts and hypotheses are distinguishable,
and no unknown remains an unclassified free-form note.

### Phase 2: Decide one specification or several

**Entry:** The preliminary brief is valid.

Read [routing-criteria.md](references/routing-criteria.md). Recommend `single` unless
two or more outcomes can be accepted and handed off independently without duplicating
the same normative rules. For `split`, produce an acyclic dependency graph, name the
shared context once, and derive a separate evidence-backed solution boundary for each
article instead of forcing the subject-level preliminary horizon onto all of them.

**Exit:** Every proposed article has its own goal, outcome and acceptance boundary.

### Phase 3: Design the block descent

**Entry:** Article boundaries are known.

Set `composition: article-led` for every article. Then define one or more semantic
blocks for the later focused passes. A block represents a coherent risk, rule set,
journey, data lifecycle or interface surface. It does not have to match one template
heading, and it must not exist merely because the implementation has BE and FE parts.

The block map is allowed to be revised after the first whole-template draft exposes a
wrong boundary. Record that as an explicit new decomposition decision; do not silently
change agent assignments inside an active case.

**Exit:** Every article uses `article-led` composition and has a justified semantic
block map for the depth passes.

### Phase 4: Record and approve

**Entry:** Phases 1–3 completed.

1. Write schema-3 `decomposition-decision.json` using
   [decision-contract.md](references/decision-contract.md). Every article carries its
   accepted solution boundary into the specification case.
2. Write schema-2 `execution-plan.json` using [plan-contract.md](references/plan-contract.md).
   Bind it to the exact brief hash; every task has a short reader-facing title for its
   product outcome, source refs and observable exit criteria. Keep stage numbers, block
   IDs and TRACE operations out of the title and in their dedicated fields.
3. Validate all three artifacts.
4. Present the four framing answers, recommendation, estimate range, plan and material
   trade-offs to the user, including the visible `simplicity-spec` result. Batch and ask
   every direct `user-decision` question that can change problem, goal, solution
   essence, preliminary user stories, scope,
   decomposition or acceptance before requesting approval.
5. After the user's choice, approve the decision and plan with exact `decision_ref`.
6. If separately authorized, sync the approved plan through the project's planning
   adapter (for example `singularity-app`) and record the exact read-back receipt.
7. Only then initialize each specification with `caseflow.py init --brief ...`. The
   brief, decision, plan and any architecture design are immutable case inputs.

**Exit:** The brief, approved decomposition and approved plan are valid; any external
sync has a read-back receipt; no final specification prose was drafted.

## Agent

Use `spec-preanalyst` for the bounded read-only recommendation and proposed artifacts.
The parent validates the artifacts, presents trade-offs, records the user's decisions,
and performs any separately authorized external synchronization.

## Success criteria

- Article count follows independent outcomes and acceptance boundaries.
- Problem and its negative consequence, goal and its benefit, and solution essence with
  behavior change plus problem resolution are explicit and evidence-linked regardless
  of article template.
- At least one evidence-linked preliminary user story is present and remains visibly
  preliminary.
- Every preliminary US and preliminary DoD is evidence-linked and must later receive an
  explicit stage-1 disposition; none can disappear during article authoring.
- Estimate is a justified range or an explicit gap, never an invented deadline.
- The plan is acyclic, its task titles are understandable without TRACE internals, and
  external publication is separately authorized and read back.
- Implementation layers did not become article boundaries by default.
- Each article uses `article-led`: whole-template baseline first, semantic blocks later.
- Dependencies are acyclic and shared rules have one owner.
- The approved decision initializes cases without manual reinterpretation.
- The proposed solution and decomposition passed `simplicity-spec`; its simplifications
  or clean result were shown to the user.
- The solution horizon is evidence-backed. `particular-case` and
  `speculative-generalization` were checked independently; the current scope is distinct
  from deferred variants and has a localized extension seam or an explicit absence reason.
- Every unknown has a disposition. Researchable items are investigated before handoff;
  user decisions are direct questions; external inputs name their owner; only details
  that cannot change observable requirements or AC are `implementation-only`.
- Any still-open content input is carried into the earliest applicable authoring open_inputs and
  cannot disappear merely because it has an owner.
- Source coverage has a visible stop verdict, including negative searches and stale or
  unavailable sources; broad research does not continue after `sufficient`.
- Architecture analysis runs only on a recorded trigger, and required design is bound
  by hash before case initialization.
