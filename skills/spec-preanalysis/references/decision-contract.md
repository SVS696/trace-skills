# Decomposition decision contract

```json
{
  "schema": 1,
  "subject_id": "TASK-123",
  "status": "proposed",
  "decision_ref": "",
  "decision": "single",
  "reason": "One independently acceptable product outcome",
  "shared_context": [],
  "unknowns": [],
  "articles": [
    {
      "id": "TASK-123",
      "title": "Reader-facing title",
      "goal": "One goal",
      "outcome": "Observable result",
      "acceptance_boundary": "What can be accepted independently",
      "dependencies": [],
      "composition": "hybrid",
      "blocks": [
        {"id": "B01", "title": "First semantic concern"},
        {"id": "B02", "title": "Second semantic concern"}
      ]
    }
  ]
}
```

The preanalysis agent always emits `proposed` with an empty `decision_ref`. Only the
parent records `approved` and the real user or project decision reference after the
user has chosen the decomposition.

`single` requires exactly one article; `split` requires at least two. `article-first`
requires the sole block `ARTICLE`; `hybrid` requires at least two blocks. Dependencies
refer to article ids and must be acyclic.
