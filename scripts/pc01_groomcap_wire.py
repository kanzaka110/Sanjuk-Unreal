# PC_01_BP 그룸 윈드캡 배선: ApplyGroomWindCap 함수 신설(캐시-온-퍼스트런 + 캡 적용) + Tick 헤드 스플라이스
# 전제: CalcWindAt 함수/변수 7종은 승호가 이전 완료. 함정 반영: §9 ext Get/Set, §2 CallArrayFunction,
#       §23 셀프 함수 오바인딩+MemberParent=None, §15 SelectFloat/bPickA, §24 atexit 로그+미연결 감사
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "ApplyGroomWindCap"
KML = "KismetMathLibrary"
KAL_REF = "(MemberParent=\"/Script/CoreUObject.Class'/Script/Engine.KismetArrayLibrary'\",MemberName=\"%s\")"
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


def node_id_of(r):
    nid = r.get("node_id") or r.get("id")
    if nid:
        return nid
    def hv(o):
        if isinstance(o, dict):
            if o.get("node_id") or o.get("id"):
                return o.get("node_id") or o.get("id")
            for v in o.values():
                x = hv(v)
                if x:
                    return x
        elif isinstance(o, list):
            for e in o:
                x = hv(e)
                if x:
                    return x
    return hv(r)


def node_pins(graph, nid):
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": graph, "node_id": nid})
    return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]


def ext_var(graph, node_type, var, parents, x, y):
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": graph, "node_type": node_type,
              "variable_name": var, "target_class": parents[0].split(".")[-1], "position": [x, y]})
    nid = node_id_of(r)
    for parent in parents:
        call("blueprint_query", "set_node_property",
             {"asset_path": BP, "graph_name": graph, "node_id": nid,
              "property_name": "VariableReference",
              "value": '(MemberParent=%s,MemberName="%s",bSelfContext=False)' % (parent, var)})
        call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": graph, "node_id": nid})
        if var in node_pins(graph, nid):
            LOG["steps"].append("%s %s OK" % (node_type, var))
            return nid
    raise SystemExit("%s %s 값핀 미생성" % (node_type, var))


def array_fn(graph, fn_name, x, y):
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": graph, "node_type": "CallArrayFunction", "position": [x, y]})
    nid = node_id_of(r)
    call("blueprint_query", "set_node_property",
         {"asset_path": BP, "graph_name": graph, "node_id": nid,
          "property_name": "FunctionReference", "value": KAL_REF % fn_name})
    call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": graph, "node_id": nid})
    return nid


def self_call(graph, fn_name, x, y):
    """§23: 셀프 함수 호출 — MemberParent=None 명시 필수"""
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": graph, "node_type": "CallFunction",
              "function_name": fn_name, "position": [x, y]})
    nid = node_id_of(r)
    call("blueprint_query", "set_node_property",
         {"asset_path": BP, "graph_name": graph, "node_id": nid,
          "property_name": "FunctionReference",
          "value": '(MemberParent=None,MemberGuid=00000000000000000000000000000000,MemberName="%s",bSelfContext=True)' % fn_name})
    call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": graph, "node_id": nid})
    return nid


# ═══ 0) 프리플라이트 ═══
gnames = [g["name"] for g in call("blueprint_query", "list_graphs", {"asset_path": BP})["graphs"]]
if FN in gnames:
    raise SystemExit("%s 이미 존재 — 중복 실행 방지 중단" % FN)
assert "CalcWindAt" in gnames, "CalcWindAt 없음"

# ═══ 1) 함수 생성 ═══
call("blueprint_query", "add_function", {"asset_path": BP, "name": FN})
gf = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
entry = None
for n in gf["nodes"]:
    if "FunctionEntry" in n.get("class", ""):
        entry = n["id"]
assert entry, "entry 미발견"
LOG["steps"].append("function created, entry=%s" % entry)

# ═══ 2) 개별 스폰 (ext/array/self-call) ═══
SB = "/Script/SB2."
EXT = {}
EXT["wsGet"] = ext_var(FN, "VariableGet", "WindScale", [SB + "SBGroomComponent"], 1550, 700)
EXT["wsSet"] = ext_var(FN, "VariableSet", "WindScale", [SB + "SBGroomComponent"], 3400, 1250)
EXT["gaGet"] = ext_var(FN, "VariableGet", "GroomAsset", ["/Script/HairStrandsCore.GroomComponent", SB + "SBGroomComponent"], 2200, 1550)
EXT["arrLen"] = array_fn(FN, "Array_Length", 350, 350)
EXT["arrClear"] = array_fn(FN, "Array_Clear", 1100, 400)
EXT["arrAdd"] = array_fn(FN, "Array_Add", 1850, 500)
EXT["arrGet"] = array_fn(FN, "Array_Get", 2800, 1450)
EXT["callW"] = self_call(FN, "CalcWindAt", 2300, 100)
assert "Point" in node_pins(FN, EXT["callW"]), "callW Point 핀 미생성"
LOG["steps"].append("individual spawns OK")

# ═══ 3) 본체 벌크 ═══
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


# 게이트 + 캐시 분기
N("brCap", "Branch", 250, 100)
N("getCap", "VariableGet", 250, 250, variable_name="CapEnabled")
C("getCap", "CapEnabled", "brCap", "Condition")
N("getCompsL", "VariableGet", 350, 500, variable_name="GroomComps")
C("getCompsL", "GroomComps", "arrLen", "TargetArray")
F("gtLen", "Greater_IntInt", 550, 350)
C("arrLen", "ReturnValue", "gtLen", "A")
D("gtLen", "B", "0")
N("brCached", "Branch", 700, 100)
C("gtLen", "ReturnValue", "brCached", "Condition")
# 캐시 체인 (self 액터 컨텍스트 — GetOwner 불필요)
F("gcls", "GetComponentsByClass", 850, 350, "Actor")
D("gcls", "ComponentClass", "/Script/SB2.SBGroomComponent")
N("setComps", "VariableSet", 950, 100, variable_name="GroomComps")
C("gcls", "ReturnValue", "setComps", "GroomComps")
N("getBaseC", "VariableGet", 1100, 550, variable_name="BaseScales")
C("getBaseC", "BaseScales", "arrClear", "TargetArray")
N("loopB", "ForEachLoop", 1400, 100)
C("setComps", "Output_Get", "loopB", "Array")
C("loopB", "Array Element", "wsGet", "self")
N("getBaseA", "VariableGet", 1850, 650, variable_name="BaseScales")
C("getBaseA", "BaseScales", "arrAdd", "TargetArray")
C("wsGet", "WindScale", "arrAdd", "NewItem")
# 캡 계산
F("locO", "K2_GetActorLocation", 1900, 250, "Actor")
F("headO", "Add_VectorVector", 2100, 250)
C("locO", "ReturnValue", "headO", "A")
D("headO", "B", "0,0,170")
C("headO", "ReturnValue", "callW", "Point")
F("magW", "VSize", 2550, 300)
C("callW", "Wind", "magW", "A")
N("getMaxW", "VariableGet", 2550, 450, variable_name="GroomWindMax")
F("gtW", "Greater_DoubleDouble", 2750, 350)
C("magW", "ReturnValue", "gtW", "A")
C("getMaxW", "GroomWindMax", "gtW", "B")
F("fmaxW", "FMax", 2750, 500)
C("magW", "ReturnValue", "fmaxW", "A")
D("fmaxW", "B", "0.001")
F("divW", "Divide_DoubleDouble", 2950, 450)
C("getMaxW", "GroomWindMax", "divW", "A")
C("fmaxW", "ReturnValue", "divW", "B")
F("selW", "SelectFloat", 3150, 400)
C("divW", "ReturnValue", "selW", "A")
D("selW", "B", "1.0")
C("gtW", "ReturnValue", "selW", "bPickA")
# 적용 루프 + 필터
N("loopT", "ForEachLoop", 2600, 100)
N("getComps2", "VariableGet", 2600, 220, variable_name="GroomComps")
C("getComps2", "GroomComps", "loopT", "Array")
C("loopT", "Array Element", "gaGet", "self")
C("loopT", "Array Element", "wsSet", "self")
F("objName", "GetObjectName", 2400, 1550, "KismetSystemLibrary")
C("gaGet", "GroomAsset", "objName", "Object")
N("getFilter", "VariableGet", 2400, 1700, variable_name="GroomAssetFilter")
F("eqName", "EqualEqual_StrStr", 2600, 1580, "KismetStringLibrary")
C("objName", "ReturnValue", "eqName", "A")
C("getFilter", "GroomAssetFilter", "eqName", "B")
F("eqEmpty", "EqualEqual_StrStr", 2600, 1730, "KismetStringLibrary")
C("getFilter", "GroomAssetFilter", "eqEmpty", "A")
D("eqEmpty", "B", "")
F("orB", "BooleanOR", 2800, 1650)
C("eqName", "ReturnValue", "orB", "A")
C("eqEmpty", "ReturnValue", "orB", "B")
N("brMatch", "Branch", 3050, 1150)
C("orB", "ReturnValue", "brMatch", "Condition")
N("getBaseG", "VariableGet", 2800, 1550, variable_name="BaseScales")
C("getBaseG", "BaseScales", "arrGet", "TargetArray")
C("loopT", "Array Index", "arrGet", "Index")
F("mulS", "Multiply_DoubleDouble", 3150, 1350)
C("arrGet", "Item", "mulS", "A")
C("selW", "ReturnValue", "mulS", "B")
C("mulS", "ReturnValue", "wsSet", "WindScale")

res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": FN, "nodes": nodes})
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
if len(tm) != len(nodes):
    raise SystemExit("노드 %d/%d 생성 실패" % (len(tm), len(nodes)))
m = dict(tm)
m.update(EXT)
for d in defaults:
    d["node_id"] = m.get(d["node_id"], d["node_id"])
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": FN, "defaults": defaults})
dfail = [x for x in (rd.get("results") or []) if not x.get("success", True)]
if dfail:
    LOG["errors"].append({"defaults": dfail})

# gcls 퓨어/임퓨어 판정
gcls_impure = "execute" in node_pins(FN, tm["gcls"])
LOG["steps"].append("gcls impure=%s" % gcls_impure)

ex = []
def E(a, ap, b, bp="execute"):
    ex.append({"source_node": a, "source_pin": ap, "target_node": b, "target_pin": bp})

E(entry, "then", "brCap")
E("brCap", "then", "brCached")
E("brCached", "then", "callW")            # 캐시돼 있으면 바로 캡
if gcls_impure:
    E("brCached", "else", "gcls")
    E("gcls", "then", "setComps")
else:
    E("brCached", "else", "setComps")
E("setComps", "then", "arrClear")
E("arrClear", "then", "loopB", "Exec")
E("loopB", "LoopBody", "arrAdd")
E("loopB", "Completed", "callW")
E("callW", "then", "loopT", "Exec")
E("loopT", "LoopBody", "brMatch")
E("brMatch", "then", "wsSet")

for c in conns + ex:
    c["source_node"] = m.get(c["source_node"], c["source_node"])
    c["target_node"] = m.get(c["target_node"], c["target_node"])
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": conns + ex})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"conns": fails})
LOG["steps"].append("fn links: %d req %d fail" % (len(conns) + len(ex), len(fails)))

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("fn compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])
if not cr.get("success"):
    raise SystemExit("함수 컴파일 실패 — 스플라이스 중단")

# ═══ 4) Tick 헤드 스플라이스 ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": "EventGraph"})
tick = None
first = None
for n in g["nodes"]:
    if "K2Node_Event" in n.get("class", "") and "Tick" in (n.get("title") or ""):
        tick = n["id"]
        for p in n.get("pins", []):
            if p.get("name") == "then":
                ct = p.get("connected_to") or []
                first = ct[0] if ct else None
assert tick, "Tick 이벤트 미발견"
LOG["steps"].append("tick=%s first=%s" % (tick, first))

callApply = self_call("EventGraph", FN, 0, 0)
if first:
    fn_node, fn_pin = first.split(".")
    call("blueprint_query", "disconnect_pins",
         {"asset_path": BP, "graph_name": "EventGraph",
          "source_node": tick, "source_pin": "then", "target_node": fn_node, "target_pin": fn_pin})
    sp = [{"source_node": tick, "source_pin": "then", "target_node": callApply, "target_pin": "execute"},
          {"source_node": callApply, "source_pin": "then", "target_node": fn_node, "target_pin": fn_pin}]
else:
    sp = [{"source_node": tick, "source_pin": "then", "target_node": callApply, "target_pin": "execute"}]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": "EventGraph", "connections": sp})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"splice": fails})
LOG["steps"].append("splice done (%d links, %d fail)" % (len(sp), len(fails)))

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("final compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])

# ═══ 5) 미연결 감사 ═══
for G in (FN, "EventGraph"):
    g2 = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": G})
    for n in g2["nodes"]:
        for p in n.get("pins", []):
            if p.get("direction") != "input" or p.get("connected_to"):
                continue
            nm = p.get("name")
            if nm in ("Condition", "Object", "Point", "Array", "TargetArray", "Index", "Item", "InVec", "NewItem") or (nm == "self" and "VariableGet" in n.get("class", "")):
                LOG["errors"].append({"unconnected": [G, n["id"], (n.get("title") or "")[:40], nm]})
