# Preliminary brief contract

`preanalysis-brief.json` uses schema 1 and contains:

- `subject_id`;
- `sources`: stable `id`, `kind`, and `ref` entries;
- `problem`, `goal`, and `solution_hypothesis`, each with `statement` and
  `evidence_refs`;
- `preliminary_user_stories`: `id`, `actor`, `need`, and `value`;
- `scope_in`, `scope_out`, `unknowns`, `assumptions`, and `dependencies` arrays;
- `estimate`.

Every `unknowns` entry is an object with `id`, `statement`, `disposition`,
`blocks_specification`, and `reason`. Allowed dispositions are:

- `researchable`: the agent must continue evidence collection;
- `user-decision`: include the exact direct `question` for the user;
- `external-owner`: include the exact `owner_ref` whose evidence is required;
- `implementation-only`: only when the answer cannot change observable requirements,
  scenarios or AC.

`researchable` and `user-decision` are always blocking. `implementation-only` is never
blocking. `external-owner` may be either, but a blocking external input must later enter
the earliest applicable stage diff until its evidence is incorporated and verified.

An estimate is either:

```json
{"status":"estimated","min":3,"max":6,"unit":"working_days","confidence":"low","basis":["source-or-assumption"]}
```

or:

```json
{"status":"unavailable","reason":"Implementation contour is not known yet"}
```

The estimate is a forecast, not a timer event or commitment date.
