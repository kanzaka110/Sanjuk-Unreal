---
name: PC_01 JustLanded 로직 + E_SBMovementMode enum 4값 (정정)
description: PC_01_ABP UpdateVariables의 JustLanded edge detection 패턴. 정상 1프레임 latch 동작 확정. enum 4값 모두 식별됨 (2026-04-29 정정).
type: project
originSessionId: d94a9729-d40a-4c7f-809a-c13a80908c1a
---

# PC_01 JustLanded 로직 (2026-04-29 정정)

## 정정 사실 — JustLanded는 정상 1프레임 latch

이전 메모리(2026-04-28)의 "항상 false stuck" 가설은 **잘못된 관측**이었음. 사용자 PIE 검증에서 **앞으로 점프 / 제자리 점프 모두 정확히 1프레임 true 깜빡임 확인**.

이전 PrintString 관측에서 false 만 본 이유 추정: 1프레임은 화면 갱신 주기 타이밍 차이로 PrintString 출력 시점에 이미 false 로 복귀.

## 위치
- 에셋: `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP`
- 함수: `UpdateVariables` (BlueprintThreadSafeUpdateAnimation에서 호출)
- 호출 순서: SetDeltaTime → Update Trajectory → UpdateStates → **UpdateVariables** → UpdateTargetRotation → UpdateMoveSide

## 정상 동작 로직

```
JustLanded = (PrevMovementMode == InAir) AND (MovementMode == OnGround)
                                  ↑                         ↑
                              NewEnumerator5            NewEnumerator4
```

노드 ID:
- `K2Node_EnumEquality_4`: PrevMovementMode == NewEnumerator5 (InAir)
- `K2Node_EnumEquality_5`: MovementMode == NewEnumerator4 (OnGround)
- `K2Node_CommutativeAssociativeBinaryOperator_12`: BooleanAND
- `K2Node_VariableSet_42`: JustLanded set
- `K2Node_VariableSet_38`: IsHeavyLand (JustLanded AND |PrevVel.Z| > threshold)

## 프레임별 추적 (실측)

| Frame | CMC | UpdateStates 후 PrevMovementMode | UpdateStates 후 MovementMode | UpdateVariables 후 JustLanded |
|---|---|---|---|---|
| F-1 (공중) | Falling | InAir | InAir | false |
| **F (착지 프레임)** | Walking | **InAir** (전 frame 보존값) | **OnGround** | **TRUE** ⭐ |
| F+1 | Walking | OnGround | OnGround | false |

UpdateStates 시퀀스 1번 단계에서 `PrevMovementMode = MovementMode` 보존 (직전 frame 마지막 값)
시퀀스 후반에 Switch on EMovementMode로 MovementMode 갱신 → frame F 안에서 둘이 다른 값이 되는 1프레임 발생.

## E_SBMovementMode enum (4값 모두 식별 — 2026-04-29 확정)

경로: `/Game/Art/Character/PC/PC_01/MotionMatching/Data/E_SBMovementMode`

| 내부명 | DisplayName | 의미 |
|--------|-------------|------|
| NewEnumerator4 | **OnGround** | Walking/NavWalking |
| NewEnumerator5 | **InAir** | Falling (점프/낙하) |
| NewEnumerator6 | **OnSpline** | Spline 이동 (`IsSplineMoving=true` 시 덮어쓰기) |
| NewEnumerator7 | **Travel** | Flying (의도적 비행 이동) |

## EMovementMode → E_SBMovementMode 매핑 (UpdateStates Switch)

| UE EMovementMode | E_SBMovementMode |
|---|---|
| MOVE_None | OnGround |
| MOVE_Walking | OnGround |
| MOVE_NavWalking | OnGround |
| **MOVE_Falling** | **InAir** |
| MOVE_Swimming | (연결 끊김) 미처리 |
| MOVE_Flying | Travel |
| MOVE_Custom | (연결 끊김) 미처리 |

Switch 후 `IsSplineMoving==true` 면 OnSpline 으로 덮어씀.

## State Machine 트랜지션 룰 (Falling → TransitTo*)

JustLanded는 **트랜지션 룰에 사용되지 않음**. 트랜지션은 MovementMode 직접 비교:

```
From Fallng → TransitToGroundIdle:
  MovementMode == OnGround AND NOT IsMoving()

From Fallng → TransitToGroundMoving:
  MovementMode == OnGround AND IsMoving() AND PrevPendingWalkMode == PendingWalkMode
```

JustLanded는 **Chooser 평가 (OnStateEntry → SetStateMachineBlendStackAnim)** 시점에서만 사용. 즉 1프레임 latch가 그 평가 1회를 정확히 커버.

## How to apply
- JustLanded 관련 디버깅 시 PrintString 단독으로 false 보고도 stuck 으로 단정 금지. Animation Insights / Watch / Slow-mo 로 1프레임 깜빡임 확인 우선.
- enum 4값은 모두 확정됨. 새 변경 추가 시 4값 모두 고려.
- JustLanded 계산식 자체는 정상. 수정하지 말 것 (이전 시도 `(PrevMovementMode != OnGround)` 변경은 의미 없거나 부작용).
- 점프 후 착지 관련 freeze 는 별도 메모리 `project_pc01_jump_land_freeze.md` 참조.
