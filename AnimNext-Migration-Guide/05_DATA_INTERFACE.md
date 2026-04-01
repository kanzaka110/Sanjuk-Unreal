# 05. Data Interface 구성

[← 이전: Workspace & System 생성](./04_WORKSPACE_AND_SYSTEM.md) | [목차](./00_INDEX.md) | [다음: Animation Graph 구축 →](./06_ANIMATION_GRAPH.md)

---

## 5.1 개요

이 단계에서는 기존 ABP의 **76개 변수 시스템**을 UAF의 **Data Interface**로 변환합니다.

Data Interface는 UAF의 핵심 혁신 중 하나입니다:
- 기존: Character BP → ABP로 매 프레임 수동 전달 (수십 줄의 Set 노드)
- UAF: Data Interface가 필요한 데이터를 **자동으로 읽어옴**

---

## 5.2 기존 ABP의 데이터 흐름 문제

### 현재 구조의 문제점

```
Character BP (매 프레임):
  ┌──────────────────────────────────────────┐
  │ Get Anim Instance                        │
  │   → Cast to SandboxCharacter_CMC_ABP     │
  │     → Set Velocity                       │
  │     → Set Acceleration                   │
  │     → Set MovementMode                   │
  │     → Set RotationMode                   │
  │     → Set Gait                           │
  │     → Set Stance                         │
  │     → Set CharacterTransform             │
  │     → ... (수십 개의 수동 전달)           │
  └──────────────────────────────────────────┘

ABP 내부 (Update_EssentialValues, 53노드):
  ┌──────────────────────────────────────────┐
  │ Velocity → 길이 계산 → Speed2D           │
  │ Velocity → 0 비교 → HasVelocity          │
  │ Acceleration → 0 비교 → HasAcceleration  │
  │ Velocity - Velocity_LastFrame → 가속도    │
  │ ... (반복적인 파생 값 계산)               │
  └──────────────────────────────────────────┘
```

**문제**:
1. 수동 전달 코드가 길고 유지보수 어려움
2. 캐릭터와 ABP 간 강한 결합 (Cast 필요)
3. 파생 값 계산이 ABP에서 매 프레임 반복

### UAF Data Interface 해결책

```
AnimNextComponent:
  ┌──────────────────────────────────────────┐
  │ Data Interface 바인딩 (자동):             │
  │                                           │
  │ MoverComponent ──▶ Velocity              │
  │                 ──▶ Acceleration          │
  │                 ──▶ MovementMode          │
  │                                           │
  │ Actor          ──▶ Transform              │
  │                                           │
  │ → Cast 불필요, Set 노드 불필요            │
  │ → 컴포넌트 참조를 이름으로 자동 해결       │
  └──────────────────────────────────────────┘
```

---

## 5.3 변수 분류: 자동화 vs 수동 유지

76개 변수를 3가지 카테고리로 분류합니다:

### 카테고리 A: Data Interface가 자동 대체 (삭제 가능)

이 변수들은 Data Interface로 자동 읽을 수 있으므로 별도 변수가 불필요합니다.

| 기존 변수 | Data Interface 소스 | 비고 |
|----------|-------------------|------|
| `Velocity` | `MoverComponent.Velocity` | 자동 |
| `Velocity_LastFrame` | 프레임 비교 기능 내장 | 자동 |
| `Acceleration` | `MoverComponent.Acceleration` | 자동 |
| `Acceleration_LastFrame` | 프레임 비교 기능 내장 | 자동 |
| `HasVelocity` | `Velocity.Length() > 0` | Module에서 1줄 계산 |
| `HasAcceleration` | `Acceleration.Length() > 0` | Module에서 1줄 계산 |
| `Speed2D` | `Velocity.Size2D()` | Module에서 1줄 계산 |
| `CharacterTransform` | `Actor.GetActorTransform()` | 자동 |
| `CharacterTransform_LastFrame` | 프레임 비교 기능 내장 | 자동 |
| `MovementMode` | `MoverComponent.MovementMode` | 자동 |
| `MovementMode_LastFrame` | 프레임 비교 기능 내장 | 자동 |
| `Mover` | Data Interface 직접 참조 | 변수 불필요 |

**결과: ~12개 변수 삭제 가능**

### 카테고리 B: Module에서 간단히 계산 (대폭 축소)

이 변수들은 Module에서 계산하지만 기존보다 훨씬 간단해집니다.

| 기존 변수 | Module에서의 처리 | 기존 노드 수 → UAF |
|----------|------------------|-------------------|
| `RelativeAcceleration` | InverseTransform으로 1줄 | 29노드 → ~3노드 |
| `VelocityAcceleration` | Velocity 차분 | 일부 → 1줄 |
| `LastNonZeroVelocity` | 조건 저장 | ~5노드 → 1줄 |
| `AccelerationAmount` | 정규화 | ~3노드 → 1줄 |
| `RotationMode` | Mover에서 읽기 | ~5노드 → 자동 |
| `Gait` | Mover에서 읽기 | ~5노드 → 자동 |
| `Stance` | Mover에서 읽기 | ~5노드 → 자동 |
| `MovementState` | Velocity 기반 판정 | ~5노드 → 1줄 |
| 각종 `_LastFrame` 변수 | 프레임 히스토리 자동 | 수동 저장 → 자동 |

**결과: ~15개 변수가 크게 단순화**

### 카테고리 C: 그대로 유지 (Workspace 공유 변수)

UAF에서도 여전히 필요한 변수들입니다.

| 기존 변수 | 이유 |
|----------|------|
| `CharacterProperties` | 커스텀 구조체, 자동화 불가 |
| `TrajectoryGenerationData_Idle` | Pose Search 파라미터 |
| `TrajectoryGenerationData_Moving` | Pose Search 파라미터 |
| `Trajectory` | 생성된 궤적 데이터 |
| `TrajectoryCollision` | 궤적 충돌 결과 |
| `BlendStackInputs` | Blend Stack 입력 |
| `StateMachineState` | SM 상태 |
| `MovementDirection` | 이동 방향 |
| `MovementDirectionThresholds` | 방향 임계값 |
| `TargetRotation` | 목표 회전 |
| `PlantSettings_*` | Foot Placement 설정 |
| `InterpolationSettings_*` | Foot Placement 보간 |
| `FootPlacementMode` | Foot Placement 모드 |
| `OffsetRootBoneEnabled` | 루트 오프셋 |
| `OffsetRootTranslationRadius` | 루트 오프셋 반경 |
| `UseExperimentalStateMachine` | SM 모드 토글 |
| `LocomotionSetup` | 로코모션 설정 |
| `MMDatabaseLOD` | MM DB LOD |
| Debug 변수들 (7개) | 디버그 전용 |

**결과: ~30개 변수 유지**

### 요약

```
기존 76개 변수
  ├── 삭제 (Data Interface 대체): ~12개
  ├── 대폭 축소 (Module 간소화):  ~15개 → 각 1~3줄
  ├── 유지 (Workspace 변수):      ~30개
  └── 삭제 (Debug, UAF 내장):     ~19개
                                   ─────
                                   ~30개 변수로 축소 (60% 감소)
```

---

## 5.4 Data Interface 설정 방법

### 단계 1: AnimNextComponent에서 Data Interface 활성화

1. 테스트 캐릭터 BP (`BP_TestCharacter_UAF`)를 엽니다

2. **Add Component** → `AnimNextComponent` 검색 → 추가

3. AnimNextComponent의 **Details** 패널에서:
   - **Workspace**: `WS_SandboxCharacter` 할당
   - **Auto Activate**: 체크

### 단계 2: Data Interface Variable Binding

Workspace 에디터 또는 Module에서 Data Interface 변수를 바인딩합니다.

#### 바인딩 방식 이해

```
Data Interface 변수 바인딩 과정:

1. 변수 정의:
   Name: "Velocity"
   Type: FVector
   Source: "MoverComponent"
   Property: "Velocity"

2. 런타임 동작:
   AnimNextComponent
     → 소유 Actor에서 "MoverComponent" 검색
       → "Velocity" 프로퍼티 읽기
         → Data Interface 변수 "Velocity"에 자동 매핑
```

#### Module에서 Data Interface 사용

Module 그래프에서:

1. **우클릭** → **Get Data Interface Variable** 검색
2. 읽고 싶은 변수 선택 (예: Velocity)
3. 해당 노드의 출력 핀을 다른 노드에 연결

```
[Get DI: Velocity] ──▶ [Vector Length 2D] ──▶ [Set: Speed2D]
                                                  (Workspace 변수)
```

### 단계 3: 스레드 안전 데이터 교환

Data Interface는 스레드 경계를 넘는 데이터 교환을 자동 처리합니다:

```
Game Thread (캐릭터 로직)     Worker Thread (애니메이션)
┌─────────────────┐          ┌─────────────────┐
│ MoverComponent  │          │ Module          │
│   .Velocity     │──Proxy──▶│   DI.Velocity   │
│   .Acceleration │──Proxy──▶│   DI.Acceleration│
│   .MovementMode │──Proxy──▶│   DI.MovementMode│
└─────────────────┘          └─────────────────┘
        │                           │
        │    PublicVariablesProxy    │
        │   (자동 복사, 스레드 안전)  │
        └───────────────────────────┘
```

`AnimNextComponent::PublicVariablesProxy`가 Game Thread의 데이터를
Worker Thread로 안전하게 복사합니다.

---

## 5.5 기존 Update_PropertiesFromCharacter 대체

### 기존 코드 (ABP, 4노드)

```
Update_PropertiesFromCharacter():
  Get Owning Actor
    → Cast to SandboxCharacter
      → Get Character Properties
        → Set CharacterProperties 변수
```

### UAF 대체

Data Interface로 `CharacterProperties` 구조체를 자동 바인딩:

```
Data Interface Binding:
  Source Component: "SandboxCharacter" (Actor 자체)
  Property Path: "CharacterProperties"
  → 자동으로 Module에서 접근 가능
```

**결과**: 4노드 → 0노드 (완전 자동화)

---

## 5.6 기존 Update_EssentialValues 대체

### 기존 코드 (ABP, 53노드) - 주요 로직

```
Update_EssentialValues():
  1. Mover에서 Velocity 읽기 → Velocity 변수에 저장
  2. Velocity 길이 계산 → Speed2D
  3. Speed2D > 임계값 → HasVelocity
  4. Mover에서 Acceleration 읽기 → Acceleration 변수에 저장
  5. Acceleration 길이 > 임계값 → HasAcceleration
  6. Velocity - Velocity_LastFrame → VelocityAcceleration
  7. InverseTransformDirection → RelativeAcceleration
  8. Actor Transform 읽기 → CharacterTransform
  9. CharacterTransform vs LastFrame → 변화량 계산
  10. ... (더 많은 파생 값 계산)

  마지막:
    현재 값 → LastFrame 변수에 복사 (다음 프레임용)
```

### UAF 대체 (Module에서 ~10노드)

```
Module (UAF):
  // Data Interface가 자동 제공하는 값 (노드 0개):
  // - Velocity, Acceleration, CharacterTransform, MovementMode

  // Module에서 계산해야 하는 파생 값 (~10노드):
  Speed2D = DI.Velocity.Size2D()
  HasVelocity = Speed2D > 1.0
  HasAcceleration = DI.Acceleration.Size() > 0.01
  RelativeAcceleration = InverseTransformDirection(DI.ActorTransform, DI.Acceleration)

  // _LastFrame 변수: UAF의 프레임 히스토리 기능 사용
  // → 수동 복사 불필요
```

**결과**: 53노드 → ~10노드 (81% 감소)

---

## 5.7 기존 Update_States 대체

### 기존 코드 (ABP, 30노드) - 주요 로직

```
Update_States():
  1. Mover에서 MovementMode 읽기
  2. MovementMode vs LastFrame → 변경 감지
  3. RotationMode 판정
  4. Gait 판정 (Walk/Run/Sprint)
  5. Stance 판정 (Standing/Crouching)
  6. MovementState 판정 (Idle/Moving)
  7. 각 상태의 _LastFrame 저장
```

### UAF 대체

```
Module (UAF):
  // Data Interface 자동:
  // - MovementMode (MoverComponent에서 직접)

  // 판정 로직 (Chooser가 대부분 흡수):
  MovementState = HasVelocity ? Moving : Idle

  // Gait, Stance: MoverComponent의 태그 또는 상태에서 직접 읽기
  // → Chooser Table의 조건 컬럼으로 이동

  // _LastFrame: 프레임 히스토리 자동
```

**결과**: 30노드 → ~5노드 (83% 감소)

---

## 5.8 Workspace 변수 정의 (최종)

Workspace 에디터에서 다음 공유 변수를 생성합니다:

### States 그룹

| 변수명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `MovementState` | EMovementState (byte) | Idle | Idle/Moving |
| `Gait` | EGait (byte) | Run | Walk/Run/Sprint |
| `Stance` | EStance (byte) | Standing | Standing/Crouching |

### Motion Matching 그룹

| 변수명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `MMDatabaseLOD` | int | 0 | MM DB LOD 레벨 |
| `StateMachineState` | EStateMachineState (byte) | IdleLoop | 현재 SM 상태 |
| `BlendStackInputs` | S_BlendStackInputs | - | 블렌드 스택 입력 |

### Movement 그룹

| 변수명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `Speed2D` | float | 0.0 | 2D 평면 속도 |
| `HasVelocity` | bool | false | 속도 존재 여부 |
| `HasAcceleration` | bool | false | 가속도 존재 여부 |
| `MovementDirection` | EMovementDirection (byte) | Forward | 이동 방향 |
| `RelativeAcceleration` | Vector | (0,0,0) | 로컬 상대 가속도 |

### Target Rotation 그룹

| 변수명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `TargetRotation` | Rotator | (0,0,0) | 목표 회전 |
| `TargetRotationDelta` | float | 0.0 | 목표 회전 변화량 |

### Settings 그룹

| 변수명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `OffsetRootBoneEnabled` | bool | true | 루트 오프셋 활성화 |
| `OffsetRootTranslationRadius` | float | 5.0 | 오프셋 반경 |
| `FootPlacementMode` | int | 0 | Foot Placement 모드 |
| `LocomotionSetup` | int | 0 | 로코모션 설정 |

### Foot Placement 그룹

| 변수명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `PlantSettings_Default` | FootPlacementPlantSettings | - | 기본 발 배치 |
| `PlantSettings_Stops` | FootPlacementPlantSettings | - | 정지 발 배치 |
| `InterpolationSettings_Default` | FootPlacementInterpolationSettings | - | 기본 보간 |
| `InterpolationSettings_Stops` | FootPlacementInterpolationSettings | - | 정지 보간 |

### Trajectory 그룹

| 변수명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `TrajectoryGenerationData_Idle` | PoseSearchTrajectoryData | - | Idle 궤적 |
| `TrajectoryGenerationData_Moving` | PoseSearchTrajectoryData | - | Moving 궤적 |

**총: ~25개 변수 (기존 76개에서 67% 감소)**

---

## 5.9 확인 체크리스트

- [ ] 76개 변수를 A/B/C 카테고리로 분류 완료
- [ ] Data Interface 바인딩 소스 식별 완료
- [ ] Workspace 공유 변수 ~25개 정의 완료
- [ ] AnimNextComponent에서 Data Interface 활성화 확인
- [ ] Module에서 Data Interface 변수 접근 테스트 완료

---

[← 이전: Workspace & System 생성](./04_WORKSPACE_AND_SYSTEM.md) | [목차](./00_INDEX.md) | [다음: Animation Graph 구축 →](./06_ANIMATION_GRAPH.md)
