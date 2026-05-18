# Parallel Subagent Workflow Patterns

Workflow patterns for decomposing complex Unreal tasks into parallel MCP tool calls and subagents.
For concurrency limits, tool parallelization classes, and key rules, see CLAUDE.md.

---

## Workflow Pattern 1: Level Setup

**Trigger:** "set up a level", "build a level", "create a scene", "populate the level"

**Phase 1 — Survey** (lead, parallel read-only):
  get_level_actors + asset_search (meshes, materials, blueprints)

**Phase 2 — Execute** (≤3 subagents, ~15-30s each):
- Subagent A (Lighting): spawn DirectionalLight, SkyLight, Fog + set_property (~6 calls)
- Subagent B (Environment): spawn Floor, Walls + set_property for materials (~6-8 calls)
- Subagent C (Gameplay): spawn PlayerStart, pickup BPs + set_property (~4-6 calls)

**Phase 3 — Verify** (lead): get_level_actors + capture_viewport

---

## Workflow Pattern 2: Character Pipeline

**Trigger:** "set up a character", "create character pipeline", "character with movement and input"

**Phase 1 — Survey** (lead): asset_search (character BPs, anim BPs, input actions)

**Phase 2 — Execute** (≤3 subagents):
- Subagent A (Character Config): character create_data_asset + character_data set values + spawn + assign (~4-6 calls)
- Subagent B (Animation BP): anim_blueprint_modify — state machine, states, transitions, sequences (~6-8 calls)
- Subagent C (Input Bindings): enhanced_input — create actions, mapping context, bind keys, assign (~5-7 calls)

**Phase 3 — Verify** (lead): blueprint_query + asset_search

---

## Workflow Pattern 3: Blueprint Construction

**Trigger:** "create multiple blueprints", "set up blueprint classes", "build BP hierarchy"

**Key Rule:** Sequential within one BP, parallel across different BPs (up to 3 simultaneously). NEVER have two subagents modify the same Blueprint.

**Phase 1 — Survey** (lead): asset_search (existing BPs, avoid name collisions)

**Phase 2 — Execute:** One subagent per BP (max 3). Each: create BP + add components + add variables/functions + compile (~4-6 sequential calls)

**Phase 3 — Verify** (lead): blueprint_query per BP (parallel)

---

## Workflow Pattern 4: Scene Audit

**Trigger:** "audit the scene", "what's in the level", "analyze the level"

**No subagents needed.** Lead agent only, batch read-only calls in waves of 4:
- Wave 1: get_level_actors + asset_search (Blueprint) + get_output_log + capture_viewport
- Wave 2 (if needed): blueprint_query + asset_dependencies per item of interest

---

## Workflow Pattern 5: Material Pipeline

**Trigger:** "create materials", "set up materials", "assign materials"

**Phase 1 — Survey** (lead): asset_search (materials, textures) + get_level_actors

**Phase 2 — Create** (≤3 subagents if >3 materials): Each subagent creates material instance + sets parameters (~2-3 calls). If 6+ materials, batch in waves of 3.

**Phase 3 — Assign** (lead): material assign per actor, batch 4 at a time (sequential, safe to batch on different actors)

---

## Workflow Pattern 6: Asset Discovery

**Trigger:** "find all assets", "asset audit", "dependency analysis"

**No subagents needed.** Lead agent only:
- Wave 1: asset_search per type (StaticMesh, Material, Blueprint, Texture)
- Wave 2: asset_dependencies + asset_referencers per key asset (batch in groups of 4)

---

## Subagent Instructions Template

When spawning a subagent for Unreal MCP work, include these constraints in the prompt:

```
You are a subagent working on [SPECIFIC TASK].

Constraints:
- Make at most 8 sequential MCP tool calls (budget: ~30s total)
- Only modify objects assigned to you: [LIST SPECIFIC NAMES]
- Do NOT modify objects owned by other subagents
- Do NOT call open_level, delete_actors, or execute_script
- If a tool call fails, report the error — do not retry more than once
- If you finish early, report what was created/modified

Your specific tasks:
1. [Tool call 1 with exact parameters]
2. [Tool call 2 with exact parameters]
...
```
