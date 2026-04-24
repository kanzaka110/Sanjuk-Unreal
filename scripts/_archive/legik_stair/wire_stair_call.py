"""BlueprintThreadSafeUpdateAnimation에 UpdateStairAlpha 호출 연결.
   CurrentCapsuleZ = GetOwningActor().GetActorLocation().Z"""
import json
import subprocess

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "BlueprintThreadSafeUpdateAnimation"


def call(action: str, args: dict) -> dict:
    payload = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {"name": "blueprint_query",
                   "arguments": {"action": action, **args}}
    }
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", MCP,
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=30)
    d = json.loads(r.stdout)
    txt = d.get("result", {}).get("content", [{}])[0].get("text", "")
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"_raw": txt}


# === 1. 현재 노드 확인: 마지막 Set Delta Time 노드 ID 찾기 ===
print("=== 현재 그래프 노드 ===")
res = call("get_graph_data", {"asset_path": BP, "graph_name": GRAPH})
nodes = res.get("nodes", [])
set_delta_time_id = None
last_exec_node = None
for n in nodes:
    cls = n.get("class", "")
    title = n.get("title", "")
    nid = n.get("id")
    print(f"  {cls:30s} id={nid} title='{title[:40]}'")
    if cls == "K2Node_VariableSet" and "Delta Time" in title:
        set_delta_time_id = nid
    if cls == "K2Node_CallFunction" and "Update Target Rotation" in title:
        last_exec_node = nid

print(f"\n  Set Delta Time = {set_delta_time_id}")
print(f"  Update Target Rotation = {last_exec_node}")

# === 2. 새 노드들 추가 ===
print("\n=== 노드 추가 ===")


def add_call(func, cls_path, x, y, alias=""):
    res = call("add_node", {
        "asset_path": BP, "graph_name": GRAPH,
        "node_type": "CallFunction",
        "function_name": func,
        "function_class": cls_path,
        "position": {"x": x, "y": y},
    })
    nid = res.get("id")
    print(f"  [{alias or func}] → {nid}")
    return nid


# Get Owning Actor
get_actor = add_call("GetOwningActor", "/Script/Engine.AnimInstance", 1000, 400, "GetOwningActor")
# Get Actor Location
get_loc = add_call("K2_GetActorLocation", "/Script/Engine.Actor", 1250, 400, "GetActorLocation")
# Break Vector
break_vec = add_call("BreakVector", "/Script/Engine.KismetMathLibrary", 1500, 400, "BreakVector")
# Call UpdateStairAlpha
call_stair = call("add_node", {
    "asset_path": BP, "graph_name": GRAPH,
    "node_type": "CallFunction",
    "function_name": "UpdateStairAlpha",
    "position": {"x": 1800, "y": 300},
})
call_stair_id = call_stair.get("id")
print(f"  [UpdateStairAlpha call] → {call_stair_id}")

# === 3. 연결 ===
print("\n=== 연결 ===")


def connect(sn, sp, tn, tp):
    r = call("connect_pins", {
        "asset_path": BP, "graph_name": GRAPH,
        "source_node": sn, "source_pin": sp,
        "target_node": tn, "target_pin": tp,
    })
    ok = r.get("success", False)
    mark = "[OK]" if ok else "[FAIL]"
    print(f"  {mark} {sn}.{sp} -> {tn}.{tp}" + ("" if ok else f" | {r}"))


# 데이터: Actor → Location → Break → Z
connect(get_actor, "ReturnValue", get_loc, "self")
connect(get_loc, "ReturnValue", break_vec, "InVec")
# UpdateStairAlpha 입력
# Entry의 DeltaSeconds 찾기
entry_id = None
for n in nodes:
    if n.get("class") == "K2Node_FunctionEntry":
        entry_id = n.get("id")
        break
connect(entry_id, "DeltaSeconds", call_stair_id, "DeltaTime")
connect(break_vec, "Z", call_stair_id, "CurrentCapsuleZ")

# exec: Update Target Rotation → UpdateStairAlpha → Set Delta Time
# 먼저 기존 연결 (Update Target Rotation → Set Delta Time) 끊기
call("disconnect_pins", {
    "asset_path": BP, "graph_name": GRAPH,
    "source_node": last_exec_node, "source_pin": "then",
    "target_node": set_delta_time_id, "target_pin": "execute",
})
# Update Target Rotation → UpdateStairAlpha
connect(last_exec_node, "then", call_stair_id, "execute")
# UpdateStairAlpha → Set Delta Time
connect(call_stair_id, "then", set_delta_time_id, "execute")

# === 4. 컴파일 ===
print("\n=== 컴파일 ===")
res = call("compile_blueprint", {"asset_path": BP})
print(f"  {res}")
