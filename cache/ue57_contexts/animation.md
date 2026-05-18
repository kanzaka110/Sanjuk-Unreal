# Unreal Engine 5.7 Animation Blueprint Context

## MCP Operations — anim_blueprint_modify

All operations require `blueprint_path` param. Routed via `unreal_ue` domain `"anim"`.

### Query Operations
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `get_info` | | AnimBlueprint overview (state machines, variables, skeleton) |
| `get_state_machine` | `state_machine` | Detailed state machine info (states, transitions) |
| `get_state_machine_diagram` | `state_machine` | ASCII visualization + enhanced JSON |
| `validate_blueprint` | | Compile errors and diagnostics |
| `find_animations` | `search_pattern`, `asset_type` | Search compatible animation assets |

### State Machine Operations
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `create_state_machine` | `state_machine` (name) | Create new state machine in AnimGraph |
| `add_state` | `state_machine`, `state_name`, `is_entry_state`, `position:{x,y}` | Add state |
| `remove_state` | `state_machine`, `state_name` | Remove state |
| `set_entry_state` | `state_machine`, `state_name` | Set entry state |
| `set_state_animation` | `state_machine`, `state_name`, `animation_type`, `animation_path`, `parameter_bindings` | Assign animation (sequence/blendspace/blendspace1d/montage) |

### Transition Operations
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `add_transition` | `state_machine`, `from_state`, `to_state` | Create transition |
| `remove_transition` | `state_machine`, `from_state`, `to_state` | Remove transition |
| `set_transition_duration` | `state_machine`, `from_state`, `to_state`, `duration` | Set blend duration |
| `set_transition_priority` | `state_machine`, `from_state`, `to_state`, `priority` | Set priority order |

### Condition Graph Operations
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `add_condition_node` | `state_machine`, `from_state`, `to_state`, `node_type`, `node_params`, `position` | Add logic node |
| `delete_condition_node` | `state_machine`, `from_state`, `to_state`, `node_id` | Remove node |
| `connect_condition_nodes` | `source_node_id`, `source_pin`, `target_node_id`, `target_pin` | Wire condition nodes |
| `connect_to_result` | `state_machine`, `from_state`, `to_state`, `source_node_id`, `source_pin` | Connect to transition result |
| `add_comparison_chain` | `state_machine`, `from_state`, `to_state`, `variable_name`, `comparison_type`, `compare_value` | Create variable→comparison→result chain (shortcut) |
| `setup_transition_conditions` | `state_machine`, `rules:[...]` | Bulk setup conditions for multiple transitions |

### Inspection Operations
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `get_transition_nodes` | `state_machine`, `from_state`, `to_state` | List nodes in transition graph with pins |
| `inspect_node_pins` | `node_id` | Get detailed pin info for a node |
| `set_pin_default_value` | `node_id`, `pin_name`, `pin_value` | Set pin value with type validation |

### Connection & Batch
| Operation | Key Params | Description |
|-----------|-----------|-------------|
| `connect_state_machine_to_output` | `state_machine` | Connect State Machine to AnimGraph Output Pose |
| `batch` | `operations:[{operation,...params}]` | Execute multiple operations atomically |

---

## Key Reference

### Condition Node Types
`TimeRemaining`, `Greater`, `Less`, `GreaterEqual`, `LessEqual`, `Equal`, `NotEqual`, `And`, `Or`, `Not`, `GetVariable`

### Comparison Functions (for transition rules)
- **Float**: `Greater_FloatFloat`, `Less_FloatFloat`, `GreaterEqual_FloatFloat`, `LessEqual_FloatFloat`
- **Int**: `Greater_IntInt`, `Less_IntInt`
- **Bool**: `EqualEqual_BoolBool`, `NotEqual_BoolBool`

Pin type matching: `PC_Real` → `*_FloatFloat`, `PC_Int` → `*_IntInt`, `PC_Boolean` → `*_BoolBool`

### Animation Types for set_state_animation
| animation_type | Asset Type | parameter_bindings |
|---------------|------------|-------------------|
| `sequence` | UAnimSequence | Not needed |
| `blendspace` | UBlendSpace (2D) | `{"Speed":"Speed","Direction":"Direction"}` |
| `blendspace1d` | UBlendSpace1D | `{"Speed":"Speed"}` |
| `montage` | UAnimMontage | Not needed |
