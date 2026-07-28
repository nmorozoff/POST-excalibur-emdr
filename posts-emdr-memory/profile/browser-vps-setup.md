# b17 + TenChat на Linux VPS (Playwright)

**Рекомендуется:** `profile/browser-linux-vps-setup.md` — Ubuntu, тот же VPS что CRM.

Ниже — устаревший вариант **Windows + Undetectable** (если Linux недоступен).

Cloud pod **не может** запустить Undetectable. Решение: **Windows VPS** с Undetectable 24/7 и тем же Local API (`:25325`), к которому обращаются скрипты.

Два рабочих режима:

| Режим | Как | Когда |
|-------|-----|--------|
| **A — Remote API** | Cloud вызывает `UNDETECTABLE_BASE_URL=https://…` на VPS | Есть HTTPS-мост с Bearer; cloud достучится до VPS |
| **B — VPS worker (рекомендуется)** | Cloud пишет `browser-local-handoff.md`; VPS по cron делает `git pull` + `publish-browser-deferred.py` | Cloud **не** ходит в VPS; проще и безопаснее |

Оба режима используют **один и тот же** профиль Undetectable с сессиями b17 и TenChat.

---

## 1. Windows VPS

Минимум:

- Windows Server 2019+ или Windows 10/11
- 4 GB RAM, 2 vCPU
- RDP для первичной настройки

Провайдеры: Timeweb, Selectel, Hetzner (Windows), любой VPS с лицензией Windows.

---

## 2. Undetectable на VPS

1. Установить [Undetectable Browser](https://undetectable.io/) на VPS (как на Mac).
2. Создать профиль (или **импортировать** с Mac — экспорт/импорт профиля в Undetectable).
3. В профиле **вручную** залогиниться на b17.ru и tenchat.ru (один раз).
4. Убедиться, что Local API слушает `127.0.0.1:25325`:

```powershell
Invoke-RestMethod http://127.0.0.1:25325/status
```

Ожидается JSON с `"code": 0`.

5. Скопировать `profile_id` профиля → `UNDETECTABLE_PROFILE_ID` в `b17.env.local` и `tenchat.env.local`.

**Автозапуск:** Task Scheduler — при старте VPS запускать Undetectable; профиль можно держать «Started» или стартовать через API `/profile/start`.

---

## 3. Репозиторий на VPS

```powershell
git clone https://github.com/nmorozoff/POST-excalibur-emdr.git
cd POST-excalibur-emdr
copy posts-emdr-memory\b17.env.example posts-emdr-memory\b17.env.local
copy posts-emdr-memory\tenchat.env.example posts-emdr-memory\tenchat.env.local
```

На VPS в env:

```env
UNDETECTABLE_BASE_URL=http://127.0.0.1:25325
UNDETECTABLE_PROFILE_ID=<ваш profile_id>
```

Установить Python 3.11+.

Проверка:

```powershell
python scripts\browser_bridge_health.py
```

---

## 4. Режим B — VPS worker (рекомендуется)

### Поток

1. Cloud Agent: контент + `publish-topic.py` (фазы 1–2, VK через MCP).
2. Если Undetectable из cloud **недоступен** → создаётся `output/{topic}/browser-local-handoff.md`.
3. VPS каждые 10 мин:
   - `git pull`
   - при отсутствии `cover.png` — скачать с `cover_public_url` из `vk-mcp-handoff.json` (опциональный шаг в cron)
   - `python scripts\publish-browser-deferred.py --submit`

### Task Scheduler (пример)

Программа: `C:\Python311\python.exe`  
Аргументы: `C:\POST-excalibur-emdr\scripts\publish-browser-deferred.py --submit`  
Рабочая папка: `C:\POST-excalibur-emdr`  
Триггер: каждые 10 минут.

Перед publish — `git pull` в `.bat`:

```bat
cd C:\POST-excalibur-emdr
git pull --ff-only
python scripts\publish-browser-deferred.py --submit
```

### Обложка

`cover.png` в `.gitignore`. Варианты:

- Скрипт на VPS: `curl -o posts-emdr-memory/output/{topic}/cover.png` URL из `vk-mcp-handoff.json`
- Или rsync с Mac/FTP (тот же файл, что залили на сайт для VK)

---

## 5. Режим A — Remote API из Cloud

Cloud pod вызывает API на VPS. **Не открывайте :25325 в интернет без защиты.**

### Схема

```
Cloud Agent  --HTTPS + Bearer-->  nginx (VPS)  -->  127.0.0.1:25325
```

### nginx + Bearer

Пример: `posts-emdr-memory/examples/nginx-undetectable-bridge.conf.example`

На VPS:

1. TLS-сертификат (Let's Encrypt) на поддомен, например `browser-bridge.example.com`.
2. Сгенерировать длинный `UNDETECTABLE_API_BEARER` (32+ символов).
3. Проксировать только `/status`, `/profile/*` (минимально необходимые пути).

### Cursor Cloud Secrets (режим A)

Добавить в Dashboard:

```
UNDETECTABLE_BASE_URL=https://browser-bridge.example.com
UNDETECTABLE_PROFILE_ID=<тот же id>
UNDETECTABLE_API_BEARER=<секрет>
```

После `materialize_cloud_env.py` cloud preflight покажет `undetectable.ok: true`, и **фаза 3 выполнится в том же run** `publish-topic.py --submit`.

Проверка из любой машины:

```bash
curl -s -H "Authorization: Bearer YOUR_TOKEN" https://browser-bridge.example.com/status
```

---

## 6. Tailscale (альтернатива публичному HTTPS)

Если у вас **свой runner** (не изолированный Cursor Cloud) в той же Tailscale-сети:

```
UNDETECTABLE_BASE_URL=http://100.x.x.x:25325
```

Для **стандартного Cursor Cloud** Tailscale в pod обычно недоступен → используйте режим B или nginx.

---

## 7. Plan B — Playwright на Linux (без Undetectable)

Если Windows VPS не подходит:

- Linux VPS + Playwright + `storage_state.json` (cookies после ручного логина).
- Отдельные селекторы для b17/TenChat; при смене вёрстки — чинить скрипты.
- В репозитории пока **нет** Playwright-паблишера; это запасной путь с большей поддержкой.

Undetectable предпочтительнее: те же скрипты `publish-b17-blog.py` / `publish-tenchat-post.py`, меньше сюрпризов с антиботом.

---

## 8. Чеклист

- [ ] VPS Windows, Undetectable установлен и автозапуск
- [ ] Профиль с логинами b17 + TenChat
- [ ] `browser_bridge_health.py` → OK на VPS
- [ ] Режим B: Task Scheduler + `publish-browser-deferred.py`
- [ ] Или режим A: nginx + Secrets в Cursor Cloud
- [ ] Обложки: pull URL или rsync для `cover.png`

---

## 9. Связанные файлы

| Файл | Назначение |
|------|------------|
| `scripts/browser_bridge_health.py` | Проверка API |
| `scripts/publish-browser-deferred.py` | Cron на VPS |
| `scripts/undetectable_browser.py` | Клиент API + Bearer |
| `profile/cloud-publish-phases.md` | Фазы 1–3 в automation |
| `cloud-secrets-checklist.txt` | Secrets для режима A |
