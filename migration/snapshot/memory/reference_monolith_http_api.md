---
name: Monolith HTTP JSON-RPC API 직접 호출 (MCP 툴 미노출 세션 폴백)
description: Claude 세션에 Monolith MCP 툴이 노출되지 않을 때 curl로 localhost:9316/mcp JSON-RPC 직접 호출해 blueprint_query 등 15개 도메인 툴 사용하는 방법.
type: reference
originSessionId: 6c06914e-adfc-4bcc-a415-ef22659354ec
---
## 엔드포인트

- URL: `http://localhost:9316/mcp` (POST, JSON-RPC 2.0)
- Health: `http://localhost:9316/health` (GET)
- v0.12.1 기준 **15개 top-level 툴** (tools/list), **blueprint만 88 actions**

## 패턴

```bash
curl -s -X POST http://localhost:9316/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":1,
       "params":{"name":"blueprint_query",
                 "arguments":{"action":"<action>",
                              "params":{...}}}}'
```

## 확인된 param 키 (중요 — schema 추정과 다름)

| action | 필수 param |
|--------|-----------|
| `get_blueprint_info` | `asset_path` (blueprint_path 아님) |
| `add_variable` | `asset_path`, `name` (variable_name 아님), `type` (variable_type 아님), `category`, `default_value` |
| `add_node` | `asset_path`, `graph_name`, `node_type`, (VariableGet 시) `variable_name`, `position` |
| `remove_node` | `asset_path`, `graph_name`, `node_id` |
| `search_nodes` | `asset_path`, `graph_name`, `query` |
| `get_node_details` | `asset_path`, `graph_name`, `node_id` |
| `connect_pins` | `source_node`, `source_pin`, `target_node`, `target_pin` (+ graph_name) |
| `disconnect_pins` | 동일 |
| `set_pin_default` | `node_id`, `pin_name`, **`value`** (default_value 아님) |
| `add_function` | `name` |
| `set_function_params` | `function_name`, `inputs`: [{name,type}] |
| `add_node` (BreakStruct/MakeStruct) | **`struct_type`** (struct_name 아님) |
| `add_node` (CallFunction) | `function_name`, 모호 시 `function_class` — 단 **Monolith가 function_class 무시하는 경우 있음** (예: GetMesh → PersonaToolMenuContext 잘못 선택) |

## 주요 함정 (2026-04-15 세션 발견)

1. **Vector MakeStruct/BreakStruct는 컴파일 에러**: "구조체는 BlueprintType 이 아닙니다"
   → CallFunction `MakeVector` / `BreakVector` (KismetMathLibrary) 사용. BreakVector 입력 핀은 `InVec`, MakeVector 출력은 `ReturnValue`
2. **GetMesh 함수 모호**: 단순 `function_name=GetMesh`는 PersonaToolMenuContext로 해석됨 → **`VariableGet` with `variable_name=Mesh`** 로 Component 레퍼런스 획득
3. **Sequence then_N 핀 자동 생성 안 됨**: `connect_pins`로 존재하지 않는 `then_3` 지정 시 "pin not found" 에러 → 기존 `then_N → existing_target` 사이에 삽입하는 방식으로 우회
4. **UE 5.0+ float ↔ double**: 변수 type=`float`이어도 산술 노드는 `Subtract_DoubleDouble`/`Add_DoubleDouble` 사용. 자동 coercion 동작

## monolith_discover로 스키마 얻기

```json
{"name":"monolith_discover","arguments":{"domain":"blueprint","action":"add_nodes_bulk"}}
```
→ 하지만 도메인 개요만 나올 때가 많음. 오류 메시지("Missing required param(s): [...]")로 파라미터 이름 역추적이 더 빠를 때가 있음.

## 노드 그래프 대규모 수정 시 주의

- 29 노드 + 40 연결 규모는 HTTP로 순차 생성 시 중간 실패 위험
- `add_nodes_bulk` / `connect_pins_bulk` / `batch_execute` 우선 시도
- 실패 시 생성된 노드 추적해 `remove_node` 롤백 준비

## BP 노드 편집 검증됨 (2026-04-24 세션 PC_01_ABP)

Animation Blueprint의 함수 그래프 (UpdateVariables, BlueprintThreadSafeUpdateAnimation 등)에서 직접 노드 추가/연결/수정 가능:

### node_type 값 (검증됨)
- `VariableGet` / `VariableSet` — `variable_name` 필수
- `CallFunction` — `function_name` + 선택적 `function_class`
- `Branch` — K2Node_IfThenElse 생성
- `Sequence` — K2Node_ExecutionSequence (then_0, then_1, ...)

### 검증된 function_name 예시
- `Abs` (KismetMathLibrary) — "Absolute (Float)"
- `Greater_DoubleDouble` — "float > float"
- `NotEqual_BoolBool` — "Not Equal (Boolean)"
- `SelectFloat` — "Select Float"
- `SetStateMachineBlendStackAnim` — SB2 ABP 내부 함수 (self, bForceBlend, StateMachineState 3 param)

### 편집 흐름 (검증 시나리오)
1. `add_variable` — 변수 먼저 만들고
2. `add_node` × N — 노드 배치
3. `connect_pins` × N — value/execution 연결
4. `set_pin_default` — 리터럴 값 (enum string, float default)
5. `compile_blueprint` — 에러 0이면 성공
6. `save_asset` — **P4 체크아웃 이슈로 자주 실패** → 사용자가 에디터에서 Ctrl+S 수동 저장

### 연결 수정 (노드 삭제 대신)
- 잘못 연결된 핀은 `disconnect_pins` + `connect_pins`로 재배선이 가장 안전
- `disconnect_pins` param: `node_id`, `pin_name` (한 쌍, 해당 핀의 모든 연결 끊김)

### Chooser Table은 BP 편집 범위 밖
- `/Script/Chooser.ChooserTable` 에셋은 `ResultsStructs` protected
- Monolith로 Chooser Row/Column 편집 액션 **없음**
- 에디터에서 수동 편집 or Python 스크립트로 구조 덤프만 가능

## How to apply

- MCP 툴이 세션에 `mcp__monolith__*` 형태로 없어도 Bash + curl로 Monolith 완전 제어 가능
- 대규모 그래프 편집은 C++ 또는 BP Macro 수동 작성을 우선 제안 (안전성 이유)
