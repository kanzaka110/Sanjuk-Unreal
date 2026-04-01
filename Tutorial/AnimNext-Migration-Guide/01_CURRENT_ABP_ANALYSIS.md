# 01. 현재 ABP 분석: SandboxCharacter_CMC_ABP

[← 목차로 돌아가기](./00_INDEX.md) | [다음: AnimNext 개념 이해 →](./02_ANIMNEXT_CONCEPTS.md)

---

## 1.1 기본 정보

| 항목 | 값 |
|------|-----|
| **에셋 경로** | `/Game/Blueprints/SandboxCharacter_CMC_ABP` |
| **부모 클래스** | `AnimInstance` |
| **스켈레톤** | `/Game/Characters/UEFN_Mannequin/Meshes/SK_UEFN_Mannequin` |
| **구현 인터페이스** | `BPI_InteractionTransform`, `BPI_SandboxCharacter_ABP` |
| **그래프 수** | 60개 |
| **변수 수** | 76개 |
| **스테이트 머신** | 1개 (State Controller) |
| **총 의존성** | 42개 에셋 |

---

## 1.2 스테이트 머신: "State Controller"

### 구조도

```
                         ┌──────────────────┐
                         │  Transition to   │
              ┌─────────▶│    In Air        │─────────▶ In Air Loop
              │          └──────────────────┘
              │  (-> In Air, 크로스페이드 0.2초)
              │
 ┌────────────┴───────────────────────────────────────────────────┐
 │                                                                 │
 │   [진입] ──▶ Transition to Idle ──▶ Idle Loop ──▶ Idle Break   │
 │                    ▲                    ▲              │        │
 │                    │                    └──────────────┘        │
 │                    │  (Locomotion -> Idle)                      │
 │                    │                                            │
 │               Conduit ◀── (-> Grounded, 착지 시)               │
 │                    │                                            │
 │                    ▼  (HasAcceleration 조건)                    │
 │              Transition to Locomotion ──▶ Locomotion Loop       │
 │                                                                 │
 └─────────────────────────────────────────────────────────────────┘
```

### 상태 목록 (7개)

| # | 상태 이름 | 역할 | 위치 (X, Y) |
|---|----------|------|-------------|
| 1 | **Transition to Idle** | 진입 상태. Idle로 전환 준비 | (128, 224) |
| 2 | **Idle Loop** | 정지 상태 메인 루프 | (512, 224) |
| 3 | **Idle Break** | Idle 중 작은 모션 (몸 풀기) | (656, 96) |
| 4 | **Transition to Locomotion** | 이동 시작 전환 | (128, -144) |
| 5 | **Locomotion Loop** | 이동 상태 메인 루프 | (560, -144) |
| 6 | **Transition to In Air** | 공중 상태 전환 | (1200, -384) |
| 7 | **In Air Loop** | 공중 상태 메인 루프 | (1536, -384) |

### 트랜지션 규칙 (22개)

주요 트랜지션:

| From | To | 조건 | 크로스페이드 |
|------|----|------|-------------|
| Idle → Locomotion | Transition to Locomotion | `HasAcceleration == true` | 0.2초 |
| Locomotion → Idle | Transition to Idle | `HasAcceleration == false` | 0.2초 |
| Transition to Locomotion | Locomotion Loop | 애니메이션 완료 | 0초 |
| Transition to Idle | Idle Loop | 애니메이션 완료 | 0초 |
| -> In Air | Transition to In Air | `MovementMode == InAir` | 0.2초 |
| -> Grounded | Conduit → 분기 | `MovementMode == Walking` | 0.2초 |
| Idle Loop | Idle Break | 일정 시간 Idle 유지 | 0.2초 |
| Idle Break | Idle Loop | Idle Break 완료 | 0.2초 |

**Conduit 노드**: 착지 시 가속도 유무에 따라 Idle 또는 Locomotion으로 분기

---

## 1.3 변수 전체 목록 (76개)

### States 카테고리 (10개)

이 변수들은 캐릭터의 현재 상태를 추적합니다.
`_LastFrame` 접미사가 붙은 변수는 이전 프레임 값으로, **상태 변화 감지**에 사용됩니다.

| 변수명 | 타입 | 용도 |
|--------|------|------|
| `MovementMode` | byte (enum) | 현재 이동 모드 (Walking, Falling 등) |
| `MovementMode_LastFrame` | byte | 이전 프레임의 이동 모드 |
| `RotationMode` | byte (enum) | 회전 모드 (Velocity Direction, Looking Direction 등) |
| `RotationMode_LastFrame` | byte | 이전 프레임의 회전 모드 |
| `MovementState` | byte (enum) | 이동 상태 (Idle, Moving 등) |
| `MovementState_LastFrame` | byte | 이전 프레임의 이동 상태 |
| `Gait` | byte (enum) | 걸음 유형 (Walk, Run, Sprint) |
| `Gait_LastFrame` | byte | 이전 프레임의 걸음 유형 |
| `Stance` | byte (enum) | 자세 (Standing, Crouching) |
| `Stance_LastFrame` | byte | 이전 프레임의 자세 |

### Essential Values 카테고리 (16개)

캐릭터의 물리적 상태를 나타내는 핵심 값들입니다.

| 변수명 | 타입 | 용도 |
|--------|------|------|
| `CharacterProperties` | struct:S_CharacterPropertiesForAnimation | 캐릭터에서 전달받는 애니메이션 속성 구조체 |
| `CharacterTransform` | Transform | 현재 캐릭터 월드 트랜스폼 |
| `CharacterTransform_LastFrame` | Transform | 이전 프레임 트랜스폼 |
| `RootTransform` | Transform | 루트 본 트랜스폼 |
| `HasAcceleration` | bool | 가속도 존재 여부 (이동 입력 감지) |
| `Acceleration` | Vector | 현재 가속도 벡터 |
| `Acceleration_LastFrame` | Vector | 이전 프레임 가속도 |
| `AccelerationAmount` | float | 가속도 크기 (0~1 정규화) |
| `HasVelocity` | bool | 속도 존재 여부 |
| `Velocity` | Vector | 현재 속도 벡터 |
| `Velocity_LastFrame` | Vector | 이전 프레임 속도 |
| `RelativeAcceleration` | Vector | 캐릭터 로컬 공간 기준 상대 가속도 |
| `VelocityAcceleration` | Vector | 속도 기반 가속도 |
| `LastNonZeroVelocity` | Vector | 마지막으로 0이 아닌 속도 (방향 유지용) |
| `Speed2D` | float | 2D 평면 속도 크기 |
| `HeavyLandSpeedThreshold` | float | 강한 착지 판정 속도 기준값 |
| `InteractionTransform` | Transform | 상호작용 대상 트랜스폼 |
| `OffsetRootBoneEnabled` | bool | 루트 본 오프셋 활성화 여부 |

### Trajectory 카테고리 (7개)

Pose Search (Motion Matching)에서 사용하는 궤적 데이터입니다.

| 변수명 | 타입 | 용도 |
|--------|------|------|
| `TrajectoryGenerationData_Idle` | PoseSearchTrajectoryData | Idle 시 궤적 생성 파라미터 |
| `TrajectoryGenerationData_Moving` | PoseSearchTrajectoryData | 이동 시 궤적 생성 파라미터 |
| `Trajectory` | TransformTrajectory | 현재 생성된 궤적 |
| `TrajectoryCollision` | PoseSearchTrajectory_WorldCollisionResults | 궤적의 월드 충돌 결과 |
| `PreviousDesiredControllerYaw` | float | 이전 프레임의 목표 컨트롤러 Yaw |
| `Trj_PastVelocity` | Vector | 궤적 과거 속도 |
| `Trj_CurrentVelocity` | Vector | 궤적 현재 속도 |
| `Trj_FutureVelocity` | Vector | 궤적 미래 속도 (예측) |

### Motion Matching 카테고리 (6개)

| 변수명 | 타입 | 용도 |
|--------|------|------|
| `MMDatabaseLOD` | int | Motion Matching DB의 LOD 레벨 |
| `CurrentSelectedAnim` | Object | 현재 MM이 선택한 애니메이션 |
| `CurrentSelectedDatabase` | PoseSearchDatabase | 현재 사용 중인 PoseSearch DB |
| `ValidDatabases` | PoseSearchDatabase | 유효한 DB 목록 |
| `MM Search Cost` | float | 마지막 MM 검색 비용 |
| `CurrentDatabaseTags` | Name | 현재 DB의 태그 목록 |

### State Machine (Experimental) 카테고리 (15개)

실험적 Blend Stack 기반 스테이트 머신 변수들입니다.

| 변수명 | 타입 | 용도 |
|--------|------|------|
| `BlendStackInputs` | S_BlendStackInputs | 현재 Blend Stack 입력 데이터 |
| `Previous_BlendStackInputs` | S_BlendStackInputs | 이전 프레임 Blend Stack 입력 |
| `StateMachineState` | byte | 실험적 SM의 현재 상태 |
| `NoValidAnim` | bool | 유효한 애니메이션 없음 플래그 |
| `NotifyTransition_Re-Transition` | bool | 재전환 노티파이 |
| `NotifyTransition_ToLoop` | bool | 루프 전환 노티파이 |
| `UseExperimentalStateMachine` | bool | 실험적 SM 사용 여부 토글 |
| `MovementDirection` | byte | 이동 방향 (Forward, Backward 등) |
| `MovementDirectionLastFrame` | byte | 이전 프레임 이동 방향 |
| `MovementDirectionBias` | byte | 이동 방향 바이어스 |
| `MovementDirectionThresholds` | S_MovementDirectionThresholds | 방향 판정 임계값 |
| `TargetRotation` | Rotator | 목표 회전값 |
| `TargetRotationOnTransitionStart` | Rotator | 전환 시작 시점의 목표 회전 |
| `TargetRotationDelta` | float | 목표 회전 변화량 |
| `DebugExperimentalStateMachine` | bool | 실험적 SM 디버그 모드 |

### Foot Placement 카테고리 (5개)

| 변수명 | 타입 | 용도 |
|--------|------|------|
| `PlantSettings_Default` | FootPlacementPlantSettings | 기본 발 배치 설정 |
| `PlantSettings_Stops` | FootPlacementPlantSettings | 정지 시 발 배치 설정 |
| `InterpolationSettings_Default` | FootPlacementInterpolationSettings | 기본 보간 설정 |
| `InterpolationSettings_Stops` | FootPlacementInterpolationSettings | 정지 시 보간 설정 |
| `FootPlacementMode` | int | 발 배치 모드 선택 |

### 기타 카테고리

| 변수명 | 카테고리 | 타입 | 용도 |
|--------|---------|------|------|
| `OffsetRootTranslationRadius` | Root Offset | float | 루트 오프셋 이동 반경 |
| `HasOwningActor` | Default | bool | 소유 액터 존재 여부 |
| `UseThreadSafeUpdateAnimation` | Default | bool | 스레드 안전 업데이트 사용 |
| `LocomotionSetup` | Default | int | 로코모션 설정값 |
| `Mover` | Default | MoverComponent | Mover 컴포넌트 참조 |
| `Search Cost` | State Machine (Exp) | float | 검색 비용 |
| `ValidAnims` | State Machine (Exp) | AnimationAsset | 유효 애니메이션 목록 |
| `TransitionHistory` | Debug | string | 전환 이력 (디버그용) |
| `PawnSpeedHistory` | Debug | float | 속도 이력 |
| 기타 Debug 변수 4개 | Debug | float | 각종 히스토리 데이터 |

---

## 1.4 함수 분류 (59개)

### 업데이트 파이프라인 (7개)

ABP가 매 프레임 실행하는 핵심 업데이트 함수들입니다.
실행 순서가 중요합니다:

```
BlueprintThreadSafeUpdateAnimation(DeltaTime)
  └── Update_Logic()
        ├── Update_CVarDrivenVariables()      ← CVar 기반 변수 설정
        ├── Update_PropertiesFromCharacter()   ← 캐릭터에서 속성 가져오기
        ├── Update_EssentialValues()           ← 핵심 값 계산 (53노드, 가장 무거움)
        ├── Update_States()                    ← 상태 업데이트 (30노드)
        └── Update_Trajectory()               ← MM용 궤적 생성 (27노드)
```

| 함수명 | 노드 수 | 역할 |
|--------|---------|------|
| `BlueprintThreadSafeUpdateAnimation` | 6 | 진입점. DeltaTime을 받아 Update_Logic 호출 |
| `Update_Logic` | 8 | 모든 업데이트 함수를 순서대로 오케스트레이션 |
| `Update_CVarDrivenVariables` | 25 | 콘솔 변수에 의해 제어되는 변수 업데이트 |
| `Update_PropertiesFromCharacter` | 4 | 캐릭터 BP에서 속성 동기화 |
| `Update_EssentialValues` | 53 | 속도, 가속도, 변환 등 핵심 값 계산 |
| `Update_States` | 30 | MovementMode, Gait, Stance 등 상태 판정 |
| `Update_Trajectory` | 27 | Pose Search용 궤적 데이터 생성 |

### Motion Matching 함수 (6개)

| 함수명 | Pure | 노드 수 | 역할 |
|--------|------|---------|------|
| `Update_MotionMatching` | No | 9 | MM 노드 업데이트 콜백 |
| `Update_MotionMatching_PostSelection` | No | 13 | MM 선택 후 후처리 |
| `Get_MMBlendTime` | Yes | 15 | MM 블렌드 시간 결정 |
| `Get_MMInterruptMode` | Yes | 24 | 인터럽트 모드 결정 |
| `Get_MMNotifyRecencyTimeOut` | Yes | 9 | 노티파이 재사용 타임아웃 |
| `Get_PoseHistoryReference` | Yes | 5 | Pose History 참조 반환 |

### Movement Analysis 함수 (12개)

모두 Pure 함수 (부작용 없음, 상태 조회만):

| 함수명 | 노드 수 | 반환 타입 | 용도 |
|--------|---------|----------|------|
| `IsMoving` | 10 | bool | 캐릭터가 이동 중인지 |
| `IsStarting` | 14 | bool | 이동을 시작하는 순간인지 |
| `IsPivoting` | 9 | bool | 방향 전환 중인지 |
| `ShouldTurnInPlace` | 16 | bool | 제자리 회전이 필요한지 |
| `ShouldSpinTransition` | 14 | bool | 스핀 전환이 필요한지 |
| `JustTraversed` | 11 | bool | 방금 장애물을 넘었는지 |
| `JustLanded_Light` | 10 | bool | 가벼운 착지 직후인지 |
| `JustLanded_Heavy` | 10 | bool | 무거운 착지 직후인지 |
| `PlayLand` | 8 | bool | 착지 애니메이션 재생 여부 |
| `PlayMovingLand` | 11 | bool | 이동 중 착지 애니메이션 재생 여부 |
| `Get_TrajectoryTurnAngle` | 8 | double | 궤적 기반 회전 각도 |
| `Get_LandVelocity` | 4 | double | 착지 시 속도 |

### 실험적 State Machine 함수 (12개)

Blend Stack 기반 실험적 SM에서 사용하는 함수들:

| 함수명 | 노드 수 | 역할 |
|--------|---------|------|
| `SetBlendStackAnimFromChooser` | **64** | 상태별 Chooser 평가 후 애니메이션 설정 |
| `Get_DynamicPlayRate` | **53** | 속도 기반 동적 재생 속도 계산 |
| `IsAnimationAlmostComplete` | 10 | 현재 애니메이션 거의 완료 판단 |
| `OnStateEntry_IdleLoop` | 3 | Idle Loop 진입 시 콜백 |
| `OnStateEntry_TransitionToIdle` | 3 | Transition to Idle 진입 콜백 |
| `OnStateEntry_LocomotionLoop` | 5 | Locomotion Loop 진입 콜백 |
| `OnStateEntry_TransitionToLocomotion` | 5 | Transition to Locomotion 진입 콜백 |
| `OnUpdate_TransitionToLocomotion` | 7 | Locomotion 전환 중 매 프레임 업데이트 |
| `OnStateEntry_InAirLoop` | 3 | In Air Loop 진입 콜백 |
| `OnStateEntry_TransitionToInAir` | 3 | Transition to In Air 진입 콜백 |
| `OnStateEntry_IdleBreak` | 3 | Idle Break 진입 콜백 |
| `OnStateEntry_SlideLoop` | 3 | Slide Loop 진입 콜백 |
| `OnStateEntry_TransitionToSlide` | 3 | Transition to Slide 진입 콜백 |

### 보조 시스템 함수

#### Steering (2개)
| 함수명 | Pure | 반환 | 용도 |
|--------|------|------|------|
| `EnableSteering` | Yes | bool | 스티어링 활성화 여부 판단 |
| `Get_DesiredFacing` | Yes | Quat | 원하는 전방 방향 쿼터니언 |

#### Aim Offset (3개)
| 함수명 | Pure | 반환 | 용도 |
|--------|------|------|------|
| `Enable_AO` | Yes | bool | AO 활성화 여부 |
| `Get_AOValue` | Yes | (X, Y) double | AO 피치/요 값 |
| `Get_AO_Yaw` | Yes | double | AO 요 값만 |

#### Additive Lean (2개)
| 함수명 | Pure | 반환 | 용도 |
|--------|------|------|------|
| `CalculateRelativeAccelerationAmount` | Yes | Vector | 상대 가속도 계산 (29노드) |
| `Get_LeanAmount` | Yes | (X, Y) double | 기울기 양 |

#### Root Offset (5개)
| 함수명 | Pure | 반환 | 용도 |
|--------|------|------|------|
| `Get_OffsetRootRotationMode` | Yes | byte | 루트 회전 오프셋 모드 |
| `Get_OffsetRootTranslationMode` | Yes | byte | 루트 이동 오프셋 모드 |
| `Get_OffsetRootTranslationHalfLife` | Yes | double | 이동 오프셋 반감기 |
| `Get_OffsetRootTranslationRadius` | Yes | double | 이동 오프셋 반경 |
| `Get_OrientationWarpingWarpingSpace` | Yes | byte | Orientation Warping 공간 |

#### Foot Placement (3개)
| 함수명 | Pure | 반환 | 용도 |
|--------|------|------|------|
| `Get_FootPlacementPlantSettings` | Yes | FootPlacementPlantSettings | 발 배치 설정 |
| `Get_FootPlacementInterpolationSettings` | Yes | FootPlacementInterpolationSettings | 보간 설정 |
| `AllowFootPinning` | Yes | bool | Foot Pinning 허용 여부 |

#### Movement Direction (2개)
| 함수명 | 노드 수 | 용도 |
|--------|---------|------|
| `Update_MovementDirection` | 49 | 이동 방향 판정 및 업데이트 |
| `Get_MovementDirectionThresholds` | 17 | 방향 판정 임계값 (FL, FR, BL, BR) |

#### Target Rotation (2개)
| 함수명 | 노드 수 | 용도 |
|--------|---------|------|
| `Update_TargetRotation` | 25 | 목표 회전값 업데이트 |
| `Get_StrafeYawRotationOffset` | 15 | 스트레이프 Yaw 회전 오프셋 (const) |

#### Debug (1개)
| 함수명 | 노드 수 | 용도 |
|--------|---------|------|
| `Debug_ExperimentalStateMachine` | **171** | 실험적 SM 디버그 시각화 (가장 큰 그래프) |

---

## 1.5 연결된 에셋

| 에셋 | 타입 | 용도 |
|------|------|------|
| `BS_Neutral_AO_Stand` | Aim Offset (BlendSpace) | 상체 Aim Offset |
| `BS1D_Additive_Lean_Run` | BlendSpace 1D | 달리기 기울기 보정 |
| `StrafeOffsetCurveContainer` | AnimSequence (커브) | 스트레이프 오프셋 커브 데이터 |

총 의존성: **42개 에셋**

---

## 1.6 아키텍처 특이사항

### 1) 이중 로코모션 시스템
`UseExperimentalStateMachine` 변수로 두 가지 모드를 전환:
- **전통적 SM**: AnimGraph 내 State Controller 사용
- **실험적 SM**: Blend Stack + Chooser 기반 (`SetBlendStackAnimFromChooser`)

### 2) Thread-Safe 업데이트
`BlueprintThreadSafeUpdateAnimation`을 메인 진입점으로 사용하여 멀티스레드 안전한 업데이트를 수행합니다. 이는 UAF의 RigVM 멀티스레드 실행 모델과 유사한 접근입니다.

### 3) 프레임 비교 패턴
`_LastFrame` 접미사 변수로 프레임 간 상태 변화를 감지합니다:
```
현재 프레임 값 != 이전 프레임 값 → 상태 변경 발생
```
이 패턴은 UAF의 Data Interface에서 자동화할 수 있습니다.

### 4) MoverComponent 참조
ABP 이름에 "CMC"가 있지만, 실제로는 `Mover` (MoverComponent) 변수가 존재합니다. 이는 UE5의 새로운 Mover 시스템을 사용하고 있음을 나타냅니다.

### 5) 이미 UAF 친화적 구조
- Chooser 기반 애니메이션 선택 (`SetBlendStackAnimFromChooser`)
- Pose Search (Motion Matching) 통합
- Blend Stack 사용
- MoverComponent 참조

이 요소들은 UAF 변환 시 거의 그대로 재활용할 수 있습니다.

---

[← 목차로 돌아가기](./00_INDEX.md) | [다음: AnimNext 개념 이해 →](./02_ANIMNEXT_CONCEPTS.md)
