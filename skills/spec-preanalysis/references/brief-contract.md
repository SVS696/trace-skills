# Preliminary brief contract

`preanalysis-brief.json` uses schema 1 and contains:

- `subject_id`;
- `sources`: stable `id`, `kind`, and `ref` entries;
- `problem`, `goal`, and `solution_hypothesis`, each with `statement` and
  `evidence_refs`;
- `preliminary_user_stories`: `id`, `actor`, `need`, and `value`;
- `scope_in`, `scope_out`, `unknowns`, `assumptions`, and `dependencies` arrays;
- `estimate`.

An estimate is either:

```json
{"status":"estimated","min":3,"max":6,"unit":"working_days","confidence":"low","basis":["source-or-assumption"]}
```

or:

```json
{"status":"unavailable","reason":"Implementation contour is not known yet"}
```

The estimate is a forecast, not a timer event or commitment date.
