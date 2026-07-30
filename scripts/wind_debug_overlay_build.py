# SBWind_Weight_TEST01_Map 레벨BP: 캐릭터 머리 위 바람 화살표+강도 오버레이 빌드 (방법 A) — v2
# 함수 CalcWindAt(Point)->Wind: Global(Priority/AABB) + Directional(box+falloff) + Radial(sphere+falloff) 벡터합
# Tick: ShowWindDebug 게이트 -> Character 전수 -> DrawDebugArrow + DrawDebugString
# 레시피: reference-monolith-bp-rpc-recipes-0723 (§2 CallArrayFunction, §3 클래스핀 default_object,
#         §9 외부 VariableGet/Set 파손->T3D+refresh, §13 Conv 타입드 체인, ForEachLoop 핀명 Exec)
# v2 수정 (0730 크래시 부검):
#  - ext 게터 id를 conns에 문자열로 참조하던 버그 -> EXT dict 병합
#  - Vector는 범용 BreakStruct 분해 불가 -> KML BreakVector 사용
#  - GetActorBounds는 퓨어(exec 없음) -> exec 체인에서 제외
#  - 빌드 중 BP 팔레트 열면 깨진 MemberReference 툴팁에서 에디터 크래시 (SBlueprintPalette)
import json, urllib.request, sys

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SBWind_Weight_TEST01_Map"
FN = "CalcWindAt"
KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"
KTL = "KismetTextLibrary"
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


def bulk_nodes(graph, nodes):
    res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": graph, "nodes": nodes})
    tm = {}
    harvest(res, tm)
    if len(tm) != len(nodes):
        raise SystemExit("노드 %d/%d 생성 실패: %s" % (len(tm), len(nodes), json.dumps(res)[:500]))
    return tm


def bulk_defaults(graph, defaults, tm):
    if not defaults:
        return
    for d in defaults:
        d["node_id"] = tm.get(d["node_id"], d["node_id"])
    rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": graph, "defaults": defaults})
    fails = [x for x in (rd.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"defaults_" + graph: fails})


EXT = {}  # ext 게터 temp명 -> 실제 노드 id


def bulk_conns(graph, conns, tm):
    m = dict(tm)
    m.update(EXT)
    for c in conns:
        c["source_node"] = m.get(c["source_node"], c["source_node"])
        c["target_node"] = m.get(c["target_node"], c["target_node"])
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": graph, "connections": conns})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns_" + graph: fails})
    LOG["steps"].append("%s links: %d req %d fail" % (graph, len(conns), len(fails)))


def ext_get(graph, var, parents, x, y):
    """외부 클래스 VariableGet: 파손 스폰 -> VariableReference T3D -> refresh -> 값핀 검증 (§9)"""
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": graph, "node_type": "VariableGet",
              "variable_name": var, "target_class": parents[0].split(".")[-1], "position": [x, y]})
    nid = r.get("node_id") or r.get("id")
    if not nid:
        tm = {}
        harvest(r, tm)
        nid = list(tm.values())[0] if tm else None
    if not nid:
        raise SystemExit("ext_get 스폰 실패 %s: %s" % (var, json.dumps(r)[:300]))
    for parent in parents:
        t3d = '(MemberParent=%s,MemberName="%s",bSelfContext=False)' % (parent, var)
        call("blueprint_query", "set_node_property",
             {"asset_path": BP, "graph_name": graph, "node_id": nid,
              "property_name": "VariableReference", "value": t3d})
        call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": graph, "node_id": nid})
        det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": graph, "node_id": nid})
        pins = [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]
        if var in pins:
            LOG["steps"].append("ext_get %s (%s) OK" % (var, parent))
            return nid
    raise SystemExit("ext_get %s 값핀 미생성 (시도: %s)" % (var, parents))


# ═══ 0) 프리플라이트 ═══
graphs = call("blueprint_query", "list_graphs", {"asset_path": BP})
gnames = [g["name"] for g in graphs["graphs"]]
if FN in gnames:
    raise SystemExit("함수 %s 이미 존재 — 중복 실행 방지 중단. 삭제 후 재실행하거나 수동 확인." % FN)
LOG["steps"].append("preflight: graphs=%s" % gnames)

# ═══ 1) 멤버 변수 ═══
VARS = [("ShowWindDebug", "bool", "true"), ("WdAccum", "struct:Vector", None), ("WdMaxPri", "int", None)]
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
for name, typ, dv in VARS:
    if name in existing:
        LOG["steps"].append("var exists: " + name)
        continue
    p = {"asset_path": BP, "name": name, "type": typ, "category": "WindDebug"}
    if dv:
        p["default_value"] = dv
    call("blueprint_query", "add_variable", p)
    LOG["steps"].append("var: " + name)

# ═══ 2) 함수 생성 + 시그니처 + 컴파일 (자기함수 호출 선행조건) ═══
call("blueprint_query", "add_function", {"asset_path": BP, "name": FN})
call("blueprint_query", "set_function_params",
     {"asset_path": BP, "function_name": FN,
      "inputs": [{"name": "Point", "type": "struct:Vector"}],
      "outputs": [{"name": "Wind", "type": "struct:Vector"}]})
call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("function + compile OK")

gf = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
entry = result = None
for n in gf["nodes"]:
    if "FunctionEntry" in n.get("class", ""):
        entry = n["id"]
    if "FunctionResult" in n.get("class", ""):
        result = n["id"]
assert entry and result, "entry/result 미발견: %s" % [(n["id"], n["class"]) for n in gf["nodes"]]

# ═══ 3) 외부 프로퍼티 게터 (개별 스폰+수리) ═══
SB = "/Script/SB2."
EXT["priG"] = ext_get(FN, "Priority", [SB + "SBWindVolume"], 900, -400)
EXT["dirG"] = ext_get(FN, "WindDirection", [SB + "SBWindVolume"], 2600, -450)
EXT["strG"] = ext_get(FN, "WindStrength", [SB + "SBWindVolume"], 2600, -320)
EXT["compD"] = ext_get(FN, "WindComponent", [SB + "SBWindActor", SB + "SBDirectionalWindActor"], 700, 1300)
EXT["extD"] = ext_get(FN, "BoxExtent", [SB + "SBDirectionalWindComponent"], 1100, 1500)
EXT["falD"] = ext_get(FN, "FalloffExponent", [SB + "SBDirectionalWindComponent"], 2900, 1650)
EXT["strD"] = ext_get(FN, "WindStrength", [SB + "SBDirectionalWindComponent"], 2900, 1780)
EXT["compR"] = ext_get(FN, "WindComponent", [SB + "SBWindActor", SB + "SBRadialWindActor"], 700, 2700)
EXT["radR"] = ext_get(FN, "Radius", [SB + "SBRadialWindComponent"], 1500, 2900)
EXT["falR"] = ext_get(FN, "FalloffExponent", [SB + "SBRadialWindComponent"], 2900, 2950)
EXT["strR"] = ext_get(FN, "WindStrength", [SB + "SBRadialWindComponent"], 2900, 3080)

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


# -- init --
N("setA0", "VariableSet", 300, 0, variable_name="WdAccum")
N("setP0", "VariableSet", 550, 0, variable_name="WdMaxPri")
D("setP0", "WdMaxPri", "-9999")

# -- Global 볼륨 루프 --
F("gaaV", "GetAllActorsOfClass", 800, 0, GS)
D("gaaV", "ActorClass", "/Script/SB2.SBWindVolume")
N("loopV", "ForEachLoop", 1100, 0)
C("gaaV", "OutActors", "loopV", "Array")
F("boundsV", "GetActorBounds", 1400, 100, "Actor")
C("loopV", "Array Element", "boundsV", "self")
D("boundsV", "bOnlyCollidingComponents", "false")
F("deltaV", "Subtract_VectorVector", 1400, 350)
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
# priority 비교
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
# 기여 = dir * strength
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
# 볼륨 게터 타깃 = 루프 element
C("loopV", "Array Element", "priG", "self")
C("loopV", "Array Element", "dirG", "self")
C("loopV", "Array Element", "strG", "self")

# -- Directional 루프 --
F("gaaD", "GetAllActorsOfClass", 400, 1200, GS)
D("gaaD", "ActorClass", "/Script/SB2.SBDirectionalWindActor")
N("loopD", "ForEachLoop", 700, 1200)
C("gaaD", "OutActors", "loopD", "Array")
C("loopD", "Array Element", "compD", "self")
F("xformD", "K2_GetComponentToWorld", 1100, 1350, "SceneComponent")
C("compD", "WindComponent", "xformD", "self")
F("invD", "InverseTransformLocation", 1350, 1350)
C("xformD", "ReturnValue", "invD", "T")
C(entry, "Point", "invD", "Location")
C("compD", "WindComponent", "extD", "self")
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
# t = (lx+ex)/(2ex), mult = (1-t)^falloff
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
C("compD", "WindComponent", "falD", "self")
C("compD", "WindComponent", "strD", "self")
F("smulD", "Multiply_DoubleDouble", 3300, 1600)
C("strD", "WindStrength", "smulD", "A")
C("powD", "ReturnValue", "smulD", "B")
F("fwdD", "GetForwardVector", 3300, 1350, "SceneComponent")
C("compD", "WindComponent", "fwdD", "self")
F("wvD", "Multiply_VectorFloat", 3500, 1450)
C("fwdD", "ReturnValue", "wvD", "A")
C("smulD", "ReturnValue", "wvD", "B")
N("getAccD", "VariableGet", 3500, 1650, variable_name="WdAccum")
F("addDv", "Add_VectorVector", 3700, 1500)
C("getAccD", "WdAccum", "addDv", "A")
C("wvD", "ReturnValue", "addDv", "B")
N("setAccD", "VariableSet", 3900, 1150, variable_name="WdAccum")
C("addDv", "ReturnValue", "setAccD", "WdAccum")

# -- Radial 루프 --
F("gaaR", "GetAllActorsOfClass", 400, 2600, GS)
D("gaaR", "ActorClass", "/Script/SB2.SBRadialWindActor")
N("loopR", "ForEachLoop", 700, 2600)
C("gaaR", "OutActors", "loopR", "Array")
C("loopR", "Array Element", "compR", "self")
F("locR", "K2_GetComponentLocation", 1100, 2750, "SceneComponent")
C("compR", "WindComponent", "locR", "self")
F("deltaR", "Subtract_VectorVector", 1300, 2750)
C(entry, "Point", "deltaR", "A")
C("locR", "ReturnValue", "deltaR", "B")
F("distR", "VSize", 1500, 2750)
C("deltaR", "ReturnValue", "distR", "A")
C("compR", "WindComponent", "radR", "self")
F("leR", "LessEqual_DoubleDouble", 1750, 2800)
C("distR", "ReturnValue", "leR", "A")
C("radR", "Radius", "leR", "B")
F("gt1R", "Greater_DoubleDouble", 1750, 2950)
C("distR", "ReturnValue", "gt1R", "A")
D("gt1R", "B", "1.0")
F("andR", "BooleanAND", 1950, 2850)
C("leR", "ReturnValue", "andR", "A")
C("gt1R", "ReturnValue", "andR", "B")
N("brInR", "Branch", 1300, 2550, node_type_hint="Branch")
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
C("compR", "WindComponent", "falR", "self")
C("compR", "WindComponent", "strR", "self")
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

# -- 결과 --
N("getFin", "VariableGet", 4200, 2650, variable_name="WdAccum")
C("getFin", "WdAccum", result, "Wind")

# node_type_hint 키 제거 (실수 방지)
for nd in nodes:
    nd.pop("node_type_hint", None)

tm = bulk_nodes(FN, nodes)
bulk_defaults(FN, defaults, tm)

# exec 체인
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

# ═══ 5) 컴파일 (함수 등록) ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile after fn body: %s" % json.dumps(cr)[:200])

# ═══ 6) EventGraph: Tick 체인 ═══
EG = "EventGraph"
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
tick = None
for n in g["nodes"]:
    if "K2Node_Event" in n.get("class", "") and "Tick" in (n.get("title") or "") + n.get("id", ""):
        tick = n["id"]
if not tick:
    for evname in ("ReceiveTick", "Tick"):
        try:
            r = call("blueprint_query", "add_event_node", {"asset_path": BP, "event_name": evname, "position": [3000, 2800]})
            tick = r.get("node_id") or r.get("id")
            if tick:
                break
        except RuntimeError as e:
            LOG["errors"].append({"add_event_node_" + evname: str(e)[:200]})
assert tick, "Tick 이벤트 확보 실패"
LOG["steps"].append("tick node: %s" % tick)

nodes, defaults, conns = [], [], []
N("brShow", "Branch", 3300, 2800)
N("getShow", "VariableGet", 3300, 2950, variable_name="ShowWindDebug")
C("getShow", "ShowWindDebug", "brShow", "Condition")
F("gaaC", "GetAllActorsOfClass", 3550, 2800, GS)
D("gaaC", "ActorClass", "/Script/Engine.Character")
N("loopC", "ForEachLoop", 3850, 2800)
C("gaaC", "OutActors", "loopC", "Array")
F("locC", "K2_GetActorLocation", 4100, 3000, "Actor")
C("loopC", "Array Element", "locC", "self")
F("headC", "Add_VectorVector", 4300, 3000)
C("locC", "ReturnValue", "headC", "A")
D("headC", "B", "0,0,190")
N("callW", "CallFunction", 4300, 2800, function_name=FN)
C("headC", "ReturnValue", "callW", "Point")
F("lenW", "VSize", 4600, 3100)
C("callW", "Wind", "lenW", "A")
F("mulAr", "Multiply_VectorFloat", 4600, 2980)
C("callW", "Wind", "mulAr", "A")
D("mulAr", "B", "10.0")
F("endC", "Add_VectorVector", 4800, 2980)
C("headC", "ReturnValue", "endC", "A")
C("mulAr", "ReturnValue", "endC", "B")
F("arrow", "DrawDebugArrow", 5000, 2800, KSL)
C("headC", "ReturnValue", "arrow", "LineStart")
C("endC", "ReturnValue", "arrow", "LineEnd")
D("arrow", "ArrowSize", "150.0")
D("arrow", "LineColor", "(R=0.000000,G=1.000000,B=1.000000,A=1.000000)")
D("arrow", "Duration", "0.0")
D("arrow", "Thickness", "3.0")
F("txtLoc", "Add_VectorVector", 4800, 3250)
C("headC", "ReturnValue", "txtLoc", "A")
D("txtLoc", "B", "0,0,-35")
F("convT", "Conv_DoubleToText", 4800, 3400, KTL)
C("lenW", "ReturnValue", "convT", "Value")
D("convT", "MaximumFractionalDigits", "1")
F("t2s", "Conv_TextToString", 5000, 3400, KTL)
C("convT", "ReturnValue", "t2s", "InText")
F("dstr", "DrawDebugString", 5300, 2800, KSL)
C("txtLoc", "ReturnValue", "dstr", "TextLocation")
C("t2s", "ReturnValue", "dstr", "Text")
D("dstr", "TextColor", "(R=1.000000,G=1.000000,B=0.000000,A=1.000000)")
D("dstr", "Duration", "0.0")

tm2 = bulk_nodes(EG, nodes)
bulk_defaults(EG, defaults, tm2)
ex = []
E(tick, "then", tm2["brShow"])
E(tm2["brShow"], "then", tm2["gaaC"])
E(tm2["gaaC"], "then", tm2["loopC"], "Exec")
E(tm2["loopC"], "LoopBody", tm2["callW"])
E(tm2["callW"], "then", tm2["arrow"])
E(tm2["arrow"], "then", tm2["dstr"])
bulk_conns(EG, conns + ex, tm2)

# ═══ 7) 최종 컴파일 ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("final compile: %s" % json.dumps(cr)[:300])

print(json.dumps(LOG, ensure_ascii=False, indent=1))
