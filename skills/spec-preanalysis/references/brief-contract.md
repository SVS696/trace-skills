# Preliminary brief contract

New `preanalysis-brief.json` artifacts use schema 4. The validator keeps schemas 1–3
readable for already started cases, but `caseflow init` accepts only schema 4.

Before routing, decomposition, or full analysis, answer these four questions. They are a
preanalysis invariant and do not depend on the selected article template or its headings:

1. **Problem:** who encounters what current difficulty, in which scenario, and what
   concrete negative consequence follows?
2. **Goal:** who receives what observable result, and what benefit does it provide?
3. **Solution essence:** how will system or process behavior change, and why will that
   remove the problem without prematurely selecting implementation details?
4. **Preliminary user stories:** who needs what capability or behavior, and for what
   value?

Answer from evidence when it is sufficient. A technical fact or an absent component is
not a problem without its consequence. A list of changes is not a goal without its
benefit. Technical names are not a solution explanation unless their role in the
behavior is clear. Do not invent a missing consequence, benefit, actor, or mechanism: if
one of the four answers can materially change scope and cannot be established from the
read-set, return `gap`, classify the unknown, and ask the exact direct question. Do not
proceed to routing with an empty or decorative answer.

Schema 4 contains:

- `subject_id`;
- `sources`: stable `id`, `kind`, `ref`, exact `query`, `authority`,
  `status=found|negative|unavailable`, ISO `checked_at` and
  `freshness=current|stale|unknown`;
- evidence-linked `facts` and `contradictions`; a resolved contradiction names its
  resolution;
- `coverage.verdict=sufficient|partial|blocked` and non-empty checked surfaces. Every
  non-covered surface references classified unknown ids through `gap_refs`;
- `problem`: `statement`, non-empty `affected_actors`, non-empty
  `negative_consequences`, and non-empty `evidence_refs`;
- `goal`: `statement`, non-empty `beneficiaries`, non-empty `benefits`, and non-empty
  `evidence_refs`;
- `solution_essence`: `statement`, non-empty `behavior_changes`, a non-empty
  `problem_resolution` explaining why the change removes the problem, and non-empty
  `evidence_refs`. This is still preliminary; uncertainty belongs in evidence,
  assumptions and classified unknowns rather than in a weaker field name;
- `solution_boundary` following `rules/solution-boundary.md`;
- `architecture_gate` following `rules/architecture-analysis.md`;
- at least one `preliminary_user_stories` entry with `id`, `actor`, `need`, `value`,
  non-empty `evidence_refs`, and `confidence=low|medium|high`;
- `preliminary_definition_of_done`: `id`, `criterion`, observable `evidence`,
  non-empty `evidence_refs`, and confidence;
- `scope_in`, `scope_out`, `unknowns`, `assumptions`, and `dependencies` arrays;
- `estimate`.

`solution_boundary` has this compact shape:

```json
{
  "horizon": "bounded-systemic",
  "observed_case": "Current evidence-backed request",
  "root_capability": "Stable user or system capability behind the request",
  "invariants": ["Rule that remains true across confirmed variants"],
  "confirmed_variants": [
    {"name": "Current variant", "evidence_refs": ["SRC-001"]}
  ],
  "hypothesized_variants": [],
  "current_scope": ["Behavior delivered by this decision"],
  "extension_seams": ["Small localized point where a confirmed variant can attach"],
  "extension_seam_absence_reason": null,
  "deferred_variants": [],
  "expansion_triggers": ["A second confirmed consumer appears"],
  "horizon_evidence": {
    "analogy_search_refs": ["SRC-001"],
    "roadmap_refs": [],
    "irreversibility_refs": []
  },
  "hotfix_exception": null,
  "implementation_transition": {
    "status": "selected",
    "mode": "evolve-in-place",
    "authoritative_owner": "current-capability-owner",
    "superseded_paths": [],
    "coexistence_reason": null,
    "stages": [],
    "retirement_trigger": null,
    "rollback_boundary": null,
    "evidence_refs": ["SRC-001"],
    "reason": "The current owner can evolve without a parallel path"
  }
}
```

Every confirmed variant has at least one source reference. `invariants`,
`current_scope`, and `expansion_triggers` are non-empty. `extension_seams` may be empty
only when `extension_seam_absence_reason` explains why no meaningful seam exists.
Hypothesized and deferred variants never justify current scope by themselves.

For `tactical`, `hotfix_exception` is required and contains non-empty `reason`,
`reversibility`, `return_trigger`, and `evidence_refs`. For the other horizons it is
`null`.

`generalized-capability` requires at least two confirmed variants, a source-linked
roadmap, or evidence of an expensive or irreversible future change. A generic mechanism
based only on `hypothesized_variants` is invalid. `bounded-systemic` is the default
horizon for an ordinary task, but still requires the recorded systemic boundary.

This boundary is the preliminary subject-level result. After `single|split` routing,
schema-3 `decomposition-decision.json` carries the applicable boundary on every article.
For `single`, preserve the brief boundary unless later evidence changed it explicitly.
For `split`, derive article-specific boundaries from the same source index; different
independently accepted outcomes may legitimately have different horizons.

`implementation_transition` is `not-applicable` or `selected`. Selected modes are
`evolve-in-place`, `replace-and-remove`, and `staged-migration`. Replacement and staged
migration name superseded paths, retirement trigger and rollback boundary. Staged
migration also gives the evidence-backed coexistence reason and one authoritative owner
for each named stage. The old path never receives new business behavior merely to ease
migration.

`architecture_gate.status=required` names one or more exact triggers from
`rules/architecture-analysis.md`; `not-required` has no triggers and explains why. A
`tactical` or `generalized-capability` horizon always requires architecture analysis.

Coverage is an explicit stopping rule. `sufficient` permits no partial/uncovered
surface and stops broad discovery. More research then needs an exact missing question,
named source surface and stop condition; model curiosity alone is not a reason to widen
the corpus.

Every `unknowns` entry is an object with `id`, `statement`, `disposition`,
`blocks_specification`, and `reason`. Allowed dispositions are:

- `researchable`: the agent must continue evidence collection;
- `user-decision`: include the exact direct `question` for the user;
- `external-owner`: include the exact `owner_ref` whose evidence is required;
- `implementation-only`: only when the answer cannot change observable requirements,
  scenarios or AC.

`researchable` and `user-decision` are always blocking. `implementation-only` is never
blocking. `external-owner` may be either, but a blocking external input must later enter
the earliest applicable authoring open_inputs until its evidence is incorporated before readiness.

An estimate is either:

```json
{"status":"estimated","min":3,"max":6,"unit":"working_days","confidence":"low","basis":["source-or-assumption"]}
```

or:

```json
{"status":"unavailable","reason":"Implementation contour is not known yet"}
```

The estimate is a forecast, not a timer event or commitment date.
