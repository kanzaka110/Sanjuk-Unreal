# PC_01_BP ApplyGroomVelCap v1: 헤어 틔는 현상 캡 — 윈드캡 v4 하이브리드 소프트니 미러
#   대상 = SimulationSettings.SimulationSetup.LinearVelocityScale / AngularVelocityScale (UE5.7 BlueprintReadWrite, 매 틱 소비)
#   factor = FMin(1, (Knee + (Max-Knee)*FClamp((V-Knee)/FMax(Sys-Knee,0.001),0,1)) / FMax(V,0.001))
#   V(선형) = VSize(GetVelocity), V(각) = |NormalizeAxis(Yaw-PrevYaw)| / dt
#   base 캐시-온-퍼스트런(0.75/0.75) -> Scale = base * factor
#   틱 스플라이스: ApplyGroomWindCap.then(빈 테일) -> ApplyGroomVelCap
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "ApplyGroomVelCap"
KML = "KismetMathLibrary"
GROOM = "/Script/HairStrandsCore.GroomComponent"
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


def add(ntype, x, y, graph=FN, **kw):
    p = {"asset_path": BP, "graph_name": graph, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return node_id_of(call("blueprint_query", "add_node", p))


def pins_of(nid, graph=FN):
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": graph, "node_id": nid})
    return det.get("pins") or det.get("node", {}).get("pins") or []


def pindef(nid, pin, val, graph=FN):
    call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": graph, "node_id": nid, "pin_name": pin, "value": val})


def connect(cs, graph=FN):
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": graph, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


def ext_var(node_type, var, parent, x, y):
    nid = add(node_type, x, y, variable_name=var, target_class=parent.split(".")[-1])
    call("blueprint_query", "set_node_property",
         {"asset_path": BP, "graph_name": FN, "node_id": nid,
          "property_name": "VariableReference",
          "value": '(MemberParent=%s,MemberName="%s",bSelfContext=False)' % (parent, var)})
    call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": FN, "node_id": nid})
    names = [p.get("name") for p in pins_of(nid)]
    if var not in names:
        raise SystemExit("%s %s 값핀 미생성: %s" % (node_type, var, names))
    return nid


def struct_pin(nid, direction):
    """Break(입력)/Make(출력)의 구조체 핀 이름을 동적으로 찾는다"""
    for p in pins_of(nid):
        if p.get("direction") == direction and not p.get("is_exec") and "struct" in (p.get("type") or ""):
            return p["name"]
    raise SystemExit("struct pin 미발견 %s %s" % (nid, direction))


# ═══ 0) 프리플라이트 ═══
gnames = [g["name"] for g in call("blueprint_query", "list_graphs", {"asset_path": BP})["graphs"]]
if FN in gnames:
    raise SystemExit("%s 이미 존재 — 중복 실행 방지 중단" % FN)

# ═══ 1) 변수 ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
CAT = "Hair|Groom Vel Cap"
VARS = [  # (name, type, default, editable)
    ("VelCapEnabled", "bool", "true", True),
    ("LinVelKnee", "float", "300.0", True),
    ("LinVelSysMax", "float", "1500.0", True),
    ("LinVelMax", "float", "700.0", True),
    ("AngVelKnee", "float", "180.0", True),
    ("AngVelSysMax", "float", "1080.0", True),
    ("AngVelMax", "float", "450.0", True),
    ("BaseLinVelScale", "float", "0.0", False),
    ("BaseAngVelScale", "float", "0.0", False),
    ("VelCapBaseCached", "bool", "false", False),
    ("VelCapPrevYaw", "float", "0.0", False),
    ("VelCapAngVel", "float", "0.0", False),
]
for nm, ty, dv, ed in VARS:
    if nm in existing:
        continue
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": nm, "type": ty, "default_value": dv,
          "category": CAT, "instance_editable": ed})
LOG["steps"].append("vars ok")

# ═══ 2) 함수 생성 ═══
call("blueprint_query", "add_function", {"asset_path": BP, "name": FN})
gf = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
entry = None
for n in gf["nodes"]:
    if "FunctionEntry" in n.get("class", ""):
        entry = n["id"]
assert entry, "entry 미발견"
LOG["steps"].append("function created, entry=%s" % entry)

# ═══ 3) 게이트 + 캐시 체인 ═══
getEn = add("VariableGet", 200, 400, variable_name="VelCapEnabled")
brEn = add("Branch", 400, 200)
getCached = add("VariableGet", 500, 450, variable_name="VelCapBaseCached")
brCached = add("Branch", 700, 200)

getHairC = add("VariableGet", 300, 700, variable_name="Hair")
getSSC = ext_var("VariableGet", "SimulationSettings", GROOM, 500, 700)
brkSSC = add("BreakStruct", 750, 700, struct_type="HairSimulationSettings")
brkSetC = add("BreakStruct", 1000, 700, struct_type="HairSimulationSetup")
inSSC = struct_pin(brkSSC, "input")
inSetC = struct_pin(brkSetC, "input")
setBaseL = add("VariableSet", 1300, 200, variable_name="BaseLinVelScale")
setBaseA = add("VariableSet", 1550, 200, variable_name="BaseLinVelScale".replace("Lin", "Ang"))
setCachedT = add("VariableSet", 1800, 200, variable_name="VelCapBaseCached")
pindef(setCachedT, "VelCapBaseCached", "true")

f = connect([
    {"source_node": entry, "source_pin": "then", "target_node": brEn, "target_pin": "execute"},
    {"source_node": getEn, "source_pin": "VelCapEnabled", "target_node": brEn, "target_pin": "Condition"},
    {"source_node": brEn, "source_pin": "then", "target_node": brCached, "target_pin": "execute"},
    {"source_node": getCached, "source_pin": "VelCapBaseCached", "target_node": brCached, "target_pin": "Condition"},
    {"source_node": brCached, "source_pin": "else", "target_node": setBaseL, "target_pin": "execute"},
    {"source_node": setBaseL, "source_pin": "then", "target_node": setBaseA, "target_pin": "execute"},
    {"source_node": setBaseA, "source_pin": "then", "target_node": setCachedT, "target_pin": "execute"},
    {"source_node": getHairC, "source_pin": "Hair", "target_node": getSSC, "target_pin": "self"},
    {"source_node": getSSC, "source_pin": "SimulationSettings", "target_node": brkSSC, "target_pin": inSSC},
    {"source_node": brkSSC, "source_pin": "SimulationSetup", "target_node": brkSetC, "target_pin": inSetC},
    {"source_node": brkSetC, "source_pin": "LinearVelocityScale", "target_node": setBaseL, "target_pin": "BaseLinVelScale"},
    {"source_node": brkSetC, "source_pin": "AngularVelocityScale", "target_node": setBaseA, "target_pin": "BaseAngVelScale"},
])
LOG["steps"].append("gate+cache links fail=%d" % f)

# ═══ 4) 측정 체인 (선형속도 + 각속도) ═══
getVel = add("CallFunction", 900, 1100, function_name="GetVelocity", target_class="Actor")
vLin = add("CallFunction", 1150, 1100, function_name="VSize", target_class=KML)
getRot = add("CallFunction", 900, 1300, function_name="K2_GetActorRotation", target_class="Actor")
brkRot = add("CallFunction", 1150, 1300, function_name="BreakRotator", target_class=KML)
getPrevY = add("VariableGet", 1150, 1500, variable_name="VelCapPrevYaw")
subYaw = add("CallFunction", 1400, 1350, function_name="Subtract_DoubleDouble", target_class=KML)
normYaw = add("CallFunction", 1600, 1350, function_name="NormalizeAxis", target_class=KML)
absYaw = add("CallFunction", 1800, 1350, function_name="Abs", target_class=KML)
getDt = add("CallFunction", 1600, 1550, function_name="GetWorldDeltaSeconds", target_class="GameplayStatics")
fmaxDt = add("CallFunction", 1800, 1550, function_name="FMax", target_class=KML)
pindef(fmaxDt, "B", "0.001")
divAng = add("CallFunction", 2000, 1400, function_name="Divide_DoubleDouble", target_class=KML)
setAngV = add("VariableSet", 2300, 200, variable_name="VelCapAngVel")
setPrevY = add("VariableSet", 2600, 200, variable_name="VelCapPrevYaw")

f = connect([
    {"source_node": getVel, "source_pin": "ReturnValue", "target_node": vLin, "target_pin": "A"},
    {"source_node": getRot, "source_pin": "ReturnValue", "target_node": brkRot, "target_pin": "InRot"},
    {"source_node": brkRot, "source_pin": "Yaw", "target_node": subYaw, "target_pin": "A"},
    {"source_node": getPrevY, "source_pin": "VelCapPrevYaw", "target_node": subYaw, "target_pin": "B"},
    {"source_node": subYaw, "source_pin": "ReturnValue", "target_node": normYaw, "target_pin": "Angle"},
    {"source_node": normYaw, "source_pin": "ReturnValue", "target_node": absYaw, "target_pin": "A"},
    {"source_node": getDt, "source_pin": "ReturnValue", "target_node": fmaxDt, "target_pin": "A"},
    {"source_node": absYaw, "source_pin": "ReturnValue", "target_node": divAng, "target_pin": "A"},
    {"source_node": fmaxDt, "source_pin": "ReturnValue", "target_node": divAng, "target_pin": "B"},
    {"source_node": divAng, "source_pin": "ReturnValue", "target_node": setAngV, "target_pin": "VelCapAngVel"},
    {"source_node": brkRot, "source_pin": "Yaw", "target_node": setPrevY, "target_pin": "VelCapPrevYaw"},
    # exec: 캐시 양갈래 -> setAngV -> setPrevY
    {"source_node": brCached, "source_pin": "then", "target_node": setAngV, "target_pin": "execute"},
    {"source_node": setCachedT, "source_pin": "then", "target_node": setAngV, "target_pin": "execute"},
    {"source_node": setAngV, "source_pin": "then", "target_node": setPrevY, "target_pin": "execute"},
])
LOG["steps"].append("measure links fail=%d" % f)


# ═══ 5) 소프트니 팩터 체인 x2 ═══
def softknee(vsrc_node, vsrc_pin, knee_var, sys_var, max_var, y0):
    getK = add("VariableGet", 2500, y0, variable_name=knee_var)
    getS = add("VariableGet", 2500, y0 + 150, variable_name=sys_var)
    getM = add("VariableGet", 2500, y0 + 300, variable_name=max_var)
    subVK = add("CallFunction", 2700, y0, function_name="Subtract_DoubleDouble", target_class=KML)
    subSK = add("CallFunction", 2700, y0 + 150, function_name="Subtract_DoubleDouble", target_class=KML)
    fmaxSK = add("CallFunction", 2870, y0 + 150, function_name="FMax", target_class=KML)
    pindef(fmaxSK, "B", "0.001")
    tDiv = add("CallFunction", 3040, y0, function_name="Divide_DoubleDouble", target_class=KML)
    tClamp = add("CallFunction", 3200, y0, function_name="FClamp", target_class=KML)
    pindef(tClamp, "Min", "0.0")
    pindef(tClamp, "Max", "1.0")
    subMK = add("CallFunction", 3040, y0 + 250, function_name="Subtract_DoubleDouble", target_class=KML)
    mulT = add("CallFunction", 3360, y0 + 100, function_name="Multiply_DoubleDouble", target_class=KML)
    addR = add("CallFunction", 3520, y0 + 50, function_name="Add_DoubleDouble", target_class=KML)
    fmaxV = add("CallFunction", 3520, y0 + 220, function_name="FMax", target_class=KML)
    pindef(fmaxV, "B", "0.001")
    fDiv = add("CallFunction", 3680, y0 + 100, function_name="Divide_DoubleDouble", target_class=KML)
    fMin = add("CallFunction", 3840, y0 + 100, function_name="FMin", target_class=KML)
    pindef(fMin, "B", "1.0")
    ff = connect([
        {"source_node": vsrc_node, "source_pin": vsrc_pin, "target_node": subVK, "target_pin": "A"},
        {"source_node": getK, "source_pin": knee_var, "target_node": subVK, "target_pin": "B"},
        {"source_node": getS, "source_pin": sys_var, "target_node": subSK, "target_pin": "A"},
        {"source_node": getK, "source_pin": knee_var, "target_node": subSK, "target_pin": "B"},
        {"source_node": subSK, "source_pin": "ReturnValue", "target_node": fmaxSK, "target_pin": "A"},
        {"source_node": subVK, "source_pin": "ReturnValue", "target_node": tDiv, "target_pin": "A"},
        {"source_node": fmaxSK, "source_pin": "ReturnValue", "target_node": tDiv, "target_pin": "B"},
        {"source_node": tDiv, "source_pin": "ReturnValue", "target_node": tClamp, "target_pin": "Value"},
        {"source_node": getM, "source_pin": max_var, "target_node": subMK, "target_pin": "A"},
        {"source_node": getK, "source_pin": knee_var, "target_node": subMK, "target_pin": "B"},
        {"source_node": subMK, "source_pin": "ReturnValue", "target_node": mulT, "target_pin": "A"},
        {"source_node": tClamp, "source_pin": "ReturnValue", "target_node": mulT, "target_pin": "B"},
        {"source_node": getK, "source_pin": knee_var, "target_node": addR, "target_pin": "A"},
        {"source_node": mulT, "source_pin": "ReturnValue", "target_node": addR, "target_pin": "B"},
        {"source_node": vsrc_node, "source_pin": vsrc_pin, "target_node": fmaxV, "target_pin": "A"},
        {"source_node": addR, "source_pin": "ReturnValue", "target_node": fDiv, "target_pin": "A"},
        {"source_node": fmaxV, "source_pin": "ReturnValue", "target_node": fDiv, "target_pin": "B"},
        {"source_node": fDiv, "source_pin": "ReturnValue", "target_node": fMin, "target_pin": "A"},
    ])
    return fMin, ff


getAngV = add("VariableGet", 2300, 2600, variable_name="VelCapAngVel")
fMinLin, f1 = softknee(vLin, "ReturnValue", "LinVelKnee", "LinVelSysMax", "LinVelMax", 1900)
fMinAng, f2 = softknee(getAngV, "VelCapAngVel", "AngVelKnee", "AngVelSysMax", "AngVelMax", 2700)
LOG["steps"].append("softknee links fail=%d,%d" % (f1, f2))

# ═══ 6) 라이트백: Break -> Make(전 필드 와이어스루) -> Set ═══
getHairW = add("VariableGet", 4000, 700, variable_name="Hair")
getSSW = ext_var("VariableGet", "SimulationSettings", GROOM, 4200, 700)
brkSSW = add("BreakStruct", 4450, 700, struct_type="HairSimulationSettings")
brkSetW = add("BreakStruct", 4700, 700, struct_type="HairSimulationSetup")
mkSet = add("MakeStruct", 5000, 700, struct_type="HairSimulationSetup")
mkSS = add("MakeStruct", 5300, 700, struct_type="HairSimulationSettings")
getBaseL = add("VariableGet", 4700, 1300, variable_name="BaseLinVelScale")
getBaseA = add("VariableGet", 4700, 1450, variable_name="BaseAngVelScale")
mulLin = add("CallFunction", 4950, 1300, function_name="Multiply_DoubleDouble", target_class=KML)
mulAng = add("CallFunction", 4950, 1450, function_name="Multiply_DoubleDouble", target_class=KML)
setSS = ext_var("VariableSet", "SimulationSettings", GROOM, 5650, 300)

inSSW = struct_pin(brkSSW, "input")
inSetW = struct_pin(brkSetW, "input")
outSet = struct_pin(mkSet, "output")
outSS = struct_pin(mkSS, "output")

cs = [
    {"source_node": getHairW, "source_pin": "Hair", "target_node": getSSW, "target_pin": "self"},
    {"source_node": getSSW, "source_pin": "SimulationSettings", "target_node": brkSSW, "target_pin": inSSW},
    {"source_node": brkSSW, "source_pin": "SimulationSetup", "target_node": brkSetW, "target_pin": inSetW},
    {"source_node": getBaseL, "source_pin": "BaseLinVelScale", "target_node": mulLin, "target_pin": "A"},
    {"source_node": fMinLin, "source_pin": "ReturnValue", "target_node": mulLin, "target_pin": "B"},
    {"source_node": getBaseA, "source_pin": "BaseAngVelScale", "target_node": mulAng, "target_pin": "A"},
    {"source_node": fMinAng, "source_pin": "ReturnValue", "target_node": mulAng, "target_pin": "B"},
    {"source_node": mulLin, "source_pin": "ReturnValue", "target_node": mkSet, "target_pin": "LinearVelocityScale"},
    {"source_node": mulAng, "source_pin": "ReturnValue", "target_node": mkSet, "target_pin": "AngularVelocityScale"},
    {"source_node": mkSet, "source_pin": outSet, "target_node": mkSS, "target_pin": "SimulationSetup"},
    {"source_node": mkSS, "source_pin": outSS, "target_node": setSS, "target_pin": "SimulationSettings"},
    {"source_node": getHairW, "source_pin": "Hair", "target_node": setSS, "target_pin": "self"},
    {"source_node": setPrevY, "source_pin": "then", "target_node": setSS, "target_pin": "execute"},
]
# mkSet 나머지 입력 <- brkSetW 동명 출력 (전 필드 와이어스루, SB2 커스텀 필드 포함)
mkSetIns = [p["name"] for p in pins_of(mkSet) if p.get("direction") == "input" and not p.get("is_exec")]
for nm in mkSetIns:
    if nm in ("LinearVelocityScale", "AngularVelocityScale"):
        continue
    cs.append({"source_node": brkSetW, "source_pin": nm, "target_node": mkSet, "target_pin": nm})
mkSSIns = [p["name"] for p in pins_of(mkSS) if p.get("direction") == "input" and not p.get("is_exec")]
for nm in mkSSIns:
    if nm == "SimulationSetup":
        continue
    cs.append({"source_node": brkSSW, "source_pin": nm, "target_node": mkSS, "target_pin": nm})
LOG["steps"].append("mkSet ins=%s / mkSS ins=%s" % (mkSetIns, mkSSIns))
f = connect(cs)
LOG["steps"].append("writeback links fail=%d" % f)

# ═══ 7) 컴파일 -> EventGraph 스플라이스 (셀프호출은 컴파일 선행 필수) ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile1: %s" % json.dumps(cr, ensure_ascii=False)[:300])

velCall = add("CallFunction", 800, 1232, graph="EventGraph", function_name=FN)
call("blueprint_query", "set_node_property",
     {"asset_path": BP, "graph_name": "EventGraph", "node_id": velCall,
      "property_name": "FunctionReference",
      "value": '(MemberParent=None,MemberGuid=00000000000000000000000000000000,MemberName="%s",bSelfContext=True)' % FN})
call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": "EventGraph", "node_id": velCall})
f = connect([{"source_node": "K2Node_CallFunction_59", "source_pin": "then", "target_node": velCall, "target_pin": "execute"}], graph="EventGraph")
LOG["steps"].append("tick splice fail=%d velCall=%s" % (f, velCall))

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile2: %s" % json.dumps(cr, ensure_ascii=False)[:300])

# ═══ 8) 미연결 입력 감사 ═══
g2 = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
for n in g2["nodes"]:
    for p in n.get("pins", []):
        if p.get("direction") != "input" or p.get("connected_to") or p.get("is_exec"):
            continue
        nm = p.get("name")
        if nm in ("Condition", "InRot", "Angle", "Value") or (nm in ("A", "B") and not p.get("default_value")):
            LOG["errors"].append({"unconnected": [n["id"], (n.get("title") or "")[:40], nm]})
