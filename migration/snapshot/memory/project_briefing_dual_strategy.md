---
name: 브리핑 병행 전략
description: briefing.py(자동/Notion) + Claude Code /briefing(심화/무료) 병행 운영 체계
type: project
---

2026-04-11부터 브리핑을 두 가지 방식으로 병행 운영.

**Why:** 자동 브리핑(briefing.py)은 일일 모니터링에 강하고, Claude Code `/브리핑`은 심화 분석에 적합. 모두 Claude CLI 사용으로 추가 비용 $0.

**How to apply:**

| 방식 | 용도 | 비용 |
|------|------|------|
| `briefing.py` (자동) | 일일 모니터링, Notion DB 자동 등록 | Claude CLI ($0) |
| `/브리핑` (Claude Code) | 심화 분석, 주간/월간 종합, 특정 주제 딥다이브 | Max 플랜 ($0) |

- briefing.py v2 (2026-04-12): 7개 모듈 분리, Map-Reduce, DDGS, 교차분석, 트렌드 추적
- 코드 위치: `UE_bot/briefing*.py` (7개 파일)
- `/브리핑` 명령어: `.claude/commands/브리핑.md`
