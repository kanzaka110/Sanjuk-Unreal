# Phase T — HandTarget 트랜짓 결정적 슬라이드 배선
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


def src(nid, pin):
    for p in nodes.get(nid, {}).get("pins", []):
        if p["name"] == pin and p.get("direction") == "input":
            c = p.get("connected_to") or []
            return c[0] if c else None


entry_outs = [p["name"] for p in nodes[E]["pins"] if p.get("direction") == "output"]
assert "bTransiting" in entry_outs and "TransitDest" in entry_outs, entry_outs
assert src("K2Node_CallFunction_19", "A") == "K2Node_CallFunction_18.ReturnValue"
assert src("K2Node_CallFunction_220", "A") == "K2Node_CallFunction_213.ReturnValue"
then29 = [p.get("connected_to") for p in nodes["K2Node_VariableSet_29"]["pins"]
          if p["name"] == "then" and p.get("direction") == "output"]
assert not then29[0], "VS_29 not tail: %s" % then29
print("anchors OK; VS_0 value <-", src("K2Node_VariableSet_0", "LedgeUnitMoving"))

res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": HT, "nodes": [
    {"temp_id": "or2", "node_type": "CallFunction", "function_name": "BooleanOR", "target_class": KML, "position": [600, 3050]},
    {"temp_id": "g_prev", "node_type": "VariableGet", "variable_name": "LedgePrevTransit", "position": [600, 3200]},
    {"temp_id": "notp", "node_type": "CallFunction", "function_name": "Not_PreBool", "target_class": KML, "position": [780, 3200]},
    {"temp_id": "and_edge", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [960, 3150]},
    {"temp_id": "or_edge", "node_type": "CallFunction", "function_name": "BooleanOR", "target_class": KML, "position": [1140, 3100]},
    {"temp_id": "sub_t", "node_type": "CallFunction", "function_name": "Subtract_VectorVector", "target_class": KML, "position": [3400, 2700]},
    {"temp_id": "sel_t", "node_type": "CallFunction", "function_name": "SelectVector", "target_class": KML, "position": [3600, 2650]},
    {"temp_id": "set_prev", "node_type": "VariableSet", "variable_name": "LedgePrevTransit", "position": [9000, 1200]},
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
assert len(tm) == 8, json.dumps(res)[:400]
print("nodes:", tm)

for nid, pin in [("K2Node_CallFunction_212", "A"), ("K2Node_VariableSet_0", "LedgeUnitMoving"),
                 ("K2Node_CallFunction_19", "A"), ("K2Node_CallFunction_220", "A")]:
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": HT,
                                                "node_id": nid, "pin_name": pin})

rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": [
    {"source_node": E, "source_pin": "InputPin2", "target_node": tm["or2"], "target_pin": "A"},
    {"source_node": E, "source_pin": "bTransiting", "target_node": tm["or2"], "target_pin": "B"},
    {"source_node": tm["or2"], "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_212", "target_pin": "A"},
    {"source_node": tm["or2"], "source_pin": "ReturnValue", "target_node": "K2Node_VariableSet_0", "target_pin": "LedgeUnitMoving"},
    {"source_node": tm["g_prev"], "source_pin": "LedgePrevTransit", "target_node": tm["notp"], "target_pin": "A"},
    {"source_node": E, "source_pin": "bTransiting", "target_node": tm["and_edge"], "target_pin": "A"},
    {"source_node": tm["notp"], "source_pin": "ReturnValue", "target_node": tm["and_edge"], "target_pin": "B"},
    {"source_node": "K2Node_CallFunction_213", "source_pin": "ReturnValue", "target_node": tm["or_edge"], "target_pin": "A"},
    {"source_node": tm["and_edge"], "source_pin": "ReturnValue", "target_node": tm["or_edge"], "target_pin": "B"},
    {"source_node": tm["or_edge"], "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_220", "target_pin": "A"},
    {"source_node": "K2Node_CallFunction_76", "source_pin": "ReturnValue", "target_node": tm["sub_t"], "target_pin": "A"},
    {"source_node": E, "source_pin": "TransitDest", "target_node": tm["sub_t"], "target_pin": "B"},
    {"source_node": tm["sub_t"], "source_pin": "ReturnValue", "target_node": tm["sel_t"], "target_pin": "A"},
    {"source_node": "K2Node_CallFunction_18", "source_pin": "ReturnValue", "target_node": tm["sel_t"], "target_pin": "B"},
    {"source_node": E, "source_pin": "bTransiting", "target_node": tm["sel_t"], "target_pin": "bPickA"},
    {"source_node": tm["sel_t"], "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_19", "target_pin": "A"},
    {"source_node": E, "source_pin": "bTransiting", "target_node": tm["set_prev"], "target_pin": "LedgePrevTransit"},
    {"source_node": "K2Node_VariableSet_29", "source_pin": "then", "target_node": tm["set_prev"], "target_pin": "execute"},
]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
print("connect fails:", fails)
cp = call("blueprint_query", "compile_blueprint", {"asset_path": ABP})
print("compile:", cp.get("success"), "| err:", cp.get("error_count"), "| warn:", cp.get("warning_count"))
if cp.get("errors"):
    print(json.dumps(cp["errors"], ensure_ascii=False)[:400])
