# Character MCP Tools Reference

Domain: `character` and `character_data` (via `unreal_ue` router)

## character Operations

Query and modify ACharacter actors in the current level.

| Operation | Required Params | Optional Params |
|-----------|----------------|-----------------|
| `list_characters` | — | class_filter, limit (default 100), offset |
| `get_character_info` | character_name | — |
| `get_movement_params` | character_name | — |
| `set_movement_params` | character_name | movement params (see table below) |
| `get_components` | character_name | component_class (filter string) |

### Movement Parameters (set_movement_params)

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| max_walk_speed | float | 0-10000 | Maximum walking speed (cm/s) |
| max_acceleration | float | 0-100000 | Maximum acceleration (cm/s^2) |
| ground_friction | float | 0-100 | Ground friction coefficient |
| jump_z_velocity | float | 0-10000 | Initial jump velocity (cm/s) |
| air_control | float | 0-1 | Air control factor |
| gravity_scale | float | -10 to 10 | Gravity multiplier |
| max_step_height | float | 0-500 | Maximum step height (cm) |
| walkable_floor_angle | float | 0-90 | Max walkable slope (degrees) |
| braking_deceleration_walking | float | 0-100000 | Braking decel when walking |
| braking_friction | float | 0-100 | Braking friction coefficient |

All movement params are optional; pass only the ones to change.

### Examples

```json
// List all characters
{"operation": "list_characters"}

// Filter by class
{"operation": "list_characters", "class_filter": "BP_Player"}

// Get character details
{"operation": "get_character_info", "character_name": "BP_PlayerCharacter_0"}

// Modify movement
{
  "operation": "set_movement_params",
  "character_name": "MyCharacter",
  "max_walk_speed": 800,
  "jump_z_velocity": 600,
  "air_control": 0.5
}

// Filter components by class
{"operation": "get_components", "character_name": "MyCharacter", "component_class": "Skeletal"}
```

---

## character_data Operations

Create and manage character configuration DataAssets and stats DataTables.
Auto-routed from character domain.

| Operation | Required Params | Optional Params |
|-----------|----------------|-----------------|
| `create_character_data` | asset_name | package_path, config fields (see below) |
| `query_character_data` | — | search_name, search_tags, limit, offset |
| `get_character_data` | asset_path | — |
| `update_character_data` | asset_path | any config field to update |
| `create_stats_table` | asset_name | package_path |
| `query_stats_table` | table_path | limit, offset |
| `add_stats_row` | table_path, row_name | stats fields (see below) |
| `update_stats_row` | table_path, row_name | any stats field to update |
| `remove_stats_row` | table_path, row_name | — |
| `apply_character_data` | asset_path, character_name | apply_movement, apply_mesh, apply_anim (bool) |

### UCharacterConfigDataAsset Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| config_id | FName | — | Unique identifier |
| display_name | string | — | |
| description | string | — | |
| skeletal_mesh | string | — | Soft reference path |
| anim_blueprint | string | — | Soft class reference path |
| is_player_character | bool | false | |
| base_walk_speed | float | 600.0 | |
| base_run_speed | float | 1000.0 | |
| base_jump_velocity | float | 420.0 | |
| base_acceleration | float | 2048.0 | |
| base_ground_friction | float | 8.0 | |
| base_air_control | float | 0.35 | |
| base_gravity_scale | float | 1.0 | |
| base_health | float | 100.0 | |
| base_stamina | float | 100.0 | |
| base_damage | float | 10.0 | |
| base_defense | float | 0.0 | |
| capsule_radius | float | 42.0 | |
| capsule_half_height | float | 96.0 | |
| gameplay_tags | string[] | [] | Array of tag names |

### FCharacterStatsRow Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| stats_id | FName | — | Row identifier |
| display_name | string | — | |
| max_health | float | 100.0 | |
| max_stamina | float | 100.0 | |
| walk_speed | float | 600.0 | |
| run_speed | float | 1000.0 | |
| jump_velocity | float | 420.0 | |
| damage_multiplier | float | 1.0 | |
| defense_multiplier | float | 1.0 | |
| xp_multiplier | float | 1.0 | |
| level | int | 1 | |
| tags | string[] | [] | |

### Example Workflow

```json
// 1. Create character config DataAsset
{
  "operation": "create_character_data",
  "asset_name": "DA_PlayerConfig",
  "config_id": "player_default",
  "display_name": "Default Player",
  "base_walk_speed": 600,
  "base_jump_velocity": 500,
  "base_health": 100,
  "is_player_character": true,
  "gameplay_tags": ["Player", "Human"]
}

// 2. Create stats DataTable
{
  "operation": "create_stats_table",
  "asset_name": "DT_PlayerStats"
}

// 3. Add stats rows
{
  "operation": "add_stats_row",
  "table_path": "/Game/Characters/DT_PlayerStats",
  "row_name": "Level1",
  "stats_id": "lvl1",
  "max_health": 100,
  "walk_speed": 600,
  "damage_multiplier": 1.0,
  "level": 1
}

{
  "operation": "add_stats_row",
  "table_path": "/Game/Characters/DT_PlayerStats",
  "row_name": "Level10",
  "stats_id": "lvl10",
  "max_health": 250,
  "walk_speed": 700,
  "damage_multiplier": 1.5,
  "level": 10
}

// 4. Query stats table
{
  "operation": "query_stats_table",
  "table_path": "/Game/Characters/DT_PlayerStats"
}

// 5. Apply config to runtime character
{
  "operation": "apply_character_data",
  "asset_path": "/Game/Characters/DA_PlayerConfig",
  "character_name": "BP_PlayerCharacter_0",
  "apply_movement": true,
  "apply_mesh": false
}
```

## Default Asset Paths

- Character configs: `/Game/Characters/`
- Stats tables: `/Game/Characters/`

Both tools accept `package_path` to customize output location.
