# Инженерное ядро Arvello — чертежи

Версия пакета: 2026-11-11. Python 3.10+, библиотеки: matplotlib, numpy, Pillow.

## Проверка среды (первый запуск)

```
cd arvello_engine
python tools/eng/selftest_new_model.py          # образец новой модели → work/selftest/*.pdf, «ГОТОВО: среда работает»
python tools/eng/check_catalog.py technical     # 36 моделей, 610 вариантов, 0 нарушений
python tools/eng/test_samal.py && python tools/eng/test_opora.py
```

## Выпуск комплекта чертежей

| Что | Команда |
| --- | --- |
| Любая модель на общем ядре (R01E) | `python tools/eng/kit13.py SKU out.pdf key=value ...` |
| Тумба «Самал» (R02E, свой генератор) | `python tools/eng/kit_samal.py out.pdf color=W` |
| Стол «Опора» (R03E, свой генератор) | `python tools/eng/kit_opora.py out.pdf size=1600 ...` |
| Деталировка и покупные в CSV | `python tools/eng/export_parts.py SKU out_dir key=value ...` |

`kit13.py` печатает проверки комплекта (`ok` / `FAIL`). Комплект с хотя бы одним `FAIL` не выпускается.
Значения ключей — оси модели из `catalog/products/SKU.json` (`values`). Без ключей — конфигурация по умолчанию.

Состав комплекта kit13: 01 Общий вид · 02 Сборочный (у кухонь — План и модули) · Детали (плита) · Металл (если есть) ·
Узлы · Спецификация · Сборка и контроль · Вопросы и решения. Формат A3, единицы мм, в штампе — ревизия и хеш снимка.

## Как устроено

- `tools/eng/cab.py` — класс `Build`: корпус (`carcass`), цоколь (`plinth`), ножки (`feet`), навесы (`hangers`), ящики Blum 560H
  (`drawers`), двери (`doors`), трубы/пластины/сварка (`tube`, `plate`, `weld`), крепёж (`ecc` Minifix, `dowel`, `conf`, `screws_into`),
  отверстия (`hole`), покупные (`buy`), итог (`design()`).
- Построители моделей: `models13.py` (тумбы, комоды, столы), `models_rest.py` (шкафы, кровати, гостиная, офис), `kitchen.py` (кухни и модули),
  **`models_new.py` — новые модели** (с образцом `example_wardrobe_2d`).
- `kit13.py` — листы комплекта; `verify13.py` — проверки комплекта; `sheetlib.py`, `boardkit.py` — оформление.
- `catalog/products/*.json` — оси и значения моделей; `catalog/revisions.json` — какая ревизия в каталоге, допуск в производство (везде «закрыто»).
- `core.py` — снимок конфигурации (детали, отверстия, покупные, хеш), спецификация `bom()`, раскрой `cut_plan()`.
- `check_catalog.py` — проверки каталога: `technical` (геометрия, спецификация, ревизии) и `commercial` (цены; сейчас красная — прайс-пример).

## Новая модель — шаги

1. Функция-построитель в `tools/eng/models_new.py` по образцу `example_wardrobe_2d` (или по ближайшей модели из models13 / models_rest / kitchen).
2. Регистрация: `NEW["ARV-XXX-NNN"] = ("Тип «Имя»", функция)`.
3. Карточка `catalog/products/ARV-XXX-NNN.json`: `sku`, `name`, `category`, `line`, `desc`, `axes` (ключи = опции построителя).
   Поле `builder` не нужно (это каталожный построитель старых моделей).
4. `catalog/revisions.json`: `"ARV-XXX-NNN": {"catalog": "R01E", "revisions": {"R01E": {"status": "инженерное предложение …", "production": "закрыто"}}}`.
5. Комплект: `python tools/eng/kit13.py ARV-XXX-NNN out.pdf ...` для каждой конфигурации, все проверки `ok`.
6. `check_catalog.py technical`: число вариантов вырастет — поправить `EXPECTED_VARIANTS` в check_catalog.py и указать новое число в отчёте.
