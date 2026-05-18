# PC_01 Sprint 시작 transition 검출 시스템 — Phase 1 완료 (2026-05-14)

## 목적

Sprint 종료 검출(`bIsSprintEndTransition`, 메모리
`project_pc01_sprint_end_transition.md` 참조) 작업 결과, Chooser row 양쪽
(`N_LockOn_TransitToMoving_Jogging` + `N_LockOn_TransitToMoving_Sprinting`)에
같은 변수가 매핑되어 Sprinting 쪽 의미가 비대칭. 따라서 거울 미러로
**Sprint 시작 (Jog→Sprint 가속) transition 검출 변수** 추가.

## 자산

- `/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP`
- 그래프: `UpdateVariables` (ThreadSafe)

## Phase 1 — 완료 항목

### 1.1 변수 4개 추가

| 변수 | 타입 | 카테고리 | default | IE |
|---|---|---|---|---|
| `bIsSprintStartTransition` | bool | Buffer | false | false |
| `SprintStartTransitionRemain` | double | Buffer | 0.0 | false |
| `SprintStartTransitionDuration` | double | Essential Values | 0.3 | **true** |
| `bPrevPendingSprinting` | bool | Buffer | false | false |

어제 Sprint End 변수 (`SprintEndTransition*`) 와 일관된 카테고리/메타.
`add_variable` API 키는 **`name` / `type`** (not `variable_name`/`variable_type`).

### 1.2 UpdateVariables 에 검출 로직 추가 (17 노드)

식 (처방서 의사코드 그대로):
```
bCurrentPendingSprinting = (PendingWalkMode == SBWalk_Sprinting)
bJustEnteredSprint       = bCurrentPendingSprinting AND NOT bPrevPendingSprinting

if bJustEnteredSprint:
    SprintStartTransitionRemain = SprintStartTransitionDuration
else:
    SprintStartTransitionRemain = FMax(0, SprintStartTransitionRemain - DeltaTime)

bIsSprintStartTransition = (SprintStartTransitionRemain > 0)
bPrevPendingSprinting    = bCurrentPendingSprinting   # last (cache)
```

#### 노드 구성 (id 매핑)

| temp | node_id | class | 용도 |
|---|---|---|---|
| VG_PWM | K2Node_VariableGet_74 | VariableGet | PendingWalkMode |
| ENUMEQ | K2Node_EnumEquality_1 | EnumEquality | curr==SBWalk_Sprinting (B default 설정) |
| VG_PREV | K2Node_VariableGet_76 | VariableGet | bPrevPendingSprinting |
| NOT_PREV | K2Node_CallFunction_46 | CallFunction Not_PreBool | |
| AND_ENTER | K2Node_CallFunction_47 | CallFunction BooleanAND | bJustEnteredSprint |
| BR_START | K2Node_IfThenElse_6 | Branch | |
| VG_DUR | K2Node_VariableGet_78 | VariableGet | SprintStartTransitionDuration |
| SET_REM_T | K2Node_VariableSet_37 | VariableSet | Remain (true) |
| VG_REM_F | K2Node_VariableGet_79 | VariableGet | Remain (false branch read) |
| VG_DT | K2Node_VariableGet_80 | VariableGet | "Delta Time" (공백 포함) |
| SUB_DT | K2Node_CallFunction_48 | Subtract_DoubleDouble | |
| FMAX | K2Node_CallFunction_49 | FMax (KismetMathLibrary) | A=0.0 default |
| SET_REM_F | K2Node_VariableSet_76 | VariableSet | Remain (false) |
| VG_REM_FINAL | K2Node_VariableGet_81 | VariableGet | Remain (>0 비교) |
| GT_ZERO | K2Node_CallFunction_50 | Greater_DoubleDouble | B=0.0 default |
| SET_FLAG | K2Node_VariableSet_77 | VariableSet | bIsSprintStartTransition |
| SET_PREV | K2Node_VariableSet_78 | VariableSet | bPrevPendingSprinting (캐시) |

위치: y=6940~7360 (어제 Sprint End 체인 6400~6900 아래 박스), x=144~2540.

#### Exec 진입점

`VariableSet_75.then` (Set bIsSprintEndTransition, 어제 작업 endpoint) 이
비어있어 새 ExecutionSequence 없이 직결 가능:

- `VariableSet_75.then` → `BR_START.execute`
- `BR_START.then` → `SET_REM_T.execute`
- `BR_START.else` → `SET_REM_F.execute`
- `SET_REM_T.then` + `SET_REM_F.then` → `SET_FLAG.execute` (Branch 수렴)
- `SET_FLAG.then` → `SET_PREV.execute`
- `SET_PREV.then` → [] (체인 끝)

어제 Phase 1 작업 (then_12까지 12핀 사용) 이후 ExecSeq_3 에 then_12 가 1개 더
추가되어 있었음 (총 13핀, 다른 작업 흔적). 본 작업에선 추가 ExecSeq 없이
완료.

#### set_pin_default 함정

API 키 **`value`** (not `default_value`). 3건 1차 실패 후 재호출 OK.

### 1.3 ANIM_REC `sstr` 키 — 사용자 수동

`AnimRewindRecorderEmit` 의 K2Node_FormatText pin 자동 생성은 Format 텍스트
박스를 에디터에서 Enter 눌러야 발생 (Monolith API 미지원 — 메모리
`project_pc01_velocity_smoothing.md` 함정 6 동일). 빈 FT 노드 1개
(K2Node_FormatText_1) 생성 시도 후 제거. 사용자 수동 단계.

## 컴파일/저장 결과

- `compile_blueprint`: success=True, status=UpToDate, errors=0, warnings=0
- `validate_blueprint`: node_errors=0, disconnected에 신규 17노드 없음 (전부 정상 연결).
  unused_variables 에 신규 4변수 없음
- `save_asset`: **실패** ("Failed to save asset") — P4 lock 추정. 사용자 에디터에서 수동 저장 필요

## 사용자 수동 단계 체크리스트

1. **에디터 Ctrl+S** 로 save (P4 checkout 후)
2. **UpdateVariables 함수 Details → BlueprintThreadSafe 메타** 유지 확인 (Monolith API 없음)
3. **Chooser row 교체**: `N_LockOn_TransitToMoving_Sprinting` row 매칭 변수를
   `bIsSprintEndTransition` → `bIsSprintStartTransition` 변경 (Monolith Chooser opaque)
4. **AnimRewindRecorderEmit 의 FT_13** (sset 노드) 뒤에 새 FT 노드 삽입,
   Format = `{prev},"sstr"={sstr}` 입력 후 Enter (pin 자동 생성),
   sstr 핀에 `Get bIsSprintStartTransition` 연결, FT 체인을
   FT_11→FT_13(sset)→[new FT_sstr]→FT_12 로 재배선
5. **PIE 검증**: 락온 ON → Jog→Sprint→Jog 반복 → ANIM_REC 의 `sset`/`sstr`
   양쪽 트리거 + Chooser row 매칭 확인

## 파일 경로 (백업/검증)

- 사전 변수 dump: `Saved/Logs/pre_vars_sprint_start.json`
- 사전 graph dump: `scripts/backup/UpdateVariables_pre_sprint_start_20260514.json`
- 사후 변수 dump: `Saved/Logs/post_vars_sprint_start.json`
- 사후 graph dump: `scripts/backup/UpdateVariables_post_sprint_start_20260514.json`
- 노드 id 맵: `Saved/Logs/sprint_start_node_map.json`
- 추가 스크립트: `scripts/build_sprint_start_chain.py`, `scripts/wire_sprint_start_chain.py`

## 패턴 / 학습

- Sprint End endpoint `VariableSet_75.then` empty exec 출구 활용 → ExecSeq 추가 불필요.
  체인 directly extension 패턴
- `add_variable` 정확한 키: `name`, `type` (Monolith blueprint 도메인)
- `set_pin_default` 정확한 키: `value` (not `default_value`)
- 신규 노드 ID 자동 할당이 어제 작업 자취(`K2Node_VariableSet_37` 등 낮은 번호)와
  겹치지 않음을 컴파일 후 dump로 검증 (336 → 353 노드, 중복 0)
