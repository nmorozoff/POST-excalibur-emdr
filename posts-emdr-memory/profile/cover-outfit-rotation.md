# Ротация одежды на обложках

**Проблема:** модель часто рисует бежевый пиджак + бежевый свитер (или оба сразу), хотя в референсе другая одежда.

**Решение:** на **каждую** новую обложку брать **один** готовый образ из таблицы ниже — по номеру поста в очереди (`sb-01` → №1, `sb-02` → №2, … `sb-12` → №12, `sb-13` → снова №1).

В `cover-prompt.txt` вставлять блок **OUTFIT** целиком (английский текст для Runware) — не перефразировать.

---

## Жёсткие правила (всегда)

| Запрет | Почему |
|--------|--------|
| Бежевый пиджак **+** бежевый/песочный/кремовый свитер вместе | Уже заезжено |
| Два слоя в одной тёплой нейтрали (beige + sand + cream) | Выглядит одинаково |
| Копировать одежду с референс-фото | Нужно разнообразие |
| Лифчик, декольте, открытые плечи, майки, вечерние наряды | Только деловой тон |
| Яркие принты, логотипы, спортивная одежда | Не по бренду |

| Разрешено | |
|-----------|--|
| Спокойные тона: graphite, navy, dusty blue, sage, warm grey, ivory, soft white, muted teal, charcoal, camel (один акцент), dusty rose | |
| Один верхний слой **или** контрастная пара (тёмный пиджак + светлая блуза) | |
| Высокий вырез или воротник; рукава до запястья; посадка свободная/прямая | |

---

## Таблица образов (12 слотов)

| № | Для промпта OUTFIT (вставить в cover-prompt.txt) |
|---|--------------------------------------------------|
| **1** | `OUTFIT: graphite structured blazer over an ivory silk blouse with a simple collar — blouse only under blazer, NO sweater. Professional, modest neckline.` |
| **2** | `OUTFIT: dusty blue fine-knit turtleneck, solo piece — NO blazer, NO cardigan. Soft matte texture, high neck.` |
| **3** | `OUTFIT: warm grey open cardigan over a crisp white crew-neck shirt — shirt collar visible, NO beige tones.` |
| **4** | `OUTFIT: soft white cotton button-down shirt, top button open, sleeves neatly rolled to forearm — NO jacket, NO sweater.` |
| **5** | `OUTFIT: muted sage green fine-gauge crew-neck sweater, solo — NO blazer. Calm matte knit.` |
| **6** | `OUTFIT: muted navy blazer over a light grey turtleneck — contrast layers, NO beige or sand.` |
| **7** | `OUTFIT: charcoal fine merino turtleneck, solo — NO blazer. Clean minimal silhouette.` |
| **8** | `OUTFIT: oatmeal knitted vest over a white long-sleeve shirt — vest + shirt only, NO blazer on top.` |
| **9** | `OUTFIT: dusty rose tailored blazer over a soft white shell top — one pastel accent, white underlayer, NO beige sweater.` |
| **10** | `OUTFIT: muted teal / blue-grey fine merino crew-neck sweater, solo — NO jacket.` |
| **11** | `OUTFIT: camel single-breasted blazer over a black fine turtleneck — dark underlayer, camel only in jacket, NOT double beige.` |
| **12** | `OUTFIT: sand linen-blend shirt, relaxed professional, worn alone — NO sweater, NO blazer, NO second warm-neutral layer.` |

---

## Как выбрать номер

```
sb-01, sb-13, sb-25 … → 1
sb-02, sb-14 …        → 2
…
sb-12, sb-24 …        → 12
```

Формула: `(номер_поста - 1) % 12 + 1`, где `sb-07` → номер поста `7`.

Для `01-panic-night`, `02-airplane-panic` и прочих не-sb тем — взять порядковый номер из `topics/queue.md` или следующий свободный слот после последней обложки.

---

## Строка-усилитель (добавлять после OUTFIT в каждом промпте)

```
Do NOT use beige blazer with beige sweater. Do NOT stack two warm-neutral knit layers. Business professional attire only: high neckline, full sleeves, modest fit. No lingerie, no low cut, no evening wear.
```

---

## Чеклист перед генерацией cover-prompt.txt

- [ ] Номер образа выбран по таблице (не «на глаз»)
- [ ] В промпте есть строка `OUTFIT: …` из таблицы
- [ ] Есть блок-усилитель про запрет double-beige
- [ ] Нет слов «beige blazer» + «beige sweater» в одном OUTFIT
