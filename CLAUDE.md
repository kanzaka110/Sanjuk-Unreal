# CLAUDE.md

## 프로젝트 개요

UE5 애니메이션 관련 튜토리얼, 가이드, 리서치 자료 모음 리포지토리.

## 구조

```
Sanjuk-Unreal/
├── Tutorial/                      # 튜토리얼 및 가이드 모음
│   ├── Monolith-MCP-Tutorial/     # Monolith MCP 튜토리얼 (10편)
│   ├── runreal-MCP-Tutorial/      # runreal MCP 튜토리얼 (12편)
│   ├── AnimNext-Migration-Guide/  # AnimNext 마이그레이션 가이드 (13편)
│   ├── UAF-Setup-Guide/          # UAF 셋업 가이드 (12편)
│   ├── Chaos-Cloth-Guide/        # Chaos Cloth & Physics Asset 가이드 (10편)
│   ├── MayaMCP-Groom-Setup/      # Maya MCP + Groom 셋업 가이드
│   └── PC01-Hair-Workflow/       # PC_01_Hair_01 신규 제작 워크플로우 (10편, Maya→UE 자동화 포함)
├── Briefing/                      # 데일리 브리핑 아카이브 (날짜별)
├── UE_bot/                        # 텔레그램 봇 + 브리핑 자동화 (briefing.py v2)
├── shared_config.py               # 봇 공통 설정 (Claude CLI, 환경변수 검증)
├── .claude/commands/              # 커스텀 슬래시 명령어 (10개, /hermes 포함)
├── .claude/hooks/                 # Pre/PostToolUse 훅 (MCP 점검 3개) + Stop 훅(Hermes 자동공유, .claude/settings.json)
├── .claude/rules/                 # UE5 전용 룰 (도메인, MCP, 코딩, 매크로, 에이전트, 버전)
├── .claude/agents/                # 프로젝트 전용 에이전트 (animbp/sim × inspector/tuner + ue-root-cause-reviewer + ta-tool-builder)
├── migration/                     # 환경 마이그레이션 패키지 (backup/restore + snapshot)
├── Monolith-Local-Setup-Guide.md  # Monolith 로컬 전용 설치법
├── drone-npc100-proxy-transform-request.md # NPC_100 드론 프록시 transform 협의 요청 (프로그래밍팀 전달용)
├── kawaii-physics-sb2-research.md # KawaiiPhysics 종합 리서치 + SB2 적용 분석/개선안
├── UE-Animation-Tech-Report-2026.md  # UE 애니메이션 최신 기술 보고서
├── UE5-AI-GitHub-Research-2026.md    # UE5 AI/GitHub 리서치
└── Unreal_Briefing.md             # UE 애니메이션 데일리 브리핑 시스템
```

### UE5 프로젝트 (별도 관리, 이 레포에 포함하지 않음)
- **SB2** — SHIFTUP SB2 메인 프로젝트 (커스텀 UE 5.7.4)
  - 경로: `E:\Perforce\SB2\Workspace\Internal\SB2\SB2.uproject`
  - Monolith v0.20.3 (1230 액션 / 26 네임스페이스, 2026-07-02 measured) + UnrealClaude (포트 3000)
- **GameAnimationSample (GASP)** — Epic 공식 MM 샘플 + DynamicAdditiveOverlay 예제
  - 경로: `C:\Users\SHIFTUP\Documents\Unreal Projects\GameAnimationSample`

## 관련 프로젝트

| 프로젝트 | 용도 |
|---------|------|
| [desktop-tutorial](https://github.com/kanzaka110/desktop-tutorial) | UE 애니메이션 데일리 브리핑 코드 (private) |
| [Sanjuk-Claude-Code](https://github.com/kanzaka110/Sanjuk-Claude-Code) | Claude Code 플러그인 (원본 리포) |

## UE5 프로젝트 환경

- UE 프로젝트 경로: `C:\Users\ohmil\OneDrive\문서\Unreal Projects\`
- 현재 프로젝트: SB2 (5.7.4 커스텀), GameAnimationSample (GASP)
- Monolith 사용 시 UE 5.7 필요

## MCP 도구 우선순위

**Monolith가 최우선.** 에디터 제어가 필요한 모든 작업은 Monolith를 먼저 사용.

### UE 직접 제어 (3개)

| 우선순위 | 도구 | 포트/방식 | 용도 |
|---------|------|----------|------|
| 1 (메인) | **Monolith** | HTTP `localhost:9316` | 에디터 제어 전체 (v0.20.3 — 1230 액션 / 26 네임스페이스, 2026-07-02 measured) |
| 2 (보조) | **unrealclaude-bridge** (UnrealClaude v1.4.1) | Node bridge + `localhost:3000` | UE5.7 API 문서 컨텍스트 (11개), C++ 코딩 어시스턴트 |
| 3 (확장) | **unreal-mcp** (runreal) | `npx @runreal/unreal-mcp` | Python 스크립트 자동화, UAF 대비 |

### 보조 MCP (3개)

| 도구 | 방식 | 용도 |
|------|------|------|
| **context7** | `npx @upstash/context7-mcp` | 외부 라이브러리/프레임워크 docs (UE 외부) |
| **maya** | local Python (`C:/Dev/MayaMCP/`) | Maya 제어 (Groom 셋업) |
| **confluence** | `npx @aashari/mcp-server-atlassian-confluence` | 회사 위키 (shiftupcorp.atlassian.net) |

## 통합 작업 환경

Claude Code 실행 위치: `C:\dev\Sanjuk-Unreal` (루트)

- `.mcp.json` — MCP 서버 6개 등록 (monolith, unreal-mcp, unrealclaude-bridge, context7, maya, confluence)
- `.claude/settings.local.json` — Claude Code 로컬 설정
- `.gitignore` — UE5 바이너리/임시 파일 제외

SB2 프로젝트는 `E:\Perforce\SB2\Workspace\Internal\SB2`에 위치.
MCP 서버들이 절대 경로/HTTP로 설정되어 있어 루트에서 Claude Code를 실행해도 UE 제어 가능.

## 리모트 세션 (모바일 접속)

GCP + 로컬 PC 두 세션 동시 운영. 모바일 claude.ai/code에서 접속.

| 세션 | 환경 | 용도 | PC 꺼도 접근 |
|------|------|------|-------------|
| Sanjuk-Unreal (Local) | 로컬 PC | 문서 + Monolith/UE 제어 | X |
| Sanjuk-Unreal (GCP) | GCP VM (sanjuk-project) | 문서 작업 전용 | O |

- GCP 레포: `/home/kanzaka110/Sanjuk-Unreal/` (SSH 시 `kanzaka110@sanjuk-project` 유저 필수, ohmil 유저로 접근 불가)
- GCP tmux: `tmux attach -t unreal`
- 재시작: `scripts/gcp-restart-remote.sh`
- 로컬 시작: `scripts/local-remote-control.cmd`

**동기화:** 세션 간 대화는 공유되지 않음. 중요한 컨텍스트는 이 CLAUDE.md에 기록하고 git push/pull로 동기화.

## 작업 규칙

- 문서는 한국어로 작성
- 마크다운 파일명은 소문자와 하이픈 또는 숫자 접두사 사용
- 새 튜토리얼/가이드 추가 시 해당 폴더의 README.md 또는 00_INDEX.md 업데이트
- UE5 프로젝트 파일(Binaries, Intermediate, Saved, DerivedDataCache)은 커밋 금지

## 토큰 효율 (Max plan 한도 절약)

- **작업 단위로 `/clear`** — 한 세션 안에서 큰 dump가 누적되면 매 메시지 cache_read 비대. 작업 완료 후 새 세션
- **대량 enumerate 자제** — Monolith `getall AnimInstance` (100+ entries), `monolith_discover()` 전체 등은 컨텍스트 폭발. 필요 부분만 query
- **MCP 응답 필터링** — `get_graph_summary` (195 노드 풀 dump) 대신 `get_node_details` 로 노드 ID 명시 조회
- **거대 메모리 Read 시 offset/limit** — 5,000 tok 이상 파일은 offset 지정으로 부분 read
- **간단 작업은 Sonnet** — `/model claude-sonnet-4-6` 또는 명시. Opus는 복잡한 분석/그래프 작업만

## 세션 시작 시 필수 확인
- `~/claude-sync/session-bridge.md` 를 읽어서 다른 세션의 최근 작업을 파악할 것
- (회사 PC 한정) `C:/Users/SHIFTUP/.claude/shared-context/current-unreal.md` + `current-hermes-ops.md` 를 읽어 UE/SB2 작업 전제·Hermes 운영 컨텍스트 반영. 파일 없으면 멈추고 사용자 확인 (추측으로 다른 파일 대체 금지)
- current-context는 최신 컨텍스트일 뿐 ground truth 아님 — UE/SB2는 실측/PIE/로그/Monolith dump 최종 우선
- 관련 메모리에 최신 digest 충돌/stale 항목이 있으면 최신 ground truth 우선
