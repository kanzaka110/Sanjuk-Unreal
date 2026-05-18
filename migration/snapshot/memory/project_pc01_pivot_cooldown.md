# PC_01_ABP Pivot Cooldown 시스템

## 목적
한 번 Pivot 발동 후 짧은 시간 재발동 차단. 좌→우 빠른 반복 입력에서 Pivot 도배 방지.

## 구현 위치
- asset: `/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP`
- IsPivoting 함수: cooldown gate
- UpdateStates 함수: cooldown timer 갱신

## 변수 추가

| 변수 | 타입 | 카테고리 | default | IE | 비고 |
|---|---|---|---|---|---|
| `PivotCooldownDuration` | double | Essential Values | 0.5 | true | 사용자 튜닝 가능 |
| `PivotCooldownRemain` | double | Buffer | 0.0 | false | 내부 timer |

## IsPivoting 게이트 식

기존 양 분기 결과를 새 AND 노드로 감싸 cooldown 게이트 추가.

```
분기 1 (IsStrafe=true):
  기존: IsLockOn AND (MoveSide != PrevMoveSide) AND bPrevIsMoving
  → ReturnValue = 기존_식 AND (PivotCooldownRemain <= 0)

분기 2 (IsStrafe=false):
  기존: |TargetRotationDelta| >= PivotAngleThreshold[PendingWalkMode] AND NOT TrjIsCircling
  → ReturnValue = 기존_식 AND (PivotCooldownRemain <= 0)
```

### 추가된 노드 (IsPivoting 그래프)
**분기 1**:
- `K2Node_VariableGet_11` — Get PivotCooldownRemain
- `K2Node_CallFunction_1` — LessEqual_DoubleDouble (Remain <= 0.0)
- `K2Node_CallFunction_3` — BooleanAND (기존_AND_0 AND LessEqual)

**분기 2**:
- `K2Node_VariableGet_14` — Get PivotCooldownRemain
- `K2Node_CallFunction_6` — LessEqual_DoubleDouble
- `K2Node_CallFunction_8` — BooleanAND (기존_AND_1 AND LessEqual)

### Connection (분기 1 예)
```
CommutativeAssociativeBinaryOperator_0.ReturnValue → CallFunction_3.A  (기존 AND 결과)
VariableGet_11.PivotCooldownRemain → CallFunction_1.A
CallFunction_1.B = 0.0 (default)
CallFunction_1.ReturnValue → CallFunction_3.B
CallFunction_3.ReturnValue → FunctionResult_0.ReturnValue
```

## UpdateStates cooldown timer 로직

ExecutionSequence_0의 비어있던 `then_3`, `then_4` 핀에 새 체인 추가.

```
then_3: IF IsPivoting() == true → Set PivotCooldownRemain = PivotCooldownDuration
then_4: Set PivotCooldownRemain = Max(0, PivotCooldownRemain - DeltaTime)
```

### 추가된 노드 (UpdateStates 그래프)
- `K2Node_CallFunction_4` — Is Pivoting (호출)
- `K2Node_IfThenElse_0` — Branch
- `K2Node_VariableSet_7` — Set PivotCooldownRemain (true 분기에서 Duration 할당)
- `K2Node_VariableGet_8` — Get PivotCooldownDuration
- `K2Node_VariableSet_13` — Set PivotCooldownRemain (decay)
- `K2Node_CallFunction_5` — FMax
- `K2Node_CallFunction_7` — Subtract_DoubleDouble
- `K2Node_VariableGet_14` — Get PivotCooldownRemain (decay 입력)
- `K2Node_VariableGet_15` — Get "Delta Time" (스페이스 포함, 기존 ABP 변수)

### Connection
```
ExecutionSequence_0.then_3 → IfThenElse_0.execute
  IfThenElse_0.Condition ← CallFunction_4 (IsPivoting).ReturnValue
  IfThenElse_0.then → VariableSet_7.execute
  VariableSet_7.PivotCooldownRemain ← VariableGet_8.PivotCooldownDuration

ExecutionSequence_0.then_4 → VariableSet_13.execute
  VariableSet_13.PivotCooldownRemain ← CallFunction_5.ReturnValue (FMax)
  CallFunction_5.A = 0.0 (default)
  CallFunction_5.B ← CallFunction_7.ReturnValue (Subtract)
  CallFunction_7.A ← VariableGet_14.PivotCooldownRemain
  CallFunction_7.B ← VariableGet_15.Delta Time
```

## 핵심 작동 원리

1. **Pivot 발생 시점**: IsPivoting()이 true 반환되는 그 1프레임에 UpdateStates의 then_3 분기가 `PivotCooldownRemain = Duration (0.5)` 으로 갱신.
2. **이후 0.5초간**: 매 프레임 UpdateStates.then_4 가 `Remain -= DeltaTime` (clamp ≥ 0). 동시에 IsPivoting()는 `Remain <= 0` 체크 fail로 false 반환 → cooldown active 동안 Pivot 차단.
3. **0.5초 경과**: `Remain == 0` 도달 → cooldown 해제 → 다시 Pivot 가능.

## 튜닝 가이드

- `PivotCooldownDuration` 는 **InstanceEditable** — BP 인스턴스에서 캐릭터별 다른 값 가능.
- 락온 strafe 좌→우 반복 시 한 동작 후 다음 발동까지 0.5초 보장.
- 너무 짧으면(0.1초 이하) 효과 없음. 너무 길면(1초 이상) 의도된 빠른 방향 전환도 차단.

## 검증

- compile_blueprint: errors=0, warnings=0
- validate_blueprint: node_errors=0
- save_asset: 실패 (Monolith save 한계) — 에디터에서 Ctrl+S 또는 P4 체크아웃 후 수동 저장 필요

## PIE 검증 시나리오

1. 락온 상태에서 좌→우 빠른 반복 입력 → 첫 회만 Pivot 발동, 0.5초 후 다음 발동 가능
2. 비락온 상태에서 빠른 회전 → 첫 Pivot 후 0.5초 차단 확인
3. PivotCooldownDuration=0 으로 설정 시 기존 동작과 동일한지 확인 (회귀 방지)

## 작업 이력
- 2026-05-13: 초기 구현. IsPivoting AND 게이트 + UpdateStates timer 추가.
- ID 충돌 발생: 1차 add에서 받은 K2Node_CallFunction_4/_5 가 UpdateStates와 충돌해 컴파일 후 사라짐 → 재추가 (CallFunction_6, _8) 후 정상 잔존.
- 2026-05-13: PIE 결과 Pivot 자체가 안 나옴 → Cooldown 임시 비활성화 차원에서 `PivotCooldownDuration` default 0.0 으로 설정. compile UpToDate. save_asset은 실패(P4 체크아웃 필요) — 디스크 반영은 에디터 Ctrl+S 또는 P4 체크아웃 후 수동 저장. **사전 dump 시점에서 이미 default=0** 이었음(처방의 "이전 0.5"는 실제 값과 불일치) — 명시적 set으로 일관성만 재확정.
- **원인 추정 보강**: cooldown 트리거 순서 — UpdateStates 가 IsPivoting() 호출 시 같은 틱에 Remain=Duration 설정 → 같은 틱 IsStarting NOT 게이트 호출 시 IsPivoting()=false (cooldown 적용) → release 실패. Duration=0 으로 우회 시 Remain 항상 0, gate 통과.
- 2026-05-13 (후속): **IsPivoting 함수 cooldown wrapper 노드가 어느 시점에 제거됨** — dump 재확인 시 if 분기에 cooldown gate 없음. 현재 if 분기 식 단순 `IsLockOn AND (MoveSide!=PrevMoveSide) AND bPrevIsMoving`(3-pin AND), else 분기는 `(|TrjDelta|>=Threshold) AND NOT TrjIsCircling`. UpdateStates timer 노드는 별도 확인 필요. **이 메모리의 wrapper 구조 설명은 outdated**, IsPivoting 함수 노드 ID 매핑도 이제 다음 항목 (IsPivoting bPrevIsMoving 제거)의 dump 기준.

## 2026-05-13 IsPivoting 식 bPrevIsMoving 조건 제거 (패드 케이스 보정)

### 배경
패드 PIE 결과 `clip=Pivot` 0건. SustainedDirection 시기엔 381건. 패드 약한 입력에서 `bPrevIsMoving`이 충분히 true로 유지되지 않아 if 분기가 잡히지 않음.

### 변경
- 그래프: `IsPivoting`
- if 분기 (IsStrafe=true):
  - 이전: `IsLockOn AND (MoveSide != PrevMoveSide) AND bPrevIsMoving` (3-pin AND)
  - 이후: `IsLockOn AND (MoveSide != PrevMoveSide)` (2-pin AND)
- else 분기, IsStrafe Branch, EnumInequality 노드 모두 보존.

### 구현 방식
3-pin AND 노드 (`K2Node_CommutativeAssociativeBinaryOperator_0`)는 NumAdditionalInputs 감소 API 없어 통째로 교체:
1. 새 2-pin BooleanAND CallFunction `K2Node_CallFunction_9` 생성
2. 기존 AND_0 모든 핀 disconnect
3. 새 AND_9에 재배선: A←IsLockOn, B←EnumInequality.ReturnValue, ReturnValue→FunctionResult_0.ReturnValue
4. 기존 AND_0 + bPrevIsMoving Get(`K2Node_VariableGet_5`) 제거

### 검증
- compile_blueprint: errors=0, warnings=0, status=UpToDate
- save_asset: success (was_dirty=true)
- 사후 dump: `Saved/ispivoting_post_remove_bprevismoving_20260513.json`
- 사전 dump: `Saved/ispivoting_pre_remove_bprevismoving_20260513.json`

### 후속 PIE 검증 시나리오
1. 패드 약한 입력 락온 strafe 좌→우 → Pivot 발동 확인
2. SustainedDirection 시기 회귀 없음 확인
3. IsStarting NOT(Pivot Tag) release 정상 동작 확인 (cooldown gate 없는 상태)

## 관련 메모리
- [PC_01 Chooser 평가 시점 구조](project_pc01_chooser_evaluation.md)
- [PC_01_ABP IsStarting 설계](reference_pc01_isstarting_design.md)
- [PC_01 CircleStrafeHysteresis 메커니즘](project_pc01_circle_strafe_hysteresis.md)
