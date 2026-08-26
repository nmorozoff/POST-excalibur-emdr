=== POSTS-EMDR-OTCHETIK ===
topic: sb-23-grounding-exercise
overall: fail
max_report_sent: true
incidents_written:
- INC-20260826-0948-sb23-telegram-proxy-stuck-port
fixic_needed: true
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260826-0948-sb23-telegram-proxy-stuck-port

## Summary
- Cloud OK: Max, VK×2, Facebook, OK
- VPS partial: b17 draft_saved (rate limit), Telegram fail (ASocks proxy timeout ×3, same port)
- Fixic: ASocks port refresh on exclude (d38b591)
- Recovery: VPS kill hung lock → git pull → one webhook retry
