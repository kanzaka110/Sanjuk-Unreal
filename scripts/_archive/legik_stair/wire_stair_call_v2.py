"""v2: Thread-safe 우회.
   1. 변수 CapturedActorZ 추가
   2. EventGraph에 BlueprintUpdateAnimation 이벤트 추가 → Z 캡처 → Set CapturedActorZ
   3. BlueprintThreadSafeUpdateAnimation의 잘못된 노드 정리 + CapturedActorZ 참조로 교체
"""
import json
import subprocess

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"


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


def pp(label, res):
    ok = res.get("success", False) or ("id" in res)
    print(f"  [{'OK' if ok else 'FAIL'}] {label}"
          + ("" if ok else f" | {res}"))


# =========================================================================
# A. BlueprintThreadSafeUpdateAnimation 잘못 추가된 노드 삭제
# =========================================================================
print("=== A. 잘못 추가된 노드 정리 ===")
TSU = "BlueprintThreadSafeUpdateAnimation"
# ids from previous run
BAD_IDS = ["K2Node_CallFunction_2", "K2Node_CallFunction_3", "K2Node_CallFunction_5"]
for nid in BAD_IDS:
    res = call("remove_node", {"asset_path": BP, "graph_name": TSU, "node_id": nid})
    pp(f"remove {nid}", res)

# UpdateStairAlpha 호출 노드(K2Node_CallFunction_6)는 유지하되 입력만 다시 연결

# =========================================================================
# B. CapturedActorZ 변수 추가
# =========================================================================
print("\n=== B. CapturedActorZ 변수 추가 ===")
res = call("add_variable", {
    "asset_path": BP,
    "name": "CapturedActorZ",
    "type": "float",
    "default_value": "0.0",
    "category": "StairDetection",
    "tooltip": "게임 스레드 BlueprintUpdateAnimation에서 캡처한 액터 Z. Thread-safe 업데이트에서 읽기용.",
})
pp("add CapturedActorZ", res)

# =========================================================================
# C. EventGraph에 BlueprintUpdateAnimation 이벤트 추가
# =========================================================================
print("\n=== C. Event Blueprint Update Animation 이벤트 추가 ===")
res = call("add_event_node", {
    "asset_path": BP,
    "graph_name": "EventGraph",
    "event_name": "BlueprintUpdateAnimation",
    "position": {"x": -800, "y": 2000},
})
pp("add event", res)
evt_id = res.get("id")
if not evt_id:
    # 이미 있으면 검색
    g = call("get_graph_data", {"asset_path": BP, "graph_name": "EventGraph"})
    for n in g.get("nodes", []):
        if "Update Animation" in n.get("title", "") and "Initialize" not in n.get("title", ""):
            evt_id = n.get("id")
            break
    print(f"  재사용 event id = {evt_id}")

# EventGraph에 나머지 노드들
print("\n  이벤트 체인 구축")


def add_ev_node(func, cls_path, x, y, alias=""):
    r = call("add_node", {
        "asset_path": BP, "graph_name": "EventGraph",
        "node_type": "CallFunction",
        "function_name": func, "function_class": cls_path,
        "position": {"x": x, "y": y},
    })
    pp(alias or func, r)
    return r.get("id")


get_actor = add_ev_node("GetOwningActor", "/Script/Engine.AnimInstance", -600, 2000, "GetOwningActor")
get_loc = add_ev_node("K2_GetActorLocation", "/Script/Engine.Actor", -350, 2000, "GetActorLocation")
break_vec = add_ev_node("BreakVector", "/Script/Engine.KismetMathLibrary", -100, 2000, "BreakVector")

set_z = call("add_node", {
    "asset_path": BP, "graph_name": "EventGraph",
    "node_type": "VariableSet",
    "variable_name": "CapturedActorZ",
    "position": {"x": 200, "y": 2000},
})
pp("Set CapturedActorZ", set_z)
set_z_id = set_z.get("id")


def conn(graph, sn, sp, tn, tp):
    r = call("connect_pins", {
        "asset_path": BP, "graph_name": graph,
        "source_node": sn, "source_pin": sp,
        "target_node": tn, "target_pin": tp,
    })
    ok = r.get("success", False)
    print(f"  [{'OK' if ok else 'FAIL'}] ({graph}) {sn}.{sp} -> {tn}.{tp}"
          + ("" if ok else f" | {r}"))


# EventGraph 연결
print("\n  EventGraph 연결")
conn("EventGraph", get_actor, "ReturnValue", get_loc, "self")
conn("EventGraph", get_loc, "ReturnValue", break_vec, "InVec")
conn("EventGraph", break_vec, "Z", set_z_id, "CapturedActorZ")
# exec: Event → Set
conn("EventGraph", evt_id, "then", set_z_id, "execute")

# =========================================================================
# D. BlueprintThreadSafeUpdateAnimation에서 Get CapturedActorZ → UpdateStairAlpha
# =========================================================================
print("\n=== D. TSU에 Get CapturedActorZ 추가 + 연결 ===")
get_cz = call("add_node", {
    "asset_path": BP, "graph_name": TSU,
    "node_type": "VariableGet",
    "variable_name": "CapturedActorZ",
    "position": {"x": 1500, "y": 350},
})
pp("Get CapturedActorZ", get_cz)
get_cz_id = get_cz.get("id")

# UpdateStairAlpha 호출 노드 (이전 run에서 생성된 K2Node_CallFunction_6)
STAIR_CALL = "K2Node_CallFunction_6"

# 데이터 연결
conn(TSU, get_cz_id, "CapturedActorZ", STAIR_CALL, "CurrentCapsuleZ")

# Entry의 DeltaTime 연결
conn(TSU, "K2Node_FunctionEntry_0", "DeltaTime", STAIR_CALL, "DeltaTime")

# =========================================================================
# E. 컴파일
# =========================================================================
print("\n=== E. 컴파일 ===")
res = call("compile_blueprint", {"asset_path": BP})
print(f"  success = {res.get('success')}, status = {res.get('status')}")
errors = res.get("errors", [])
if errors:
    print(f"  errors ({len(errors)}):")
    for e in errors[:10]:
        print(f"    [{e.get('node_id','?')}] {e.get('message','')[:120]}")
