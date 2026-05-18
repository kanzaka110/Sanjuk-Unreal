# Actor & Level MCP Tools

Context for MCP tools that spawn, move, query, and delete actors in the Unreal Editor.

## Simple Tools (called directly with `unreal_` prefix)

### unreal_spawn_actor

Spawn an actor into the current level.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `class` | string | Yes | Actor class name or full path (e.g., `"StaticMeshActor"`, `"/Game/BP_MyActor"`) |
| `name` | string | No | Display name for the actor |
| `location` | object | No | `{x, y, z}` world position |
| `rotation` | object | No | `{pitch, yaw, roll}` in degrees |
| `scale` | object | No | `{x, y, z}` scale factor |

### unreal_move_actor

Set or offset an actor's transform.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actor_name` | string | Yes | Name of the actor in the level |
| `location` | object | No | `{x, y, z}` world position |
| `rotation` | object | No | `{pitch, yaw, roll}` in degrees |
| `scale` | object | No | `{x, y, z}` scale factor |
| `relative` | bool | No | If true, values are offsets from current transform |

### unreal_delete_actors

Remove actors from the level. **Destructive** -- cannot be undone via MCP.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actor_names` | string[] | No* | List of actor names to delete |
| `actor_name` | string | No* | Single actor name to delete |
| `class_filter` | string | No | Delete only actors of this class |

*At least one of `actor_names` or `actor_name` must be provided.

### unreal_get_level_actors

Query actors in the current level. **Read-only.**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `class_filter` | string | No | | Filter by class name |
| `name_filter` | string | No | | Filter by actor name (substring match) |
| `include_hidden` | bool | No | false | Include hidden actors |
| `brief` | bool | No | true | Return minimal info (name, class, location) |
| `limit` | int | No | 25 | Max actors to return |
| `offset` | int | No | 0 | Skip first N results (pagination) |

### unreal_set_property

Set a property on an actor or its component.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actor_name` | string | Yes | Name of the actor |
| `property` | string | Yes | Property path (e.g., `"LightComponent.Intensity"`, `"bHidden"`) |
| `value` | any | Yes | New value for the property |

Property paths can traverse components using dot notation: `"ComponentName.PropertyName"`.

---

## Level Management: unreal_open_level

Manage levels in the editor.

| Action | Parameters | Description |
|--------|-----------|-------------|
| `open` | `level_path` (required) | Load existing map by asset path (e.g., `/Game/Maps/MyLevel`) |
| `new` | `template` (optional), `save_current` (optional, bool) | Create new blank map or from a named template |
| `save_as` | `save_path` (required) | Save current level to asset path |
| `list_templates` | (none) | List available map templates with names and paths |

**Sequential-only tool** -- invalidates all actor references. Never run in parallel with other tools.

---

## Level Path Validation Rules

Level paths used with MCP tools must:
- Start with `/Game/` (project content only)
- Not contain path traversal (`..`)
- Not reference `/Engine/` or `/Script/` paths
- Not exceed 512 characters
- Not contain dangerous characters (`<>|&;$(){}[]!*?~`)

---

## Usage Tips

- Use `get_level_actors` to survey the scene before modifying actors.
- Use `list_templates` before `new` to discover available template names.
- Use `asset_search` to find Blueprint class paths before passing to `spawn_actor`.
- `set_property` supports nested component properties via dot notation.
- When spawning many actors, parallelize `spawn_actor` calls with **different names** (max 4 concurrent).
