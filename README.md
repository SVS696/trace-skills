# Workflow Skills

Небольшая экосистема скиллов для подготовки постановок и последующей разработки.
Она заменяет активные Vigers и Delivery Engineering, но не переписывает их историю.

## Что меняется

- Шаблон статьи остаётся неизменяемым каркасом результата.
- Анализ идёт по блокам, но блоки не становятся самостоятельными постановками.
- Процесс состоит из четырёх стадий. После каждой стадии все блоки сшиваются.
- Найденные расхождения попадают в один `required-diff.json` текущей стадии.
- Исправления ограничены пунктами этого diff и подтверждаются receipts.
- После сборки единой статьи её diff проходит стандартную сходимость `revmux`.
- Разработка запускается отдельно только после явного решения `delivery`; иначе процесс
  заканчивается на готовой постановке.

## Состав

| Компонент | Назначение |
|---|---|
| `method-library` | Адресная материализация книжных правил Vigers и Delivery |
| `spec-preanalysis` | Сбор данных, problem framing, предварительные US, оценка, план и декомпозиция |
| `spec-workflow` | Четыре стадии постановки и сборка единой статьи |
| `delivery-workflow` | Опциональная разработка с теми же integration barriers |
| `process-timer` | Независимый журнал времени и событий для Work Metrics |
| `legacy-case-migration` | Пересмотр незавершённых кейсов старого процесса |
| `scripts/caseflow.py` | Машинное состояние стадий, diff-pool и переходы |
| `scripts/work_timer.py` | Append-only события времени без зависимости от Vigers |
| `agents/` | Узкие роли, загружаемые только при конкретном назначении |
| `rules/process-kernel.md` | Компактные накопленные инженерные инварианты |
| `library/` | Pinned методические дистилляты с routing и hash-проверкой |

Подробное решение описано в [архитектуре](docs/architecture.md). Сравнение блочной
работы и article-first подхода находится в [исследовании](research/block-vs-article.md),
а замеры контекста и независимые forward-тесты — в
[проверке понятности](research/model-context-evaluation.md).
Происхождение и способ сохранения книжных и накопленных правил описаны в
[карте правил](docs/rule-preservation.md).

## Быстрый старт

```bash
python3 scripts/caseflow.py init \
  --case-root .workflow/cases/CASE-123 \
  --template /absolute/path/to/current-template.md \
  --decision /absolute/path/to/decomposition-decision.json \
  --article-id CASE-123

python3 scripts/caseflow.py status --case-root .workflow/cases/CASE-123
python3 scripts/caseflow.py context --case-root .workflow/cases/CASE-123
```

Команда `context` возвращает ограниченный read-set текущей стадии. Модель не должна
загружать весь репозиторий скиллов или все материалы кейса.

## Старый процесс

Исторические репозитории остаются источниками старой реализации:

- [SVS696/vigers-skill](https://github.com/SVS696/vigers-skill)
- [SVS696/delivery-engineering-skill](https://github.com/SVS696/delivery-engineering-skill)

Локальные спорные изменения Vigers не публикуются как принятая версия. При отключении
старого discovery их dirty worktree сохраняется локально целиком.
