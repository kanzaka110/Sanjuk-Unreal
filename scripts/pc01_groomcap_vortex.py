# PC_01_BP CalcWindAt: Vortex 기여 추가 (4번째 루프)
#   축=컴포넌트 Up, 원통 판정(반경 Radius, |축거리|<=Height), t=rdist/Radius, mult=(1-t)^Falloff
#   contrib = (tdir*Tangential + rdir*Radial + up*Axial) * mult
#   exec: loopR.Completed -> [기존 Result] 를 -> gaaX -> loopX -> ... -> Result 로 삽입
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "CalcWindAt"
KML = "KismetMathLibrary"
LOG = {"steps": [], "errors": []}
atexit.register(lambda: print(json.dumps(LOG, ensure_ascii=False, indent=1)))


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def nid_of(r):
    return r.get("node_id") or r.get("id")


def node_pins(nid):
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": FN, "node_id": nid})
    return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]


def ext_var(var, x, y):
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": FN, "node_type": "VariableGet",
              "variable_name": var, "target_class": "SBVortexWindComponent", "position": [x, y]})
    nid = nid_of(r)
    call("blueprint_query", "set_node_property",
         {"asset_path": BP, "graph_name": FN, "node_id": nid,
          "property_name": "VariableReference",
          "value": '(MemberParent=/Script/SB2.SBVortexWindComponent,MemberName="%s",bSelfContext=False)' % var})
    call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": FN, "node_id": nid})
    assert var in node_pins(nid), "ext %s 실패" % var
    return nid


# ═══ 1) 앵커 탐색: loopR / Result / entry(Point) ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
nodes = {n["id"]: n for n in g["nodes"]}
def P(n): return {p["name"]: p for p in n.get("pins", [])}
loopR = result = entry = None
for nid, n in nodes.items():
    cls = n.get("class", "")
    pn = P(n)
    if "MacroInstance" in cls and pn.get("Array Element", {}).get("type") == "object:SBRadialWindActor":
        loopR = nid
    if "FunctionResult" in cls:
        result = nid
    if "FunctionEntry" in cls:
        entry = nid
assert loopR and result and entry, "앵커 실패: %s %s %s" % (loopR, result, entry)
LOG["steps"].append("loopR=%s result=%s entry=%s" % (loopR, result, entry))

# ═══ 2) ext 게터 6종 + 개별 스폰 ═══
EXT = {}
for i, var in enumerate(["Radius", "FalloffExponent", "TangentialStrength", "RadialStrength", "AxialStrength", "Height"]):
    EXT[var] = ext_var(var, 1500 + (i % 3) * 250, 3600 + (i // 3) * 150)
LOG["steps"].append("ext 6 OK")

# ═══ 3) 본체 벌크 ═══
nodes_spec, defaults, conns = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    nodes_spec.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(nid, pin, val):
    defaults.append({"node_id": nid, "pin_name": pin, "value": val})


def F(tid, fn, x, y, cls=KML):
    N(tid, "CallFunction", x, y, function_name=fn, target_class=cls)


F("gaaX", "GetAllActorsOfClass", 400, 3500, "GameplayStatics")
D("gaaX", "ActorClass", "/Script/SB2.SBVortexWindActor")
N("loopX", "ForEachLoop", 700, 3500)
C("gaaX", "OutActors", "loopX", "Array")
F("gcX", "GetComponentByClass", 950, 3600, "Actor")
D("gcX", "ComponentClass", "/Script/SB2.SBVortexWindComponent")
C("loopX", "Array Element", "gcX", "self")
for var in EXT:
    C("gcX", "ReturnValue", EXT[var], "self")
F("locX", "K2_GetComponentLocation", 1150, 3650, "SceneComponent")
C("gcX", "ReturnValue", "locX", "self")
F("upX", "GetUpVector", 1150, 3800, "SceneComponent")
C("gcX", "ReturnValue", "upX", "self")
F("dX", "Subtract_VectorVector", 1350, 3650)
C(entry, "Point", "dX", "A")
C("locX", "ReturnValue", "dX", "B")
F("dotA", "Dot_VectorVector", 1550, 3750)
C("dX", "ReturnValue", "dotA", "A")
C("upX", "ReturnValue", "dotA", "B")
F("upS", "Multiply_VectorFloat", 1750, 3800)
C("upX", "ReturnValue", "upS", "A")
C("dotA", "ReturnValue", "upS", "B")
F("radV", "Subtract_VectorVector", 1950, 3700)
C("dX", "ReturnValue", "radV", "A")
C("upS", "ReturnValue", "radV", "B")
F("rdist", "VSize", 2150, 3700)
C("radV", "ReturnValue", "rdist", "A")
F("inR", "LessEqual_DoubleDouble", 2350, 3600)
C("rdist", "ReturnValue", "inR", "A")
C(EXT["Radius"], "Radius", "inR", "B")
F("absA", "Abs", 2350, 3750)
C("dotA", "ReturnValue", "absA", "A")
F("inH", "LessEqual_DoubleDouble", 2550, 3750)
C("absA", "ReturnValue", "inH", "A")
C(EXT["Height"], "Height", "inH", "B")
F("andX", "BooleanAND", 2700, 3650)
C("inR", "ReturnValue", "andX", "A")
C("inH", "ReturnValue", "andX", "B")
N("brX", "Branch", 1300, 3450)
C("andX", "ReturnValue", "brX", "Condition")
# 방향/감쇠
F("fmaxR", "FMax", 2150, 3850)
C("rdist", "ReturnValue", "fmaxR", "A")
D("fmaxR", "B", "1.0")
F("rdir", "Divide_VectorFloat", 2350, 3900)
C("radV", "ReturnValue", "rdir", "A")
C("fmaxR", "ReturnValue", "rdir", "B")
F("tdir", "Cross_VectorVector", 2550, 3950)
C("upX", "ReturnValue", "tdir", "A")
C("rdir", "ReturnValue", "tdir", "B")
F("fmaxRad", "FMax", 2550, 3850)
C(EXT["Radius"], "Radius", "fmaxRad", "A")
D("fmaxRad", "B", "0.001")
F("tt", "Divide_DoubleDouble", 2750, 3850)
C("rdist", "ReturnValue", "tt", "A")
C("fmaxRad", "ReturnValue", "tt", "B")
F("oneT", "Subtract_DoubleDouble", 2950, 3850)
D("oneT", "A", "1.0")
C("tt", "ReturnValue", "oneT", "B")
F("powX", "MultiplyMultiply_FloatFloat", 3150, 3850)
C("oneT", "ReturnValue", "powX", "Base")
C(EXT["FalloffExponent"], "FalloffExponent", "powX", "Exp")
# 3성분 합성
F("tv", "Multiply_VectorFloat", 2950, 4050)
C("tdir", "ReturnValue", "tv", "A")
C(EXT["TangentialStrength"], "TangentialStrength", "tv", "B")
F("rv", "Multiply_VectorFloat", 2950, 4200)
C("rdir", "ReturnValue", "rv", "A")
C(EXT["RadialStrength"], "RadialStrength", "rv", "B")
F("av", "Multiply_VectorFloat", 2950, 4350)
C("upX", "ReturnValue", "av", "A")
C(EXT["AxialStrength"], "AxialStrength", "av", "B")
F("sum1", "Add_VectorVector", 3150, 4100)
C("tv", "ReturnValue", "sum1", "A")
C("rv", "ReturnValue", "sum1", "B")
F("sum2", "Add_VectorVector", 3350, 4200)
C("sum1", "ReturnValue", "sum2", "A")
C("av", "ReturnValue", "sum2", "B")
F("scaled", "Multiply_VectorFloat", 3550, 4000)
C("sum2", "ReturnValue", "scaled", "A")
C("powX", "ReturnValue", "scaled", "B")
N("getAccX", "VariableGet", 3550, 4200, variable_name="WdAccum")
F("addX", "Add_VectorVector", 3750, 4100)
C("getAccX", "WdAccum", "addX", "A")
C("scaled", "ReturnValue", "addX", "B")
N("setAccX", "VariableSet", 3950, 3450, variable_name="WdAccum")
C("addX", "ReturnValue", "setAccX", "WdAccum")

res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": FN, "nodes": nodes_spec})
tm = {}
def hv(o):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tm[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                hv(v)
    elif isinstance(o, list):
        for e in o:
            hv(e)
hv(res)
assert len(tm) == len(nodes_spec), "노드 %d/%d" % (len(tm), len(nodes_spec))
m = dict(tm)
m.update(EXT)
for d in defaults:
    d["node_id"] = m.get(d["node_id"], d["node_id"])
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": FN, "defaults": defaults})
dfail = [x for x in (rd.get("results") or []) if not x.get("success", True)]
if dfail:
    LOG["errors"].append({"defaults": dfail})

# exec: loopR.Completed 재배선
call("blueprint_query", "disconnect_pins",
     {"asset_path": BP, "graph_name": FN,
      "source_node": loopR, "source_pin": "Completed", "target_node": result, "target_pin": "execute"})
ex = [
    {"source_node": loopR, "source_pin": "Completed", "target_node": "gaaX", "target_pin": "execute"},
    {"source_node": "gaaX", "source_pin": "then", "target_node": "loopX", "target_pin": "Exec"},
    {"source_node": "loopX", "source_pin": "LoopBody", "target_node": "brX", "target_pin": "execute"},
    {"source_node": "brX", "source_pin": "then", "target_node": "setAccX", "target_pin": "execute"},
    {"source_node": "loopX", "source_pin": "Completed", "target_node": result, "target_pin": "execute"},
]
for c in conns + ex:
    c["source_node"] = m.get(c["source_node"], c["source_node"])
    c["target_node"] = m.get(c["target_node"], c["target_node"])
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": conns + ex})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"conns": fails})
LOG["steps"].append("links: %d req %d fail" % (len(conns) + len(ex), len(fails)))

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])
# 미연결 감사
g2 = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
for n in g2["nodes"]:
    for p in n.get("pins", []):
        if p.get("direction") != "input" or p.get("connected_to"):
            continue
        nm = p.get("name")
        if nm in ("Condition", "Point", "Array", "InVec") or (nm in ("A", "B") and not p.get("default_value")) or (nm == "self" and "VariableGet" in n.get("class", "")):
            LOG["errors"].append({"unconnected": [n["id"], (n.get("title") or "")[:36], nm]})
