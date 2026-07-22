# Phase T2 — 트랜짓 도착점 사전 래치 + 트랜짓 중 텔레포트 가드 해제
# 근거: pop.log 실측 — bt=1 시 NextLedgeCandidateClosest=(0,0,0) 클리어, 550cm 수직 크로싱서 dist>200 연발
import json
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
HT = "Ledge_HandTarget"
KML = "KismetMathLibrary"
E = "K2Node_FunctionEntry_0"


def call(tool, action, params, timeout=240):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:300])
    return json.loads(txt)


# 0) 변수
try:
    call("blueprint_query", "add_variable",
         {"asset_path": ABP, "name": "LedgeTransitDest", "type": "struct:Vector", "category": "Ledge"})
    print("var LedgeTransitDest added")
except RuntimeError as e:
    print("var:", str(e)[:100])

g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": HT})
nodes = {n["id"]: n for n in g["nodes"]}


def src(nid, pin):
    for p in nodes.get(nid, {}).get("pins", []):
        if p["name"] == pin and p.get("direction") == "input":
            c = p.get("connected_to") or []
            return c[0] if c else None


def then_dst(nid):
    for p in nodes[nid]["pins"]:
        if p["name"] == "then" and p.get("direction") == "output":
            c = p.get("connected_to") or []
            return c[0] if c else None


# 앵커: sub_t(현재 CF_9).B ← Entry.TransitDest / CF_219.B 디폴트 200 / VS_0(UnitMoving) 존재
assert src("K2Node_CallFunction_9", "B") == "K2Node_FunctionEntry_0.TransitDest", src("K2Node_CallFunction_9", "B")
vs0_next = then_dst("K2Node_VariableSet_0")
assert vs0_next, "VS_0.then 없음"
print("anchors OK; VS_0.then ->", vs0_next)

res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": HT, "nodes": [
    {"temp_id": "vlen", "node_type": "CallFunction", "function_name": "VSize", "target_class": KML, "position": [300, 3400]},
    {"temp_id": "gt1", "node_type": "CallFunction", "function_name": "Greater_DoubleDouble", "target_class": KML, "position": [480, 3400]},
    {"temp_id": "g_td", "node_type": "VariableGet", "variable_name": "LedgeTransitDest", "position": [300, 3550]},
    {"temp_id": "selv", "node_type": "CallFunction", "function_name": "SelectVector", "target_class": KML, "position": [660, 3450]},
    {"temp_id": "set_td", "node_type": "VariableSet", "variable_name": "LedgeTransitDest", "position": [840, 3450]},
    {"temp_id": "g_td2", "node_type": "VariableGet", "variable_name": "LedgeTransitDest", "position": [3250, 2750]},
    {"temp_id": "selg", "node_type": "CallFunction", "function_name": "SelectFloat", "target_class": KML, "position": [5000, 2100]},
]})
tm = {}


def harvest(o):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tm[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v)
    elif isinstance(o, list):
        for e in o:
            harvest(e)


harvest(res)
assert len(tm) == 7, json.dumps(res)[:400]
print("nodes:", tm)

call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": HT, "defaults": [
    {"node_id": tm["gt1"], "pin_name": "B", "value": "1.0"},
    {"node_id": tm["selg"], "pin_name": "A", "value": "100000.0"},
    {"node_id": tm["selg"], "pin_name": "B", "value": "200.0"},
]})

# 재배선: sub_t.B ← Get LedgeTransitDest / CF_219.B ← selg / VS_0 뒤에 set_td 스플라이스
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": HT,
                                            "node_id": "K2Node_CallFunction_9", "pin_name": "B"})
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": HT,
                                            "node_id": "K2Node_VariableSet_0", "pin_name": "then"})
on_nid, on_pin = vs0_next.split(".", 1)
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": [
    {"source_node": E, "source_pin": "TransitDest", "target_node": tm["vlen"], "target_pin": "A"},
    {"source_node": tm["vlen"], "source_pin": "ReturnValue", "target_node": tm["gt1"], "target_pin": "A"},
    {"source_node": E, "source_pin": "TransitDest", "target_node": tm["selv"], "target_pin": "A"},
    {"source_node": tm["g_td"], "source_pin": "LedgeTransitDest", "target_node": tm["selv"], "target_pin": "B"},
    {"source_node": tm["gt1"], "source_pin": "ReturnValue", "target_node": tm["selv"], "target_pin": "bPickA"},
    {"source_node": tm["selv"], "source_pin": "ReturnValue", "target_node": tm["set_td"], "target_pin": "LedgeTransitDest"},
    {"source_node": "K2Node_VariableSet_0", "source_pin": "then", "target_node": tm["set_td"], "target_pin": "execute"},
    {"source_node": tm["set_td"], "source_pin": "then", "target_node": on_nid, "target_pin": on_pin},
    {"source_node": tm["g_td2"], "source_pin": "LedgeTransitDest", "target_node": "K2Node_CallFunction_9", "target_pin": "B"},
    {"source_node": E, "source_pin": "bTransiting", "target_node": tm["selg"], "target_pin": "bPickA"},
    {"source_node": tm["selg"], "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_219", "target_pin": "B"},
]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
print("connect fails:", fails)
cp = call("blueprint_query", "compile_blueprint", {"asset_path": ABP})
print("compile:", cp.get("success"), "| err:", cp.get("error_count"), "| warn:", cp.get("warning_count"))
if cp.get("errors"):
    print(json.dumps(cp["errors"], ensure_ascii=False)[:400])
