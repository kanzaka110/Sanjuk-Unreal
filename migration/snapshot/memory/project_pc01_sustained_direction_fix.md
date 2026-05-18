# PC_01 SustainedDirection 시스템 결함 2건 수정 (2026-05-13)

## 배경

`UpdateSustainedDirectionWithBuffer` 함수 + `bSustainedDirPivotTrigger` (sdpt) 플래그.
- 목적: |TrjTurnAngle| < StableThreshold 인 상태가 일정 시간(SustainedDirMinTime) 이상 유지된 후, 큰 방향 전환(|tta| >= AngleThreshold) 발생 시 한 틱 sdpt=true 트리거.
- AnimRewindRecorder가 sdpt를 캡처해 로그 진단.

## 진단된 결함 (Inspector)

1. **race condition**: `BlueprintThreadSafeUpdateAnimation` 에서 호출 순서가 `Trajectory → UpdateStates → UpdateVariables → ...` 였음. UpdateStates 내 Sequence then_3 에서 UpdateSustainedDirectionWithBuffer가 호출되는데, 이 시점엔 같은 틱의 TrjTurnAngle / Speed2D 가 아직 UpdateVariables 갱신 전이라 **이전 틱 값**으로 sdpt 판정. ANIM_REC는 같은 틱 후반(또는 다음 틱) 캡처라 새 TrjTurnAngle + 리셋된 sdt + 이전 틱 기반 sdpt 가 함께 로그되어 모순처럼 보임.

2. **설계 결함**: 정지 상태(Speed2D ≈ 0, |TrjTurnAngle| < Stable)에서도 sdt 무한 누적. 정지 → 회전 시작 시 즉시 sdpt=true 가능 → false trigger.

## Step A: Speed 게이트 추가 (식 강화)

### 추가 변수
- `SustainedDirMinSpeed`: double, default **50.0**, category "Essential Values", instance_editable=true, blueprint_read_only=false

### 새 식
```
DirStable = (|TrjTurnAngle| < SustainedDirStableThreshold)
            AND (Speed2D >= SustainedDirMinSpeed)
```

### 그래프 변경 (UpdateSustainedDirectionWithBuffer 함수)
신규 노드 4개:
- `K2Node_VariableGet_8` = Get Speed2D
- `K2Node_VariableGet_9` = Get SustainedDirMinSpeed
- `K2Node_CallFunction_8` = GreaterEqual_DoubleDouble (Speed >= MinSpeed)
- `K2Node_CallFunction_9` = BooleanAND (기존 `|tta|<Stable` AND Speed gate)

결선 변경:
- 기존 `K2Node_CallFunction_1.ReturnValue` (Less) → `K2Node_CallFunction_4.A` (NOT) **끊고**
- 기존 `K2Node_CallFunction_1.ReturnValue` (Less) → `K2Node_IfThenElse_0.Condition` **끊고**
- 새 `K2Node_CallFunction_9.ReturnValue` (새 AND) 가 NOT.A 와 Branch.Condition 둘 다 공급
- 기존 Less.ReturnValue 는 새 AND.A 로, GE.ReturnValue 는 새 AND.B 로 들어감

## Step B: BlueprintThreadSafeUpdateAnimation 호출 순서 스왑

### 분석
- `TrjTurnAngle`/`Speed2D` Set 위치: **UpdateVariables** 함수 (단 1곳씩)
- `UpdateSustainedDirectionWithBuffer` 호출 위치: **UpdateStates** 함수 Sequence then_3
- 두 함수는 `BlueprintThreadSafeUpdateAnimation` 그래프에서 순차 호출됨

### 기존 체인
```
Set Delta Time → Update Trajectory → UpdateStates → UpdateVariables → UpdateTargetRotation → UpdateMoveSide
                                       ^^^^^^^^^^^^   ^^^^^^^^^^^^^^^
                                       (sdpt 판정)    (TrjTurnAngle/Speed2D Set)
```
→ sdpt가 항상 이전 틱 값으로 판정됨.

### 새 체인 (수정 후)
```
Set Delta Time → Update Trajectory → UpdateVariables → UpdateStates → UpdateTargetRotation → UpdateMoveSide
                                       ^^^^^^^^^^^^^^^   ^^^^^^^^^^^^
                                       (값 Set 먼저)     (sdpt 판정)
```

### 결선 변경 (BlueprintThreadSafeUpdateAnimation)
노드 ID:
- `K2Node_VariableSet_2` = Set Delta Time
- `K2Node_CallFunction_7` = Update Trajectory
- `K2Node_CallFunction_16` = UpdateStates
- `K2Node_CallFunction_1` = UpdateVariables
- `K2Node_CallFunction_0` = UpdateTargetRotation
- `K2Node_CallFunction_4` = UpdateMoveSide

3 disconnect + 3 connect:
- DISC Trajectory.then ↔ States.execute
- DISC States.then ↔ Variables.execute
- DISC Variables.then ↔ TargetRotation.execute
- CONN Trajectory.then → Variables.execute
- CONN Variables.then → States.execute
- CONN States.then → TargetRotation.execute

## 영향 분석

UpdateVariables를 UpdateStates 앞으로 이동했을 때 UpdateStates의 Sequence 다른 분기(then_0~then_2) 영향:
- **then_0**: PrevMovementMode 캐시 + Switch on EMovementMode → MovementMode/PendingWalkMode 갱신. CMC MovementMode는 별도 입력이라 Variables 의존 X. 안전.
- **then_1**: PrevPendingWalkMode/JustExitedSprint 캐시 + PendingWalkMode 갱신. 자체 trigger 기반. 안전.
- **then_2**: PrevAnimStance + AnimStance 캐시. 자체. 안전.
- **then_3**: UpdateSustainedDirectionWithBuffer — **의도된 수혜자** (Speed2D/TrjTurnAngle 같은 틱 값 사용 가능).

## 검증

- compile_blueprint: errors 0, warnings 0 (Step A 후 + Step B 후 둘 다)
- save_asset: 실패 (메모리 `reference_monolith_animgraph_editing_limits.md` 알려진 현상 — read-only/P4 unchecked. 컴파일 성공이면 다음 PIE 진입 시 적용)

## 백업 파일

- `C:/Dev/Sanjuk-Unreal/Saved/sustained_func_pre_speed_gate_20260513.json`
- `C:/Dev/Sanjuk-Unreal/Saved/sustained_func_post_speed_gate_20260513.json`
- `C:/Dev/Sanjuk-Unreal/Saved/threadsafe_update_pre_swap_20260513.json`
- `C:/Dev/Sanjuk-Unreal/Saved/threadsafe_update_post_swap_20260513.json`
- `C:/Dev/Sanjuk-Unreal/Saved/updatestates_dump_20260513.json`
- `C:/Dev/Sanjuk-Unreal/Saved/eventgraph_dump.json`
- `C:/Dev/Sanjuk-Unreal/Saved/pc01_abp_variables_20260513.json`

## PIE 재테스트 시나리오

1. **race 해소 확인**: 락온 ON + 0.5초 이상 한 방향 strafe 유지 → 큰 방향 전환. sdt가 0.4초 이상 누적된 시점에 |tta|>=90 발생 시 sdpt=true 가 같은 틱에 캡처되는지 (ANIM_REC 출력에서 sdpt=true + sdt가 리셋 직전 값으로 함께 잡힘) 확인.
2. **Speed 게이트 효과**: 정지 상태(Speed2D < 50)에서 |tta|가 0에 가깝게 머물러도 sdt 누적 안 됨. 천천히 회전만 하는 케이스에서 false trigger 안 나는지 확인.
3. **회귀 검사**: 일반 strafe → pivot 케이스에서 기존 동작이 유지되는지 (sdt 누적 → |tta|>=90 트리거).

## 주의 / 향후 작업

- `SustainedDirMinSpeed` 기본값 50.0은 임시. PIE 관찰 후 조정 필요. 너무 높으면 가속 초기 진입 누락, 너무 낮으면 정지 게이트 효과 없음.
- 호출 순서 스왑은 UpdateStates의 모든 분기를 영향 범위로 만들었으므로, 향후 UpdateStates에 새 로직 추가 시 "Variables 갱신 후" 라는 전제 깔고 작성.
