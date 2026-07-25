# Humanizer-RU

Скилл: `skills/humanizer-ru/skills/humanizer-ru/SKILL.md`

**Когда применять:** после черновика поста, перед публикацией.

**Режим для Посты EMDR:** полное редактирование + паспорт голоса из `posts-emdr-memory/profile/tone-of-voice.md`

**Ограничение для соцсетей Натальи:** не больше 1 короткой фразы (≤4 слов) подряд; избегать паттерна #49 «рваная медитативность». Ритм как в Telegram-постах: абзацы 2-4 предложения, короткое - только для акцента.

**Сканер (опционально):**
```bash
python3 -m venv skills/humanizer-ru/.venv
source skills/humanizer-ru/.venv/bin/activate
pip install razdel pymorphy3
python3 skills/humanizer-ru/skills/humanizer-ru/scripts/scan.py posts-emdr-memory/output/01-panic-night/max-post.md
```
