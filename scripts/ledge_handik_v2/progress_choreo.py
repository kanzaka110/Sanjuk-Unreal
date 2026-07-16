# v11 — 진행률 기반 안무: mcAdj 소스를 커브에서 스플라인 진행률 (cd-sd)/(td-sd) 로 교체
# 컷 면역(컷=진행률1=도착완료) + 몸 동기화. 커브/모디파이어 무변경 — VLerp.Alpha 배선만 교체 (롤백=재연결)
# 스태거: 선행/후행 remap 창 (방향 부호 td-sd>0 = 우 = R 선행)
# HandTarget: prog/dir 계산 + 멤버 캡처(LedgeUnitProg/LedgeDirPos) + 손 remap
# FootTarget: 캡처 소비 + 발 remap
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
HT = "Ledge_HandTarget"
FT = "Ledge_FootTarget"
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


# ── 0) 변수 ──
VARS = [("LedgeUnitProg", "float", None), ("LedgeDirPos", "bool", None),
        ("LedgeProgLeadStart", "float", "0.0"), ("LedgeProgLeadEnd", "float", "0.7"),
        ("LedgeProgTrailStart", "float", "0.3"), ("LedgeProgTrailEnd", "float", "1.0"),
        ("LedgeFootProgLeadStart", "float", "0.25"), ("LedgeFootProgLeadEnd", "float", "0.85"),
        ("LedgeFootProgTrailStart", "float", "0.4"), ("LedgeFootProgTrailEnd", "float", "1.0")]
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for name, typ, dv in VARS:
    if name in existing:
        continue
    p = {"asset_path": ABP, "name": name, "type": typ, "category": "Ledge|ProgChoreo", "instance_editable": False}
    if dv:
        p["default_value"] = dv
    call("blueprint_query", "add_variable", p)
    LOG["steps"].append("var: " + name)


def remap_cluster(b, pf, y, prog_src, dir_src, leadS, leadE, trailS, trailE, lead_is_A):
    """(prog - StartSel)/(EndSel - StartSel) clamp01. lead_is_A: SelectFloat.A=Lead(참=선행)"""
    b.append({"temp_id": pf + "_gLS", "node_type": "VariableGet", "variable_name": leadS, "position": [200, y]})
    b.append({"temp_id": pf + "_gLE", "node_type": "VariableGet", "variable_name": leadE, "position": [200, y + 70]})
    b.append({"temp_id": pf + "_gTS", "node_type": "VariableGet", "variable_name": trailS, "position": [200, y + 140]})
    b.append({"temp_id": pf + "_gTE", "node_type": "VariableGet", "variable_name": trailE, "position": [200, y + 210]})
    b.append({"temp_id": pf + "_selS", "node_type": "CallFunction", "function_name": "SelectFloat", "target_class": KML, "position": [400, y]})
    b.append({"temp_id": pf + "_selE", "node_type": "CallFunction", "function_name": "SelectFloat", "target_class": KML, "position": [400, y + 120]})
    b.append({"temp_id": pf + "_num", "node_type": "CallFunction", "function_name": "Subtract_DoubleDouble", "target_class": KML, "position": [580, y]})
    b.append({"temp_id": pf + "_den", "node_type": "CallFunction", "function_name": "Subtract_DoubleDouble", "target_class": KML, "position": [580, y + 120]})
    b.append({"temp_id": pf + "_div", "node_type": "CallFunction", "function_name": "Divide_DoubleDouble", "target_class": KML, "position": [760, y + 60]})
    b.append({"temp_id": pf + "_mc", "node_type": "CallFunction", "function_name": "FClamp", "target_class": KML, "position": [940, y + 60]})
    conns = []
    SA, SB = (leadS, trailS) if lead_is_A else (trailS, leadS)
    EA, EB = (leadE, trailE) if lead_is_A else (trailE, leadE)
    gmap = {leadS: pf + "_gLS", leadE: pf + "_gLE", trailS: pf + "_gTS", trailE: pf + "_gTE"}
    conns.append({"source_node": gmap[SA], "source_pin": SA, "target_node": pf + "_selS", "target_pin": "A"})
    conns.append({"source_node": gmap[SB], "source_pin": SB, "target_node": pf + "_selS", "target_pin": "B"})
    conns.append({"source_node": gmap[EA], "source_pin": EA, "target_node": pf + "_selE", "target_pin": "A"})
    conns.append({"source_node": gmap[EB], "source_pin": EB, "target_node": pf + "_selE", "target_pin": "B"})
    conns.append({"source_node": dir_src[0], "source_pin": dir_src[1], "target_node": pf + "_selS", "target_pin": "bPickA"})
    conns.append({"source_node": dir_src[0], "source_pin": dir_src[1], "target_node": pf + "_selE", "target_pin": "bPickA"})
    conns.append({"source_node": prog_src[0], "source_pin": prog_src[1], "target_node": pf + "_num", "target_pin": "A"})
    conns.append({"source_node": pf + "_selS", "source_pin": "ReturnValue", "target_node": pf + "_num", "target_pin": "B"})
    conns.append({"source_node": pf + "_selE", "source_pin": "ReturnValue", "target_node": pf + "_den", "target_pin": "A"})
    conns.append({"source_node": pf + "_selS", "source_pin": "ReturnValue", "target_node": pf + "_den", "target_pin": "B"})
    conns.append({"source_node": pf + "_num", "source_pin": "ReturnValue", "target_node": pf + "_div", "target_pin": "A"})
    conns.append({"source_node": pf + "_den", "source_pin": "ReturnValue", "target_node": pf + "_div", "target_pin": "B"})
    conns.append({"source_node": pf + "_div", "source_pin": "ReturnValue", "target_node": pf + "_mc", "target_pin": "Value"})
    return conns


# ── 1) HandTarget ──
g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": HT})
nodes = {n["id"]: n for n in g["nodes"]}
def pins(n): return {p["name"]: p for p in n.get("pins", [])}
def conn(n, pin): return (pins(n).get(pin, {}).get("connected_to") or [])
entry = None
vlerps = {}   # 손 VLerp: A<-Get LedgeHandAnchorL/R
fblatch_set = None
for nid, n in nodes.items():
    cls = n.get("class", "")
    t = (n.get("title") or "").split("\n")[0]
    if "FunctionEntry" in cls:
        entry = nid
    if t == "Set LedgeFBLatch":
        fblatch_set = nid
    if t.startswith("Lerp (Vector)"):
        a = (conn(n, "A") or [""])[0].split(".")[0]
        at = (nodes.get(a, {}).get("title") or "")
        if "LedgeHandAnchorL" in at:
            vlerps["L"] = nid
        if "LedgeHandAnchorR" in at:
            vlerps["R"] = nid
assert entry and fblatch_set and len(vlerps) == 2, (entry, fblatch_set, vlerps)
spec = [
    # prog = clamp(sel((cd-sd)/(td-sd),0, |den|>1), 0,1) / dir = (td-sd)>0
    {"temp_id": "subN", "node_type": "CallFunction", "function_name": "Subtract_DoubleDouble", "target_class": KML, "position": [-800, 2600]},
    {"temp_id": "subD", "node_type": "CallFunction", "function_name": "Subtract_DoubleDouble", "target_class": KML, "position": [-800, 2700]},
    {"temp_id": "absD", "node_type": "CallFunction", "function_name": "Abs", "target_class": KML, "position": [-640, 2760]},
    {"temp_id": "gtD", "node_type": "CallFunction", "function_name": "Greater_DoubleDouble", "target_class": KML, "position": [-480, 2760]},
    {"temp_id": "divP", "node_type": "CallFunction", "function_name": "Divide_DoubleDouble", "target_class": KML, "position": [-640, 2620]},
    {"temp_id": "selP", "node_type": "CallFunction", "function_name": "SelectFloat", "target_class": KML, "position": [-480, 2620]},
    {"temp_id": "clP", "node_type": "CallFunction", "function_name": "FClamp", "target_class": KML, "position": [-320, 2620]},
    {"temp_id": "dirP", "node_type": "CallFunction", "function_name": "Greater_DoubleDouble", "target_class": KML, "position": [-480, 2860]},
    {"temp_id": "setProg", "node_type": "VariableSet", "variable_name": "LedgeUnitProg", "position": [-160, 2560]},
    {"temp_id": "setDir", "node_type": "VariableSet", "variable_name": "LedgeDirPos", "position": [20, 2560]},
]
b = []
c_all = []
# 손 remap: R = lead_is_A(True: dirPos->Lead), L = lead_is_A(False)
c_all += remap_cluster(b, "hR", 3000, ("clP", "ReturnValue"), ("dirP", "ReturnValue"),
                       "LedgeProgLeadStart", "LedgeProgLeadEnd", "LedgeProgTrailStart", "LedgeProgTrailEnd", True)
c_all += remap_cluster(b, "hL", 3400, ("clP", "ReturnValue"), ("dirP", "ReturnValue"),
                       "LedgeProgLeadStart", "LedgeProgLeadEnd", "LedgeProgTrailStart", "LedgeProgTrailEnd", False)
for e in b:
    e["position"][0] += -800
    e["position"][1] += 0
spec += b
tm = {}
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": HT, "nodes": spec})
harvest(res, tm)
if len(tm) != len(spec):
    made = set(tm)
    raise SystemExit("HT 노드 %d/%d missing=%s" % (len(tm), len(spec), [n["temp_id"] for n in spec if n["temp_id"] not in made]))
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": HT, "defaults": [
    {"node_id": tm["gtD"], "pin_name": "B", "value": "1.0"},
    {"node_id": tm["selP"], "pin_name": "B", "value": "0.0"},
    {"node_id": tm["dirP"], "pin_name": "B", "value": "0.0"},
]})
conns = [
    {"source_node": entry, "source_pin": "B", "target_node": tm["subN"], "target_pin": "A"},          # cd
    {"source_node": entry, "source_pin": "InputPin3", "target_node": tm["subN"], "target_pin": "B"},  # sd
    {"source_node": entry, "source_pin": "InputPin4", "target_node": tm["subD"], "target_pin": "A"},  # td
    {"source_node": entry, "source_pin": "InputPin3", "target_node": tm["subD"], "target_pin": "B"},
    {"source_node": tm["subD"], "source_pin": "ReturnValue", "target_node": tm["absD"], "target_pin": "A"},
    {"source_node": tm["absD"], "source_pin": "ReturnValue", "target_node": tm["gtD"], "target_pin": "A"},
    {"source_node": tm["subN"], "source_pin": "ReturnValue", "target_node": tm["divP"], "target_pin": "A"},
    {"source_node": tm["subD"], "source_pin": "ReturnValue", "target_node": tm["divP"], "target_pin": "B"},
    {"source_node": tm["divP"], "source_pin": "ReturnValue", "target_node": tm["selP"], "target_pin": "A"},
    {"source_node": tm["gtD"], "source_pin": "ReturnValue", "target_node": tm["selP"], "target_pin": "bPickA"},
    {"source_node": tm["selP"], "source_pin": "ReturnValue", "target_node": tm["clP"], "target_pin": "Value"},
    {"source_node": tm["clP"], "source_pin": "ReturnValue", "target_node": tm["setProg"], "target_pin": "LedgeUnitProg"},
    {"source_node": tm["subD"], "source_pin": "ReturnValue", "target_node": tm["dirP"], "target_pin": "A"},
    {"source_node": tm["dirP"], "source_pin": "ReturnValue", "target_node": tm["setDir"], "target_pin": "LedgeDirPos"},
]
for c in c_all:
    c["source_node"] = tm.get(c["source_node"], c["source_node"])
    c["target_node"] = tm.get(c["target_node"], c["target_node"])
    conns.append(c)
# VLerp.Alpha 재배선
for side in ("L", "R"):
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": HT, "node_id": vlerps[side], "pin_name": "Alpha"})
    conns.append({"source_node": tm["h%s_mc" % side], "source_pin": "ReturnValue", "target_node": vlerps[side], "target_pin": "Alpha"})
# exec: SetFBLatch -> setProg -> setDir -> (기존 다음)
nxt = (conn(nodes[fblatch_set], "then") or [""])[0].split(".")[0]
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": HT, "node_id": fblatch_set, "pin_name": "then"})
conns += [
    {"source_node": fblatch_set, "source_pin": "then", "target_node": tm["setProg"], "target_pin": "execute"},
    {"source_node": tm["setProg"], "source_pin": "then", "target_node": tm["setDir"], "target_pin": "execute"},
    {"source_node": tm["setDir"], "source_pin": "then", "target_node": nxt, "target_pin": "execute"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"HT": fails})
LOG["steps"].append("HT: %d links %d fail" % (len(conns), len(fails)))

# ── 2) FootTarget ──
g2 = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": FT})
n2 = {n["id"]: n for n in g2["nodes"]}
def conn2(n, pin):
    P = {p["name"]: p for p in n.get("pins", [])}
    return (P.get(pin, {}).get("connected_to") or [])
fvl = {}
for nid, n in n2.items():
    if (n.get("title") or "").startswith("Lerp (Vector)"):
        a = (conn2(n, "A") or [""])[0].split(".")[0]
        at = (n2.get(a, {}).get("title") or "")
        if "LedgeFootAnchorL" in at:
            fvl["L"] = nid
        if "LedgeFootAnchorR" in at:
            fvl["R"] = nid
assert len(fvl) == 2, fvl
spec2 = [
    {"temp_id": "gProg", "node_type": "VariableGet", "variable_name": "LedgeUnitProg", "position": [-800, 600]},
    {"temp_id": "gDir", "node_type": "VariableGet", "variable_name": "LedgeDirPos", "position": [-800, 700]},
]
b2 = []
c2_all = []
c2_all += remap_cluster(b2, "fR", 800, ("gProg", "LedgeUnitProg"), ("gDir", "LedgeDirPos"),
                        "LedgeFootProgLeadStart", "LedgeFootProgLeadEnd", "LedgeFootProgTrailStart", "LedgeFootProgTrailEnd", True)
c2_all += remap_cluster(b2, "fL", 1200, ("gProg", "LedgeUnitProg"), ("gDir", "LedgeDirPos"),
                        "LedgeFootProgLeadStart", "LedgeFootProgLeadEnd", "LedgeFootProgTrailStart", "LedgeFootProgTrailEnd", False)
for e in b2:
    e["position"][0] += -800
spec2 += b2
tm2 = {}
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": FT, "nodes": spec2})
harvest(res, tm2)
if len(tm2) != len(spec2):
    made = set(tm2)
    raise SystemExit("FT 노드 %d/%d missing=%s" % (len(tm2), len(spec2), [n["temp_id"] for n in spec2 if n["temp_id"] not in made]))
conns2 = []
for c in c2_all:
    c["source_node"] = tm2.get(c["source_node"], c["source_node"])
    c["target_node"] = tm2.get(c["target_node"], c["target_node"])
    conns2.append(c)
for side in ("L", "R"):
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": FT, "node_id": fvl[side], "pin_name": "Alpha"})
    conns2.append({"source_node": tm2["f%s_mc" % side], "source_pin": "ReturnValue", "target_node": fvl[side], "target_pin": "Alpha"})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": FT, "connections": conns2})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"FT": fails})
LOG["steps"].append("FT: %d links %d fail" % (len(conns2), len(fails)))

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/prog_choreo.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("PROG_CHOREO_DONE errors=%s" % ("none" if not LOG["errors"] else json.dumps(LOG["errors"], ensure_ascii=False)[:400]))
