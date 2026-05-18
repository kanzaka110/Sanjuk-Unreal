# Unreal Engine 5.7 Blueprint Context

## MCP Operations — blueprint_modify

All operations require `blueprint_path` param. Routed via `unreal_ue` domain `"blueprint"`.

### Query Operations
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `get_info` | | Blueprint overview (parent class, variables, functions, graphs) |
| `get_nodes` | `graph_name`, `summary:true` | Get nodes in a graph with pin/connection details |
| `get_component_defaults` | `component_name` | Get default property values of a component |
| `compile` | | Compile the blueprint |

### Structure Operations
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `create` | `package_path`, `blueprint_name`, `parent_class` | Create new blueprint asset |
| `add_variable` | `variable_name`, `variable_type` | Add member variable |
| `remove_variable` | `variable_name` | Remove member variable |
| `add_function` | `function_name` | Create new function graph |
| `remove_function` | `function_name` | Delete function graph |
| `add_component` | `component_name`, `component_class`, `attach_to_root` | Add component |
| `add_components` | `components:[{name,class,defaults?}]` | Batch add multiple components (with optional defaults) |
| `remove_component` | `component_name` | Remove component |
| `set_component_defaults` | `component_name`, property key-values | Set component default values |
| `clone_component` | `source_component`, `new_name`, `overrides?:{...}` | Clone component with all properties, apply overrides |

### Node Operations
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `add_node` | `node_type`, `node_params`, `graph_name`, `pos_x`, `pos_y` | Add single node |
| `add_nodes` | `nodes:[]`, `connections:[]` | Batch add nodes with connections |
| `delete_node` | `node_id` | Remove a node (alias: `remove_node`) |
| `delete_nodes` | `node_ids:[]` or `delete_all:true` | Batch remove nodes (alias: `remove_nodes`) |

### Wiring Operations
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `connect_pins` | `source_node_id`, `source_pin`, `target_node_id`, `target_pin` | Wire two pins (alias: `connect_nodes`) |
| `connect_pins` (batch) | `connections:[{source_node_id, source_pin, target_node_id, target_pin}]` | Wire multiple pins at once |
| `disconnect_pins` | `source_node_id`, `source_pin`, `target_node_id`, `target_pin` | Break connection (alias: `disconnect_pin`) |
| `set_pin_value` | `node_id`, `pin_name`, `pin_value` | Set default value (alias: `set_default`) |

### Batch Operation
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `batch_modify` | `operations:[{operation,...params}]`, `compile_after:true` | Multiple ops in single compile |

---

## MCP Operations — blueprint_query (Simple Tool: `unreal_blueprint_query`)

| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `list` | `path_filter`, `type_filter`, `name_filter`, `limit` | List blueprints with filters |
| `inspect` | `blueprint_path`, `include_variables`, `include_functions`, `include_graphs` | Detailed blueprint info |
| `get_graph` | `blueprint_path`, `graph_name`, `is_function_graph` | Graph structure overview |
| `get_nodes` | `blueprint_path`, `graph_name`, `include_connections` | Full node/pin/connection details |

---

## add_nodes 실전 패턴

### 노드 정의 형식

nodes 배열의 각 항목:
| Field | Type | Description |
|-------|------|-------------|
| `type` | string | 노드 클래스명 (필수) |
| `params` | object | 노드별 파라미터 (또는 최상위에 `function`/`variable` 직접 기술 가능) |
| `pos_x`, `pos_y` | int | 그래프 내 위치 (선택) |
| `pin_values` | object | 핀 기본값 `{pin_name: "value"}` (선택) |

### 노드 타입별 params 패턴

| type | params | 예시 |
|------|--------|------|
| `K2Node_CallFunction` | `{function: "/Script/Module.Class:FunctionName"}` | `"/Script/Engine.KismetMathLibrary:Multiply_FloatFloat"` |
| `K2Node_VariableGet` | `{variable: "MyVar"}` | 멤버 변수 읽기 |
| `K2Node_VariableSet` | `{variable: "MyVar"}` | 멤버 변수 쓰기 |
| `K2Node_CallFunction` | `{function: "/Script/Engine.KismetMathLibrary:MakeVector"}` | FVector 생성 |
| `K2Node_CallFunction` | `{function: "/Script/Engine.KismetMathLibrary:BreakVector"}` | FVector 분해 |
| `K2Node_IfThenElse` | `{}` | Branch 노드 |
| `K2Node_MakeStruct` | `{struct: "/Script/CoreUObject.Vector"}` | 구조체 생성 |

### connections 형식

| Field | Type | Description |
|-------|------|-------------|
| `from_node` | int or string | nodes 배열의 **0-based 인덱스** 또는 기존 노드의 node_id |
| `to_node` | int or string | 동일 |
| `from_pin` | string | 소스 핀 이름 (정확한 문자열 필수) |
| `to_pin` | string | 타겟 핀 이름 |

실행 핀 예시: `from_pin: "then"`, `to_pin: "execute"`

### 구조체 핀 주의사항 (중요!)

구조체 핀(FVector, FRotator 등)은 **분할(split) 불가** — `SetRelativeLocation`의 `NewLocation` 핀에 X/Y/Z 개별 연결 안 됨.

**해결법**: `MakeVector` 노드를 명시적으로 추가하고 연결:
```
nodes: [
  {type: "K2Node_CallFunction", params: {function: "/Script/Engine.KismetMathLibrary:MakeVector"}},
  {type: "K2Node_CallFunction", params: {function: "/Script/Engine.SceneComponent:K2_SetRelativeLocation"}}
]
connections: [
  {from_node: 0, from_pin: "ReturnValue", to_node: 1, to_pin: "NewLocation"}
]
```
이후 MakeVector의 X/Y/Z 핀에 값 또는 다른 노드를 연결.

### add_nodes 응답

```json
{
  "node_count": 3,
  "node_ids": ["ID_0", "ID_1", "ID_2"],
  "node_map": {"0": "ID_0", "1": "ID_1", "2": "ID_2"}
}
```
`node_map`으로 입력 인덱스와 생성된 ID를 직접 매핑 가능 — 후속 `connect_pins`에 활용.

---

## batch_modify 실전 패턴

blueprint 도메인의 `batch_modify`로 여러 작업을 한 호출에 묶어 실행:

```json
{
  "domain": "blueprint",
  "operation": "batch_modify",
  "params": {
    "blueprint_path": "/Game/BP_Example",
    "operations": [
      {"operation": "add_components", "components": [
        {"name": "MyCable", "class": "/Script/CableComponent.CableComponent",
         "defaults": {"CableLength": 500, "CableWidth": 5}}
      ]},
      {"operation": "set_component_defaults", "component_name": "MyCable",
       "CableLength": 800},
      {"operation": "add_nodes", "graph_name": "UserConstructionScript",
       "is_function_graph": true,
       "nodes": [...], "connections": [...]},
      {"operation": "compile"}
    ],
    "compile_after": true
  }
}
```

- add_components + set_component_defaults + add_nodes + compile을 **한 호출로 통합**
- 개별 호출 20~30회 → 1~3회로 축소

---

## unreal_batch — LLM ↔ MCP 라운드트립 최소화

`unreal_batch` 도구로 여러 MCP 도구 호출을 시퀀스로 묶어 한 번에 실행:

```json
{
  "steps": [
    {"tool": "unreal_blueprint_query", "args": {
      "operation": "inspect", "blueprint_path": "/Game/BP_Example",
      "include_variables": true, "include_graphs": true}},
    {"tool": "unreal_ue", "args": {
      "domain": "blueprint", "operation": "batch_modify",
      "params": {"blueprint_path": "/Game/BP_Example", "operations": [
        {"operation": "add_components", "components": [...]},
        {"operation": "add_nodes", "graph_name": "UserConstructionScript",
         "is_function_graph": true, "nodes": [...], "connections": [...]},
        {"operation": "compile"}
      ]}}
    }
  ]
}
```

- `$prev[0].result` 등으로 이전 스텝 결과 참조 가능
- `continue_on_error: true`로 일부 실패해도 나머지 진행
- 조회 → 수정 → 컴파일을 **1 라운드트립**으로 완료

---

## Key Reference

### UK2Node Hierarchy
```
UK2Node
├── UK2Node_CallFunction      — Function calls
├── UK2Node_VariableGet/Set   — Variable access
├── UK2Node_Event             — Events (BeginPlay, Tick)
├── UK2Node_IfThenElse        — Branch node
├── UK2Node_MacroInstance     — Macro usage
└── UK2Node_FunctionEntry     — Function entry point
```

### Pin Type Categories (PC_*)
| Category | C++ Type | Category | C++ Type |
|----------|----------|----------|----------|
| `PC_Exec` | N/A (execution) | `PC_Boolean` | bool |
| `PC_Int` | int32 | `PC_Int64` | int64 |
| `PC_Real` | float/double | `PC_Byte` | uint8 |
| `PC_String` | FString | `PC_Name` | FName |
| `PC_Text` | FText | `PC_Object` | UObject* |
| `PC_Class` | UClass* | `PC_Struct` | UScriptStruct* |
| `PC_SoftObject` | TSoftObjectPtr | `PC_SoftClass` | TSoftClassPtr |
| `PC_Enum` | UEnum* | `PC_Wildcard` | varies |

### Graph Types
- **EventGraph** — Main execution graph
- **ConstructionScript** — Actor construction (use `graph_name: "UserConstructionScript"`, `is_function_graph: true`)
- **Function graphs** — User-defined functions (use `is_function_graph:true`)
