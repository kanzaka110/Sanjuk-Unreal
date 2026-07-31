# 스텝퍼 v5: 균등 스텝 -> 지정 시퀀스 [4,6,7.5,9,12,-12,-9,-7.5,-6,-4] 순환 (10단계)
#   전제(T3D 실측): 승호가 체인을 SBDirectionalWindActor8 컴포넌트 타깃으로 개조
#     IfThenElse_8 -> VariableSet_11(SBDirectionalWindComponent.WindStrength) -> Print_121 -> Set_10(idx+1) -> Delay_123
#   변경:
#     - array:float 변수 WindStepValues 추가 (10개 값)
#     - 값 체인: idx %10 -> Array_Get -> WindStrength / DoubleToString(표시)
#     - 제거: Add+1(_83), IntToDouble(_118), Multiply(_124), Get WindStepSize(VariableGet_22)
#     - 루프백 복구: Delay_123.then -> IfThenElse_8.execute (T3D에서 끊김 확인)
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
EG = "EventGraph"
KAL = "KismetArrayLibrary"
MOD = "K2Node_CallFunction_68"       # Percent_IntInt (B=5 -> 10)
ADD1 = "K2Node_CallFunction_83"      # Add_IntInt +1 (제거)
CNV = "K2Node_CallFunction_118"      # Conv_IntToDouble (제거)
MUL = "K2Node_CallFunction_124"      # Multiply_DoubleDouble (제거)
GSS = "K2Node_VariableGet_22"        # Get WindStepSize (제거)
D2S = "K2Node_CallFunction_125"      # Conv_DoubleToString (유지, 입력 교체)
SETSTR = "K2Node_VariableSet_11"     # Set WindStrength (Directional 컴포넌트, 승호 개조)
BR = "K2Node_IfThenElse_8"
DLY = "K2Node_CallFunction_123"
VALUES = "(4.0,6.0,7.5,9.0,12.0,-12.0,-9.0,-7.5,-6.0,-4.0)"
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
for nid in (MOD, ADD1, CNV, MUL, GSS, D2S, SETSTR, BR, DLY):
    assert nid in nodes, "노드 미발견: %s — T3D와 그래프 불일치, 재분석 필요" % nid
# 승호 개조 확인: SETSTR self 가 SBDirectionalWindComponent 인지
self_t = pm(nodes, SETSTR).get("self", {}).get("type", "")
assert "SBDirectionalWindComponent" in self_t, "SETSTR 타깃 예상 불일치: %s" % self_t
LOG["steps"].append("preflight ok (타깃=%s)" % self_t)

# ═══ 1) 배열 변수 ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
if "WindStepValues" not in existing:
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": "WindStepValues", "type": "array:float", "default_value": VALUES,
          "category": "WindStep", "instance_editable": True})
gv = call("blueprint_query", "get_variables", {"asset_path": BP})
vinfo = next((v for v in gv.get("variables", []) if v["name"] == "WindStepValues"), {})
LOG["steps"].append("var WindStepValues: %s" % json.dumps(vinfo, ensure_ascii=False)[:250])

# ═══ 2) 룩업 노드 ═══
garr = add("VariableGet", -700, 1700, variable_name="WindStepValues")
aget = add("CallFunction", -400, 1650, function_name="Array_Get", target_class=KAL)
det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": EG, "node_id": aget})
aget_pins = [p.get("name") for p in (det.get("pins") or [])]
LOG["steps"].append("Array_Get pins: %s" % aget_pins)
arr_pin = next(p for p in aget_pins if "Array" in p)
idx_pin = next(p for p in aget_pins if "Index" in p)
item_pin = next(p for p in aget_pins if p not in (arr_pin, idx_pin, "self", "execute", "then"))

# ═══ 3) 재배선 ═══
call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": EG, "node_id": MOD, "pin_name": "B", "value": "10"})
for nid, pin in ((SETSTR, "WindStrength"), (D2S, "InDouble"), (MOD, "ReturnValue")):
    call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": EG, "node_id": nid, "pin_name": pin})

# 배열 -> Array_Get 먼저 (와일드카드 타입 확정), 그다음 나머지
f1 = connect([{"source_node": garr, "source_pin": "WindStepValues", "target_node": aget, "target_pin": arr_pin}])
f2 = connect([
    {"source_node": MOD, "source_pin": "ReturnValue", "target_node": aget, "target_pin": idx_pin},
    {"source_node": aget, "source_pin": item_pin, "target_node": SETSTR, "target_pin": "WindStrength"},
    {"source_node": aget, "source_pin": item_pin, "target_node": D2S, "target_pin": "InDouble"},
    # 루프백 복구
    {"source_node": DLY, "source_pin": "then", "target_node": BR, "target_pin": "execute"},
])
LOG["steps"].append("connects fail=%d+%d" % (f1, f2))
assert f1 + f2 == 0, "배선 실패 — LOG.errors 확인"

# ═══ 4) 구 수식 노드 제거 ═══
for nid in (ADD1, CNV, MUL, GSS):
    call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": EG, "node_id": nid})
LOG["steps"].append("구 수식 노드 4개 제거")

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:250])

nodes = graph()
LOG["steps"].append("verify WindStrength <- %s" % pm(nodes, SETSTR)["WindStrength"].get("connected_to"))
LOG["steps"].append("verify D2S.InDouble <- %s" % pm(nodes, D2S)["InDouble"].get("connected_to"))
LOG["steps"].append("verify Delay.then -> %s (루프백)" % pm(nodes, DLY)["then"].get("connected_to"))
LOG["steps"].append("verify MOD.B = %s" % pm(nodes, MOD)["B"].get("default_value"))
