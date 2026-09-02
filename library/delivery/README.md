# Delivery engineering library

Адресная инженерная база из Delivery Engineering. Главные книжные источники:

- `SWEBOK 4.0a` — Software Construction, Software Testing и Software Quality;
- `Software Engineering at Google`, online edition 2020 — style guides, code review,
  testing и static analysis.

Точные редакции и дополнительные стандарты находятся в `references/source-registry.md`.
Дистилляты `E/B/F/T/S` перенесены byte-identical с commit `56a93cb` и защищены hash.

Lane получает один основной route и, только при отдельной поверхности, один
дополнительный. Полный корпус другой lane не загружается.
Локальные расширения маршрутов находятся в `library/route-overrides.json`; это overlay,
а не часть byte-identical зеркала.
