# Проектные адаптеры

`setups/rtl.json` и `setups/haeze.json` не копируют проектные доктрины в эту
экосистему. Они фиксируют шесть маршрутов, включая `method-library`, имя переменной
окружения с project root и fingerprint действующего шаблона,
локальные системы публикации и требование явного выбора после постановки.

При старте модель сначала читает проектные `CLAUDE.md` и `AGENTS.md`, затем активный
workflow-скилл. Источники правды, правила Redmine/Jira/Confluence, паспорта, git и
публикация остаются проектными. TRACE владеет только способом организации
анализа, интеграционных барьеров и required diff.

Проверка адаптера:

```bash
RTL_PROJECT_ROOT=/absolute/path/to/RTL python3 scripts/validate_setup.py setups/rtl.json
HAEZE_PROJECT_ROOT=/absolute/path/to/HAEZE python3 scripts/validate_setup.py setups/haeze.json
```

Если fingerprint шаблона изменился, проверка падает. Обновление fingerprint допустимо
только после отдельного осознанного изменения проектного шаблона; текущая миграция
шаблоны не меняет.
