# Phase T3 — 트랜짓 유효 게이트: bTransiting 소비 4곳을 (bt AND dist<800)로 교체
# 근거: 점프 진입 시 bt=1 + ncc=(0,0,0) 실측 — 무효 트랜짓이 쓰레기 벡터/앵커 동결 유발
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


g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": HT})
nodes = {n["id"]: n for n in g["nodes"]}


def title(nid):
    return str(nodes.get(nid, {}).get("title", "?")).split(chr(10))[0]


def src(nid, pin):
    for p in nodes.get(nid, {}).get("pins", []):
        if p["name"] == pin and p.get("direction") == "input":
            c = p.get("connected_to") or []
            return c[0] if c else None


# 현재 raw bTransiting 소비처 확인 (기대: or2.B / and_edge.A / sel_t.bPickA / selg.bPickA / set_prev값 / T2 vlen.A / selv.A)
consumers = []
for nid, n in nodes.items():
    for p in n.get("pins", []):
        if p.get("direction") == "input":
            for c in p.get("connected_to") or []:
                if c == "K2Node_FunctionEntry_0.bTransiting":
                    consumers.append((nid, p["name"], title(nid)))
print("raw bt consumers:", consumers)

# 게이트 노드: dist = Distance(손기준중심 CF_76, Get LedgeTransitDest), lt = dist < 800, andv = bt AND lt
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": HT, "nodes": [
    {"temp_id": "g_td3", "node_type": "VariableGet", "variable_name": "LedgeTransitDest", "position": [150, 3700]},
    {"temp_id": "distv", "node_type": "CallFunction", "function_name": "Vector_Distance", "target_class": KML, "position": [330, 3700]},
    {"temp_id": "lt800", "node_type": "CallFunction", "function_name": "Less_DoubleDouble", "target_class": KML, "position": [510, 3700]},
    {"temp_id": "andv", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [690, 3650]},
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
assert len(tm) == 4, json.dumps(res)[:400]
print("nodes:", tm)
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": HT, "defaults": [
    {"node_id": tm["lt800"], "pin_name": "B", "value": "800.0"},
]})

# 게이트 배선
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": [
    {"source_node": "K2Node_CallFunction_76", "source_pin": "ReturnValue", "target_node": tm["distv"], "target_pin": "V1"},
    {"source_node": tm["g_td3"], "source_pin": "LedgeTransitDest", "target_node": tm["distv"], "target_pin": "V2"},
    {"source_node": tm["distv"], "source_pin": "ReturnValue", "target_node": tm["lt800"], "target_pin": "A"},
    {"source_node": E, "source_pin": "bTransiting", "target_node": tm["andv"], "target_pin": "A"},
    {"source_node": tm["lt800"], "source_pin": "ReturnValue", "target_node": tm["andv"], "target_pin": "B"},
]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
print("gate wiring fails:", fails)

# raw bt 소비 4곳 교체: or2(CF_5).B / and_edge(CF_7).A / sel_t(CF_10).bPickA / selg(CF_15).bPickA / set_prev(VS_1) 값
targets = [
    ("K2Node_CallFunction_5", "B"),
    ("K2Node_CallFunction_7", "A"),
    ("K2Node_CallFunction_10", "bPickA"),
    ("K2Node_CallFunction_15", "bPickA"),
    ("K2Node_VariableSet_1", "LedgePrevTransit"),
]
conns = []
for nid, pin in targets:
    cur = src(nid, pin)
    if cur != "K2Node_FunctionEntry_0.bTransiting":
        print("SKIP(소스 다름)", nid, pin, cur)
        continue
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": HT,
                                                "node_id": nid, "pin_name": pin})
    conns.append({"source_node": tm["andv"], "source_pin": "ReturnValue",
                  "target_node": nid, "target_pin": pin})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
print("rewire fails:", fails, "| rewired:", len(conns))

cp = call("blueprint_query", "compile_blueprint", {"asset_path": ABP})
print("compile:", cp.get("success"), "| err:", cp.get("error_count"), "| warn:", cp.get("warning_count"))
if cp.get("errors"):
    print(json.dumps(cp["errors"], ensure_ascii=False)[:400])
