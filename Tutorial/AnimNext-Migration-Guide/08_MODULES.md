# 08. Module 작성

[← 이전: Chooser + Motion Matching](./07_CHOOSER_AND_MOTION_MATCHING.md) | [목차](./00_INDEX.md) | [다음: Character BP 연결 →](./09_CHARACTER_INTEGRATION.md)

---

## 8.1 개요

이 단계에서는 기존 ABP의 **59개 함수**를 UAF **Module**로 이전합니다.
Data Interface와 Chooser가 대부분의 로직을 흡수하므로,
Module에서 구현해야 할 로직은 크게 줄어듭니다.

---

## 8.2 기존 59개 함수의 UAF 운명

### 삭제 가능 (Data Interface/Chooser가 대체): 29개

| 기존 함수 | 노드 수 | 대체 방법 |
|----------|---------|----------|
| `Update_PropertiesFromCharacter` | 4 | Data Interface 자동 |
| `Update_States` | 30 | Data Interface + Chooser 조건 |
| `Update_Trajectory` | 27 | Pose Search 내장 궤적 |
| `Update_MotionMatching` | 9 | MM Trait 콜백 |
| `Update_MotionMatching_PostSelection` | 13 | MM Trait 콜백 |
| `SetBlendStackAnimFromChooser` | 64 | Chooser + MM Trait (선언적) |
| `IsAnimationAlmostComplete` | 10 | MM 자동 전환 |
| `OnStateEntry_IdleLoop` | 3 | Chooser 행 |
| `OnStateEntry_TransitionToIdle` | 3 | MM 자동 전환 |
| `OnStateEntry_LocomotionLoop` | 5 | Chooser 행 |
| `OnStateEntry_TransitionToLocomotion` | 5 | MM 자동 전환 |
| `OnUpdate_TransitionToLocomotion` | 7 | MM 자동 처리 |
| `OnStateEntry_InAirLoop` | 3 | Chooser 행 |
| `OnStateEntry_TransitionToInAir` | 3 | MM 자동 전환 |
| `OnStateEntry_IdleBreak` | 3 | Chooser 행 |
| `OnStateEntry_SlideLoop` | 3 | Chooser 행 |
| `OnStateEntry_TransitionToSlide` | 3 | MM 자동 전환 |
| `Get_MMBlendTime` | 15 | MM Trait 파라미터 |
| `Get_MMInterruptMode` | 24 | MM Trait 파라미터 |
| `Get_MMNotifyRecencyTimeOut` | 9 | MM Trait 파라미터 |
| `Get_PoseHistoryReference` | 5 | MM Trait 자동 관리 |
| `Get_DynamicPlayRate` | 53 | Stride Warping Trait |
| `Get_OffsetRootRotationMode` | 6 | Root Offset Trait 파라미터 |
| `Get_OffsetRootTranslationMode` | 12 | Root Offset Trait 파라미터 |
| `Get_OffsetRootTranslationHalfLife` | 6 | Root Offset Trait 파라미터 |
| `Get_OffsetRootTranslationRadius` | 4 | Root Offset Trait 파라미터 |
| `Get_OrientationWarpingWarpingSpace` | 6 | Warping Trait 파라미터 |
| `Update_CVarDrivenVariables` | 25 | 에디터 설정 또는 Module 초기화 |
| `Debug_ExperimentalStateMachine` | 171 | UAF 내장 디버거 또는 별도 모듈 |

**삭제 노드 합계: ~530노드**

### Module로 이전 (간소화): 18개

| 기존 함수 | 기존 노드 | → UAF 노드 | 이전 방법 |
|----------|----------|------------|----------|
| `Update_EssentialValues` | 53 | ~10 | 파생값만 계산 |
| `Update_Logic` | 8 | ~5 | 파이프라인 축소 |
| `BlueprintThreadSafeUpdateAnimation` | 6 | 0 | System이 대체 |
| `IsMoving` | 10 | ~2 | 단순화 |
| `IsStarting` | 14 | ~3 | 단순화 |
| `IsPivoting` | 9 | ~3 | 단순화 |
| `ShouldTurnInPlace` | 16 | ~5 | Module 내 판정 |
| `ShouldSpinTransition` | 14 | ~4 | Module 내 판정 |
| `JustTraversed` | 11 | ~3 | Module 내 판정 |
| `JustLanded_Light` | 10 | ~3 | Module 내 판정 |
| `JustLanded_Heavy` | 10 | ~3 | Module 내 판정 |
| `PlayLand` | 8 | ~2 | Module 내 판정 |
| `PlayMovingLand` | 11 | ~3 | Module 내 판정 |
| `Get_TrajectoryTurnAngle` | 8 | ~3 | Module 내 계산 |
| `Get_LandVelocity` | 4 | ~2 | Module 내 계산 |
| `Update_MovementDirection` | 49 | ~15 | Module 내 또는 Chooser 흡수 |
| `Update_TargetRotation` | 25 | ~8 | Module 내 계산 |
| `Get_StrafeYawRotationOffset` | 15 | ~5 | Module 내 계산 |

### Trait 파라미터 바인딩으로 이전: 12개

| 기존 함수 | → Trait | 파라미터 |
|----------|--------|---------|
| `EnableSteering` | Steering Trait | Enable |
| `Get_DesiredFacing` | Steering Trait | DesiredFacing |
| `Enable_AO` | Aim Offset Trait | Alpha |
| `Get_AOValue` | Aim Offset Trait | X, Y |
| `Get_AO_Yaw` | Aim Offset Trait | X |
| `CalculateRelativeAccelerationAmount` | Module → Lean Trait | Value 계산 |
| `Get_LeanAmount` | Lean Trait | Value |
| `Get_FootPlacementPlantSettings` | Foot Placement Trait | PlantSettings |
| `Get_FootPlacementInterpolationSettings` | Foot Placement Trait | InterpolationSettings |
| `AllowFootPinning` | Foot Placement Trait | EnablePinning |
| `Get_MovementDirectionThresholds` | Module 내 계산 | Chooser 조건 |
| `Get_LandVelocity` | Module → Chooser 조건 | DB 선택 |

---

## 8.3 Module 생성

### 생성 단계

1. **Workspace 에디터** (`WS_SandboxCharacter`) 열기

2. **Asset Tree** → **Modules** 우클릭 → **Add New Module**

3. 이름: `Mod_SandboxCharacter_Logic`

4. Module 그래프 에디터가 열립니다

### Module 구조 설계

하나의 큰 Module 대신, 역할별로 나눌 수 있습니다:

```
Option A: 단일 Module (간단)
  Mod_SandboxCharacter_Logic
    ├── Essential Values 계산
    ├── Movement Analysis
    ├── Aim Offset 값 계산
    ├── Lean 값 계산
    └── Target Rotation 계산

Option B: 역할별 Module (확장성)
  Mod_EssentialValues         ← 핵심 값 계산
  Mod_MovementAnalysis        ← 이동 분석 판정
  Mod_AimAndLean              ← AO + Lean 계산
  Mod_TargetRotation          ← 회전 계산
```

**권장**: 처음에는 **Option A**로 시작하고, 필요 시 분리합니다.

---

## 8.4 Module 내용 작성: Essential Values

### 기존 Update_EssentialValues (53노드) → Module (~10노드)

```
Module: Mod_SandboxCharacter_Logic
Section: Essential Values

  ┌─────────────────────────────────────────────────────────┐
  │ // Data Interface에서 자동 제공 (노드 0개):              │
  │ // DI.Velocity, DI.Acceleration, DI.Transform,           │
  │ // DI.MovementMode                                       │
  │                                                          │
  │ // 파생 값 계산 (~10노드):                                │
  │                                                          │
  │ [Get DI: Velocity]                                       │
  │       │                                                  │
  │       ├──▶ [Vector Length 2D] ──▶ [Set: Speed2D]        │
  │       │                                                  │
  │       ├──▶ [> 1.0] ──▶ [Set: HasVelocity]              │
  │       │                                                  │
  │       └──▶ [Branch: HasVelocity]                        │
  │                 └──▶ [Set: LastNonZeroVelocity]          │
  │                                                          │
  │ [Get DI: Acceleration]                                   │
  │       │                                                  │
  │       └──▶ [Size > 0.01] ──▶ [Set: HasAcceleration]    │
  │                                                          │
  │ [Get DI: Acceleration] + [Get DI: Transform]            │
  │       │                                                  │
  │       └──▶ [Inverse Transform Direction]                │
  │              └──▶ [Set: RelativeAcceleration]            │
  └─────────────────────────────────────────────────────────┘
```

---

## 8.5 Module 내용 작성: Movement Analysis

### 기존 12개 판정 함수 → Module 내 조건 블록 (~30노드)

```
Module: Mod_SandboxCharacter_Logic
Section: Movement Analysis

  // IsMoving: Speed2D > 임계값
  [Get: Speed2D] ──▶ [> 10.0] ──▶ [Set: IsMoving]

  // IsStarting: 이전 프레임 !Moving → 현재 Moving
  [Get: IsMoving] + [Frame History: IsMoving_Prev]
    ──▶ [AND: IsMoving && !IsMoving_Prev] ──▶ [Set: IsStarting]

  // IsPivoting: 속도 방향 변화 > 임계값
  [Get DI: Velocity] + [Frame History: Velocity_Prev]
    ──▶ [Angle Between] ──▶ [> 45.0] ──▶ [Set: IsPivoting]

  // ShouldTurnInPlace: 정지 + 회전 차이 > 임계값
  [Get: !IsMoving] + [Get: TargetRotationDelta > 60.0]
    ──▶ [AND] ──▶ [Set: ShouldTurnInPlace]

  // JustLanded: MovementMode 변화 감지
  [Get DI: MovementMode] + [Frame History: MovementMode_Prev]
    ──▶ [Was Falling && Now Walking] ──▶ [Set: JustLanded]

  // JustLanded_Heavy: JustLanded + 속도 > 임계값
  [Get: JustLanded] + [Get DI: Velocity.Z < -HeavyThreshold]
    ──▶ [AND] ──▶ [Set: JustLanded_Heavy]
```

> **핵심 차이**: 기존에는 각각 독립된 Pure 함수 (10~16노드씩)였지만,
> Module에서는 Data Interface의 자동 데이터 + 프레임 히스토리로 **대폭 간소화**.

---

## 8.6 Module 내용 작성: Aim Offset & Lean

### Aim Offset 계산 (~5노드)

```
Module: Mod_SandboxCharacter_Logic
Section: Aim & Lean

  // Enable_AO: Idle 또는 느린 이동 시 활성화
  [Get: IsMoving] ──▶ [NOT] ──▶ [OR: + IsSlowWalk]
    ──▶ [Set: EnableAO]

  // AO Value: 컨트롤러 회전과 액터 회전의 차이
  [Get DI: Controller Rotation] - [Get DI: Actor Rotation]
    ──▶ [Normalize] ──▶ [Split: Yaw, Pitch]
      ──▶ [Set: AO_Yaw, AO_Pitch]
```

### Lean 계산 (~5노드)

```
  // Lean Amount: 상대 가속도 기반
  [Get: RelativeAcceleration]
    ──▶ [Normalize] ──▶ [* LeanMultiplier]
      ──▶ [Clamp: -1 ~ 1]
        ──▶ [Set: LeanAmount_X, LeanAmount_Y]
```

---

## 8.7 Module 내용 작성: Target Rotation

### 기존 Update_TargetRotation (25노드) → Module (~8노드)

```
Module: Mod_SandboxCharacter_Logic
Section: Target Rotation

  // 이동 방향 기반 목표 회전
  [Get DI: Velocity] ──▶ [Make Rot from X] ──▶ [Set: TargetRotation]

  // 스트레이프 모드인 경우: 컨트롤러 방향 사용
  [Get: RotationMode == Strafe]
    ──▶ [Branch]
      ├── True: [Get DI: Controller Yaw] ──▶ [Set: TargetRotation.Yaw]
      └── False: (위의 속도 기반 유지)

  // Delta 계산
  [Get: TargetRotation] - [Get DI: Actor Rotation]
    ──▶ [Delta Angle] ──▶ [Set: TargetRotationDelta]
```

---

## 8.8 Module에서 Trait 파라미터 출력

Module에서 계산한 값을 Animation Graph의 Trait에 전달하는 방법:

### Workspace 공유 변수를 통한 전달

```
Module                          Animation Graph
┌──────────────────┐            ┌──────────────────────┐
│                   │            │                       │
│ 계산 결과:        │  Workspace │  Trait 파라미터:      │
│                   │  Variables │                       │
│ [Set: Speed2D]   ─┼───────────┼─▶ Stride Warping.Speed│
│ [Set: EnableAO]  ─┼───────────┼─▶ AimOffset.Alpha     │
│ [Set: AO_Yaw]   ─┼───────────┼─▶ AimOffset.X         │
│ [Set: LeanAmt]  ─┼───────────┼─▶ Lean.Value           │
│ [Set: TargetRot] ┼───────────┼─▶ Warping.TargetRot    │
│                   │            │                       │
└──────────────────┘            └──────────────────────┘
```

### 흐름 정리

```
System 실행 순서:
  1. Data Interface 업데이트 (자동)
  2. Module 실행:
       - Essential Values 계산 → Workspace 변수에 저장
       - Movement Analysis → Workspace 변수에 저장
       - Aim/Lean 계산 → Workspace 변수에 저장
       - Target Rotation → Workspace 변수에 저장
  3. Animation Graph 실행:
       - 각 Trait가 Workspace 변수를 읽어서 파라미터로 사용
```

---

## 8.9 기존 vs UAF 노드 수 비교

| 영역 | 기존 ABP 노드 | UAF Module 노드 | 감소율 |
|------|-------------|----------------|--------|
| Essential Values | 53 | ~10 | 81% |
| Update States | 30 | ~5 | 83% |
| Update Trajectory | 27 | 0 (자동) | 100% |
| Update Logic | 8 | ~5 | 38% |
| Movement Analysis (12함수) | ~137 | ~30 | 78% |
| Motion Matching (6함수) | 75 | 0 (Trait) | 100% |
| State Machine (12함수) | 163 | 0 (Chooser) | 100% |
| Aim/Lean (5함수) | 72 | ~10 | 86% |
| Root Offset (5함수) | 34 | 0 (Trait) | 100% |
| Foot Placement (3함수) | 32 | 0 (Trait) | 100% |
| Target Rotation (2함수) | 40 | ~8 | 80% |
| Movement Direction (2함수) | 66 | ~15 | 77% |
| Steering (2함수) | 21 | ~5 | 76% |
| Debug | 171 | (별도 모듈) | - |
| CVarDriven | 25 | ~5 | 80% |
| **합계** | **~954** | **~93** | **90%** |

> **결론**: 기존 954노드 → UAF ~93노드로 **약 90% 감소**

---

## 8.10 확인 체크리스트

- [ ] `Mod_SandboxCharacter_Logic` Module 생성됨
- [ ] Essential Values 섹션 구현 (~10노드)
- [ ] Movement Analysis 섹션 구현 (~30노드)
- [ ] Aim & Lean 섹션 구현 (~10노드)
- [ ] Target Rotation 섹션 구현 (~8노드)
- [ ] 모든 출력이 Workspace 공유 변수에 저장됨
- [ ] System에서 Module 실행 노드가 올바른 순서에 배치됨
- [ ] Animation Graph의 Trait들이 Workspace 변수를 올바르게 참조함

---

[← 이전: Chooser + Motion Matching](./07_CHOOSER_AND_MOTION_MATCHING.md) | [목차](./00_INDEX.md) | [다음: Character BP 연결 →](./09_CHARACTER_INTEGRATION.md)
