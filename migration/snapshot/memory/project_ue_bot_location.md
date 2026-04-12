---
name: UE_bot 코드 위치 변경
description: briefing.py 등 텔레그램 봇 코드가 desktop-tutorial에서 Sanjuk-Unreal/UE_bot/으로 이관됨
type: project
---

briefing.py를 포함한 UE 텔레그램 봇 코드가 `Sanjuk-Unreal/UE_bot/`로 이관됨 (2026-04-12).

**Why:** 기존 `desktop-tutorial` 리포에서 분리하여 Sanjuk-Unreal 레포 내에서 통합 관리하기 위함.

**How to apply:**
- briefing v2 (7개 모듈): `UE_bot/briefing*.py`
  - briefing.py (엔트리포인트), briefing_config.py, briefing_search.py,
    briefing_analyze.py, briefing_generate.py, briefing_notion.py, briefing_telegram.py
- 텔레그램 봇: `UE_bot/telegram_bot.py`
- 공유 설정: `shared_config.py` (루트, Claude CLI 유틸리티)
- 셋업 가이드: `UE_bot/SETUP.md`
