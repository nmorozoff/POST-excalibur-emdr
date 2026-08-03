# Fragment — sb-05-tolerate-uncertainty cloud publish

**Date:** 2026-08-03
**Topic:** sb-05-tolerate-uncertainty
**Mode:** full publish (cloud 1–2 done; VPS phase 3 blocked on TenChat + hung webhook)

## Done (cloud)

- Content all platforms + END_POST
- Cover: MCP nano_banana_2 (Runware insufficientCredits)
- Max https://max.ru/se13417616_biz/AZ_HI8MTTQI
- VK profile https://vk.com/wall218367867_652 (📸)
- VK group https://vk.com/wall-224685309_153 (📸)
- Facebook https://www.facebook.com/632301483303094_122181018242837712
- Registries max/vk-profile/vk-group/facebook
- Site cover on VPS FTP: https://morozovanatalia.ru/social-covers/sb-05-tolerate-uncertainty.jpg
- Queue NOT marked published (await VPS --finish)

## Fixic shipped this run

- VPS ensure_site_cover before platforms
- Soft TenChat session gate + cron continue
- Telegram ASocks port: no B17 CONNECT_PORT override
- Continue deferred if Telegram fails
- Webhook async 202 (needs systemd restart on VPS)

## Remaining

- Restart VPS webhook service; TenChat re-login; re-trigger publish for TG+b17+TenChat

incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260803-1045-tenchat-session-blocks-vps
