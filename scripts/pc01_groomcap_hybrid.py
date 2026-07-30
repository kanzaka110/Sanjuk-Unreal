# PC_01_BP ApplyGroomWindCap v4: 비율 상시감쇠 -> 하이브리드 소프트니
#   factor = FMin(1, (Knee + (Max_i-Knee)*FClamp((W-Knee)/FMax(Sys-Knee,0.001),0,1)) / FMax(W,0.001))
#   W<=Knee: 원본 100% / Knee~Sys: 선형 압축 / Sys 초과: Max 고정
# - CapKneeWind 변수 신설 (기본 6)
# - CalcWindAt 호출 복원 (locO/headO/callW/magW) + exec 재삽입
# - 구 비율 노드(divR/fmaxS) 제거
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "ApplyGroomWindCap"
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


def add(ntype, x, y, **kw):
    p = {"asset_path": BP, "graph_name": FN, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return node_id_of(call("blueprint_query", "add_node", p))


def pindef(nid, pin, val):
    call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": FN, "node_id": nid, "pin_name": pin, "value": val})


def connect(cs):
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


# ═══ 1) 변수 ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
if "CapKneeWind" not in existing:
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": "CapKneeWind", "type": "float", "default_value": "6.0",
          "category": "Hair|Groom Wind Cap", "instance_editable": True})
    LOG["steps"].append("var CapKneeWind (6)")

# ═══ 2) 탐색 ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
nodes = {n["id"]: n for n in g["nodes"]}
def P(n): return {p["name"]: p for p in n.get("pins", [])}
getSys = getMM = loopT = mulS = divR = None
for nid, n in nodes.items():
    pn = P(n)
    cls = n.get("class", "")
    if "VariableGet" in cls and "WindSystemMax" in pn:
        getSys = nid
    if "VariableGet" in cls and "WcMatchedMax" in pn:
        getMM = nid
    if "MacroInstance" in cls and pn.get("Array Element", {}).get("type") == "object:SBGroomComponent":
        loopT = nid
# divR = getMM 소비처(pin A), mulS = divR 소비처
mmGetters = [nid for nid, n in nodes.items() if "VariableGet" in n.get("class", "") and "WcMatchedMax" in P(n)]
for mg in mmGetters:
    for c in (P(nodes[mg]).get("WcMatchedMax", {}).get("connected_to") or []):
        cn, cp = c.split(".")
        if cp == "A":
            divR = cn
            getMM = mg
assert divR, "divR 미발견"
for c in (P(nodes[divR]).get("ReturnValue", {}).get("connected_to") or []):
    mulS = c.split(".")[0]
fmaxS = (P(nodes[divR]).get("B", {}).get("connected_to") or [""])[0].split(".")[0] or None
assert all([getSys, getMM, loopT, mulS, fmaxS]), "탐색 실패: %s %s %s %s %s" % (getSys, getMM, loopT, mulS, fmaxS)
# loopT.Exec 소스 2개 (brCached.then / loopB.Completed)
exec_srcs = P(nodes[loopT]).get("Exec", {}).get("connected_to") or []
LOG["steps"].append("found: getSys=%s getMM=%s loopT=%s mulS=%s divR=%s fmaxS=%s loopT.Exec<-%s"
                    % (getSys, getMM, loopT, mulS, divR, fmaxS, exec_srcs))
assert len(exec_srcs) >= 1, "loopT exec 소스 없음"

# ═══ 3) 측정 체인 복원 ═══
locO = add("CallFunction", 1900, 250, function_name="K2_GetActorLocation", target_class="Actor")
headO = add("CallFunction", 2100, 250, function_name="Add_VectorVector", target_class=KML)
pindef(headO, "B", "0,0,170")
callW = add("CallFunction", 2300, 100, function_name="CalcWindAt")
call("blueprint_query", "set_node_property",
     {"asset_path": BP, "graph_name": FN, "node_id": callW,
      "property_name": "FunctionReference",
      "value": '(MemberParent=None,MemberGuid=00000000000000000000000000000000,MemberName="CalcWindAt",bSelfContext=True)'})
call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": FN, "node_id": callW})
magW = add("CallFunction", 2550, 300, function_name="VSize", target_class=KML)
LOG["steps"].append("measure chain restored: callW=%s" % callW)

# exec: 소스들 -> callW -> loopT
for s in exec_srcs:
    sn, sp = s.split(".")
    call("blueprint_query", "disconnect_pins",
         {"asset_path": BP, "graph_name": FN, "source_node": sn, "source_pin": sp,
          "target_node": loopT, "target_pin": "Exec"})
cs = [{"source_node": s.split(".")[0], "source_pin": s.split(".")[1], "target_node": callW, "target_pin": "execute"} for s in exec_srcs]
cs += [{"source_node": callW, "source_pin": "then", "target_node": loopT, "target_pin": "Exec"},
       {"source_node": locO, "source_pin": "ReturnValue", "target_node": headO, "target_pin": "A"},
       {"source_node": headO, "source_pin": "ReturnValue", "target_node": callW, "target_pin": "Point"},
       {"source_node": callW, "source_pin": "Wind", "target_node": magW, "target_pin": "A"}]
f1 = connect(cs)
LOG["steps"].append("exec+measure links fail=%d" % f1)

# ═══ 4) 소프트니 팩터 체인 ═══
getKnee = add("VariableGet", 2500, 1900, variable_name="CapKneeWind")
subWK = add("CallFunction", 2700, 1850, function_name="Subtract_DoubleDouble", target_class=KML)   # W-Knee
subSK = add("CallFunction", 2700, 2000, function_name="Subtract_DoubleDouble", target_class=KML)   # Sys-Knee
fmaxSK = add("CallFunction", 2870, 2000, function_name="FMax", target_class=KML)
pindef(fmaxSK, "B", "0.001")
tDiv = add("CallFunction", 3040, 1900, function_name="Divide_DoubleDouble", target_class=KML)
tClamp = add("CallFunction", 3200, 1900, function_name="FClamp", target_class=KML)
pindef(tClamp, "Min", "0.0")
pindef(tClamp, "Max", "1.0")
subMK = add("CallFunction", 3040, 2100, function_name="Subtract_DoubleDouble", target_class=KML)   # Max_i-Knee
mulT = add("CallFunction", 3360, 2000, function_name="Multiply_DoubleDouble", target_class=KML)
addR = add("CallFunction", 3520, 1950, function_name="Add_DoubleDouble", target_class=KML)         # received
fmaxW2 = add("CallFunction", 3520, 2120, function_name="FMax", target_class=KML)
pindef(fmaxW2, "B", "0.001")
fDiv = add("CallFunction", 3680, 2000, function_name="Divide_DoubleDouble", target_class=KML)
fMin = add("CallFunction", 3840, 2000, function_name="FMin", target_class=KML)
pindef(fMin, "B", "1.0")
f2 = connect([
    {"source_node": magW, "source_pin": "ReturnValue", "target_node": subWK, "target_pin": "A"},
    {"source_node": getKnee, "source_pin": "CapKneeWind", "target_node": subWK, "target_pin": "B"},
    {"source_node": getSys, "source_pin": "WindSystemMax", "target_node": subSK, "target_pin": "A"},
    {"source_node": getKnee, "source_pin": "CapKneeWind", "target_node": subSK, "target_pin": "B"},
    {"source_node": subSK, "source_pin": "ReturnValue", "target_node": fmaxSK, "target_pin": "A"},
    {"source_node": subWK, "source_pin": "ReturnValue", "target_node": tDiv, "target_pin": "A"},
    {"source_node": fmaxSK, "source_pin": "ReturnValue", "target_node": tDiv, "target_pin": "B"},
    {"source_node": tDiv, "source_pin": "ReturnValue", "target_node": tClamp, "target_pin": "Value"},
    {"source_node": getMM, "source_pin": "WcMatchedMax", "target_node": subMK, "target_pin": "A"},
    {"source_node": getKnee, "source_pin": "CapKneeWind", "target_node": subMK, "target_pin": "B"},
    {"source_node": subMK, "source_pin": "ReturnValue", "target_node": mulT, "target_pin": "A"},
    {"source_node": tClamp, "source_pin": "ReturnValue", "target_node": mulT, "target_pin": "B"},
    {"source_node": getKnee, "source_pin": "CapKneeWind", "target_node": addR, "target_pin": "A"},
    {"source_node": mulT, "source_pin": "ReturnValue", "target_node": addR, "target_pin": "B"},
    {"source_node": magW, "source_pin": "ReturnValue", "target_node": fmaxW2, "target_pin": "A"},
    {"source_node": addR, "source_pin": "ReturnValue", "target_node": fDiv, "target_pin": "A"},
    {"source_node": fmaxW2, "source_pin": "ReturnValue", "target_node": fDiv, "target_pin": "B"},
    {"source_node": fDiv, "source_pin": "ReturnValue", "target_node": fMin, "target_pin": "A"},
    {"source_node": fMin, "source_pin": "ReturnValue", "target_node": mulS, "target_pin": "B"},
])
LOG["steps"].append("softknee links fail=%d" % f2)

# ═══ 5) 구 비율 노드 제거 ═══
for nid in (divR, fmaxS):
    try:
        call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": FN, "node_id": nid})
    except RuntimeError as e:
        LOG["errors"].append({"remove_" + str(nid): str(e)[:120]})
LOG["steps"].append("old ratio nodes removed")

# ═══ 6) 컴파일 + 감사 ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:400])
g2 = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
for n in g2["nodes"]:
    for p in n.get("pins", []):
        if p.get("direction") != "input" or p.get("connected_to"):
            continue
        nm = p.get("name")
        if nm in ("Condition", "Point", "Array", "TargetArray", "Index", "Item", "InStruct", "S_GroomWindCap", "Object", "NewItem", "Value") or (nm in ("A", "B") and not p.get("default_value")) or (nm == "self" and "VariableGet" in n.get("class", "")):
            LOG["errors"].append({"unconnected": [n["id"], (n.get("title") or "")[:40], nm]})
