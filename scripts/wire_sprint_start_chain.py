"""Wire connections for Sprint Start Transition detection chain."""

import json, requests

URL = "http://localhost:9316/mcp"
ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "UpdateVariables"

# Loaded node map (from build script)
NM = json.load(open('C:/Dev/Sanjuk-Unreal/Saved/Logs/sprint_start_node_map.json'))
print('Node map:', json.dumps(NM, indent=2))

# Anchor (Sprint End chain endpoint, has empty .then)
ANCHOR_SET_END = "K2Node_VariableSet_75"  # Set bIsSprintEndTransition

req_id = [300]

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
        c = js["result"].get("content", [])
        if c:
            t = c[0].get("text", "")
            try:
                return js["result"].get("isError"), json.loads(t)
            except Exception:
                return js["result"].get("isError"), {"raw": t}
    return True, js


def connect(src, src_pin, dst, dst_pin):
    err, r = call("connect_pins", {
        "asset_path": ASSET,
        "graph_name": GRAPH,
        "source_node": src,
        "source_pin": src_pin,
        "target_node": dst,
        "target_pin": dst_pin,
    })
    status = "FAIL" if err else "OK"
    print(f"  [{status}] {src}.{src_pin} -> {dst}.{dst_pin}")
    if err:
        print(f"     {r}")
    return not err


def set_pin_default(node, pin, value):
    err, r = call("set_pin_default", {
        "asset_path": ASSET,
        "graph_name": GRAPH,
        "node_id": node,
        "pin_name": pin,
        "default_value": value,
    })
    status = "FAIL" if err else "OK"
    print(f"  [{status}] set_pin_default {node}.{pin} = {value}")
    if err:
        print(f"     {r}")
    return not err


# ===== Data wiring (pure) =====
print("\n--- Data connections ---")

# 1. PendingWalkMode -> EnumEquality.A
connect(NM["VG_PWM"], "PendingWalkMode", NM["ENUMEQ"], "A")

# 2. EnumEquality.B = SBWalk_Sprinting (enum literal default)
set_pin_default(NM["ENUMEQ"], "B", "SBWalk_Sprinting")

# 3. bPrevPendingSprinting -> NOT.A
connect(NM["VG_PREV"], "bPrevPendingSprinting", NM["NOT_PREV"], "A")

# 4. EnumEquality.ReturnValue -> AND.A (current PendingSprinting)
connect(NM["ENUMEQ"], "ReturnValue", NM["AND_ENTER"], "A")

# 5. NOT.ReturnValue -> AND.B  (NOT prev)
connect(NM["NOT_PREV"], "ReturnValue", NM["AND_ENTER"], "B")

# 6. AND.ReturnValue -> Branch.Condition
connect(NM["AND_ENTER"], "ReturnValue", NM["BR_START"], "Condition")

# 7. SprintStartTransitionDuration -> SET_REM_T.SprintStartTransitionRemain (input value)
connect(NM["VG_DUR"], "SprintStartTransitionDuration", NM["SET_REM_T"], "SprintStartTransitionRemain")

# 8. SprintStartTransitionRemain (false branch read) -> SUB_DT.A
connect(NM["VG_REM_F"], "SprintStartTransitionRemain", NM["SUB_DT"], "A")

# 9. Delta Time -> SUB_DT.B
connect(NM["VG_DT"], "Delta Time", NM["SUB_DT"], "B")

# 10. SUB_DT.ReturnValue -> FMAX.B
connect(NM["SUB_DT"], "ReturnValue", NM["FMAX"], "B")

# 11. FMAX.A = 0 (literal) — leave default 0.0
set_pin_default(NM["FMAX"], "A", "0.0")

# 12. FMAX.ReturnValue -> SET_REM_F.SprintStartTransitionRemain
connect(NM["FMAX"], "ReturnValue", NM["SET_REM_F"], "SprintStartTransitionRemain")

# 13. SprintStartTransitionRemain (final read) -> GT_ZERO.A
connect(NM["VG_REM_FINAL"], "SprintStartTransitionRemain", NM["GT_ZERO"], "A")

# 14. GT_ZERO.B = 0.0
set_pin_default(NM["GT_ZERO"], "B", "0.0")

# 15. GT_ZERO.ReturnValue -> SET_FLAG.bIsSprintStartTransition
connect(NM["GT_ZERO"], "ReturnValue", NM["SET_FLAG"], "bIsSprintStartTransition")

# 16. EnumEquality.ReturnValue -> SET_PREV.bPrevPendingSprinting (curr value cached)
connect(NM["ENUMEQ"], "ReturnValue", NM["SET_PREV"], "bPrevPendingSprinting")


# ===== Exec wiring =====
print("\n--- Exec connections ---")

# 17. Anchor: VariableSet_75 (Sprint End SET).then -> Branch.execute
connect(ANCHOR_SET_END, "then", NM["BR_START"], "execute")

# 18. Branch.then -> SET_REM_T.execute (true)
connect(NM["BR_START"], "then", NM["SET_REM_T"], "execute")

# 19. Branch.else -> SET_REM_F.execute (false)
connect(NM["BR_START"], "else", NM["SET_REM_F"], "execute")

# 20. SET_REM_T.then -> SET_FLAG.execute
connect(NM["SET_REM_T"], "then", NM["SET_FLAG"], "execute")

# 21. SET_REM_F.then -> SET_FLAG.execute (same target — Branch convergence)
connect(NM["SET_REM_F"], "then", NM["SET_FLAG"], "execute")

# 22. SET_FLAG.then -> SET_PREV.execute
connect(NM["SET_FLAG"], "then", NM["SET_PREV"], "execute")

print("\n=== Wiring complete ===")
