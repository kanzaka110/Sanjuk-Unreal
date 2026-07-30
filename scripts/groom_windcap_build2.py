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



# (후속) 스테이지 5만 재실행 — 이벤트 타이틀 'Begin Play 이벤트' 공백 매칭 수정
SB = "/Script/SB2."

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
ex = []
def E(a, ap, b, bp="execute"):
    ex.append({"source_node": a, "source_pin": ap, "target_node": b, "target_pin": bp})
# ═══ 5) EventGraph: BeginPlay 캐시 + Tick 캡 ═══
EG = "EventGraph"
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
beginplay = tick = None
for n in g["nodes"]:
    t = (n.get("title") or "")
    if "K2Node_Event" in n.get("class", ""):
        if "Begin Play" in t or "BeginPlay" in t:
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
