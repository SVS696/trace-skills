# Архитектурный анализ и независимая сверка

Этот контракт раскрывает архитектурную часть `P26`. Он включается адресно и не
добавляет новую стадию TRACE.

## Когда нужен архитектор

`spec-preanalysis` ставит `architecture_gate.status=required`, если подтверждён хотя
бы один триггер:

- горизонт `tactical` или `generalized-capability`;
- меняются границы компонента, сервиса, данных или authoritative owner;
- появляется интеграция, новый API либо решение sync/async/transport;
- меняются storage, lifecycle, consistency, transaction, idempotency, migration или rollback;
- затронуты security, RBAC/ABAC, multitenancy или audit;
- существенно меняются performance, availability или scaling;
- вводится новый service, storage, infrastructure element либо требуется ADR.

Отсутствие триггера фиксируется как `not-required` с причиной. Название технического
слоя само по себе триггером не является.

## Design pass

Свежий `spec-solution-architect` получает brief, source index, проектный архитектурный
канон, `solution_boundary` и точный список триггеров. Он возвращает один schema-1 JSON
design artifact с `mode=design`, своим `actor.role/run_id`, `status=designed`, списком
`triggers`, непустым `decisions` и пустым `gaps`. Каждое decision содержит `id`,
`surface`, `decision` и `reason`. Содержательно он фиксирует:

- выбранные границы и authoritative owners;
- интерфейсы, данные, lifecycle и качества только для сработавших поверхностей;
- реализационный переход: что эволюционирует, что заменяется, когда старое удаляется;
- migration/rollback и ADR decision points, если они действительно нужны;
- gaps и прямые вопросы вместо придуманных проектных фактов.

Архитектор не меняет бизнес-цель, требования или acceptance boundary. Проектный канон
выше общей методики. `decomposition-decision.json` связывает design path, SHA-256 и
`design_run_id`; `caseflow init` проверяет сам artifact, а не только наличие файла.

## Conformance pass

На stage 4 другой запуск той же роли в режиме `conformance` сравнивает точные bytes
статьи с утверждённым design artifact. Он не перепроектирует решение и возвращает:

```json
{
  "schema": 1,
  "mode": "conformance",
  "actor": {"role": "spec-solution-architect", "run_id": "fresh-run"},
  "subject": {"path": "article.md", "sha256": "..."},
  "design_sha256": "...",
  "status": "conform",
  "findings": []
}
```

При расхождениях `status=changes-required`, а каждый finding имеет `id`, `target`,
`change`, `reason` и входит по `source_finding_id` в единый stage-4 diff-pool.
Intentional deviation закрывается новым решением/ADR, а не молчаливым исправлением
design или статьи.
