# Сохранение методических и накопленных правил

TRACE наследует знания Vigers, Delivery Engineering & Co., но не их старую оркестрацию.

## Книжный слой

| Область | Источник | Что перенесено |
|---|---|---|
| Требования | памятка 23.07.2019 по книге К. Вигерса «Разработка требований к программному обеспечению» | requirements method, 26 checklist, 26 tables, 18 diagrams, image map и routing map |
| Разработка | SWEBOK 4.0a | construction, testing и quality distilled rules |
| Разработка | Software Engineering at Google, online edition 2020 | style guides/rules, code review, testing и static analysis distilled rules |
| Специальные поверхности | ISTQB CTFL, ISO 29119 overview, RFC 9110, WCAG 2.2, Testing Library, OWASP ASVS | адресные test/HTTP/accessibility/security rules |

Все перенесённые файлы привязаны к принятым Git commit и SHA-256. Полная книжная
выжимка Vigers остаётся fallback в старом pinned-репозитории; модель никогда не
загружает её целиком по умолчанию.

## Накопленный инженерный слой

Полезные правила, появившиеся после книжного baseline, сведены в
`rules/process-kernel.md`: порядок источников, no-invention и gaps, solution boundary,
декомпозиция, трассировка, reader projection, AC/DoD, exact diff, независимость review,
честные lifecycle-статусы, external-write boundary, project ownership, bounded context
и impact recheck.

Старые machine transitions, эпохи, профили и команды не переносятся как правила
предметного качества. Они остаются в архивных Git-репозиториях для истории. Их
заменяет четырёхстадийная машина TRACE с одним diff-pool на gate и стандартными
revmux-раундами единой статьи.

## Как не перегрузить модель

Один рабочий пакет состоит из:

1. `process-kernel.md` один раз на задачу;
2. активного workflow skill и одного stage-reference;
3. одного материализованного книжного route;
4. предметного read-set и active diff.

Полные `C/T/D` и `E/B/F/T/S` справочники остаются индексом. Parent передаёт агенту
только rule IDs и извлечённые sections, относящиеся к его блоку или lane.
