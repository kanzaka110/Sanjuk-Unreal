# SB2 PC_01 ABP 구조 덤프

수집일: 2026-04-16  
Monolith 버전: 0.12.1  
실제 에셋 경로 기준: `/Game/Art/Character/PC/PC_01/` (소문자 Art)

---

## 1. PC_01 AnimBlueprint 에셋 목록

| 에셋명 | 경로 | 역할 |
|--------|------|------|
| **PC_01_ABP** | `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP` | 메인 바디 ABP |
| **PC_01_AnimLayer_IK** | `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK` | IK 레이어 |
| **PC_01_AnimLayerInterface** | `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayerInterface` | 레이어 인터페이스 정의 |
| **PC_01_AnimationLayerInterface_Overlay** | `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimationLayerInterface_Overlay` | 오버레이 레이어 인터페이스 |
| **PC_01_Body_001_PostProcess** | `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_Body_001_PostProcess` | 바디 PostProcess ABP |
| **CH_P_01_Head_001_AnimBlueprint** | `/Game/Art/Character/PC/PC_01/Head/CH_P_01_Head_001/Blueprints/` | 헤드 ABP |
| **CH_P_01_Head_001_PostProcess_AnimBP** | `/Game/Art/Character/PC/PC_01/Head/CH_P_01_Head_001/Blueprints/` | 헤드 PostProcess |

---

## 2. PC_01_ABP 메인 정보

```
asset_path:      /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP
skeleton:        /Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_Skeleton
parent_class:    SBActorAnimInstance
state_machine_count: 1
graph_count:     48
variable_count:  124
interfaces:
  - PC_01_AnimLayerInterface_C
  - PC_01_AnimationLayerInterface_Overlay_C
  - BPI_Travel_ABP_C
```

### 그래프 목록 (48개)
```
AnimGraph
Update Trajectory
SetReference
GetLeanAmount
Calculate Relative Acceleration Amount
IsMoving
IsStarting
IsPivoting
BlueprintThreadSafeUpdateAnimation
GetOffsetRootRotationMode
GetOffsetRootTranslationMode
GetOffsetRootTranslationHalfLife
UpdateStates
Get Interrupt Mode
GetDesireFacing
GetFootPlacementPlantSettings
GetFootPlacementInterpolationSettings
UpdateVariables
GetFootIKWeight
UpdateTargetRotation
DrawDebug
UpdateMoveSide
Get_DynamicPlayRate
Get_DesiredFacing
OnStateEntry_GroundIdle
SetStateMachineBlendStackAnim
IsStateMachineBlendStackAnimInBlendOut
OnStateEntry_GroundMoving
OnStateEntry_TransitGroundMoving
OnStateEntry_TransitGroundIdle
OnUpdate_TransitGroundMoving
OnStateEntry_Falling
OnStateEntry_TransitToFalling
shouldTurnInPlace
UpdateValueFromPostEvaluation
CalcWalkMode
OnStateEntry_Blocked
UpdatePendingWalkModeWithBuffer
Get_MoveSide
UpdateMovementStateWithBuffer
Get_MaxTranslationError
OnStateEntry_PlayingMontage
GetPrevSpeedThreshold
Get_TrajectoryTurnAngle
GetProceduralTargetTime
GetSteeringEnabled
OnStateEntry_SplineMoving
EventGraph
```

---

## 3. State Machine: MoveStateMachine

```
name:        MoveStateMachine
graph:       AnimGraph
entry_state: TransitToGroundIdle
state_count: 12
transition_count: 40
```

### 상태 목록

| 상태명 | 포지션 (X, Y) |
|--------|--------------|
| GroundIdle | (816, 832) |
| GroundMoving | (-480, 832) |
| TransitToGroundIdle | (784, 320) |
| TransitToGroundMoving | (-512, 320) |
| Falling | (336, -64) |
| TransitToFalling | (48, -64) |
| PlayingMontage | (-352, 1808) |
| _toTTF | (48, 32) |
| _toTTG | (-512, 448) |
| _toTTGI | (768, 448) |
| _toPM | (-352, 1680) |
| SplineMoving | (176, 848) |

### 주요 전환 규칙 (transition_count: 40)

| From | To | 페이드 시간 |
|------|----|-----------|
| FromGroundMoving | TransitToGroundIdle | 0.2s |
| TransitToGroundIdle | GroundIdle | 0.2s |
| TransitToGroundMoving | GroundMoving | 0.2s |
| From GroundIdle | TransitToGroundMoving | 0.2s |
| OnGround | TransitToFalling | 0.2s |
| TransitToFalling | Falling | 0.2s |
| From Fallng | TransitToGroundMoving | 0.2s |
| From Fallng | TransitToGroundIdle | 0.2s |
| FromLocomotion | PlayingMontage | 0.2s |
| FromPlayingMontage | _toPM | 0.2s |
| From Others (Non Spline Move) | SplineMoving | 0.2s |
| From Spline | TransitToGroundIdle | 0.2s |
| From Spline | TransitToGroundMoving | 0.2s |
| Re-Transit to GroundMoving | _toTTG | 0.2s |
| Re-Transit to GroundIdle | _toTTGI | 0.2s |
| Re-Transit to TransitFalling | _toTTF | 0.2s |

모든 블렌드 모드: `Other` (단방향)

---

## 4. Linked Layers (AnimGraph 내)

| 레이어명 | 인터페이스 | 클래스 |
|---------|-----------|--------|
| OverlayPose | PC_01_AnimationLayerInterface_Overlay | AnimGraphNode_LinkedAnimLayer |
| IK | PC_01_AnimLayerInterface | AnimGraphNode_LinkedAnimLayer |

### Linked ABP 의존성 (총 34개)
```
/Game/Art/Character/PC/PC_01/OverlaySystem/PC_OverlayLayerBlending
/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimationLayerInterface_Overlay
/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK
/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayerInterface
```

### BlendSpace 참조
```
/Game/Art/Character/PC/PC_01/Animation/Body/AdditiveLean/BS1D_P_Evie_Additive_lean
```

---

## 5. PC_01_ABP 변수 목록 (124개)

### 카테고리별 분류

#### Essential Values
| 변수명 | 타입 |
|--------|------|
| Delta Time | real |
| RootTransform | struct:Transform |
| CharacterTransform | struct:Transform |
| IsLockOn | bool |
| PrevIsLockOn | bool |
| Speed2D | real |
| TrjPrevSpeed2D | real |
| Acceleration | struct:Vector |
| PrevVelocity | struct:Vector |
| TrjPrevVelocity | struct:Vector |
| TrjVelocity | struct:Vector |
| TrjFutureVelocity | struct:Vector |
| bIsMoving | bool |
| bPrevIsMoving | bool |
| IsFullBodySlotActive | bool |
| PrevIsFullBodySlotActive | bool |
| TargetRotation | struct:Rotator |
| TargetRotationDelta | real |
| TurnInPlaceThreshold | real (EditInstance) |
| PivotAngleThreshold | struct:S_PivotAngleThreshold (EditInstance) |
| MovementDirectionThresholds | struct:S_MoveSideProfie (EditInstance) |
| bNonInputVelocity | bool |
| IsBlocked | bool |
| UseCorrectiveStep | bool |
| CurrentAnimTags | name |

#### States
| 변수명 | 타입 |
|--------|------|
| MovementState | byte |
| PrevMovementState | byte |
| MovementMode | byte |
| PrevMovementMode | byte |
| PendingWalkMode | byte |
| PrevPendingWalkMode | byte |
| AnimStance | byte |
| PrevAnimStance | byte |
| MoveSide | byte |
| PrevMoveSide | byte |

#### StateMachine
| 변수명 | 타입 |
|--------|------|
| BlendStackInputs | struct:S_BlendStackInputs |
| PrevBlendStackInputs | struct:S_BlendStackInputs |
| StateMachineMoveState | byte |
| NullAnim | bool |
| ReTransitState | bool |
| TransitToLoop | bool |
| SearchCost | real |
| TargetRotationAtBeginState | struct:Rotator |
| TargetRotationDeltaAtBeginState | real |
| RetransitReason | name |
| RunRetransit | bool |

#### Foot Placement
| 변수명 | 타입 |
|--------|------|
| FootPlacementAlpha | real |
| FootIKWeight | real |
| CurrentFootIKWeight | real |
| InterpolationSettingsDefault | struct:FootPlacementInterpolationSettings |
| InterpolationSettingsStops | struct:FootPlacementInterpolationSettings |
| InterpolationSettingsFullBody | struct:FootPlacementInterpolationSettings |
| PlantSettingsDefault | struct:FootPlacementPlantSettings |
| PlantSettingsStop | struct:FootPlacementPlantSettings |
| PlantSettingsFullBody | struct:FootPlacementPlantSettings |

#### Trajectory
| 변수명 | 타입 |
|--------|------|
| Trajectory | struct:TransformTrajectory |
| PoseSearchData_Moving | struct:PoseSearchTrajectoryData |
| PoseSearchData_Idle | struct:PoseSearchTrajectoryData |
| TrajectoryCollision | struct:PoseSearchTrajectory_WorldCollisionResults |
| PrevDesiredControllerYaw | real |
| CurrentSelectedDatabase | object:PoseSearchDatabase |
| TrjTurnAngle | real |
| TrjPastAngularVelocity | struct:Vector |
| TrjCurrentAngularVelocity | struct:Vector |
| TrjIsCircling | bool |

#### OverlayPose
| 변수명 | 타입 |
|--------|------|
| OverlayPoseState | byte |
| OverlayWeight | real |

#### Additive Lean / OrientationWarping
| 변수명 | 타입 |
|--------|------|
| VelocityAcceleration | struct:Vector |
| LeanAmount | real |
| Velocity | struct:Vector |
| NoneZeroVelocity | struct:Vector |

#### Reference
| 변수명 | 타입 |
|--------|------|
| SBCharacter | object:SBCharacter |
| SBCharacterMovement | object:SBCharacterMovementComponent |
| As PC 01 BP | object:PC_01_BP_C |
| IsSequenceBindingActor | bool |
| ACTravelLogic | object:AC_Travel_Logic_C |

#### Buffer (입력 버퍼링)
| 변수명 | 타입 |
|--------|------|
| PendingWalkModeAccumulatedTime | real |
| MovementModeAccumulatedTime | real |
| HoldTimeThreshold | real |
| CandidatePendingWalkMode | byte |
| PrevCandidatePendingWalkMode | byte |
| CandidateMovementState | byte |
| PrevCandidateMovementState | byte |

#### Offset Root Bone
| 변수명 | 타입 |
|--------|------|
| ResetOffset | bool |
| ResetOffsetPulse | bool |
| MaxTranslationError | real |

#### Wriggle
| 변수명 | 타입 |
|--------|------|
| bIsWriggling | bool |
| bPrevIsWriggling | bool |
| WriggleStart | bool |
| WriggleEnd | bool |
| InWriggle | bool |
| WriggleMoveType | byte |
| PrevWriggleMoveType | byte |

#### Evade
| 변수명 | 타입 |
|--------|------|
| HasEvade | bool |
| HasEvadeDuration | real |
| EvadeDurationThreshold | real |
| AirEvade | bool |

#### Jump/상태
| 변수명 | 타입 |
|--------|------|
| bJumping | bool |
| bDoubleJumping | bool |
| JumpCurrentCount | int |
| JumpPrevCount | int |
| IsHeavyLand | bool |
| HeavyLandZVelocityThreshold | real |
| JustLanded | bool |

#### Travel
| 변수명 | 타입 |
|--------|------|
| IsSplineMoving | bool |
| IsInTravel | bool |
| PrevIsInTravel | bool |
| InteractionTransform | struct:Transform |
| RuleMoveFlag | name |
| PrevRuleMoveFlag | name |

#### 기타
| 변수명 | 타입 |
|--------|------|
| LOD | int |
| bDrawDebug | bool |
| DebugOnScreen | bool |
| FullBodySlotWeight | real |
| PrevFullBodySlotWeight | real |
| IsStrafe | bool |
| PrevIsStrafe | bool |
| bIsStart | bool |
| bPrevIsStart | bool |
| MoveSideProfies | struct:S_MoveSideProfie |
| bActiveMaxAcceleration | bool |
| CurrAnimTag | name |
| PrevAnimTag | name |
| PrevShouldWriggel | bool |

---

## 6. PC_01_AnimLayer_IK 정보

```
asset_path:      /Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK
skeleton:        PC_01_Body_001_Skeleton
parent_class:    AnimInstance
state_machine_count: 0
graph_count:     2 (AnimGraph, EventGraph)
variable_count:  10
interfaces:      PC_01_AnimLayerInterface_C
```

### 변수 목록

| 변수명 | 타입 | 카테고리 |
|--------|------|---------|
| EnableHeadLookAt | bool | LookAtIK |
| EnableBodyLookAt | bool | LookAtIK |
| LookAtLocation | struct:Vector | LookAtIK |
| Body_LookAtSettings | struct:LookAtSetting | Look at IK |
| Head_LookAtSettings | struct:LookAtSetting | Look at IK |
| HitIK | struct:SBCharacterHitIK | 디폴트 |
| IsLockOn | bool | 디폴트 |
| PelvisSettingsDefault | struct:FootPlacementPelvisSettings | 디폴트 |
| PelvisSettingsProne | struct:FootPlacementPelvisSettings | 디폴트 |
| bUseFootIK | bool | Option (EditInstance) |
