# Шаблон обложки — статьи блога (Artur / zine)

> **Для постов в каналы** (Макс, Telegram, VK) используйте  
> [`social-cover-prompt-template.md`](./social-cover-prompt-template.md) — YouTube thumbnail, тёмный фон.

Ниже — стиль **editorial hook collage, DIY zine, белый фон** для статей на сайте (другой агент).

**Одежда на коллаже:** тот же принцип — [`cover-outfit-rotation.md`](./cover-outfit-rotation.md), один OUTFIT на статью.

## Базовый промпт (копировать в Gemini / Excalibur cover)

Подставлять: `{HEADLINE}`, `{HIGHLIGHT_PHRASE}`, `{STICKY_NOTE}`, `{MINI_CARD}`, `{REFERENCE_PHOTO}`.

```
Russian human-made editorial hook collage, DIY zine aesthetic adapted to 16:9 widescreen, layered pasted scraps on pure white background #FFFFFF — NOT dark, NOT lavender gradient, NOT clinical stock infographic.

Single 16:9 panel, 1280×720 or 1920×1080. High detail, looks like a human editor glued screenshots, notes and a portrait cutout on a desk.

REFERENCE FACE (mandatory): preserve EXACT likeness from input reference photo — same face, age, hair, features. Do NOT retouch, rejuvenate, or change her face. Natural calm professional expression, no wide smile, no dramatic pose. Blog host cutout placed right or center-right, upper body visible.

{OUTFIT_BLOCK}
Do NOT use beige blazer with beige sweater. Do NOT stack warm-neutral double layers. Business professional only — no lingerie, no low cut. Solid colors, no logos.

LEFT and center-left: huge bold condensed Cyrillic headline, readable on mobile:
{HEADLINE}

Highlight the phrase «{HIGHLIGHT_PHRASE}» with bright yellow marker rectangle #F5C400 behind it — sharp edges, one key phrase only.

Human-made layers (helpful, respectful — NO mockery):
— torn paper strip with short Cyrillic note «{STICKY_NOTE}»
— pink OR warm-coral sticky note with arrow pointing to headline
— scotch tape corners on pasted cards
— fake phone screen: calm notes app or calendar «запись к психологу» (Cyrillic UI, subtle)
— small pasted card «{MINI_CARD}» mini comparison, tape edge visible
— red/pink marker arrow annotation, handwritten style

Tone: warm, adult, psychology blog — NEVER insult the reader, NO sarcastic meme stickers, NO Drake, NO facepalm, NO reaction meme faces, NO joke captions.

Background: clean white #FFFFFF with subtle paper shadow under layers only — no full-panel beige grunge, no grey gradient wash.

Bottom-left small signature, dark grey Cyrillic:
Морозова Наталья
Психолог, EMDR терапевт

Safe margins: all text and headline fully inside frame, 10% padding from edges — nothing cropped.

Ultra realistic portrait cutout blended into collage. 16:9 horizontal. No watermark, no logo, no English UI, no pencil sketch, no whiteboard doodle, no hospital ad, no horror imagery.
```
