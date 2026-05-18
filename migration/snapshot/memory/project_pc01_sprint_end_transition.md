# PC_01 Sprint 종료 transition 검출 시스템 — Phase 1 완료 (2026-05-14)

## 목적

사용자가 Sprint 종료 (Sprint→Jog 전환) 시점에 락온 상태에서 잘못 매칭되는 `Sprint_Turn`
클립을 Chooser 에서 차단하고 싶음. 이를 위해 **ABP 에서 Sprint 종료 transition 검출 변수**를
먼저 추가하는 사전 작업.

## 자산

- `/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP`
- 부모 클래스: `SBActorAnimInstance` (`/Script/SB2.SBActorAnimInstance`)

## Phase 1 — 완료 항목

### 1.1 변수 4개 추가

| 변수 | 타입 | 카테고리 | default | IE |
|---|---|---|---|---|
| `bIsSprintEndTransition` | bool | Buffer | false | false |
| `SprintEndTransitionRemain` | double | Buffer | 0.0 | false |
| `SprintEndTransitionDuration` | double | Essential Values | 0.3 | **true** |
| `bPrevIsSprinting` | bool | Buffer | false | false |

`double` 사용 (UE 5.7 LWC; ABP 다른 buffer 변수와 일관).

### 1.2 UpdateVariables 에 검출 로직 추가

**원래 명세는 `SBCharacter::IsSprinting()` CallFunction 호출**이었으나, ABP 어디에서도
해당 함수 호출 사례가 없고 PropertyAccess path 설정이 Monolith API 로 노출되지 않아
**`PendingWalkMode == SBWalk_Sprinting` enum 비교로 대체**함.

근거:
- `UpdateStates` 의 `JustExitedSprint` 검출도 동일 패턴 사용 (PrevPendingWalkMode +
  PendingWalkMode 의 enum 비교)
- `PendingWalkMode` 는 ABP 의 `byte / Essential Values` 변수로 이미 sprint 상태 반영
- ThreadSafe 안전 (enum 비교는 pure)
- `K2Node_CallFunction EqualEqual_ByteByte` 는 byte default 값으로 enum literal
  ("SBWalk_Sprinting") 을 못 받음 → `K2Node_EnumEquality` 로 전환

식:
```
currIsSprinting = (PendingWalkMode == SBWalk_Sprinting)
isSprintEnding  = bPrevIsSprinting AND (NOT currIsSprinting) AND IsLockOn

if isSprintEnding:
    SprintEndTransitionRemain = SprintEndTransitionDuration
else:
    SprintEndTransitionRemain = FMax(0, SprintEndTransitionRemain - DeltaTime)

bIsSprintEndTransition = (SprintEndTransitionRemain > 0)
bPrevIsSprinting       = currIsSprinting
```

#### 노드 구성 (id 매핑)

| temp | node_id | class | 용도 |
|---|---|---|---|
| VG_PWM | K2Node_VariableGet_57 | VariableGet | PendingWalkMode |
| ENUMEQ | K2Node_EnumEquality_1 | EnumEquality | currIsSprinting |
| VG_Prev | K2Node_VariableGet_58 | VariableGet | bPrevIsSprinting |
| NOT_Curr | K2Node_CallFunction_33 | NOT Boolean | |
| AND_1 | K2Node_CallFunction_34 | AND Boolean | bPrev AND NOT curr |
| VG_LOn | K2Node_VariableGet_59 | VariableGet | IsLockOn |
| AND_2 | K2Node_CallFunction_35 | AND Boolean | isSprintEnding |
| BR_End | K2Node_IfThenElse_0 | Branch | |
| VG_Dur | K2Node_VariableGet_60 | VariableGet | SprintEndTransitionDuration |
| SET_RemT | K2Node_VariableSet_73 | VariableSet | Remain (true branch) |
| VG_RemF | K2Node_VariableGet_61 | VariableGet | Remain (이전값) |
| VG_DT  | K2Node_VariableGet_65 | VariableGet | "Delta Time" (variable_name 에 공백 필수!) |
| SUB | K2Node_CallFunction_36 | Subtract_DoubleDouble | |
| FMAX | K2Node_CallFunction_39 | FMax (KismetMathLibrary) | |
| SET_RemF | K2Node_VariableSet_74 | VariableSet | Remain (false branch) |
| VG_RemFinal | K2Node_VariableGet_63 | VariableGet | Remain (>0 비교용) |
| GT_Zero | K2Node_CallFunction_38 | Greater_DoubleDouble | |
| SET_Flag | K2Node_VariableSet_75 | VariableSet | bIsSprintEndTransition |
| SET_PrevS | K2Node_VariableSet_76 | VariableSet | bPrevIsSprinting (캐시) |

#### Exec 진입점

UpdateVariables 의 `K2Node_ExecutionSequence_3` 은 then_0..then_11 12 핀 모두 사용중.
`Monolith connect_pins` 은 **한 exec output 에 multi-target 을 자동 fan-out 하지 않음**
(기존 연결을 덮어쓰기). 따라서 새 `K2Node_ExecutionSequence_0` 를 삽입:
- `ExecSeq_3.then_11` → `ExecSeq_0.execute`
- `ExecSeq_0.then_0` → `Knot_1.InputPin` (기존 분기 복원)
- `ExecSeq_0.then_1` → `BR_End.execute` (새 검출 분기)

#### 함정

- `EqualEqual_ByteByte` 는 byte default 가 raw 숫자 필요. enum literal 사용 시
  `K2Node_EnumEquality` (wildcard 핀) 사용.
- `Max` 는 다중 오버로드. KismetMathLibrary 에서 `FMax` 로 지정해야 `Max (Float)` 가 잡힘.
- UAnimInstance `DeltaTime` 은 monolith add_node 에서 `variable_name="DeltaTime"` 로는
  못 찾음. **`variable_name="Delta Time"` (공백 포함)** 로 가능.

### 1.3 AnimRewindRecorderEmit 에 `sset` 키 추가

신규 FormatText 노드 `K2Node_FormatText_13` 를 FT_11→FT_12 사이에 삽입:
- format: `{prev},"sset"={sset}`
- prev (text) ← FT_11.Result
- sset (bool) ← VariableGet bIsSprintEndTransition (`K2Node_VariableGet_41`)
- Result → FT_12.prev (기존 FT_11→FT_12 연결은 제거)

`JustExitedSprint` (jes) 키와 같은 FormatText 단계(FT_11) 직후 들어가므로 ANIM_REC
출력 순서는 …,jes,...,htt,...,sset,phase,... 식.

## 컴파일/저장 결과

- `compile_blueprint`: success=True, status=UpToDate, errors=0, warnings=0
- `validate_blueprint`: 우리 새 노드 disconnected/error 없음
- `save_asset`: **실패** ("Failed to save asset"). 메모리
  `reference_monolith_animgraph_editing_limits.md` 따르면 save 실패해도 디스크 적용 가능,
  사용자 에디터에서 수동 저장 권장. P4 checkout 상태 확인 필요.

## 사용자 PIE 확인 사항

1. 락온 상태에서 Sprint → Jog 전환 시:
   - `sset=true` 가 ANIM_REC 출력에 0.3 초 동안 노출되는지
   - 비-락온 상태에선 `sset=false` 유지
2. SprintEndTransitionDuration 변수 (Essential Values, IE=true) 를 PIE 중 디테일 패널에서
   조정 가능

## Phase 2 (다음 단계) — Chooser 처방

Chooser 테이블 `(SB2 PC_01 Motion Matching 시스템)` 에 `bIsSprintEndTransition`
조건 추가:
- 락온 + Sprint→Jog 전환 + 반대 방향 → Sprint_Turn 후보 제외 / 다른 안정 클립 우선
- Chooser 평가 시점 (state 진입 시 1회) 에 대한 제약은
  `project_pc01_chooser_evaluation.md` 메모리 참조

## 파일 경로 (백업/검증)

- 사전 dump:
  - `Saved/sprint_pre_vars.json`
  - `Saved/sprint_pre_uv.json`
  - `Saved/sprint_pre_animrec.json`
- 사후 dump:
  - `Saved/sprint_post_vars_final.json`
  - `Saved/sprint_post_uv.json`
  - `Saved/sprint_post_animrec.json`
- 컴파일 응답: `Saved/resp_compile_sset4.json`
- validate 응답: `Saved/resp_validate.json`

## Phase 1.5 — 검출 식 단순화 (2026-05-14)

### 동기

Phase 1 검출 식 `bPrevIsSprinting AND NOT (PendingWalkMode == Sprinting) AND IsLockOn`
은 PIE ANIM_REC 분석 결과 **buffer 지연으로 1~2틱 늦게 발동**:

- Sprint_Turn 끼임 시점 (f.2,906,585):
  - sset=false (검출 미발동)
  - pwm=4 (Sprinting 아직 buffer 유지 — 본 검출이 못 잡음)
  - **jes=true** (`JustExitedSprint` — Sprint 키 release 직후 트리거됨)
- jes 는 UpdateStates 에서 미리 edge 검출되어 즉시 발동

따라서 `JustExitedSprint` 가 더 빠르고 정확한 트리거.

### 변경 식

```
isSprintEnding = JustExitedSprint AND IsLockOn
```

bPrevIsSprinting / PendingWalkMode 캐시-비교 체인 전체 제거.

### 노드 변경

**제거 (6개):**
- `K2Node_VariableGet_57` (Get PendingWalkMode)
- `K2Node_EnumEquality_1` (== SBWalk_Sprinting)
- `K2Node_CallFunction_33` (NOT)
- `K2Node_CallFunction_34` (AND prev × NOT curr)
- `K2Node_VariableGet_58` (Get bPrevIsSprinting)
- `K2Node_VariableSet_76` (Set bPrevIsSprinting, 캐시 갱신)

**추가 (1개):**
- `K2Node_VariableGet_67` (Get JustExitedSprint) at (960, 6464)

**재배선:**
- `K2Node_CallFunction_35.A` (최종 AND): `CallFunction_34.ReturnValue` → `VariableGet_67.JustExitedSprint`
- 보존: `CallFunction_35.B` ← `VariableGet_59.IsLockOn`, `CallFunction_35.ReturnValue` → `IfThenElse_0.Condition`
- 보존: Branch(IfThenElse_0) → Set Remain (73=Duration / 74=FMax) → Set bIsSprintEndTransition (75) — 타이머 로직 전부 유지
- 종결: `VariableSet_75.then → []` (이전엔 VariableSet_76 으로 이어졌으나 그 노드가 제거되어 블록 종착)

### 변수 제거

`bPrevIsSprinting` 변수 — UpdateVariables 외 사용처 0건 확인 → 변수 자체 제거.

### 컴파일/검증

- `compile_blueprint` 2회 (노드 제거 후, 변수 제거 후) 모두 success/UpToDate/errors=0/warnings=0
- `validate_blueprint`: unused_variables 에 bPrevIsSprinting 없음 (정상 제거 확인).
  새로운 disconnected/node_errors 없음 (Phase 1 의 기존 항목만 잔존)
- `save_asset`: **실패** (Phase 1 과 동일 — 사용자 에디터에서 수동 저장 필요).
  메모리 데이터는 적용됨 (post-state get_node_details 로 새 연결 확증)

### 백업

- pre: `C:/Dev/Sanjuk-Unreal/scripts/backup/UpdateVariables_pre_20260514.json` (189,352 bytes)
- post: `C:/Dev/Sanjuk-Unreal/scripts/backup/UpdateVariables_post_20260514.json` (186,209 bytes)
- 차분 ≈ -3 KB (6 노드 제거 + 1 노드 추가 + 1 변수 제거 net)

### 사용자 PIE 확인 사항

1. **타이밍**: `Sprint_Turn` 매칭 시점 (Sprint 키 release 직후 frame) 에 `sset=true` 가
   `jes=true` 와 **같은 프레임에** 잡히는지 (이전엔 1~2틱 늦었음)
2. **유지**: SprintEndTransitionDuration (0.3 s) 동안 sset=true 유지
3. **락온 게이트**: 비-락온 상태에서 Sprint 종료해도 sset=false 유지
4. **Chooser 효과** (Phase 2 처방 적용 시): Sprint→Jog 락온 전환에서 Sprint_Turn 안 끼는지

### 함정 / 주의

- `add_node` 의 K2Node prefix: `node_type="VariableGet"` (prefix 없음). prefix 사용 시
  generic fallback 으로 pins 없는 빈 노드 생성됨 (`reference_monolith_animgraph_editing_limits.md`)
- `disconnect_pins` 파라미터: source/target 이 아니라 `node_id` + `pin_name` + `target_node` + `target_pin`

## Phase 1.6 — Sprint 유지 중 게이트 추가 (2026-05-14)

### 동기

Phase 1.5 까지 식: `bIsSprintEndTransition = (SprintEndTransitionRemain > 0)`
- Sprint → Jog 락온 전환 OK
- 그러나 **Sprint 유지 중 좌우 이동(Sprint_Turn)** 시 sset=true 가 0.3 초 timer 동안 유지됨.
  Chooser 가 차단해 Sprint_Turn 매칭 실패.

### 변경 식

```
bIsSprintEndTransition = (SprintEndTransitionRemain > 0) AND (PendingWalkMode != SBWalk_Sprinting)
```

Sprint 재진입 (PendingWalkMode 가 다시 Sprinting) 하면 즉시 sset=false. Timer 는 그대로
0.3 초 흐르되 flag 만 게이트로 가려짐.

### IsSprinting() 직접 호출 시도 → ThreadSafe 위반

처방서는 `SBCharacter::IsSprinting()` 직접 호출 우선, 실패 시 PropertyAccess fallback.
시도 결과:

1. `Get SBCharacter` (`K2Node_VariableGet_68`) + `Call IsSprinting`
   (`K2Node_CallFunction_40`, function_class=`/Script/SB2.SBCharacter`) — 컴파일 4 errors:
   - `Get SBCharacter 오브젝트 레퍼런스에 접근하는 것은 스레드 세이프 방식이 아닙니다`
   - `IsSprinting 스레드 세이프 그래프 Is Sprinting 에서 호출된 스레드 세이프 방식이 아닌 함수 UpdateVariables`
2. `K2Node_PropertyAccess` 노드는 `add_node` 로 만들어지나 **binding path 설정 액션이
   Monolith API 에 없음** (set_property_access_path Unknown action). path 없이 wildcard
   상태 → 사용 불가
3. **PendingWalkMode 비교 대체** (Phase 1 패턴 재사용) — ThreadSafe 통과

### 노드 변경

**제거:** `K2Node_VariableGet_68`, `K2Node_CallFunction_40` (IsSprinting), `K2Node_CallFunction_41` (NOT), `K2Node_PropertyAccess_0` (wildcard)

**추가 (3개):**
- `K2Node_VariableGet_69` (Get PendingWalkMode) at (2784, 6560)
- `K2Node_EnumInequality_1` (PendingWalkMode != SBWalk_Sprinting) at (3008, 6560)
- `K2Node_CallFunction_42` (BooleanAND) at (3232, 6432)

**결선:**
- `CallFunction_38.ReturnValue` (Remain>0) → `CallFunction_42.A`
- `VariableGet_69.PendingWalkMode` → `EnumInequality_1.A`
- `EnumInequality_1.B` default = `SBWalk_Sprinting`
- `EnumInequality_1.ReturnValue` → `CallFunction_42.B`
- `CallFunction_42.ReturnValue` → `VariableSet_75.bIsSprintEndTransition`
- (분해) `CallFunction_38.ReturnValue` ↔ `VariableSet_75.bIsSprintEndTransition` 끊김

### 컴파일/저장

- `compile_blueprint`: success=True, status=UpToDate, errors=0, warnings=0
- `save_asset`: **success** (was_dirty=true) — Phase 1/1.5 와 달리 이번엔 P4 checkout 정상
- `validate_blueprint`: 0 node_errors. 우리 새 노드 disconnected/error 없음
- side-effect: 컴파일러가 dead 노드 4개 자동 정리
  (CallFunction_31, ExecutionSequence_0, VariableGet_56, VariableSet_37 —
   `Set bIsPlayingTransitionBack` 죽은 분기 + 미사용 ExecutionSequence 압축).
  의도된 동작 영향 없음.

### 백업

- pre: `C:/Dev/Sanjuk-Unreal/Saved/sset_pre_graph.json`
- post: `C:/Dev/Sanjuk-Unreal/Saved/sset_post_graph.json`

### 사용자 PIE 확인 사항

1. **Sprint 유지 중 좌우 회전**: PendingWalkMode=Sprinting 유지되는 frame 에서
   sset=false 가 즉시 잡히는지 (이전엔 0.3 s timer 동안 true 유지). Chooser 가
   Sprint_Turn 매칭 가능해야 함
2. **Sprint → Jog 락온 전환** (Phase 1.5 기능): 여전히 0.3 s 동안 sset=true 유지
   (PendingWalkMode 가 Jogging 으로 빠지므로 게이트 OK)
3. **재진입 timing**: Sprint → 잠깐 Jog → Sprint 재가속 시퀀스에서 sset 이
   Sprint 재진입과 동시에 false 로 떨어지는지

### 학습 / 패턴

- ABP UpdateVariables 같은 ThreadSafe 그래프 안에서 외부 actor 함수 호출은
  **PropertyAccess 또는 ABP 멤버변수 캐시** 경유. Monolith 로 PropertyAccess path
  설정 불가하므로, **ABP 가 이미 캐시하는 변수**(`PendingWalkMode`, `SBCharacter`,
  `bIsLockOn` 등) 만 ThreadSafe-safe 하게 읽을 수 있음.
- `Get SBCharacter` 도 ABP 멤버변수임에도 ThreadSafe 위반 — object reference 자체가
  비-ThreadSafe 분류. PropertyAccess 만이 정식 통로.

## Phase 1.7 — Phase 1.5 식으로 회귀 (2026-05-14)

### 동기

Phase 1.6 식 `(Remain > 0) AND (PendingWalkMode != Sprinting)` 운용 결과 사용자 호소:
- Sprint 종료 frame 에서 PendingWalkMode buffer 가 1-2 frame 늦게 Jogging 으로 빠짐
- 그 사이 게이트가 true (== Sprinting) 로 sset=false 유지 → 검출 누락 window 발생
- Sprint_Turn 끼임 재현 → 게이트 제거 결정

### 변경 식 (Phase 1.5 회귀)

```
bIsSprintEndTransition = (SprintEndTransitionRemain > 0)
```

Sprint 유지 중 좌우 이동 시 0.3 s sset=true 유지는 Phase 2 Chooser 처방으로 보완 예정
(MovementState/Direction 으로 분기). buffer 지연 문제가 더 큰 비용이라 회귀 우선.

### 노드 변경

**제거 (3개):**
- `K2Node_CallFunction_42` (AND Boolean)
- `K2Node_EnumInequality_1` (PendingWalkMode != Sprinting)
- `K2Node_VariableGet_69` (Get PendingWalkMode — UpdateVariables 내 다른 PendingWalkMode get
  은 `VariableGet_14`, `VariableGet_50` 두 곳 — 별도 용도, 보존)

**결선:** 변경 없음. Phase 1.6 작업 후에도 graph in-memory 상태에서
`CallFunction_38.ReturnValue → VariableSet_75.bIsSprintEndTransition` 직결이 이미 존재했음
(처방서의 "현재 식: AND 게이트 경유" 가정과 달리 graph dump 가 직결 상태로 나옴).
따라서 orphan 3개 제거만 수행. 결과적으로 Phase 1.5 식과 동일.

### 컴파일/저장

- `compile_blueprint`: success=True, status=UpToDate, errors=0, warnings=0
- `save_asset`: success (was_dirty=false — 컴파일 시점 이미 디스크 반영됨 추정)
- 노드 카운트: 325 → 322 (정확히 -3, added=0)
- 잔존 PendingWalkMode get: 2개 (VariableGet_14, VariableGet_50) — side effect 없음

### 백업

- pre graph: `C:/Dev/Sanjuk-Unreal/Saved/Logs/UpdateVariables_graph_pre.json`
- post graph: `C:/Dev/Sanjuk-Unreal/Saved/Logs/UpdateVariables_graph_post_20260514.json`
- compile: `C:/Dev/Sanjuk-Unreal/Saved/Logs/compile_post_20260514.json`
- save: `C:/Dev/Sanjuk-Unreal/Saved/Logs/save_post_20260514.json`

### 사용자 PIE 확인 사항

1. **Sprint 종료 buffer-지연 window**: Sprint 키 release 직후 sset=true 가 jes=true 와
   같은 프레임에 잡히는지 (1-2 frame window 사라졌는지)
2. **Sprint 유지 중 좌우 이동**: sset=true 가 0.3 s timer 동안 유지됨 — Phase 2 Chooser
   처방으로 Sprint_Turn 분기 분리 필요. 본 회귀로는 미해결

## Phase 1.8 — TargetRotationDelta 각도 게이트 추가 (2026-05-14)

### 동기

Phase 1.7 식 `(Remain > 0)` 단독 운용 결과 Sprint→Battle 락온 전환에서 `F_Lfoot` 끼임
발생. 사용자 분석:
- Sprint 종료 직후 timer 0.3 s 동안 sset=true 유지 → Chooser 가 F_Lfoot 변형 제외
- 그러나 **방향 결정 전 (트레지트 직후 정면 유지)** 구간에서도 sset=true 유지되어
  Chooser 가 잘못 분기 → F_Lfoot 후보를 못 고름
- |TargetRotationDelta| 가 충분히 커진 (방향이 결정된) 시점부터 sset=true 가 의미 있음

### 변경 식

```
bIsSprintEndTransition = (SprintEndTransitionRemain > 0)
                         AND (|TargetRotationDelta| > SprintEndTransitionAngleThreshold)
```

Default threshold = 45.0 deg. |trd|<45 (정면 ±45 fan) 동안 sset=false 유지 →
Chooser 가 F 계열 정상 분기. |trd|>=45 (좌/우 또는 후방 결정) 후 sset=true →
Sprint_Turn 차단 효과 발동.

### 변수 추가 (1개)

| 변수 | 타입 | 카테고리 | default | IE |
|---|---|---|---|---|
| `SprintEndTransitionAngleThreshold` | double | Essential Values | 45.0 | **true** |

`add_variable` 에서 type="real" 거부 → "double" 로 사용 (UE 5.7 LWC, ABP 일관).
SprintEndTransitionDuration 과 동일 메타.

### 노드 변경

**추가 (5개, `add_nodes_bulk`):**

| temp_id | node_id | class | 설명 |
|---|---|---|---|
| Get_TRD | K2Node_VariableGet_57 | VariableGet | TargetRotationDelta (재할당된 id) |
| Abs | K2Node_CallFunction_34 | CallFunction Abs | KismetMathLibrary |
| Get_Threshold | K2Node_VariableGet_58 | VariableGet | SprintEndTransitionAngleThreshold |
| Greater_AbsTRD | K2Node_CallFunction_37 | CallFunction Greater_DoubleDouble | \|trd\| > Threshold |
| AND_node | K2Node_CallFunction_40 | CallFunction BooleanAND | 최종 AND |

위치: Set_75 좌측 하단 ((2208,6624)~(2720,6560) 박스).

**결선 (`connect_pins_bulk`, 6/6 success):**

| from | to |
|---|---|
| VariableGet_57.TargetRotationDelta | CallFunction_34.A (Abs) |
| CallFunction_34.ReturnValue | CallFunction_37.A (Greater) |
| VariableGet_58.SprintEndTransitionAngleThreshold | CallFunction_37.B |
| CallFunction_38.ReturnValue (Remain>0) | CallFunction_40.A |
| CallFunction_37.ReturnValue (\|trd\|>thr) | CallFunction_40.B |
| CallFunction_40.ReturnValue | VariableSet_75.bIsSprintEndTransition |

기존 직결 `CallFunction_38.ReturnValue → VariableSet_75.bIsSprintEndTransition` 끊음
(disconnect_pins: node_id=CallFunction_38, pin_name=ReturnValue, target=Set_75).

### 안전 검증 (side effect)

- Set_75.execute 입력 보존: `VariableSet_73.then`, `VariableSet_74.then` (timer 분기) 둘 다
- Timer 갱신 로직 (Branch IfThenElse_0 + Set Remain) 변경 없음
- isSprintEnding 검출 (`JustExitedSprint AND IsLockOn`) 변경 없음
- Set_75 위치는 자동 시프트로 (2720,6416) → (3040,6416). 동작 영향 없음
- CallFunction_38.B 는 default_value="0.0" 유지 (Remain > 0 의미 동일)
- ThreadSafe: 모든 신규 노드 pure (VariableGet/Abs/Greater/AND). 메타 영향 없음

### 컴파일/저장

- `compile_blueprint`: success=True, status=UpToDate, errors=0, warnings=0
- `save_asset`: saved=true (was_dirty=false — 컴파일 시점에 이미 디스크 반영)

### 트러블슈팅 — add_node 키 정정

처음 `add_nodes_bulk` 호출에서 잘못된 키 사용 (`function`, `function_class`, `variable`)
→ 노드는 만들어지나 핀이 없음. 5개 모두 remove 후 정확한 키로 재호출 →

**정확한 add_node 스키마**:
- `node_type` (필수): "CallFunction", "VariableGet", "VariableSet", "Branch", … 또는 alias ("get", "set", "call", "if", …)
- `function_name` (CallFunction 용)
- `target_class` (CallFunction 용, optional — 생략 시 모든 로드된 class 검색)
- `variable_name` (VariableGet/Set 용)

prefix "K2Node_" 사용 시 generic fallback (`reference_monolith_animgraph_editing_limits.md`)
— 빈 핀 노드 만들어짐. prefix 없이 사용.

### 백업

- pre graph: `C:/Dev/Sanjuk-Unreal/Saved/Logs/UpdateVariables_pre_20260514_1359.json` (184,510 bytes)
- post graph: `C:/Dev/Sanjuk-Unreal/Saved/Logs/UpdateVariables_post_20260514_1359.json` (187,349 bytes)
- 차분: +2,839 bytes (5 신규 노드 + 4 신규 연결 + Set_75 위치 변경)

### 사용자 PIE 확인 사항

1. **정면 유지 구간**: Sprint→Battle 전환 직후 |trd|<45 (정면 ±45 fan) 동안 sset=false 유지
   → Chooser 가 F_Lfoot 등 F 계열 정상 분기
2. **방향 결정 후**: |trd|>=45 시점부터 sset=true 발동 → Sprint_Turn 차단
3. **threshold 튜닝**: SprintEndTransitionAngleThreshold (Essential Values, IE=true) 를
   PIE 중 디테일 패널에서 조정. 30~60도 범위에서 끼임/전환감 균형 찾기 권장
4. **기존 jes 트리거 보존**: jes=true 와 sset=true 가 |trd|>=45 같은 frame 에 잡히는지

### 한계 / 후속

- TargetRotationDelta 가 매 frame 정확히 업데이트되어야 함. UpdateTargetRotation 의
  Set 시점이 UpdateVariables 보다 먼저 실행되는지 graph order 점검 필요 (실측 시 차이 발견 시
  ExecutionSequence 순서 조정)
- Sprint 직후 한 frame 만이라도 |trd| 가 큰 값으로 누적된 상태라면 첫 frame 즉시 sset=true
  발동 — 이는 의도 (Phase 1.7 회귀 동기와 동일)
- 후방 (|trd|≈180) 회피와 측면 (|trd|≈90) 모두 같은 threshold. 비대칭이 필요하면
  ABS 후 Sign 분기 추가 (Phase 2 후보)

## Phase 1.9 — 2-phase 식 (Forced Delay + Angle Gate) (2026-05-14)

### 동기

Phase 1.8 식 `(Remain > 0) AND (|trd| > 45)` 운용:
- Sprint→Battle 전환 초기 |trd|<45 구간에서 sset=false 유지 → F_Lfoot 정상 분기 OK
- 그러나 **Sprint→Jog 전환 직후 첫 0.1 s** 에 trd 가 아직 안 누적된 frame 에서 `Sprint_Turn` 매칭이 가끔 끼임
- 즉 timer 시작 직후 짧은 forced-true 구간이 필요. 그 후엔 각도 게이트로 정확한 분기

### 변경 식 (2-phase)

```
phase1 = (Remain > Duration - ForcedDelay)        # 첫 ForcedDelay 초 강제 true
phase2 = (Remain > 0) AND (|trd| > Threshold)     # Phase 1.8 식 (게이트)
bIsSprintEndTransition = phase1 OR phase2
```

기본값: Duration=0.3, ForcedDelay=0.1 → threshold = 0.2
- t=0..0.1 (Remain 0.3→0.2): phase1=true → sset=true (trd 무관, Sprint_Turn 강제 차단)
- t=0.1..0.3 (Remain 0.2→0): phase1=false → sset=phase2 (|trd|>45 시점부터 발동)
- t>=0.3 (Remain=0): 모두 false → sset=false

### 변수 추가 (1개)

| 변수 | 타입 | 카테고리 | default | IE |
|---|---|---|---|---|
| `SprintEndForcedDelay` | double | Essential Values | 0.1 | true |

`add_variable` `type="double"` 사용. Duration / Threshold 와 일관 메타.

### 노드 변경

**추가 (6개, add_nodes_bulk):**

| temp_id | node_id | class | 설명 |
|---|---|---|---|
| VG_Dur2 | K2Node_VariableGet_62 | VariableGet | SprintEndTransitionDuration (별도 인스턴스) |
| VG_FD | K2Node_VariableGet_64 | VariableGet | SprintEndForcedDelay |
| SUB_Thr | K2Node_CallFunction_41 | Subtract_DoubleDouble | Duration - ForcedDelay |
| VG_Rem2 | K2Node_VariableGet_66 | VariableGet | SprintEndTransitionRemain (별도 인스턴스, 기존 VG_63 보존) |
| GT_Phase1 | K2Node_CallFunction_43 | Greater_DoubleDouble | Remain > (Duration - ForcedDelay) |
| OR_Phase | K2Node_CallFunction_44 | BooleanOR | phase1 OR phase2 |

위치: Set_75 (3040,6416) 좌측 하단 (2208~3072, 6608~6864) 박스.

**결선 (connect_pins_bulk, 7/7 success):**

| from | to |
|---|---|
| VG_62.SprintEndTransitionDuration | CF_41.A (Sub) |
| VG_64.SprintEndForcedDelay | CF_41.B (Sub) |
| VG_66.SprintEndTransitionRemain | CF_43.A (Greater phase1) |
| CF_41.ReturnValue (Sub) | CF_43.B (Greater phase1) |
| CF_43.ReturnValue (phase1) | CF_44.A (OR) |
| CF_40.ReturnValue (phase2, 기존 AND 그대로) | CF_44.B (OR) |
| CF_44.ReturnValue (sset) | VariableSet_75.bIsSprintEndTransition |

기존 `CF_40.ReturnValue → VariableSet_75.bIsSprintEndTransition` 직결 끊김
(disconnect_pins: node_id=K2Node_CallFunction_40, pin_name=ReturnValue, target=Set_75).

### 안전 검증 (side effect)

- Phase 1.8 노드 (Abs CF_34, Greater CF_37, AND CF_40, VG_57 TRD, VG_58 Threshold) **전부 보존** — phase2 식 그대로 재사용
- Timer 갱신 로직 (Branch IfThenElse_0 + Set Remain_73/_74) 변경 없음
- isSprintEnding 검출 (JustExitedSprint AND IsLockOn) 변경 없음
- Set_75.execute 입력 보존: Set_73.then + Set_74.then
- ThreadSafe: 모든 신규 노드 pure (VariableGet/Subtract/Greater/OR). 메타 영향 없음
- validate: node_errors=0, disconnected nodes 중 우리 신규 노드 없음 (기존 dead 노드만 잔존)

### 트러블슈팅

- `disconnect_pins` param 명 **`node_id` + `pin_name`** 필수 (source_node 아님). 메모리 reference_monolith_http_api.md 와 일치
- `add_variable` 응답에서 IE 플래그 echo 안 됨 — 실제 에디터에서 디테일 패널로 검증 권장

### 컴파일/저장

- `compile_blueprint`: success=True, status=UpToDate, errors=0, warnings=0
- `save_asset`: 1차 실패 (P4 checkout) → 재시도 success (saved=true, was_dirty=true)

### 백업

- pre node graph (요약): `C:/Dev/Sanjuk-Unreal/Saved/Logs/UpdateVariables_pre_phase19.json`
- post node graph (요약): `C:/Dev/Sanjuk-Unreal/Saved/Logs/UpdateVariables_post_phase19.json`
- 노드별 검증 dump: `Saved/Logs/{cf40_pre,set75_pre,or_post,set75_post,gtphase1_post,sub_post}.json`
- compile: `Saved/Logs/compile_phase19.json`
- validate: `Saved/Logs/validate_phase19.json`
- save: `Saved/Logs/save_phase19.json`, `save_phase19_retry.json`

### 사용자 PIE 확인 사항

1. **forced 구간 (첫 0.1 s)**: Sprint 종료 frame 부터 Remain ≈ 0.3→0.2 동안 |trd| 와 무관하게 sset=true 유지
2. **gate 구간 (그 후 0.2 s)**: Remain 0.2→0 동안 |trd|>=45 일 때만 sset=true
3. **튜닝**: SprintEndForcedDelay (Essential Values, IE=true) 디테일 패널에서 0~Duration 사이 조정 가능
   - 0 → Phase 1.8 식으로 회귀
   - Duration → 전 구간 forced (= Phase 1.7 식)
4. **Chooser 효과**: Sprint→Jog 락온 전환 첫 frame 부터 Sprint_Turn 차단. 그 후 |trd|<45 정면 fan 에서 F_Lfoot 정상 분기 유지

## Phase 1.10 — isSprintEnding 트리거에 Sprint 유지 게이트 (2026-05-14)

### 동기

Phase 1.9 까지 트리거 식 `isSprintEnding = JustExitedSprint AND IsLockOn` 운용:
- Sprint→Jog 전환 시점은 정확히 잡힘 (jes 즉시 edge 검출)
- 그러나 **Sprint 유지 중 좌우 키 토글로 발생하는 false JustExitedSprint pulse** 케이스에서
  timer 가 0.3 s 시작되어 sset 이 잘못 발동
- 트리거 자체에 `PendingWalkMode != SBWalk_Sprinting` 게이트를 추가해, 진짜로 Sprint 모드를
  벗어난 경우에만 timer 시작

### 변경 식

```
Before: isSprintEnding = JustExitedSprint AND IsLockOn
After:  isSprintEnding = JustExitedSprint AND IsLockOn AND (PendingWalkMode != SBWalk_Sprinting)
```

### 노드 변경

**추가 (3개, add_nodes_bulk):**

| temp_id | node_id | class | 설명 |
|---|---|---|---|
| VG_PWM2 | K2Node_VariableGet_68 | VariableGet | PendingWalkMode @ (832,6592) |
| ENUMINEQ | K2Node_EnumInequality_2 | EnumInequality | PendingWalkMode != SBWalk_Sprinting @ (1056,6608) |
| AND_45 | K2Node_CallFunction_45 | CallFunction BooleanAND @ (1456,6512) |

**결선 변경:**

| 작업 | from | to |
|---|---|---|
| 끊김 | K2Node_CallFunction_35.ReturnValue (`JustExitedSprint AND IsLockOn`) | K2Node_IfThenElse_0.Condition |
| 추가 | K2Node_VariableGet_68.PendingWalkMode | K2Node_EnumInequality_2.A |
| 추가 | K2Node_CallFunction_35.ReturnValue | K2Node_CallFunction_45.A |
| 추가 | K2Node_EnumInequality_2.ReturnValue | K2Node_CallFunction_45.B |
| 추가 | K2Node_CallFunction_45.ReturnValue | K2Node_IfThenElse_0.Condition |

`K2Node_EnumInequality_2.B` default = `SBWalk_Sprinting` (set_pin_default 적용).

### 컴파일/검증/저장

- `compile_blueprint`: success=True, status=UpToDate, errors=0, warnings=0
- `validate_blueprint`: node_errors=0. 우리 신규 3개 노드 disconnected 없음
  (UpdateVariables 의 dangling 4개는 Phase 1.5 이전부터 존재하는 Knot_10/VariableSet_29/Knot_20/VariableSet_64)
- `save_asset`: **실패** ("Failed to save asset", P4 잠금) → 사용자 에디터에서 Ctrl+S 수동 저장 필요
- 노드 카운트: 333 → 336 (정확히 +3)
- ThreadSafe: 신규 노드 모두 pure (VariableGet/EnumInequality/AND Boolean)

### 안전 검증 (side effect)

- timer 분기 (IfThenElse_0 → Set_73/Set_74) 변경 없음
- Phase 1.9 2-phase 게이트 (CF_40, OR_Phase=CF_44) 변경 없음
- bIsSprintEndTransition 최종 Set 결선 변경 없음
- 다른 PendingWalkMode VariableGet (VG_14, VG_50) 보존

### 백업

- pre dump: `C:/Dev/Sanjuk-Unreal/Saved/Logs/phase110/uv_pre.json` (333 노드)
- post dump: `C:/Dev/Sanjuk-Unreal/Saved/Logs/phase110/uv_post.json` (336 노드)
- 응답 파일: `Saved/Logs/phase110/resp_{addnodes,disconnect,setpindef,connect,compile,validate,save}.json`

### 트러블슈팅

- `disconnect_pins` 스키마: `node_id` + `pin_name` (필수) + `target_node` + `target_pin` (옵션).
  source/target 키워드 사용 시 missing_params 에러
- `set_pin_default` 스키마: `value` (string) 필수. `default_value` 사용 시 missing_params 에러
- `validate_blueprint` disconnected_nodes 는 그래프-별로 구분 안 된 채 평면 출력 — graph
  필드로 필터링하면 안전. `K2Node_CallFunction_45` id 가 DrawDebug 그래프의 별개 Print
  String 노드와 충돌하나 그래프-내 dangling 검사에선 무시 가능

### 사용자 PIE 확인 사항

1. **Sprint 유지 중 좌우 토글 시** false jes pulse 가 생겨도 PendingWalkMode 가 여전히
   Sprinting → timer 시작 안 됨, sset=false 유지
2. **Sprint→Jog 락온 전환**: jes=true + PendingWalkMode→Jogging 같은 frame 에 timer 시작,
   Phase 1.9 2-phase 식이 정상 동작
3. **저장 마무리**: 본 변경은 메모리 적용 + compile 완료. 사용자가 PC_01_ABP 를 에디터에서
   Ctrl+S 로 디스크 저장해야 PIE 에서 영구 반영

## Phase 1.13 — 독립 isSprintEnding 변수 노드 그룹 추가 (2026-05-14)

### 동기

사용자가 별도 `isSprintEnding` (bool) ABP 변수를 추가하고, UpdateVariables 그래프 우측
빈 공간 (x=4500~5400) 에 **기존 결선을 일절 건드리지 않는 격리된 계산 노드 그룹**을 신설.
exec 결선은 의도적으로 비워둠 — 사용자가 추후 수동으로 ExecutionSequence 분기 또는 기존
Set 노드의 then 에 연결 예정.

식:
```
isSprintEnding = JustExitedSprint AND IsLockOn AND (PendingWalkMode != SBWalk_Sprinting)
```

Phase 1.10 의 트리거 식과 동일하지만, 본 그룹은 **타이머/게이트 체인 없이 isSprintEnding
변수 단일 값**을 매 틱 갱신하는 단순 boolean. 기존 `bIsSprintEndTransition` (timer 기반)
와는 독립.

### 노드 추가 (7개, add_nodes_bulk)

| temp_id | 실제 node_id | class | 용도 | position |
|---|---|---|---|---|
| VG_JES | K2Node_VariableGet_84 | VariableGet | JustExitedSprint | (4500,6400) |
| VG_IL | K2Node_VariableGet_85 | VariableGet | IsLockOn | (4500,6500) |
| VG_PWM | K2Node_VariableGet_86 | VariableGet | PendingWalkMode | (4500,6600) |
| ENUMINEQ | K2Node_EnumInequality_3 | EnumInequality | PendingWalkMode != Sprinting | (4720,6620) |
| AND1 | K2Node_CallFunction_33 | BooleanAND | JES AND IL | (4900,6450) |
| AND2 | K2Node_CallFunction_42 | BooleanAND | AND1 AND ENUMINEQ | (5120,6500) |
| SET_ISE | K2Node_VariableSet_83 | VariableSet | isSprintEnding | (5360,6480) |

### 데이터 결선 (connect_pins_bulk, 6/6 success)

```
VG_JES.JustExitedSprint   → AND1.A
VG_IL.IsLockOn            → AND1.B
VG_PWM.PendingWalkMode    → ENUMINEQ.A
AND1.ReturnValue          → AND2.A
ENUMINEQ.ReturnValue      → AND2.B
AND2.ReturnValue          → SET_ISE.isSprintEnding   (data input)
```

ENUMINEQ.B default = `SBWalk_Sprinting` (set_pin_default).

### 무손상 검증

Pre/post graph diff (`Saved/Logs/phase113/uv_{pre,post}.json`):
- pre 338 노드 → post 345 노드 (정확히 +7)
- removed = 0
- **기존 노드의 핀-연결 변경 = 0건** (목표 달성)

### 컴파일/저장

- `compile_blueprint`: success=True, status=UpToDate, errors=0, warnings=0
  - SET_ISE.execute 가 unconnected 상태지만 dangling Set 은 warning 미발생
- `validate_blueprint`: K2Node_VariableSet_83 가 disconnected_nodes 리스트에 등장 — **의도된 상태** (사용자가 수동으로 exec 결선 예정). 다른 항목은 사전 상태와 동일
- `save_asset`: **실패** ("Failed to save asset", P4 잠금) → 사용자 Ctrl+S 폴백

### 사용자 수동 작업 (필수)

`K2Node_VariableSet_83` (Set isSprintEnding) 의 **execute 입력 핀** 에 exec 연결을 추가해야
변수가 매 틱 갱신됨. 옵션:
1. UpdateVariables 의 기존 ExecutionSequence (예: K2Node_ExecutionSequence_3) 에 새 then 핀 추가
2. 기존 Set 노드의 then output → SET_ISE.execute → 그 노드의 다음 노드 사이에 끼워넣기

연결 안 하면 isSprintEnding 변수는 default 값 (false) 으로 고정.

### 백업

- pre: `C:/Dev/Sanjuk-Unreal/Saved/Logs/phase113/uv_pre.json` (193,186 bytes)
- post: `C:/Dev/Sanjuk-Unreal/Saved/Logs/phase113/uv_post.json` (197,086 bytes)
- 차분 +3,900 bytes (7 신규 노드 + 6 신규 데이터 결선)
- 응답 파일: `Saved/Logs/phase113/{step_a,step_b,step_c,compile,validate,save}_response.json`

## Phase 1.14 — PrevIsSprintEnding 이전 frame 추적 노드 추가 (2026-05-14)

### 동기

사용자가 `PrevIsSprintEnding` (bool) ABP 변수 추가 + 컴파일 완료. Phase 1.13 의
`isSprintEnding` (Set_83) 을 매 틱 캐시해 frame N+1 에서 이전 frame 값 비교 가능하도록 함
(edge 검출/rising-falling 트리거 대비).

식:
```
프레임 N: Set_83 → isSprintEnding = (계산)   ← Phase 1.13
          Set_84 → PrevIsSprintEnding = isSprintEnding (Set_83.then 직후)   ← Phase 1.14
프레임 N+1: PrevIsSprintEnding 은 frame N 의 값
```

### Step 0 — Set_83.then 사전 상태

`K2Node_VariableSet_83.then` 의 connected_to = `[]` (Phase 1.13 후속 그대로) → 새 결선
추가 가능. 기존 결선 손상 risk 0.

Set_83 기존 결선 (사전 dump):
- execute (in) ← Knot_1.OutputPin
- isSprintEnding (in, data) ← CallFunction_42.ReturnValue (AND2 결과)

### 노드 추가 (2개, add_nodes_bulk)

| temp_id | 실제 node_id | class | 용도 | position |
|---|---|---|---|---|
| VG_ISE | K2Node_VariableGet_87 | VariableGet | isSprintEnding | (5360,6600) |
| SET_PREV | K2Node_VariableSet_84 | VariableSet | PrevIsSprintEnding | (5600,6480) |

### 결선 (connect_pins_bulk, 2/2 success)

- `VG_ISE.isSprintEnding (output)` → `SET_PREV.PrevIsSprintEnding (data input)`
- `Set_83.then (output)` → `SET_PREV.execute (input)`

### 트러블슈팅

connect_pins_bulk param 명: `from_node/from_pin/to_node/to_pin` 거부됨
(missing_params: source_node). **`source_node/source_pin/target_node/target_pin`** 필수
(Monolith HTTP API 표준 — Phase 1.10 disconnect 처럼 일관).

### 무손상 검증

Pre/post graph diff (`Saved/Logs/phase114/uv_{pre,post}.json`):
- pre 345 노드 → post 347 노드 (정확히 +2)
- Set_83 의 execute/isSprintEnding 입력 결선 둘 다 보존
- Set_83.then 만 비어있던 → SET_84.execute 로 새로 연결됨 (= 의도된 단일 추가)

### 컴파일/검증/저장

- `compile_blueprint`: success=True, status=UpToDate, errors=0, warnings=0
- `validate_blueprint`: issues=0, 새 노드 disconnected 없음 (SET_84.then 빈 상태는 dangling
  Set 미경고 — Phase 1.13 SET_ISE 와 동일 패턴)
- `save_asset`: **실패** ("Failed to save asset", P4 잠금) → 사용자 Ctrl+S 폴백

### 백업

- pre: `C:/Dev/Sanjuk-Unreal/Saved/Logs/phase114/uv_pre.json`
- post: `C:/Dev/Sanjuk-Unreal/Saved/Logs/phase114/uv_post.json`
- 응답: `Saved/Logs/phase114/{add_nodes,connect2,compile,validate,save}.json`

### 사용자 수동 작업

PC_01_ABP 를 에디터에서 Ctrl+S 로 디스크 저장 필요 (P4 lock 해제 후).

## Phase 2 — `bIsSprintEndTransition` 변수 → Pure 함수 `IsInSprintEndTransition` (2026-05-14)

### 동기

사용자 옵션 d 확정: 검출식을 Pure 함수로 분리. 변수는 "이전 틱 UpdateVariables 에서 set 된 값" 이라 Chooser/Trajectory 평가 시점에 1틱 lag 가능. Pure 함수는 호출 시점에 즉시 evaluate → **타이밍 분리**.

### 신규 함수 `IsInSprintEndTransition`

- 카테고리: `Sprint Transition`
- BlueprintPure: true
- Access: Public
- 입력: 없음 / 출력: `ReturnValue : bool`
- 노드 14개 (Entry + Result + 5 VariableGet + Subtract + 3 Greater + Abs + AND + OR)

**식 (Phase 1.9 와 100% 동일):**
```
phase1 = (SprintEndTransitionRemain > SprintEndTransitionDuration - SprintEndForcedDelay)
phase2 = (SprintEndTransitionRemain > 0) AND (Abs(TargetRotationDelta) > SprintEndTransitionAngleThreshold)
ReturnValue = phase1 OR phase2
```

함수 그래프 노드 매핑:
| node_id | 역할 |
|---|---|
| K2Node_FunctionEntry_0 | Entry |
| K2Node_FunctionResult_0 | Result (ReturnValue ← OR) |
| K2Node_VariableGet_5 | SprintEndTransitionRemain |
| K2Node_VariableGet_6 | SprintEndTransitionDuration |
| K2Node_VariableGet_7 | SprintEndForcedDelay |
| K2Node_VariableGet_8 | TargetRotationDelta |
| K2Node_VariableGet_9 | SprintEndTransitionAngleThreshold |
| K2Node_CallFunction_5 | Subtract (Duration - ForcedDelay) |
| K2Node_CallFunction_6 | Greater phase1 |
| K2Node_CallFunction_7 | Greater (Remain > 0) |
| K2Node_CallFunction_8 | Abs(TRD) |
| K2Node_CallFunction_9 | Greater (Abs > Threshold) |
| K2Node_CallFunction_10 | AND (phase2) |
| K2Node_CallFunction_11 | OR (phase1 OR phase2) |

ThreadSafe 메타: Monolith API 에 BlueprintThreadSafe 설정 액션 없음 ([reference_monolith_animgraph_editing_limits.md](reference_monolith_animgraph_editing_limits.md)). 함수가 ABP 멤버변수 6개만 읽으므로 자연스레 안전, 다만 ThreadSafe 메타 플래그는 사용자가 디테일 패널에서 수동 설정 권장. 패턴은 [project_pc01_animstance_buffer.md](project_pc01_animstance_buffer.md) 와 동일.

### AnimRewindRecorderEmit 변경 (sset 키 소스 교체)

- 제거: `K2Node_VariableGet_41` (Get bIsSprintEndTransition)
- 추가: `K2Node_CallFunction_12` (Call IsInSprintEndTransition) at (3392, 1936)
- 재배선: `CallFunction_12.ReturnValue` → `K2Node_FormatText_2.sset`

ANIM_REC `sset` 값이 이제 **Recorder 호출 시점에 즉시 evaluate** 된 값.

### UpdateVariables 변경 (변수 setter + dead chain 제거)

**삭제 (15개):**
- K2Node_VariableSet_85 (active setter)
- K2Node_VariableSet_80 (orphan setter)
- K2Node_CallFunction_44 (OR — Phase 1.9 final)
- K2Node_CallFunction_43 (Greater phase1)
- K2Node_CallFunction_40 (AND phase2)
- K2Node_CallFunction_41 (Subtract Duration-ForcedDelay)
- K2Node_CallFunction_38 (Greater Remain>0)
- K2Node_CallFunction_37 (Greater Abs>Threshold)
- K2Node_CallFunction_34 (Abs(TRD))
- K2Node_VariableGet_66, _63 (Remain dead instances)
- K2Node_VariableGet_62 (Duration dead instance)
- K2Node_VariableGet_64 (ForcedDelay dead instance)
- K2Node_VariableGet_57 (TRD dead instance)
- K2Node_VariableGet_58 (AngleThreshold dead instance)

**보존 (timer state + isSprintEnding 트리거 체인):**
- K2Node_VariableSet_73 (Set Remain = Duration, true branch)
- K2Node_VariableSet_74 (Set Remain = FMax(0, Remain-DeltaTime), false branch)
- K2Node_IfThenElse_7 (Branch on CABO_14)
- K2Node_CommutativeAssociativeBinaryOperator_14 (AND: JustExitedSprint AND IsLockOn AND PendingWalkMode≠Sprinting)
- 그 입력 VariableGet 들 (VG_69 JustExitedSprint, VG_56 IsLockOn, EnumInequality_1 PWM≠Sprinting)
- Set_73.then 끝 (정상 — 그래프 종착)
- Knot_26.OutputPin 끝 (정상 — else 분기 종착)

### 변수 제거

`bIsSprintEndTransition` (bool, Buffer, default=false) — UpdateVariables 외 read 0건, AnimRewindRecorderEmit 의 VG_41 도 제거됨 → 안전하게 `remove_variable` 호출 성공.

다른 sprint end 관련 변수는 **모두 보존** (함수가 매 호출마다 read):
- SprintEndTransitionRemain (timer state)
- SprintEndTransitionDuration (IE=true, 0.3 default)
- SprintEndForcedDelay (IE=true, 0.1 default)
- SprintEndTransitionAngleThreshold (IE=true, 45 default)

### 컴파일/검증/저장

- compile #1 (함수 생성/wiring 후): success=True, UpToDate, errors=0, warnings=0
- compile #2 (AnimRewindRecorderEmit swap 후): success=True, UpToDate, errors=0
- compile #3 (UpdateVariables dead 제거 후): success=True, UpToDate, errors=0
- compile #4 (변수 제거 후): success=True, UpToDate, errors=0
- validate_blueprint: node_errors=0. 신규 노드 (CallFunction_12, 함수 내부 노드) disconnected 없음. FunctionResult_0 가 disconnected_nodes 에 등장하나 **Pure 함수는 exec wire 없음 — 정상**
- save_asset: **실패** ("Failed to save asset", P4 잠금) → 사용자 Ctrl+S 폴백

### 백업

- 사전 노드 dump (Inspector 가 사전 정찰): `C:/Dev/Sanjuk-Unreal/Saved/Logs/{cabo14,cf44,cf43,cf40,cf41,cf38,cf37,cf34,set85,set80,set73,set74,get41,ifthen7}.json`
- 사후 그래프 dump:
  - `C:/Dev/Sanjuk-Unreal/Saved/PROBE_IsInSprintEndTransition_20260514.json` (7,836 bytes, 14 노드)
  - `C:/Dev/Sanjuk-Unreal/Saved/PROBE_UpdateVariables_post_sset_remove_20260514.json` (184,630 bytes, 323 노드, bIsSprintEndTransition 참조 0건)
  - `C:/Dev/Sanjuk-Unreal/Saved/PROBE_AnimRewindRecorderEmit_post_func_20260514.json` (49,706 bytes, 80 노드)

### 함정 / 학습

- `add_nodes_bulk` 로 CallFunction 노드를 만들면 function 이 "None" 으로 잡혀 컴파일 실패. 단일 `add_node` 로 재생성하면 OK ([reference_monolith_animgraph_editing_limits.md](reference_monolith_animgraph_editing_limits.md))
- `add_function` 파라미터: `name` (not function_name), `access` (not access_specifier)
- `set_function_params` 의 outputs 추가: `{name, type}` 형태
- `remove_variable` 도 `name` (not variable_name)
- Pure 함수의 CallFunction 결과 노드는 self 핀 / exec 핀 없이 ReturnValue 만 — 호출 그래프에서 단순한 데이터 노드처럼 동작
- `add_node` 후 `compile` 한 번 안 돌려도 핀 ID 가 즉시 dump 에 노출됨 (단일 add 한정. bulk 는 reconstruct 미보장)

### 사용자 수동 작업

1. PC_01_ABP 에디터에서 Ctrl+S 로 디스크 저장 (P4 lock 해제 후)
2. (선택) IsInSprintEndTransition 함수 디테일 패널에서 ThreadSafe 메타 플래그 체크
3. PIE 검증:
   - ANIM_REC `sset` 키가 이전과 동일 타이밍/값을 유지하는지 (변수 → 함수 swap 효과 무손상)
   - **Chooser/Trajectory 평가 시점에서 sset=true 가 1틱 빠르게 잡히는지** (타이밍 분리 효과 — 본 Phase 의 핵심 목표)
4. 후속 — Chooser 조건에서 `bIsSprintEndTransition` 참조하던 row 가 있다면 함수 호출로 swap (이번 작업 범위 밖, 추가 Inspector 정찰 후 처방 필요)

## Phase 2.1 — `bIsSprintEndTransition` 변수 부활 (Chooser 인터페이스 복구) (2026-05-14)

### 동기

Phase 2 에서 변수를 제거하고 Pure 함수 `IsInSprintTransition` (실제 이름; 메모리 일부에서 IsInSprintEndTransition 으로 표기됨) 만 남겼으나 — Chooser 테이블 `EvieAnimChooser_StateMachine` row 에서 해당 property 를 못 읽음. **UE Chooser 는 UPROPERTY reflection 만 지원, BlueprintPure 함수 read 불가**. 변수 복구 필수.

### 신규 setter 패턴 — 한 줄 set

이전 (Phase 1.x): 검출식 분기 (Branch + Set Remain + AND/OR 게이트 + Set Flag) 를 UpdateVariables 본 그래프에 직조

신규 (Phase 2.1): UpdateVariables 에서 **`IsInSprintTransition()` 함수 호출 결과를 변수에 직접 set**. 식 1줄.

```
bIsSprintEndTransition = IsInSprintTransition()    # 매 틱 갱신
```

함수와 변수 병용:
- **변수** (`bIsSprintEndTransition`, bool, Buffer, default=false): Chooser reflection 용 인터페이스. 이전 틱 UpdateVariables 끝에 캐시된 값.
- **함수** (`IsInSprintTransition`, Pure, Sprint Transition 카테고리, 14노드, ReturnValue:bool): BP 내부 즉시 평가용. ANIM_REC sset 소스 (AnimRewindRecorderEmit.CallFunction_12) 그대로 유지.

ANIM_REC sset 값은 여전히 함수 호출 (Recorder 호출 시점에 즉시 evaluate). UpdateVariables 의 변수는 1틱 lag 가능하지만 Chooser 가 state 진입 시 1회 evaluate 라 큰 영향 없음.

### 변수 추가

| 변수 | 타입 | 카테고리 | default | IE | BlueprintReadOnly | Replicated |
|---|---|---|---|---|---|---|
| `bIsSprintEndTransition` | bool | Buffer | false | false | false | false |

`blueprint_query.add_variable` (params: `name`, `type`, `default_value`, `category`, `instance_editable`, `blueprint_read_only`, `replicated` — 스키마 키 정정. 이전 메모리 일부에 `variable_name` 으로 잘못 적힌 곳 있음).

### 노드 추가 (3개, UpdateVariables)

| node_id | class | 용도 | position |
|---|---|---|---|
| K2Node_CallFunction_53 | CallFunction | IsInSprintTransition (Pure, ReturnValue 만) | (1300, 1200) |
| K2Node_VariableSet_86 | VariableSet | Set bIsSprintEndTransition | (1600, 1200) |
| K2Node_ExecutionSequence_0 | ExecutionSequence | splice 노드 (then 핀 부족 회피) | (640, 560) |

ExecSeq_3 은 then_0..then_12 모두 사용 중 → connect 시 자동 핀 추가 안 됨 (Monolith 한계). 새 ExecSeq_0 을 then_12 직후에 splice.

### 결선 (connect_pins_bulk 3/3 success)

| from | to |
|---|---|
| K2Node_ExecutionSequence_3.then_12 | K2Node_ExecutionSequence_0.execute |
| K2Node_ExecutionSequence_0.then_0 | K2Node_Knot_1.InputPin (기존 IfThenElse_7 분기 복원) |
| K2Node_ExecutionSequence_0.then_1 | K2Node_VariableSet_86.execute |
| K2Node_CallFunction_53.ReturnValue | K2Node_VariableSet_86.bIsSprintEndTransition (data) |

기존 ExecSeq_3.then_12 → Knot_1 직결은 disconnect (target_node=Knot_1, target_pin=InputPin).

### 안전 검증 (side effect)

- Set_73 / Set_74 / IfThenElse_7 / Knot_27 (Remain timer 분기) 모두 보존 — exec 결선 변경 없음
- K2Node_Knot_26 (Set_74 trailing dangling knot): Monolith 자동 cleanup 으로 제거됨. 동작 영향 0 (그래프 진짜 leaf 의 wire 통과용 knot 이라 의미 없음).
- pre 323 → post 325 (+2 net = +3 신규 노드 - 1 dangling knot)
- AnimRewindRecorderEmit.CallFunction_12: 손대지 않음. ANIM_REC sset 소스 여전히 함수 직접 호출.
- 타이머 변수 4개 (`SprintEndTransitionRemain`, `Duration`, `ForcedDelay`, `AngleThreshold`) 모두 보존.

### 컴파일/검증/저장

- `compile_blueprint`: **errors=2** (ThreadSafe 위반)
  - `K2Node_CallFunction_53`: `IsInSprintTransition  스레드 세이프 그래프  Is in Sprint Transition 에서 호출된 스레드 세이프 방식이 아닌 함수  UpdateVariables`
  - `K2Node_VariableSet_86`: 동일 메시지
- `validate_blueprint`: node_errors 2건 (위와 동일), wire 자체는 정상
- `save_asset`: **실패** ("Failed to save asset", P4 잠금)

### 원인 / 해결

함수 `IsInSprintTransition` 의 BlueprintThreadSafe 메타가 미설정. Monolith API 에 메타 플래그 설정 액션 없음 ([reference_monolith_animgraph_editing_limits.md](reference_monolith_animgraph_editing_limits.md), [project_pc01_animstance_buffer.md](project_pc01_animstance_buffer.md)).

**사용자 수동 작업 필수:**
1. PC_01_ABP 에디터 열고 `IsInSprintTransition` 함수 선택 → My Blueprint 패널 디테일에서 **Thread Safe** 체크박스 ON
2. Compile (PC_01_ABP 컴파일 버튼) → errors 0 확인
3. Ctrl+S 로 디스크 저장 (P4 lock 해제 후)

### 백업

- pre dump (Phase 2 직후): `C:/Dev/Sanjuk-Unreal/Saved/PROBE_UpdateVariables_post_sset_remove_20260514.json` (323 노드, 184,630 bytes)
- post dump (Phase 2.1): `C:/Dev/Sanjuk-Unreal/Saved/PROBE_UpdateVariables_post_setvar_20260514.json` (325 노드)
- 노드 diff: added=3 (CallFunction_53, VariableSet_86, ExecutionSequence_0), removed=1 (Knot_26)

### 사용자 PIE 확인 사항

1. **Thread Safe 메타 ON 후 컴파일 통과** — `IsInSprintTransition` 디테일 패널 체크 후 errors 0
2. **Chooser row 동작**: `EvieAnimChooser_StateMachine` 의 `bIsSprintEndTransition` property read 가 정상 — Sprint→Jog 락온 전환 시 Sprint_Turn 차단 row 매칭 발동
3. **ANIM_REC sset 보존**: AnimRewindRecorderEmit 의 sset 키 출력은 함수 호출 기반 그대로 — 타이밍/값 변화 없음
4. **변수 1틱 lag**: bIsSprintEndTransition (UpdateVariables 끝에 set 됨) 는 frame N 의 함수 결과를 frame N+1 Chooser 가 읽는 구조. Chooser 평가 시점 state 진입 1회라 큰 영향 없음. 실시간 정확성이 더 필요하면 함수 직접 참조 (Chooser 비지원 → 변수 경유 불가피).

