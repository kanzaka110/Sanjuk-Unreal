# PC_01_BP GroomVelCap v3: 스파이크 가드 — 순간 가속(착지/월런 시작/회피/이동 틱) 전용 억제
#   승호 피드백: 낙하 중 과경직(30 과함) + 순간 이벤트에서 과한 틔는 잔존
#   처방: ①AirborneBendBoost 30->5 ②가속도 |dV|/dt > 임계 -> SpikeTimer(0.3s) 발동
#        스파이크 중: BendStiffness=SpikeBendBoost(60) + 속도주입 x SpikeVelFactor(0.1)
#   VelCap 그래프 = 감지+타이머+주입킬 / AirHold 그래프 = 벤드 우선순위(스파이크>공중>베이스)
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FV = "ApplyGroomVelCap"
FA = "ApplyGroomAirborneHold"
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


def add(graph, ntype, x, y, **kw):
    p = {"asset_path": BP, "graph_name": graph, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return node_id_of(call("blueprint_query", "add_node", p))


def pindef(graph, nid, pin, val):
    call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": graph, "node_id": nid, "pin_name": pin, "value": val})


def connect(graph, cs):
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": graph, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"graph": graph, "conns": fails})
    return len(fails)


def disconnect(graph, sn, sp, tn, tp):
    call("blueprint_query", "disconnect_pins",
         {"asset_path": BP, "graph_name": graph, "source_node": sn, "source_pin": sp,
          "target_node": tn, "target_pin": tp})


def graph_nodes(graph):
    g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": graph})
    return {n["id"]: n for n in g["nodes"]}


def pinmap(n):
    return {p["name"]: p for p in n.get("pins", [])}


# ═══ 1) 변수 ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
for nm, ty, dv, ed in [
    ("VelCapPrevVel", "vector", "0,0,0", False),
    ("SpikeTimer", "float", "0.0", False),
    ("SpikeAccelThreshold", "float", "8000.0", True),
    ("SpikeHoldTime", "float", "0.3", True),
    ("SpikeVelFactor", "float", "0.1", True),
    ("SpikeBendBoost", "float", "60.0", True),
]:
    if nm in existing:
        continue
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": nm, "type": ty, "default_value": dv,
          "category": "Hair|Groom Vel Cap", "instance_editable": ed})
# 낙하 홀드 완화 30 -> 5
call("blueprint_query", "set_variable_defaults", {"asset_path": BP, "name": "AirborneBendBoost", "default_value": "5.0"})
LOG["steps"].append("vars ok + AirborneBendBoost=5")

# ═══ 2) VelCap 그래프 노드 탐색 ═══
nodes = graph_nodes(FV)
getVel = setPrevY = setSS = mkSet = getDt = mulLin = mulAng = None
for nid, n in nodes.items():
    pm = pinmap(n)
    if n.get("function") == "GetVelocity":
        getVel = nid
    if n.get("function") == "GetWorldDeltaSeconds":
        getDt = nid
    if "VariableSet" in n["class"] and "VelCapPrevYaw" in pm:
        setPrevY = nid
    if "VariableSet" in n["class"] and "SimulationSettings" in pm:
        setSS = nid
    if "MakeStruct" in n["class"] and "LinearVelocityScale" in pm:
        mkSet = nid
        mulLin = pm["LinearVelocityScale"]["connected_to"][0].split(".")[0]
        mulAng = pm["AngularVelocityScale"]["connected_to"][0].split(".")[0]
assert all([getVel, setPrevY, setSS, mkSet, getDt, mulLin, mulAng]), \
    "탐색 실패 %s" % [getVel, setPrevY, setSS, mkSet, getDt, mulLin, mulAng]
LOG["steps"].append("found getVel=%s setPrevY=%s setSS=%s mkSet=%s mulLin=%s mulAng=%s" % (getVel, setPrevY, setSS, mkSet, mulLin, mulAng))

# ═══ 3) 스파이크 감지 + 타이머 (VelCap) ═══
getPrevV = add(FV, "VariableGet", 2000, 2900, variable_name="VelCapPrevVel")
subVec = add(FV, "CallFunction", 2250, 2900, function_name="Subtract_VectorVector", target_class=KML)
vsizeD = add(FV, "CallFunction", 2450, 2900, function_name="VSize", target_class=KML)
fmaxDt2 = add(FV, "CallFunction", 2450, 3050, function_name="FMax", target_class=KML)
pindef(FV, fmaxDt2, "B", "0.001")
divAcc = add(FV, "CallFunction", 2650, 2950, function_name="Divide_DoubleDouble", target_class=KML)
getThr = add(FV, "VariableGet", 2650, 3150, variable_name="SpikeAccelThreshold")
gtAcc = add(FV, "CallFunction", 2850, 3000, function_name="Greater_DoubleDouble", target_class=KML)

getST1 = add(FV, "VariableGet", 2900, 2700, variable_name="SpikeTimer")
subT = add(FV, "CallFunction", 3100, 2700, function_name="Subtract_DoubleDouble", target_class=KML)
fmax0 = add(FV, "CallFunction", 3300, 2700, function_name="FMax", target_class=KML)
pindef(FV, fmax0, "B", "0.0")
setDecay = add(FV, "VariableSet", 2900, 200, variable_name="SpikeTimer")
brAcc = add(FV, "Branch", 3200, 200)
getHold = add(FV, "VariableGet", 3400, 400, variable_name="SpikeHoldTime")
setHold = add(FV, "VariableSet", 3550, 100, variable_name="SpikeTimer")
setPrevV = add(FV, "VariableSet", 3850, 200, variable_name="VelCapPrevVel")

disconnect(FV, setPrevY, "then", setSS, "execute")
f = connect(FV, [
    # pures
    {"source_node": getVel, "source_pin": "ReturnValue", "target_node": subVec, "target_pin": "A"},
    {"source_node": getPrevV, "source_pin": "VelCapPrevVel", "target_node": subVec, "target_pin": "B"},
    {"source_node": subVec, "source_pin": "ReturnValue", "target_node": vsizeD, "target_pin": "A"},
    {"source_node": getDt, "source_pin": "ReturnValue", "target_node": fmaxDt2, "target_pin": "A"},
    {"source_node": vsizeD, "source_pin": "ReturnValue", "target_node": divAcc, "target_pin": "A"},
    {"source_node": fmaxDt2, "source_pin": "ReturnValue", "target_node": divAcc, "target_pin": "B"},
    {"source_node": divAcc, "source_pin": "ReturnValue", "target_node": gtAcc, "target_pin": "A"},
    {"source_node": getThr, "source_pin": "SpikeAccelThreshold", "target_node": gtAcc, "target_pin": "B"},
    {"source_node": getST1, "source_pin": "SpikeTimer", "target_node": subT, "target_pin": "A"},
    {"source_node": getDt, "source_pin": "ReturnValue", "target_node": subT, "target_pin": "B"},
    {"source_node": subT, "source_pin": "ReturnValue", "target_node": fmax0, "target_pin": "A"},
    {"source_node": fmax0, "source_pin": "ReturnValue", "target_node": setDecay, "target_pin": "SpikeTimer"},
    {"source_node": getHold, "source_pin": "SpikeHoldTime", "target_node": setHold, "target_pin": "SpikeTimer"},
    {"source_node": gtAcc, "source_pin": "ReturnValue", "target_node": brAcc, "target_pin": "Condition"},
    {"source_node": getVel, "source_pin": "ReturnValue", "target_node": setPrevV, "target_pin": "VelCapPrevVel"},
    # exec: setPrevY -> setDecay -> brAcc -> (then: setHold ->) setPrevV -> setSS
    {"source_node": setPrevY, "source_pin": "then", "target_node": setDecay, "target_pin": "execute"},
    {"source_node": setDecay, "source_pin": "then", "target_node": brAcc, "target_pin": "execute"},
    {"source_node": brAcc, "source_pin": "then", "target_node": setHold, "target_pin": "execute"},
    {"source_node": setHold, "source_pin": "then", "target_node": setPrevV, "target_pin": "execute"},
    {"source_node": brAcc, "source_pin": "else", "target_node": setPrevV, "target_pin": "execute"},
    {"source_node": setPrevV, "source_pin": "then", "target_node": setSS, "target_pin": "execute"},
])
LOG["steps"].append("spike detect links fail=%d" % f)

# ═══ 4) 주입 킬 (VelCap): mul -> x Select(스파이크? factor : 1) -> mkSet ═══
getST2 = add(FV, "VariableGet", 4300, 1600, variable_name="SpikeTimer")
gtSp = add(FV, "CallFunction", 4500, 1600, function_name="Greater_DoubleDouble", target_class=KML)
pindef(FV, gtSp, "B", "0.0")
getKillF = add(FV, "VariableGet", 4500, 1750, variable_name="SpikeVelFactor")
sel = add(FV, "CallFunction", 4700, 1650, function_name="SelectFloat", target_class=KML)
pindef(FV, sel, "B", "1.0")
killL = add(FV, "CallFunction", 4870, 1350, function_name="Multiply_DoubleDouble", target_class=KML)
killA = add(FV, "CallFunction", 4870, 1500, function_name="Multiply_DoubleDouble", target_class=KML)

disconnect(FV, mulLin, "ReturnValue", mkSet, "LinearVelocityScale")
disconnect(FV, mulAng, "ReturnValue", mkSet, "AngularVelocityScale")
f = connect(FV, [
    {"source_node": getST2, "source_pin": "SpikeTimer", "target_node": gtSp, "target_pin": "A"},
    {"source_node": getKillF, "source_pin": "SpikeVelFactor", "target_node": sel, "target_pin": "A"},
    {"source_node": gtSp, "source_pin": "ReturnValue", "target_node": sel, "target_pin": "bPickA"},
    {"source_node": mulLin, "source_pin": "ReturnValue", "target_node": killL, "target_pin": "A"},
    {"source_node": sel, "source_pin": "ReturnValue", "target_node": killL, "target_pin": "B"},
    {"source_node": mulAng, "source_pin": "ReturnValue", "target_node": killA, "target_pin": "A"},
    {"source_node": sel, "source_pin": "ReturnValue", "target_node": killA, "target_pin": "B"},
    {"source_node": killL, "source_pin": "ReturnValue", "target_node": mkSet, "target_pin": "LinearVelocityScale"},
    {"source_node": killA, "source_pin": "ReturnValue", "target_node": mkSet, "target_pin": "AngularVelocityScale"},
])
LOG["steps"].append("injection kill links fail=%d" % f)

# ═══ 5) AirHold 벤드 우선순위: 스파이크 > 공중 > 베이스 ═══
# 기존: brFall(then->setManual->setBoost / else->setRelease->setManualOff)
an = graph_nodes(FA)
brFall = setManual = setBoost = setRelease = getBoost = None
for nid, n in an.items():
    pm = pinmap(n)
    if n["class"] == "K2Node_IfThenElse" and (pm.get("Condition", {}).get("connected_to") or [""])[0].startswith("K2Node_CallFunction"):
        brFall = nid
    if "VariableSet" in n["class"] and "bUseManualBendScales" in pm and pm["bUseManualBendScales"].get("default_value") == "true":
        setManual = nid
    if "VariableSet" in n["class"] and "BendStiffnessScale" in pm:
        src = (pm["BendStiffnessScale"].get("connected_to") or [""])[0]
        if "VariableGet" in src:
            setBoost = nid
            getBoost = src.split(".")[0]
        elif "CallFunction" in src:
            setRelease = nid
assert all([brFall, setManual, setBoost, setRelease, getBoost]), \
    "AirHold 탐색 실패 %s" % [brFall, setManual, setBoost, setRelease, getBoost]
LOG["steps"].append("airhold found brFall=%s setManual=%s setBoost=%s setRelease=%s getBoost=%s" % (brFall, setManual, setBoost, setRelease, getBoost))

getSTH = add(FA, "VariableGet", 600, 1500, variable_name="SpikeTimer")
gtSpH = add(FA, "CallFunction", 800, 1500, function_name="Greater_DoubleDouble", target_class=KML)
pindef(FA, gtSpH, "B", "0.0")
getSpB = add(FA, "VariableGet", 1000, 1600, variable_name="SpikeBendBoost")
selB = add(FA, "CallFunction", 1200, 1550, function_name="SelectFloat", target_class=KML)
brSpike = add(FA, "Branch", 1000, 700)

disconnect(FA, getBoost, "AirborneBendBoost", setBoost, "BendStiffnessScale")
disconnect(FA, brFall, "else", setRelease, "execute")
f = connect(FA, [
    {"source_node": getSTH, "source_pin": "SpikeTimer", "target_node": gtSpH, "target_pin": "A"},
    {"source_node": getSpB, "source_pin": "SpikeBendBoost", "target_node": selB, "target_pin": "A"},
    {"source_node": getBoost, "source_pin": "AirborneBendBoost", "target_node": selB, "target_pin": "B"},
    {"source_node": gtSpH, "source_pin": "ReturnValue", "target_node": selB, "target_pin": "bPickA"},
    {"source_node": selB, "source_pin": "ReturnValue", "target_node": setBoost, "target_pin": "BendStiffnessScale"},
    # 지상: 스파이크면 setManual(공중 노드 재사용, exec 팬인) / 아니면 이징 복귀
    {"source_node": brFall, "source_pin": "else", "target_node": brSpike, "target_pin": "execute"},
    {"source_node": gtSpH, "source_pin": "ReturnValue", "target_node": brSpike, "target_pin": "Condition"},
    {"source_node": brSpike, "source_pin": "then", "target_node": setManual, "target_pin": "execute"},
    {"source_node": brSpike, "source_pin": "else", "target_node": setRelease, "target_pin": "execute"},
])
LOG["steps"].append("airhold priority links fail=%d" % f)

# ═══ 6) 컴파일 ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:250])
