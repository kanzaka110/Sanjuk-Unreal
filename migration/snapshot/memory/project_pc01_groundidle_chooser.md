---
name: PC_01 GroundIdle Chooser가 Overlay 전환보다 늦게 반응하는 이유
description: GroundIdle ChooserTable이 OverlayPoseState 외에 Prev* 변수들을 매칭 조건으로 써서 1틱 이상 지연 발생. GroundMoving과의 비대칭.
type: project
originSessionId: a8a2881c-43ff-477a-bb1a-7537d544873c
---
**에셋 경로:** `/Game/Art/Character/PC/PC_01/StateMachine/GroundIdle`

**Chooser 바인딩 비대칭 (2026-04-22 uasset string 덤프):**

| Chooser | OverlayPoseState | Prev* 조건 |
|---|---|---|
| GroundIdle | 있음 | `bPrevIsMoving`, `PrevAnimStance`, `PrevIsFullBodySlotActive`, `PrevMovementMode`, `PrevPendingWalkMode`, `PrevWriggleMoveType` |
| GroundMoving | **없음** | `PrevMovementMode`, `PrevPendingWalkMode`, `PrevWriggleMoveType` (AnimStance는 현재값) |

**PC_01_ABP 업데이트 순서 (`BlueprintThreadSafeUpdateAnimation` exec 체인):**
```
SetDeltaTime → UpdateTrajectory → UpdateStates → UpdateVariables → UpdateTargetRotation → UpdateMoveSide
```

- `OverlayPoseState` Set ← **UpdateVariables** (VariableSet_65)
- `PrevAnimStance`, `PrevMovementMode` Set ← **UpdateStates**
- `PrevIsFullBodySlotActive`, `bPrevIsMoving` Set ← **UpdateVariables**
- Prev* 는 `Prev = 현재 (old)` 패턴이라 정의상 **tick N−1 값**

**지연 시나리오 (가드 ON):**
1. T0: OverlayPoseState=Guard 즉시, Overlay ABP 포즈는 정상 스위칭
2. T0 Chooser 평가: Prev* 는 아직 "이전 상태" → Guard 행 매칭 실패, 이전 행 유지
3. T+1틱: Prev* 싱크 → 비로소 Guard 행 선택
4. 가드 Start FullBody 몽타주가 끼면 `IsFullBodySlotActive=true→false` 의 한 틱 뒤에야 `PrevIsFullBodySlotActive=false` → "몽타주 종료 + 1틱" 추가 지연
5. BlendStack BlendTime(0.15~0.3s) + MM SearchThrottleTime → 시각적 지연 증폭

**Why:** 사용자가 "Overlay Pose State는 맞게 스위칭되는데 GroundIdle Chooser만 늦다"고 문의 (2026-04-22). uasset string 덤프 + blueprint_query search_nodes로 확증.

**How to apply:**
- Guard/Overlay 체감 지연 이슈는 Overlay ABP가 아닌 **GroundIdle Chooser 컬럼 바인딩** 문제로 접근
- Prev* 조건이 **히스테리시스로 의도된 건지** 먼저 확인 후 조치 (채터링 방지용일 수 있음)
- 해결 옵션: 해당 컬럼을 현재값 변수로 교체 + OnBecomeRelevant BlendIn / Inertialization 으로 1틱 깜빡임 흡수
- GroundMoving은 OverlayPoseState 컬럼 자체가 없어 같은 문제가 안 보임
