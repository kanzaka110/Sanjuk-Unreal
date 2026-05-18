---
name: PC_01_ABP IsStarting "B 트리거 + A latch + Tag release" 설계
description: IsStarting 함수의 정상 동작 식과 한 틱 cut 회피 패턴. 회피 작업 재개 시 NOT(HasEvade) 추가 위치 메모.
type: reference
originSessionId: a44afb55-887c-4d27-8ee8-e38c3eca007b
---
## 최종 식 (2026-05-13 수정판 — IsPivoting() release 게이트 추가)

```
IsStarting =
  bIsMoving                                                                ← Branch 게이트
    ? [ bPrevIsStart                                                       ← A: 단독 latch (자기참조)
        OR
        (PrevVel < threshold AND NOT bPrevIsMoving AND bIsMoving) ]        ← B: 진입 트리거
      AND NOT(BlendStackInputs.Tags Contains "Pivot")                      ← release 게이트 1
      AND NOT( IsPivoting() )                                              ← release 게이트 2 (2026-05-13)
    : false
```

요약: `IsStarting = (bPrevIsStart OR B_trigger) AND NOT(BlendStackInputs.Tags Contains "Pivot") AND NOT(IsPivoting())`

### 노드 구조 (2026-05-13 사용자 수동 추가)
- `K2Node_CallFunction_10` — Self.IsPivoting() pure call (NodePosX=1136, NodePosY=844)
- `K2Node_CallFunction_11` — KismetMathLibrary.Not_PreBool (NodePosX=1312, NodePosY=860)
- 결선:
  - `IsPivoting.ReturnValue → NOT.A`
  - `NOT.ReturnValue → K2Node_CommutativeAssociativeBinaryOperator_4.B` (기존 AND 노드의 추가 입력 핀)

### 노드 구조 (2026-05-13 복구 — IsPivoting NOT 게이트 재추가, Tuner)

SustainedDirection 제거 작업 중 IsPivoting NOT 게이트가 손실된 상태(Inspector 진단) → Tuner가 옵션 B(새 BooleanAND 직렬 삽입) 패턴으로 복구.

- 사전 상태 (23 노드): 외측 AND `K2Node_CommutativeAssociativeBinaryOperator_3` → 직접 `FunctionResult_0.ReturnValue` 결선. `NOT(IsPivoting())` 게이트 없음.
- 추가 노드 (+3, 26 노드):
  - `K2Node_CallFunction_4` — Self.IsPivoting() pure (pos=[1600,640])
  - `K2Node_CallFunction_5` — KismetMathLibrary.Not_PreBool (pos=[1808,640])
  - `K2Node_CallFunction_8` — KismetMathLibrary.BooleanAND (pos=[2048,400]) — 새 외측 AND
- 결선 변경:
  - disconnect: `K2Node_FunctionResult_0.ReturnValue` ← `K2Node_CommutativeAssociativeBinaryOperator_3.ReturnValue`
  - connect: `IsPivoting.ReturnValue → NOT.A`
  - connect: `K2Node_CommutativeAssociativeBinaryOperator_3.ReturnValue → K2Node_CallFunction_8.A`
  - connect: `K2Node_CallFunction_5.ReturnValue (NOT) → K2Node_CallFunction_8.B`
  - connect: `K2Node_CallFunction_8.ReturnValue → K2Node_FunctionResult_0.ReturnValue`
- 컴파일: success / errors:0 / warnings:0 / UpToDate
- save_asset: 실패 (P4 체크아웃) → 사용자 Ctrl+S 필요
- 백업: `Saved/isstarting_pre_restore_ispivoting_gate_20260513.json` (11,606 B, 23 nodes)
- 사후: `Saved/isstarting_post_restore_ispivoting_gate_20260513.json` (13,279 B, 26 nodes)

**왜 옵션 B (직렬 삽입)인지**: 기존 외측 AND `_3`은 `K2Node_CommutativeAssociativeBinaryOperator` (가변 입력 가능)이지만 옵션 A(`NumAdditionalInputs` 확장) 는 Monolith add_pin 미노출 + wildcard 핀 이슈로 막힌 전례 있음. 새 BooleanAND 직렬 삽입은 식 동치 (`X AND Y ≡ (X) AND Y`) 보장 + 안전.

**기존 노드 구조 차이**: 2026-05-13 첫 수동 추가는 외측 AND 이름이 `_4` 였고 이번 복구 시점엔 `_3` (다른 빌드 / SustainedDirection 작업 영향). 식 의미는 동일.

### 단순화 시도 → 롤백 (2026-05-13)

처방 A: `Tags Contains "Start"` 단순 식으로 22→8 노드 축소.
**문제**: 닭/달걀 데드락 — BlendStack에 Start tag가 들어오려면 Chooser가 Start row를 선택 → IsStarting=true 가 선행 조건. 식 자체가 true 안 됨 → Start 클립 전혀 안 나옴.

**복원 (Tuner 2026-05-13)**:
- 노드: 8 → 27 (+19. Comment 3 + 함수 노드 16개, 백업 22 + 신규 add_comment 흔적은 후처리로 정리)
- 백업 ID와 다름 — 백업의 `K2Node_PromotableOperator_8` / `K2Node_CommutativeAssociativeBinaryOperator_6/7/8` 은 Monolith `add_node` 미지원이라 모두 `K2Node_CallFunction(Less_DoubleDouble / BooleanOR / BooleanAND)` 로 대체. 3-input AND 도 `K2Node_CallFunction(BooleanAND)` 2개로 분리 (Less ∧ NOT_prev → AND_8, AND_8 ∧ bIsMoving → AND_9).
- 식 구조는 백업과 식별 가능 동치 (`(A ∧ B) ∧ C ≡ A ∧ B ∧ C`).
- 컴파일: success / errors:0 / warnings:0 / UpToDate
- 백업: `Saved/isstarting_pre_simplify_20260513.json` (12,659 B, 25 nodes)
- pre-rollback: `Saved/isstarting_before_rollback_20260513.json` (4,771 B, 11 nodes - 단순화 상태)
- post-rollback: `Saved/isstarting_after_rollback_20260513.json` (12,935 B, 26 nodes)

### 단순화 식 핵심 결함 (재시도 금지)
1. Start tag가 활성이 되려면 Chooser가 Start row 선택 필요
2. Chooser는 IsStarting=true 조건으로 Start row 활성
3. 둘 다 서로를 기다리는 데드락 → Start 클립 영원히 안 나옴
4. 따라서 IsStarting은 BlendStack 결과가 아닌 **선행 외부 조건**(PrevVel/PrevMoving)으로 트리거되어야 함

## 역할 분리

- **B (Started 분기, 코멘트 영역 위치)**: 정지→이동 전환 한 틱만 true. **켜는 트리거** 역할만.
- **A (Prev 유지 분기, 코멘트 영역 위치)**: `bPrevIsStart` 단독. **유지 latch**. 외부 조건과 무관히 self-sustain.
- **외부 AND `NOT(Pivot Tag)`**: Pivot 클립이 BlendStack에 들어오면 즉시 false. **release 게이트** 역할.

## 한 틱 cut 회피 원리

이전 A = `bPrevIsStart AND PrevVel<threshold` 였을 때 — PrevVelocity가 사실상 "현재 Velocity"(UpdateVariables.VariableSet_59에서 `PrevVelocity=Velocity` 직대입)라 한 틱 만에 임계 초과 → A 깨짐 → Start 클립 씹힘.

A에서 `PrevVel<threshold` 제거하니 latch가 외부 조건과 무관히 유지. Tag 기반 종료로 메커니즘 통일.

## GetPrevSpeedThreshold 값

곱셈 인자 0.85 적용 후:
- Walking 51 / Jogging 114.75 / Running 191.25 / Sprinting 267.75 (cm/s)

이 값은 이제 **B 분기 진입 검출에만 사용**. A latch와 무관.

## 회피 작업 재개 시 NOT(HasEvade) 추가 위치

B 분기 AND 노드(`K2Node_CommutativeAssociativeBinaryOperator_8`)의 추가 입력 핀(D)에 `NOT(HasEvade)` 연결. NumAdditionalInputs를 +1.

```
B_new = (PrevVel<threshold) AND NOT(bPrevIsMoving) AND bIsMoving AND NOT(HasEvade)
```

A latch에는 HasEvade 추가하지 말 것 — A는 self-sustaining이라 진입 차단만 의미 있음.

## Why
- 2026-05-11: 한 틱 cut 진단 → A 분기 단순화(자기참조만)로 해결. B 트리거 + A latch + Tag release 패턴 명문화.
- 2026-05-12: A latch가 너무 끈질겨 속도가 충분히 올라간 뒤에도 Start 유지되는 케이스 발견 → A에 `Velocity < threshold*1.2` 가드 추가. Tuner 작업: Get Velocity → VSizeXY → Less → 새 AND 노드 추가, 기존 bPrevIsStart → OR.A 결선을 새 AND 경유로 변경. 컴파일 OK.
- **2026-05-13 (Tag 단순화 시도 → 롤백)**: 처방 — 식 전체를 `Tags Contains "Start"` 로 축소(노드 22→8). 사용자 PIE 검증: **Start 클립이 전혀 안 나옴**. 닭/달걀 데드락 — Start tag는 Chooser가 Start row 선택해야 BlendStack에 들어오고, Chooser는 IsStarting=true 조건으로 Start row 활성. 둘이 서로 기다림. **Tuner 롤백 작업**: 디스컨넥트 1건(ArrayContains.ReturnValue → FunctionResult), set_pin_default(ItemToFind: Start → Pivot), add_nodes_bulk 13건, add_node 2건(분리 AND), connect_pins_bulk 15건, comment 추가(중복 제거). 백업 22 nodes → 복원 26 nodes (Comment 1개 더 늘어남 — 기존 Started Comment_6 와 함께 백업에 없던 위치에 1개 추가? 실제는 그대로). **백업 형태와 다른 점**: `K2Node_PromotableOperator` / `K2Node_CommutativeAssociativeBinaryOperator` 가 Monolith add_node 에서 function 미설정 fallback 으로 빈 wildcard 노드만 생기는 한계로 모두 `K2Node_CallFunction(Less_DoubleDouble / BooleanAND / BooleanOR)` 로 대체. 3-input AND 도 2-input AND 2개 분리(결합법칙으로 식 동치). 식 자체는 백업과 완전 동일. 컴파일 0/0 success. 백업: `Saved/isstarting_pre_simplify_20260513.json` (단일 진실원), pre-rollback: `Saved/isstarting_before_rollback_20260513.json`, post-rollback: `Saved/isstarting_after_rollback_20260513.json`.
- **2026-05-13 (복구 — IsPivoting NOT 게이트 재추가, Tuner)**: Inspector 진단 — SustainedDirection 제거 작업 중 `NOT(IsPivoting())` 게이트가 손실됨(Pivot 모션 매칭 안 됨, Start latch 유지). 처방 옵션 B 적용 — 새 BooleanAND `_8` 을 외측 AND `_3` 와 FunctionResult 사이 직렬 삽입. 추가 노드 3개: `K2Node_CallFunction_4`(IsPivoting), `_5`(NOT), `_8`(새 AND). 결선 5건(disconnect 1 + connect 4). 23→26 노드. compile 0/0 UpToDate. save_asset 실패 → Ctrl+S. 백업/사후: `Saved/isstarting_{pre,post}_restore_ispivoting_gate_20260513.json`. 이번 복구의 외측 AND 노드 ID는 `_3` (이전 메모 `_4` 와 다름 — SustainedDirection 작업으로 변경).
- **2026-05-13 (단순화 → 데드락 → 롤백 → release 게이트 추가)**:
  - 사용자가 처음엔 `IsStarting = Tags.Contains("Start")` 단순화 시도 → Start 클립이 전혀 안 나옴 (Chooser가 Start row 선택하려면 IsStarting=true 선행 필요 → 닭/달걀 데드락) → 백업에서 결합법칙 분리하며 롤백.
  - 그 후 falling-edge pulse 방식(`bStartTagReleased` 변수)을 별도 검토 → 옵션 C로 사용자 수동 ArrayContains 노드 추가하는 단계에서, 사용자가 더 직접적 해법으로 우회 — `IsPivoting()` 함수 호출 결과를 NOT 처리해 release 게이트로 추가.
  - 효과: Pivot tag가 BlendStack에 들어오기 전이라도 `IsPivoting` 판정만으로 즉시 release 가능. Tag 캐시 한 틱 지연 회피.
  - 후속 cleanup (Tuner 2026-05-13): falling-edge pulse 용으로 추가됐던 변수 2개 (`bStartTagReleased`, `bPrevHasStartTag`) 미사용 상태 — `search_nodes` 0건 확인 후 `remove_variable` × 2. compile 0/0 UpToDate. save_asset 실패 → 사용자 Ctrl+S. 폐기 작업 메모: 기존 `project_pc01_starttag_pulse.md` 삭제.
- **2026-05-12 (롤백)**: PIE 검증 결과 Start 모션이 아예 안 나옴. `Velocity < threshold × 1.2` 게이트가 너무 빡빡 → Start 진입 직후 한 틱 만에 A latch가 false로 떨어짐(한 틱 cut 부활). 추가했던 6개 노드(Get Velocity / VSizeXY / GetPrevSpeedThreshold / Multiply×1.2 / Less / 새 AND) 전부 제거, `bPrevIsStart → OR_6.A` 직결로 복원. 컴파일 OK + 백업과 노드 25개 PERFECT MATCH 확인. **재설계 필요**: 단순 임계 게이트는 부적합. 후보 — (1) 더 큰 배수(1.5~2.0), (2) `Velocity < threshold AND timer > minStartDuration` 같은 시간 가드, (3) `bIsAccelerating` 기반 가드, (4) Pivot Tag release만으로 충분한지 재검토. 백업/스냅샷: `Saved/isstarting_before.json` / `Saved/isstarting_rollback.json`.
- **2026-05-12 (옵션 B-3 시도 → 롤백)**: 처방 — `A_new = bPrevIsStart AND (BlendStackInputs.Tags Contains "Start")`. Tuner 진행 중 **Monolith add_node 한계 노출**: `K2Node_CallFunction` 으로 만든 `Array_Contains` 호출 노드는 wildcard 핀(`array:wildcard` / `wildcard`)을 컴파일 시점에 해결하지 못함 (실제로 필요한 클래스는 `K2Node_CallArrayFunction` 이며 add_node 가 노출 안 함). `copy_nodes` 로 기존 Pivot Contains(_4) 복제는 동일한 pin GUID 를 재사용해 원본의 `Tags→TargetArray` / `ReturnValue→NOT_11.A` 연결을 새 노드에 강탈 후 복제 노드 제거 시 같이 사라짐 → 원본도 끊김(2건). 즉시 disconnect→re-connect 로 복원, 추가했던 모든 임시 노드(Array_Contains _12 / _14, AND _13) 제거, `bPrevIsStart → OR_6.A` 직결 복원. 컴파일 0/0, dump 파일 크기 pre 와 동일 (summary 3141B, export 2221B). **결론**: 옵션 B-3 는 Monolith Tuner 만으로 적용 불가. **수동 작업 필요** — UE 에디터에서 Array Contains 노드를 변수 패널의 Tags 배열을 드래그-드롭해 만들거나, Pivot Contains 노드를 Ctrl+W 로 복제 후 ItemToFind="Start" 로 바꾸고 AND 노드 사이에 끼우면 됨. 백업/dump: `C:\Dev\Sanjuk-Unreal\dumps\isstarting_B3\_pre_isstartingB3_20260512_isstarting_summary.json` / `..._export.json` / `_post_rollback_summary.json` / `_post_rollback_export.json`.

## How to apply
- IsStarting 관련 호소 시 이 식 구조 기억
- "Start가 씹힌다" → A latch 깨졌는지 먼저 의심
- "Pivot 출력 안 됨" → BlendStack에 Pivot Tag가 정말 들어오는지 확인 (release 안 되면 IsStarting=true 유지되어 Pivot row 매칭 안 됨)
- "Start가 안 꺼지는 호소" → Pivot Tag 검사뿐 아니라 `IsPivoting()` 호출도 release 게이트에 포함됐는지 확인 (2026-05-13 release 게이트 2 추가됨)

## 2026-05-12 (디버그 Print 설치)

좌/우/뒤→앞 이동 시 IsStart 안 꺼짐 / 앞→뒤만 꺼짐 가설 판정용 임시 진단 노드 설치. 사용자 보고 후 별도 task에서 제거 예정.

### 추가된 변수
- `bDebugIsStartingEnabled` (bool, default=true, category=Debug) — PIE 토글 게이트
- `DebugIsStartString` (string, default="", category=Debug) — UpdateVariables에서 빌드된 디버그 문자열 캐시

### UpdateVariables (Thread-Safe 그래프)
`Set bIsStart` (VariableSet_26) 직후 19개 노드 삽입:
- Branch (IfThenElse_0) — `bDebugIsStartingEnabled` 게이트
- Get × 5: bIsStart, bIsMoving, Velocity, CurrAnimTag (CurrentAnimTags 단일 캐시), bDebugIsStartingEnabled
- 변환 5: VSizeXY, BoolToString × 2, DoubleToString, NameToString
- Append (Concat_StrStr) × 7: 라벨 + 값 직렬 누적
- `Set DebugIsStartString` (VariableSet_24) — 최종 문자열 변수에 저장
- exec: Set bIsStart.then → Branch → (True) Set DebugIsStartString → Set IsSplineMoving / (False) Set IsSplineMoving

### EventGraph (Non-Thread-Safe)
`BlueprintPostEvaluateAnimation` 이벤트의 DrawDebug.then 다음에 4개 노드 추가:
- Branch (조건 = bDebugIsStartingEnabled)
- Get bDebugIsStartingEnabled
- Get DebugIsStartString
- Print String — Key="ISD", Duration=0.0, Yellow, Screen+Log

### 패턴
`IsStart={0} bMoving={1} Vel={2} Tag={3}` (작업 명세 TagsLen/HasPivot/HasStart는 Array_Contains wildcard 한계로 단일 `CurrAnimTag` 로 축소. Pivot vs Start 태그 판정은 CurrTag 값으로 추론)

### 왜 ThreadSafe / Non-ThreadSafe 분리
- UpdateVariables는 BlueprintThreadSafe 메타 → PrintString (non-thread-safe) 직접 호출 시 컴파일 에러
- 데이터 빌드는 UpdateVariables에서, 출력은 EventGraph에서 분리. 한 틱 지연 무시 가능

### 백업
- `C:\Dev\Sanjuk-Unreal\Saved\updvar_before_debug.json` (299 노드)
- `C:\Dev\Sanjuk-Unreal\Saved\updvar_after_debug.json` (318 노드, +19)

### 컴파일
- success: True / errors: 0 / warnings: 0
- save_asset: 실패 → 사용자 에디터에서 Ctrl+S 필요

### 제거 절차 (사용자 검증 완료 후)
- UpdateVariables: K2Node_VariableGet_8/51/53/54/55, K2Node_CallFunction_32~43, K2Node_IfThenElse_0, K2Node_VariableSet_24 19개 노드 remove
- UpdateVariables: K2Node_VariableSet_26.then → K2Node_VariableSet_28.execute 직결 복원
- EventGraph: K2Node_IfThenElse_0, K2Node_VariableGet_0/1, K2Node_CallFunction_1 4개 노드 remove
- EventGraph: K2Node_CallFunction_3.then 빈 상태로 유지 (원래 비어있었음)
- 변수: bDebugIsStartingEnabled, DebugIsStartString 2개 remove
