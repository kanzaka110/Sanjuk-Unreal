---
name: PC_01_ABP CDO 임계값 + 핵심 노드 설정 레퍼런스
description: PC_01_ABP의 CDO 임계값(TurnInPlace/Pivot/HoldTime)과 OffsetRootBone 노드 설정 실측. RootMotionMode 등 system 모드 포함.
type: reference
originSessionId: 1ac42bc0-21a9-4ffe-b4a1-61251faca330
---
PC_01_ABP 경로: `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP` (Blueprint/ 아래, Animation/ 아님)

**CDO 임계값 (2026-05-07 실측, get_cdo_properties)**:
- `TurnInPlaceThreshold = 40` (도) — turn-in-place 트리거 |Delta(CharacterRot, RootRot)| 임계. GASP default 45°와 유사
- `PivotAngleThreshold` (struct, 속도별):
  - Walking: 50, Jogging: 55, Running: 60, Sprinting: 60
- `HoldTimeThreshold = 0.03` (초) — IsMoving 상태 hold time, 매우 짧음
- `EvadeDurationThreshold = 0.05`
- `MaxTranslationError = 0` — OffsetRootBone translation 즉시 reset
- `HeavyLandZVelocityThreshold = 900`
- `MovementDirectionThresholds`: `MoveSide_LockOn_Default: []`, `MoveSide_Default: []` (CDO에선 빈 배열 — 함수에서 동적으로 채워질 가능성)

**ABP 시스템 모드**:
- `RootMotionMode = RootMotionFromMontagesOnly` — **AnimSequence는 root motion 무시**. PC_01은 input-driven CMC 시스템 (GASP의 root-motion-driven 아님). `RootMotionFromEverything`로 바꾸면 캐릭터가 안 움직이는 회귀 발생.

**OffsetRootBone 노드 (`AnimGraphNode_OffsetRootBone_0`, AnimGraph 단 1개)**:
- RotationMode: Interpolate, RotationHalfLife: 0.20s, RotationSpeedRatio: 0.5
- TranslationMode: Interpolate, TranslationHalflife: 0.10s, TranslationSpeedRatio: 0.5
- MaxRotationError: 원래 -1 (무제한). 2026-05-07 사용자가 45로 변경 시도했지만 무효 (offset 캡일 뿐). 현재 45 상태일 수 있음 — 원복 여부 미정.
- MaxTranslationError: 0 (즉시 reset)
- bUseManualRelease: **true** — Reset은 외부 이벤트(`OnResetOffsetRootBoneEvent`)로만 가능
- bResetEveryFrame: false
- EvaluationMode: Graph (그래프에서 핀으로 동적 제어 가능)
- bClampToTranslationVelocity: true, bClampToRotationVelocity: false
- CollisionTestingMode: ShrinkMaxTranslation, CollisionTestShapeRadius: 45, CollisionTestShapeOffset: (0,0,60)
- bOnGround: true

**State Machine** (`MoveStateMachine`): 12 states, 41 transitions, 변수 131개.
- 핵심 흐름: GroundMoving → TransitToGroundIdle → GroundIdle
- `GroundMoving → TransitToGroundIdle`: rule = `NOT IsMoving AND NOT HasEvade` (락온 분기 없음)
- `TransitToGroundIdle → GroundIdle`: rule = `(StateTime > X) AND IsStateMachineBlendStackAnimInBlendOut`
- `Re-Transit to GroundIdle → _toTTGI` (turn-in-place 트리거): rule = `Should Turn in Place AND StateTime > 0`
- `Should Turn in Place` 식 = `|Delta(CharacterRot, RootRot)| >= TurnInPlaceThreshold`

**OnStateEntry_TransitGroundIdle 실행 순서**:
1. `Set TargetRotationDeltaAtBeginState` (현재 delta 캐시)
2. `Set TargetRotationAtBeginState` (현재 rotation 캐시)
3. `SetStateMachineBlendStackAnim` ← EvieAnimChooser_StateMachine 평가 + Motion Match 1회 push

**Update 순서 (BlueprintThreadSafeUpdateAnimation)**:
DeltaTime → UpdateTrajectory → UpdateStates → UpdateVariables → UpdateTargetRotation → UpdateMoveSide

**Chooser** `/Game/Art/Character/PC/PC_01/StateMachine/EvieAnimChooser_StateMachine`: root 6 row (1 disabled, index 4), NestedChoosers 2개, ContextData 2개. sub-chooser 내부 protected (Monolith로 row 매핑 직접 검증 불가).
