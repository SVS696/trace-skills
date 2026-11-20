---
name: method-library
description: >-
  Select a small set of traceable rules for one requirements or delivery assignment. Use the Vigers, SWEBOK, Software Engineering at Google, ISTQB, RFC, WCAG, and OWASP sources. Product decisions belong to the project.
allowed-tools: Read Glob Grep Write Bash
---

# Выбор методических правил

Библиотека хранит точные копии правил из источников. Для одного смыслового блока или участка разработки подготовь отдельный `method-basis.md`. Ведущий агент один раз читает [правила TRACE](../../rules/process-kernel.md).

1. Посмотри доступные маршруты.

   ```bash
   python3 scripts/rule_library.py list --domain requirements
   python3 scripts/rule_library.py list --domain delivery
   ```

2. Получи предложение по тексту задания.

   ```bash
   python3 scripts/rule_library.py route --domain requirements --task "<bounded assignment>"
   ```

3. Сверь маршрут с заданием. Для сценария с участниками, событием, основным ходом, альтернативами и исключениями используй `requirements/scenarios`. Для каждого изменения кода нужен `delivery/core-change`. Для HTTP-метода, запроса, ответа или кода состояния используй специализированный маршрут `delivery/backend-http`. Другие идентификаторы возьми из вывода `list`. Правила маршрутизации можно дополнить через `library/route-overrides.json`. Сохраняй закреплённые копии карт.
4. Подготовь один маршрут. Добавь второй только для отдельного предмета проверки.

   ```bash
   python3 scripts/rule_library.py materialize \
     --domain requirements --route scenarios --output <method-basis.md>
   ```

5. Передай исполнителю путь и хеш полученного файла. Остальные разделы библиотеки и материалы других исполнителей оставь за пределами задания. Если файл ссылается на `rules/diagram-contract.md`, прочитай этот документ для назначенной диаграммы. При подготовке маршрута утилита исправляет устаревшую относительную ссылку в выводе. Байты закреплённого источника сохраняются.

Применяй метод как набор проверочных вопросов. Границы продукта определяют запрос, правила проекта и текущие факты. Если выдержки недостаточно, открой нужное место в `book-extract.md` на закреплённом коммите Vigers. Версия в реестре подтверждает происхождение источника. Вывод о соответствии ограничь проверенной частью.

Перед выпуском или установкой выполни `python3 scripts/rule_library.py validate`. Утилита проверяет хеши SHA-256, ссылки и доступность каждого правила через маршрут. Тест `tests/test_rule_library.py` фиксирует 70 исходных правил требований (`C/T/D`) и 30 правил разработки (`E/B/F/T/S`).
