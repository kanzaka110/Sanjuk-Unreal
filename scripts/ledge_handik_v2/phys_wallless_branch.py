# LedgePhysAlpha 벽없음 분기 (2026-07-21, 유저 요청)
# 증상: Wallless에서 피직스가 빨리 끊겨 '틔는' 느낌.
# 처방: LedgeFBLatch(벽 래치)로 Hold/Fade/FallSpeed 3분기 — 벽=기존 변수값, Wallless=리터럴 노브.
#   Hold 0.4->0.9 / Fade 1.2->2.2 / Fall 1.0->0.45  (가설 — PIE 튜닝 전제. 노브=Select B 핀)
# 배선: VG16(Hold)->SelHold.A, B=0.9 -> CF_56.B / VG17(Fade)->SelFade.A, B=2.2 -> CF_58.B
#       VG10(Fall)->SelFall.A, B=0.45 -> CF_15.B / bPickA <- Get LedgeFBLatch (신규)
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "Ledge_DangleAlpha"
KML = "KismetMathLibrary"
LOG = {"steps": [], "fails": []}


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:250])
    return json.loads(txt)


# 사전 검증 (스테일 ID 방어)
g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": G})
nodes = {n["id"]: n for n in g["nodes"]}
EXPECT = {
    "K2Node_CallFunction_56": ("B", "K2Node_VariableGet_16.LedgePhysicsHoldTime"),
    "K2Node_CallFunction_58": ("B", "K2Node_VariableGet_17.LedgePhysicsFadeTime"),
    "K2Node_CallFunction_15": ("B", "K2Node_VariableGet_10.LedgePhysFallSpeed"),
}
for nid, (pin, want) in EXPECT.items():
    src = None
    for p in nodes[nid]["pins"]:
        if p["name"] == pin:
            src = (p.get("connected_to") or [None])[0]
    if src != want:
        raise SystemExit("앵커 불일치 %s.%s: %s (기대 %s)" % (nid, pin, src, want))
LOG["steps"].append("anchors verified")

# 노드 생성: Get FBLatch + SelectFloat x3
specs = [
    {"temp_id": "g_fb", "node_type": "VariableGet", "variable_name": "LedgeFBLatch", "position": [2400, 1400]},
    {"temp_id": "sel_hold", "node_type": "CallFunction", "function_name": "SelectFloat", "target_class": KML, "position": [2600, 1300]},
    {"temp_id": "sel_fade", "node_type": "CallFunction", "function_name": "SelectFloat", "target_class": KML, "position": [2600, 1450]},
    {"temp_id": "sel_fall", "node_type": "CallFunction", "function_name": "SelectFloat", "target_class": KML, "position": [2600, 1600]},
]
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G, "nodes": specs})
tmap = {}


def harvest(o):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tmap[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v)
    elif isinstance(o, list):
        for e in o:
            harvest(e)


harvest(res)
if len(tmap) != 4:
    raise SystemExit("노드 생성 실패: " + json.dumps(res)[:250])
LOG["steps"].append("nodes: %s" % tmap)

call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": G, "defaults": [
    {"node_id": tmap["sel_hold"], "pin_name": "B", "value": "0.9"},
    {"node_id": tmap["sel_fade"], "pin_name": "B", "value": "2.2"},
    {"node_id": tmap["sel_fall"], "pin_name": "B", "value": "0.45"},
]})

for nid, pin in (("K2Node_CallFunction_56", "B"), ("K2Node_CallFunction_58", "B"), ("K2Node_CallFunction_15", "B")):
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": nid, "pin_name": pin})

conns = [
    {"source_node": "K2Node_VariableGet_16", "source_pin": "LedgePhysicsHoldTime", "target_node": tmap["sel_hold"], "target_pin": "A"},
    {"source_node": "K2Node_VariableGet_17", "source_pin": "LedgePhysicsFadeTime", "target_node": tmap["sel_fade"], "target_pin": "A"},
    {"source_node": "K2Node_VariableGet_10", "source_pin": "LedgePhysFallSpeed", "target_node": tmap["sel_fall"], "target_pin": "A"},
    {"source_node": tmap["g_fb"], "source_pin": "LedgeFBLatch", "target_node": tmap["sel_hold"], "target_pin": "bPickA"},
    {"source_node": tmap["g_fb"], "source_pin": "LedgeFBLatch", "target_node": tmap["sel_fade"], "target_pin": "bPickA"},
    {"source_node": tmap["g_fb"], "source_pin": "LedgeFBLatch", "target_node": tmap["sel_fall"], "target_pin": "bPickA"},
    {"source_node": tmap["sel_hold"], "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_56", "target_pin": "B"},
    {"source_node": tmap["sel_fade"], "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_58", "target_pin": "B"},
    {"source_node": tmap["sel_fall"], "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_15", "target_pin": "B"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
LOG["fails"] = fails
LOG["steps"].append("links %d (%d fails)" % (len(conns), len(fails)))

json.dump(LOG, open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/phys_wallless.json", "w"), indent=1, ensure_ascii=False)
print("PHYS_WALLLESS_DONE fails=%d" % len(fails))
for s in LOG["steps"]:
    print("  " + s)
