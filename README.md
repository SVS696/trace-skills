# TRACE

**Traceable Requirements Analysis, Composition & Engineering**

TRACE — наследник Vigers, Delivery Engineering & Co.

Он объединяет их полезные правила, узкие агентские роли, таймер, валидаторы и
методические библиотеки для подготовки постановок и последующей разработки. Git-история
предшественников сохраняется, а их активную оркестрацию заменяет ограниченный по
контексту поэтапный процесс.

## Рабочий порядок

Самостоятельное исследование, сравнение решений или восстановление их оснований ведёт
`analysis-workflow`. Оно даёт проверяемый аналитический результат без обязательной
постановки и разработки. Передачи между участниками и проектные источники определяет
[контракт передачи](rules/handoff-contract.md); конкретный проект сохраняет свой канон.

Преданализ устанавливает источники, проблему, цель, суть решения, preliminary US/DoD,
границу решения и план. После утверждения каждая статья проходит whole-template
foundation, behavioral depth, acceptance и final article. Каждая интеграция сохраняет
новый snapshot; pre-review authoring и deterministic checks не создают diff-pool.

Независимый цикл один: article → revmux → findings → diff-pool → fix article →
article v2 → обычный revmux. Исправление источника без исправления статьи не закрывает
finding. Отдельная targeted verification не выполняется. Предел — пять содержательных
revmux rounds с ранней остановкой на clean или явно показанном minor residual.

Выбирается шаблон основной постановки или компонентной подзадачи. Указываются только
изменяемые компоненты; нет пустых «Изменений нет». Delivery, публикация и приёмка
остаются отдельными маршрутами и фактами. Подробности — в docs/architecture.md.

## Состав

| Компонент | Назначение |
|---|---|
| `method-library` | Адресная материализация книжных правил Vigers и Delivery |
| `analysis-workflow` | Самостоятельное исследование, сравнение решений и общий контекст с проверенными основаниями |
| `spec-preanalysis` | Coverage источников, template-independent проблема/цель/суть решения, предварительные US/DoD, оценка, план и декомпозиция |
| `spec-workflow` | Сквозной черновик, поблочное углубление и контрольные проекции статьи |
| `delivery-workflow` | Опциональная разработка с теми же integration barriers |
| external `OpenSpec` | Обязательный пакет изменения на входе в новую разработку |
| `process-timer` | Независимый журнал времени и событий для Work Metrics |
| external `Smoke Break` | Runtime-зависимость для `P23 COURSE-CHECK` в длинном turn |
| `legacy-case-migration` | Пересмотр незавершённых кейсов старого процесса |
| `scripts/caseflow.py` | Машинное состояние стадий, diff-pool и переходы |
| `scripts/work_timer.py` | Append-only события времени без зависимости от Vigers |
| `agents/` | Узкие роли, загружаемые только при конкретном назначении |
| `rules/process-kernel.md` | Компактные накопленные инженерные инварианты |
| `library/` | Pinned методические дистилляты с routing и hash-проверкой |

Peer-gates `simplicity-spec`, `humanizer` и `simplicity-code` остаются самостоятельными узкими
скиллами и вызываются только в соответствующей точке процесса; их документация не
загружается в остальные стадии.

Каждый проход оставляет наблюдаемый отчёт по
[контракту quality-pass](rules/quality-pass.md). Это один
отчёт на проход, а не новая стадия workflow.

Автоматический временной course check зависит от
[Smoke Break](https://github.com/ElKornacio/agent-plugins/tree/511e18062c95d746bed7ff0ca300fbcbd31fc57f/plugins/smoke-break).
Codex использует upstream-плагин, а для Claude Code репозиторий содержит совместимый
[адаптер](integrations/smoke-break/README.md). Рекомендуемый интервал TRACE — 15 минут;
общий файл конфигурации — `~/.smoke-break.env`. Без плагина остальные gates TRACE
работают, но автоматического временного trigger нет.

Подробное решение описано в [архитектуре](docs/architecture.md). Сравнение блочной
работы и article-first подхода, включая последующую смену решения по производственному
сигналу, находится в [исследовании](research/block-vs-article.md),
а замеры контекста и независимые forward-тесты — в
[проверке понятности](research/model-context-evaluation.md).
Происхождение и способ сохранения книжных и накопленных правил описаны в
[карте правил](docs/rule-preservation.md).

## Быстрый старт

Для разработки нужен [OpenSpec](https://github.com/Fission-AI/OpenSpec): Node.js
>=20.19.0, OpenSpec >=1.13.0,<2.0.0; проверенная версия — 1.13.0. Анализ и подготовка
постановки работают без него. Установить CLI и проверить доступность:

```bash
npm install -g @fission-ai/openspec@1.13.0
python3 scripts/openspec_bridge.py
```

На входе в разработку следовать [контракту OpenSpec](skills/delivery-workflow/references/openspec.md).
Новый delivery-кейс связывается с конкретным изменением и проверенной статьёй;
`context` и переходы стадий проверяют пакет повторно. Codex и Claude Code используют
один контракт, а `openspec init --tools codex,claude` создаёт проектные интеграции
обоих харнесов. TRACE сохраняет проверки и управление исполнителями. Галочки
OpenSpec не заменяют результаты тестов, независимое ревью или приёмку.

```bash
python3 scripts/caseflow.py init \
  --case-root .workflow/cases/CASE-123 \
  --template /absolute/path/to/current-template.md \
  --brief /absolute/path/to/preanalysis-brief.json \
  --decision /absolute/path/to/decomposition-decision.json \
  --plan /absolute/path/to/execution-plan.json \
  --article-id CASE-123

python3 scripts/caseflow.py status --case-root .workflow/cases/CASE-123
python3 scripts/caseflow.py context --case-root .workflow/cases/CASE-123
python3 scripts/smoke_break_dependency.py verify
```

Команда `context` возвращает ограниченный read-set текущей стадии. Модель не должна
загружать весь репозиторий скиллов или все материалы кейса.

## Наследие

Vigers и Delivery Engineering остаются отдельными историческими репозиториями:

- [SVS696/vigers-skill](https://github.com/SVS696/vigers-skill)
- [SVS696/delivery-engineering-skill](https://github.com/SVS696/delivery-engineering-skill)

`& Co.` включает перенесённые агентские роли, таймер, проверки, publication guards и
другие процессные инструменты вокруг этих двух систем. Их полезные правила входят в
TRACE адресно; старые state machines и универсальные контекстные пакеты не продолжаются.

Локальные спорные изменения Vigers не публикуются как принятая версия. При отключении
старого discovery их dirty worktree сохраняется локально целиком.

Внутренний путь установки `~/.workflow-skills/current` пока сохранён для совместимости
с уже установленными агентами и незавершёнными кейсами. Публичное имя системы и
репозитория — TRACE.
