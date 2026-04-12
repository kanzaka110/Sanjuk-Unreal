---
name: UE5 프로젝트 경로
description: MonolithTest(Monolith+UnrealClaude) 및 기타 UE 프로젝트의 로컬 경로
type: project
---

UE 프로젝트 기본 경로: `C:\Users\ohmil\OneDrive\문서\Unreal Projects\` (2026-04-06 최신화)

| 프로젝트 | UE 버전 | 플러그인 | 비고 |
|----------|---------|---------|------|
| MonolithTest | 5.7 | Monolith v0.12.0 + UnrealClaude v1.4.1 | 메인 테스트 프로젝트 |
| MetaHumans | 5.6 | — | |
| MetaHumans_5_5 | 5.5 | — | |
| SlayAnimationSample | 5.6 | — | |

UE 엔진 경로: `C:\Program Files\Epic Games\UE_5.7\`

**Why:** MonolithTest를 Sanjuk-Unreal 레포에서 분리함 (4.6GB → 별도 관리).

**How to apply:** MonolithTest 파일 참조 시 절대 경로 사용. git 커밋에 UE5 바이너리 포함 금지.
