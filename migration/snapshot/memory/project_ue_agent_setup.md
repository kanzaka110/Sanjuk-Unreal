---
name: UE 전문 에이전트 구성
description: 2026-04-12 구축한 UE5 전용 룰/명령어/훅/매크로 전체 구성 현황
type: project
originSessionId: 119b56cd-4bf6-4f42-a8cb-75582b9396a5
---
UE5 전문 에이전트 환경을 구축함 (2026-04-12).

**룰 세트 (.claude/rules/):**
- `ue-domain.md` — UE5 핵심 개념, ABP→UAF 용어 매핑
- `mcp-workflow.md` — MCP 도구 우선순위, 모듈 목록, 실패 처리
- `ue-coding.md` — UE C++/Blueprint 네이밍, UPROPERTY 패턴
- `monolith-macros.md` — 5개 워크플로우 매크로 (로코모션, 전투, 리타겟, AI, Cloth)
- `ue-agents.md` — 작업별 에이전트 선택 규칙
- `ue-versions.md` — 5.5→5.7 변경사항, Cloth 파라미터 참조

**추가 명령어:**
- `/ue-status` — MCP 빠른 상태 확인
- `/ue-debug` — 크래시/빌드 실패 진단
- `/ue-anim` — 애니메이션 작업 체크리스트
- `/ue-setup` — 새 프로젝트 MCP 세팅

**추가 훅:**
- `pre-unrealclaude-check.sh` — UnrealClaude 사전 점검
- `post-monolith-verify.sh` — Monolith 결과 에러 감지

**Why:** 매 대화마다 UE 도메인 지식을 자동 주입하여 전문성 유지
**How to apply:** 룰은 .gitignore에 !.claude/rules/ 추가로 git 동기화 필수
