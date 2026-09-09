# Архитектура TRACE

TRACE готовит одну целостную статью для каждого независимо принимаемого результата.
Смысловые блоки углубляют готовую модель целого; BE/FE и удобство агентов сами по себе
не являются основанием делить постановку.

## Порядок

1. Преданализ: проверенные источники, проблема и последствие, цель и польза, суть
   решения, preliminary US/DoD, scope, горизонт решения, переход, оценка и план.
2. Пользователь утверждает brief, decomposition и plan; они связываются hash при init.
   Архитектурный design появляется только при подтверждённом trigger до утверждения.
3. Стадия 1: весь применимый шаблон и явная судьба каждого preliminary US/DoD.
4. Стадия 2: углубление поведения и новая интегрированная статья.
5. Стадия 3: наблюдаемая приёмка и новая интегрированная статья.
6. Стадия 4: готовая статья и deterministic preflight.
7. article → обычный revmux → findings → принятый diff-pool → fix article →
   article v2 → следующий обычный revmux.
8. Остановка на постановке или явно выбранный delivery. Публикация, handoff,
   реализация, merge, deploy и acceptance остаются отдельными фактами.

## Контекст

Parent читает kernel один раз, текущий skill и одну стадию. Он материализует один
method-library route и формирует окончательный read_set через context с повторяемыми
--project-rule и --source. Узкий агент получает применимые проектные правила, сами
источники, предыдущую whole article, accepted solution_boundary и точные output paths.
Ссылка в source-map не разрешает неназванный источник. Missing required input
возвращается как input-error или точный запрос на дополнение; весь проект не загружается.

Preanalysis brief и lineage нужны на стадии 1. Architecture design передаётся только
затронутым назначениям, в том числе conformance-рецензенту внутри обычного revmux.
Шаблон выбирается из семейства main/component по rules/template-family.md; source
не меняется при авторинге, неприменимые секции удаляются только из article output.

## Авторинг и readiness

До первого revmux нет correction pool. Авторы и integrator исправляют кандидат,
согласуют блоки, выполняют deterministic preflight и разрешают content inputs.
Прямой вопрос нужен только для недостающего решения; доступные факты исследуются.
Неразрешённый вход, меняющий требование, сценарий или AC, не допускает status ready.

Каждая стадия регистрирует новый snapshot и JSON stitch report (schema 1, stage,
status ready, open_inputs [], описание checks), затем advance. Стадия 1 дополнительно
сохраняет US/DoD lineage. Fingerprints запрещают менять зарегистрированные bytes между
ready и advance или переписывать закрытые стадии. Finalize выбирает статью стадии 4.
Это готовность к review, не согласование или приёмка.

## Findings и подтверждение исправлений

Обычный revmux включает актуальные проектные критерии, логику, простоту, язык и
сработавшие архитектурные поверхности. Дизайнер не выдаёт собственный независимый
conformance verdict. Отдельные pre-revmux review loops и targeted verification не нужны.

После полного результата receipt-bound simplicity adjudication отбирает достижимые,
существенные findings и минимальные corrections; это не повторное ревью статьи.
Pool точно покрывает принятый набор. Каждый target указывает итоговую article;
синхронизация промежуточного артефакта может выполняться дополнительно в том же diff.

После исправления всей партии и deterministic checks resolve-review сохраняет applied
receipt с hash обновлённой статьи. Неизменившаяся article или устаревший receipt не
принимаются. Article-updated допускает следующий обычный revmux без verify-review.
Полный чистый revmux подтверждает applied corrections; degraded receipt их не закрывает.
Рецензенты, необходимые для предыдущих findings, сохраняются. При новых findings
повторяется тот же цикл. Авторская запись «исправлено» не является независимым verdict.

Считаются только содержательные раунды revmux, максимум пять на article. Технические
retries и deterministic checks не считаются. Чистый результат останавливает цикл;
только minor позволяет ранний minor-pending с явным остатком. Шестой раунд требует
реального решения пользователя. Никакой собственный decision-файл не заменяет его.

## Совместимость и остальные контуры

Init нового кейса помечает его как article-revmux и не принимает pre-review pools. Исторические кейсы
без этой пометки по-прежнему читают свои старые stage pools/receipts; их не мигрируют
автоматически. Эти команды не являются альтернативным маршрутом нового авторинга.

Delivery сохраняет собственные lane/stage pools, developer checks и независимый
implementation verification. Не переносить команду «нет targeted verification для
article» на реальные тесты кода. Process-timer фиксирует фактически наблюдаемые события,
не определяет состояние workflow и не подменяет оценку длительностью.

Smoke Break запускает P23 COURSE-CHECK в длинном turn: outcome, frontier, измеримый
progress, drift, falsifier и CONTINUE/BACKTRACK/ASK/STOP. Это checkpoint parent, не новый
stage, artifact или агент. Без плагина workflow работает без автоматического таймера.
