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
│   └── UAF-Setup-Guide/          # UAF 셋업 가이드 (12편)
├── Briefing/                      # 데일리 브리핑 아카이브 (날짜별)
├── .claude/commands/              # 커스텀 슬래시 명령어 (/push, /pull)
├── Monolith-Local-Setup-Guide.md  # Monolith 로컬 전용 설치법
├── UE-Animation-Tech-Report-2026.md  # UE 애니메이션 최신 기술 보고서
├── UE5-AI-GitHub-Research-2026.md    # UE5 AI/GitHub 리서치
└── Unreal_Briefing.md             # UE 애니메이션 데일리 브리핑 시스템
```

### 문서 (Tutorial/)
- **Monolith-MCP-Tutorial/** — Monolith MCP 튜토리얼 10편 (UE 5.7 + Claude Code 애니메이션 제어)
- **runreal-MCP-Tutorial/** — runreal MCP 튜토리얼 12편 (Python 기반 UE5 자동화)
- **AnimNext-Migration-Guide/** — AnimNext 마이그레이션 가이드 13편 (ABP → AnimNext 전환)
- **UAF-Setup-Guide/** — UAF 셋업 가이드 12편 (Universal Animation Framework)

### 리서치 및 브리핑 (루트)
- **Briefing/** — 데일리 브리핑 아카이브 (날짜별 폴더)
- **UE-Animation-Tech-Report-2026.md** — UE 애니메이션 최신 기술 보고서
- **UE5-AI-GitHub-Research-2026.md** — UE5 AI/GitHub 리서치 자료
- **Monolith-Local-Setup-Guide.md** — 회사 P4에 안 올리고 로컬에서만 Monolith 사용하는 방법
- **Unreal_Briefing.md** — UE 애니메이션 데일리 브리핑 시스템 설명

### UE5 프로젝트 (별도 관리, 이 레포에 포함하지 않음)
- **MonolithTest** — Monolith MCP 테스트용 UE 5.7 프로젝트
  - 경로: `C:\Users\ohmil\OneDrive\문서\Unreal Projects\MonolithTest`
  - Monolith v0.12.0 (1,125 액션, 16 모듈) + UnrealClaude v1.4.1 (20+ 도구)

## 관련 프로젝트

| 프로젝트 | 용도 |
|---------|------|
| [desktop-tutorial](https://github.com/kanzaka110/desktop-tutorial) | UE 애니메이션 데일리 브리핑 코드 (private) |
| [Sanjuk-Claude-Code](https://github.com/kanzaka110/Sanjuk-Claude-Code) | Claude Code 플러그인 (원본 리포) |

## UE5 프로젝트 환경

- UE 프로젝트 경로: `C:\Users\ohmil\OneDrive\문서\Unreal Projects\`
- 현재 프로젝트: MetaHumans (5.6), MetaHumans_5_5 (5.5), SlayAnimationSample (5.6), MonolithTest (5.7)
- Monolith 사용 시 UE 5.7 필요

## MCP 도구 우선순위

**Monolith가 최우선.** 에디터 제어가 필요한 모든 작업은 Monolith를 먼저 사용.

| 우선순위 | 도구 | 포트 | 용도 |
|---------|------|------|------|
| 1 (메인) | **Monolith** v0.12.0 | 9316 | 에디터 제어 전체 (1,125 액션 / 16 모듈) |
| 2 (보조) | **UnrealClaude** v1.4.1 | 3000 | UE5.7 API 문서 컨텍스트 (11개), C++ 코딩 어시스턴트 |
| 3 (확장) | **runreal** | stdio | Python 스크립트 자동화, UAF 대비 |
| 4 (특수) | **ChiR24/Unreal_mcp** | — | Cloth 시뮬레이션 (Chaos Cloth 유일 지원) |

## 통합 작업 환경

Claude Code 실행 위치: `C:\dev\Sanjuk-Unreal` (루트)

- `.mcp.json` — MCP 서버 3개 등록 (monolith, unreal-mcp, unrealclaude-bridge)
- `.claude/settings.local.json` — Claude Code 로컬 설정
- `.gitignore` — UE5 바이너리/임시 파일 제외

MonolithTest 프로젝트는 `C:\Users\ohmil\OneDrive\문서\Unreal Projects\MonolithTest`에 위치.
MCP 서버들이 절대 경로/HTTP로 설정되어 있어 루트에서 Claude Code를 실행해도 UE 제어 가능.

## 리모트 세션 (모바일 접속)

GCP + 로컬 PC 두 세션 동시 운영. 모바일 claude.ai/code에서 접속.

| 세션 | 환경 | 용도 | PC 꺼도 접근 |
|------|------|------|-------------|
| Sanjuk-Unreal (Local) | 로컬 PC | 문서 + Monolith/UE 제어 | X |
| Sanjuk-Unreal (GCP) | GCP VM (sanjuk-project) | 문서 작업 전용 | O |

- GCP 레포: `/home/ohmil/Sanjuk-Unreal/`
- GCP tmux: `tmux attach -t unreal`
- 재시작: `scripts/gcp-restart-remote.sh`
- 로컬 시작: `scripts/local-remote-control.cmd`

**동기화:** 세션 간 대화는 공유되지 않음. 중요한 컨텍스트는 이 CLAUDE.md에 기록하고 git push/pull로 동기화.

## 작업 규칙

- 문서는 한국어로 작성
- 마크다운 파일명은 소문자와 하이픈 또는 숫자 접두사 사용
- 새 튜토리얼/가이드 추가 시 해당 폴더의 README.md 또는 00_INDEX.md 업데이트
- UE5 프로젝트 파일(Binaries, Intermediate, Saved, DerivedDataCache)은 커밋 금지
