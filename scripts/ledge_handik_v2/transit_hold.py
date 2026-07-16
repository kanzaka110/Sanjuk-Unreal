# v12 — bTransitMoving 하강 에지 홀드 (UpdateStates)
# 유닛무브 종료 시 IsTransitMoving 즉시 false -> SM Move->Idle 전환이 애님 절단.
# held = raw OR (prev(bTransitMoving) AND LedgeMoveData.bActive AND timer < HoldTime)
# raw true 경로: 타이머 리셋 / false 경로: 타이머 누적. 렛지 한정(bActive), 상승 에지 즉시 통과.
# 롤백 = VS_19 데이터/exec 원복 2링크.
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


# ── 변수 ──
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for name, typ, dv in (("LedgeTransitHoldTimer", "float", None), ("LedgeTransitHoldTime", "float", "0.15")):
    if name in existing:
        continue
    p = {"asset_path": ABP, "name": name, "type": typ, "category": "Ledge|TransitHold", "instance_editable": False}
    if dv:
        p["default_value"] = dv
    call("blueprint_query", "add_variable", p)
    LOG["steps"].append("var: " + name)

# ── 앵커 확인 (T3D 기준 ID) ──
g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": G})
nodes = {n["id"]: n for n in g["nodes"]}
def pins(n): return {p["name"]: p for p in n.get("pins", [])}
def conn(n, pin): return (pins(n).get(pin, {}).get("connected_to") or [])
VS18 = "K2Node_VariableSet_18"   # Set bPrevTransitMoving (then -> VS_19)
VS19 = "K2Node_VariableSet_19"   # Set bTransitMoving (data <- PA_8)
VG7 = "K2Node_VariableGet_7"     # Get bTransitMoving (prev)
PA8 = "K2Node_PropertyAccess_8"  # IsTransitMoving
BRK1 = "K2Node_BreakStruct_1"    # Break LedgeMoveData (bActive 미사용 핀)
miss = [x for x in (VS18, VS19, VG7, PA8, BRK1) if x not in nodes]
if miss:
    raise SystemExit("앵커 소실: " + str(miss))
assert "K2Node_VariableSet_19" in str(conn(nodes[VS18], "then"))
assert PA8 in str(conn(nodes[VS19], "bTransitMoving"))
LOG["steps"].append("preflight OK")

spec = [
    {"temp_id": "brA", "node_type": "Branch", "position": [1120, -250]},
    {"temp_id": "setT0", "node_type": "VariableSet", "variable_name": "LedgeTransitHoldTimer", "position": [1300, -320]},
    {"temp_id": "gT", "node_type": "VariableGet", "variable_name": "LedgeTransitHoldTimer", "position": [1120, -120]},
    {"temp_id": "dt", "node_type": "CallFunction", "function_name": "GetWorldDeltaSeconds", "target_class": "GameplayStatics", "position": [1120, -40]},
    {"temp_id": "addT", "node_type": "CallFunction", "function_name": "Add_DoubleDouble", "target_class": KML, "position": [1300, -80]},
    {"temp_id": "setTA", "node_type": "VariableSet", "variable_name": "LedgeTransitHoldTimer", "position": [1470, -180]},
    # 퓨어 held 체인
    {"temp_id": "gT2", "node_type": "VariableGet", "variable_name": "LedgeTransitHoldTimer", "position": [1120, 40]},
    {"temp_id": "gHold", "node_type": "VariableGet", "variable_name": "LedgeTransitHoldTime", "position": [1120, 120]},
    {"temp_id": "lt", "node_type": "CallFunction", "function_name": "Less_DoubleDouble", "target_class": KML, "position": [1300, 60]},
    {"temp_id": "and1", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [1300, 160]},
    {"temp_id": "and2", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [1470, 100]},
    {"temp_id": "or1", "node_type": "CallFunction", "function_name": "BooleanOR", "target_class": KML, "position": [1640, 0]},
]
tm = {}
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G, "nodes": spec})
harvest(res, tm)
if len(tm) != len(spec):
    made = set(tm)
    raise SystemExit("노드 %d/%d missing=%s" % (len(tm), len(spec), [n["temp_id"] for n in spec if n["temp_id"] not in made]))
conns = [
    # brA: raw 분기
    {"source_node": PA8, "source_pin": "Value", "target_node": tm["brA"], "target_pin": "Condition"},
    # true: 타이머 리셋(디폴트 0) -> VS_19 / false: 타이머 누적 -> VS_19
    {"source_node": tm["gT"], "source_pin": "LedgeTransitHoldTimer", "target_node": tm["addT"], "target_pin": "A"},
    {"source_node": tm["dt"], "source_pin": "ReturnValue", "target_node": tm["addT"], "target_pin": "B"},
    {"source_node": tm["addT"], "source_pin": "ReturnValue", "target_node": tm["setTA"], "target_pin": "LedgeTransitHoldTimer"},
    # held = raw OR (prev AND bActive AND timer<hold)
    {"source_node": VG7, "source_pin": "bTransitMoving", "target_node": tm["and1"], "target_pin": "A"},
    {"source_node": BRK1, "source_pin": "bActive", "target_node": tm["and1"], "target_pin": "B"},
    {"source_node": tm["gT2"], "source_pin": "LedgeTransitHoldTimer", "target_node": tm["lt"], "target_pin": "A"},
    {"source_node": tm["gHold"], "source_pin": "LedgeTransitHoldTime", "target_node": tm["lt"], "target_pin": "B"},
    {"source_node": tm["and1"], "source_pin": "ReturnValue", "target_node": tm["and2"], "target_pin": "A"},
    {"source_node": tm["lt"], "source_pin": "ReturnValue", "target_node": tm["and2"], "target_pin": "B"},
    {"source_node": PA8, "source_pin": "Value", "target_node": tm["or1"], "target_pin": "A"},
    {"source_node": tm["and2"], "source_pin": "ReturnValue", "target_node": tm["or1"], "target_pin": "B"},
]
# 재배선: VS_18.then -> brA / brA.then -> setT0 -> VS_19 / brA.else -> setTA -> VS_19 / VS_19.data <- or1
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": VS18, "pin_name": "then"})
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": VS19, "pin_name": "bTransitMoving"})
conns += [
    {"source_node": VS18, "source_pin": "then", "target_node": tm["brA"], "target_pin": "execute"},
    {"source_node": tm["brA"], "source_pin": "then", "target_node": tm["setT0"], "target_pin": "execute"},
    {"source_node": tm["setT0"], "source_pin": "then", "target_node": VS19, "target_pin": "execute"},
    {"source_node": tm["brA"], "source_pin": "else", "target_node": tm["setTA"], "target_pin": "execute"},
    {"source_node": tm["setTA"], "source_pin": "then", "target_node": VS19, "target_pin": "execute"},
    {"source_node": tm["or1"], "source_pin": "ReturnValue", "target_node": VS19, "target_pin": "bTransitMoving"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append(fails)
LOG["steps"].append("links: %d req %d fail" % (len(conns), len(fails)))

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/transit_hold.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("TRANSIT_HOLD_DONE errors=%s" % ("none" if not LOG["errors"] else json.dumps(LOG["errors"], ensure_ascii=False)[:300]))
