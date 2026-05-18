# UE5 Graybox Level Design Context

## MCP Tools

### graymap_spawn

Bulk spawn graybox layout objects from an array of definitions.

**Parameters:**
- `objects` (array, required): Object definitions array
- `description` (string): Layout description for logging
- `folder_name` (string): Custom Outliner folder name. Default: `AI_GrayMap_YYYYMMDD_HHMMSS`
- `base_location` (object, optional but **REQUIRED for team builds**): World-space origin offset `{x, y, z}` in meters. When provided, the MCP bridge automatically adds this offset to every object's `location` before sending to Unreal. Objects should use **relative coordinates (0,0,0 origin)**. This eliminates the need for each Builder agent to manually calculate absolute positions.
  - **⚠ WARNING**: Omitting `base_location` causes ALL objects to spawn at world origin (0,0,0). In team builds, this means some Builder outputs will be at origin while others are at the correct location, resulting in a split/broken structure. **Every `graymap_spawn` call in a team build MUST include `base_location`.**

**Object definition format:**
```json
{
  "name": "Floor_Main",
  "type": "Cube",
  "location": {"x": 0, "y": 0, "z": 0},
  "rotation": {"x": 0, "y": 0, "z": 0},
  "scale": {"x": 10, "y": 8, "z": 0.2},
  "material": "Gray"
}
```

**Full example call:**
```json
{
  "objects": [
    {"name": "Floor", "type": "Cube", "location": {"x":0,"y":0,"z":0}, "rotation": {"x":0,"y":0,"z":0}, "scale": {"x":9,"y":8,"z":0.2}, "material": "Gray"},
    {"name": "Wall_North", "type": "Cube", "location": {"x":0,"y":8,"z":0}, "rotation": {"x":0,"y":0,"z":0}, "scale": {"x":9,"y":0.5,"z":4.5}, "material": "White"},
    {"name": "Pillar_Center", "type": "Cylinder", "location": {"x":4.5,"y":4,"z":0}, "rotation": {"x":0,"y":0,"z":0}, "scale": {"x":0.5,"y":0.5,"z":4.5}, "material": "Orange"}
  ],
  "description": "Medium combat room with pillar"
}
```

All spawns are wrapped in a single undo transaction — Ctrl+Z undoes the entire batch.
To iterate, undo (Ctrl+Z) and call `graymap_spawn` again with revised objects.

**⚠ Batch size limit**: 단일 `graymap_spawn` 호출당 오브젝트 **30개 이하** 권장. 30개 초과 시 JSON 구성 과정에서 `scale`, `rotation` 등 파라미터가 누락될 확률이 높아진다. 30개를 초과하면 **2회 이상으로 분할 호출**할 것. 같은 `folder_name`을 사용하면 동일 폴더에 합산된다.

### Team Agent Workflow (for complex structures)

For large/complex layouts (bridges, arenas, multi-room dungeons), use parallel subagents to split the work by structural component.

**Constraints:**
- MCP task queue: max 4 concurrent tool calls → max 3 subagents + 1 lead
- Each subagent calls `graymap_spawn` independently → separate folder & undo transaction
- Lead must pre-assign coordinate regions to prevent overlapping objects
- **`base_location` REQUIRED for team workflows**: Lead must pass the same `base_location` to every Builder agent. Builders use **relative coordinates only** (0,0,0 origin). The MCP bridge applies the offset automatically — Builders must NEVER add base offset manually

**Team Composition:**

```
Lead Agent (coordinator)
├─ 1. Call get_ue_context category="graymap" to load this context
├─ 2. Analyze request and decompose into structural components
├─ 3. Define coordinate boundaries and naming conventions per agent
├─ 4. ⚠ PILOT TEST (MANDATORY before full build):
│     Spawn 1 Builder with 1 simple object (e.g. foundation platform) only.
│     After completion, call get_level_actors and verify:
│       - Actor exists at expected world coordinates (base_location × 100 ± 10cm)
│       - folder_name is correct
│     If coordinates are wrong → fix the prompt and re-test before proceeding.
│     If correct → proceed to step 5.
├─ 5. Spawn ≤3 Builder subagents in parallel with:
│     - This full graymap context (copy into each agent's prompt)
│     - Assigned component type and coordinate region
│     - folder_name convention: "{structure}_{component}" (e.g. "Bridge_Deck")
│     - Material color assignment per component (MATERIAL RULE)
│     - ⚠ base_location JSON template (see below) — MUST be copy-pasted into prompt
├─ 6. Wait for all Builder agents to complete
├─ 7. Spawn Discriminator agent to validate results (including coordinate verification)
├─ 8. If Discriminator reports issues → fix or re-spawn failed components
└─ 9. Report final result to user

Builder Agent 1: Base structures (deck, floor, ramp, stairs)
Builder Agent 2: Vertical structures (tower, pillar, wall, cover)
Builder Agent 3: Connecting elements (cable, railing, decoration, landmark)

Discriminator Agent (validator) — runs AFTER all Builders complete:
├─ 1. ⚠ COORDINATE VERIFICATION (MUST DO FIRST):
│     a. get_level_actors to list all spawned actors with transforms
│     b. For EACH Builder folder, pick the first actor and verify:
│        - Actor world position matches expected (base_location × 100 + relative offset × 100)
│        - Tolerance: ± 10cm (± 10 UE units)
│     c. Verify ALL Builder folders share the same base coordinate origin
│        - If any folder's actors are at origin (0,0,0) while others are at base_location → FAIL
│     d. If coordinate mismatch detected → immediately FAIL, list which Builder(s) failed
│        and their actual vs expected coordinates. Do NOT proceed to visual inspection.
├─ 2. capture_viewport from multiple angles to visually inspect
├─ 3. get_level_actors to verify spawned actor count and folders
├─ 4. Validate against quality checklist (section 9 of this context):
│     - Spatial scale: room sizes, door sizes, ceiling heights
│     - Flow: reachability, dead-end rewards, gap/height ranges
│     - Design intent: shape language, material variety, landmarks
│     - Technical: all values in meters, valid types/materials
├─ 5. Check structural coherence between components:
│     - Do deck edges align with tower positions?
│     - Do cables connect from tower tops to deck?
│     - Are ramps/stairs reachable from ground level?
│     - Any floating objects or gaps between components?
└─ 6. Return verdict: PASS with summary, or FAIL with specific issues list
```

**Example — Bridge decomposition (base at world X=50, Y=20, Z=0):**
```
Lead assigns:
  base_location: {x: 50, y: 20, z: 0}   ← ALL Builders receive the same base_location
  Builder 1 (Deck):     folder="Bridge_Deck",     material=Gray,   region: z=5 platform
  Builder 2 (Towers):   folder="Bridge_Towers",   material=Orange, region: x=25,75 vertical
  Builder 3 (Cables):   folder="Bridge_Cables",   material=Red,    region: connecting towers to deck
  Discriminator:        runs after Builders, validates alignment and structure

Each Builder calls graymap_spawn with base_location={x:50, y:20, z:0} and uses relative coords:
  Builder 1: object.location={x:0, y:0, z:5}  → MCP applies → {x:50, y:20, z:5}
  Builder 2: object.location={x:25, y:0, z:0} → MCP applies → {x:75, y:20, z:0}
```

**Each Builder subagent prompt MUST include:**
1. The full graymap context (coordinate system, shapes, pivots, materials) — **copy the entire context, not a summary**
2. Exact coordinate region boundaries (to avoid overlap)
3. Assigned `folder_name` and `material` color
4. Naming prefix for objects (e.g., "Deck_Floor_01", "Tower_North_Base")
5. **⚠ Shape 방향 표 필수 복사 (Ramp/Stairs rotation)**: Builder가 Ramp 또는 Stairs를 배치할 경우, 아래 방향 테이블을 프롬프트에 **반드시 그대로 복사**하여 포함. Builder가 자체 판단으로 yaw를 결정하는 것을 방지.
   - **Lead가 모든 Ramp/Stairs의 rotation.z(yaw) 값을 사전 계산**하여 숫자로 명시할 것. "적절히 회전", "전면이므로 반대로" 같은 **추상적 rotation 지시 금지**.
   ```
   ━━━ Ramp 방향 (경사가 내려가는 방향) ━━━
   | 내려가는 방향 | Yaw (z) |
   | +Y (기본)    | 0       |
   | -Y           | 180     |
   | +X           | -90     |
   | -X           | 90      |
   
   ━━━ Stairs 방향 (계단이 올라가는 방향) ━━━
   | 올라가는 방향 | Yaw (z) |
   | +Y (기본)    | 0       |
   | -Y           | 180     |
   | +X           | -90     |
   | -X           | 90      |
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```
6. **⚠ base_location JSON call template (CRITICAL — copy-paste this exact block into every Builder prompt):**

```
━━━ graymap_spawn 호출 시 반드시 아래 구조를 사용하라 ━━━
graymap_spawn({
  "base_location": {"x": <LEAD가 지정한 X>, "y": <LEAD가 지정한 Y>, "z": <LEAD가 지정한 Z>},
  "folder_name": "<할당된 폴더명>",
  "description": "<설명>",
  "objects": [ ... ]
})
⚠ base_location을 누락하면 오브젝트가 원점(0,0,0)에 생성되어 전체 빌드가 실패한다.
⚠ 모든 object의 location은 상대 좌표(0,0,0 기준)만 사용하라. base_location 오프셋은 MCP가 자동 적용한다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

   Lead는 `<LEAD가 지정한 X/Y/Z>` 부분을 실제 좌표값으로 치환한 뒤 각 Builder 프롬프트에 포함한다.
   **Builder는 이 블록을 그대로 따라 호출해야 하며, base_location 파라미터를 생략하거나 변경해서는 안 된다.**

**Discriminator subagent prompt must include:**
1. The original user request (what was asked to build)
2. The full graymap context (especially section 9: Quality Verification Checklist)
3. Expected component list and their coordinate regions
4. Instructions to use `capture_viewport` and `get_level_actors` for inspection
5. **⚠ base_location value and expected world coordinates** — Discriminator must verify that actors are at `base_location × 100` (UE cm), NOT at origin (0,0,0). Include the exact expected UE coordinates for at least one reference actor per Builder folder.

---

## Coordinate System & Units

- **Coordinate system**: Z-up (X=Forward, Y=Right, Z=Up)
- **ALL values use METERS** (1 = 1 meter). The tool converts to UE cm internally.
- **location**: Pivot point position in meters (NOT bounding box center — each shape has a different pivot)
- **scale**: Desired bounding box size in meters, defined in **LOCAL space** (x=width, y=depth, z=height).
  - Scale axes are relative to the ACTOR, not the world. Rotation is applied AFTER scale.
  - At Yaw=0: scale.x aligns with world X, scale.y aligns with world Y.
  - At Yaw=90: scale.x aligns with world Y, scale.y aligns with world -X.
  - **Rule**: When placing an elongated object, set scale.x to the object's LONG dimension. Then use Yaw to orient that long side to the desired world axis.
  - Example: A 3m×0.6m bench parallel to the Y-axis → scale={x:3, y:0.6, z:0.45}, rotation={z:90}
- **rotation**: Degrees. x=Roll (around X-Forward), y=Pitch (around Y-Right), z=Yaw (around Z-Up)
  - z rotation: turns object left/right on the ground plane (most common)
  - y rotation: tilts object forward/backward
  - x rotation: rolls object sideways
  - Example: Ramp facing +Y direction = Ramp with z=90
  - IMPORTANT: For thin diagonal elements (cables, wires, angled beams), use Cylinder.
    Cylinder pivot is at BOTTOM-CENTER. Set scale x,y=small diameter, z=cable length.
    Use y rotation (pitch) for tilt angle, z rotation (yaw) for tilt DIRECTION:
      z=0 + pitch → tilts toward -X
      z=90 + pitch → tilts toward -Y
      z=180 + pitch → tilts toward +X
      z=270 + pitch → tilts toward +Y
    Place location at the cable's LOWER end (where it connects to deck).
    pitch angle = degrees from vertical (e.g. 30 = slight tilt, 60 = steep tilt).

### Scale Reference
- Human character: ~1.8m tall
- **⚠ Character clearance envelope: 1m wide × 2m tall** — see MANDATORY CLEARANCE rule in §5
- Floor thickness: 0.2m
- Wall thickness: 0.5m
- Ground level: z=0
- Door/Room/Corridor 상세 치수: §5.4 Spatial Presets 참조

---

## Shapes (5 types, ALL pivots are at the BOTTOM)

### Cube
Box shape. scale={x:W, y:D, z:H}.
Pivot at **BOTTOM-CORNER** (min X, min Y, min Z).
A 1m cube at origin occupies x=[0,1], y=[0,1], z=[0,1].

### Cylinder
Z-axis aligned cylinder. scale={x:diameter, y:diameter, z:height}.
Pivot at **BOTTOM-CENTER**.

### QuarterCylinder
Quarter-circle, Z-axis aligned. scale={x:W, y:D, z:H}.
Pivot at **BOTTOM of the right-angle corner** (where two flat faces meet).

Default orientation (yaw=0): curved surface extends into the **+X, +Y quadrant**.
- Flat face A: along XZ plane (Y=0), extends toward +X
- Flat face B: along YZ plane (X=0), extends toward +Y
- Curved face: arc connecting the +X end to the +Y end

Top-down view (yaw=0):
```
    +Y
    │  ╲  (curved face)
    │    ╲
    │     )
    P────── +X
  (pivot = right-angle corner)
```

Yaw rotation changes which quadrant the curve occupies:
- yaw=0:   curve in +X,+Y quadrant
- yaw=90:  curve in -X,+Y quadrant
- yaw=180: curve in -X,-Y quadrant
- yaw=270: curve in +X,-Y quadrant

**`curve_direction` shortcut** (QuarterCylinder only, optional):
Instead of calculating yaw manually, specify which direction the curved face should extend.
The tool auto-calculates the correct yaw. If both `curve_direction` and `rotation.z` are set, `curve_direction` wins.

| curve_direction | Resulting Yaw | Curve extends toward |
|-----------------|---------------|----------------------|
| `"+x+y"` | 0° | +X and +Y |
| `"-x+y"` | 90° | -X and +Y |
| `"-x-y"` | 180° | -X and -Y |
| `"+x-y"` | 270° | +X and -Y |

**Arch recipe** (two QuarterCylinders forming an arch between columns):

Both QCs share the same pivot location (arch top-center, between columns).
- Left half:  curve extends toward -X → `curve_direction: "-x-y"` (or yaw=180)
- Right half: curve extends toward +X → `curve_direction: "+x-y"` (or yaw=270)

Example — arch 3m wide, 1m tall, 0.5m deep, between columns 3m apart:
```json
{"name":"Arch_01_Left",  "type":"QuarterCylinder", "location":{"x":1.5,"y":0,"z":3},
 "scale":{"x":1.5,"y":0.5,"z":1}, "curve_direction":"-x-y", "material":"Orange"}
{"name":"Arch_01_Right", "type":"QuarterCylinder", "location":{"x":1.5,"y":0,"z":3},
 "scale":{"x":1.5,"y":0.5,"z":1}, "curve_direction":"+x-y", "material":"Orange"}
```
Note: Both QCs are at the SAME location (arch center-top). The curve_direction controls which side each half-arch extends to.

### Ramp
Wedge/slope shape. Pivot at **BOTTOM-CORNER** (min X, min Y, min Z).
scale: x=width, y=slope_run (horizontal length of slope), z=height (of tall vertical face).

Default orientation: tall vertical face at min-Y (pivot side), slopes DOWN toward +Y to ground.

Example — ramp from ground up to 5m deck, 15m run, 10m wide:
  location={x:0, y:-15, z:0}, scale={x:10, y:15, z:5}, rotation={x:0, y:0, z:0}
  (pivot at y=-15 z=0, high edge at y=-15 z=5, low edge at y=0 z=0)

**Direction table** (where the ramp slopes DOWN to):

| Slopes down toward | Yaw (z) | High edge at | Low edge at |
|--------------------|---------|-------------|-------------|
| +Y (default) | 0 | min Y (pivot) | max Y |
| -Y | 180 | max Y | min Y (pivot) |
| +X | -90 | min X (pivot) | max X |
| -X | 90 | max X | min X (pivot) |

### Stairs
Procedural stepped staircase (BP_Stairs Blueprint actor). Pivot at **BOTTOM-CORNER** (min X, min Y, min Z).
scale: x=width, y=depth (horizontal run), z=height (total rise).
Unlike other shapes, Stairs spawns a Blueprint actor with procedural mesh generation.

Default orientation: first step at pivot (min Y), ascends toward **+Y** while rising in +Z.

Example — 3m wide staircase, 5m run, 3m rise (ascends toward +Y):
  {"name":"Stairs_Main", "type":"Stairs", "location":{"x":0,"y":0,"z":0},
   "rotation":{"x":0,"y":0,"z":0}, "scale":{"x":3,"y":5,"z":3}, "material":"Gray"}
  → auto: step_height=0.25m, num_steps=12
  (pivot at y=0 z=0, top step at y=5 z=3)

To ascend toward -X: rotation z=90. Toward -Y: z=180. Toward +X: z=-90.

**⚠️ Slope constraint (CRITICAL)**: `atan(scale.z / scale.y)` must be ≤ 44° (UE5 default walkable floor angle).
  - Max ratio: `scale.z / scale.y ≤ 0.97` (e.g., z=3 → y must be ≥ 3.1)
  - If single run exceeds 44°: **use Switchback pattern (Section 7.8)** — split into two half-runs + landing.
  - **NEVER place a single full-height stair for multi-story buildings.** Always use switchback.
  - The code will emit a warning if slope exceeds 44°, but you must fix it at design time.

**Run depth formula (MUST USE when calculating stair dimensions)**:
  - Given target height H: **minimum run depth y = H / tan(40°) ≈ H × 1.2**
  - This gives ~40° slope — comfortable for gameplay and safely under 44° limit.
  - Example: 5m height → y = 6m run → atan(5/6) = 39.8° ✓
  - Example: 3m height → y = 3.6m run → atan(3/3.6) = 39.8° ✓
  - **Always calculate run depth BEFORE placing.** Never guess or use scale 1:1:1.

**Extra optional fields** (Stairs only):
- `step_height` (meters): Height of each individual step. Default: 0.25m (25cm).
- `num_steps` (int): Number of steps. Default: auto-calculated as floor(height / step_height).
- `floating` (bool): If true, gaps between steps. Default: false.

Example — custom steps:
  {"name":"Stairs_Wide", "type":"Stairs", "location":{"x":0,"y":0,"z":0},
   "rotation":{"x":0,"y":0,"z":0}, "scale":{"x":4,"y":8,"z":4}, "material":"Orange",
   "step_height":0.3, "num_steps":13}

**⚠️ Footplate rule (MANDATORY for walkable stairs)**:

캐릭터가 걸어서 이동하는 목적의 Stairs는 **시작 변(bottom edge)과 종료 변(top edge)이 동선과 연결**되어 있어야 한다. 해당 변이 바닥 슬래브, 랜딩, 플랫폼 등 걸을 수 있는 표면에 닿지 않고 **허공에 떠 있는 경우**, 반드시 발판(footplate)을 추가해야 한다.

**발판 규격:**
- **너비(width)**: 계단의 시작/종료 변 너비와 동일 (= `scale.x`)
- **깊이(depth)**: 최소 **1m** (계단 진행 방향으로 연장)
- **두께**: 0.2m (표준 슬래브 두께)
- **Type**: Cube
- **Material**: 계단과 동일 색상 또는 Gray

**발판이 필요한 경우 (floating edge):**
- 계단 시작점이 바닥 슬래브 위에 있지 않을 때 → 시작 변 발판
- 계단 종료점이 상부 슬래브/플랫폼에 맞닿지 않을 때 → 종료 변 발판
- Switchback의 Run1 시작이 바닥 슬래브 범위 밖일 때 → 시작 변 발판
- Switchback의 Run2 종료가 상층 슬래브 개구부 가장자리에 도달하지 못할 때 → 종료 변 발판

**발판이 불필요한 경우 (connected edge):**
- 시작/종료 변이 바닥 슬래브 위에 직접 놓여 있을 때
- Switchback 중간 랜딩이 Run1↔Run2를 연결할 때 (랜딩 자체가 발판 역할)
- 종료 변이 플랫폼/캣워크 표면과 정확히 맞닿을 때

**발판 배치 공식:**
```
시작 변 발판 (bottom footplate):
  location: 계단 pivot에서 진행 반대 방향으로 1m 오프셋
  scale: {x: stair_width, y: 1.0, z: 0.2}
  z: 계단 시작 Z (= 계단 location.z)

종료 변 발판 (top footplate):
  location: 계단 상단 끝(top step) 위치에서 진행 방향으로 연장
  scale: {x: stair_width, y: 1.0, z: 0.2}
  z: 계단 종료 Z (= 계단 location.z + scale.z)
```

**Footplate position by yaw:**

| Yaw | 상승 방향 | Bottom footplate location (Y offset) | Top footplate location (Y offset) |
|-----|----------|--------------------------------------|-----------------------------------|
| 0 | +Y | y = pivot.y - 1.0 | y = pivot.y + scale.y |
| 180 | -Y | y = pivot.y | y = pivot.y - scale.y - 1.0 |
| 90 | -X | x = pivot.x | x = pivot.x - scale.y - 1.0 |
| -90 | +X | x = pivot.x - 1.0 | x = pivot.x + scale.y |

**Example — 3m wide, 5m run, 3m rise stair with both footplates (both edges floating):**
```json
{"name":"Stair_BottomPlate", "type":"Cube", "location":{"x":0,"y":-1,"z":0},
 "scale":{"x":3,"y":1,"z":0.2}, "material":"Gray"},
{"name":"Stair_Main", "type":"Stairs", "location":{"x":0,"y":0,"z":0},
 "scale":{"x":3,"y":5,"z":3}, "material":"Gray"},
{"name":"Stair_TopPlate", "type":"Cube", "location":{"x":0,"y":5,"z":2.8},
 "scale":{"x":3,"y":1,"z":0.2}, "material":"Gray"}
```
→ 시작 변(y=0, z=0)과 종료 변(y=5, z=3)에 각각 발판(3m×1m×0.2m)이 맞닿아 캐릭터가 안전하게 진입/이탈할 수 있음.

**검증 방법**: 계단을 배치한 후, 시작 변과 종료 변 각각에 대해 "이 변 아래/위에 걸을 수 있는 표면이 있는가?"를 확인한다. 없으면 발판을 추가한다.

---

## Materials (10 colors)

Black, Blue, ChromeYellow, Gray, Green, Orange, Pink, Red, White, Yellow

**MATERIAL RULE**: Each structural component group MUST use a DIFFERENT color so they are visually distinguishable.
Example: deck=Gray, towers=Orange, cables=Red, railings=White, ramps=Yellow, pillars=Blue.

---

## Level Design Quick Reference

### Graymap-Specific Rules
- **"See it → reach it"**: Visually perceivable spaces must be reachable. Block unreachable areas with walls/height.
- **Material color guidance**: warm (Orange, Yellow) = progress/safe; cool/intense (Blue, Red) = danger; neutral (Gray, White) = structural. Use different palettes per zone.
- **Birth-Canal pattern**: Narrow corridor (2-3m wide, 3m tall) → open space (8m+ wide). Required for every new area entry.
- **Shape language → primitives**: Round/safe = Cylinder, QuarterCylinder; Square/stable = Cube; Triangle/danger = Ramp, angled Cubes.
- **Weenie landmarks**: Tall Cylinder/Cube in eye-catching color (Orange, ChromeYellow). At least 1 per zone, always visible.
- **Dead-end reward rule**: Every branch off the main path MUST have a reward or point of interest at its end.
- **Verticality**: Ascending = progress; Descending = danger. Even 1-2m height changes add variety.
- **Tension-release rhythm**: Alternate narrow/complex spaces (combat) with wide/open spaces (rest/exploration).

### Spatial Organization Patterns

| Pattern | Use For |
|---------|---------|
| **Linear** | Tutorials, narrative, corridors |
| **Grid** | Mazes, dungeons, metroidvania |
| **Centralized** | Hub worlds, boss arenas |
| **Radial** | Boss approaches, convergence |
| **Clustered** | Open world outposts, villages |

### Dungeon Progression (atmosphere shift)
- **Early**: Bright (White, Yellow), wide, simple
- **Mid**: Medium (Gray, Blue), narrowing, height differences
- **Late**: Dark/intense (Black, Red), complex, narrow + wide alternation

---

## 5. Character Abilities & Spatial Presets (DT_LevelCmd)

Project-specific character movement abilities and spatial presets. All values in meters.

### ⚠ MANDATORY CLEARANCE RULE (NON-NEGOTIABLE)

**Every space the character walks through MUST have at least 1m clear width AND 2m clear height.**

This applies to ALL passable spaces including but not limited to:
- Doorways, corridors, passages
- Stairwell entrances and landings
- Gaps between walls, partitions, stairs, and any other geometry
- The space BETWEEN a stair run and an adjacent wall or partition

**Measurement method**: At the narrowest/lowest point of any passage, measure the unobstructed gap. If ANY axis is below the minimum, the character CANNOT pass through.

**Common violation**: Stairs placed flush against a partition wall, leaving zero clearance between the stair geometry and the door opening. The player sees the door but cannot reach it because the stair body blocks the path.

**How to apply**: After placing geometry, mentally walk the character (1m-wide, 2m-tall cylinder) through every intended path. At every doorway and transition, verify that no adjacent object intrudes into the 1m × 2m envelope.

### 5.1 Character Movement — Vertical (Z-axis)

| Action | Height (m) | Design Usage |
|--------|-----------|--------------|
| Single jump max | 3.1 | Obstacles below this can be jumped over |
| Double jump max | 4.0 | Maximum height for double-jump sections |
| Fall no-damage max | 15.0 | Falls below this are safe. Above is dangerous |

### 5.2 Character Movement — Horizontal (XY-axis)

| Action | Distance (m) | Design Usage |
|--------|-------------|--------------|
| Jump distance | 3.4 | Max gap crossable by basic jump |
| Double jump distance | 5.0 | Gap requiring double jump |
| Jump + dash | 5.0 | |
| Double jump + dash | 5.0 | |
| Sprint + jump | 4.9 | |
| Sprint + double jump | 11.0 | Expert reward paths |
| Sprint + double jump + air dash | 14.0 | Maximum reach. Extreme challenge only |

### 5.3 Hurdle-Up (Ledge Climbing)

| Action | Height (m) | Description |
|--------|-----------|-------------|
| Ground hurdle 1 | 0.45-0.7 | Step over |
| Ground hurdle 2 | 0.7-1.1 | One-hand climb |
| Ground hurdle 3 | 1.1-1.5 | Two-hand climb |
| Ground hurdle 4 | 1.5-2.0 | High two-hand climb |
| Air hurdle 1 | 0.8-1.4 | Waist-height ledge (mid-air) |
| Air hurdle 2 | 1.8-1.87 | Head-height ledge (mid-air) |

**Design rules**:
- Walls above 2.0m (hurdle impossible) serve as boundaries
- Hurdle-able ledges serve as exploration paths or shortcuts

### 5.4 Spatial Presets

**Path (Corridor)**:

| Size | Width (m) | Depth (m) | Height (m) | Purpose |
|------|-----------|-----------|-----------|---------|
| S | 2.5 | 10 | 3.0 | Medium-or-smaller monsters only |
| M | 4.0 | 10 | 3.0 | Medium+ monsters can pass |
| L | 7.0 | 10 | 4.5 | Large corridor |

**Door**:

| Size | Width (m) | Thickness (m) | Height (m) | Purpose |
|------|-----------|---------------|-----------|---------|
| S | 1.0 | 0.2 | 2.0 | Small door |
| M | 1.4 | 0.2 | 2.2 | Medium door |
| L | 2.5 | 0.2 | 3.0 | Large door — Strider-class passable |

**Room**:

| Size | Width (m) | Depth (m) | Height (m) | Purpose |
|------|-----------|-----------|-----------|---------|
| S | 5 | 2 | 3.0 | Small room — no combat |
| M | 9 | 8 | 4.5 | Medium room — large monster placement |
| L | 25 | 25 | 5.5 | Large room — minimum boss room size |

**Other Presets**:

| Element | Value (m) | Notes |
|---------|----------|-------|
| Minimum ceiling height | 3.5 | All indoor spaces |
| Wall thickness | 0.5 | Standard wall thickness |

### 5.5 Ability-Based Spatial Design Guide

**Gap/Pit Width**:
- Easy (single jump): gap ≤ 3.0m
- Normal (double jump/dash): gap 3.5-5.0m
- Hard (sprint+jump): gap 5.0-11.0m
- Extreme (max combo): gap 11.0-13.0m (reward paths only)

**Height Differences**:
- Hurdle-up climbable: 0.45-2.0m → exploration/shortcut paths
- Single jump: ≤ 3.1m → normal platforming
- Double jump: 3.1-4.0m → challenge sections
- Jump impossible: > 4.0m → Ramp/stairs required

**Safe vs Dangerous Falls**:
- ≤ 15m: Safe | > 15m: Damage → show danger or install railings

---

## 6. Primitive Architecture Implementation Guide

| Element | Shape | Scale Example | Notes |
|---------|-------|--------------|-------|
| **Wall** | Cube | {x:4, y:0.5, z:3.5} | Curved: QuarterCylinder or multiple Cylinders |
| **Floor** | Cube | {x:9, y:8, z:0.2} | Thickness 0.2m |
| **Doorway** | Gap in wall | Two pillars + lintel Cube above | S: 1x2m, M: 1.4x2.2m, L: 2.5x3m |
| **Stairs (smooth)** | Ramp | {x:3, y:15, z:5} | ~18° slope for 5m climb |
| **Stairs (stepped)** | Stairs | {x:3, y:5, z:3} | Procedural steps, auto step_height=0.25m |
| **Stairs (manual)** | Cubes | {x:2, y:0.3, z:0.25} each | 0.25m height increments (manual placement) |
| **Pillar** | Cylinder | {x:0.5, y:0.5, z:3} | Square: use Cube {x:0.5, y:0.5, z:3} |
| **Low cover** | Cube | {x:2, y:0.5, z:1.0} | High cover: z=1.8 |
| **Round cover** | Cylinder | {x:1.0, y:1.0, z:1.0} | |
| **Railing** | Cube + Cylinders | Bar: {x:len, y:0.05, z:0.05} at z=1.0; Posts: Cyl {x:0.05, y:0.05, z:1.0} | |
| **Platform** | Cube | {x:W, y:D, z:0.2} at desired z | Always pair with Ramp/stairs access |
| **Landmark** | Cylinder | {x:1, y:1, z:10} Orange/ChromeYellow | Visible from distance |

---

## 7. Spatial Pattern Recipes

### 7.1 Medium Room (Room_M)
Floor Cube {x:9,y:8,z:0.2} at z=0. 4 walls Cube {y:0.5,z:4.5}. Ceiling at z=4.5. 1-2 medium doors (M). Palette: floor=Gray, walls=White, ceiling=Gray.

### 7.2 Birth-Canal → Open Space
Narrow corridor Path_S (2.5m wide, 3m tall) → wide room Room_L (25x25m) or Room_M. Weenie in wide room. Different material palette per zone.

### 7.3 Boss Arena
Entry: Birth-Canal → Large door (L). Arena: 25x25m+. Cover: 2-4 low Cubes/Cylinders. Pillars: Cylinder x4-6 at edges. Exit on opposite side. Palette: floor=Red/Black, pillars=Orange, cover=Gray. Shape language: danger (Ramps/slopes).

### 7.4 Hub Space
Center: Room_M+ (9x8m+). 3-5 exits (Path_M or Door_M/L). Central landmark. Color hints per exit direction. Shape: round/safe (Cylinder pillars). Palette: center=White/Gray, exits=zone colors.

### 7.5 Vertical Exploration
Base z=0 → hurdle ledge 1.5m → single jump platform z=3 → double jump z=4 → top z=8+ (Ramp required). Railings at 15m+ falls. Different color per height level.

### 7.6 Gap Jump Section
Easy: 2-3m gap (single jump). Normal: 3.5-5m (double jump/dash). Hard: 5-10m (sprint+double jump). Extreme reward: 11-13m. Below: safe (≤15m) or dangerous (>15m). Palette: safe=Green, danger=Red.

### 7.7 Shortcut Structures
- **Hurdle-up ledge**: 1.5-2.0m Cube (jump down from above, hurdle from below)
- **One-way Ramp**: descends high→low, cannot ascend reverse
- **Opening door**: one-side-only (remove wall Cube segment)
- **Elevator marker**: Cube platforms at two heights

### 7.8 Switchback Staircase (Multi-Story)

A switchback stair fits two half-runs and an intermediate landing inside a vertical shaft. This is the correct pattern for multi-story buildings where a single straight run is too long or steep.

**Anatomy (side view, floor height H=3.5m, shaft depth D=5m):**
```
         z=H (3.5m)  ──── Upper Floor Slab (with opening) ────
                      │                                       │
         z=H/2(1.75) ─┤  Run2 ↑ (1.75m run)                  │
                      │  (walks toward -Y)                    │
                      │                                       │
         z=H/2-0.1   ─┤  ══ Landing (flat, ≥1.5m deep) ══    │← Door to upper floor
                      │      y=run_depth ~ y=run_depth+1.5   │
                      │                                       │
         z=0          ─┤  Run1 ↑ (1.75m run)                  │
                      │  (walks toward +Y)                    │
                      │  y=0 ~ y=run_depth                    │
         z=0          ──── Lower Floor Slab ──────────────────
```

**Top view (Y-axis layout — THIS IS WHERE ERRORS HAPPEN):**
```
  y=0         y=run_depth    y=run_depth+landing    y=shaft_end
  ├── Run1 ──┤── Landing ───┤──── Run2 ────────────┤
              ↑              ↑
              Run1 ends      Run2 starts
              HERE            HERE
              
  ⚠ Landing MUST span from Run1's end to Run2's start.
     If Landing is shorter, there is an impassable gap.
```

**Key rules:**
1. **Two half-runs + one landing** — never one full-height run. Each run rises H/2 (half the floor height).
2. **Landing connects to door** — the intermediate landing's XY must align with the partition door so the player can exit to the main room. This is the most critical rule.
3. **Landing height = H/2 minus slab thickness** — the landing sits at half the floor height (e.g., z=1.65m for H=3.5m with 0.2m thick slab). NOT at upper floor z.
4. **Runs face opposite directions** — Run1 yaw=0 (toward +Y), Run2 yaw=180 (toward -Y), or vice versa.
5. **Opening in slab** — the upper floor slab must have a hole covering BOTH runs and the landing.
6. **Landing Y-span must bridge Run1→Run2** — Landing starts exactly where Run1 ends, and ends exactly where Run2 starts. No gap allowed. This is the #1 source of broken staircases.

**⚠ Switchback Stair Dimension Formula (MANDATORY):**

Given: `floor_height` (층고), `stair_width` (계단 폭), `shaft_depth` (계단실 Y깊이)

```
landing_depth = max(1.5m, stair_width)        ← 최소 1.5m, 방향 전환 공간 확보
run_depth     = (shaft_depth - landing_depth) / 2
run_height    = floor_height / 2
slope         = atan(run_height / run_depth)   ← 44° 이하여야 함 (§Stairs slope constraint 참조)

Run1 Y범위:  shaft_start ~ shaft_start + run_depth
Landing Y범위: shaft_start + run_depth ~ shaft_start + run_depth + landing_depth
Run2 Y범위:  shaft_start + run_depth + landing_depth ~ shaft_end

⚠ 랜딩은 Run1 상단 끝 ~ Run2 하단 시작을 물리적으로 완전히 연결해야 함
  Landing.Y위치 = Run1 끝 Y좌표
  Landing.Y스케일 = landing_depth (Run2 시작점까지 도달)
  이 규칙을 어기면 캐릭터가 Run1에서 내려도 Run2에 진입할 수 없음
```

**Dimension example (floor height 3.5m, shaft 2.5m × 5m):**

| Element | Type | Scale (x,y,z) | Offset from shaft origin | Notes |
|---------|------|---------------|--------------------------|-------|
| Run1 | Stairs | (2.5, 1.75, 1.75) | y=0, z=0 | Rises from z=0 to z=1.75 |
| Landing | Cube | (2.5, **1.5**, 0.2) | y=1.75, z=1.65 | **Run1 끝 ~ Run2 시작을 완전히 커버** |
| Run2 | Stairs | (2.5, 1.75, 1.75) | y=3.25, z=1.75, yaw=180 | Rises from z=1.75 to z=3.5 |

Verification: Run1 ends at y=1.75, Landing spans y=1.75~3.25, Run2 starts at y=3.25 → **연속, 갭 없음** ✅

**Copy-paste template (floor height 3.5m, stair width 1.5m, shaft depth 5m):**

```json
// 계단실 원점 기준 오프셋. base_location이나 건물 오프셋에 더하여 사용
{ "name": "{F}_Stair_Run1",    "type": "Stairs", "scale": {"x":1.5, "y":1.75, "z":1.75},
  "offset": {"x":0, "y":0, "z":0} },
{ "name": "{F}_Stair_Landing", "type": "Cube",   "scale": {"x":1.5, "y":1.5,  "z":0.2},
  "offset": {"x":0, "y":1.75, "z":1.65} },
{ "name": "{F}_Stair_Run2",    "type": "Stairs", "scale": {"x":1.5, "y":1.75, "z":1.75},
  "offset": {"x":0, "y":3.25, "z":1.75}, "rotation": {"x":0, "y":0, "z":180} }
```

**⚠ Switchback Footplate Rule (§Stairs footplate rule 적용):**

Switchback 계단에서 발판이 필요한 위치:
- **Run1 시작 변(bottom)**: Run1 하단이 바닥 슬래브 위에 놓여 있으면 불필요. 슬래브 범위 밖이면 발판 추가.
- **Run2 종료 변(top)**: Run2 상단이 상층 슬래브에 맞닿으면 불필요. 슬래브 개구부 안쪽에서 끝나 허공이면 발판 추가.
- **중간 랜딩**: Landing Cube가 Run1↔Run2를 연결하므로 별도 발판 불필요 (랜딩 = 발판).

**Copy-paste template에 발판 포함 (Run1 bottom, Run2 top이 floating인 경우):**
```json
{ "name": "{F}_Stair_BottomPlate", "type": "Cube", "scale": {"x":1.5, "y":1.0, "z":0.2},
  "offset": {"x":0, "y":-1.0, "z":-0.2} },
{ "name": "{F}_Stair_Run1",    "type": "Stairs", "scale": {"x":1.5, "y":1.75, "z":1.75},
  "offset": {"x":0, "y":0, "z":0} },
{ "name": "{F}_Stair_Landing", "type": "Cube",   "scale": {"x":1.5, "y":1.5,  "z":0.2},
  "offset": {"x":0, "y":1.75, "z":1.65} },
{ "name": "{F}_Stair_Run2",    "type": "Stairs", "scale": {"x":1.5, "y":1.75, "z":1.75},
  "offset": {"x":0, "y":3.25, "z":1.75}, "rotation": {"x":0, "y":0, "z":180} },
{ "name": "{F}_Stair_TopPlate", "type": "Cube", "scale": {"x":1.5, "y":1.0, "z":0.2},
  "offset": {"x":0, "y":1.5, "z":3.3} }
```
→ Run2 yaw=180: 상단은 y=3.25-1.75=1.5 위치, z=1.75+1.75=3.5. TopPlate는 y=1.5, z=3.3(=3.5-0.2)에 배치.

**Common mistakes to avoid:**
- ❌ Single full-height run with no landing → arrival point far from door, blocked by partition
- ❌ Landing not aligned with partition door → player reaches landing but cannot enter room
- ❌ Two independent full-height stairs labeled "switchback" → not a true switchback, same problem
- ❌ Forgot slab opening → player hits ceiling at top of run
- ❌ **Landing too small to bridge Run1→Run2** → 랜딩이 Run1 상단에만 걸치고 Run2 하단에 도달하지 못함. 캐릭터가 랜딩에서 Run2로 건너갈 수 없음
- ❌ **Floating stair edge without footplate** → 계단 시작/종료 변이 허공에 떠 있는데 발판이 없음. 캐릭터가 계단에 진입/이탈 불가

**Landing clearance rules (CRITICAL):**

계단 시작/끝이 벽이나 슬래브에 바로 붙으면 캐릭터가 끼이거나 점프해야 하는 상황이 발생한다.

| 위치 | 최소 여유 공간 | 설명 |
|------|---------------|------|
| Run 시작/끝 | 1~1.5m 평탄 공간 | 계단 진입/도착 지점에 평탄한 랜딩 확보 |
| 스위치백 중간 랜딩 | 1.5m 깊이 이상 | 방향 전환이 가능할 만큼 넉넉하게 |
| 슬래브 개구부 | 계단 투영 + 각 방향 1m | 머리가 걸리지 않도록 여유 확보 |
| 벽-계단 간격 | 0.5m 이상 | 계단실 벽과 계단 사이 간격 |

### 7.9 Multi-Story Building (층 반복 패턴)

다층 건물은 **1개 층을 완전 설계 → 층 반복 → 계단으로 연결**하는 순서로 구성한다.

**1개 층 구성 요소:**

| 요소 | 형태 | 설명 |
|------|------|------|
| 바닥 슬래브 | Cube {z:0.2} | 계단실 위치에 개구부(slab opening) 필요 |
| 외벽 | Cube {y:0.5} × 4면 | 문/창문 위치에 갭 |
| 내부 파티션 | Cube {y:0.2~0.5} | 방 분할, 문 포함 |
| 천장/상층 바닥 | 다음 층 슬래브가 겸함 | 최상층만 별도 천장 |

**층 반복 공식:**
```
N층 바닥 z = (N-1) × floor_height
N층 벽 z   = N층 바닥 z
N층 천장   = N+1층 바닥 (최상층은 별도 Cube)
```

**슬래브 개구부:**
- 계단실 투영 면적 + 각 방향 1m 여유
- 개구부는 해당 층 바닥 슬래브에서 계단실 영역만 제외하여 구현 (바닥을 여러 Cube로 분할)

**⚠ 벽·파티션 개구부 규칙 (MANDATORY):**

`graymap_spawn`에는 "벽에 문 뚫기" 기능이 없다. 개구부(문, 창문, 통로)가 필요한 벽은 **반드시 갭 전후로 분할된 여러 Cube로 지정**해야 한다. "문 2개", "창문 갭 4개씩" 같은 **추상적 지시는 금지** — 에이전트가 벽을 통째로 하나의 Cube로 생성하여 캐릭터가 이동할 수 없게 된다.

**원칙: 모든 벽·파티션·슬래브의 개구부는 분할된 Cube 목록으로 완전히 전개(fully expand)하여 지정한다.**

벽 분할 예시 — Y=0, X=0~20 벽에 문 2개 (Y=5~6.4, Y=12~13.4):
```
벽 구간1: {location:{x:0,y:0,z:0},  scale:{x:5,   y:0.5, z:5}}    ← X=0~5
벽 구간2: {location:{x:6.4,y:0,z:0}, scale:{x:5.6, y:0.5, z:5}}   ← X=6.4~12
벽 구간3: {location:{x:13.4,y:0,z:0},scale:{x:6.6, y:0.5, z:5}}   ← X=13.4~20
상부(문1): {location:{x:5,y:0,z:2.2}, scale:{x:1.4, y:0.5, z:2.8}} ← 문 위 잔여벽
상부(문2): {location:{x:12,y:0,z:2.2},scale:{x:1.4, y:0.5, z:2.8}} ← 문 위 잔여벽
```
→ 5개 Cube로 분할. "문 2개 있는 벽" ≠ Cube 1개.

슬래브 분할 예시 — 20×15m 바닥에 계단 개구부(X=8~13, Y=6~11):
```
슬래브A: {location:{x:0,y:0,z:0},  scale:{x:8,  y:15, z:0.2}}   ← 개구부 왼쪽
슬래브B: {location:{x:13,y:0,z:0}, scale:{x:7,  y:15, z:0.2}}   ← 개구부 오른쪽
슬래브C: {location:{x:8,y:0,z:0},  scale:{x:5,  y:6,  z:0.2}}   ← 개구부 앞
슬래브D: {location:{x:8,y:11,z:0}, scale:{x:5,  y:4,  z:0.2}}   ← 개구부 뒤
```
→ 4개 Cube로 분할. 개구부(X=8~13, Y=6~11)는 빈 공간.

**팀 빌드 시 Lead의 의무:**
- 프롬프트에 "문 N개" 대신 **분할된 Cube 목록을 직접 작성**하여 Builder에게 전달
- 각 Cube의 location, scale을 숫자로 명시 — Builder는 이 좌표를 그대로 사용
- 개구부 위치가 확정되지 않은 채 Builder를 스폰하지 말 것

**조립 순서:**
1. 1F 바닥(z=0) + 외벽 + 파티션 + 문 배치
2. 계단실 위치 결정 (파티션 문과 정렬 — §7.8 규칙 2)
3. 2F 바닥(z=floor_height) 배치, 계단실 위치에 개구부
4. 1F→2F Switchback 계단 배치 (§7.8)
5. 2F 외벽 + 파티션 반복
6. 추가 층은 3~5 반복
7. 최상층에 천장 슬래브 추가

### 7.10 Straight Access Stair (Platform/Catwalk Connection)

단일 높이 플랫폼(캣워크, 메자닌, 적재대 등)에 접근하는 직선 계단. Switchback이 필요 없는 경우(층고 ≤ 6m, 수평 공간 충분) 사용.

**Anatomy (side view):**
```
  z=H ─────────┬── Platform (Cube, z:0.2) ──
               │↗ Stair ascends
  z=0 ─────────┘
       y=0      y=run_depth
       (stair   (stair top = platform edge)
        bottom)
```

**Dimension formula (MANDATORY):**
```
Given: platform_height (H), stair_width (W)
  run_depth   = H × 1.2                    ← ~40° slope (comfortably under 44°)
  stair_scale = {x: W, y: run_depth, z: H}
```

**Connection rules (CRITICAL — #1 source of broken catwalk stairs):**

1. **상단 연결**: 계단 상단(y=run_depth, z=H)이 플랫폼 표면과 정확히 맞닿아야 함
   - 플랫폼의 edge Y좌표 = 계단 location.y + run_depth
   - 플랫폼 Z = 계단 location.z + H (- 플랫폼 두께 0.2m 이내)
2. **하단 접근**: 계단 시작점(y=0, z=0) 앞에 최소 1m 평탄 공간 확보
3. **좌우 여유**: 계단 양 옆에 최소 0.5m 이상 벽/구조물과 간격 유지
4. **방향 설정**: 계단이 향하는 방향(ascend direction)을 먼저 결정한 후 yaw 설정
   - +Y 방향 상승: yaw=0 (default)
   - -Y 방향 상승: yaw=180
   - +X 방향 상승: yaw=-90
   - -X 방향 상승: yaw=90

**Example — 5m 높이 캣워크, 2.5m 폭 계단 (동쪽 벽면, +Y 방향 상승):**

| Element | Type | Scale (x,y,z) | Location (상대) | Notes |
|---------|------|---------------|----------------|-------|
| Stair_East | Stairs | (2.5, 6, 5) | (wall_x - 2.5, y_start, 0) | run=6m, atan(5/6)=39.8° ✅ |
| CW_East | Cube | (3, 35, 0.2) | (wall_x - 3, y_cw_start, 5) | 캣워크 플랫폼 |

연결 검증: Stair top at y=y_start+6, z=5 → CW_East at z=5, y 범위가 y_start+6 포함 → ✅ 연속

**Copy-paste template (5m platform, 2.5m wide stair):**
```json
{"name": "Stair_Access", "type": "Stairs", "scale": {"x":2.5, "y":6, "z":5},
 "location": {"x":0, "y":0, "z":0}, "rotation": {"x":0, "y":0, "z":0}, "material": "Green"}
```
→ 상단 도착점: (x:0~2.5, y:6, z:5). 이 좌표에 플랫폼 edge가 맞닿아야 함.

**Common mistakes:**
- ❌ run_depth 미계산 (scale y=z로 설정 → 45° 초과, 걸을 수 없음)
- ❌ 계단 상단이 플랫폼 Y범위 바깥 → 도착해도 플랫폼에 못 올라감
- ❌ 계단을 벽에 붙여 배치하면서 폭 방향(scale.x) 확인 안 함 → 벽 관통
- ❌ 방향(yaw)을 고려하지 않아 플랫폼 반대편으로 상승

### 7.11 Industrial Catwalk / Elevated Walkway

창고, 공장, 물류 시설 등에서 사용하는 2층 보행로 패턴. 벽면 캣워크 + 횡단 브릿지 + 접근 계단 + 난간 + 지지 기둥으로 구성.

**구성 요소:**

| 요소 | Type | 스케일 예시 | 배치 규칙 |
|------|------|-----------|----------|
| 벽면 캣워크 | Cube | {x:3, y:길이, z:0.2} | 벽에서 안쪽으로, z=플랫폼높이 |
| 횡단 브릿지 | Cube | {x:실내폭, y:3, z:0.2} | 양쪽 캣워크 연결, z=플랫폼높이 |
| 접근 계단 | Stairs | {x:2.5, y:H×1.2, z:H} | §7.10 공식 적용. 상단이 캣워크 edge에 맞닿을 것 |
| 내측 난간 | Cube | {x:0.05, y:길이, z:1.0} | 캣워크 내측 가장자리, z=플랫폼높이 |
| 지지 기둥 | Cylinder | {x:0.4, y:0.4, z:H} | 캣워크 하부, 5~8m 간격 |

**조립 순서:**
1. 캣워크 플랫폼 배치 (양쪽 벽면 + 횡단 브릿지)
2. 지지 기둥 배치 (캣워크 하부, 등간격)
3. **접근 계단 배치** — §7.10 공식으로 run_depth 계산, 상단이 캣워크 Y범위 내에 도달하도록 위치 설정
4. 난간 배치 (캣워크 내측 + 브릿지 양측)
5. 연결 검증: 지면 → 계단 → 캣워크 → 브릿지 → 반대편 캣워크 동선 확인

**Example — 30×50m 창고, 5m 높이 캣워크:**
```json
// 서쪽 캣워크 (벽면)
{"name":"CW_West", "type":"Cube", "scale":{"x":3,"y":35,"z":0.2},
 "location":{"x":0,"y":5,"z":5}, "material":"Yellow"}

// 서쪽 접근 계단 (+Y 방향 상승, 캣워크 남단에 연결)
{"name":"Stair_West", "type":"Stairs", "scale":{"x":2.5,"y":6,"z":5},
 "location":{"x":0.25,"y":-1,"z":0}, "rotation":{"x":0,"y":0,"z":0}, "material":"Green"}
// → 상단 도착: y=-1+6=5, z=5 → CW_West는 y=5에서 시작 → 정확히 연결 ✅

// 동쪽 접근 계단 (-Y 방향 상승, 캣워크 북단에 연결)
{"name":"Stair_East", "type":"Stairs", "scale":{"x":2.5,"y":6,"z":5},
 "location":{"x":27.5,"y":46,"z":0}, "rotation":{"x":0,"y":0,"z":180}, "material":"Green"}
// → yaw=180이므로 -Y방향 상승: 상단 y=46-6=40, z=5 → CW_East y범위 내 ✅

// 횡단 브릿지
{"name":"CW_Cross", "type":"Cube", "scale":{"x":24,"y":3,"z":0.2},
 "location":{"x":3,"y":23,"z":5}, "material":"Yellow"}
```

**⚠ 계단-캣워크 연결 체크리스트:**
- [ ] run_depth = platform_height × 1.2 로 계산했는가?
- [ ] 계단 상단 Y좌표가 캣워크 Y범위 안에 있는가?
- [ ] 계단 상단 Z = 캣워크 Z (±0.2m 이내)?
- [ ] 계단 하단에 1m+ 평탄 공간이 있는가?
- [ ] 계단이 벽이나 랙과 겹치지 않는가?
- [ ] 양쪽 계단의 yaw가 올바른 상승 방향인가?

---

## 8. Generation Process

1. **Intent Analysis**: Extract purpose, atmosphere, scale. If image attached, analyze proportions.
2. **Floor Plan Structural Analysis** (REQUIRED when floor plan/drawing is provided):

   Before coordinate mapping, read the drawing as a **structural blueprint** — not just a proportion reference.

   **Procedure:**
   1. **Identify every wall segment** and classify each as: solid wall, glass/window wall, partial wall (with opening), or absent (open side).
   2. **Identify every opening** (doors, archways, passages) — mark position, approximate size, and which wall it belongs to.
   3. **Identify interior partitions** — distinguish internal dividers from exterior walls. Internal partitions separate zones within the room; exterior walls define the boundary.
   4. **Identify labeled or implied materials** — line style, color, hatching, or annotations that indicate material (e.g., blue line = glass, thick line = concrete).
   5. **Produce a Wall Table:**

      | Wall | Side | Type | Material | Openings |
      |------|------|------|----------|----------|
      | North | top (−Y) | Solid + Door | Concrete | 2.5m door center |
      | East | right (+X) | Solid + Door | Concrete | 1.4m door |
      | South | bottom (+Y) | Solid | Concrete | None |
      | West | left (−X) | Solid | Concrete | None |
      | Interior | x≈14m | Glass partition | Glass | None |

   **Conflict resolution rule:**
   - When the text description and the drawing disagree, **the drawing takes priority** for structural layout (wall types, openings, partitions).
   - Text description takes priority for **atmosphere, material names, and non-structural details** not depicted in the drawing.
   - If ambiguity remains after applying this rule, ask the user before proceeding.

3. **Floor Plan Coordinate Mapping** (REQUIRED when image/floor plan is provided):

   2D floor plans use a fixed mapping to 3D coordinates:

   | Floor Plan Direction | 3D Axis |
   |----------------------|---------|
   | Top (↑)              | −Y      |
   | Bottom (↓)           | +Y      |
   | Left (←)             | −X      |
   | Right (→)            | +X      |

   **Procedure:**
   1. Identify key landmarks on the floor plan (entry door, windows, major furniture) and their 2D positions (top/bottom/left/right).
   2. Convert each landmark to 3D coordinates using the mapping table above.
   3. Present the converted coordinate layout to the user for confirmation before proceeding.

   > **Why this step exists:** Without explicit mapping, the 2D→3D conversion is ambiguous and can produce a mirrored layout. Always confirm before placement.

4. **Pattern Selection**: Choose organization pattern, plan flow paths, reference spatial recipes (section 7).
5. **Opening Expansion (MANDATORY)**: Convert ALL abstract opening descriptions into explicit split-Cube lists BEFORE passing to Builder agents or placing primitives:

   **What to expand:**
   - "문 N개 있는 벽" → N+1 wall segments + N lintel cubes (with exact coordinates)
   - "창문 갭 N개" → N+1 wall segments + N sill/lintel cubes
   - "개구부 제외한 슬래브" → 3~4 slab segments surrounding the opening
   - "통로", "아치", "입구 갭" → same treatment as doors

   **Expansion rule:** Every wall/partition/slab that contains an opening MUST be decomposed into a numbered list of Cubes with explicit `location` and `scale` values. Abstract descriptions like "문 2개", "창문 갭 4개씩", "개구부 제외" are **PROHIBITED** in Builder prompts — they will be interpreted as solid geometry.

   **Procedure:**
   1. List every wall/partition that needs an opening (from floor plan or design spec)
   2. For each wall, determine opening positions (door/window center Y or X coordinate)
   3. Calculate split segments: segment_before + gap + segment_after (+ lintel above door-height gaps)
   4. Write out each segment as a Cube with numeric location/scale
   5. Include the expanded Cube list in the Builder prompt — NOT the abstract description

   > **Why this step exists:** `graymap_spawn` is a coordinate-based primitive API. It has NO "punch hole in wall" operation. If a wall is specified as a single Cube, it will be a solid wall with no openings, making the space impassable.

6. **Circulation-First Layout**: Before placing ANY primitives, fully design the circulation path on paper:

   **Step A — Define waypoints (ordered list of positions the player walks through):**
   - Entry point (e.g., front door) → 1F main room → partition door → stair shaft → landing → 2F main room → ...
   - Each waypoint has: name, XY position, Z height, and connected waypoints
   - Every waypoint must be reachable from the previous one without jumping or clipping through geometry

   **Step B — Verify stair-to-door connectivity (CRITICAL for multi-story):**
   - For each stair: where does the player arrive at the top? (exact XY + Z)
   - Is there a door/opening at that arrival point leading to the destination room?
   - If using switchback stairs: the LANDING (not the top of the final run) must connect to the partition door
   - Draw the path: stair bottom → landing → door → room. If any segment is blocked by a wall, redesign before placing.

   **Step C — Validate vertical transitions:**
   - Stair top-end XY must fall inside the upper floor's slab opening (otherwise player hits ceiling)
   - Slab opening must be large enough for BOTH stair runs + landing (for switchback)
   - No partition wall may cross between the stair arrival point and the nearest door

   **Step D — Confirm with adjacency table:**
   Create a table: `| From | To | Connection Type | Blocked By |`
   Every row must have "None" in the Blocked By column before proceeding to placement.
6. **Primitive Placement**: Follow section 6 guide, use section 5 human-scale dimensions, assign different colors per zone (MATERIAL RULE).
7. **Circulation & Quality Verification**: Run section 9 checklist. Use `capture_viewport` to visually inspect from player perspective.

---

## 9. Quality Verification Checklist

### Spatial Scale
- [ ] Combat spaces at least medium room (9x8m)? Boss rooms 25x25m+?
- [ ] Doors: S(1x2m) / M(1.4x2.2m) / L(2.5x3m)?
- [ ] Corridors: S(2.5m) / M(4m) / L(7m) width?
- [ ] Ceiling ≥ 3.5m? Wall thickness 0.5m?

### Flow & Character Abilities
- [ ] **⚠ CLEARANCE CHECK**: Every passable space ≥ 1m wide × 2m tall? (doors, stair entries, landings, gaps between geometry)
- [ ] All intended areas reachable from start?
- [ ] **Circulation path unobstructed?** Entry → interior doors → stairs all connected without wall blockage?
- [ ] **Interior openings aligned with entry?** Openings on the same axis as the entry point they connect to?
- [ ] **Stair top under floor opening?** Each stair's top-end XY falls inside the upper floor's hole — no ceiling blockage?
- [ ] Dead-end branches have rewards?
- [ ] Gap widths match difficulty? (easy ≤3m, normal 3.5-5m, hard 5-11m)
- [ ] Heights match abilities? (hurdle ≤2m, jump ≤3.1m, double jump ≤4m, >4m needs Ramp)
- [ ] Falls >15m have railings or danger indicators?

### Stair Placement Checklist (per staircase)
- [ ] **⚠ Run depth calculated?** run_depth = height × 1.2 (≈40° slope) 공식으로 계산했는가? scale y를 z와 동일하게 설정하지 않았는가?
- [ ] **⚠ Stair-to-door clearance ≥ 1m?** Between the stair body and the partition door, is there at least 1m × 2m of unobstructed space for the character to pass through?
- [ ] **Arrival-to-door path clear?** From stair top (or landing), can the player walk to the nearest door WITHOUT crossing any wall/partition?
- [ ] **Landing aligned with door?** (Switchback only) The landing's XY overlaps with the partition door opening — not offset to the opposite end.
- [ ] **Slab opening covers full stair footprint?** For switchback: opening must cover both runs + landing. For straight: opening covers the full run length.
- [ ] **No dead-end landings?** Every landing/arrival platform has at least one exit (door, corridor, or next stair run).
- [ ] **Landing clearance?** Run 시작/끝에 1~1.5m 평탄 공간, 중간 랜딩 깊이 1.5m+, 슬래브 개구부 각 방향 +1m, 벽-계단 간격 0.5m+?
- [ ] **Run height = floor_height / num_runs?** Each run in a switchback rises exactly half the floor height (e.g., 1.75m for 3.5m floor).
- [ ] **Opposite run directions?** Switchback runs face 180° apart (e.g., yaw=0 and yaw=180).
- [ ] **Walk the full path mentally:** Ground floor entry → partition door → stair shaft → Run1 → Landing → (exit to room OR Run2) → upper floor. Every segment passable?
- [ ] **⚠ Footplate at floating edges?** 계단의 시작 변(bottom)과 종료 변(top) 각각에 대해: 바닥 슬래브·랜딩·플랫폼에 맞닿아 있는가? 아니면 허공인가? 허공이면 발판(Cube, width=stair width, depth≥1m, thickness=0.2m)이 있는가?

### Platform/Catwalk Stair Connection Checklist (§7.10, §7.11)
- [ ] **⚠ 상단 연결**: 계단 상단 Y좌표(location.y + run_depth 또는 yaw=180일 때 location.y - run_depth)가 플랫폼 Y범위 내에 있는가?
- [ ] **⚠ 상단 Z 일치**: 계단 상단 Z(location.z + height)와 플랫폼 Z가 ±0.2m 이내로 일치하는가?
- [ ] **하단 접근 공간**: 계단 시작점 앞에 1m+ 평탄 공간이 있는가? (벽, 랙 등에 막히지 않는가?)
- [ ] **벽/구조물 비관통**: 계단 폭(scale.x)이 벽이나 인접 구조물과 겹치지 않는가?
- [ ] **방향(yaw) 정확성**: 계단 상승 방향이 플랫폼이 있는 쪽을 향하는가?
- [ ] **⚠ Footplate at floating edges?** 계단 하단이 지면 슬래브 위에 있는가? 상단이 캣워크 표면에 맞닿는가? 어느 쪽이든 허공이면 발판(width=stair width, depth≥1m) 추가했는가?

### Opening Specification (Walls, Partitions, Slabs)
- [ ] **⚠ No abstract openings in Builder prompts?** Search for "문", "갭", "개구부", "통로", "창문" — every occurrence MUST be followed by split-Cube coordinates, NOT left as a verbal description
- [ ] **Every wall with doors is multi-Cube?** A wall containing N doors = at least N+1 wall Cubes + N lintel Cubes. A single Cube spanning the full wall length = solid wall = FAIL
- [ ] **Every slab with openings is multi-Cube?** Floor slabs with stair/elevator openings must be 3~4 Cubes surrounding the void. A single full-span slab = no opening = FAIL
- [ ] **Door gaps ≥ 1m wide × 2m tall?** Each gap between wall segments meets minimum clearance
- [ ] **Lintel cubes present above door gaps?** The space above each door gap (from door top to ceiling) is filled with a wall Cube

### Design Intent
- [ ] Shape language matches emotion? (safe=curves, danger=pointed)
- [ ] Weenie/landmarks visible from key positions?
- [ ] Birth-Canal at new area entries?
- [ ] Different material palettes per zone?

### Technical Spec
- [ ] All values in meters?
- [ ] type: Cube/Cylinder/QuarterCylinder/Ramp/Stairs?
- [ ] material: one of 10 colors?
- [ ] Different colors per structural group?
- [ ] All objects named meaningfully? All values are numbers?

### ⚠ Parameter Integrity (ALL Builds)
- [ ] **⚠ No default-scale actors?** `get_level_actors`로 모든 액터의 scale 확인. scale이 `{1,1,1}` (기본값)인 오브젝트가 있으면 **즉시 FAIL** — 파라미터 누락 의심. 의도적으로 1×1×1m인 경우는 오브젝트 이름이나 용도로 판별
- [ ] **⚠ Ramp/Stairs rotation 검증?** 각 Ramp/Stairs의 `rotation.z`(yaw)가 의도한 경사/상승 방향과 일치하는지 방향 표 대조. 특히 도머 지붕, 입구 계단 등 방향이 중요한 오브젝트를 우선 확인
- [ ] **Scale 합리성 검증?** 벽 두께(0.3~0.5m), 바닥 두께(0.2m), 기둥 지름(0.3~1.0m) 등 구조 요소의 scale이 합리적 범위 내인지 확인

### ⚠ Coordinate Verification (Team Builds Only)
- [ ] **All Builder folders at correct base position?** Pick 1 actor per folder, verify world position = base_location × 100 + relative offset × 100 (± 10cm tolerance)
- [ ] **No orphan actors at origin?** No actors at (0, 0, 0) that should be at base_location — indicates base_location was not applied
- [ ] **Cross-folder alignment?** Actors from different Builder folders that should be adjacent are actually adjacent (e.g., wall bottom aligns with floor top)
- [ ] **No duplicate builds?** No leftover actors from previous failed attempts at different coordinates
