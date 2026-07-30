# BP_GroomWindCap (ActorComponent) 빌드: 그룸 윈드 소스 크기 10 캡
#  - BeginPlay: 오너의 SBGroomComponent 수집 + 원본 WindScale 캐시
#  - Tick: |CalcWindAt(머리)| > GroomWindMax 면 factor=Max/mag, 아니면 1 → WindScale = base*factor
#  - CalcWindAt = wind_debug_overlay_build v2와 동일 로직 (Global AABB/Priority + Directional + Radial 벡터합)
# 함정 반영: §2 CallArrayFunction, §3 클래스핀, §9 ext Get/Set 수리, §17 BreakVector, §19 핀타입 탐색,
#           §20 GetComponentByClass(퓨어) 파생 접근, §15 SelectFloat/bPickA, div0 가드 FMax
# 마지막에 PC_01_BP 에 컴포넌트 추가 + 양쪽 컴파일. 저장은 수동(P4).
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/BP_GroomWindCap"
PC01 = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "CalcWindAt"
KML = "KismetMathLibrary"
KAL_REF = "(MemberParent=\"/Script/CoreUObject.Class'/Script/Engine.KismetArrayLibrary'\",MemberName=\"%s\")"
GS = "GameplayStatics"
LOG = {"steps": [], "errors": []}


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


def node_id_of(r):
    nid = r.get("node_id") or r.get("id")
    if not nid:
        tm = {}
        harvest(r, tm)
        nid = list(tm.values())[0] if tm else None
    return nid


def node_pins(graph, nid):
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": graph, "node_id": nid})
    return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]


def bulk_nodes(graph, nodes):
    res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": graph, "nodes": nodes})
    tm = {}
    harvest(res, tm)
    if len(tm) != len(nodes):
        raise SystemExit("노드 %d/%d 생성 실패: %s" % (len(tm), len(nodes), json.dumps(res)[:500]))
    return tm


EXT = {}


def bulk_defaults(graph, defaults, tm):
    if not defaults:
        return
    m = dict(tm); m.update(EXT)
    for d in defaults:
        d["node_id"] = m.get(d["node_id"], d["node_id"])
    rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": graph, "defaults": defaults})
    fails = [x for x in (rd.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"defaults_" + graph: fails})


def bulk_conns(graph, conns, tm):
    m = dict(tm); m.update(EXT)
    for c in conns:
        c["source_node"] = m.get(c["source_node"], c["source_node"])
        c["target_node"] = m.get(c["target_node"], c["target_node"])
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": graph, "connections": conns})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns_" + graph: fails})
    LOG["steps"].append("%s links: %d req %d fail" % (graph, len(conns), len(fails)))


def ext_var(graph, node_type, var, parents, x, y):
    """외부 클래스 VariableGet/Set: 파손 스폰 -> T3D 수리 -> refresh -> 값핀 검증 (§9/§16)"""
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": graph, "node_type": node_type,
              "variable_name": var, "target_class": parents[0].split(".")[-1], "position": [x, y]})
    nid = node_id_of(r)
    if not nid:
        raise SystemExit("%s %s 스폰 실패" % (node_type, var))
    for parent in parents:
        t3d = '(MemberParent=%s,MemberName="%s",bSelfContext=False)' % (parent, var)
        call("blueprint_query", "set_node_property",
             {"asset_path": BP, "graph_name": graph, "node_id": nid,
              "property_name": "VariableReference", "value": t3d})
        call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": graph, "node_id": nid})
        if var in node_pins(graph, nid):
            LOG["steps"].append("%s %s (%s) OK" % (node_type, var, parent))
            return nid
    raise SystemExit("%s %s 값핀 미생성" % (node_type, var))


def array_fn(graph, fn_name, x, y):
    """§2 CallArrayFunction 3단 스폰 (FunctionReference 주입까지, 연결은 호출측)"""
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": graph, "node_type": "CallArrayFunction", "position": [x, y]})
    nid = node_id_of(r)
    call("blueprint_query", "set_node_property",
         {"asset_path": BP, "graph_name": graph, "node_id": nid,
          "property_name": "FunctionReference", "value": KAL_REF % fn_name})
    call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": graph, "node_id": nid})
    LOG["steps"].append("arrayfn %s = %s" % (fn_name, nid))
    return nid


# ═══ 0) BP 에셋 생성 ═══
try:
    call("blueprint_query", "list_graphs", {"asset_path": BP})
    raise SystemExit("BP_GroomWindCap 이미 존재 — 중복 실행 방지 중단.")
except RuntimeError:
    pass
r = call("blueprint_query", "create_blueprint",
         {"save_path": BP, "parent_class": "ActorComponent"})
LOG["steps"].append("create_blueprint: %s" % json.dumps(r)[:150])

# ═══ 1) 변수 ═══
VARS = [("CapEnabled", "bool", "true", True),
        ("GroomWindMax", "float", "10.0", True),
        ("GroomComps", "array:object:SBGroomComponent", None, False),
        ("BaseScales", "array:float", None, False),
        ("WdAccum", "struct:Vector", None, False),
        ("WdMaxPri", "int", None, False)]
for name, typ, dv, edit in VARS:
    p = {"asset_path": BP, "name": name, "type": typ, "category": "GroomWindCap", "instance_editable": edit}
    if dv:
        p["default_value"] = dv
    call("blueprint_query", "add_variable", p)
LOG["steps"].append("vars OK")

# ═══ 2) 함수 + 시그니처 + 컴파일 ═══
call("blueprint_query", "add_function", {"asset_path": BP, "name": FN})
call("blueprint_query", "set_function_params",
     {"asset_path": BP, "function_name": FN,
      "inputs": [{"name": "Point", "type": "struct:Vector"}],
      "outputs": [{"name": "Wind", "type": "struct:Vector"}]})
call("blueprint_query", "compile_blueprint", {"asset_path": BP})
gf = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
entry = result = None
for n in gf["nodes"]:
    if "FunctionEntry" in n.get("class", ""):
        entry = n["id"]
    if "FunctionResult" in n.get("class", ""):
        result = n["id"]
assert entry and result, "entry/result 미발견"
LOG["steps"].append("function OK")

# ═══ 3) 외부 프로퍼티 게터 (볼륨 3 + 파생컴포넌트 6) ═══
SB = "/Script/SB2."
EXT["priG"] = ext_var(FN, "VariableGet", "Priority", [SB + "SBWindVolume"], 900, -400)
EXT["dirG"] = ext_var(FN, "VariableGet", "WindDirection", [SB + "SBWindVolume"], 2600, -450)
EXT["strG"] = ext_var(FN, "VariableGet", "WindStrength", [SB + "SBWindVolume"], 2600, -320)
EXT["extD"] = ext_var(FN, "VariableGet", "BoxExtent", [SB + "SBDirectionalWindComponent"], 1100, 1500)
EXT["falD"] = ext_var(FN, "VariableGet", "FalloffExponent", [SB + "SBDirectionalWindComponent"], 2900, 1650)
EXT["strD"] = ext_var(FN, "VariableGet", "WindStrength", [SB + "SBDirectionalWindComponent"], 2900, 1780)
EXT["radR"] = ext_var(FN, "VariableGet", "Radius", [SB + "SBRadialWindComponent"], 1500, 2900)
EXT["falR"] = ext_var(FN, "VariableGet", "FalloffExponent", [SB + "SBRadialWindComponent"], 2900, 2950)
EXT["strR"] = ext_var(FN, "VariableGet", "WindStrength", [SB + "SBRadialWindComponent"], 2900, 3080)

# ═══ 4) 함수 그래프 본체 ═══
nodes, defaults, conns = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(nid, pin, val):
    defaults.append({"node_id": nid, "pin_name": pin, "value": val})


def F(tid, fn, x, y, cls=KML):
    N(tid, "CallFunction", x, y, function_name=fn, target_class=cls)


# init
N("setA0", "VariableSet", 300, 0, variable_name="WdAccum")
N("setP0", "VariableSet", 550, 0, variable_name="WdMaxPri")
D("setP0", "WdMaxPri", "-9999")
# Global 볼륨 루프
F("gaaV", "GetAllActorsOfClass", 800, 0, GS)
D("gaaV", "ActorClass", "/Script/SB2.SBWindVolume")
N("loopV", "ForEachLoop", 1100, 0)
C("gaaV", "OutActors", "loopV", "Array")
F("boundsV", "GetActorBounds", 1400, 100, "Actor")
C("loopV", "Array Element", "boundsV", "self")
D("boundsV", "bOnlyCollidingComponents", "false")
F("deltaV", "Subtract_VectorVector", 1400, 350)
C(entry, "Point", "deltaV", "A")
C("boundsV", "Origin", "deltaV", "B")
F("bkDV", "BreakVector", 1600, 350)
C("deltaV", "ReturnValue", "bkDV", "InVec")
F("bkEV", "BreakVector", 1600, 500)
C("boundsV", "BoxExtent", "bkEV", "InVec")
for ax in ("X", "Y", "Z"):
    F("absV" + ax, "Abs", 1800, 350 + 100 * "XYZ".index(ax))
    C("bkDV", ax, "absV" + ax, "A")
    F("leV" + ax, "LessEqual_DoubleDouble", 1950, 350 + 100 * "XYZ".index(ax))
    C("absV" + ax, "ReturnValue", "leV" + ax, "A")
    C("bkEV", ax, "leV" + ax, "B")
F("andV1", "BooleanAND", 2100, 380)
C("leVX", "ReturnValue", "andV1", "A")
C("leVY", "ReturnValue", "andV1", "B")
F("andV2", "BooleanAND", 2250, 420)
C("andV1", "ReturnValue", "andV2", "A")
C("leVZ", "ReturnValue", "andV2", "B")
N("brInV", "Branch", 1750, 100)
C("andV2", "ReturnValue", "brInV", "Condition")
N("getMax1", "VariableGet", 2000, -300, variable_name="WdMaxPri")
F("gtP", "Greater_IntInt", 2150, -350)
C("priG", "Priority", "gtP", "A")
C("getMax1", "WdMaxPri", "gtP", "B")
N("brGT", "Branch", 2100, 100)
C("gtP", "ReturnValue", "brGT", "Condition")
F("eqP", "EqualEqual_IntInt", 2150, -200)
C("priG", "Priority", "eqP", "A")
C("getMax1", "WdMaxPri", "eqP", "B")
N("brEQ", "Branch", 2500, 250)
C("eqP", "ReturnValue", "brEQ", "Condition")
F("mulGv", "Multiply_VectorFloat", 2850, -380)
C("dirG", "WindDirection", "mulGv", "A")
C("strG", "WindStrength", "mulGv", "B")
N("setMax", "VariableSet", 2500, 100, variable_name="WdMaxPri")
C("priG", "Priority", "setMax", "WdMaxPri")
N("setAccG", "VariableSet", 2750, 100, variable_name="WdAccum")
C("mulGv", "ReturnValue", "setAccG", "WdAccum")
N("getAccG", "VariableGet", 2650, 420, variable_name="WdAccum")
F("addGv", "Add_VectorVector", 2850, 400)
C("getAccG", "WdAccum", "addGv", "A")
C("mulGv", "ReturnValue", "addGv", "B")
N("setAccG2", "VariableSet", 3050, 250, variable_name="WdAccum")
C("addGv", "ReturnValue", "setAccG2", "WdAccum")
C("loopV", "Array Element", "priG", "self")
C("loopV", "Array Element", "dirG", "self")
C("loopV", "Array Element", "strG", "self")
# Directional 루프 (§20: GetComponentByClass 퓨어)
F("gaaD", "GetAllActorsOfClass", 400, 1200, GS)
D("gaaD", "ActorClass", "/Script/SB2.SBDirectionalWindActor")
N("loopD", "ForEachLoop", 700, 1200)
C("gaaD", "OutActors", "loopD", "Array")
F("gcD", "GetComponentByClass", 950, 1300, "Actor")
D("gcD", "ComponentClass", "/Script/SB2.SBDirectionalWindComponent")
C("loopD", "Array Element", "gcD", "self")
F("xformD", "K2_GetComponentToWorld", 1100, 1350, "SceneComponent")
C("gcD", "ReturnValue", "xformD", "self")
F("invD", "InverseTransformLocation", 1350, 1350)
C("xformD", "ReturnValue", "invD", "T")
C(entry, "Point", "invD", "Location")
C("gcD", "ReturnValue", "extD", "self")
F("bkLD", "BreakVector", 1550, 1350)
C("invD", "ReturnValue", "bkLD", "InVec")
F("bkED", "BreakVector", 1550, 1550)
C("extD", "BoxExtent", "bkED", "InVec")
for ax in ("X", "Y", "Z"):
    F("absD" + ax, "Abs", 1750, 1350 + 100 * "XYZ".index(ax))
    C("bkLD", ax, "absD" + ax, "A")
    F("leD" + ax, "LessEqual_DoubleDouble", 1900, 1350 + 100 * "XYZ".index(ax))
    C("absD" + ax, "ReturnValue", "leD" + ax, "A")
    C("bkED", ax, "leD" + ax, "B")
F("andD1", "BooleanAND", 2050, 1400)
C("leDX", "ReturnValue", "andD1", "A")
C("leDY", "ReturnValue", "andD1", "B")
F("andD2", "BooleanAND", 2200, 1450)
C("andD1", "ReturnValue", "andD2", "A")
C("leDZ", "ReturnValue", "andD2", "B")
N("brInD", "Branch", 1300, 1150)
C("andD2", "ReturnValue", "brInD", "Condition")
F("addT", "Add_DoubleDouble", 2400, 1400)
C("bkLD", "X", "addT", "A")
C("bkED", "X", "addT", "B")
F("mulE2", "Multiply_DoubleDouble", 2400, 1550)
C("bkED", "X", "mulE2", "A")
D("mulE2", "B", "2.0")
F("divT", "Divide_DoubleDouble", 2600, 1450)
C("addT", "ReturnValue", "divT", "A")
C("mulE2", "ReturnValue", "divT", "B")
F("oneT", "Subtract_DoubleDouble", 2750, 1450)
D("oneT", "A", "1.0")
C("divT", "ReturnValue", "oneT", "B")
F("powD", "MultiplyMultiply_FloatFloat", 3100, 1500)
C("oneT", "ReturnValue", "powD", "Base")
C("falD", "FalloffExponent", "powD", "Exp")
C("gcD", "ReturnValue", "falD", "self")
C("gcD", "ReturnValue", "strD", "self")
F("smulD", "Multiply_DoubleDouble", 3300, 1600)
C("strD", "WindStrength", "smulD", "A")
C("powD", "ReturnValue", "smulD", "B")
F("fwdD", "GetForwardVector", 3300, 1350, "SceneComponent")
C("gcD", "ReturnValue", "fwdD", "self")
F("wvD", "Multiply_VectorFloat", 3500, 1450)
C("fwdD", "ReturnValue", "wvD", "A")
C("smulD", "ReturnValue", "wvD", "B")
N("getAccD", "VariableGet", 3500, 1650, variable_name="WdAccum")
F("addDv", "Add_VectorVector", 3700, 1500)
C("getAccD", "WdAccum", "addDv", "A")
C("wvD", "ReturnValue", "addDv", "B")
N("setAccD", "VariableSet", 3900, 1150, variable_name="WdAccum")
C("addDv", "ReturnValue", "setAccD", "WdAccum")
# Radial 루프
F("gaaR", "GetAllActorsOfClass", 400, 2600, GS)
D("gaaR", "ActorClass", "/Script/SB2.SBRadialWindActor")
N("loopR", "ForEachLoop", 700, 2600)
C("gaaR", "OutActors", "loopR", "Array")
F("gcR", "GetComponentByClass", 950, 2700, "Actor")
D("gcR", "ComponentClass", "/Script/SB2.SBRadialWindComponent")
C("loopR", "Array Element", "gcR", "self")
F("locR", "K2_GetComponentLocation", 1100, 2750, "SceneComponent")
C("gcR", "ReturnValue", "locR", "self")
F("deltaR", "Subtract_VectorVector", 1300, 2750)
C(entry, "Point", "deltaR", "A")
C("locR", "ReturnValue", "deltaR", "B")
F("distR", "VSize", 1500, 2750)
C("deltaR", "ReturnValue", "distR", "A")
C("gcR", "ReturnValue", "radR", "self")
F("leR", "LessEqual_DoubleDouble", 1750, 2800)
C("distR", "ReturnValue", "leR", "A")
C("radR", "Radius", "leR", "B")
F("gt1R", "Greater_DoubleDouble", 1750, 2950)
C("distR", "ReturnValue", "gt1R", "A")
D("gt1R", "B", "1.0")
F("andR", "BooleanAND", 1950, 2850)
C("leR", "ReturnValue", "andR", "A")
C("gt1R", "ReturnValue", "andR", "B")
N("brInR", "Branch", 1300, 2550)
C("andR", "ReturnValue", "brInR", "Condition")
F("dirRv", "Divide_VectorFloat", 2200, 2750)
C("deltaR", "ReturnValue", "dirRv", "A")
C("distR", "ReturnValue", "dirRv", "B")
F("tR", "Divide_DoubleDouble", 2400, 2900)
C("distR", "ReturnValue", "tR", "A")
C("radR", "Radius", "tR", "B")
F("oneTR", "Subtract_DoubleDouble", 2600, 2900)
D("oneTR", "A", "1.0")
C("tR", "ReturnValue", "oneTR", "B")
F("powR", "MultiplyMultiply_FloatFloat", 3100, 2900)
C("oneTR", "ReturnValue", "powR", "Base")
C("falR", "FalloffExponent", "powR", "Exp")
C("gcR", "ReturnValue", "falR", "self")
C("gcR", "ReturnValue", "strR", "self")
F("smulR", "Multiply_DoubleDouble", 3300, 3000)
C("strR", "WindStrength", "smulR", "A")
C("powR", "ReturnValue", "smulR", "B")
F("wvR", "Multiply_VectorFloat", 3500, 2850)
C("dirRv", "ReturnValue", "wvR", "A")
C("smulR", "ReturnValue", "wvR", "B")
N("getAccR", "VariableGet", 3500, 3050, variable_name="WdAccum")
F("addRv", "Add_VectorVector", 3700, 2900)
C("getAccR", "WdAccum", "addRv", "A")
C("wvR", "ReturnValue", "addRv", "B")
N("setAccR", "VariableSet", 3900, 2550, variable_name="WdAccum")
C("addRv", "ReturnValue", "setAccR", "WdAccum")
# 결과
N("getFin", "VariableGet", 4200, 2650, variable_name="WdAccum")
C("getFin", "WdAccum", result, "Wind")

tm = bulk_nodes(FN, nodes)
bulk_defaults(FN, defaults, tm)
ex = []


def E(a, ap, b, bp="execute"):
    ex.append({"source_node": a, "source_pin": ap, "target_node": b, "target_pin": bp})


E(entry, "then", tm["setA0"])
E(tm["setA0"], "then", tm["setP0"])
E(tm["setP0"], "then", tm["gaaV"])
E(tm["gaaV"], "then", tm["loopV"], "Exec")
E(tm["loopV"], "LoopBody", tm["brInV"])
E(tm["brInV"], "then", tm["brGT"])
E(tm["brGT"], "then", tm["setMax"])
E(tm["setMax"], "then", tm["setAccG"])
E(tm["brGT"], "else", tm["brEQ"])
E(tm["brEQ"], "then", tm["setAccG2"])
E(tm["loopV"], "Completed", tm["gaaD"])
E(tm["gaaD"], "then", tm["loopD"], "Exec")
E(tm["loopD"], "LoopBody", tm["brInD"])
E(tm["brInD"], "then", tm["setAccD"])
E(tm["loopD"], "Completed", tm["gaaR"])
E(tm["gaaR"], "then", tm["loopR"], "Exec")
E(tm["loopR"], "LoopBody", tm["brInR"])
E(tm["brInR"], "then", tm["setAccR"])
E(tm["loopR"], "Completed", result)
bulk_conns(FN, conns + ex, tm)
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("fn compile: %s" % json.dumps(cr)[:200])

# ═══ 5) EventGraph: BeginPlay 캐시 + Tick 캡 ═══
EG = "EventGraph"
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
beginplay = tick = None
for n in g["nodes"]:
    t = (n.get("title") or "")
    if "K2Node_Event" in n.get("class", ""):
        if "BeginPlay" in t:
            beginplay = n["id"]
        if "Tick" in t:
            tick = n["id"]
if not beginplay:
    r = call("blueprint_query", "add_event_node", {"asset_path": BP, "event_name": "ReceiveBeginPlay", "position": [0, 0]})
    beginplay = node_id_of(r)
if not tick:
    r = call("blueprint_query", "add_event_node", {"asset_path": BP, "event_name": "ReceiveTick", "position": [0, 1200]})
    tick = node_id_of(r)
assert beginplay and tick, "이벤트 확보 실패"
LOG["steps"].append("events: begin=%s tick=%s" % (beginplay, tick))

# ext WindScale Get(캐시)/Set(적용) + 배열 노드
EXT["wsGet"] = ext_var(EG, "VariableGet", "WindScale", [SB + "SBGroomComponent"], 1500, 500)
EXT["wsSet"] = ext_var(EG, "VariableSet", "WindScale", [SB + "SBGroomComponent"], 2600, 1250)
EXT["arrClear"] = array_fn(EG, "Array_Clear", 700, 300)
EXT["arrAdd"] = array_fn(EG, "Array_Add", 1800, 350)
EXT["arrGet"] = array_fn(EG, "Array_Get", 2100, 1500)

nodes, defaults, conns = [], [], []
# BeginPlay: GetOwner -> GetComponentsByClass -> Set GroomComps -> Clear BaseScales -> loop add
F("own1", "GetOwner", 200, 300, "ActorComponent")
F("gcls", "GetComponentsByClass", 400, 250, "Actor")
C("own1", "ReturnValue", "gcls", "self")
D("gcls", "ComponentClass", "/Script/SB2.SBGroomComponent")
N("setComps", "VariableSet", 650, 150, variable_name="GroomComps")
C("gcls", "ReturnValue", "setComps", "GroomComps")
N("getBase1", "VariableGet", 700, 450, variable_name="BaseScales")
C("getBase1", "BaseScales", "arrClear", "TargetArray")
N("loopB", "ForEachLoop", 1100, 250)
C("setComps", "Output_Get", "loopB", "Array")
C("loopB", "Array Element", "wsGet", "self")
N("getBase2", "VariableGet", 1800, 500, variable_name="BaseScales")
C("getBase2", "BaseScales", "arrAdd", "TargetArray")
C("wsGet", "WindScale", "arrAdd", "NewItem")
# Tick: 게이트 -> 머리 위치 -> CalcWindAt -> factor -> loop set
N("brCap", "Branch", 300, 1200)
N("getCap", "VariableGet", 300, 1350, variable_name="CapEnabled")
C("getCap", "CapEnabled", "brCap", "Condition")
F("own2", "GetOwner", 500, 1400, "ActorComponent")
F("locO", "K2_GetActorLocation", 650, 1400, "Actor")
C("own2", "ReturnValue", "locO", "self")
F("headO", "Add_VectorVector", 800, 1400)
C("locO", "ReturnValue", "headO", "A")
D("headO", "B", "0,0,170")
N("callW", "CallFunction", 700, 1200, function_name=FN)
C("headO", "ReturnValue", "callW", "Point")
F("magW", "VSize", 1000, 1400)
C("callW", "Wind", "magW", "A")
N("getMaxW", "VariableGet", 1000, 1550, variable_name="GroomWindMax")
F("gtW", "Greater_DoubleDouble", 1200, 1450)
C("magW", "ReturnValue", "gtW", "A")
C("getMaxW", "GroomWindMax", "gtW", "B")
F("fmaxW", "FMax", 1200, 1600)
C("magW", "ReturnValue", "fmaxW", "A")
D("fmaxW", "B", "0.001")
F("divW", "Divide_DoubleDouble", 1400, 1550)
C("getMaxW", "GroomWindMax", "divW", "A")
C("fmaxW", "ReturnValue", "divW", "B")
F("selW", "SelectFloat", 1600, 1500)
C("divW", "ReturnValue", "selW", "A")
D("selW", "B", "1.0")
C("gtW", "ReturnValue", "selW", "bPickA")
N("loopT", "ForEachLoop", 1200, 1200)
N("getComps2", "VariableGet", 1200, 1350, variable_name="GroomComps")
C("getComps2", "GroomComps", "loopT", "Array")
N("getBase3", "VariableGet", 2100, 1650, variable_name="BaseScales")
C("getBase3", "BaseScales", "arrGet", "TargetArray")
C("loopT", "Array Index", "arrGet", "Index")
F("mulS", "Multiply_DoubleDouble", 2350, 1500)
C("arrGet", "Item", "mulS", "A")
C("selW", "ReturnValue", "mulS", "B")
C("mulS", "ReturnValue", "wsSet", "WindScale")
C("loopT", "Array Element", "wsSet", "self")

tm2 = bulk_nodes(EG, nodes)
bulk_defaults(EG, defaults, tm2)
# gcls 임퓨어 여부
gcls_pins = node_pins(EG, tm2["gcls"])
gcls_impure = "execute" in gcls_pins
LOG["steps"].append("gcls impure=%s" % gcls_impure)
ex = []
if gcls_impure:
    E(beginplay, "then", tm2["gcls"])
    E(tm2["gcls"], "then", tm2["setComps"])
else:
    E(beginplay, "then", tm2["setComps"])
E(tm2["setComps"], "then", "arrClear")
E("arrClear", "then", tm2["loopB"], "Exec")
E(tm2["loopB"], "LoopBody", "arrAdd")
E(tick, "then", tm2["brCap"])
E(tm2["brCap"], "then", tm2["callW"])
E(tm2["callW"], "then", tm2["loopT"], "Exec")
E(tm2["loopT"], "LoopBody", "wsSet")
bulk_conns(EG, conns + ex, tm2)

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("final compile: %s" % json.dumps(cr, ensure_ascii=False)[:600])
print(json.dumps(LOG, ensure_ascii=False, indent=1))
