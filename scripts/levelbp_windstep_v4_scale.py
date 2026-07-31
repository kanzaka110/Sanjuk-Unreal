# 스텝퍼 v4: 1,2,3,4,5 -> 1.2 간격 5단계 (1.2/2.4/3.6/4.8/6.0)
#   strength = ((idx%5)+1) * WindStepSize(신규 float 변수, 기본 1.2)
#   PrintString 도 실제 강도값 표시로 교체 (IntToString -> DoubleToString)
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
EG = "EventGraph"
KML = "KismetMathLibrary"
KStr = "KismetStringLibrary"
SEQ_BP = "K2Node_ExecutionSequence_1"
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


def first_target(nodes: dict, nid: str, pin: str) -> str:
    ct = pm(nodes, nid).get(pin, {}).get("connected_to") or []
    assert ct, "%s.%s 연결 없음" % (nid, pin)
    return ct[0].split(".")[0]


nodes = graph()

# ═══ 0) 신규 체인 노드 위치 추적: SEQ.then_0 -> br -> sstr -> prn ═══
br = first_target(nodes, SEQ_BP, "then_0")
sstr = first_target(nodes, br, "then")
prn = first_target(nodes, sstr, "then")
cnv = first_target(nodes, sstr, "WindStrength")   # Conv_IntToDouble
cat = first_target(nodes, prn, "InString")        # Concat_StrStr
i2s = first_target(nodes, cat, "B")               # Conv_IntToString (제거 대상)
assert "IfThenElse" in nodes[br]["class"] and "VariableSet" in nodes[sstr]["class"], "체인 추적 이상"
LOG["steps"].append("chain: br=%s sstr=%s prn=%s cnv=%s cat=%s i2s=%s" % (br, sstr, prn, cnv, cat, i2s))

# ═══ 1) 변수 WindStepSize (기본 1.2) ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
if "WindStepSize" not in existing:
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": "WindStepSize", "type": "float", "default_value": "1.2",
          "category": "WindStep", "instance_editable": True})
LOG["steps"].append("var WindStepSize ok")

# ═══ 2) 곱셈 + 표시 변환 노드 ═══
pos = nodes[cnv].get("pos") or nodes[cnv].get("position") or [1100, 9500]
mx, my = int(pos[0]) + 150, int(pos[1]) + 120
gss = add("VariableGet", mx - 200, my + 120, variable_name="WindStepSize")
mul = None
for fn in ("Multiply_DoubleDouble", "Multiply_FloatFloat"):
    try:
        mul = add("CallFunction", mx, my, function_name=fn, target_class=KML)
        LOG["steps"].append("mul=%s" % fn)
        break
    except Exception as e:
        LOG["errors"].append({"mul_try": fn, "err": str(e)[:150]})
assert mul, "곱셈 노드 스폰 실패"
d2s = None
for fn in ("Conv_DoubleToString", "Conv_FloatToString"):
    try:
        d2s = add("CallFunction", mx + 250, my + 150, function_name=fn, target_class=KStr)
        det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": EG, "node_id": d2s})
        d2s_in = next(p["name"] for p in (det.get("pins") or [])
                      if p.get("direction") == "input" and p.get("name") not in ("self", "execute"))
        LOG["steps"].append("d2s=%s in=%s" % (fn, d2s_in))
        break
    except Exception as e:
        LOG["errors"].append({"d2s_try": fn, "err": str(e)[:150]})
        d2s = None
assert d2s, "Double->String 노드 스폰 실패"

# ═══ 3) 재배선 ═══
call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": EG, "node_id": sstr, "pin_name": "WindStrength"})
call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": EG, "node_id": cat, "pin_name": "B"})
f = connect([
    {"source_node": cnv, "source_pin": "ReturnValue", "target_node": mul, "target_pin": "A"},
    {"source_node": gss, "source_pin": "WindStepSize", "target_node": mul, "target_pin": "B"},
    {"source_node": mul, "source_pin": "ReturnValue", "target_node": sstr, "target_pin": "WindStrength"},
    {"source_node": mul, "source_pin": "ReturnValue", "target_node": d2s, "target_pin": d2s_in},
    {"source_node": d2s, "source_pin": "ReturnValue", "target_node": cat, "target_pin": "B"},
])
LOG["steps"].append("connects fail=%d" % f)
assert f == 0, "배선 실패"
call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": EG, "node_id": i2s})

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:250])

nodes = graph()
LOG["steps"].append("verify WindStrength <- %s" % pm(nodes, sstr)["WindStrength"].get("connected_to"))
LOG["steps"].append("verify cat.B <- %s" % pm(nodes, cat)["B"].get("connected_to"))
