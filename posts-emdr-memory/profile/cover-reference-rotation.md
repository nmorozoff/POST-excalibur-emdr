# Ротация референс-фото на обложках

**Проблема:** на всех обложках один и тот же `portrait.jpg` → лицо и поза повторяются.

**Решение:** на каждый пост — **свой** портрет из пула (8 слотов), синхронно с ротацией OUTFIT.

| Пост MSP | Референс | OUTFIT |
|----------|----------|--------|
| sb-01, sb-09… | portrait-01 | OUTFIT №1 |
| sb-02, sb-10… | portrait-02 | OUTFIT №2 |
| … | … | … |
| sb-08, sb-16… | portrait-08 | OUTFIT №8 |

Формула: `(номер_поста - 1) % 8 + 1` для фото, `(номер_поста - 1) % 12 + 1` для одежды.

## Файлы

| Путь | Назначение |
|------|------------|
| `assets/reference/manifest.json` | Список portrait-01…08 |
| `assets/reference/portrait-NN.jpg` | Сжатые копии из `~/Desktop/РЕФЕРЕНСЫ/` |
| `scripts/sync-reference-photos.sh` | Обновить пул с рабочего стола |

## Перед cloud / новой темой

```bash
./scripts/sync-reference-photos.sh
```

Runware сам подберёт референс по `topic_id` (legacy). **Основной путь — Kie:**

```bash
python3 scripts/kie-cover.py \
  --topic sb-04-what-if-phrase \
  --prompt-file posts-emdr-memory/output/sb-04-what-if-phrase/cover-prompt.txt \
  --output posts-emdr-memory/output/sb-04-what-if-phrase/cover.png
```

Параметры: **5:4, 1K**. Ключ: `KIE_API_KEY` (`kie.env.local` или Carusel `.env`).

Переопределение одного поста: `--reference path/to.jpg`

Глобальный override (не рекомендуется): `RUNWARE_REFERENCE_IMAGE` в `runware.env.local`
