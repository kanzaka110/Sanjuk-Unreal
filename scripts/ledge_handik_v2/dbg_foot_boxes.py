# LedgeDebugs 발 IK 디버그 박스 4개 (v9.3) — 손 패턴 미러
#   FootAnchorL/R = 4cm 어두운 초록/주황 (출발지 래치), FootDestL/R = 5cm 밝은 초록/주황 (도착지 라이브)
# 사전: Ledge_FootTarget에 LedgeFootDestL/R 미러 Set 추가 (dest Add 노드 출력)
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
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


def harvest(obj, tmap):
    if isinstance(obj, dict):
        if obj.get("temp_id") and (obj.get("node_id") or obj.get("id")):
            tmap[obj["temp_id"]] = obj.get("node_id") or obj.get("id")
        else:
            for v in obj.values():
                harvest(v, tmap)
    elif isinstance(obj, list):
        for e in obj:
            harvest(e, tmap)


# ── 1) 미러 변수 ──
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for v in ("LedgeFootDestL", "LedgeFootDestR"):
    if v not in existing:
        call("blueprint_query", "add_variable",
             {"asset_path": ABP, "name": v, "type": "struct:Vector", "category": "Ledge|FootIK", "instance_editable": False})
        LOG["steps"].append("var added: " + v)

# ── 2) Ledge_FootTarget: dest 노드/꼬리 구조 식별 → Set 2개 스플라이스 ──
FT = "Ledge_FootTarget"
g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": FT})
nodes = {n["id"]: n for n in g["nodes"]}
def pins(n): return {p["name"]: p for p in n.get("pins", [])}
def conn(n, pin): return (pins(n).get(pin, {}).get("connected_to") or [])
# dest = Add(vector+vector) with B<-Get LedgeMoveOffset, A<-TransformLocation
dest = {}
tail = None
consts = {}
for nid, n in nodes.items():
    t = n.get("title") or ""
    if t.startswith("Transform Location"):
        loc = pins(n).get("Location", {}).get("default_value", "")
        if loc.startswith("7.17"):
            consts["L"] = nid
        elif loc.startswith("-7.08"):
            consts["R"] = nid
    if t == "Set LedgeFootIKAlphaR":
        tail = nid
for nid, n in nodes.items():
    if (n.get("title") or "").startswith("vector + vector"):
        bsrc = (conn(n, "B") or [""])[0]
        asrc = (conn(n, "A") or [""])[0]
        if "LedgeMoveOffset" in str(nodes.get(bsrc.split(".")[0], {}).get("title", "")):
            for s, cn in consts.items():
                if asrc.split(".")[0] == cn:
                    dest[s] = nid
if len(dest) != 2 or not tail:
    raise SystemExit("FT 구조 식별 실패: dest=%s tail=%s" % (dest, tail))
LOG["steps"].append("FT dest=%s tail=%s" % (dest, tail))
tm = {}
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": FT, "nodes": [
    {"temp_id": "sdL", "node_type": "VariableSet", "variable_name": "LedgeFootDestL", "position": [4450, 500]},
    {"temp_id": "sdR", "node_type": "VariableSet", "variable_name": "LedgeFootDestR", "position": [4650, 500]},
]})
harvest(res, tm)
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": FT, "connections": [
    {"source_node": dest["L"], "source_pin": "ReturnValue", "target_node": tm["sdL"], "target_pin": "LedgeFootDestL"},
    {"source_node": dest["R"], "source_pin": "ReturnValue", "target_node": tm["sdR"], "target_pin": "LedgeFootDestR"},
    {"source_node": tail, "source_pin": "then", "target_node": tm["sdL"], "target_pin": "execute"},
    {"source_node": tm["sdL"], "source_pin": "then", "target_node": tm["sdR"], "target_pin": "execute"},
]})
f1 = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if f1:
    LOG["errors"].append({"ft": f1})
LOG["steps"].append("FT dest mirror wired (%d fails)" % len(f1))

# ── 3) LedgeDebugs: 게터4 + 박스4 스플라이스 (CF_18 -> ... -> FunctionResult_1) ──
DG = "LedgeDebugs"
BOXES = [  # (temp, var, extent, color, thickness)
    ("bFAL", "LedgeFootAnchorL", "4.0,4.0,4.0", "(R=0.0,G=0.35,B=0.0,A=1.0)", "1.5"),
    ("bFAR", "LedgeFootAnchorR", "4.0,4.0,4.0", "(R=0.35,G=0.18,B=0.0,A=1.0)", "1.5"),
    ("bFDL", "LedgeFootDestL", "5.0,5.0,5.0", "(R=0.0,G=1.0,B=0.0,A=1.0)", "2.0"),
    ("bFDR", "LedgeFootDestR", "5.0,5.0,5.0", "(R=1.0,G=0.5,B=0.0,A=1.0)", "2.0"),
]
spec, defaults, conns = [], [], []
for i, (t, var, ext, col, th) in enumerate(BOXES):
    spec.append({"temp_id": "g_" + t, "node_type": "VariableGet", "variable_name": var, "position": [2900 + i * 260, 900]})
    spec.append({"temp_id": t, "node_type": "CallFunction", "function_name": "DrawDebugBox",
                 "target_class": "KismetSystemLibrary", "position": [2900 + i * 260, 700]})
    defaults += [{"node_id": t, "pin_name": "Extent", "value": ext},
                 {"node_id": t, "pin_name": "LineColor", "value": col},
                 {"node_id": t, "pin_name": "Thickness", "value": th},
                 {"node_id": t, "pin_name": "Duration", "value": "0.0"}]
    conns.append({"source_node": "g_" + t, "source_pin": var, "target_node": t, "target_pin": "Center"})
tm2 = {}
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": DG, "nodes": spec})
harvest(res, tm2)
if len(tm2) != len(spec):
    raise SystemExit("LedgeDebugs 노드 생성 %d/%d" % (len(tm2), len(spec)))
for d in defaults:
    d["node_id"] = tm2[d["node_id"]]
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": DG, "defaults": defaults})
call("blueprint_query", "disconnect_pins",
     {"asset_path": ABP, "graph_name": DG, "node_id": "K2Node_CallFunction_18", "pin_name": "then"})
chain = ["K2Node_CallFunction_18"] + [tm2[b[0]] for b in BOXES] + ["K2Node_FunctionResult_1"]
for i in range(len(chain) - 1):
    conns.append({"source_node": chain[i], "source_pin": "then", "target_node": chain[i + 1], "target_pin": "execute"})
for c in conns:
    c["source_node"] = tm2.get(c["source_node"], c["source_node"])
    c["target_node"] = tm2.get(c["target_node"], c["target_node"])
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": DG, "connections": conns})
f2 = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if f2:
    LOG["errors"].append({"dbg": f2})
LOG["steps"].append("debug boxes wired (%d fails)" % len(f2))

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/dbg_foot.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("DBG_FOOT_DONE errors=%s" % (LOG["errors"] if LOG["errors"] else "none"))
