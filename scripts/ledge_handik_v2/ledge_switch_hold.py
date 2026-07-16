# v10 — 렛지 유닛컷 절단 TA측 우회: Move->Idle 애님 스위치 홀드
# SetStateMachineBlendStackAnim: Chooser 적용 직전 가드 —
#   현재=P_Player_Ledge*(비Idle) AND 후보=Ledge_Idle AND LedgeMoveTimer<HoldTime → 스킵+펜딩
# 적용 경로엔 타이머 리셋+펜딩 해제. Ledge 오케스트레이터 꼬리: 타이머 누적 + 펜딩 발화(재호출)
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
SS = "SetStateMachineBlendStackAnim"
KML = "KismetMathLibrary"
KSL = "KismetStringLibrary"
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


# ── 0) 변수 ──
VARS = [("bLedgePendingSwitch", "bool", None), ("LedgePendingState", "byte", None),
        ("LedgeMoveTimer", "float", None), ("LedgeMoveHoldTime", "float", "0.55")]
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for name, typ, dv in VARS:
    if name in existing:
        continue
    p = {"asset_path": ABP, "name": name, "type": typ, "category": "Ledge|SwitchHold", "instance_editable": False}
    if dv:
        p["default_value"] = dv
    call("blueprint_query", "add_variable", p)
    LOG["steps"].append("var: " + name)

# ── 1) 셋터 함수: 가드 + 리셋 ──
g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": SS})
nodes = {n["id"]: n for n in g["nodes"]}
def pins(n): return {p["name"]: p for p in n.get("pins", [])}
def conn(n, pin): return (pins(n).get(pin, {}).get("connected_to") or [])
need = ["K2Node_IfThenElse_1", "K2Node_SetFieldsInStruct_1", "K2Node_GetArrayItem_0",
        "K2Node_VariableSet_7", "K2Node_FunctionEntry_0"]
miss = [x for x in need if x not in nodes]
if miss:
    raise SystemExit("앵커 소실: " + str(miss))
# IfThenElse_1.then -> SetFieldsInStruct_1 (재배선 대상) 확인
assert "K2Node_SetFieldsInStruct_1" in str(conn(nodes["K2Node_IfThenElse_1"], "then")), conn(nodes["K2Node_IfThenElse_1"], "then")
assert "K2Node_VariableSet_7" in str(conn(nodes["K2Node_SetFieldsInStruct_1"], "then"))

spec = [
    # 현재 애님 이름
    {"temp_id": "gBSI", "node_type": "VariableGet", "variable_name": "BlendStackInputs", "position": [2300, 900]},
    {"temp_id": "brk", "node_type": "BreakStruct", "struct_type": "S_BlendStackInputs", "position": [2480, 900]},
    {"temp_id": "curNm", "node_type": "CallFunction", "function_name": "GetObjectName", "target_class": "KismetSystemLibrary", "position": [2660, 900]},
    {"temp_id": "candNm", "node_type": "CallFunction", "function_name": "GetObjectName", "target_class": "KismetSystemLibrary", "position": [2660, 1000]},
    {"temp_id": "cLedge", "node_type": "CallFunction", "function_name": "Contains", "target_class": KSL, "position": [2840, 860]},
    {"temp_id": "cIdleCur", "node_type": "CallFunction", "function_name": "Contains", "target_class": KSL, "position": [2840, 940]},
    {"temp_id": "nIdleCur", "node_type": "CallFunction", "function_name": "Not_PreBool", "target_class": KML, "position": [3000, 940]},
    {"temp_id": "cIdleCand", "node_type": "CallFunction", "function_name": "Contains", "target_class": KSL, "position": [2840, 1020]},
    {"temp_id": "gTimer", "node_type": "VariableGet", "variable_name": "LedgeMoveTimer", "position": [2840, 1100]},
    {"temp_id": "gHold", "node_type": "VariableGet", "variable_name": "LedgeMoveHoldTime", "position": [2840, 1180]},
    {"temp_id": "lt", "node_type": "CallFunction", "function_name": "Less_DoubleDouble", "target_class": KML, "position": [3000, 1120]},
    {"temp_id": "and1", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [3160, 900]},
    {"temp_id": "and2", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [3320, 940]},
    {"temp_id": "and3", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [3480, 980]},
    {"temp_id": "brH", "node_type": "Branch", "position": [3320, 700]},
    {"temp_id": "setPend", "node_type": "VariableSet", "variable_name": "bLedgePendingSwitch", "position": [3500, 620]},
    {"temp_id": "setPSt", "node_type": "VariableSet", "variable_name": "LedgePendingState", "position": [3680, 620]},
    {"temp_id": "ret", "node_type": "Return", "position": [3860, 620]},
    # 적용 경로 리셋 2개
    {"temp_id": "setT0", "node_type": "VariableSet", "variable_name": "LedgeMoveTimer", "position": [3500, 760]},
    {"temp_id": "setPend0", "node_type": "VariableSet", "variable_name": "bLedgePendingSwitch", "position": [3680, 760]},
]
tm = {}
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": SS, "nodes": spec})
harvest(res, tm)
if len(tm) != len(spec):
    made = set(tm)
    raise SystemExit("셋터 노드 %d/%d missing=%s" % (len(tm), len(spec), [n["temp_id"] for n in spec if n["temp_id"] not in made]))
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": SS, "defaults": [
    {"node_id": tm["cLedge"], "pin_name": "Substring", "value": "P_Player_Ledge"},
    {"node_id": tm["cIdleCur"], "pin_name": "Substring", "value": "Idle"},
    {"node_id": tm["cIdleCand"], "pin_name": "Substring", "value": "Ledge_Idle"},
    {"node_id": tm["setPend"], "pin_name": "bLedgePendingSwitch", "value": "true"},
]})
conns = [
    {"source_node": tm["gBSI"], "source_pin": "BlendStackInputs", "target_node": tm["brk"], "target_pin": "S_BlendStackInputs"},
    {"source_node": tm["brk"], "source_pin": "Anim_3_CE8F6C8948855759C43A24A538203DDC", "target_node": tm["curNm"], "target_pin": "Object"},
    {"source_node": "K2Node_GetArrayItem_0", "source_pin": "Output", "target_node": tm["candNm"], "target_pin": "Object"},
    {"source_node": tm["curNm"], "source_pin": "ReturnValue", "target_node": tm["cLedge"], "target_pin": "SearchIn"},
    {"source_node": tm["curNm"], "source_pin": "ReturnValue", "target_node": tm["cIdleCur"], "target_pin": "SearchIn"},
    {"source_node": tm["cIdleCur"], "source_pin": "ReturnValue", "target_node": tm["nIdleCur"], "target_pin": "A"},
    {"source_node": tm["candNm"], "source_pin": "ReturnValue", "target_node": tm["cIdleCand"], "target_pin": "SearchIn"},
    {"source_node": tm["gTimer"], "source_pin": "LedgeMoveTimer", "target_node": tm["lt"], "target_pin": "A"},
    {"source_node": tm["gHold"], "source_pin": "LedgeMoveHoldTime", "target_node": tm["lt"], "target_pin": "B"},
    {"source_node": tm["cLedge"], "source_pin": "ReturnValue", "target_node": tm["and1"], "target_pin": "A"},
    {"source_node": tm["nIdleCur"], "source_pin": "ReturnValue", "target_node": tm["and1"], "target_pin": "B"},
    {"source_node": tm["and1"], "source_pin": "ReturnValue", "target_node": tm["and2"], "target_pin": "A"},
    {"source_node": tm["cIdleCand"], "source_pin": "ReturnValue", "target_node": tm["and2"], "target_pin": "B"},
    {"source_node": tm["and2"], "source_pin": "ReturnValue", "target_node": tm["and3"], "target_pin": "A"},
    {"source_node": tm["lt"], "source_pin": "ReturnValue", "target_node": tm["and3"], "target_pin": "B"},
    {"source_node": tm["and3"], "source_pin": "ReturnValue", "target_node": tm["brH"], "target_pin": "Condition"},
    {"source_node": "K2Node_FunctionEntry_0", "source_pin": "StateMachineState", "target_node": tm["setPSt"], "target_pin": "LedgePendingState"},
]
# exec 재배선: IfThenElse_1.then -> brH ; brH.then(홀드) -> setPend -> setPSt -> ret
#              brH.else -> SetFields_1 ; SetFields_1.then -> setT0 -> setPend0 -> VS_7
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": SS, "node_id": "K2Node_IfThenElse_1", "pin_name": "then"})
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": SS, "node_id": "K2Node_SetFieldsInStruct_1", "pin_name": "then"})
conns += [
    {"source_node": "K2Node_IfThenElse_1", "source_pin": "then", "target_node": tm["brH"], "target_pin": "execute"},
    {"source_node": tm["brH"], "source_pin": "then", "target_node": tm["setPend"], "target_pin": "execute"},
    {"source_node": tm["setPend"], "source_pin": "then", "target_node": tm["setPSt"], "target_pin": "execute"},
    {"source_node": tm["setPSt"], "source_pin": "then", "target_node": tm["ret"], "target_pin": "execute"},
    {"source_node": tm["brH"], "source_pin": "else", "target_node": "K2Node_SetFieldsInStruct_1", "target_pin": "execute"},
    {"source_node": "K2Node_SetFieldsInStruct_1", "source_pin": "then", "target_node": tm["setT0"], "target_pin": "execute"},
    {"source_node": tm["setT0"], "source_pin": "then", "target_node": tm["setPend0"], "target_pin": "execute"},
    {"source_node": tm["setPend0"], "source_pin": "then", "target_node": "K2Node_VariableSet_7", "target_pin": "execute"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": SS, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"setter": fails})
LOG["steps"].append("setter: %d links %d fail" % (len(conns), len(fails)))

# ── 2) Ledge 오케스트레이터 꼬리: 타이머 누적 + 펜딩 발화 ──
g2 = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": "Ledge"})
n2 = {n["id"]: n for n in g2["nodes"]}
def conn2(n, pin):
    P = {p["name"]: p for p in n.get("pins", [])}
    return (P.get(pin, {}).get("connected_to") or [])
tail = None
for nid, n in n2.items():
    t = (n.get("title") or "")
    if "Foot Gate" in t and not conn2(n, "then"):
        tail = nid
assert tail, "FootGate 꼬리 미발견"
spec2 = [
    {"temp_id": "gT", "node_type": "VariableGet", "variable_name": "LedgeMoveTimer", "position": [5200, 700]},
    {"temp_id": "dt", "node_type": "CallFunction", "function_name": "GetWorldDeltaSeconds", "target_class": "GameplayStatics", "position": [5200, 780]},
    {"temp_id": "add", "node_type": "CallFunction", "function_name": "Add_DoubleDouble", "target_class": KML, "position": [5380, 720]},
    {"temp_id": "setT", "node_type": "VariableSet", "variable_name": "LedgeMoveTimer", "position": [5560, 600]},
    {"temp_id": "gPend", "node_type": "VariableGet", "variable_name": "bLedgePendingSwitch", "position": [5560, 780]},
    {"temp_id": "gT2", "node_type": "VariableGet", "variable_name": "LedgeMoveTimer", "position": [5560, 860]},
    {"temp_id": "gH2", "node_type": "VariableGet", "variable_name": "LedgeMoveHoldTime", "position": [5560, 940]},
    {"temp_id": "ge", "node_type": "CallFunction", "function_name": "GreaterEqual_DoubleDouble", "target_class": KML, "position": [5740, 880]},
    {"temp_id": "andF", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [5900, 820]},
    {"temp_id": "brF", "node_type": "Branch", "position": [5900, 600]},
    {"temp_id": "clrP", "node_type": "VariableSet", "variable_name": "bLedgePendingSwitch", "position": [6080, 600]},
    {"temp_id": "gPSt", "node_type": "VariableGet", "variable_name": "LedgePendingState", "position": [6080, 760]},
    {"temp_id": "fire", "node_type": "CallFunction", "function_name": SS, "position": [6260, 600]},
]
tm2 = {}
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": "Ledge", "nodes": spec2})
harvest(res, tm2)
if len(tm2) != len(spec2):
    made = set(tm2)
    raise SystemExit("Ledge 노드 %d/%d missing=%s" % (len(tm2), len(spec2), [n["temp_id"] for n in spec2 if n["temp_id"] not in made]))
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": "Ledge", "defaults": [
    {"node_id": tm2["fire"], "pin_name": "bForceBlend", "value": "true"},
]})
c2 = [
    {"source_node": tm2["gT"], "source_pin": "LedgeMoveTimer", "target_node": tm2["add"], "target_pin": "A"},
    {"source_node": tm2["dt"], "source_pin": "ReturnValue", "target_node": tm2["add"], "target_pin": "B"},
    {"source_node": tm2["add"], "source_pin": "ReturnValue", "target_node": tm2["setT"], "target_pin": "LedgeMoveTimer"},
    {"source_node": tm2["gT2"], "source_pin": "LedgeMoveTimer", "target_node": tm2["ge"], "target_pin": "A"},
    {"source_node": tm2["gH2"], "source_pin": "LedgeMoveHoldTime", "target_node": tm2["ge"], "target_pin": "B"},
    {"source_node": tm2["gPend"], "source_pin": "bLedgePendingSwitch", "target_node": tm2["andF"], "target_pin": "A"},
    {"source_node": tm2["ge"], "source_pin": "ReturnValue", "target_node": tm2["andF"], "target_pin": "B"},
    {"source_node": tm2["andF"], "source_pin": "ReturnValue", "target_node": tm2["brF"], "target_pin": "Condition"},
    {"source_node": tm2["gPSt"], "source_pin": "LedgePendingState", "target_node": tm2["fire"], "target_pin": "StateMachineState"},
    # exec: FootGate -> setT -> brF ; brF.then -> clrP -> fire
    {"source_node": tail, "source_pin": "then", "target_node": tm2["setT"], "target_pin": "execute"},
    {"source_node": tm2["setT"], "source_pin": "then", "target_node": tm2["brF"], "target_pin": "execute"},
    {"source_node": tm2["brF"], "source_pin": "then", "target_node": tm2["clrP"], "target_pin": "execute"},
    {"source_node": tm2["clrP"], "source_pin": "then", "target_node": tm2["fire"], "target_pin": "execute"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": "Ledge", "connections": c2})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"ledge": fails})
LOG["steps"].append("ledge tail: %d links %d fail" % (len(c2), len(fails)))

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/switch_hold.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("SWITCH_HOLD_DONE errors=%s" % ("none" if not LOG["errors"] else json.dumps(LOG["errors"], ensure_ascii=False)[:400]))
