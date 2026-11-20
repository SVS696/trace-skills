# Отчёт о проверке качества

Назначенная роль выполняет проверку и возвращает один отчёт JSON. Привяжи отчёт к точным байтам проверяемого файла и инструкции `SKILL.md`. Чтение инструкции само по себе не подтверждает выполнение проверки.

```json
{
  "schema": 1,
  "gate": "simplicity-spec | humanizer | simplicity-code",
  "actor": {"role": "assigned narrow role", "run_id": "different run"},
  "subject": {"path": "artifact-or-diff", "sha256": "64 hex"},
  "skill": {"path": "/absolute/path/SKILL.md", "sha256": "64 hex"},
  "style_profile": {"path": "/absolute/path/profile.md", "sha256": "64 hex"},
  "outcome": "clean | changes-required",
  "checks": ["checks required by the selected gate"],
  "findings": [
    {"id": "stable-id", "target": "exact location", "change": "exact diff", "reason": "evidence"}
  ]
}
```

Поле `style_profile` обязательно только для `humanizer`. Если замечаний нет, запиши `clean`. Если есть замечания, запиши `changes-required`. Даже при чистом результате перечисли фактические проверки. Автор статьи или кода не может подписать независимый отчёт с тем же `run_id`.

Для технической статьи назначь `humanizer` проверку понятности для указанной аудитории. Предложи конкретное место правки и поясни, какой ответ читателю трудно найти. Сохрани словарь, обязательность и исключения из источника. Цикл скилла относится к предложенной редакции. Автор применяет принятые правки и сверяет их с источником через `utr` или `simplified-technical-english` в режиме проверки. Используй для этого существующий проход. [Порядок редактуры](technical-writing.md)

До ревью автор исправляет рабочую версию статьи напрямую. Независимые проверки статьи выполняй внутри обычного revmux. В общий список исправлений включай только принятые замечания revmux. В разработке используй правила этапа разработки.

После revmux проверяющий разбирает замечания по точной версии отчёта. В `findings` включи каждое подтверждённое замечание с минимальной правкой. В `dismissed_findings` укажи остальные замечания с причиной и подтверждающими сведениями. Каждое замечание должно попасть ровно в один список. Только для такого разбора добавь:

```json
{
  "purpose": "revmux-finding-adjudication",
  "dismissed_findings": [
    {
      "id": "revmux-finding-id",
      "reason": "why it is dismissed",
      "evidence": "exact requirement or execution evidence"
    }
  ]
}
```

| Скилл | Обязательные значения `checks` |
|---|---|
| `simplicity-spec` | `minimum-core`, `seven-step-ladder`, `element-classification`, `rewritten-result` |
| `humanizer` | `draft-rewrite`, `anti-ai-audit`, `final-rewrite` |
| `simplicity-code` | `minimum-core`, `real-flow`, `seven-step-ladder`, `element-classification`, `runnable-result` |

В `element-classification` для `simplicity-spec` укажи, что меняется в каждом техническом блоке и какое требование это обосновывает. Если основания нет, предложи `REMOVE` или `SIMPLIFY`. Оставь в статье новое поведение и изменения контракта. Для необходимой совместимости достаточно короткого условия или ссылки. Перечень всех прежних запросов, ответов и операций CRUD расширяет объём постановки. Пока такой перечень остаётся в проверенной полной статье без основания, результат не может быть `clean`. Для частичной проверки ограничь вывод проверенным файлом и доступными источниками.
