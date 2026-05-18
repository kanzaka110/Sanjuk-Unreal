# Asset MCP Tools

Context for MCP tools that search, inspect, and modify Content Browser assets.

## Simple Tools (called directly with `unreal_` prefix)

### unreal_asset_search

Search for assets in the Content Browser. **Read-only.**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search term (asset name, partial match) |
| `class_filter` | string | No | Filter by asset class (e.g., `"StaticMesh"`, `"MaterialInstanceConstant"`) |
| `path_filter` | string | No | Limit search to a content path (e.g., `"/Game/Characters/"`) |
| `limit` | int | No | Max results to return |

### unreal_asset_dependencies

Get assets that a given asset depends on. **Read-only.**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `asset_path` | string | Yes | Full asset path (e.g., `"/Game/Characters/SK_Character"`) |

### unreal_asset_referencers

Get assets that reference a given asset. **Read-only.**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `asset_path` | string | Yes | Full asset path |

---

## Domain Tool: `unreal_ue` with `domain: "asset"`

### Operations

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `set_asset_property` | Set a property value on an asset | `asset_path`, `property`, `value` | |
| `save_asset` | Save or mark asset dirty | `asset_path` | `save` (bool), `mark_dirty` (bool) |
| `get_asset_info` | Get asset metadata and properties | `asset_path` | `include_properties` (bool) |
| `list_assets` | List assets in a directory | `directory` | `class_filter`, `recursive` (bool), `limit` |

### Example: Set Property and Save

```json
{
  "domain": "asset",
  "operation": "set_asset_property",
  "params": {
    "asset_path": "/Game/Characters/SK_Character",
    "property": "bEnablePerPolyCollision",
    "value": true
  }
}
```

```json
{
  "domain": "asset",
  "operation": "save_asset",
  "params": {
    "asset_path": "/Game/Characters/SK_Character",
    "save": true
  }
}
```

### Example: List and Inspect

```json
{
  "domain": "asset",
  "operation": "list_assets",
  "params": {
    "directory": "/Game/Characters/",
    "class_filter": "SkeletalMesh",
    "recursive": true,
    "limit": 50
  }
}
```

```json
{
  "domain": "asset",
  "operation": "get_asset_info",
  "params": {
    "asset_path": "/Game/Characters/SK_Character",
    "include_properties": true
  }
}
```

---

## Supported Property Types for `set_asset_property`

| Type | JSON Value | Example |
|------|------------|---------|
| bool | boolean | `true` |
| int32, int64 | number | `42` |
| float, double | number | `3.14` |
| FString | string | `"text"` |
| FName | string | `"Name"` |
| FVector | object | `{"x": 1, "y": 2, "z": 3}` |
| FRotator | object | `{"pitch": 0, "yaw": 90, "roll": 0}` |
| FLinearColor | object | `{"r": 1, "g": 0, "b": 0, "a": 1}` |
| UObject* | string (path) | `"/Game/Assets/MyAsset"` |

---

## Hard vs Soft References

- **Hard reference** (`TObjectPtr`): Asset loads when the referencing object loads. Creates a direct dependency.
- **Soft reference** (`TSoftObjectPtr`): Stores only the asset path. Asset loads on demand. Use for optional or large assets.

`asset_dependencies` and `asset_referencers` report both types. Hard references cause cascading loads; soft references do not.
