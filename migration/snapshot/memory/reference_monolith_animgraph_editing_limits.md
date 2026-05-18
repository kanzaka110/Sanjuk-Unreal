---
name: Monolith ABP/AnimGraph 편집 한계
description: Monolith blueprint_query write 액션의 함정 — node_type 명명, save 실패, fallback mode, State Machine sub-graph 미접근.
type: reference
originSessionId: 000356af-f6ab-4220-891c-ca3825b31e2a
---
## add_node 핵심: prefix 없이 사용해야 정상 function ref
```
WRONG: node_type="K2Node_CallFunction" + function_name="Not_PreBool"
       → fallback mode (function="None", pins 없음)

CORRECT: node_type="CallFunction" + function_name="Not_PreBool" + function_class="/Script/Engine.KismetMathLibrary"
        → 정상 (function="Not_PreBool", pins 정상)
```

지원되는 공식 node_type (prefix 없음):
`CallFunction, VariableGet, VariableSet, CustomEvent, Branch, Sequence, MacroInstance, SpawnActorFromClass, DynamicCast, Self, Return, MakeStruct, BreakStruct, SwitchOnEnum, SwitchOnInt, SwitchOnString, FormatText, MakeArray, Select`

그 외 K2Node_* 는 fallback (pins 없거나 부족 → 사용 불가). 예: `K2Node_EvaluateChooser2`, `K2Node_PromotableOperator` 등.

## save_asset이 P4 환경에서 자주 실패
- `save_asset` 응답: `Failed to save asset` (구체 이유 없음)
- 컴파일은 성공해도 디스크 push 실패 가능
- **사용자 환경(SB2)에선 실제로는 디스크에 적용된 적도 있음** — 응답이 Failed여도 실제 파일 modified time은 변경됨
- 해결: 사용자가 에디터에서 Ctrl+S 강제 저장 + P4 Check Out 확인

## Chooser ResultsStructs는 protected
```
get_editor_property("ResultsStructs") → "Property is protected and cannot be read"
```
- Columns/Rows 메타정보는 dump 가능 (`get_editor_property("ColumnsStructs")`)
- 결과 시퀀스 매핑은 직접 접근 불가
- 우회 1: ChooserTable의 .uasset binary 스캔 또는 Python `unreal` 모듈
- **우회 2 (2026-04-29 검증)**: Monolith `blueprint_query.get_cdo_properties` 로 메타 dump 가능 — array 길이 + DisabledRows + NestedChoosers + NestedObjects + ColumnsStructs 노출. 단 ResultsStructs InstancedStruct 내용물 (시퀀스 ref / output struct) 은 빈 `{}` 직렬화. 즉 컬럼 binding/RowValues 와 row count + disabled 패턴까지는 dump, **셀별 enum 값과 결과 시퀀스 매핑은 여전히 protected**.
- 보강 우회 절차 (3중 결합):
  1. Python `get_editor_property("ColumnsStructs").export_text()` → 컬럼 binding/RowValues
  2. Monolith `get_cdo_properties` → row 메타 + nested 토폴로지
  3. uasset binary scan → 시퀀스 경로 추출 (단 row 매핑은 추정)
- 셀 값 + 시퀀스 ↔ row 정확 매핑이 필요하면 **에디터 수동 inspect** 필수

## State Machine sub-graph 접근 불가
- `list_graphs`는 ABP 최상위 그래프만 반환
- State Machine 안의 transition rules, sub-state graphs는 미노출
- transition rule 작성은 사용자가 에디터에서 직접 작업
- conduit/sub-state 구조 변경도 마찬가지

## set_pin_default 후 컴파일 시 default 값 reset 가능성
- `K2Node_PromotableOperator`의 wildcard pin은 type promotion 시 default reset
- ABP가 reload되면 우리 변경이 사라질 수 있음
- 변경 후 즉시 재dump해서 확인 권장

## Hysteresis edge → SetStateMachineBlendStackAnim 호출 메커니즘 무력화 위험
- ABP에 일반적으로 있는 패턴: `NotEqual(Var, PrevVar)` → IfThenElse → Set...
- 이 분기를 끊으면 state 머무는 동안 변수 변화가 BlendStack에 반영 안 됨
- 단 Stop 씹힘 같은 부작용도 막아주는 역할이라 trade-off

## 한계 종합
Monolith로 가능한 것:
- 단순 노드 추가/삭제/연결
- 공식 node_type만 정상 작동
- 변수 default 변경 (단 reset 위험)

Monolith로 어려운 것:
- ChooserResultsStructs 변경
- State Machine transition rule 작성
- AnimGraph 노드 detail (Property Binding 등) 설정
- P4 잠금 환경에서 안정적 save
- `K2Node_EvaluateChooser2` 등 특수 노드의 chooser asset 지정

## 2026-05-12 추가: 함수 metadata (BlueprintThreadSafe 등) 설정 액션 없음
- AnimBlueprint의 thread-safe graph (UpdateStates 등) 에서 호출하려면 호출되는 함수에 **BlueprintThreadSafe** 메타데이터 필요
- Monolith `add_function` / `set_function_params` 둘 다 metadata 미지원 (param schema에 없음)
- `set_cdo_property` 는 CDO 인스턴스 default 값용, 함수 metadata에 적용 안 됨
- 결과적으로 신규 함수가 thread-safe 그래프에서 호출되어야 하면 **사용자가 에디터에서 함수 선택 후 Details 패널의 "Thread Safe" 체크박스 수동 체크** 필수
- 그렇지 않으면 컴파일 에러: `<함수> 스레드 세이프 그래프 <호출그래프> 에서 호출된 스레드 세이프 방식이 아닌 함수`

## 2026-05-12 추가: K2Node_EnumEquality 와 함수 입력 byte 핀 비호환
- `K2Node_EnumEquality` 의 wildcard A/B pin은 **enum 변수 GET** 으로만 promote (그 후 같은 enum byte 변수 연결 OK)
- 함수 입력 핀 (`K2Node_FunctionEntry` output) 의 byte 는 enum 으로 promote 안 됨 → "열거형 동등 연산자는 열거형 이외에는 사용할 수 없습니다" 에러
- **우회**: `KismetMathLibrary::EqualEqual_ByteByte` CallFunction 노드 사용 (byte-byte 직접 비교)

## 2026-05-12 추가: set_function_params 는 기존 파라미터 덮어쓰지 않고 추가만 함
- 함수 입력 타입을 바꾸려고 `set_function_params(inputs=[{...same name, new type}])` 호출하면 **NewStance + NewStance1 두 개** 가 생김
- 안전한 절차: `remove_function` → `add_function` → `set_function_params` 로 처음부터 재생성

## 2026-05-12 추가: 변수 add 시 'real' 타입 거부
- ABP의 기존 변수 type 이 `"real"` 로 보이지만 (UE 5 LWC), `add_variable` 의 type 파라미터에는 **`double`** 사용 (그러면 result 도 type=double 로 표시)
- 유효 타입: `bool, byte, int, int64, float, double, string, text, name, Vector, Rotator, Transform, LinearColor`. enum은 `enum:<Name>`, struct은 `struct:<Name>`, object는 `object:<Class>`.
- enum 변수의 default 값으로 enum name 문자열 (`"CharacterStance_Peaceful"`) 설정은 type이 `enum:E...` 일 때만 됨. type=byte 면 정수만 받음.

## 2026-05-12 추가: Array_Contains (wildcard polymorphism 함수) add_node 불가
- KismetArrayLibrary 의 `Array_Contains` / `Array_Find` / `Array_Add` 등은 메타데이터 `ArrayParm=TargetArray, ArrayTypeDependentParams=ItemToFind` 로 wildcard 타입을 가짐
- 에디터에서 만들면 `K2Node_CallArrayFunction` 클래스가 사용돼 polymorphism 처리 (TargetArray 연결 시 ItemToFind/ReturnValue 타입 자동 resolve)
- **Monolith `add_node(node_type=CallFunction, function_name=Array_Contains)` 는 일반 `K2Node_CallFunction` 클래스로 만듦** → wildcard pin (`array:wildcard`/`wildcard`) 그대로 → connect_pins 로 array:name 연결해도 resolve 안 됨 → 컴파일 시 "타입이 결정되지 않았습니다" 7개 에러
- 우회 시도 (실패):
  - `resolve_node` 액션은 add_node 별칭이라 wildcard 해결 불가
  - `copy_nodes` 로 기존 K2Node_CallArrayFunction 노드 복제 시 **동일 pin GUID 재사용** → 원본의 외부 연결을 복제본에 강탈하고, 복제본 제거 시 원본 연결까지 사라짐 (양방향 손상)
- **결론**: Array polymorphism 함수가 필요한 작업은 **사용자가 에디터에서 직접** Tags 변수 핀을 그래프로 드래그-아웃 후 "Get a copy" / "Contains" 메뉴 선택하거나, 기존 동급 노드를 Ctrl+W 로 복제 후 default 변경하는 방식 사용

## 2026-05-11 추가: project_query.find_references는 PSD 등록 detection 못 함
- `find_references(AnimSequence)` 응답에 `referenced_by`가 비어도 PSD에 등록돼 있을 수 있음
- 실측 예: `P_Player_Run_Start_F_Lfoot_Evade`는 `referenced_by:[]`인데 `PSD_GroundMovingTransit` idx 192에 정상 등록 (sampling 0~0.128초)
- 즉 "PSD orphan 판정"은 find_references만으로 결정 금지
- 정확한 확인: `animation_query.get_pose_search_database`로 모든 PSD의 sequences 목록을 직접 grep
- Stop / Pivot orphan 판정도 같은 false negative 가능성 — 메모리 `project_pc01_mm_pipeline.md`의 "Stop PSD 미등록" 주장도 재검증 필요

## 2026-05-13 추가: Cross-graph 노드 ID 충돌 시 컴파일 후 노드 소실
- 같은 BP에서 **그래프 A에서 add_node** 후 **그래프 B에 add_node** 했을 때, B에서 받은 노드 ID가 A의 노드 ID와 겹치면 → A 또는 B의 노드가 컴파일 후 사라짐 (silent removal)
- 실측: PC_01_ABP에서 IsPivoting 그래프에 `K2Node_CallFunction_3` 추가 후, UpdateStates 그래프에 `K2Node_CallFunction_4`, `_5` 추가했더니 IsPivoting의 `_4`, `_5` 가 컴파일 후 사라짐
- compile_blueprint는 errors=0 로 성공 보고하지만 dump 시 노드 미존재
- **우회**: 한 그래프 작업 후 컴파일 + dump 검증 → 사라진 노드 있으면 **재추가** (이때는 새 ID 부여받음). 또는 단일 트랜잭션처럼 한 작업 단위 끝나기 전까지는 다른 그래프 노드 추가 자제.
- 영향: 여러 그래프 동시 편집은 위험. 그래프 단위 atomic 작업 권장.

## 2026-05-15 추가: BreakStruct add_node 정정 — split-struct API 가능
- 이전 메모: "AnimGraph 노드 detail 설정 불가" 한도 안에서 BreakStruct도 막힌 듯 기록됐으나 **정정**
- 검증: `add_node(node_type="BreakStruct", struct_type="SBTravelActionResult", graph_name=..., position=[x,y])` 정상 작동
- 응답: 모든 sub-field가 pin 으로 노출 (`MatchedConfigIndex`/`bIsFalling`/…). prefix 없는 깨끗한 pin 이름 (메모리에서 "ReturnValue_" 추정했던 prefix 는 없음)
- 같은 패턴으로 Vector / Rotator / 등 standard struct 도 OK. 단 **K2Node_BreakStruct 로 만든 Vector 는 컴파일 warning** ("범용 break 노드로 분해할 수 없습니다") → `KismetMathLibrary::BreakVector` CallFunction 사용 권장
- struct_type 값: 정식 struct 이름 (네임스페이스 없이 `Vector`, `SBTravelActionResult` 등)

## 2026-05-15 추가: set_pin_default 는 object pin (UEnum/Class ref) 의 UObject 바인딩 불가
- `K2Node_CallFunction::GetEnumeratorName` 의 `Enum` pin (type `object:Enum`) 에 enum 클래스를 string 으로 set_pin_default 하면:
  - `default_value` (string) 만 set 됨
  - `default_object` (UObject ref) 는 **resolve 안 됨**
  - 컴파일 시 즉시 에러: `"String NewDefaultValue '...' specified on object pin 'Enum'"`
- 시도한 format 모두 실패: `/Game/.../E.E`, `/Script/Mod.E`, `Enum'/Game/.../E.E'`, `EClass'/...'`
- set_pin_defaults_bulk 의 `default_object` 파라미터도 무시됨 (서버 응답 success 인데 실제 set 안 됨)
- save_asset 후에도 resolve 안 됨 (string-only 상태 그대로 저장)
- **유일한 경로**: 사용자가 에디터에서 노드 drop-down 으로 enum 클래스 선택 (수동) — 한 번 resolve 되면 그 후 dump 의 `default_object` 필드에 UObject ref 가 박힘. 그 상태에서 set_pin_default 로 같은 값 다시 set 해도 OK
- 단 한 번 잘못 set 한 string 은 pin 을 "broken" 상태로 만듦 — 빈 값으로 reset 안 됨 (`""` 거부, `"None"` 도 invalid). **유일한 복구**: `remove_node` → `add_node` 로 새로 만들기 (이때 default 가 깨끗한 unset 상태로 출발)
- 패턴: enum class 가 이미 resolve 된 기존 노드는 동작, 새로 만든 enum-name 노드는 사용자 수동 작업 필수

## How to apply
- ABP 변경 시 add_node에 `CallFunction`/`VariableGet` 등 prefix 없는 공식 type 사용
- save 실패해도 사용자가 수동 save하면 적용될 수 있으니 응답만 보고 포기하지 말 것
- State Machine 편집은 사용자에게 가이드 (단계별 UI 작업)
- 변경 후 즉시 재dump로 검증 (reset 위험)
- BreakStruct 는 generic API 로 add 가능. Vector 는 BreakVector 함수 권장
- enum-name 노드의 Enum class ref 는 API 로 set 불가 — 사용자 에디터 수동 작업
- 잘못된 enum ref 박힌 노드는 reset 안 됨 → remove + add 로 재시작
