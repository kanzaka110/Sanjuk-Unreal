# CLAUDE.md — 코어 라우팅 (토큰 최적화 v2, 2026-08-10)

UE5 애니메이션 튜토리얼/리서치 + SB2 작업 보조 리포. 상세 규칙은 상시 로딩하지 않는다 —
아래 라우팅 표의 도메인 파일을 **해당 작업을 시작할 때 Read** 한다.

## 도메인 라우팅 (작업 전 필독)

| 작업 | 먼저 Read |
|------|-----------|
| UE/SB2 에디터 제어, Monolith RPC | `.claude/rules-domain/mcp-workflow.md` |
| ABP/애니메이션 분석·튜닝·진단 | `.claude/rules-domain/ue-accuracy.md` (+`ue-domain.md`) |
| Monolith 멀티스텝 시퀀스 | `.claude/rules-domain/monolith-macros.md` |
| 에이전트(inspector/tuner) 위임 | `.claude/rules-domain/agent-triggers.md`, `ue-agents.md` |
| UE C++/BP 코드 작성 | `.claude/rules-domain/ue-coding.md` |
| UE 버전 차이, Chaos Cloth/PhysAsset 파라미터 | `.claude/rules-domain/ue-versions.md` |
| 리포 구조, 관련 프로젝트, 리모트/GCP 세션 | `.claude/rules-domain/repo-map.md` |

## 안전 계약 (항상 적용 — 원문은 rules-domain)

- **SB2 크래시/차단**: `//Game/...` 이중 슬래시 인풋 = read-only 호출도 에디터 즉시 fatal crash.
  `source.*`·`scripting python` 호출 금지(licensee 빌드 실패 확정). `monolith_discover` 전체·`getall` 100+ 금지 — 항상 targeted query.
- **write 액션**(`create_*/add_*/remove_*/set_*/connect_*/save_asset` 등)은 **사용자 승인 전 실행 금지**. Inspector=read-only, 변경=Tuner.
- **비가역 변경(Tier 2) 직전에만** `/evidence` 패킷 + 필요시 ue-root-cause-reviewer. Tier 0~1 일상 진단엔 검수 블록 자동 생성 금지 (`ue-accuracy.md` §0/§10).
- 수식어 없는 **"푸시" = Evidence Packet 메모리 업로드**. git push / P4 제출은 승호가 정확히 명시한 경우에만.
- 검증된 새 사실은 메모리 기록 + 신뢰도 태그 (✅실측 날짜 / ⚠가설·미적용 / 📄외부 / ❌폐기).

## UE5 프로젝트 경로

- SB2 (커스텀 UE 5.7.4): `E:\Perforce\SB2\Workspace\Internal\SB2\SB2.uproject`
  — Monolith v0.20.3 (HTTP localhost:9316), UnrealClaude (localhost:3000)
- GASP: `C:\Users\SHIFTUP\Documents\Unreal Projects\GameAnimationSample`
- 에셋 경로는 `/Game/...` 단일 슬래시, 에디터 Copy Reference로 취득

## MCP / 실행 프로필

- 우선순위: **Monolith(9316) 최우선** > unrealclaude-bridge(3000) > unreal-mcp(runreal). 실패 시 `/recover`.
- 기본 세션은 **monolith만** 연결. 다른 조합은 `scripts/claude-profiles/` 런처 사용:
  `claude-read`(조회, MCP 없음) / `claude-code`(구현, MCP 없음) / `claude-ue`(UE MCP 3종) / `claude-review`(읽기 전용 리뷰) / `claude-full`(전체 6종: maya·confluence·context7 포함)

## 토큰 규칙

- 작업 단위로 `/clear`. 대량 enumerate 금지. `get_graph_summary` 풀 dump 대신 `get_node_details`.
- 5,000tok+ 파일은 offset/limit read. 간단 작업은 Sonnet, Opus는 복잡 분석만.

## 세션 시작 확인

1. Work Brain(`H:\내 드라이브\Obsidian\Sanjuk Work Brain`): `00_START_HERE.md` → `01_WORK_RULES.md` → `02_RETRIEVAL.md` → `Areas\UE_SB2.md` 순서로 읽기
2. `~/claude-sync/session-bridge.md` + (회사 PC) `C:/Users/SHIFTUP/.claude/shared-context/current-unreal.md`, `current-hermes-ops.md`
   — 없으면 추측/다른 파일 대체 금지. 해당 컨텍스트에 의존하는 판단만 BLOCK, 탐색·실측은 계속.
3. current-context/메모리는 ground truth 아님 — 실측/PIE/로그/Monolith dump/P4 상태 최종 우선.

## Work Brain 경계

- 쓰기 허용: `Inbox\Company-Claude\`, `Projects\Company-Claude\` / 읽기 전용: `Sources\`, `Evidence\`, `Areas\`
- 투자·건강·개인 대화·인증정보 유입 금지. 중요 컨텍스트를 CLAUDE.md 본문에 누적하지 않는다 (초안=Inbox, 확정=Projects).

## 문서 규칙

한국어 작성. 파일명은 소문자-하이픈 또는 숫자 접두사. 가이드 추가 시 해당 폴더 README/00_INDEX 갱신.
UE Binaries/Intermediate/Saved/DerivedDataCache 커밋 금지.
