# Аудит переноса аналитических правил Vigers в TRACE без FSM

> Это baseline-аудит TRACE commit `eb039ee`, а не описание состояния после исправлений.
> Выявленный приоритетный пул закрывается текущими schema-3 brief/decision, schema-2
> plan, stage-1 lineage, архитектурным и diagram-контрактами; исторические evidence и
> line references ниже сохранены как основание изменений.

## Граница аудита

- **Subject:** содержательные правила анализа требований и решения.
- **Stage:** независимый evidence-аудит принятого Vigers против текущего TRACE.
- **Вопросы:** какие правила сохранены, перенесены частично, потеряны либо намеренно
  остались вне аналитического контура; какие неполные места имеют наибольшую ценность.
- **Старый baseline:** только Git object
  `62bb3275ec3a56a8e37ea6f1218c89120389fb6a` репозитория Vigers. Dirty working tree
  не использовался.
- **Текущий baseline:** TRACE `eb039ee2527da74b25dc017d5c3f17261b2eacea`.
- **Исключено:** состояния и переходы case machine, epochs, CLI-команды, механические
  hash/barrier gates, telemetry, tracking и чистая оркестрация.

Статусы ниже означают:

- `preserved` — правило остаётся явно достижимым в рабочем аналитическом маршруте;
- `partial` — смысл присутствует, но обязательность, evidence-контракт либо часть
  поверхности ослаблена;
- `missing` — в текущем read-set нет рабочего эквивалента;
- `intentionally out of analytical scope` — старое правило относится к исключённой
  механике либо сознательно заменено новым владельцем, а не забыто.

Обозначение `V:` — путь и строки в pinned Vigers SHA; `T:` — путь и строки текущего
TRACE.

## Итог

Книжная база Вигерса сохранена хорошо: семь зеркал совпадают byte-for-byte с pinned
Vigers, `rule_library.py validate` подтверждает 23 requirements-route и достижимость
всех 70 нативных `C/T/D` правил. Основной метод анализа требований также совпадает
побайтно.

Но утверждение «все полезные не-FSM правила анализа перенесены» было бы неверным.
Обнаружены шесть существенных разрывов: сам handoff preliminary brief в
specification case, полноценная coverage-модель предварительного исследования,
lineage предварительных US/DoD, качественный контракт плана, архитектурная граница
вместе с судьбой существующей реализации и полный diagram contract. Reader
projection и набор независимых review-lenses перенесены лишь частично.

## Матрица правил

| ID | Правило Vigers | Статус TRACE | Evidence и вывод |
|---|---|---|---|
| A01 | Проектный канон и актуальные источники выше общей методики; предположение или старый тикет не становятся фактом | `preserved` | V: `references/requirements-method.md:30-45`, `SKILL.md:13-16`. T: `rules/process-kernel.md:7-14`, `library/requirements/references/requirements-method.md:30-45`, `rules/process-kernel.md:52-55`. |
| A02 | Progressive disclosure: один маршрут, сначала дистиллят, ограниченный fallback только под точный пробел | `preserved` | V: `references/requirements-method.md:47-120`. T: идентичный `library/requirements/references/requirements-method.md:47-120`; рабочий владелец материализации — `skills/method-library/SKILL.md:15-17,29-55`. |
| A03 | Не смешивать факты, интерпретации, гипотезы, assumptions, contradictions и unknowns; не закрывать неизвестное догадкой | `preserved` | V: `agents/contracts/system-analyst.md:24-38,42-49`, `references/requirements-method.md:199-216`. T: `rules/process-kernel.md:9-14`, `agents/contracts/spec-preanalyst.md:12-18`, `agents/contracts/spec-evidence-analyst.md:17-25`. Ослабление хранения этих категорий в preliminary artifact разобрано отдельно в A04. |
| A04 | Исследование начинается с search matrix; сохраняются запросы и отрицательные результаты, exact ref, authority/status/freshness, contradictions, gaps и coverage verdict `sufficient\|partial\|blocked` | `partial` | V: `references/planning-contract.md:61-82`, `agents/contracts/planner.md:49-58`. T: `skills/spec-preanalysis/SKILL.md:52-61` требует source index и классификацию, но `skills/spec-preanalysis/references/brief-contract.md:6-15` хранит лишь `sources{id,kind,ref}` и не задаёт executed query, negative result, authority, freshness, facts, contradictions или coverage verdict; validator также проверяет у source только `id/ref/kind` (`scripts/preanalysis.py:191-215`). |
| A05 | Сначала problem, user/stakeholders, effect, facts и unknowns; цель — наблюдаемый результат; scope in/out, dependencies, success proxy и business risk | `preserved` | V: `references/requirements-method.md:199-247`. T: идентичный `library/requirements/references/requirements-method.md:199-247`; предварительный слой дополнительно требует evidence-linked problem/goal/hypothesis и scope/dependencies в `skills/spec-preanalysis/references/brief-contract.md:8-15`. |
| A06 | Предварительные User Stories остаются гипотезами, имеют actor/goal/value, source refs и confidence | `partial` | V: `references/planning-contract.md:99-135`, `agents/contracts/planner.md:91-96`. T: `skills/spec-preanalysis/SKILL.md:62-64,139-142` сохраняет предварительный статус; `skills/spec-preanalysis/references/brief-contract.md:13` оставляет actor/need/value, но теряет source refs и confidence каждой истории, что подтверждает machine validator `scripts/preanalysis.py:218-231`. |
| A07 | Полный анализ обязан дать disposition каждой preliminary US/DoD: `confirmed\|changed\|split\|rejected`, не переписывая planning snapshot | `missing` | V: `references/planning-contract.md:147-151`, `agents/contracts/system-analyst.md:71-78`. T: stage 1 получает preanalysis artifacts (`skills/spec-workflow/references/stage-1-foundation.md:6-8`), но ни stage contract, ни `agents/contracts/spec-article-editor.md:9-29`, ни `agents/contracts/spec-block-analyst.md:9-28` не требуют disposition предварительных историй. |
| A08 | Предварительный анализ формирует source-linked preliminary DoD как гипотезу, отличную от финальных AC/DoD | `missing` | V: `references/planning-contract.md:99-135`, `agents/contracts/planner.md:91-96`. T: schema brief перечисляет только `preliminary_user_stories` и затем `estimate` (`skills/spec-preanalysis/references/brief-contract.md:6-15`); preliminary DoD отсутствует. Финальный DoD сохранён отдельно, см. A20. |
| A09 | Плановый шаг имеет самостоятельный outcome, dependencies, exit criteria и source refs; checklist не заменяет план | `partial` | V: `references/planning-contract.md:84-97`, `agents/contracts/planner.md:71-84`. T: `skills/spec-preanalysis/references/plan-contract.md:3-22` оставляет `id/title/output/depends_on`, но не содержит exit criteria, source refs или проверяемый состав результата. Ацикличность сохранена (`:25-29`). |
| A10 | Декомпозиция сохраняет одну бизнес-цель и не делит результат только по компонентам; границы определяются самостоятельной приёмкой | `preserved` | V: `references/requirements-method.md:182-197`. T: `rules/process-kernel.md:23-26`, `skills/spec-preanalysis/SKILL.md:19-29,82-108`, `skills/spec-preanalysis/references/routing-criteria.md:3-31`. Правило сохранено в новой article-led форме; это содержательная замена старого block-first подхода, а не его потеря. |
| A11 | Двусторонняя solution boundary: три горизонта, доказанная extension seam, оба запаха, expansion trigger и protected minimum | `preserved` | V: `references/solution-boundary-contract.md:3-74,101-147`. T: `rules/process-kernel.md:15-22`, `rules/solution-boundary.md:8-69`, `skills/spec-preanalysis/references/brief-contract.md:17-55`. |
| A12 | При уже существующей способности анализ выбирает `evolve-in-place\|replace-and-remove\|staged-migration`, называет authoritative owner, superseded paths, rollback/cutover и retirement trigger | `missing` | V: `references/solution-boundary-contract.md:76-99`, `agents/contracts/solution-architect.md:62-71`. В T `rules/solution-boundary.md:13-73` и schema boundary `skills/spec-preanalysis/references/brief-contract.md:17-55` завершаются на horizon/seams/triggers; repo-wide поиск `implementation_transition`, трёх transition-mode и `retirement_trigger` не дал рабочего TRACE-правила. Общие слова migration/rollback в книжном методе не заменяют выбор владельца и судьбы старых путей. |
| A13 | Архитектурное влияние анализируется отдельно; при trigger сравниваются варианты, границы/данные/qualities/security/migration/rollback и затем независимо проверяется conformance проектному канону | `missing` как отдельная аналитическая ответственность | V: `SKILL.md:23-24`, `agents/contracts/system-analyst.md:42-58`, `agents/contracts/solution-architect.md:39-99`. T: список владельцев в `docs/architecture.md:56-70` не содержит spec solution architect; stage 1 проверяет только causal chain, solution boundary и layer ownership (`skills/spec-workflow/references/stage-1-foundation.md:15-18`). Независимая архитектурная surface в current repo не объявлена. |
| A14 | Полная цепочка модели требований и разделение BR/UR/UC/FR/RULE/DATA/INTF/QR/CON/PRJ; атомарность и проверяемость | `preserved` | V: `references/requirements-method.md:122-152,249-260,377-404`. T: идентичный `library/requirements/references/requirements-method.md:122-152,249-260,377-404`; whole-template и block stages требуют единую модель (`skills/spec-workflow/references/stage-1-foundation.md:9-18`, `stage-2-behavior.md:5-13`). |
| A15 | Сценарий содержит actor, trigger, preconditions, main/alternative/error flow, recovery, итоговые состояния и качества; UI имеет evidence-backed screen/path без выдумывания | `preserved` | V: `references/requirements-method.md:262-281`. T: идентичный `library/requirements/references/requirements-method.md:262-281`; шаблон закрепляет UI-контекст в `assets/reader-specification-ru.md:153-161`. |
| A16 | DATA отделено от wire DTO; API содержит фактический request/response, ошибки и mapping; BE/FE имеют разные обязанности, trigger и response use | `preserved` | V: `references/requirements-method.md:302-347`, `agents/contracts/system-analyst.md:123-138`. T: идентичный `library/requirements/references/requirements-method.md:302-347`, плюс усиление в `rules/process-kernel.md:94-99`, `skills/spec-workflow/references/stage-2-behavior.md:19-25` и `docs/architecture.md:98-110`. |
| A17 | Diagram gate выбирает минимальное представление по states/branching/sequence/boundaries/data; схема отвечает на один вопрос, не создаёт семантику, имеет source IDs, decomposition и visual render QA | `partial` | V: `references/diagram-contract.md:1-49,88-122`, `agents/contracts/system-analyst.md:89-94`. T: книжный метод и неизменённый template сохраняют основную эвристику (`library/requirements/references/requirements-method.md:283-300`, `assets/reader-specification-ru.md:140-149`), но отдельного current `references/diagram-contract.md` нет, а stage 4 называет только общий deterministic diagram check (`skills/spec-workflow/references/stage-4-article.md:30-32`). Нет общего output contract для status/surfaces/source IDs/decomposition/render receipt. |
| A18 | Reader projection: problem→goal→solution, owner map, delta-only, один факт один раз, внутренние IDs/process history наружу не выходят, UI/API/AC остаются воспроизводимыми | `partial` | V: `references/reader-projection-contract.md:7-24,41-110,122-216`. T: `rules/process-kernel.md:28-39`, `agents/contracts/spec-article-editor.md:11-28`, идентичный шаблон `assets/reader-specification-ru.md:33-128,238-281`, а также метод `library/requirements/references/requirements-method.md:237-247,421-451`. Основная семантика сохранена; ослаблены единый progressive-disclosure contract и profile-owned conformance: current repo не содержит аналога старого reader-projection contract. |
| A19 | Финальная User Story имеет единую project-owned форму role→goal→value и не подменяется ACT/SCN/системной моделью | `partial` | V: `SKILL.md:60-63`, `profiles/project-profile-template.md:192-199`, `agents/contracts/spec-editor.md:49-52`. T: bundled template полностью сохраняет форму (`assets/reader-specification-ru.md:114-128`), preliminary brief сохраняет actor/need/value (`skills/spec-preanalysis/references/brief-contract.md:13`), но kernel и current editor contract не формулируют обязательную проверку project-owned формы. Для неизменённого bundled template правило сработает; для внешнего project template доказательства нет. |
| A20 | AC проверяет наблюдаемое поведение и конкретную точку входа; DoD — готовность к живой приёмке, а не self-check; прямая трассировка остаётся отдельной | `preserved` | V: `references/requirements-method.md:406-454`, `references/reader-projection-contract.md:163-209`. T: идентичный `library/requirements/references/requirements-method.md:406-454`, `rules/process-kernel.md:30-39`, `skills/spec-workflow/references/stage-3-acceptance.md:5-29`, `assets/reader-specification-ru.md:246-281`. |
| A21 | Приоритизация по value/cost/risk, quality attributes, reuse, change impact, data, integration и modeling подключаются адресно | `preserved` | V: `references/knowledge-map.md:138-359` и соответствующие `C/T/D`. T: byte-identical `library/requirements/references/knowledge-map.md:138-359`; `library/route-overrides.json:4-35` делает ранее optional rules достижимыми, `skills/method-library/SKILL.md:64-72` фиксирует coverage. Validator: 23 routes, 70/70 native requirements rules reachable. |
| A22 | Изменение существующего поведения требует impact на requirements/data/interfaces/tests/docs/compatibility/operations | `preserved` | V: `references/requirements-method.md:193-197,357-363`. T: идентичный `library/requirements/references/requirements-method.md:193-197,357-363`; `rules/process-kernel.md:56-58` добавляет bounded recheck после правки. Transition ownership остаётся отдельным gap A12. |
| A23 | Старый planner не оценивает сроки моделью; отдельный timing model строит human-only forecast | `intentionally out of analytical scope` | V: `agents/contracts/planner.md:104-108`, `references/planning-contract.md:84-95`. T сознательно ввёл другую продуктовую договорённость: range с basis/confidence либо unavailable (`skills/spec-preanalysis/SKILL.md:30-31,76`, `skills/spec-preanalysis/references/brief-contract.md:76-88`). Старую timing/FSM-механику возвращать для сохранения анализа не требуется; это явная смена правила, не тихая потеря. |
| A24 | Независимый review имеет отдельные аналитические линзы acceptance, architecture, contradictions, reader projection, scope boundary и traceability | `partial` | V: `revmux/lenses/vigers-acceptance.md:1-6`, `revmux/lenses/vigers-architecture.md:1-6`, `revmux/lenses/vigers-contradictions.md:1-5`, `revmux/lenses/vigers-reader-projection.md:1-6`, `revmux/lenses/vigers-scope-boundary.md:1-6`, `revmux/lenses/vigers-traceability.md:1-6`. T: acceptance/traceability/reader/scope проверки распределены по kernel и stages (`rules/process-kernel.md:15-39`, `skills/spec-workflow/references/stage-1-foundation.md:15-18`, `skills/spec-workflow/references/stage-3-acceptance.md:10-28`, `skills/spec-workflow/references/stage-4-article.md:44-60`), но current repo не содержит самих lens-файлов и setup не фиксирует их состав (`setups/rtl.json:10-21`, `setups/haeze.json:10-21`). Архитектурная линза остаётся самым явным пробелом. |
| A25 | Утверждённый preliminary brief с problem/goal/PUS и evidence должен быть связан с specification case и входить в первый article pass | `missing` | V: системный аналитик явно получает preliminary `PUS/PDOD` и boundary probe (`agents/contracts/system-analyst.md:17-18`), а handoff переносит approved input (`references/planning-contract.md:329-337`). T: stage 1 просит approved preanalysis artifacts (`skills/spec-workflow/references/stage-1-foundation.md:6-8`), но `caseflow init` принимает и hash-bind-ит только decision и plan (`scripts/caseflow.py:669-750`); stage-1 context включает их и optional `sources.md`, но не brief (`scripts/caseflow.py:850-905`); CLI не имеет `--brief` (`scripts/caseflow.py:1906-1912`). Decision сохраняет goal/outcome/boundary, но не problem и PUS (`skills/spec-preanalysis/references/decision-contract.md:3-48`). |
| A26 | `simplicity-spec` защищает не только YAGNI, но и бизнес-смысл, security/recovery/compliance/accessibility, публичный контракт, доказанную вариативность и extension seam; решение проходит лестницу до первого достаточного уровня | `preserved` по смыслу, `partial` по раннему receipt | Установленный `/Users/svs/.agents/skills/simplicity-spec/SKILL.md` сохраняет лестницу решения, protected minimum, `REMOVE\|DEFER\|ASK`, `ceiling`, `revisit_trigger` и `upgrade_path`. T запускает его до финализации preliminary brief (`skills/spec-preanalysis/SKILL.md:64-75`) и ещё раз на целой статье до revmux (`skills/spec-workflow/references/stage-4-article.md:12-25`). Однако preliminary schema/validator не hash-bind-ят отдельный observable simplicity report; жёсткий receipt-контракт есть только на stage 4. Это ослабление доказуемости раннего прохода, а не потеря самого правила простоты. |

## Противоречия и разорванные зависимости

### C01. Живой method basis ссылается на отсутствующий diagram contract

`library/requirements/references/requirements-method.md:295-300` требует для каждой
сработавшей поверхности решение по `references/diagram-contract.md`. Такого файла нет
ни в `library/requirements/references`, ни в `rules`, ни в active skill references.
Bundled template содержит часть правил, но не заменяет названный output contract. Это
не просто неперенесённая механическая проверка, а разорванная аналитическая ссылка.

### C02. Preanalysis требует классифицировать contradictions, но его schema не имеет
места для них

`skills/spec-preanalysis/SKILL.md:56-59` требует классифицировать facts,
contradictions и assumptions. `skills/spec-preanalysis/references/brief-contract.md:6-15`
перечисляет sources, problem/goal/hypothesis, stories, scope, unknowns, assumptions,
dependencies и estimate, но не facts/interpretations/contradictions и не отдельный
coverage artifact. Поэтому требование существует в prose, но обязательный handoff его
не удерживает.

### C03. Solution boundary объявлена перенесённой, но перенесён только горизонт

`docs/rule-preservation.md:29-34` точно перечисляет перенесённые части: horizons,
smells, seam и trigger. Это утверждение корректно. Однако старый non-FSM блок судьбы
существующей реализации (`references/solution-boundary-contract.md:76-99`) не входит в
этот список и не появился у другого владельца TRACE. Следовательно, это не ложь в
документации, а неполная семантическая миграция под общим названием solution boundary.

### C04. Stage 1 требует approved preanalysis artifacts, но caseflow теряет brief

`skills/spec-workflow/references/stage-1-foundation.md:6-8` объявляет approved
preanalysis artifacts входом article editor. Однако `caseflow init` не принимает путь
brief и не сохраняет его hash (`scripts/caseflow.py:669-750`), а stage-1 context отдаёт
только decision, plan и необязательный `sources.md` (`scripts/caseflow.py:850-905`).
CLI подтверждает отсутствие `--brief` (`scripts/caseflow.py:1906-1912`). Поэтому
problem и preliminary PUS могут существовать в валидном brief, но не попасть в
bounded read-set первой статьи. Это разрыв handoff, а не дефект старой или новой FSM.

## Существенные partial/missing gaps

1. **Preanalysis brief handoff — high.** Валидный brief не hash-bind-ится к case и не
   входит в stage-1 context. Problem и preliminary PUS способны исчезнуть между
   предварительным анализом и первой целостной статьёй.
2. **Architecture and transition boundary — high.** Нет обязательного выбора судьбы
   существующего semantic owner и старых путей, а также независимой проверки решения
   проектному канону. Это допускает параллельных владельцев правила, бессрочный legacy
   и миграцию без retirement/rollback boundary.
3. **Preliminary evidence coverage — high.** Источники перечисляются, но выполненные
   поиски, отрицательные результаты, freshness, конфликты и verdict достаточности не
   являются обязательным сохраняемым результатом.
4. **Diagram contract — high.** Сохранились советы и шаблон, но отсутствует контракт,
   на который прямо ссылается активный method basis: trigger/status, source IDs,
   decomposition и semantic/visual QA могут не сработать как единый обязательный проход.
5. **Preliminary US/DoD lineage — high.** US потеряли per-item evidence/confidence;
   preliminary DoD исчез; полный анализ не обязан показать disposition каждой гипотезы.
6. **Plan quality — medium/high.** DAG сохранён, но этап лишился exit criteria и
   source refs. Формально валидный план может оказаться перечнем названий без
   проверяемой границы результата.
7. **Reader and review contracts — medium.** Большая часть смысла живёт в неизменённом
   template и зеркале метода, но project-owned User Story/document conformance и точный
   набор revmux lenses не доказаны самим TRACE repo.

Эти gaps являются содержательными и не требуют считать старые states, epochs или
pipeline-команды полезными правилами анализа.

## Неизвестные и нужный источник

| ID | Неизвестное | Нужный источник |
|---|---|---|
| U01 | Покрывают ли фактические RTL/HÆZE revmux profiles все шесть старых аналитических lenses, особенно architecture | Точные активные profile/lens-файлы revmux и receipt хотя бы одного полного запуска каждого профиля |
| U02 | Закрепляют ли реальные неизменяемые project templates форму User Story, reader navigation, diagram lifecycle и link style | Текущие `ШАБЛОН ПОСТАНОВКИ.md`, проектные `AGENTS.md`/`CLAUDE.md` и deterministic document-check contract каждого проекта |
| U03 | Доступен ли remote fallback полного `book-extract.md` в реальной установке без ручного обращения к архиву | Live materialization/fallback receipt для одного requirements route; manifest подтверждает ссылку, но не сетевую доступность |
| U04 | Компенсируется ли отсутствие brief в caseflow ручным копированием problem/PUS в `sources.md` в реальных кейсах | Один полный case package от approved preanalysis через `caseflow context` до stage-1 article с fingerprint каждого входа; текущий contract такой перенос не требует |

## Видимые зависимости

- Содержательная полнота книжных правил зависит от `method-library` и передачи
  материализованного route/hash конкретному агенту (`skills/method-library/SKILL.md:47-55`).
- Preliminary facts и hypotheses должны доходить до stage 1 через brief/source index,
  но current caseflow не связывает brief и считает `sources.md` необязательным;
  prose-инструкция не компенсирует отсутствующий handoff.
- Диаграммы зависят от отсутствующего current diagram contract, хотя template и method
  продолжают на него ссылаться по смыслу.
- Project-specific reader rules и фактическая architecture policy остаются внешними по
  `P14 PROJECT-OWNERSHIP` (`rules/process-kernel.md:52-53`); без их read-set нельзя
  повысить `partial` до `preserved`.
- Финальный независимый контроль зависит от внешнего revmux profile, состав которого
  setups TRACE не фиксируют.

## Ответы на вопросы назначения

1. **Есть ли не-FSM правила анализа, которые не доперенеслись?** Да. Самые явные:
   handoff preliminary brief, implementation transition, архитектурная
   design/conformance boundary, полный diagram contract, предварительный coverage
   contract, preliminary DoD и disposition предварительных гипотез.
2. **Сохранились ли книжные правила Вигерса?** Да, в пределах проверенного корпуса:
   mirrored method, task template, knowledge map, 26 checklist, 26 tables, 18 diagrams
   и image map совпадают с pinned SHA; все 70 native rules достижимы.
3. **Какие зоны перенесены лишь частично?** Research coverage, preliminary US, plan
   quality, reader projection/project-owned User Story и независимые review lenses.
4. **Нужно ли для закрытия этих разрывов возвращать старую FSM?** Из прочитанных
   источников это не следует. Найденные пробелы относятся к содержательным контрактам
   и evidence-полям; состояния, epochs и старые команды в аудит не включались.
