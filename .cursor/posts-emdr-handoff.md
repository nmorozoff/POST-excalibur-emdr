# Posts EMDR — Handoff

=== POSTS EMDR DONE ===

status: partial_vps_pending
updated_at: 2026-08-03
topic_id: sb-05-tolerate-uncertainty
title: Что происходит, если разрешить себе не знать, чем всё закончится
post_type: наблюдение→инсайт
site_url: https://morozovanatalia.ru/anxiety
mode: full publish
otchetik: partial

## INC vps-pending

INC-20260803-1800-vps-git-pull-dirty-tree — VPS git_pull blocked phase 3. Fix merged to main (PR #12): stash+reset. **На VPS:** `git stash -u && git fetch origin main && git reset --hard origin/main && systemctl restart posts-emdr-webhook`, затем повтор `POST /publish`.

## Published (cloud)

| Platform | URL |
|----------|-----|
| Max | https://max.ru/se13417616_biz/AZ_HI8MTTQI |
| VK profile | https://vk.com/wall218367867_652 |
| VK group | https://vk.com/wall-224685309_153 |
| Facebook | https://www.facebook.com/632301483303094_122181018242837712 |

## Pending (VPS phase 3)

- Telegram @nmorozova_emdr, @natalia_morozova_psy
- b17.ru
- TenChat: out of scope

## Pipeline

- [x] Fixic gate (OPEN_INCIDENTS=0)
- [x] Content + cover (kie-cover.py)
- [x] Cloud Max + Facebook
- [x] VK MCP ×2
- [x] git push + PR #12 merged
- [x] VPS webhook 202 (×2; git_pull failed until VPS reset)
- [ ] VPS TG + b17 + --finish
