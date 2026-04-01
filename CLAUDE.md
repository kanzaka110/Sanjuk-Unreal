# CLAUDE.md

## 프로젝트 개요

UE5 애니메이션 관련 튜토리얼, 가이드, 리서치 자료 모음 리포지토리.

## 구조

- **Monolith-MCP-Tutorial/** — Monolith MCP 튜토리얼 10편 (UE 5.7 + Claude Code 애니메이션 제어)
- **runreal-MCP-Tutorial/** — runreal MCP 튜토리얼 12편 (Python 기반 UE5 자동화)
- **AnimNext-Migration-Guide/** — AnimNext 마이그레이션 가이드 13편 (ABP → AnimNext 전환)
- **UAF-Setup-Guide/** — UAF 셋업 가이드 12편 (Universal Animation Framework)
- **Monolith-Local-Setup-Guide.md** — 회사 P4에 안 올리고 로컬에서만 Monolith 사용하는 방법
- **Unreal_Briefing.md** — UE 애니메이션 데일리 브리핑 시스템 설명

## 관련 프로젝트

| 프로젝트 | 용도 |
|---------|------|
| [desktop-tutorial](https://github.com/kanzaka110/desktop-tutorial) | UE 애니메이션 데일리 브리핑 코드 (private) |
| [Sanjuk-Claude-Code](https://github.com/kanzaka110/Sanjuk-Claude-Code) | Claude Code 플러그인 (원본 리포) |

## UE5 프로젝트 환경

- UE 프로젝트 경로: `C:\Users\ohmil\OneDrive\문서\Unreal Projects\`
- 현재 프로젝트: MetaHumans (5.6), MetaHumans_5_5 (5.5), SlayAnimationSample (5.6)
- Monolith 사용 시 UE 5.7 필요

## MCP 추천 조합 (애니메이션 특화)

```
Monolith (메인, 115 애니메이션 액션)
+ runreal/unreal-mcp (Python 확장/UAF 대비, 플러그인 불필요)
+ ChiR24/Unreal_mcp (Cloth 시뮬레이션, Chaos Cloth 유일 지원)
```

## 작업 규칙

- 문서는 한국어로 작성
- 마크다운 파일명은 소문자와 하이픈 또는 숫자 접두사 사용
- 새 튜토리얼/가이드 추가 시 해당 폴더의 README.md 또는 00_INDEX.md 업데이트
