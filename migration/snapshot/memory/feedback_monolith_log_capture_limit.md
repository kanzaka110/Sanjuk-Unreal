---
name: monolith-log-capture-limit
description: Monolith editor.search_logs / tail_log 는 error/warning verbosity 만 캡처. LogBlueprintUserMessages (PrintString Display) 같은 일반 로그는 못 받는다.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

Monolith v0.12.1 의 editor.search_logs / tail_log / get_recent_logs 는 **error / warning verbosity 만 캡처**한다. log / verbose 카테고리 메시지는 capture buffer 에 안 들어간다.

**Why:** 2026-05-18 anim_rec_viewer Monolith 백엔드 PoC 작성 중 확인.
- `editor.get_log_stats` → total=6316 / error=2847 / warning=3469 / **log=0 / verbose=0**
- `editor.get_log_categories` 응답 27개 중 `LogBlueprintUserMessages` **빠짐** — capture 대상 외
- PC_01_ABP 의 [ANIM_REC] PrintString 출력은 LogBlueprintUserMessages 카테고리 (Display verbosity) → search_logs 로 0건 매칭
- 같은 데이터가 파일(SB2.log)에는 정상 기록됨

**How to apply:**
- 일반 PrintString / UE_LOG(LogTemp, Display) 결과를 라이브로 받고 싶으면 **파일 tail 모드 폴백** 필요. Monolith 로 못 받음.
- search_logs 는 빌드 오류, 크래시 분석, warning 추적에는 즉시 유용.
- ANIM_REC 같은 사용자 정의 로그를 Monolith 로 받으려면 ABP 의 PrintString 을 UE_LOG (Warning) 으로 출력하거나 다른 카테고리로 redirect.
- 흡수 후보 ① (`editor.tail_log` / `search_logs`) 의 적용 범위는 좁혀짐 — anim_rec_viewer 완전 대체 불가. 운용은 **하이브리드** (모노리스 진단 + 파일 폴백) 가 현실.

관련 메모리: [[pc01-anim-rewind-recorder]], [[absorption-candidates-2026-05-18]].
