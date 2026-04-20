"""Final: UpdateStairAlpha를 EventGraph의 BlueprintUpdateAnimation에서 호출.
   BlueprintThreadSafeUpdateAnimation의 잘못 연결된 호출 원복.
"""
import json
import subprocess

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"


def call(action, args):
    payload = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
               "params": {"name": "blueprint_query",
                          "arguments": {"action": action, **args}}}
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", MCP,
         "-H", "Content-Type: application/json", "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=30)
    d = json.loads(r.stdout)
    txt = d.get("result", {}).get("content", [{}])[0].get("text", "")
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"_raw": txt}


def pp(label, res):
    ok = res.get("success", False) or ("id" in res)
    print(f"  [{'OK' if ok else 'FAIL'}] {label}"
          + ("" if ok else f" | {res}"))


# ==== A. TSU에서 UpdateStairAlpha 호출 노드 제거 + 원래 exec 복구 ====
print("=== A. BlueprintThreadSafeUpdateAnimation 원복 ===")
TSU = "BlueprintThreadSafeUpdateAnimation"

# Get CapturedActorZ Get 노드도 제거
for nid in ("K2Node_CallFunction_6", "K2Node_VariableGet_0"):
    r = call("remove_node", {"asset_path": BP, "graph_name": TSU, "node_id": nid})
    pp(f"remove {nid}", r)

# Update Target Rotation → Set Delta Time 복구
r = call("connect_pins", {
    "asset_path": BP, "graph_name": TSU,
    "source_node": "K2Node_CallFunction_0", "source_pin": "then",
    "target_node": "K2Node_VariableSet_2", "target_pin": "execute",
})
pp("restore UpdateTargetRotation -> SetDeltaTime", r)

# ==== B. EventGraph에 UpdateStairAlpha 호출 추가 ====
print("\n=== B. EventGraph에 UpdateStairAlpha 호출 ===")

# 기존 이벤트/노드 ID 확인
g = call("get_graph_data", {"asset_path": BP, "graph_name": "EventGraph"})
evt_id = None
set_z_id = None
break_vec_id = None
for n in g.get("nodes", []):
    cls = n.get("class", "")
    title = n.get("title", "")
    if cls == "K2Node_Event" and "Update Animation" in title and "Initialize" not in title:
        evt_id = n.get("id")
    if cls == "K2Node_VariableSet" and "CapturedActorZ" in title:
        set_z_id = n.get("id")
    if cls == "K2Node_CallFunction" and "Break" in title:
        break_vec_id = n.get("id")

print(f"  event = {evt_id}, set_z = {set_z_id}, break_vec = {break_vec_id}")

# UpdateStairAlpha 호출 노드 추가 — Set CapturedActorZ 다음
r = call("add_node", {
    "asset_path": BP, "graph_name": "EventGraph",
    "node_type": "CallFunction",
    "function_name": "UpdateStairAlpha",
    "position": {"x": 500, "y": 2000},
})
pp("add UpdateStairAlpha call", r)
stair_call = r.get("id")

# exec: Set CapturedActorZ.then → UpdateStairAlpha.execute
r = call("connect_pins", {
    "asset_path": BP, "graph_name": "EventGraph",
    "source_node": set_z_id, "source_pin": "then",
    "target_node": stair_call, "target_pin": "execute",
})
pp("SetCapturedActorZ -> UpdateStairAlpha (exec)", r)

# 데이터: DeltaTimeX (Event pin) → DeltaTime, BreakVec.Z → CurrentCapsuleZ
r = call("connect_pins", {
    "asset_path": BP, "graph_name": "EventGraph",
    "source_node": evt_id, "source_pin": "DeltaTimeX",
    "target_node": stair_call, "target_pin": "DeltaTime",
})
pp("Event.DeltaTimeX -> UpdateStairAlpha.DeltaTime", r)

r = call("connect_pins", {
    "asset_path": BP, "graph_name": "EventGraph",
    "source_node": break_vec_id, "source_pin": "Z",
    "target_node": stair_call, "target_pin": "CurrentCapsuleZ",
})
pp("BreakVec.Z -> UpdateStairAlpha.CurrentCapsuleZ", r)

# ==== C. 컴파일 ====
print("\n=== C. 컴파일 ===")
r = call("compile_blueprint", {"asset_path": BP})
print(f"  success = {r.get('success')}, status = {r.get('status')}")
for e in (r.get("errors") or [])[:10]:
    print(f"    [{e.get('node_id')}] {e.get('message','')[:120]}")
for w in (r.get("warnings") or [])[:5]:
    print(f"    WARN: {w.get('message','')[:120]}")

# ==== D. 저장 ====
print("\n=== D. 저장 ===")
r = call("save_asset", {"asset_path": BP})
print(f"  {r}")
