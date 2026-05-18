# Material MCP Tools

Context for MCP tools that create material instances, set parameters, and assign materials.

## Material Class Hierarchy

```
UMaterialInterface
  +-- UMaterial                    (base material with shader graph)
  +-- UMaterialInstance
        +-- UMaterialInstanceConstant  (editor-time, saved with asset)
        +-- UMaterialInstanceDynamic   (runtime only, not saved)
```

MCP tools work with **UMaterialInstanceConstant** (MIC). Use `create_material_instance` to create, `set_material_parameters` to modify.

---

## Domain Tool: `unreal_ue` with `domain: "material"`

### Operations

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `create_material_instance` | Create a new MIC asset | `material_path`, `instance_name`, `package_path` | |
| `set_material_parameters` | Set scalar/vector/texture params | `material_path` | `scalars`, `vectors`, `textures` |
| `get_material_info` | Get material details and parameter values | `material_path` | |
| `set_skeletal_mesh_material` | Assign material to a skeletal mesh slot | `actor_name`, `material_path` | `slot_index` |
| `set_actor_material` | Assign material to an actor's mesh component | `actor_name`, `material_path` | `slot_index`, `component_name` |

### Parameter Formats

For `set_material_parameters`:
- `scalars`: `[{name, value}]`
- `vectors`: `[{name, r, g, b, a}]`
- `textures`: `[{name, texture_path}]`

---

### Example: Create Instance and Set Parameters

```json
{
  "domain": "material",
  "operation": "create_material_instance",
  "params": {
    "material_path": "/Game/Materials/M_Character_Base",
    "instance_name": "MI_Character_Red",
    "package_path": "/Game/Materials/Characters/"
  }
}
```

```json
{
  "domain": "material",
  "operation": "set_material_parameters",
  "params": {
    "material_path": "/Game/Materials/Characters/MI_Character_Red",
    "scalars": [
      {"name": "Roughness", "value": 0.4},
      {"name": "Metallic", "value": 0.0}
    ],
    "vectors": [
      {"name": "BaseColor", "r": 1.0, "g": 0.2, "b": 0.1, "a": 1.0}
    ],
    "textures": [
      {"name": "Normal", "texture_path": "/Game/Textures/T_Character_Normal"}
    ]
  }
}
```

### Example: Assign Material to Actor

```json
{
  "domain": "material",
  "operation": "set_actor_material",
  "params": {
    "actor_name": "Cube",
    "material_path": "/Game/Materials/Characters/MI_Character_Red",
    "slot_index": 0
  }
}
```

### Example: Get Material Info

```json
{
  "domain": "material",
  "operation": "get_material_info",
  "params": {
    "material_path": "/Game/Materials/Characters/MI_Character_Red"
  }
}
```

Response includes parent material, class, and all parameter values:

```json
{
  "name": "MI_Character_Red",
  "path": "/Game/Materials/Characters/MI_Character_Red",
  "class": "MaterialInstanceConstant",
  "is_instance": true,
  "parent": "/Game/Materials/M_Character_Base",
  "scalar_parameters": {"Roughness": 0.4, "Metallic": 0.0},
  "vector_parameters": {"BaseColor": {"r": 1.0, "g": 0.2, "b": 0.1, "a": 1.0}},
  "texture_parameters": {"Normal": "/Game/Textures/T_Character_Normal"}
}
```

---

## Common Parameter Names

| Parameter | Type | Typical Range | Description |
|-----------|------|---------------|-------------|
| `BaseColor` | vector | 0-1 per channel | Main albedo color |
| `Roughness` | scalar | 0-1 | Surface roughness |
| `Metallic` | scalar | 0-1 | Metallic amount |
| `Specular` | scalar | 0-1 | Specular intensity |
| `EmissiveColor` | vector | any | Emissive color |
| `EmissiveIntensity` | scalar | 0+ | Emissive strength |
| `Opacity` | scalar | 0-1 | Transparency |
| `Normal` | texture | | Normal map |
| `Albedo` / `Diffuse` | texture | | Base color texture |

Parameter names are defined by the parent material. Use `get_material_info` to discover available parameters on a specific material.

---

## Usage Tips

- Always `get_material_info` first to see available parameters and their current values.
- `create_material_instance` only creates the asset; use `set_material_parameters` separately to set values.
- `set_actor_material` works on any mesh component (StaticMesh, SkeletalMesh). Use `component_name` to target a specific component if the actor has multiple.
- Material paths follow standard asset path rules: must start with `/Game/`, no `..` traversal.
