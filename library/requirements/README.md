# Requirements method library

Адресная библиотека правил из исходной выжимки К. Вигерса. Файлы в `references/`
перенесены byte-identical из `vigers-skill` на commit `62bb327` и защищены hash в
`library/manifest.json`.

`requirements-method.md` содержит исполняемый метод, `native-checklists.md`,
`native-tables.md` и `native-diagrams.md` — дистилляты с исходными `C/T/D` ids.
Полный `book-extract.md` не копируется в новый активный пакет: это большой fallback,
доступный по pinned-ссылке в manifest и в локальном архиве старого репозитория.

Модель не читает библиотеку целиком. `scripts/rule_library.py` выбирает один маршрут
из `knowledge-map.md` и материализует только названные sections.

