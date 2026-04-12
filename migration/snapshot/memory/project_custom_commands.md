---
name: 커스텀 명령어 및 훅
description: 9개 명령어 + 3개 훅 구성 현황 (UE 전용 4개 포함)
type: project
originSessionId: 119b56cd-4bf6-4f42-a8cb-75582b9396a5
---
`.claude/commands/`에 9개 명령어, `.claude/hooks/`에 3개 훅 스크립트 운영.

**기본 명령어:**
- **/push**: 메모리 갱신 → CLAUDE.md 점검 → git commit & push → GCP 동기화 (stale branch 감지 포함)
- **/pull**: 로컬 상태 확인 → git pull → 변경사항 분석 → 메모리 동기화
- **/doctor**: MCP 3개 + UE5 프로젝트 + Git + 메모리 전체 환경 진단
- **/recover**: MCP 연결 실패, Git stale, UE5 셰이더 등 알려진 실패 시나리오 자동 복구
- **/브리핑**: 심화 브리핑 — UE5 애니메이션 기술 종합 리서치

**UE 전용 명령어 (2026-04-12 추가):**
- **/ue-status**: MCP 연결 빠른 확인 (3초)
- **/ue-debug**: 크래시/빌드 실패 단계별 진단
- **/ue-anim**: 애니메이션 작업 시작 체크리스트
- **/ue-setup**: 새 프로젝트 MCP 연결 세팅

**훅 (3개):**
- `pre-monolith-check.sh` — Monolith 미응답 시 deny + `/recover` 안내
- `pre-unrealclaude-check.sh` — UnrealClaude Bridge 미응답 시 deny
- `post-monolith-verify.sh` — Monolith 결과 에러 패턴 감지 알림

**Why:** MCP 하드닝 + UE 전문 에이전트 작업 효율화
**How to apply:** 새 명령어는 `.claude/commands/`, 훅은 `.claude/hooks/` + settings.local.json 등록
