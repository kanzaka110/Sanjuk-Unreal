"""Build Sprint Start Transition detection chain in UpdateVariables.

Mirror of Sprint End Phase 1 (per Inspector prescription).

Logic:
  bCurrentPendingSprinting = (PendingWalkMode == SBWalk_Sprinting)
  bJustEnteredSprint       = bCurrentPendingSprinting AND NOT bPrevPendingSprinting
  if bJustEnteredSprint:
      SprintStartTransitionRemain = SprintStartTransitionDuration
  else:
      SprintStartTransitionRemain = FMax(0, SprintStartTransitionRemain - DeltaTime)
  bIsSprintStartTransition = (SprintStartTransitionRemain > 0)
  bPrevPendingSprinting    = bCurrentPendingSprinting   # last

Anchor: VariableSet_75 (Set bIsSprintEndTransition).then is currently empty.
We chain from VariableSet_75.then -> new Branch.

Position offset: y ~ 7000~7600 (below Sprint End chain @ 6400~6900).
"""

import json, requests, time

URL = "http://localhost:9316/mcp"
ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "UpdateVariables"

req_id = [100]

def call(action, params):
    req_id[0] += 1
    payload = {
        "jsonrpc": "2.0",
        "id": req_id[0],
        "method": "tools/call",
        "params": {
            "name": "blueprint_query",
            "arguments": {"action": action, "params": params},
        },
    }
    r = requests.post(URL, json=payload, timeout=30)
    js = r.json()
    if "result" in js:
        content = js["result"].get("content", [])
        if content:
            t = content[0].get("text", "")
            try:
                return json.loads(t)
            except Exception:
                return {"raw": t}
    return js


def add_node(node_type, position, **kwargs):
    params = {
        "asset_path": ASSET,
        "graph_name": GRAPH,
        "node_type": node_type,
        "position": position,
    }
    params.update(kwargs)
    return call("add_node", params)


def connect(from_node, from_pin, to_node, to_pin):
    return call("connect_pins", {
        "asset_path": ASSET,
        "graph_name": GRAPH,
        "source_node": from_node,
        "source_pin": from_pin,
        "target_node": to_node,
        "target_pin": to_pin,
    })


def set_pin_default(node, pin, value):
    return call("set_pin_default", {
        "asset_path": ASSET,
        "graph_name": GRAPH,
        "node_id": node,
        "pin_name": pin,
        "default_value": value,
    })


results = []

# === Build nodes ===
# Layout (y ~ 7000 ~ 7600, below Sprint End chain):
#   row A (y=7008): VG PendingWalkMode | EnumEquality | VG bPrev | NOT | AND
#   row B (y=7008): Branch
#   row C (y=7008): SET Remain (true)
#   row D (y=7104): SET Remain (false)  [FMax stack to the left]
#   row E (y=7008): SET bIsSprintStartTransition
#   row F (y=7104): SET bPrevPendingSprinting

# Node 1: Get PendingWalkMode
r = add_node("VariableGet", [144, 7008], variable_name="PendingWalkMode")
results.append(("VG_PWM", r)); print("VG_PWM:", r)

# Node 2: EnumEquality (PendingWalkMode == SBWalk_Sprinting)
r = add_node("EnumEquality", [400, 7008])
results.append(("ENUMEQ", r)); print("ENUMEQ:", r)

# Node 3: Get bPrevPendingSprinting
r = add_node("VariableGet", [144, 7152], variable_name="bPrevPendingSprinting")
results.append(("VG_PREV", r)); print("VG_PREV:", r)

# Node 4: NOT Boolean
r = add_node("CallFunction", [640, 7152], function_name="Not_PreBool", target_class="/Script/Engine.KismetMathLibrary")
results.append(("NOT_PREV", r)); print("NOT_PREV:", r)

# Node 5: AND (curr AND NOT prev)
r = add_node("CallFunction", [880, 7008], function_name="BooleanAND", target_class="/Script/Engine.KismetMathLibrary")
results.append(("AND_ENTER", r)); print("AND_ENTER:", r)

# Node 6: Branch (Sprint Start detection)
r = add_node("Branch", [1120, 7008])
results.append(("BR_START", r)); print("BR_START:", r)

# Node 7: Get SprintStartTransitionDuration
r = add_node("VariableGet", [1300, 6940], variable_name="SprintStartTransitionDuration")
results.append(("VG_DUR", r)); print("VG_DUR:", r)

# Node 8: SET Remain (true branch) = Duration
r = add_node("VariableSet", [1500, 7008], variable_name="SprintStartTransitionRemain")
results.append(("SET_REM_T", r)); print("SET_REM_T:", r)

# Node 9: Get SprintStartTransitionRemain (for false branch read)
r = add_node("VariableGet", [1080, 7280], variable_name="SprintStartTransitionRemain")
results.append(("VG_REM_F", r)); print("VG_REM_F:", r)

# Node 10: Get Delta Time
r = add_node("VariableGet", [1080, 7360], variable_name="Delta Time")
results.append(("VG_DT", r)); print("VG_DT:", r)

# Node 11: Subtract (Remain - DT)
r = add_node("CallFunction", [1280, 7320], function_name="Subtract_DoubleDouble", target_class="/Script/Engine.KismetMathLibrary")
results.append(("SUB_DT", r)); print("SUB_DT:", r)

# Node 12: FMax (Float)
r = add_node("CallFunction", [1440, 7320], function_name="FMax", target_class="/Script/Engine.KismetMathLibrary")
results.append(("FMAX", r)); print("FMAX:", r)

# Node 13: SET Remain (false branch) = FMax(0, Remain-DT)
r = add_node("VariableSet", [1640, 7152], variable_name="SprintStartTransitionRemain")
results.append(("SET_REM_F", r)); print("SET_REM_F:", r)

# Node 14: Get SprintStartTransitionRemain (for >0 read after set)
r = add_node("VariableGet", [1880, 7280], variable_name="SprintStartTransitionRemain")
results.append(("VG_REM_FINAL", r)); print("VG_REM_FINAL:", r)

# Node 15: Greater (Remain > 0)
r = add_node("CallFunction", [2080, 7280], function_name="Greater_DoubleDouble", target_class="/Script/Engine.KismetMathLibrary")
results.append(("GT_ZERO", r)); print("GT_ZERO:", r)

# Node 16: SET bIsSprintStartTransition
r = add_node("VariableSet", [2280, 7008], variable_name="bIsSprintStartTransition")
results.append(("SET_FLAG", r)); print("SET_FLAG:", r)

# Node 17: SET bPrevPendingSprinting (cache for next tick)
r = add_node("VariableSet", [2540, 7008], variable_name="bPrevPendingSprinting")
results.append(("SET_PREV", r)); print("SET_PREV:", r)

# Save node IDs
node_map = {}
for tag, r in results:
    nid = r.get("node_id") or r.get("id")
    node_map[tag] = nid
    print(f"  {tag} = {nid}")

# Save mapping
with open('C:/Dev/Sanjuk-Unreal/Saved/Logs/sprint_start_node_map.json', 'w') as f:
    json.dump(node_map, f, indent=2)

print("\n=== node_map saved ===")
print(json.dumps(node_map, indent=2))
