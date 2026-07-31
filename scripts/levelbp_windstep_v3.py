# 스텝퍼 PHASE B 재실행 (v2에서 PHASE A 원복은 완료됨)
#   - v2 실패 런의 고아 리터럴(Unknown 핀) 제거
#   - 실제 액터 경로(OFPA 실측)로 독립 체인 빌드
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
EG = "EventGraph"
KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"
KStr = "KismetStringLibrary"
SB_WV = "/Script/SB2.SBWindVolume"
SEQ_BP = "K2Node_ExecutionSequence_1"
ACTOR = ("/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map."
         "SBWind_Weight_TEST01_Map:PersistentLevel.SBWindVolume_UAID_30560F6BCAE5D3F202_1767786249")
LOG = {"steps": [], "errors": []}
atexit.register(lambda: print(json.dumps(LOG, ensure_ascii=False, indent=1)))


def call(tool: str, action: str, params: dict, timeout: int = 300) -> dict:
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def nid_of(r: dict) -> str:
    return r.get("node_id") or r.get("id")


def add(ntype: str, x: int, y: int, **kw) -> str:
    p = {"asset_path": BP, "graph_name": EG, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return nid_of(call("blueprint_query", "add_node", p))


def pin_names(nid: str) -> list:
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": EG, "node_id": nid})
    return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]


def connect(cs: list) -> int:
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": EG, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


def graph() -> dict:
    g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
    return {n["id"]: n for n in g["nodes"]}


def pm(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


nodes = graph()

# ═══ 0) v2 고아 리터럴 제거 (Unknown 핀, 연결 없음) ═══
for nid, n in list(nodes.items()):
    if "K2Node_Literal" not in n.get("class", ""):
        continue
    pins = n.get("pins", [])
    if pins and pins[0].get("name") == "Unknown" and not (pins[0].get("connected_to") or []):
        call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": EG, "node_id": nid})
        LOG["steps"].append("고아 리터럴 제거: %s" % nid)

seq_p = pm(nodes, SEQ_BP)
assert not (seq_p.get("then_0", {}).get("connected_to") or []), "SEQ then_0 이 비어있지 않음"

# ═══ 1) 리터럴 (실측 경로) ═══
BX, BY = 300, 9000
lit = add("K2Node_Literal", BX, BY + 350)
call("blueprint_query", "set_node_property", {"asset_path": BP, "graph_name": EG, "node_id": lit,
     "property_name": "ObjectRef", "value": ACTOR})
call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": lit})
lit_pin = [p for p in pin_names(lit) if p not in ("execute", "then")][0]
assert lit_pin != "Unknown", "리터럴 미해석 — 액터 경로 재확인 필요"
LOG["steps"].append("literal ok pin=%s" % lit_pin)

# ═══ 2) 노드 스폰 ═══
isv = add("CallFunction", BX + 250, BY + 300, function_name="IsValid", target_class=KSL)
br = add("Branch", BX + 500, BY)
sstr = add("VariableSet", BX + 800, BY, variable_name="WindStrength", target_class="SBWindVolume")
call("blueprint_query", "set_node_property", {"asset_path": BP, "graph_name": EG, "node_id": sstr,
     "property_name": "VariableReference",
     "value": '(MemberParent=%s,MemberName="WindStrength",bSelfContext=False)' % SB_WV})
call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": sstr})
assert "WindStrength" in pin_names(sstr), "WindStrength 셋터 값핀 실패"

g1 = add("VariableGet", BX + 200, BY + 500, variable_name="WindStepIdx")
mod2 = add("CallFunction", BX + 400, BY + 500, function_name="Percent_IntInt", target_class=KML)
add2 = add("CallFunction", BX + 600, BY + 500, function_name="Add_IntInt", target_class=KML)
cnv = add("CallFunction", BX + 800, BY + 500, function_name="Conv_IntToDouble", target_class=KML)
i2s = add("CallFunction", BX + 1000, BY + 650, function_name="Conv_IntToString", target_class=KStr)
cat = add("CallFunction", BX + 1200, BY + 650, function_name="Concat_StrStr", target_class=KStr)
prn = add("CallFunction", BX + 1200, BY, function_name="PrintString", target_class=KSL)
g2 = add("VariableGet", BX + 1450, BY + 500, variable_name="WindStepIdx")
add3 = add("CallFunction", BX + 1600, BY + 500, function_name="Add_IntInt", target_class=KML)
inc2 = add("VariableSet", BX + 1650, BY, variable_name="WindStepIdx")
assert "WindStepIdx" in pin_names(inc2), "inc 셋터 값핀 실패"
dly = add("CallFunction", BX + 1950, BY, function_name="Delay", target_class=KSL)

call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": EG, "defaults": [
    {"node_id": mod2, "pin_name": "B", "value": "5"},
    {"node_id": add2, "pin_name": "B", "value": "1"},
    {"node_id": add3, "pin_name": "B", "value": "1"},
    {"node_id": cat, "pin_name": "A", "value": "GlobalWindStep Str "},
    {"node_id": prn, "pin_name": "Duration", "value": "3.0"},
    {"node_id": prn, "pin_name": "Key", "value": "WindStep"},
    {"node_id": dly, "pin_name": "Duration", "value": "3.0"},
]})

# ═══ 3) 배선 ═══
f = connect([
    {"source_node": lit, "source_pin": lit_pin, "target_node": isv, "target_pin": "Object"},
    {"source_node": isv, "source_pin": "ReturnValue", "target_node": br, "target_pin": "Condition"},
    {"source_node": lit, "source_pin": lit_pin, "target_node": sstr, "target_pin": "self"},
    {"source_node": g1, "source_pin": "WindStepIdx", "target_node": mod2, "target_pin": "A"},
    {"source_node": mod2, "source_pin": "ReturnValue", "target_node": add2, "target_pin": "A"},
    {"source_node": add2, "source_pin": "ReturnValue", "target_node": cnv, "target_pin": "InInt"},
    {"source_node": cnv, "source_pin": "ReturnValue", "target_node": sstr, "target_pin": "WindStrength"},
    {"source_node": add2, "source_pin": "ReturnValue", "target_node": i2s, "target_pin": "InInt"},
    {"source_node": i2s, "source_pin": "ReturnValue", "target_node": cat, "target_pin": "B"},
    {"source_node": cat, "source_pin": "ReturnValue", "target_node": prn, "target_pin": "InString"},
    {"source_node": g2, "source_pin": "WindStepIdx", "target_node": add3, "target_pin": "A"},
    {"source_node": add3, "source_pin": "ReturnValue", "target_node": inc2, "target_pin": "WindStepIdx"},
    {"source_node": SEQ_BP, "source_pin": "then_0", "target_node": br, "target_pin": "execute"},
    {"source_node": br, "source_pin": "then", "target_node": sstr, "target_pin": "execute"},
    {"source_node": sstr, "source_pin": "then", "target_node": prn, "target_pin": "execute"},
    {"source_node": prn, "source_pin": "then", "target_node": inc2, "target_pin": "execute"},
    {"source_node": inc2, "source_pin": "then", "target_node": dly, "target_pin": "execute"},
    {"source_node": dly, "source_pin": "then", "target_node": br, "target_pin": "execute"},
])
LOG["steps"].append("connects fail=%d" % f)
assert f == 0, "배선 실패 — LOG.errors 확인"

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])

nodes = graph()
LOG["steps"].append("verify SEQ.then_0 -> %s" % pm(nodes, SEQ_BP)["then_0"].get("connected_to"))
LOG["steps"].append("verify SetStr.WindStrength <- %s" % pm(nodes, sstr)["WindStrength"].get("connected_to"))
LOG["steps"].append("verify Delay.then -> %s (루프백)" % pm(nodes, dly)["then"].get("connected_to"))
