---
name: UE 5.7 핵심 소스 헤더 로컬 캐시
description: Animation Warping / AnimGraphRuntime / CharacterMovement / PoseSearch / BlendStack / ControlRig 핵심 헤더 11개 로컬 저장. 파라미터 기본값/enum/함수 시그니처 확증 시 Read로 즉시 조회.
type: reference
originSessionId: 6c06914e-adfc-4bcc-a415-ef22659354ec
---
## 위치

```
C:\Dev\Sanjuk-Unreal\cache\ue57\
```

## 인덱스 (UE 5.7 브랜치 기준, 2026-04-16 재캐싱 최신)

### Animation Warping 플러그인

| 파일 | 크기 | 경로 |
|------|------|------|
| `AnimNode_FootPlacement.h` | 28KB | Engine/Plugins/Animation/AnimationWarping/.../BoneControllers/ |
| `AnimNode_OrientationWarping.h` | 11KB | Engine/Plugins/Animation/AnimationWarping/.../BoneControllers/ |
| `AnimNode_SlopeWarping.h` | 4KB | Engine/Plugins/Animation/AnimationWarping/.../BoneControllers/ |

### AnimGraphRuntime 표준 노드

| 파일 | 크기 | 경로 |
|------|------|------|
| `AnimNode_LegIK.h` | 7KB | Engine/Source/Runtime/AnimGraphRuntime/Public/BoneControllers/ |
| `AnimNode_Inertialization.h` | 18KB | Engine/Source/Runtime/Engine/Classes/Animation/ |

### Motion Matching / PoseSearch

| 파일 | 크기 | 경로 |
|------|------|------|
| `PoseSearchSchema.h` | 10KB | Engine/Plugins/Animation/PoseSearch/.../PoseSearch/ |
| `PoseSearchDatabase.h` | 46KB | Engine/Plugins/Animation/PoseSearch/.../PoseSearch/ |
| `PoseSearchResult.h` | 13KB | Engine/Plugins/Animation/PoseSearch/.../PoseSearch/ |

### Character Movement

| 파일 | 크기 | 비고 |
|------|------|------|
| `CharacterMovementComponent.h` | 25KB (500줄) | 원본 177KB — 첫 500줄만 저장 |

### Control Rig

| 파일 | 크기 | 경로 |
|------|------|------|
| `RigUnit_BeginExecution.h` | 2.5KB | Engine/Plugins/Animation/ControlRig/.../Units/Execution/ |

### BlendStack (실험적)

| 파일 | 크기 | 경로 |
|------|------|------|
| `AnimNode_BlendStack.h` | 18KB | Engine/Plugins/Animation/BlendStack/.../BlendStack/ |

## How to apply

- UE 파라미터 기본값/enum 질문 → **먼저 이 캐시 Read**, GitHub API 호출 전에
- 캐시에 없는 파일이 필요하면 `gh api repos/EpicGames/UnrealEngine/contents/<path>?ref=5.7` 또는 raw URL로 추가 후 이 인덱스 업데이트
- UE 5.8 등 다른 버전 질문은 해당 브랜치 재조회 (캐시는 5.7 고정)
- cpp 파일은 필요시 개별 excerpt만 취득 (용량 큼)

## UnrealClaude Bridge (localhost:3000) 와 분담 (2026-05-18)

cache/ue57 은 **시점 고정 오프라인 캐시 (2026-04-17 재캐싱)**, UnrealClaude Bridge 는 **라이브 UE 5.7 API 문서 + C++ 어시스턴트** 11개 컨텍스트. 둘은 경쟁이 아니라 보완.

| 상황 | 우선 도구 | 이유 |
|---|---|---|
| 파라미터 기본값 / enum 즉답 | **cache/ue57 Read** | 1ms, 오프라인, 캐시 13 헤더 안에 있으면 끝 |
| 캐시에 없는 5.7 신규 클래스 | **UnrealClaude** | 라이브, 캐시 미추가분 보충 |
| C++ 코드 작성 / 시그니처 검증 | **UnrealClaude** | 어시스턴트 모드, UPROPERTY 자동 |
| 5.7 → 5.8 변경 추적 | UnrealClaude 또는 `gh api ref=5.8` | 캐시는 5.7 고정 |
| 오프라인 / Bridge 미응답 | cache/ue57 + gh api | UnrealClaude 폴백 |

워크플로우 예 (PC_01 FootPlacement 진단):
1. `Monolith animation_query.get_node_details` → 노드 class = `AnimNode_FootPlacement`
2. cache 우선 `Read cache/ue57/AnimNode_FootPlacement.h` → UPROPERTY 즉답
3. 캐시에 없는 새 멤버가 필요하면 `UnrealClaude` 로 라이브 조회
4. 변경 적용 = `Monolith blueprint_query.set_pin_default`

미응답 시 자동 폴백 순서: **UnrealClaude → cache/ue57 → gh api (EpicGames raw URL)**

## UnrealClaude contexts/ 13 가이드 (2026-05-18 cache 미러)

UnrealClaude bridge HTTP backend (localhost:3000) 는 30 액션 도구 외에 **사용 가이드 마크다운 13파일** 도 제공. 액션 도구는 Monolith 가 압도 (895 vs 30) 하지만, **가이드는 UnrealClaude 만** 가짐.

cache 위치: `C:\Dev\Sanjuk-Unreal\cache\ue57_contexts\`

| 파일 | 크기 | 용도 |
|---|---:|---|
| `actor.md` | 4KB | 액터 스폰/조작 패턴 |
| `animation.md` | 4KB | ABP / Animation 워크플로우 |
| `assets.md` | 4KB | 에셋 CRUD / import |
| `blueprint.md` | 9KB | BP 노드/그래프 편집 패턴 |
| `character.md` | 6KB | Character / MovementComponent |
| `enhanced_input.md` | 4KB | Enhanced Input 시스템 |
| `graymap.md` | **59KB** | 레벨 디자인 + graymap workflow (최대) |
| `material.md` | 4KB | Material 노드/파라미터 |
| `material_graph.md` | 9KB | Material 그래프 패턴 |
| `parallel_workflows.md` | 4KB | 병렬 작업 워크플로우 |
| `replication.md` | 3KB | Replication 패턴 |
| `slate.md` | 3KB | Slate UI |
| `ue-core-api.md` | 7KB | UE 핵심 API 사용 패턴 |

**cache/ue57/ (C++ 헤더) vs ue57_contexts/ (가이드)**:
- cache/ue57: 시그니처 / UPROPERTY / enum 즉답 (low-level)
- ue57_contexts: 사용 패턴 / 워크플로우 / 예시 코드 (high-level)
- 두 캐시 모두 동시 활용 가능: 시그니처 확인 + 사용 예 → 권장 코드 작성

업데이트: UnrealClaude 플러그인 P4 sync 후 다시 cp 로 미러 (스크립트화 가능).

관련 메모리: [[absorption-candidates-2026-05-18]], [[reference-monolith-animgraph-editing-limits]].

## 주요 소스 URL 템플릿

```
https://raw.githubusercontent.com/EpicGames/UnrealEngine/5.7/<path>
```

Authorization 헤더에 `gh auth token` 필요 (EpicGames 리포 private 접근).
