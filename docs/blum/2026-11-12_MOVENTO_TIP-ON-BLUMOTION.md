# Blum MOVENTO + TIP-ON BLUMOTION — сверка с конфигуратором изделий Blum

Дата: 12.11.2026. Источник: Blum E-SERVICES → Product Configurator (вход владельца, страна KZ), детальная конфигурация.
Сессия конфигурации: externalConfigurationId `b20866da-3a3f-44d3-940f-ec05712eae2f`.

## Входные данные (колонна комода ARV-NST-101)

| Параметр | Значение |
|---|---|
| Система | MOVENTO, полное выдвижение, выдвижной ящик без релинга |
| Внутренняя ширина корпуса LW | 568 |
| Номинальная длина NL / нагрузка | 450 / 40 кг |
| Крепление направляющих к корпусу | саморезы (не евровинты) |
| Высота ящика (боковины) | 150 |
| Передняя панель / царга / дно | 16 / 16 / 16 |
| Глубина ниши (recess) | 13 |
| Технология | TIP-ON BLUMOTION, синхронизатор — да; механизм L1 |
| Вес | пустой ящик 3,4; фасад 0,8; содержимое 2,4 («хозяйственные мелочи»); всего 6,5 кг |
| Фасад | 597 × 270 × 18, наложение слева / справа / снизу 14,5 |

## Результат Blum

Спецификация:

| Кол. | Артикул | Описание |
|---|---|---|
| 1 | 760H4500S | MOVENTO, BLUMOTION, для TIP-ON BLUMOTION / SERVO-DRIVE, полное выдвижение, 40 кг, NL 450, Л/П |
| 1 | T51.7600 | замок MOVENTO, Л+П |
| 1 | T60L7340 | набор TIP-ON BLUMOTION (блок + защёлка + адаптер), L1 (до 20 кг), NL 350–600, Л+П |
| 1 | T60.1125W | синхронизация TIP-ON BLUMOTION, 1125 мм, отрезать по месту |

Раскрой ящика (Blum):

| Деталь | Длина | Ширина | Толщина |
|---|---|---|---|
| Фасад | 270 | 597 | 18 |
| Задняя стенка | 526 | 121 | 16 |
| Передняя панель (царга) | 526 | 121 | 16 |
| Боковина левая / правая | 440 | 150 | 16 |
| Дно | 536 | 440 | 16 |

Следствия для нашего ящика: стенки ниже боковин на 29 (= ниша 13 + дно 16); дно шире внутренней ширины на 10 → по 5 мм в пазы боковин (проверить по рисунку обработки ящика Blum `76XHSK`). Наш текущий короб (TANDEM-логика генератора) собран иначе — переделать.

Высоты (рисунок «Space requirements in cabinet», TIP-ON BLUMOTION):
- ось саморезов профиля — 38 над низом профиля;
- низ ящика — 28,5 над низом профиля;
- зазор боковины ящика до стенки корпуса — 21;
- над ящиком мин. 7.

По длине (рисунок «Side planning view», NL 450): отмечены (залитые) отверстия 37 и 69 от передней кромки; длина ящика 440, NL 450, глубина корпуса мин. 453, задний упор 10. На рисунке сборки корпуса (`76XHKOR`) стрелки показывают ещё точки крепления дальше по длине — координаты на рисунке не подписаны. **Не угадывать.** Закрыть отчётом «Configuration details» (PDF) или данными CAD/CAM — владелец разрешил скачать (12.11, «да»).

Ссылки на рисунки (открываются без входа):
- Space requirement: https://d2.blum.com/services/PAI_Planningmapping_Service/Pool/PIK_PlatzbedarfImKorpus/Blum_A_PIK-MOV-VAZ-SK-TOB-SMO_P_1_PL_BAU_$SALL_$APK02_$V1.gif
- Side planning view NL 450: https://d2.blum.com/services/PAI_Planningmapping_Service/Pool/PLS_PlanungsansichtSeitlich/Blum_A_PLS-MOV-VAZ-SK-450-TOB-SMO_P_1_PL_BAU_$SALL_$APK02_$V1.gif
- Rear planning view: https://d2.blum.com/services/PAI_Planningmapping_Service/Pool/Planungsansicht_hinten/Blum_A_PLH-MOV-VAZ-SK-TOB-SMO_P_1_PL_BAU_$SALL_$APK02_$V1.gif
- Drawer processing: https://d2.blum.com/services/PAI_Planningmapping_Service/Pool/SBE_Schubkastenbearbeitung/Blum_A_76XHSK_H_1_PL_BAU_$SALL_$APK02_$V1.gif
- Cabinet assembly: https://d2.blum.com/services/PAI_Planningmapping_Service/Pool/KOZ_Korpuszusammenbau/Blum_A_76XHKOR_B_1_PL_BAU_$SALL_$APK02_$V1.gif

Инструкции Blum (PDF в результате конфигурации): MOVENTO; MOVENTO side stabilisation; MOVENTO with TIP-ON synchronisation; TIP-ON BLUMOTION for LEGRABOX and MOVENTO.

## Как работать с конфигуратором (опыт 12.11)

- Встроенный браузер приложения Claude, вход владельца сохранён. Пароли Claude не вводит.
- Конфигуратор корпусов (Cabinet Configurator) требует перетаскивания мышью в 3D — из встроенного браузера не сработало. Конфигуратор изделий (Product Configurator) работает формой.
- Поля формы надёжно задаются через JS: найти видимые `input`, выставить значение нативным сеттером, отправить `input` / `change` / `focusout`, после каждого поля заново искать `input` (форма перерисовывается).
- Узкая панель: `resize_window` 1500 × 950, после работы вернуть `desktop`.
