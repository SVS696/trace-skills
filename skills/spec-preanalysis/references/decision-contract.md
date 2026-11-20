# Решение о составе постановок

Для нового `decomposition-decision.json` используй схему 3. Схемы 1 и 2 поддерживаются при чтении ранее начатых кейсов.

Пример описывает условную задачу. Для рабочего решения нужны сведения проекта.

```json
{
  "schema": 3,
  "subject_id": "TASK-123",
  "status": "proposed",
  "decision_ref": "",
  "decision": "single",
  "reason": "Результат можно принять одним сценарием сохранения черновика.",
  "shared_context": [],
  "unknowns": [],
  "articles": [
    {
      "id": "TASK-123",
      "title": "Ошибка сохранения черновика с пустым названием",
      "goal": "Пользователь видит, какое поле нужно заполнить.",
      "outcome": "Форма указывает пустое обязательное поле после попытки сохранения.",
      "acceptance_boundary": "Пользователь исправляет название и повторяет сохранение.",
      "dependencies": [],
      "composition": "article-led",
      "solution_boundary": {
        "horizon": "bounded-systemic",
        "observed_case": "При пустом названии пользователь получает общее сообщение об ошибке сохранения.",
        "root_capability": "Пользователь сохраняет черновик сценария.",
        "invariants": ["Сервис сценариев проверяет обязательные поля."],
        "confirmed_variants": [
          {"name": "Сохранение черновика с пустым названием", "evidence_refs": ["SRC-001"]}
        ],
        "hypothesized_variants": [],
        "current_scope": ["Если название пустое, форма указывает поле, которое нужно заполнить."],
        "extension_seams": ["Форма использует существующее сопоставление кода ошибки и поля."],
        "extension_seam_absence_reason": null,
        "deferred_variants": [],
        "expansion_triggers": ["Появился второй подтверждённый потребитель сведений об ошибке."],
        "horizon_evidence": {
          "analogy_search_refs": ["SRC-001"],
          "roadmap_refs": [],
          "irreversibility_refs": []
        },
        "hotfix_exception": null,
        "implementation_transition": {
          "status": "selected",
          "mode": "evolve-in-place",
          "authoritative_owner": "scenario-service",
          "superseded_paths": [],
          "coexistence_reason": null,
          "stages": [],
          "retirement_trigger": null,
          "rollback_boundary": null,
          "evidence_refs": ["SRC-001"],
          "reason": "Сервис уже возвращает ошибку проверки названия."
        }
      },
      "architecture": {
        "status": "not-required",
        "triggers": [],
        "design_ref": null,
        "design_sha256": null,
        "design_run_id": null,
        "reason": "Компоненты, владельцы, API и хранение данных сохраняются. Других архитектурных условий в примере нет."
      },
      "blocks": [
        {"id": "B01", "title": "Обработка пустого названия"},
        {"id": "B02", "title": "Повторное сохранение после исправления"}
      ]
    }
  ]
}
```

1. Исполнитель предварительного анализа записывает `proposed` и оставляет `decision_ref` пустым. Когда пользователь выбрал вариант, ведущий агент записывает `approved` и ссылку на фактическое решение пользователя или проекта.
2. Для `single` укажи одну статью. Для `split` укажи как минимум две. Для каждой статьи задай `article-led` и хотя бы один смысловой блок. Идентификатор `ARTICLE` зарезервирован для этапов работы над полным текстом. В зависимостях указывай идентификаторы статей. Проверь, что циклов нет.
3. Для каждой статьи заполни `solution_boundary` по [правилам записки](brief-contract.md). Независимые результаты могут иметь разные горизонты. При создании кейса TRACE копирует границу выбранной статьи в `case.json` и передаёт её в контекст постановки и реализации.
4. Укажи `architecture.status=designed|not-required`. Для готового [архитектурного решения](../../../rules/architecture-analysis.md) нужны условия, путь, SHA-256 и `design_run_id` автора. Если решение не требуется, укажи причину и `null` для привязки. До создания кейса `caseflow init` сверяет точные байты обязательного решения. На этапе 4 другой запуск роли проверяет статью по этой версии.
