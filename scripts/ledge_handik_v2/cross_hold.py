# v12b — TransitingToNextLedge(크로싱) 하강 에지 홀드 (UpdateStates)
# 실측: 크로싱 transit=0.3s vs 애님 2.5s → 절단. held = raw OR (prev AND bActive AND t<CrossHold AND NOT rawUnitMove)
# 새 이동(rawTransitMoving) 시 홀드 즉시 해제 → 반응성 보존. 롤백=VS_20 데이터(PA_5)+exec(VS_19.then→VS_20) 2링크.
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "UpdateStates"
KML = "KismetMathLibrary"
LOG = {"steps": [], "errors": []}


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:300])
    return json.loads(txt)


def harvest(o, tm):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tm[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v, tm)
    elif isinstance(o, list):
        for e in o:
            harvest(e, tm)


existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for name, typ, dv in (("LedgeCrossHoldTimer", "float", None), ("LedgeCrossHoldTime", "float", "2.2")):
    if name in existing:
        continue
    p = {"asset_path": ABP, "name": name, "type": typ, "category": "Ledge|TransitHold", "instance_editable": False}
    if dv:
        p["default_value"] = dv
    call("blueprint_query", "add_variable", p)
    LOG["steps"].append("var: " + name)

g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": G})
nodes = {n["id"]: n for n in g["nodes"]}
def pins(n): return {p["name"]: p for p in n.get("pins", [])}
def conn(n, pin): return (pins(n).get(pin, {}).get("connected_to") or [])
# 앵커: VS_20(Set TransitingToNextLedge ← PA_5), 선행 exec=VS_19.then, 후행=VS_20.then→VS_22
VS19 = "K2Node_VariableSet_19"
VS20 = "K2Node_VariableSet_20"
PA5 = "K2Node_PropertyAccess_5"   # GetLedgeMoveData.bTransitingToNextLedge (raw)
PA8 = "K2Node_PropertyAccess_8"   # IsTransitMoving (raw — 홀드 해제 조건)
BRK1 = "K2Node_BreakStruct_1"     # bActive
miss = [x for x in (VS19, VS20, PA5, PA8, BRK1) if x not in nodes]
if miss:
    raise SystemExit("앵커 소실: " + str(miss))
assert VS20 in str(conn(nodes[VS19], "then"))
assert PA5 in str(conn(nodes[VS20], "TransitingToNextLedge"))
# prev 게터: TransitingToNextLedge Get 노드 필요 (기존에 없음 — 추가)
spec = [
    {"temp_id": "gPrevTr", "node_type": "VariableGet", "variable_name": "TransitingToNextLedge", "position": [900, 100]},
    {"temp_id": "brA", "node_type": "Branch", "position": [1104, -350]},
    {"temp_id": "setT0", "node_type": "VariableSet", "variable_name": "LedgeCrossHoldTimer", "position": [1104, -430]},
    {"temp_id": "gT", "node_type": "VariableGet", "variable_name": "LedgeCrossHoldTimer", "position": [900, 180]},
    {"temp_id": "gdt", "node_type": "VariableGet", "variable_name": "Delta Time", "position": [900, 260]},
    {"temp_id": "addT", "node_type": "CallFunction", "function_name": "Add_DoubleDouble", "target_class": KML, "position": [1060, 220]},
    {"temp_id": "setTA", "node_type": "VariableSet", "variable_name": "LedgeCrossHoldTimer", "position": [1104, -510]},
    {"temp_id": "gT2", "node_type": "VariableGet", "variable_name": "LedgeCrossHoldTimer", "position": [900, 340]},
    {"temp_id": "gHold", "node_type": "VariableGet", "variable_name": "LedgeCrossHoldTime", "position": [900, 420]},
    {"temp_id": "lt", "node_type": "CallFunction", "function_name": "Less_DoubleDouble", "target_class": KML, "position": [1060, 360]},
    {"temp_id": "notMv", "node_type": "CallFunction", "function_name": "Not_PreBool", "target_class": KML, "position": [1060, 500]},
    {"temp_id": "and1", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [1220, 140]},
    {"temp_id": "and2", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [1380, 200]},
    {"temp_id": "and3", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [1540, 260]},
    {"temp_id": "or1", "node_type": "CallFunction", "function_name": "BooleanOR", "target_class": KML, "position": [1700, 120]},
]
tm = {}
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G, "nodes": spec})
harvest(res, tm)
if len(tm) != len(spec):
    made = set(tm)
    raise SystemExit("노드 %d/%d missing=%s" % (len(tm), len(spec), [n["temp_id"] for n in spec if n["temp_id"] not in made]))
conns = [
    {"source_node": PA5, "source_pin": "Value", "target_node": tm["brA"], "target_pin": "Condition"},
    {"source_node": tm["gT"], "source_pin": "LedgeCrossHoldTimer", "target_node": tm["addT"], "target_pin": "A"},
    {"source_node": tm["gdt"], "source_pin": "Delta Time", "target_node": tm["addT"], "target_pin": "B"},
    {"source_node": tm["addT"], "source_pin": "ReturnValue", "target_node": tm["setTA"], "target_pin": "LedgeCrossHoldTimer"},
    # held = rawTr OR (prevTr AND bActive AND t<hold AND NOT rawMv)
    {"source_node": tm["gPrevTr"], "source_pin": "TransitingToNextLedge", "target_node": tm["and1"], "target_pin": "A"},
    {"source_node": BRK1, "source_pin": "bActive", "target_node": tm["and1"], "target_pin": "B"},
    {"source_node": tm["gT2"], "source_pin": "LedgeCrossHoldTimer", "target_node": tm["lt"], "target_pin": "A"},
    {"source_node": tm["gHold"], "source_pin": "LedgeCrossHoldTime", "target_node": tm["lt"], "target_pin": "B"},
    {"source_node": PA8, "source_pin": "Value", "target_node": tm["notMv"], "target_pin": "A"},
    {"source_node": tm["and1"], "source_pin": "ReturnValue", "target_node": tm["and2"], "target_pin": "A"},
    {"source_node": tm["lt"], "source_pin": "ReturnValue", "target_node": tm["and2"], "target_pin": "B"},
    {"source_node": tm["and2"], "source_pin": "ReturnValue", "target_node": tm["and3"], "target_pin": "A"},
    {"source_node": tm["notMv"], "source_pin": "ReturnValue", "target_node": tm["and3"], "target_pin": "B"},
    {"source_node": PA5, "source_pin": "Value", "target_node": tm["or1"], "target_pin": "A"},
    {"source_node": tm["and3"], "source_pin": "ReturnValue", "target_node": tm["or1"], "target_pin": "B"},
]
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": VS19, "pin_name": "then"})
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": VS20, "pin_name": "TransitingToNextLedge"})
conns += [
    {"source_node": VS19, "source_pin": "then", "target_node": tm["brA"], "target_pin": "execute"},
    {"source_node": tm["brA"], "source_pin": "then", "target_node": tm["setT0"], "target_pin": "execute"},
    {"source_node": tm["setT0"], "source_pin": "then", "target_node": VS20, "target_pin": "execute"},
    {"source_node": tm["brA"], "source_pin": "else", "target_node": tm["setTA"], "target_pin": "execute"},
    {"source_node": tm["setTA"], "source_pin": "then", "target_node": VS20, "target_pin": "execute"},
    {"source_node": tm["or1"], "source_pin": "ReturnValue", "target_node": VS20, "target_pin": "TransitingToNextLedge"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append(fails)
LOG["steps"].append("links: %d req %d fail" % (len(conns), len(fails)))
with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/cross_hold.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("CROSS_HOLD_DONE errors=%s" % ("none" if not LOG["errors"] else json.dumps(LOG["errors"], ensure_ascii=False)[:300]))
