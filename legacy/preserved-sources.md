# Сохранённые источники старого процесса

| Система | GitHub | Принятый branch | Зафиксированный SHA |
|---|---|---|---|
| Vigers | https://github.com/SVS696/vigers-skill | `main` | `62bb3275ec3a56a8e37ea6f1218c89120389fb6a` |
| Delivery Engineering | https://github.com/SVS696/delivery-engineering-skill | `main` | `56a93cb0c3e4021e099238dde1606344ab590dad` |

Роли агентов, их Codex/Claude adapters, contracts, validators и история остаются в
этих репозиториях. Локальный Vigers содержит спорный незакоммиченный diff; он намеренно
не входит в зафиксированный GitHub SHA и не должен публиковаться как принятое решение.

## Локальный архив после отключения discovery

| Содержимое | Путь |
|---|---|
| Репозиторий Vigers с dirty worktree | `~/.codex/legacy-workflows/2026-09-02/repos/vigers` |
| Репозиторий Delivery Engineering | `~/.codex/legacy-workflows/2026-09-02/repos/delivery-engineering` |
| Снимки установленных Codex-агентов | `~/.codex/legacy-workflows/2026-09-02/installed-agents/codex` |
| Снимки установленных Claude-агентов | `~/.codex/legacy-workflows/2026-09-02/installed-agents/claude` |
| Выведенные из discovery ссылки | `~/.codex/legacy-workflows/2026-09-02/discovery-links` |

Спорный tracked diff Vigers сохранён с SHA-256
`d55489004f3a253e0d69410d60017adbe695884ee5cf5fd618fdfffe2f12162f`.
Хеш проверен до и после переноса. Diff не коммитился и не отправлялся на GitHub.

Исходники всех старых агентов находятся также в архивных Git-репозиториях. Снимки
старых discovery-ссылок нужны только как инвентарь: после переноса репозиториев часть
из них ожидаемо неработоспособна и не должна возвращаться в активный discovery.
