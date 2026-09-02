# Decomposition decision contract

```json
{
  "schema": 1,
  "subject_id": "TASK-123",
  "status": "approved",
  "decision_ref": "user-message-or-project-decision",
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

`single` requires exactly one article; `split` requires at least two. `article-first`
requires the sole block `ARTICLE`; `hybrid` requires at least two blocks. Dependencies
refer to article ids and must be acyclic.
