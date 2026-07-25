# Обложка через Gemini (браузер)

## Шаги

1. Прочитать `posts-emdr-memory/profile/cover-prompt-template.md`
2. Подставить HEADLINE / HIGHLIGHT / STICKY / MINI_CARD из темы
3. Открыть Gemini:

```text
browser_navigate → https://gemini.google.com
```

4. Загрузить референс-фото Натальи (путь уточнить у пользователя — обычно в `РЕФЕРЕНСЫ/`)
5. Вставить финальный промпт
6. Сгенерировать → скачать PNG
7. Сохранить: `posts-emdr-memory/output/{topic_id}/cover.png`

## Fallback — MCP KV

```text
CallMcpTool: user-mcp-kv / nano_banana_2
  prompt: <из cover-prompt-template.md>
  reference: <URL или upload>
```

## Gate

- 16:9, белый фон #FFFFFF
- Портрет справа, likeness сохранён
- Жёлтый маркер #F5C400 на ключевой фразе
- Подпись «Морозова Наталья / Психолог, EMDR терапевт»
