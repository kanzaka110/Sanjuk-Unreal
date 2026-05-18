# Enhanced Input MCP Tools Reference

Domain: `enhanced_input` (via `unreal_ue` router)

## Operations

| Operation | Required Params | Optional Params |
|-----------|----------------|-----------------|
| `create_input_action` | action_name | package_path, value_type |
| `create_mapping_context` | context_name | package_path |
| `add_mapping` | context_path, action_path, key | — |
| `remove_mapping` | context_path, mapping_index | — |
| `add_trigger` | context_path, mapping_index, trigger_type | hold_time, tap_release_time, pulse_interval, chord_action_path |
| `add_modifier` | context_path, mapping_index, modifier_type | swizzle_order, scalar (object), dead_zone_lower, dead_zone_upper, dead_zone_type |
| `query_context` | context_path | — |
| `query_action` | action_path | — |

## Value Types

| MCP value_type | UE Enum | Returns |
|---------------|---------|---------|
| `Digital` | Boolean | bool (button press) |
| `Axis1D` | Axis1D | float (trigger) |
| `Axis2D` | Axis2D | FVector2D (thumbstick) |
| `Axis3D` | Axis3D | FVector (motion controller) |

## Trigger Types

| trigger_type | Description | Extra Params |
|-------------|-------------|--------------|
| `Pressed` | Fires once on key press | — |
| `Released` | Fires once on key release | — |
| `Down` | Fires every frame while held | — |
| `Hold` | Fires after held for duration | hold_time (seconds) |
| `HoldAndRelease` | Fires on release after hold duration | hold_time (seconds) |
| `Tap` | Quick press and release | tap_release_time (max seconds between press/release) |
| `Pulse` | Repeating trigger at interval while held | pulse_interval (seconds) |
| `ChordAction` | Requires another action to be active | chord_action_path (asset path) |

## Modifier Types

| modifier_type | Description | Extra Params |
|--------------|-------------|--------------|
| `Negate` | Inverts input values (e.g., S for backward) | — |
| `Swizzle` | Remaps axes (e.g., X input to Y output) | swizzle_order: `YXZ`, `ZYX`, `XZY`, `YZX`, `ZXY` |
| `Scalar` | Multiplies input by scale factor | scalar: `{x, y, z}` |
| `DeadZone` | Dead zone for analog inputs | dead_zone_lower, dead_zone_upper, dead_zone_type (`Axial`/`Radial`) |

## Common Key Names

### Keyboard
| Category | Keys |
|----------|------|
| Letters | `A` - `Z` |
| Numbers | `Zero`, `One` ... `Nine` |
| Function | `F1` - `F12` |
| Special | `SpaceBar`, `Enter`, `Escape`, `Tab`, `BackSpace` |
| Modifiers | `LeftShift`, `RightShift`, `LeftControl`, `RightControl`, `LeftAlt`, `RightAlt` |
| Arrows | `Left`, `Right`, `Up`, `Down` |

### Mouse
- Buttons: `LeftMouseButton`, `RightMouseButton`, `MiddleMouseButton`, `ThumbMouseButton`, `ThumbMouseButton2`
- Axes: `MouseX`, `MouseY`, `MouseScrollUp`, `MouseScrollDown`, `MouseWheelAxis`

### Gamepad
- Face: `Gamepad_FaceButton_Bottom` (A/X), `_Right` (B/O), `_Left` (X/Square), `_Top` (Y/Triangle)
- Shoulders: `Gamepad_LeftShoulder`, `Gamepad_RightShoulder`
- Triggers: `Gamepad_LeftTrigger`, `Gamepad_RightTrigger`, `Gamepad_LeftTriggerAxis`, `Gamepad_RightTriggerAxis`
- Sticks: `Gamepad_LeftStick_Up/Down/Left/Right`, `Gamepad_RightStick_Up/Down/Left/Right`
- Stick Buttons: `Gamepad_LeftThumbstick`, `Gamepad_RightThumbstick`
- D-Pad: `Gamepad_DPad_Up/Down/Left/Right`
- Special: `Gamepad_Special_Left` (Select), `Gamepad_Special_Right` (Start)

## Example Workflow

```json
// 1. Create InputAction
{
  "operation": "create_input_action",
  "action_name": "IA_Jump",
  "value_type": "Digital"
}

// 2. Create MappingContext
{
  "operation": "create_mapping_context",
  "context_name": "IMC_Default"
}

// 3. Add key mapping (returns mapping_index)
{
  "operation": "add_mapping",
  "context_path": "/Game/Input/IMC_Default",
  "action_path": "/Game/Input/IA_Jump",
  "key": "SpaceBar"
}

// 4. Add hold trigger to mapping
{
  "operation": "add_trigger",
  "context_path": "/Game/Input/IMC_Default",
  "mapping_index": 0,
  "trigger_type": "Hold",
  "hold_time": 0.5
}

// 5. Add modifier (e.g., negate for backward movement)
{
  "operation": "add_modifier",
  "context_path": "/Game/Input/IMC_Default",
  "mapping_index": 1,
  "modifier_type": "Negate"
}

// 6. Query to verify
{
  "operation": "query_context",
  "context_path": "/Game/Input/IMC_Default"
}
```
