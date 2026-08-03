# Posts EMDR — Handoff

status: cloud_done_vps_blocked
updated_at: 2026-08-03
topic_id: sb-05-tolerate-uncertainty
mode: full publish

## Published (cloud)

| Platform | URL |
|----------|-----|
| Max | https://max.ru/se13417616_biz/AZ_HI8MTTQI |
| VK profile | https://vk.com/wall218367867_652 |
| VK group | https://vk.com/wall-224685309_153 |
| Facebook | https://www.facebook.com/632301483303094_122181018242837712 |

Site cover: https://morozovanatalia.ru/social-covers/sb-05-tolerate-uncertainty.jpg

## Blocked (VPS phase 3)

1. Restart webhook systemd (async server + clear hung process)
2. TenChat re-login (`tenchat-vnc-login.sh`)
3. Re-trigger: `curl ... /publish {"topic":"sb-05-tolerate-uncertainty"}`
4. Do NOT mark published until VPS --finish

incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260803-1045-tenchat-session-blocks-vps

=== POSTS EMDR DONE ===
(cloud phases complete; VPS deferred open)
