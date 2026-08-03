# Posts EMDR — Handoff

status: partial_vps_pending
updated_at: 2026-08-03
topic_id: sb-05-tolerate-uncertainty
title: Что происходит, если разрешить себе не знать, чем всё закончится
post_type: наблюдение→инсайт
site_url: https://morozovanatalia.ru/anxiety
mode: full publish

## Published (cloud)

| Platform | URL |
|----------|-----|
| Max | https://max.ru/se13417616_biz/AZ_HI8MTTQI |
| VK profile | https://vk.com/wall218367867_652 |
| VK group | https://vk.com/wall-224685309_153 |
| Facebook | https://www.facebook.com/632301483303094_122181018242837712 |

## Pending (VPS phase 3)

| Platform | Status |
|----------|--------|
| Telegram @nmorozova_emdr | pending |
| Telegram @natalia_morozova_psy | pending |
| b17 | pending |
| TenChat | out of scope |

## Blocker

INC-20260803-1800-vps-git-pull-dirty-tree — VPS git_pull merge conflict. Fix pushed: stash+reset in vps-webhook-server.py (branch cursor/short-blog-end-to-end-dcaa). Needs merge to main + webhook restart + retry POST /publish.

## Pipeline

- [x] Content all platforms
- [x] Cover (kie-cover.py)
- [x] Max + Facebook
- [x] VK MCP ×2 + photo gate
- [x] Registries max/vk/fb
- [x] git push (cloud)
- [x] VPS webhook 202 (git_pull failed)
- [ ] VPS: TG + b17 + --finish
- [ ] Do NOT mark published in queue (VPS --finish)

## Otchetik

Verdict: **partial** — cloud pass, VPS pending.
