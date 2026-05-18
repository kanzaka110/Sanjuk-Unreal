---
name: pc01-anim-rewind-recorder
description: "PC_01_ABP에 BP-only로 구현한 매 틱 20필드 [ANIM_REC] 로그 레코더. 디버깅 시 한 프레임 단위로 PC_01 상태 캡처용. 토글 메커니즘은 별도 작업으로 보류."
metadata: 
  node_type: memory
  type: project
  originSessionId: 95d95ebd-e198-45ed-97a6-30eca60701fb
---

# PC_01_ABP AnimRewindRecorder — 매 틱 20필드 디버그 레코더 (2026-05-13)

## 무엇

PC_01_ABP의 BlueprintPostEvaluateAnimation 체인 끝에 매 틱 [ANIM_REC] 한 줄을 SB2_2.log에 쏘는 BP-only 디버거. 락온 strafe, evade 시퀀스, FootIK/Clamp/Overlay weight 등을 프레임 단위로 시각화하기 위함.

**핵심 라인 예시:**
```
[ANIM_REC] "f"=3493442,"sp"=310.208,"as"=1,"ms"=1,"ist"=true,"he"=false,
"vlen"=310.208,"pwm"=2,"il"=true,"isf"=false,"isc"=false,"csh"=false,
"trd"=-2.015,"ib"=false,"rmf"=None,"fik"=1,"fca"=1,"ow"=0,"ig"=false,"sc"=0.044
```

## 적용 위치

`/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP` 한 에셋만 수정. 외부 BP / Plugin 없음. P4 변경분은 이 1 uasset만. 사용자 본인 로컬 디버깅용이라 submit 안 함.

## 추가 노드 구성

**변수 1개** (카테고리: `AnimRewind`):
- `bAnimRewindRecording : bool` (instance_editable=true) — Branch_Emit 게이트. 사용자가 ABP 변수 패널에서 default value 클릭으로 ON/OFF (PIE 재시작 필요)

**신규 함수 `AnimRewindRecorderEmit`** (게임 스레드, ThreadSafe 메타 없음, Public access):
- 흐름 (정리 후): `FunctionEntry → Branch(bAnimRewindRecording) → [true] body FormatText (20 args) → wrap FormatText → PrintText [ANIM_REC] line`
- F6/Numpad 입력 폴링 노드들은 SB2 Enhanced Input이 키 consume해서 작동 X — 11노드 모두 제거됨 (정리 2026-05-13)

**EventGraph wire**:
- `BlueprintInitializeAnimation → ExecuteConsoleCommand("log LogBlueprintUserMessages all") → SetReference` — PIE 진입 시 카테고리 자동 활성화
- `BlueprintPostEvaluateAnimation → UpdateValueFromPostEvaluation → DrawDebug → AnimRewindRecorderEmit` — 매 틱 호출

## 20 필드 매핑

| key | 의미 | 변수 / 변환 |
|---|---|---|
| f | 프레임 번호 | GetFrameCount (KismetSystemLibrary) |
| sp | Speed2D | direct |
| as | AnimStance | byte enum → Conv_ByteToString |
| ms | MovementState | byte enum → Conv_ByteToString |
| ist | bIsStart | direct bool |
| he | HasEvade | direct bool |
| vlen | Velocity XY 길이 | KismetMathLibrary::VSizeXY(Velocity) |
| pwm | PendingWalkMode | byte enum → Conv_ByteToString |
| il | IsLockOn | direct bool |
| isf | IsStrafe | direct bool |
| isc | TrjIsCircling | direct bool |
| csh | CircleStrafeHysteresis | direct bool |
| trd | TargetRotationDelta | direct float |
| ib | IsBattle | direct bool |
| rmf | RuleMoveFlag | direct name (wildcard 받음) |
| fik | FootIKWeight | direct float |
| fca | FootClampAlpha | direct float |
| ow | OverlayWeight | direct float |
| ig | IsGuarding | direct bool |
| sc | SearchCost | direct float (MM 비용) |
| sdt | SustainedDirTime | direct float (사용자 추가 — Pivot 트리거 진단) |
| tta | TrjTurnAngle | direct float (사용자 추가) |
| sdpt | bSustainedDirPivotTrigger | direct bool (사용자 추가) |

FormatText 세 개 직렬: `body` (20 args) → `chain` (prev + sdt/tta/sdpt 3 args, 사용자 추가) → `wrap` (`[ANIM_REC] {b}`) → PrintText InText. 향후 필드 더 추가 시 chain 노드에 args 추가하거나 새 chain 노드 직렬 추가.

## 작동 검증 결과 (17,262 라인 캡처)

- **Lock-on strafe 1프레임 단위로 잡힘** (`il`/`isf`/`trd`/`sc` 변화)
- **Evade 시퀀스 정확** — `rmf=Evade` 한 프레임만 뜨고 `he`/`csh` 동작 확인됨
- **MovementState/AnimStance 전환 정확** — byte 값으로 캡처 후 후처리 매핑 필요

## 주의 사항

**Why:** Monolith API로 한 사이클 만들면서 발견한 함정들. 다음에 이걸로 V2 같은 거 만들 때 시간 절약.

**How to apply:**

1. **LogBlueprintUserMessages 묵음** — SB2 빌드는 기본 PrintString/PrintText 로그 카테고리가 묵음. PIE 콘솔에서 `log LogBlueprintUserMessages all` 입력 필요. 이 레코더는 BlueprintInitializeAnimation에서 자동 ExecuteConsoleCommand로 해결.
2. **PC.WasInputKeyJustPressed 무력화** — SB2 Enhanced Input system이 키 입력을 consume해서 ABP에서 PC 레벨 폴링이 작동 안 함. F6/F12/Numpad 모두 동일. 입력 받으려면 PC_01_BP 또는 SB2 Cheat Manager 경유 필요.
3. **FormatText `{{` `}}` brace literal escape는 nested arg와 충돌** — `{{{f}}}` 파서가 arg name으로 `{f` 까지 잡음. JSON brace는 두 FormatText 직렬 (body 안에 brace 없음, wrap에서 별도 처리)로 우회.
4. **byte enum은 FormatText wildcard 받지 못함** — "포맷 아규먼트는 바이트... 만 가능" 에러. byte enum도 byte인데 enum metadata 때문. `KismetStringLibrary::Conv_ByteToString` 한 번 거치면 통과 (결과는 enum value 숫자, name 아님).
5. **천단위 콤마** — UE FormatText가 정수 `f=3,493,442` 식으로 콤마 박음. JSON 파싱 전 strip 필요: `sed 's/\([0-9]\),\([0-9]\)/\1\2/g'`
6. **add_function의 access="Private"은 ABP에서 컴파일 경고 유발** — 같은 BP 내 호출이라 동작은 OK지만 경고 잡힘. Public으로 만들 것 (또는 사후 에디터에서 Access Specifier 변경).
7. **Branch_Emit Condition=true 임시 우회 상태** — 토글 안 되니까 매 틱 발화. 정상 토글 복원 시 Condition에 `bAnimRewindRecording` 변수 GET 다시 wire.

## 로그 추출

`E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2_2.log` (또는 SB2.log)

```bash
grep -E '\[ANIM_REC\]' SB2_2.log | sed 's/\([0-9]\),\([0-9]\)/\1\2/g' > recorder.jsonl
```

이후 enum 매핑 (as/ms/pwm 숫자 → 이름) 후 분석.

## 미완 / 다음 작업

- **토글 메커니즘** ([[pc01-anim-rewind-toggle-todo]] 등) — 옵션: (a) PC_01_BP에 IA 추가 + ABP 변수 set, (b) ABP details 패널 직접 클릭, (c) SB2 Cheat Manager에 콘솔 명령 등록
- **V2.3 enum name 변환** — 현재 byte 숫자. K2Node_GetEnumeratorNameAsString을 DrawDebug에서 copy_nodes로 복사하면 enum name 그대로 출력 가능 (시도 안 함)
- **Velocity.Z 별도 필드** (`vz`) — 점프 디버그 시 추가

## 확장 이력 — SustainedDirection 게이트 변수 3개 추가 (2026-05-13)

20필드 → **23필드**. 락온 측면 정지 턴모션 + SustainedDir Pivot 게이트 검증용.

### 추가된 키

| key | 변수 | 타입 |
|---|---|---|
| sdt | SustainedDirTime | float |
| tta | TrjTurnAngle | float |
| sdpt | bSustainedDirPivotTrigger | bool |

새 출력 형식 (끝부분):
```
...,"sc"=0.62,"sdt"=0.382,"tta"=12.3,"sdpt"=false
```

### 구현 패턴 — "두 번째 FormatText 끼우기"

기존 FormatText_8(20 args, body)을 **건드리지 않고** 새 FormatText_9 직렬 삽입.

```
[전]  FormatText_8.Result → FormatText_5.b
[후]  FormatText_8.Result → FormatText_9.prev
      VariableGet(SustainedDirTime)        → FormatText_9.sdt   (float, wildcard 추론)
      VariableGet(TrjTurnAngle)            → FormatText_9.tta   (float, wildcard 추론)
      VariableGet(bSustainedDirPivotTrigger) → FormatText_9.sdpt (bool, wildcard 추론)
      FormatText_9.Result → FormatText_5.b
```

FormatText_9 Format = `{prev},"sdt"={sdt},"tta"={tta},"sdpt"={sdpt}` — placeholder 4개로 input 핀 자동 생성.

### 핵심 발견 — FormatText 인자 핀의 wildcard

K2Node_FormatText의 NamedArgument 핀은 **wildcard 타입**으로 시작 → 첫 연결 시 source 타입으로 추론. float/bool/double/int64/name/string 모두 직접 연결 가능, **별도 Conv_* 노드 불필요**. 단 byte enum만 예외 (기존 메모: byte FormatText 함정 — Conv_ByteToString 필요).

### Monolith API로 적용된 노드 추가 절차

1. `add_nodes_bulk` (각 노드에 `node_type` 키 필수) — VariableGet × 3 + FormatText × 1
2. `disconnect_pins` (`node_id` + `pin_name` + `target_node` + `target_pin`) — 기존 FormatText_8→5 연결 끊기
3. `connect_pins_bulk` (각 연결: `source_node, source_pin, target_node, target_pin`) — 5개 연결
4. `compile_blueprint` → `save_asset`

### API 시그니처 함정 정리

- `connect_pins` 파라미터: `source_node, source_pin, target_node, target_pin` (NOT from_*/to_*)
- `disconnect_pins`: `node_id + pin_name + target_node + target_pin` (방향성 추론 가능)
- `add_node`/`add_nodes_bulk`: `node_type` 이 필수 키 (NOT node_class). FormatText는 `format` 파라미터로 placeholder 자동 핀 생성.
- `inspect_graph` 액션 미존재 → `get_graph_data` 사용
- K2Node_FormatText의 Format 텍스트 원본은 API에서 노출 안 됨 (FText prop는 raw 안 보임) — 기존 노드 직접 수정 위험, 새 노드 직렬 삽입이 안전

### 검증 결과

- compile_blueprint: errors 0, warnings 0, status UpToDate
- save_asset: saved=true, was_dirty=true
- FormatText_8의 기존 20핀 모두 그대로 (side effect 없음)
- 사후 dump: `C:/Dev/Sanjuk-Unreal/Saved/anim_rec_post_20260513.json` (사전: `anim_rec_pre_20260513.json`)

### PIE 시나리오 (사용자 검증용)

1. 락온 ON
2. 0.5초 strafe (좌)
3. 반대편(우) 입력
4. SB2_2.log의 `[ANIM_REC]` 라인에서 시계열 확인:
   - strafe 유지 동안 `sdt` 증가 (시간 누적)
   - 방향 전환 순간 `tta` 큰 값 + `sdpt=true` 1프레임
   - 이후 `sdt` 리셋
5. SustainedDirMinTime / SustainedDirAngleThreshold / SustainedDirStableThreshold 와 비교해서 게이트 임계값 튜닝

## 확장 이력 — clip 필드 (BlendStack 현재 클립 추적) 추가 (2026-05-13, 2차)

> **NOTE**: 이 2차 작업은 디스크 미반영(P4 save 실패). 변수 `CurrentAnimSequenceName` 도 4차에서 제거됨. 아래 기록은 절차 레퍼런스로만 유지. 현재 clip 핀 wire는 3차 작업의 `CurrAnimTag` 가 유효.

23필드 → **24필드**. 디버그 라인에 매 틱 MotionMatch가 선택한 AnimSequence 이름 출력.

### 추가된 키

| key | 변수 | 타입 |
|---|---|---|
| clip | CurrentAnimSequenceName | String (FString) |

새 출력 형식 (끝부분):
```
...,"sdpt"=false,"clip"=MM_PC01_Jog_Fwd
```

기본값 `<none>` — 그래프에서 Set 전에는 빈 표시 회피.

### 구현 패턴 — sdt/tta/sdpt 와 동일하게 새 FormatText 직렬 삽입

기존 FormatText_8(20 args body) / FormatText_9(sdt/tta/sdpt chain) 모두 **건드리지 않고** 새 FormatText_0 직렬 끼움.

```
[전]  FormatText_9.Result → FormatText_5.b
[후]  FormatText_9.Result → FormatText_0.prev
      VariableGet(CurrentAnimSequenceName) → FormatText_0.clip   (string, wildcard 추론)
      FormatText_0.Result → FormatText_5.b
```

FormatText_0 Format = `{prev},"clip"={clip}` — placeholder 2개로 prev/clip 핀 자동 생성.

### 신규 노드 ID
- `K2Node_VariableGet_0` — Get CurrentAnimSequenceName (pos 2400,720)
- `K2Node_FormatText_0` — chain wrap (pos 2640,640)

### 변수 추가
- `CurrentAnimSequenceName : String` category=Debug default=`<none>` (InstanceEditable=false, BlueprintReadOnly=false 기본)
- AnimGraph의 MotionMatch 노드 출력 캡처해 Set 해야 동작 — **수동 작업** 별도

### Monolith 절차 (검증됨)

1. `add_variable` — name/type/category/default_value (NOT variable_name/variable_type)
2. `add_nodes_bulk` — VariableGet + FormatText × 1
3. `disconnect_pins` — FormatText_9.Result ↔ FormatText_5.b 끊기
4. `connect_pins_bulk` — 3개 연결 (9→0.prev, VG_0→0.clip, 0→5.b)
5. `compile_blueprint` → errors 0, warnings 0, UpToDate
6. `save_asset` → 실패 (P4 체크아웃) — 사용자 Ctrl+S 필요

### 검증 결과 (2차 확장)
- compile: errors 0, warnings 0
- save: 실패 — **사용자 에디터에서 Ctrl+S 필요**
- FormatText_8/9 기존 핀 무손실 (side effect 없음)
- nodes_count: 35 → 37 (+2)
- 사전 dump: `C:/Dev/Sanjuk-Unreal/Saved/anim_rec_pre_clip_20260513.json`
- 사후 dump: `C:/Dev/Sanjuk-Unreal/Saved/anim_rec_post_clip_20260513.json`

### 수동 작업 (남음) — AnimGraph MotionMatch 출력 캡처

`CurrentAnimSequenceName` 변수에 매 틱 MotionMatch 선택 클립명을 Set해야 출력됨. 자동화 못한 이유: AnimGraph는 EventGraph와 달리 데이터 출력 노드를 임의 위치에 끼우기 위험 (메모리 `feedback_monolith_graph_editing_risks.md` PC_01_ABP AnimGraph 무한루프 전례).

사용자 수동:
1. PC_01_ABP 열기 → AnimGraph 탭
2. `MotionMatch` 노드 찾기 (메모리 `project_pc01_mm_pipeline.md`)
3. 출력 핀 `Result` (FPoseSearchBlueprintResult) 우클릭 → **Split Struct Pin**
4. Split된 핀 중 `SelectedAnimation` (UAnimationAsset*) 핀에서 드래그
5. 검색 → "Get Object Name" 노드 추가
6. `Get Object Name.ReturnValue` (FString) 드래그
7. 검색 → "Set CurrentAnimSequenceName" 노드 추가
8. AnimGraph exec 체인에 끼움 — BlendStack 노드 직전 권장
9. 컴파일 + Ctrl+S

## 확장 이력 — clip 키 wire를 CurrAnimTag로 교체 (2026-05-13, 3차)

clip 필드의 출처 변경: `CurrentAnimSequenceName` (string) → `CurrAnimTag` (name).

### 이유
- 직전 2차 작업의 Save가 P4 체크아웃 실패로 디스크에 반영 안 됨 — 사용자 Ctrl+S도 안 됐던 것으로 추정. 사전 dump 결과 그래프에 clip 노드 자체 없음 (FT_5/FT_8/FT_1만 존재, FT_0 + VG_0 흔적 없음).
- 또한 `CurrentAnimSequenceName` Set 노드를 자동화 불가 (`ValidAnimFromChooser`가 StateMachine sub-graph 내부, Monolith로 접근 불가).
- 기존 `CurrAnimTag` (name) 변수가 이미 `UpdateVariables` 의 `K2Node_GetArrayItem_2` 로 매 틱 `CurrentAnimTags[0]` 캐싱 중 → BlendStack 최상단 첫 tag = 현재 재생 중인 MM 결과 클립의 tag. clip 디버그 의도와 일치.

### 적용 결과 (이번 작업)
이전 작업이 디스크 반영 안 됐으므로 **새로 clip chain 노드를 만듦** (wire 교체가 아니라 신설):
- 신규 `K2Node_VariableGet_26` (Get CurrAnimTag, pos 2400,720)
- 신규 `K2Node_FormatText_2` (Format=`{prev},"clip"={clip}`, pos 2640,640)
- disconnect: `FT_1.Result → FT_5.Format`
- connect (3):
  - `FT_1.Result → FT_2.prev` (text)
  - `VG_26.CurrAnimTag → FT_2.clip` (name, wildcard resolve 성공)
  - `FT_2.Result → FT_5.Format` (text)

### 최종 체인 (검증됨)
```
FT_8 (20 args body)
  → FT_1.prev (sdt/tta/sdpt chain)
    → FT_2.prev (clip chain)
       ← VG_26.CurrAnimTag → FT_2.clip
    → FT_5.Format (wrap)
       → PrintText / Set RewindMonitorLine
```

### 검증
- compile_blueprint: success=true, status=UpToDate, errors 0, warnings 0
- FT_2.clip 핀 type=`name` 으로 정상 추론 — **Conv_NameToString 불필요** (wildcard가 name 직접 수용)
- nodes_count: 35 → 37 (+2). FT_8 20핀 / FT_1 sdt/tta/sdpt 핀 모두 무손실 (side effect 0).
- save_asset 실패 (P4 체크아웃) — 사용자 Ctrl+S 필요 + PIE 재테스트
- 사전 dump: `C:/Dev/Sanjuk-Unreal/Saved/anim_rec_pre_currtag_wire_20260513.json`
- 사후 dump: `C:/Dev/Sanjuk-Unreal/Saved/anim_rec_post_currtag_wire_20260513.json`

### 후속 정리
- 변수 `CurrentAnimSequenceName` — **제거됨 (4차 작업 결과, 아래 참조)**.
- 새 출력 형식: `...,"sdpt"=false,"clip"=MM_PC01_Jog_Fwd` 형태 (CurrAnimTag = MM_PC01_* tag name)

## 확장 이력 — CurrentAnimSequenceName 변수 제거 (2026-05-13, 4차)

3차 작업으로 clip 출처가 `CurrAnimTag` 로 교체되면서 `CurrentAnimSequenceName` 미사용 상태. Monolith `search_nodes("CurrentAnimSequenceName")` 결과 match_count=0 (전체 그래프 Get/Set 0건) 확인 후 안전 제거.

### 적용 결과
- `blueprint.remove_variable` action=remove_variable, param `name` (NOT `variable_name`) → success=true
- `compile_blueprint` → success, UpToDate, errors 0, warnings 0
- `save_asset` → 실패 (P4 체크아웃) — 사용자 Ctrl+S 필요

### 검증 (side effect 0)
- 변수 카운트: 138 → 137 (정확히 -1)
- pre/post 변수명 diff: only `CurrentAnimSequenceName` 사라짐, 추가/이름변경 0
- 사전 dump: `C:/Dev/Sanjuk-Unreal/Saved/vars_pre_remove_cans_20260513.json`
- 사후 dump: `C:/Dev/Sanjuk-Unreal/Saved/vars_post_remove_cans_20260513.json`

### 교훈 (메모리 누적)
- `blueprint.remove_variable` 의 변수 이름 파라미터 키는 `name` (다른 액션의 `variable_name` 과 비일관) — `reference_monolith_http_api.md` 갱신 권장.
- 미사용 변수 제거 전 `search_nodes(query=변수명)` 으로 Get/Set 0건 보장이 안전 체크리스트.

## 확장 이력 — seq 필드 (DrawDebug Animation 메커니즘 활용) 추가 (2026-05-13, 5차)

clip(CurrAnimTag, name) 만으로는 Rewind Debugger 의 클립 라벨 매칭에 부족 — Tag는 MM 그룹명이라 같은 Tag 안에 여러 sequence 존재. 실제 재생 중인 AnimSequence 자체 이름이 필요. SB2 가 이미 **DrawDebug 함수** 안에 sequence 이름 캡처 메커니즘을 가지고 있음을 발견 (사용자 T3D 제공).

### 핵심 발견 — DrawDebug 의 BlendStackInputs 캡처 패턴

DrawDebug 함수 안 chain (소스 확인 완료):
```
VariableGet(BlendStackInputs)  // ABP 멤버, struct:S_BlendStackInputs
   → BreakStruct(S_BlendStackInputs).Anim  // type: object:AnimationAsset
      → KismetSystemLibrary::GetDisplayName(Object=Anim).ReturnValue  // type: string
         → Set Animation (local var, MemberScope=DrawDebug, type=string)
            → SelectString (IsFullBodySlotActive 기준) → "Playing Montage / (Animation)" or "Animation"
               → ... 화면 디버그 출력
```

`BlendStackInputs` 멤버 변수가 **매 틱 갱신** 되고 있어 `.Anim` 의 GetDisplayName 결과가 BlendStack 최상단 현재 재생 sequence 이름과 일치. ANIM_REC 에서 직접 BlendStack API 호출 없이 이 메커니즘 재사용 가능.

### 추가된 키

| key | 변수 | 타입 |
|---|---|---|
| seq | `CurrentSequenceName` (신규 ABP 멤버 변수) | string |

### 옵션 결정

- **옵션 A (채택)**: ABP 멤버 변수 `CurrentSequenceName` 추가 → DrawDebug 안에서 GetDisplayName 결과를 Animation(로컬) 직후 멤버 변수에도 mirror set → ANIM_REC 에서 `Get CurrentSequenceName` 으로 읽음. 단순, side effect 적음.
- 옵션 B (폐기): ANIM_REC 안에 BlendStackInputs → Break → GetDisplayName 체인 복제. 노드 4개 추가 필요 + UpdateVariables 처럼 매 틱 set 위치 불확실.

### 구현 변경

**ABP 멤버 변수 추가 (1개)**:
- `CurrentSequenceName : string`, category=`Debug`, InstanceEditable=false, BlueprintReadOnly=**false** (Set 노드 컴파일 위해), Transient=true

**DrawDebug 함수 변경 (Set Animation 직후 mirror Set 끼움)**:
- 신규 `K2Node_VariableSet_5` (Set CurrentSequenceName, pos -340,512)
- exec 체인: `K2Node_VariableSet_6.then (Set Animation)` → **신규 Set_5.execute** → `K2Node_IfThenElse_3.execute`
- data: `K2Node_CallFunction_7.ReturnValue` (GetDisplayName) → **Set_5.CurrentSequenceName** (기존 Set Animation 과 동일 source 분기)
- 기존 Set Animation (로컬) 의 데이터 흐름 보존 (Animation 로컬 변수는 그대로 SelectString 으로 흘러감).

**AnimRewindRecorderEmit 함수 변경 (clip 후 seq 직렬)**:
- 기존 FormatText_2 (`{prev},"clip"={clip}`) 를 **신규 FT_4 로 교체** (set_pin_default 만으로는 K2Node_FormatText 의 argument 핀 reconstruct 가 트리거 안 됨 → 새 노드를 `format` 파라미터로 만들어야 핀 자동 생성됨)
- 신규 `K2Node_FormatText_4` (Format=`{prev},"clip"={clip},"seq"={seq}`, pos 2528,560)
- 신규 `K2Node_VariableGet_30` (Get CurrentSequenceName, pos 2300,640)
- 신규 체인: `FT_8.Result → FT_4.prev`, `VG_26.CurrAnimTag → FT_4.clip`, `VG_30.CurrentSequenceName → FT_4.seq`, `FT_4.Result → FT_0.prev`
- 기존 `K2Node_FormatText_2` 제거 (remove_node)

### 새 출력 형식

```
[ANIM_REC] ...,sc=0.62,sdt=0.382,tta=12.3,sdpt=false,"clip"=MM_PC01_Jog_Fwd,"seq"=P_Player_Fist_Battle_Jog_Stop_F,...
```

### Monolith API 절차 (검증됨)

1. `add_variable` (name=CurrentSequenceName, type=string, blueprint_read_only=false)
2. `add_node` × 2 (DrawDebug.VariableSet_5, AnimRec.VariableGet_30) + 1 (FT_4 with format=`{prev},"clip"={clip},"seq"={seq}`)
3. `disconnect_pins` × 2 (DrawDebug: Set_6.then↔IfThenElse_3.execute, AnimRec: FT_8.Result↔FT_2.prev 등 자동 처리 — remove_node 시 함께 사라짐)
4. `connect_pins` × 7 (DrawDebug 3: Set_6→Set_5, Set_5→IfThenElse_3, CallFunc_7→Set_5; AnimRec 4: FT_8→FT_4.prev, VG_26→FT_4.clip, VG_30→FT_4.seq, FT_4→FT_0.prev)
5. `remove_node` (FT_2)
6. `set_pin_default` (FT_4.Format) — 보강 (이미 add_node format 으로 설정됐지만 확실히)
7. `compile_blueprint` → errors 0, warnings 0, UpToDate
8. `validate_blueprint` → node_errors 0 (disconnected_nodes 는 사전부터 존재한 별개 orphan)
9. `save_asset` → 실패 (P4 체크아웃) — 사용자 Ctrl+S 필요

### 핵심 함정 — K2Node_FormatText 의 Format 핀 set_pin_default 만으로는 인자 핀 reconstruct 안 됨

이전에 `set_pin_default(FT_2.Format, "{prev},\"clip\"={clip},\"seq\"={seq}")` 호출 시:
- `default_value` 는 새 텍스트로 갱신됨
- compile 후에도 argument 핀 (`seq`) 은 **생성 안 됨**
- 후속 `connect_pins(target_pin="seq")` 는 "Available pins: Format, Result, prev, clip" 에러

해결: **새 FormatText 노드를 add_node 의 `format` 파라미터로 생성**해 argument 핀이 만들어지도록 함 → 기존 노드 교체. 이전 3차 작업에서도 동일 패턴이 효과적이었던 이유.

### 검증
- compile_blueprint: success, UpToDate, errors 0, warnings 0
- 사후 export: FT_4.seq 핀 type=`string`, connected_to=VG_30; FT_4.clip type=`name` 유지; 데이터 chain 모두 보존
- DrawDebug: VariableSet_5.execute ← Set_6.then 연결됨, .then → IfThenElse_3 연결됨, .CurrentSequenceName ← CallFunc_7.ReturnValue
- 사전 dump: `C:/Dev/Sanjuk-Unreal/Saved/drawdebug_pre_20260513.json`, `C:/Dev/Sanjuk-Unreal/Saved/animrec_pre_20260513.json`
- 사후 dump: `C:/Dev/Sanjuk-Unreal/Saved/drawdebug_post_20260513.json`, `C:/Dev/Sanjuk-Unreal/Saved/animrec_post_20260513.json`

### 사용자 작업 (필요)

1. 에디터 활성 → PC_01_ABP 탭 → Ctrl+S (P4 체크아웃 자동 prompt)
2. PIE 진입 → `log LogBlueprintUserMessages all`
3. PC_01 조작 → SB2_2.log 에서 `[ANIM_REC]` 라인 확인:
   - clip = MM_PC01_* (tag)
   - seq = 실제 sequence asset 이름 (e.g. `P_Player_Fist_Battle_Jog_Stop_F`) — Rewind Debugger 클립 라벨과 매칭 가능

### 후속 (다음 작업 후보)

- BlendStack 의 multi-slot 케이스 (FullBody Montage 재생 중) — `IsFullBodySlotActive` 분기에 따라 sequence vs montage 구별 출력
- seq 외 BlendStack 다른 메타 (Loop, StartTime, BlendTime) 도 노출 필요 시 동일 패턴 (DrawDebug 의 BreakStruct 결과 mirror)

## 확장 이력 — 36필드 대확장 (FT_NEW_A 16 + FT_NEW_B 20) (2026-05-13, 6차)

24필드 → **약 60필드**. AnimGraph 상태 (Overlay, FullBody Slot, Wriggle, Travel/Vault, MotionMatch trajectory, curve 등) 를 한 번에 노출하기 위한 대규모 확장.

### 추가된 키 (36개)

**FT_NEW_A (K2Node_FormatText_11) — 16 필드:**

| key | 의미 | 소스 |
|---|---|---|
| mm | MovementMode | VG_0(MovementMode) → EnumToString_6 |
| ops | OverlayPoseState | VG_24(OverlayPoseState) → EnumToString_3 |
| fbsw | FullBodySlotWeight | VG_28 direct float |
| fa | IsFullBodySlotActive | VG_29 direct bool |
| rop | ResetOffsetPulse | VG_59 direct bool |
| sba | IsSequenceBindingActor | VG_20 direct bool |
| ibk | IsBlocked | VG_17 direct bool |
| we | WriggleEnd | VG_43 direct bool |
| iw | InWriggle | VG_38 direct bool |
| jes | JustExitedSprint | VG_11 direct bool |
| htt | HoldTimeThreshold | VG_56 direct double |
| stip | ShouldTurnInPlace | CF_9.ReturnValue direct bool |
| ip | IsPivoting | CF_52.ReturnValue direct bool |
| lm | GetLeanAmount | CF_118.ReturnValue direct double |
| dal | GetCurveValue(Disable_AdditiveLean) | CF_121.ReturnValue float |

**FT_NEW_B (K2Node_FormatText_12) — 20 필드:**

| key | 의미 | 소스 |
|---|---|---|
| phase | GetCurveValue(Phase) | CF_46.ReturnValue float |
| eow | GetCurveValue(enable_orientationwarping) | CF_48.ReturnValue float |
| eprw | GetCurveValue(enable_playratewarping) | CF_18.ReturnValue float |
| fv | VSizeXY(TrjFutureVelocity) | CF_119.ReturnValue double |
| acc | VSizeXY(Acceleration) | CF_120.ReturnValue double |
| isafb | IsSlotActive("FullBody") | CF_40.ReturnValue bool |
| isaub | IsSlotActive("UpperBody") | CF_16.ReturnValue bool |
| sswseq | Blueprint_GetSlotMontageLocalWeight("Sequence") | CF_44.ReturnValue float |
| wt | GetWriggleMoveType | CF_63 → EnumToString_7 |
| cvco | CanVaultCurrentObstacle | CF_11.ReturnValue bool (CMC self 연결됨) |
| ubsw | UpperBodyBlendWeight | VG_30 direct float |
| rva | GetCurrentTravelActionResult.ActionType | CF_43 → EnumToString_5 |
| rvmci | .MatchedConfigIndex | CF_43.ReturnValue_MatchedConfigIndex int |
| ifl | .bIsFalling | CF_43.ReturnValue_bIsFalling bool |
| rj | .bRequiresJump | CF_43.ReturnValue_bRequiresJump bool |
| dog | .DiffOnGround | CF_43.ReturnValue_DiffOnGround float |
| hd | .HeightDiff | CF_43.ReturnValue_HeightDiff float |
| pav_z | TrjPastAngularVelocity_Z | VG_12 split pin double |
| cav_z | TrjCurrentAngularVelocity_Z | VG_13 split pin double |

### 새 출력 형식 (끝부분)

```
...,seq=P_Player_Fist_Battle_Jog_Stop_F,
[ANIM_REC] {prev_chain},"mm"=Walking,"ops"=...,"fbsw"=0,"fa"=false,"rop"=false,"sba"=false,"ibk"=false,"we"=false,"iw"=false,"jes"=false,"htt"=0.25,"stip"=false,"ip"=false,"lm"=0,"dal"=0,
{prev},"phase"=0.3,"eow"=1,"eprw"=0,"fv"=320,"acc"=120,"isafb"=false,"isaub"=false,"sswseq"=0,"wt"=None,"cvco"=false,"ubsw"=0,"rva"=Walk,"rvmci"=0,"ifl"=false,"rj"=false,"dog"=0,"hd"=0,"pav_z"=0,"cav_z"=0
```

### 핵심 발견 (검증) — FormatText placeholder 자동 핀 생성은 add_node 시점 format 파라미터 필수

직전 5차 작업에서 비슷한 함정 기록되었으나 이번 작업에서 명확히 재현/검증:

- **올바른 방법**: `add_node(node_type="FormatText", format="...")` → placeholder `{name}` 들이 즉시 input 핀으로 자동 생성됨. 응답에 pins 배열로 노출.
- **잘못된 방법**: 빈 FormatText 추가 후 `set_pin_default(Format, "...")` → default_value만 갱신되고 argument 핀 reconstruct 안 됨. 후속 connect_pins 시 "Available pins: Format, Result" 에러.

이번 검증:
- FT_NEW_A (`format` 16 placeholder 포함 add_node) → **16/16 pins 자동 생성** ✅
- FT_NEW_B (`format` 20 placeholder 포함 add_node) → **20/20 pins 자동 생성** ✅
- 직전 시도의 FT_3/FT_9 (빈 FT add_node + 후속 set_pin_default) → FT_3는 일부만 6 pins, FT_9는 0 pins (실패)

### CMC self 함정 — SBCharacterMovementComponent 호출 시 Target 핀 명시 wire 필수

`GetCurrentTravelActionResult`, `CanVaultCurrentObstacle` 등 CMC 메서드는 ABP self가 SBCharacterMovementComponent 아니므로 **Target 핀 명시 연결 필요**. 미연결 시 컴파일 에러:
```
"이 블루프린트(셀프)는 SBCharacterMovementComponent 이지 않으므로, ' Target '에 연결이 있어야 합니다."
```

해결: ABP에 이미 캐시된 멤버 변수 `SBCharacterMovement : object:SBCharacterMovementComponent` (사용자 ABP 표준)의 VariableGet 노드 (VG_40) 한 번 추가하고, 모든 CMC 호출의 self에 fan-out wire.

### Monolith API 절차 (검증됨)

1. `remove_node` × 2 — 직전 시도의 빈 FT_3, FT_9 제거
2. `add_node(node_type="FormatText", format="...")` × 2 — FT_11 (16 args), FT_12 (20 args)
3. `connect_pins_bulk` (34건) — paste된 leaf 노드 33 + 추가 1 (모두 성공)
4. `disconnect_pins(FT_5.Result)` — 기존 출력 정리
5. `connect_pins_bulk` (4건) — 체인: FT_5→FT_11.prev, FT_11→FT_12.prev, FT_12→PrintText.InText + Set RewindMonitorLine
6. `compile_blueprint` → 에러 2건 (CF_50, CF_43 CMC self)
7. `remove_node(CF_50)` 후 recompile → CF_43 단독 에러 (예상 — wire 활성화로 검증 트리거)
8. `add_node(VariableGet, "SBCharacterMovement")` → VG_40
9. `add_node(CallFunction, "CanVaultCurrentObstacle", target_class="SBCharacterMovementComponent")` → CF_11 (재추가)
10. `connect_pins_bulk` (3건) — VG_40→CF_43.self, VG_40→CF_11.self, CF_11→FT_12.cvco
11. `compile_blueprint` → success, UpToDate, errors 0, warnings 0 ✅
12. `remove_node(FT_10)` — add_node 부수효과로 발생한 orphan ghost 노드 제거
13. `compile_blueprint` 재 → 클린 유지
14. `save_asset` → 실패 (P4 체크아웃) — 사용자 Ctrl+S 필요

### 부수 발견 — add_node FormatText 가 ghost sibling 노드 생성

FT_NEW_A 추가 시 응답에는 `FT_11` 만 반환했으나, 사후 dump에서 동일 pos `[3184,2032]` 에 `FT_10` 도 존재 (16 placeholder 자동 생성됨, 모두 disconnect). 원인 미상 — Monolith 내부 commit 사이클 추정. 클린업으로 remove_node 해결. **다음 작업 시 add_node 직후 list 재검토 권장.**

### 검증

- compile_blueprint: success=true, status=UpToDate, errors 0, warnings 0
- save_asset: 실패 (P4 lock 추정) — `reference_monolith_animgraph_editing_limits.md` 에 따라 in-memory 적용 보장됨, 사용자 Ctrl+S 필요
- 사전 dump: `C:/Dev/Sanjuk-Unreal/Saved/anim_rec_emit_pre_retry_BACKUP_20260513_2105.json` (78 nodes)
- 사후 dump: `C:/Dev/Sanjuk-Unreal/Saved/anim_rec_emit_final_20260513_2122.json` (79 nodes)
- 신규 노드: FT_11, FT_12, VG_40, CF_11 (+4)
- 삭제 노드: FT_3, FT_9, CF_50, FT_10 (-4)
- 순 변동: 78 → 79 (paste된 33 leaf 노드는 모두 보존되며 wire 완료)
- FT_11 connected pins: 16/16 ✅
- FT_12 connected pins: 20/20 ✅

### 사용자 작업 (필요)

1. 에디터 활성 → PC_01_ABP 탭 → Ctrl+S (P4 체크아웃 자동 prompt)
2. PIE 진입 → `log LogBlueprintUserMessages all`
3. PC_01 조작 → SB2_2.log 에서 `[ANIM_REC]` 라인 새 36필드 검증
4. enum 매핑 후처리: `mm` (MovementMode), `ops` (OverlayPoseState), `wt` (WriggleMoveType), `rva` (TravelActionType) — 모두 EnumToString 거쳐서 enum literal 이름으로 출력됨

## 확장 이력 — StateMachine 5필드 (sms/vac/na/rrt/rrr) 추가 (2026-05-14, 7차)

60필드 → **약 65필드** (단, `vac` 만 default value, 직접 Get/Length 우회). State Machine 분기 / Chooser 결과 / Retransit 진단을 위한 5 필드. 락온 측면 Stop→Turn 시점에 Chooser가 어떤 클립 후보를 내놓는지, MotionMatch가 NullAnim으로 빠지는지, RunRetransit이 어떤 reason으로 트리거되는지 한 줄에서 보기 위함.

### 추가된 키

| key | 변수 | 타입 | 비고 |
|---|---|---|---|
| sms | StateMachineMoveState | byte (enum) | Conv_ByteToString 경유 (메모리 6차 함정 확인) |
| vac | ValidAnimFromChooser.Length | int | **default=-1 우회** (ABP `get_variables` 결과 누락 + 컴파일러 unresolved property → Array_Length+Get 노드 모두 제거 후 default value `-1`로 설정) |
| na | NullAnim | bool | direct |
| rrt | RunRetransit | bool | direct (사용자 처방: ReTransitState보다 frame edge 잡기 적합) |
| rrr | RetransitReason | name | direct (name은 FormatText wildcard 직접 수용) |

새 출력 형식 (끝부분):
```
...,"hd"=0,"pav_z"=0,"cav_z"=0,"sms"=NewEnumerator0,"vac"=-1,"na"=false,"rrt"=false,"rrr"=None
```

### 핵심 발견 — ValidAnimFromChooser는 `get_variables` 결과에서 누락

Inspector 보고는 ABP 변수로 분류했지만 실제 결과:
1. `blueprint.get_variables` 응답에 `ValidAnimFromChooser` 없음 (142개 변수 검사) — 부모 클래스 `SBActorAnimInstance` (C++) 변수 또는 BlueprintReadOnly가 아닌 transient prop일 가능성
2. `add_node(node_type="get", variable_name="ValidAnimFromChooser")` 결과 — VariableGet 노드는 생성되지만 **pins:[] 빈 상태** (제목 "Get", 변수 unresolved)
3. **우회 발견**: `copy_nodes` 로 `SetStateMachineBlendStackAnim` 그래프의 정상 `VariableGet_12` 를 가져오면 핀 정상 (`ValidAnimFromChooser` output type `array:object:AnimationAsset`) → 그래프 단위로는 작동
4. **단, compile 시점에 실패**: `'/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP.PC_01_ABP_C'에서 Valid Anim from Chooser 와 연관된 프로퍼티를 찾지 못했습니다.` → 이 변수는 PC_01_ABP_C 컴파일 결과에 존재하지 않음. SetStateMachineBlendStackAnim 그래프가 이미 같은 unresolved 상태로 운영 중일 가능성 (parent class 상속 변수 미생성 등).

**결정**: vac 필드 값 자체는 안전하게 출력 불가. Array_Length(CF_10) + Get_12 모두 제거하고 **FT_1.vac 핀에 default value "-1"** 설정 — 출력에 항상 -1로 표시 (값 의미 없음, 필드만 자리 유지). 추후 사용자가 BlendStackInputs 같은 alternate 출처로 wire 가능 (SetStateMachineBlendStackAnim 의 정상 Get_12와 동일 ID로 grafting).

### Monolith API 절차 (실측)

1. **pre dump 백업**: `PROBE_AnimRewindRecorderEmit_pre_20260514.json` (81 nodes)
2. **체인 순서 재검증** (가설 vs 실측):
   - 가설 (인스펙터 보고): `FT_8 → 4 → 11 → 13 → 12 → 0 → 5`
   - **실측 (PROBE 덤프 connected_to 추적)**: `FT_8 → FT_4 → FT_0 → FT_5 → FT_11 → FT_13 → FT_12 → (PrintText.InText + VariableSet_1.RewindMonitorLine)`
   - `FT_12` 가 마지막 chain. 새 FT_1 을 `FT_12.Result` 와 `PrintText.InText` 사이에 끼움.
3. `add_node(node_type="get", variable_name=X)` × 4 (StateMachineMoveState/NullAnim/RunRetransit/RetransitReason) → VG_22/42/44/45 (모두 정상 핀 생성)
4. `add_node(node_type="get", variable_name="ValidAnimFromChooser")` → VG_23 (pins:[]) — **실패, 추후 제거**
5. `add_node(node_type="function", function_name="Conv_ByteToString", target_class="KismetStringLibrary")` → CF_6
6. `add_node(node_type="function", function_name="Array_Length", target_class="KismetArrayLibrary")` → CF_10 (wildcard)
7. `add_node(node_type="format_text", format='{prev},"sms"={sms},"vac"={vac},"na"={na},"rrt"={rrt},"rrr"={rrr}')` → FT_1 (6 input pins 자동 생성 확인 ✅)
8. `connect_pins` × 7 — VG들→helpers→FT_1 인자들 + FT_12.Result→FT_1.prev + FT_1.Result→PrintText.InText / VariableSet_1.RewindMonitorLine
9. `compile_blueprint` → **에러 2** (Array_Length wildcard, ValidAnim unresolved)
10. `remove_node` × 2 (CF_10 Array_Length, VG_12 copied) — vac 우회 시작
11. `set_pin_default(FT_1.vac, value="-1")` → success
12. `compile_blueprint` → **success=true, UpToDate, errors 0, warnings 0** ✅
13. `save_asset` → **실패** (P4 lock 추정 — 사용자 Ctrl+S 필요)
14. **post dump**: `PROBE_AnimRewindRecorderEmit_post_20260514.json` (87 nodes, +6 = FT_1, CF_6 ByteToString, VG_22/42/44/45)

### API 시그니처 정정 (이번에 확인된 함정)

- `add_node` 필수 키 = `node_type` (이전 메모리의 `node_class` 오기 → 정정)
- `add_node` 위치 키 = `position` (이전 메모리의 `node_position` 오기 → 정정)
- `connect_pins` 키 = `source_node, source_pin, target_node, target_pin` (메모리 5차 기록과 일치)
- `disconnect_pins` 키 = `node_id, pin_name, target_node, target_pin` (양쪽 끝 지정 필요 — 이전 메모리 정확)
- `set_pin_default` 값 키 = `value` (NOT `default_value`)
- `get_node_details` — 변수 unresolved 진단에 가장 빠름 (pins:[] 이면 변수명 매칭 실패)
- `copy_nodes` — 그래프 간 ABP 변수 노드 복사 가능. 단 컴파일 시점에는 변수 자체가 클래스에 있어야 resolve됨.

### 검증

- node count: 81 → 87 (+6)
- 신규 노드: K2Node_FormatText_1, K2Node_CallFunction_6 (Conv_ByteToString), K2Node_VariableGet_22 (StateMachineMoveState), K2Node_VariableGet_42 (NullAnim), K2Node_VariableGet_44 (RunRetransit), K2Node_VariableGet_45 (RetransitReason)
- 제거 노드: K2Node_VariableGet_23 (unresolved ValidAnim 1차), K2Node_CallFunction_10 (Array_Length wildcard), K2Node_VariableGet_12 (copy된 ValidAnim get) — 총 3개 cleanup
- FT_1 input pins: 6/6 정상 (prev/sms/vac/na/rrt/rrr) — vac만 default="-1", 나머지 4 모두 source wire 정상
- chain 최종: `... → FT_12 → FT_1 → (CF_4 PrintText.InText + VS_1 RewindMonitorLine)` ✅
- 기존 FT_8/4/0/5/11/13/12 의 입력 핀 모두 무손실 (side effect 0)
- compile: errors 0, warnings 0, status UpToDate
- save: 실패 (P4 lock)
- 사전 dump: `C:/Dev/Sanjuk-Unreal/Saved/PROBE_AnimRewindRecorderEmit_pre_20260514.json`
- 사후 dump: `C:/Dev/Sanjuk-Unreal/Saved/PROBE_AnimRewindRecorderEmit_post_20260514.json`

### 사용자 작업 (필요)

1. 에디터 활성 → PC_01_ABP 탭 → Ctrl+S (P4 체크아웃 자동 prompt)
2. PIE 진입 → `log LogBlueprintUserMessages all`
3. PC_01 조작 → SB2_2.log 에서 `[ANIM_REC]` 라인 새 5필드 검증:
   - `sms` — StateMachineMoveState enum의 byte 숫자 출력 (NewEnumerator0/1/2...). 후처리로 enum 이름 매핑 필요 (mm/ops/wt/rva 와 동일 패턴)
   - `vac` — 항상 `-1` (기능 비활성, 자리만 유지). 추후 BlendStackInputs 등 alternate 경유로 정상 출력 wire 가능
   - `na` — MotionMatch 결과가 NullAnim 인지 (true/false)
   - `rrt` — RunRetransit 트리거 발생 (frame edge)
   - `rrr` — Retransit 이유 name (None / Reason1 / Reason2 ...)

### 후속 작업 후보

- **vac 정상화**: `ValidAnimFromChooser` 가 PC_01_ABP_C 컴파일 결과에 안 잡히는 원인 추적 — 부모 C++ `SBActorAnimInstance` 헤더 확인 필요. 또는 BlendStackInputs.Anim 같은 alternate 출처 사용.
- **sms enum 이름 출력**: 다른 enum 필드와 동일하게 `EnumToString` 노드 경유로 변경 (현재 Conv_ByteToString은 숫자만 출력).
- **vac default value 더 명시적인 값**: `-1` 대신 `(skipped)` 같은 텍스트로? — int 핀이라 문자열 불가, 그대로 유지.

## 확장 이력 — 8개 FT 체인을 단일 FormatText로 통합 (2026-05-14, 8차)

7차까지 누적된 FormatText 8개 직렬 (FT_8 → 4 → 0 → 5 → 11 → 13 → 12 → 1) 을 **단일 K2Node_FormatText_2** 로 통합. 노드 수 87 → 80 (-7). 출력 결과/소스 wire는 완전 보존, 라우팅만 변경.

### 동기

- 디버그 라인 1줄 만들기 위해 FT 8개 직렬 = 매 틱 8회 FormatText evaluation. 단일 FT면 한 번이면 충분.
- 함수 그래프 가독성 — 86노드 중 FT 체인이 화면 가로로 깔려있어 다른 leaf 노드 추적 어려움.
- 단일 source-of-truth — Format 문자열 한 곳에서 모든 필드 확인 가능.

### 통합 형식 (66 인자 단일 FT)

```
[ANIM_REC] "f"={f},"sp"={sp},"as"={as},"ms"={ms},"ist"={ist},"he"={he},"vlen"={vlen},
"pwm"={pwm},"il"={il},"isf"={isf},"isc"={isc},"csh"={csh},"trd"={trd},"ib"={ib},
"rmf"={rmf},"fik"={fik},"fca"={fca},"ow"={ow},"ig"={ig},"sc"={sc},"clip"={clip},
"seq"={seq},"bim"={bim},"bpim"={bpim},"ms_l"={ms_l},"ms_p"={ms_p},"mm"={mm},"ops"={ops},
"fbsw"={fbsw},"fa"={fa},"rop"={rop},"sba"={sba},"ibk"={ibk},"we"={we},"iw"={iw},
"jes"={jes},"htt"={htt},"stip"={stip},"ip"={ip},"lm"={lm},"dal"={dal},"sset"={sset},
"phase"={phase},"eow"={eow},"eprw"={eprw},"fv"={fv},"acc"={acc},"isafb"={isafb},
"isaub"={isaub},"sswseq"={sswseq},"wt"={wt},"cvco"={cvco},"ubsw"={ubsw},"rva"={rva},
"rvmci"={rvmci},"ifl"={ifl},"rj"={rj},"dog"={dog},"hd"={hd},"pav_z"={pav_z},
"cav_z"={cav_z},"sms"={sms},"vac"={vac},"na"={na},"rrt"={rrt},"rrr"={rrr}
```

**Format string size**: 810 bytes — `add_node` 의 `format` extra 파라미터 1회 호출로 통과 (placeholder fallback 불필요).

### 옵션 A 절차 (검증됨)

1. `add_node(node_type="format_text", position=[7280,1500], format=<810B>)` → **K2Node_FormatText_2** (66 input pins + Format/Result 자동 생성, 핀 이름 100% 일치) ✅
2. `connect_pins` × 65 (vac 제외) — 처방서 wire map 그대로. **모든 65건 성공**, side effect 없음
3. `set_pin_default(node_id=FT_2, pin_name="vac", value="-1")` → 기존 FT_1 default 보존 ✅
4. `compile_blueprint` → **errors 0, warnings 0, UpToDate** ✅
5. 출력처 스위치:
   - `disconnect_pins` 시도 → **파라미터 스키마 다름** (`node_id`/`pin_name` 필수, `source_*` 사용 시 fail)
   - 그러나 `connect_pins(new_FT.Result → CallFunction_4.InText)` 만으로 **input 단일 connection 정책에 의해 자동 replace 됨** ✅
   - 두 destination (`CallFunction_4.InText`, `VariableSet_1.RewindMonitorLine`) 모두 새 FT.Result 로 단일 wire 전환 검증 (get_node_details 로 FT_1.Result.connected_to=[] 확인)
6. `compile_blueprint` 재 → errors 0 ✅
7. `remove_node` × 8 + 매 회 compile (FT_8 / 4 / 0 / 5 / 11 / 13 / 12 / 1) — 매 단계 errors 0 ✅
8. `save_asset` → **실패 (P4 체크아웃 — 사용자 Ctrl+S 필요)**
9. post dump → 80 nodes (87 - 8 + 1), FormatText 노드 단 1개 (FT_2) ✅

### 핵심 발견 / 함정

- **`disconnect_pins` API 시그니처 (정정)**: 7차 메모리는 `node_id + pin_name + target_node + target_pin` 라고 기록했으나, 이번 호출 시 "Missing required param(s): [node_id, pin_name]. Provided keys: [source_node, source_pin, target_node, target_pin]" 에러 → 양식 다름. `source_*` 키는 지원 안 됨. **정확한 키는 `node_id + pin_name (+optional target_node/target_pin)`**.
- **input 핀 단일 connection 자동 replace**: BP input data 핀은 기본적으로 다중 연결 금지 → 새 connect_pins 시 기존 wire 자동 break. disconnect 명시 호출 실패해도 무방.
- **66 placeholder 의 add_node 1회 통과**: 7차 5필드 (6 placeholder 포함 110B) 가 통과했으니 810B도 안전 가설 → 검증됨. 한계는 미상 (수 KB까지 시도 가치 있음).
- **노드 ID 재사용 패턴**: 7차에서 만든 `K2Node_FormatText_2` 가 5차 작업 때 한 번 등장했다 사라진 ID. Monolith는 grpah 내 사라진 ID도 재할당함. 7차 작업 후 백업 dump의 노드 id 와 8차 dump 의 노드 id 가 `FT_2` 로 충돌하지 않은 이유 = 7차 작업 종료 시점에 `FT_2` 가 이미 그래프에 없었음 (5차에서 제거됨).
- **wildcard 타입 재추론 일관**: 단일 FT 66핀 모두 wildcard로 시작 → 65 wire 연결 시 각각 source 타입으로 추론. byte enum (없음, sms는 사전 Conv_ByteToString CF_6 거침), name (rmf/clip/wt/rva/rrr), bool, float, double, int, string 혼합 모두 통과. 컴파일 0 errors = 타입 추론 충돌 없음 확증.

### 검증

- node count: 87 → 80 (-7 = -8 FT + 1 새 FT)
- FormatText 잔존: 1개 (K2Node_FormatText_2)
- compile: success=true, status=UpToDate, errors 0, warnings 0
- save: 실패 (P4 lock) — 사용자 Ctrl+S 필요
- 사전 dump (백업 복사): `C:/Dev/Sanjuk-Unreal/Saved/PROBE_AnimRewindRecorderEmit_pre_consolidate_20260514.json` (87 nodes, 7차 직후 상태)
- 사후 dump: `C:/Dev/Sanjuk-Unreal/Saved/PROBE_AnimRewindRecorderEmit_consolidated_20260514.json` (80 nodes, 단일 FT)
- 65개 wire 모두 source 노드 ID 의 ReturnValue / 멤버 변수 출력으로 정확히 매핑 — 처방서 100% 일치
- vac default `-1` 7차에서 이어받음 (set_pin_default 명시 적용)

### 사용자 작업 (필요)

1. 에디터 활성 → PC_01_ABP 탭 → Ctrl+S (P4 체크아웃 자동 prompt)
2. PIE 진입 → `log LogBlueprintUserMessages all`
3. SB2_2.log `[ANIM_REC]` 라인이 통합 전과 **동일 필드/동일 값**으로 출력되는지 확인 (66 필드, vac=-1)
4. 출력 라인 길이 ~800 byte/frame — PrintText 로그 잘림 한계 확인 (UE 기본 4096 byte 안에 들지만 후처리 grep 시 안전)

### 후속 작업 후보

- **Format 문자열 추가 인자**: 단일 FT 라 추가 필드 삽입 시 7차 패턴 (chain 새 FT 끼우기) 불필요 → 처방: `add_node` 새 FT (이전 + 신 필드 placeholder 포함) 만들고 wire 옮기는 게 가장 단순. 또는 (위험) Format 핀 default 만 갱신 + 핀 reconstruct? — 5차 메모리: **불가**.
- **build_ft14_chain.py / consolidate_ft_chain_step*.py 스크립트 보존** — 향후 비슷한 합치기/쪼개기 작업 시 패턴 재사용.

## 2026-05-15 크래시 후 풀 복구 (8차 통합 상태 재현)

### 무엇

크래시로 `AnimRewindRecorderEmit` 그래프 자체가 소실 (시나리오 A). 5/14 백업 dump (`PROBE_AnimRewindRecorderEmit_consolidated_20260514.json`, 80 노드)를 기준으로 그래프 + 변수 + Emit hook을 풀 복구. 핵심 부분 컴파일/save 성공, side-effect 0건. 11개 wire는 split-struct/enum-name 한계로 미연결(아래 정리).

### 진행 Phase

1. **Phase 0 — 변수 5개 추가** (`scripts/abrr_phase0_variables.py`):
   - 신규: `bAnimRewindRecording`(bool, AnimRewind, IE=true), `RewindMonitorLine`(text, AnimRewind), `bIsSprintEndTransition`(bool, Buffer), `CurrentSequenceName`(string, 디폴트)
   - 이미 있던 것: `TrjPastAngularVelocity`, `TrjCurrentAngularVelocity` (FVector, cat=디폴트)
   - **누락(API 버그)**: `UpperBodyBlendWeight` — float/double 모두 add_variable success=true 응답인데 실제 추가 안 됨. SBActorAnimInstance C++ 부모 클래스에 이미 정의되어 있을 가능성. **VariableGet 노드는 정상 wire** (부모 변수로 동작).
   - API param 정정: `add_variable` 키는 `variable_name`이 아니라 `name`. `variable_type`이 아니라 `type` (5/14 `restore_abp_variables.py`의 스펙과 다름).

2. **Phase 1 — 함수 그래프 생성** (`add_function`):
   - 파라미터: `{name=AnimRewindRecorderEmit, category=AnimRewind, access=Public}` → node_count=1 (FunctionEntry 자동) ✅
   - API param 정정: `function_name`이 아니라 `name`

3. **Phase 2 — 79 노드 bulk add** (`scripts/abrr_phase2_addnodes.py`):
   - 백업 80개 - FunctionEntry 1 = 79 추가
   - 76 OK (VariableGet 48 + CallFunction 24 + IfThenElse 1 + VariableSet 1 + FormatText 1 + 자동매핑 FunctionEntry 1)
   - **4 FAIL**: `K2Node_GetEnumeratorNameAsString` 노드는 add_node가 직접 지원 안 함. node_type=function/function_name=GetEnumeratorNameAsString 시 "Function not found".
   - 함정: **스크립트 두 번 실행 → 중복 80+80 노드 들어감**. `remove_function` → `add_function` 깨끗하게 재시작 후 한 번만 실행.

4. **Phase 2b — enum-name 우회 추가** (`scripts/abrr_phase2b_enum_names.py`):
   - 후보 함수명 순차 시도: `GetEnumeratorName` ✅ (4건 모두 성공)
   - 단, **GetEnumeratorName output type = `name`** (백업의 GetEnumeratorNameAsString는 `string`). FormatText input 핀이 wildcard라 wire는 가능.
   - 위치 일치는 보장 → Phase 3 매핑에 자동 매칭됨

5. **Phase 2c — ID map rebuild** (`scripts/abrr_rebuild_id_map.py`):
   - 백업 backup_id → live new_id 매핑을 (class, x, y) 기반 자동 매칭
   - GetEnumeratorNameAsString → CallFunction substitution 처리
   - FunctionEntry는 pos=[0,0] (자동 생성 시) vs 백업 [1520,160] 차이 → Pass2에서 유일 클래스 매칭
   - 출력: `Saved/ABRR_id_map.json` (80 엔트리)
   - **부수 문제**: 첫 run 시 FormatText 2개 발생 (`K2Node_FormatText_0` 추가됨 + 두 번째 run 시 새 `K2Node_FormatText_1` 또 추가) → `remove_node` FT_0 → 80 유지

6. **Phase 3 — 86 wire 연결** (`scripts/abrr_phase3_wires.py`):
   - 백업 모든 input pin의 connected_to 순회 → 86개 wire 시도
   - **75 OK**, 11 FAIL:
     - 4건: GetEnumeratorName 입력 핀 `Enumerator` (실제 핀명 `EnumeratorValue` + `Enum` class ref) — wire 안 됨
     - 5건: K2Node_CallFunction_43 (GetCurrentTravelActionResult) 출력 핀이 백업엔 `ReturnValue_*` 5개, 실제론 struct로 묶인 단일 `ReturnValue` (`struct:SBTravelActionResult`) → split 필요
     - 2건: VariableGet의 vector 출력이 백업엔 `_X/_Y/_Z` split, 실제론 단일 `TrjPastAngularVelocity` / `TrjCurrentAngularVelocity` 핀
   - 백업의 핵심 디버그 필드(sset, ip, IsLockOn, FootIK 등)는 모두 OK

7. **Phase 3b — GetCurveValue target 보정** (`scripts/abrr_fix_getcurvevalue.py`):
   - `validate_blueprint`에서 발견된 새 에러: `Get Curve Value` 4개 노드 (eprw/phase/eow/dal)가 SkeletalMeshComponent 함수와 매칭됨 ("이 블루프린트(셀프)는 SkeletalMeshComponent 이지 않으므로 Target 연결 필요")
   - 4개 노드 remove → `add_node(target_class="AnimInstance", function_name="GetCurveValue")` 재생성 → CurveName 핀 default 설정 → FT input wire
   - 모두 success, ID map 갱신

8. **Phase 4 — vac default**: `set_pin_default(FT_1, vac, "-1")` ✅

9. **Phase 5 — compile #1**: errors 0, warnings 0, status=UpToDate ✅
   - 단 한 차례 transient한 UpdateStates ThreadSafe 에러 → 그래프 의존성 재계산 후 사라짐
   - 5/14 메모리 sset 작업의 SBWalk_Sprinting byte 에러도 transient (재컴파일 시 사라짐)

10. **Phase 6 — UpdateValueFromPostEvaluation hook** (`scripts/abrr_phase6_hook.py`):
    - **선택한 패턴**: ExecutionSequence 삽입 (매 틱 보장)
    - 토폴로지: `FunctionEntry → Sequence.execute → {then_0: 기존 IfThenElse_0, then_1: CallFunction(AnimRewindRecorderEmit)}`
    - `disconnect_pins`은 API param 다름 (5/14 8차 메모리에 기록) → connect_pins로 wire 새로 만들면 input 단일 connection 정책에 의해 자동 replace
    - 7노드 (기존 5 + Sequence + AnimRewindRecorderEmit Call)

11. **Phase 7 — compile #2 + save + dump**:
    - compile: errors 0, warnings 0, status=UpToDate ✅
    - `save_asset`: saved=true, was_dirty=true ✅ (P4 lock 없는 로컬 환경)
    - 최종 dump: `Saved/PROBE_AnimRewindRecorderEmit_restored_20260515.json` (80 nodes)

### 최종 상태

- `AnimRewindRecorderEmit` 그래프 80 노드 ✓
- FormatText 1개 (66 arg pins) — 58 wired + vac default `-1` + 7 unwired (rvmci/ifl/rj/dog/hd/pav_z/cav_z)
- FT_1.Result → CF_1.InText (PrintText) + VarSet_0.RewindMonitorLine ✓
- UpdateValueFromPostEvaluation에 hook 매 틱 호출 ✓
- 컴파일/save OK

### 미연결 7개 핀 (split-struct/vector 제약)

| dest_pin | 누락 원인 | 출력될 값 |
|---|---|---|
| rvmci | CF_43.ReturnValue_MatchedConfigIndex split 필요 | wildcard default |
| ifl   | CF_43.ReturnValue_bIsFalling split 필요 | wildcard default |
| rj    | CF_43.ReturnValue_bRequiresJump split 필요 | wildcard default |
| dog   | CF_43.ReturnValue_DiffOnGround split 필요 | wildcard default |
| hd    | CF_43.ReturnValue_HeightDiff split 필요 | wildcard default |
| pav_z | VG_28(TrjPastAngularVelocity) Vector → Z split 필요 | wildcard default |
| cav_z | VG_29(TrjCurrentAngularVelocity) Vector → Z split 필요 | wildcard default |

**4개 enum-name 노드 입력 핀 (CF_32~35의 EnumeratorValue + Enum)**: 자동 wire 실패. 출력은 'None' name 으로 나옴 (백업 string output 대비 약간 다름).

### 사용자 후속 조치 (수동)

1. **PC_01_ABP 에디터 → 미연결 핀 split** (선택사항, 7필드 디버그 부활 필요 시):
   - `K2Node_CallFunction_12` (GetCurrentTravelActionResult): ReturnValue 핀 우클릭 → Split Struct Pin → 자동으로 sub-핀 5개 생성 → FT_1의 rvmci/ifl/rj/dog/hd로 wire (Connect Pin)
   - `K2Node_VariableGet_28` (TrjPastAngularVelocity): ReturnValue 우클릭 → Split → Z 핀 → FT_1.pav_z
   - `K2Node_VariableGet_29` (TrjCurrentAngularVelocity): 동일하게 Z → FT_1.cav_z
2. **enum 이름 출력 보정** (선택사항, ops/mm/rva/wt를 숫자 대신 enum 이름으로 출력하고 싶을 때):
   - `K2Node_CallFunction_32~35` (GetEnumeratorName) 4개 노드의 Enum 핀에 클래스 ref 드롭, EnumeratorValue 핀에 wire (백업 wire map: CF_32 ← VG_32.OverlayPoseState, CF_33 ← CF_12.ReturnValue_ActionType, CF_34 ← VG_26.MovementMode, CF_35 ← CF_17.ReturnValue WriggleMoveType)
3. **UpperBodyBlendWeight 변수 누락 확인**: 부모 SBActorAnimInstance C++ 헤더에 정의돼 있는지 확인. VG_35는 정상 wire 되어 있음 (FT.ubsw OK). 만약 부모에 없으면 ABP에 수동 add.
4. **PIE 진입** → `log LogBlueprintUserMessages all` → `[ANIM_REC]` 라인 출력 확인 (58 필드는 정상값, 7 필드는 default)

### ID 매핑 테이블

- 위치: `C:/Dev/Sanjuk-Unreal/Saved/ABRR_id_map.json` (80 엔트리)
- backup_old_id → current_new_id (Phase 3b로 GetCurveValue 4건 갱신됨)

### 스크립트 (재사용)

| 단계 | 파일 |
|---|---|
| Phase 0 변수 | `scripts/abrr_phase0_variables.py` |
| Phase 1 함수 생성 | 직접 `mcp_call.ps1 add_function` |
| Phase 2 80노드 | `scripts/abrr_phase2_addnodes.py` (한 번만!) |
| Phase 2b enum-name | `scripts/abrr_phase2b_enum_names.py` |
| Phase 2c ID map | `scripts/abrr_rebuild_id_map.py` |
| Phase 3 wire | `scripts/abrr_phase3_wires.py` |
| Phase 3b GetCurveValue | `scripts/abrr_fix_getcurvevalue.py` |
| Phase 6 hook | `scripts/abrr_phase6_hook.py` |
| 검증 | `scripts/verify_restored.ps1`, `scripts/unwired_pins.ps1` |

### 주요 함정 (5/15 학습)

1. **add_variable param 변경**: `variable_name`/`variable_type` → `name`/`type` (5/14 restore_abp_variables.py와 다름 — 최근 Monolith 빌드에서 변경?)
2. **add_function param**: `name` 필수 (`function_name` 아님)
3. **GetEnumeratorNameAsString 직접 add 불가** → `GetEnumeratorName` 함수로 우회 (output type 다름)
4. **GetCurveValue target_class 명시 필수**: 안 주면 SkeletalMeshComponent 버전이 매칭됨 → validate에서 4건 에러
5. **split-struct 핀은 add_node로 불가능**: `connect_pins`에 `ReturnValue_*` 사용 시 핀 미존재 에러. UE 에디터 수동 split만 가능.
6. **스크립트 중복 실행 가드 없음**: idempotent하지 않으므로 중복 추가됨. 재실행 전 반드시 `remove_function` + `add_function` 으로 깨끗하게.
7. **`disconnect_pins` API**: `source_*` 키 아니라 `node_id` + `pin_name`. 그러나 input 단일 connection 정책으로 새 connect_pins가 자동 replace.
8. **UpperBodyBlendWeight 변수 add 실패 (응답 success=true)**: BP 부모 C++ 클래스 변수와 충돌? — 검증 필요.

---

## 2026-05-15 레이아웃 정리 (카테고리 그룹 + 코멘트 박스)

복원 후 80노드가 무질서하게 흩어진 상태였음 (id 재할당 + Monolith add 위치 임의 배치). Wire는 손대지 않고 위치만 재배치 + 카테고리 코멘트 박스 추가.

### 좌표 시스템

- **백본 (좌측, exec 체인)**: FunctionEntry(0,0) → bAnimRewindRecording(220,180) → Branch(520,0) → VariableSet(820,0) → PrintText(1180,280) → FormatText_1(8700,0)
- **카테고리 컬럼**: x = 1600 + 700·n, 첫 노드 y=280, VG 스텝 110px, CF 스텝 140px
- **코멘트 박스**: 각 컬럼 y=200에 배치, `node_ids` 파라미터로 컬럼 노드 자동 enclose

### 10 카테고리 (좌→우)

| # | 이름 | x | 노드수 | 색상 | 코멘트 ID |
|---|------|---|------|------|----------|
| 1 | Frame_Basics | 1600 | 19 | yellow | EdGraphNode_Comment_0 |
| 2 | IK_Foot | 2300 | 5 | orange | EdGraphNode_Comment_1 |
| 3 | Animation | 3000 | 8 | purple | EdGraphNode_Comment_2 |
| 4 | MotionMatching | 3700 | 10 | blue | EdGraphNode_Comment_3 |
| 5 | Thresholds | 4400 | 6 | teal | EdGraphNode_Comment_4 |
| 6 | Phase_Eval | 5100 | 10 | pink | EdGraphNode_Comment_5 |
| 7 | Weight_Curve | 5800 | 5 | brown | EdGraphNode_Comment_6 |
| 8 | Travel | 6500 | 2 | grey | EdGraphNode_Comment_7 |
| 9 | Trajectory | 7200 | 4 | grey | EdGraphNode_Comment_8 |
| 10 | StateMachine | 7900 | 5 | green | EdGraphNode_Comment_9 |

합계 80 노드 + 백본 5 + FT 1 = 86 (백본/FT는 카테고리 외). 코멘트 10개 추가 → 총 90 노드.

### 실행 스크립트

`scripts/layout_anim_rewind_recorder_emit.py` — Monolith `batch_execute`로 80개 `set_node_position` 단일 호출 + 10번의 `add_comment_node` (auto-size).

### 결과

- batch_execute set_node_position 80/80 succeeded, 0 failed
- add_comment_node 10/10 OK
- compile: errors 0 / warnings 0 (status UpToDate)
- save_asset: 실패 (P4 잠금 — 사용자 Ctrl+S 필요)
- 사전 덤프: `Saved/PROBE_AnimRewindRecorderEmit_pre_layout_20260515.json`
- 사후 덤프: `Saved/PROBE_AnimRewindRecorderEmit_clean_layout_20260515.json`

### 함정 / 메모

9. **EdGraphNode_Comment vs K2Node_Comment**: API는 `add_comment_node`지만 dump에는 `EdGraphNode_Comment` 클래스로 나타남.
10. **`node_ids` 인자**: comment box에 노드 enclose 시 자동 padding 50px + auto-size. 수동 width/height 계산 불필요.
11. **batch_execute가 80 ops 단일 호출**: 80번 curl 대비 압도적으로 빠름. `compile_on_complete: false` 권장 (별도 compile 단계로 분리하면 결과 추적 명확).

---

# 2026-05-15 10-FT chain 분할 (카테고리당 FT 1개)

## 무엇

기존 단일 거대 FT (`K2Node_FormatText_1`, 65 wire fan-in)가 그래프 좌→우 전체를 가로지르는 긴 wire를 만들어 가독성을 해쳤다. 카테고리당 FT 1개로 분할하여 **wire 길이 단축 + 컬럼별 self-contained** 구조로 재편.

각 새 FT는 해당 카테고리 컬럼 바로 아래(y=3000)에 배치. source 노드 → 가까운 FT 짧은 wire. FT 간엔 `{prev}` 한 칸씩 chain.

## 분할 사유

- 단일 FT는 65 input pin이라 wire 가시성 매우 낮음 (특히 좌측 컬럼 노드 → 우측 FT 거리)
- 카테고리 컬럼이 이미 정리돼 있지만(2026-05-15 1차 작업), FT 1개에 65 wire 다 들어가서 컬럼 의미가 약화
- chain 형태로 분리하면 변경 영향 범위가 카테고리로 격리됨

## 변경 노드

**제거 1개**:
- `K2Node_FormatText_1` (기존 65 wire FT)

**추가 10개** (모두 `K2Node_FormatText`, 카테고리당 1개, y=3000):

| 카테고리 | 노드 ID | x | 데이터 필드 수 | 비고 |
|---------|--------|---|---------|------|
| FrameBasics | `K2Node_FormatText_2` | 1600 | 15 | `[ANIM_REC]` prefix, prev 없음 |
| IK | `K2Node_FormatText_3` | 2300 | 5 | |
| Animation | `K2Node_FormatText_4` | 3000 | 6 | |
| MotionMatching | `K2Node_FormatText_5` | 3700 | 10 | |
| Thresholds | `K2Node_FormatText_6` | 4400 | 6 | |
| PhaseEval | `K2Node_FormatText_7` | 5100 | 8 | |
| WeightCurve | `K2Node_FormatText_8` | 5800 | 4 | |
| Travel | `K2Node_FormatText_9` | 6500 | 5 (모두 미연결) | wildcard placeholder, split-struct 차후 수동 |
| Trajectory | `K2Node_FormatText_10` | 7200 | 2 (모두 미연결) | wildcard placeholder |
| StateMachine | `K2Node_FormatText_11` | 7900 | 5 | `vac` default `-1`, 나머지 4 wire |

## prev chain (9 wire)

```
FT_2 → FT_3 → FT_4 → FT_5 → FT_6 → FT_7 → FT_8 → FT_9 → FT_10 → FT_11
```

각 FT의 `Result` (text) → 다음 FT의 `prev` (text) 입력. text concat 누적.

## downstream

`FT_11.Result` → PrintText(`K2Node_CallFunction_1`).InText
`FT_11.Result` → VariableSet(`K2Node_VariableSet_0`).RewindMonitorLine

## 명세 vs 실제 source 매핑 차이 (실제 사용)

처방서가 일부 source CallFunction ID를 swap한 형태로 적었으나, **현재 그래프 상태가 ground truth**라 dump에서 추출한 실제 매핑으로 wire를 연결함:

| FT field | 처방 | 실제 사용 |
|---|---|---|
| FT_FrameBasics.as | CallFunction_3 | **CallFunction_2** |
| FT_FrameBasics.ms | CallFunction_2 | **CallFunction_3** |
| FT_Animation.ms_l | CallFunction_7 | **CallFunction_6** |
| FT_Animation.ms_p | CallFunction_6 | **CallFunction_7** |
| FT_MotionMatching.mm | CallFunction_32 | **CallFunction_34** |
| FT_MotionMatching.ops | CallFunction_34 | **CallFunction_32** |
| FT_PhaseEval.phase | CallFunction_36 | **CallFunction_37** |
| FT_PhaseEval.eow | CallFunction_37 | **CallFunction_38** |
| FT_PhaseEval.eprw | CallFunction_38 | **CallFunction_36** |
| FT_PhaseEval.isafb | CallFunction_9 | **CallFunction_11** |
| FT_PhaseEval.isaub | CallFunction_11 | **CallFunction_9** |
| FT_WeightCurve.wt | CallFunction_33 | **CallFunction_35** |
| FT_WeightCurve.rva | CallFunction_35 | **CallFunction_33** |

→ 각 FT의 **필드 이름과 의미는 유지**되었고, source 노드 ID 매핑은 기존 FT_1의 connected_to를 그대로 옮겨와 동작 동일성 100% 보장.

## 실행 결과

- STEP 1: 사전 덤프 OK (`PROBE_AnimRewindRecorderEmit_pre_split_20260515.json`, 90 노드, FT_1 65 input wire 확인)
- STEP 2: add_node × 10 → FT_2~FT_11 (모두 wildcard 핀 자동 생성)
- STEP 3: connect_pins_bulk 58/58 success (FT_9 5개 + FT_10 2개 미연결 = 의도된 wildcard placeholder)
- STEP 3b: FT_11.vac default `-1` set
- STEP 4: prev chain 9/9 success
- STEP 5: compile #1 = 0 errors / 0 warnings / UpToDate
- STEP 6: disconnect 2 + connect 2 → FT_11.Result → PrintText/VarSet
- STEP 7: compile #2 = 0 errors / 0 warnings
- STEP 8: FT_1 remove + compile #3 = 0 errors / 0 warnings
- STEP 9: save_asset success (was_dirty true → saved true)
- 사후 덤프: 99 노드 (예상치 정확히 일치), FT_1 부재, FT_2~FT_11 prev chain·downstream 모두 검증

## 노드 수 변화

| 시점 | 노드 수 | 비고 |
|---|---|---|
| 통합 후 (8차) | 80 | FT_1 + 79 source/backbone |
| 컬럼 정리 + 코멘트 10 (2026-05-15 1차) | 90 | + 10 코멘트 |
| **10-FT chain 분할 (2026-05-15 2차, 본 작업)** | **99** | -1 (FT_1) +10 (FT_2~11) |

## 백업 파일

- `Saved/PROBE_AnimRewindRecorderEmit_pre_split_20260515.json` — 분할 전 (90 노드, 단일 FT_1)
- `Saved/PROBE_AnimRewindRecorderEmit_split10_20260515.json` — 분할 후 (99 노드, FT_2~FT_11 chain)
- `Saved/_connections_step3.json` — STEP 3 source 데이터 wire 정의 (58 connections)
- `Saved/_connections_step4.json` — STEP 4 prev chain 정의 (9 connections)
- `Saved/_connections_step6.json` — STEP 6 downstream swap 정의 (2 connections)

## 사용자 후속 조치 (선택)

1. **FT_9 (Travel), FT_10 (Trajectory) wildcard 필드 wire 연결**: split-struct 필요 (rvmci/ifl/rj/dog/hd/pav_z/cav_z). 현재 placeholder만 출력됨. 필요 시 수동 split.
2. **코멘트 박스 재조정**: 기존 10개 코멘트 박스 (`EdGraphNode_Comment_0~9`)는 y=200대 위쪽 컬럼만 감싸고 있고, 새 FT는 y=3000에 있어 코멘트 외부에 있음. 카테고리당 FT까지 enclose하려면 height 확장 (별도 작업).
3. **P4 submit**: 사용자 본인 로컬 디버깅용이라 submit 안 함.

## 함정 / 메모

12. **add_node 스키마**: `node_type`이 필수 (class 아님), `position`은 `[x,y]` 배열 (object 아님). `FormatText` shortcut OK. `format` param으로 format 문자열 전달 시 `{argname}` 자동으로 wildcard input pin 생성.
13. **set_pin_default**: param 키가 `value` (default_value 아님).
14. **disconnect_pins**: `node_id`/`pin_name`이 source 측. `target_node`/`target_pin`은 optional (단일 connection 끊기 시 사용).
15. **wildcard input pin은 첫 연결 시 type 결정**: 미연결 wildcard는 그대로 wildcard로 유지되며 컴파일은 통과함 (FT 내부에서 string 캐스팅).
16. **input 단일 connection 정책**: PrintText.InText / VarSet.RewindMonitorLine 모두 input single. STEP 6에서 disconnect 했어도 connect만으로도 swap 됐을 가능성 있으나, 명시적 disconnect로 안전성 확보.
17. **connect_pins_bulk 응답 구조**: `connected` (성공 수), `failed` (실패 수), `results` (각 항목 detail). isError=False여도 results 내 `success: false` 있을 수 있어 항상 확인.

---

## 2026-05-15 미연결 자동 복구 (seq / Travel / Trajectory / Enum-name / vac)

10-FT chain 분할 직후 wildcard 필드 + Enum 클래스 미설정 + seq 항상 빈 문자열 문제를 Inspector 처방대로 자동 복구.

### TRACK A: seq Setter 복구 (DrawDebug 그래프)

**원인**: `CurrentSequenceName` 변수는 ABRR 의 source 노드로 wire 돼 있으나 어디서도 Set 되지 않아 매 틱 빈 `""` 출력.

**처방**: DrawDebug 의 `Set Animation` (`K2Node_VariableSet_6`) 직후에 mirror Set 추가.
- 신규 노드: `K2Node_VariableSet_0` (Set CurrentSequenceName) at `[-256, 512]`
- exec splice: `Set Animation.then` → `Set CurrentSequenceName.execute` → `K2Node_IfThenElse_3.execute` (기존 끊고 재배선)
- data wire: `K2Node_CallFunction_7.ReturnValue` (GetDisplayName) → `Set CurrentSequenceName.CurrentSequenceName`

compile #1 결과: 0 new errors (사전 존재하던 CF_32 Enum 에러만 잔존)

### TRACK B: Travel 5필드 split-struct (ABRR)

**원인**: `Get Current Travel Action Result` (`K2Node_CallFunction_12`) 의 `ReturnValue` 가 `SBTravelActionResult` struct. 5 sub-field 가 split 안 돼 FT_9 (rvmci/ifl/rj/dog/hd) 가 빈 값.

**처방**: BreakStruct 노드 추가 → 5 sub-field → FT_9 입력 wire.
- 신규 노드: `K2Node_BreakStruct_1` (Break SBTravel Action Result) at `[8700, 400]`
- 입력 wire: `K2Node_CallFunction_12.ReturnValue` → `K2Node_BreakStruct_1.SBTravelActionResult`
- 출력 wire (5개):
  - `MatchedConfigIndex` → FT_9.rvmci
  - `bIsFalling` → FT_9.ifl
  - `bRequiresJump` → FT_9.rj
  - `DiffOnGround` → FT_9.dog
  - `HeightDiff` → FT_9.hd
- **Bonus**: `ActionType` (byte) 출력은 TRACK D 의 CF_33.EnumeratorValue 입력으로 추가 wire (Travel ActionType enum-name 변환)

API 정정: `add_node(node_type="BreakStruct", struct_type="<StructName>", graph_name=..., position=[x,y])` 정상 작동. 핀 이름은 prefix 없이 sub-field 원본 그대로 (`MatchedConfigIndex`, `bIsFalling`, …). 처방서의 `ReturnValue_` prefix 추정은 부정확.

compile #2 결과: 0 new errors

### TRACK C: Trajectory 2필드 Vector Z (ABRR)

**원인**: `Get TrjPastAngularVelocity` (`K2Node_VariableGet_28`) / `Get TrjCurrentAngularVelocity` (`K2Node_VariableGet_29`) 가 FVector 자체 출력. Z 컴포넌트 split 안 돼 FT_10 (pav_z/cav_z) 빈 값.

**처방 (1차 시도, warning 발생)**: `K2Node_BreakStruct(Vector)` 2개 추가. compile 시 "범용 break 노드 분해 불가" warning 2건.

**처방 (최종, warning 0)**: 위 2개 제거 후 `KismetMathLibrary::BreakVector` CallFunction 노드로 대체.
- `K2Node_CallFunction_10` (Break Vector) at `[9700, 500]`
- `K2Node_CallFunction_14` (Break Vector) at `[9700, 620]`
- wire (4개):
  - VG_28 → CF_10.InVec → CF_10.Z → FT_10.pav_z
  - VG_29 → CF_14.InVec → CF_14.Z → FT_10.cav_z

compile #3 결과: 0 errors / 0 warnings

### TRACK D: Enum-name 4 노드 (CF_32~35, CF_34 재생성 CF_21)

**시도**: 4개 노드의 `Enum` (class ref) 핀에 enum 클래스 경로를 set_pin_default 로 박기 + `EnumeratorValue` (byte) 입력에 변수 GET wire.

**Enum 클래스 발견**:
- `OverlayPoseState` → `/Game/Art/Character/PC/PC_01/OverlaySystem/Data/E_OverlayPose` (UserDefinedEnum, 사용자 추정 `/Script/SB2.E_SBOverlayPoseState` 는 오류 — 실제로는 UserDefinedEnum)
- `MovementMode` → `/Game/Art/Character/PC/PC_01/MotionMatching/Data/E_SBMovementMode` (UserDefinedEnum)
- `WriggleMoveType` → C++ UENUM 추정 (UserDefinedEnum 미발견, `/Script/SB2.E_SBWriggleMoveType` 시도 미검증)
- `Travel ActionType` → C++ UENUM (SBTravelActionResult.ActionType, 위와 동일)

**중요 한계 발견 (메모리 정정)**: `set_pin_default` 는 object pin (UEnum ref) 의 UObject 바인딩을 **resolve 못 함**. `default_value` (string) 만 저장하고 `default_object` (UObject ref) 는 None 유지 → 컴파일 즉시 invalid string default 에러.
- 시도 형식: `/Game/.../E.E`, `Class'/Game/.../E.E'`, `EClassName'/...'`, set_pin_defaults_bulk 의 `default_object` 추가 시도 — 전부 실패
- save_asset 후에도 resolve 안 됨
- 유일한 복구: `remove_node` → `add_node` (새 노드는 default 가 깨끗한 unset 상태)
- 기존에 default_object 가 박혀 있던 노드 (CF_32) 는 다시 set 가능 (string 만 매칭하면 기존 ref 사용)

**실제 결과**:
- CF_32 (OverlayPoseState): 이미 default_object 가 박혀 있어 set 성공. EnumeratorValue 입력 wire 추가.
- CF_33 (Travel ActionType): Enum class 미설정 (사용자 수동 필요). EnumeratorValue 입력은 BreakStruct_1.ActionType 으로 wire.
- CF_34 (MovementMode): set 시도 후 broken → remove + add 로 재생성 = `K2Node_CallFunction_21` at `[4064, 276]`. Enum class 미설정. EnumeratorValue 입력 wire 추가.
- CF_35 (WriggleMoveType): Enum class 미설정. EnumeratorValue 입력 wire 추가.

**신규 VariableGet 노드 3개**:
- `K2Node_VariableGet_48` (Get OverlayPoseState) at `[3880, 460]` → CF_32.EnumeratorValue
- `K2Node_VariableGet_49` (Get MovementMode) at `[3880, 320]` → CF_21.EnumeratorValue
- `K2Node_VariableGet_50` (Get WriggleMoveType) at `[7240, 316]` → CF_35.EnumeratorValue

compile 결과: 0 errors / 0 warnings. **단 CF_21/33/35 는 출력 매 틱 "None"** (Enum class 설정 안 됨)

### TRACK E: vac (ValidAnimFromChooser array length) — 폐기

**시도**: `ValidAnimFromChooser` 변수 VG 를 ABRR 에 추가하려 했으나 pin 0 개 응답 — `ValidAnimFromChooser` 는 `SetStateMachineBlendStackAnim` 함수의 **로컬 변수** 라 다른 그래프에서 접근 불가. copy_nodes 시도해도 동일 한계.

**처방대로 fallback**: 추가한 orphan VG_51 노드 제거. FT_11.vac default `-1` 유지.

### 최종 결과

- compile_blueprint: success / 0 errors / 0 warnings
- validate_blueprint: success (disconnected_nodes 는 무관 — 기존부터 있던 미사용 노드)
- save_asset: success / was_dirty true → saved true
- 노드 수: 99 → 126 (+27, 사용자 직접 + intermediate metadata 포함)
- 신규 functional 노드 7개: BreakStruct_1, CF_10, CF_14, CF_21, VG_48, VG_49, VG_50

### 사용자 후속 조치 (필수)

1. **에디터에서 ABRR 그래프 열기**
2. **CF_21 (MovementMode), CF_33 (Travel ActionType), CF_35 (WriggleMoveType) 의 Enum class 드롭다운에서 enum 클래스 직접 선택**:
   - CF_21: `E_SBMovementMode`
   - CF_33: SBTravelActionResult 의 ActionType enum (`E_SBTravelActionType` 추정, 정확한 명은 BreakStruct_1.ActionType 핀 hover 로 확인)
   - CF_35: WriggleMoveType enum (`E_SBWriggleMoveType` 추정)
3. 컴파일 + 저장 (Ctrl+S, P4 잠금 사용자 수동)
4. PIE 에서 [ANIM_REC] 로그의 `seq=`, `rva=`, `mm=`, `wt=`, `dog=`, `hd=`, `pav_z=`, `cav_z=` 필드가 의미 있는 값 출력되는지 확인

### 백업 파일

- pre: `Saved/PROBE_AnimRewindRecorderEmit_split10_20260515.json` (99 노드)
- post: `Saved/PROBE_AnimRewindRecorderEmit_filled_20260515.json` (126 노드)

### 함정 추가

18. **set_pin_default 는 object pin (UEnum/Class ref) 의 UObject 바인딩 못 함** — string 만 저장됨. 컴파일 시 즉시 에러. 사용자 에디터 수동 작업 필수. (`reference_monolith_animgraph_editing_limits.md` 도 정정)
19. **로컬 변수 cross-graph 접근 불가** — `ValidAnimFromChooser` 같이 함수 로컬로 선언된 변수는 다른 그래프에서 VariableGet 으로 못 불러옴 (pin 0 response).
20. **BreakStruct(Vector) 는 컴파일 warning** — UE5 LWC 환경에서 generic break 노드로 분해 불가. `KismetMathLibrary::BreakVector` CallFunction 사용 권장.
21. **add_node(BreakStruct) 패턴 검증** — `struct_type="<Name>"` 으로 generic struct break 정상 작동. `SBTravelActionResult` 등 모든 sub-field 가 pin 으로 노출됨. (메모리 정정: 이전엔 한계로 기록됐으나 실제 가능)

