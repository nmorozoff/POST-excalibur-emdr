# Шаблон обложки — одна на все соцсети

**Генерируется один раз на шаге Макс.** Дальше тот же файл `cover.png` идёт в Telegram, VK, LinkedIn, Facebook — **без повторной генерации**.

| Когда | Что |
|-------|-----|
| Шаг Макс | `cover-prompt.txt` → Runware → `cover.png` |
| Telegram, VK, LI, FB | только читают `cover.png` |

**Стиль:** editorial podcast, тёмный фон, крупный заголовок сверху.  
**НЕ использовать** для статей блога — там отдельный промпт Artur/zine.

## Подстановки

| Поле | Описание |
|------|----------|
| `{LINE1}` | Строка 1 заголовка (белый текст) |
| `{LINE2}` | Строка 2 — слова в жёлтом прямоугольнике |
| `{LINE3}` | Строка 3 заголовка (белый текст) |
| `{YELLOW_WORD}` | Слово/фраза для жёлтой подсветки #F5C400 (должно быть в LINE2) |

**Правило:** не дублировать одно и то же слово в заголовке. Разбивать на 3 строки для мобилы.

**UTM:** только в ссылках поста (`profile/utm-sources.md`). **На обложке URL не печатать.**

**Одежда:** один образ из ротации [`cover-outfit-rotation.md`](./cover-outfit-rotation.md) — по номеру поста. Не придумывать outfit на лету.

**Референс-фото:** портрет из ротации [`cover-reference-rotation.md`](./cover-reference-rotation.md) — `sb-04` → `portrait-04.jpg` и т.д. Обновить пул: `./scripts/sync-reference-photos.sh`.

## Промпт (Runware / GPT Image 2)

```
YouTube thumbnail style editorial cover. Dark background (#0d0d0d or near-black), cinematic and clean.

Photo-realistic portrait of the woman from the reference photo placed on the RIGHT side of the frame, upper body visible. Preserve her exact face, features, age, hair, and likeness from the reference — do NOT alter, retouch, rejuvenate, or change her face in any way. Natural, calm, professional expression — no wide smile, no dramatic pose. Soft studio lighting, slight vignette. Blurred warm therapy office background fading into dark.

{OUTFIT_BLOCK}
Do NOT use beige blazer with beige sweater. Do NOT stack two warm-neutral layers (beige + sand + cream). Do NOT copy clothing from the reference photo. Business professional only: high neckline, full sleeves, modest fit — no lingerie, no low cut, no evening wear. Solid colors, no prints, no logos.

LEFT side typography — CRITICAL layout rules:
- Headline block starts near the TOP of the frame (top margin only 5–8% of canvas height). Do NOT leave large empty dark area above the text.
- Headline occupies ~65–75% of the LEFT half height. Large, bold, stacked tightly with minimal line gaps.
- Text size: very large mobile headline scale — each line should feel like a poster title, not a subtitle.
- Bold white Cyrillic text, clean modern sans-serif. Text content:
Line 1: {LINE1}
Line 2: {LINE2}
Line 3: {LINE3}
- The phrase «{YELLOW_WORD}» must have a bright yellow (#F5C400) rectangle behind it.

Bottom-left corner only (below headline block), small white signature — exactly two lines, no URLs:
Морозова Наталья
Психолог, EMDR терапевт

Format: 5:4 horizontal landscape, 1280×1024px. Ultra realistic, cinematic color grading. No watermarks, no logos, no URLs, no extra text.
```

## Файлы на тему

| Файл | Назначение |
|------|------------|
| `cover-prompt.txt` | Промпт генерации; **OUTFIT** из `cover-outfit-rotation.md` |
| `cover.png` | **Единственная обложка** для всех платформ |
| `cover.url` | Кэш Runware URL (создаётся скриптом) |

## Генерация (только на шаге Макс)

```bash
python scripts/runware-cover.py \
  --topic {topic_id} \
  --prompt-file posts-emdr-memory/output/{topic_id}/cover-prompt.txt \
  --output posts-emdr-memory/output/{topic_id}/cover.png \
  --width 1280 --height 1024 --quality low
```

Референс подставится автоматически по номеру поста (см. `cover-reference-rotation.md`).

**Runware:** обложка на каждый short-blog пост — автоматически (`scripts/runware-cover.py`). OUTFIT из `cover-outfit-rotation.md`.

После этого **не запускать** runware-cover для TG/VK/LI/FB — только переиспользовать `cover.png`.
