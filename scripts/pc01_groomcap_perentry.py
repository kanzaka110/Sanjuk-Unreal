# PC_01_BP 그룸 윈드캡 v2: 등록 배열을 (GroomAsset, MaxWind) 구조체 배열로 확장
# 1) S_GroomWindCap 구조체 에셋 생성 (Hair 폴더)
# 2) GroomCapEntries(array:struct) 변수 + 내부 WcMatched/WcMatchedMax
# 3) ApplyGroomWindCap: Array_Contains 판정 -> 엔트리 루프(에셋 매칭 + 개별 Max 래치)로 교체
#    factor 계산의 Max 소스를 WcMatchedMax 로 리와이어 (미등록+빈배열 폴백 = GroomWindMax)
# 4) TargetGroomAssets 변수/노드 제거
# UDS 함정 대비: BreakStruct 핀명은 GUID 접미사 -> 실핀명 조회 후 연결
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "ApplyGroomWindCap"
STRUCT = "/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/S_GroomWindCap"
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


def pins_of(nid):
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": FN, "node_id": nid})
    return det.get("pins") or det.get("node", {}).get("pins") or []


def connect(cs):
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


# ═══ 0) 구조체 생성 ═══
try:
    call("blueprint_query", "create_user_defined_struct",
         {"save_path": STRUCT,
          "fields": [{"name": "GroomAsset", "type": "object:GroomAsset"},
                     {"name": "MaxWind", "type": "float", "default_value": "10.0"}]})
    LOG["steps"].append("struct created")
except RuntimeError as e:
    if "exist" in str(e).lower():
        LOG["steps"].append("struct exists")
    else:
        raise

# ═══ 1) 변수 정리 ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
if "GroomCapEntries" not in existing:
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": "GroomCapEntries", "type": "array:struct:S_GroomWindCap",
          "category": "Hair|Groom Wind Cap", "instance_editable": True})
    LOG["steps"].append("var GroomCapEntries")
for nm, ty in (("WcMatched", "bool"), ("WcMatchedMax", "float")):
    if nm not in existing:
        call("blueprint_query", "add_variable", {"asset_path": BP, "name": nm, "type": ty, "category": "Hair|Groom Wind Cap", "instance_editable": False})
LOG["steps"].append("vars ok")

# ═══ 2) 기존 노드 탐색 ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
nodes = {n["id"]: n for n in g["nodes"]}
def P(n): return {p["name"]: p for p in n.get("pins", [])}
getTargets = cont = lenT = eq0 = orNew = brMatch = gaGet = loopT = getMaxW = gtW = divW = None
for nid, n in nodes.items():
    pn = P(n)
    t = (n.get("title") or "")
    cls = n.get("class", "")
    if "VariableGet" in cls and "TargetGroomAssets" in pn:
        getTargets = nid
    if "CallArrayFunction" in cls and "ItemToFind" in pn:
        cont = nid
    if "CallArrayFunction" in cls and "ReturnValue" in pn and "ItemToFind" not in pn and pn.get("TargetArray", {}).get("type", "").startswith("array:object:GroomAsset"):
        lenT = nid
    if "Equal (Integer)" in t or ("EqualEqual" in t and "Integer" in t):
        eq0 = nid
    if "OR Boolean" in t:
        orNew = nid
    if "IfThenElse" in cls:
        cond = (pn.get("Condition", {}).get("connected_to") or [""])[0]
        if cond and "OR" in (nodes.get(cond.split(".")[0], {}).get("title") or ""):
            brMatch = nid
    if "VariableGet" in cls and "GroomAsset" in pn and pn.get("self", {}).get("type", "").startswith("object:"):
        gaGet = nid
    if "MacroInstance" in cls and pn.get("Array Element", {}).get("type") == "object:SBGroomComponent":
        loopT = nid
    if "VariableGet" in cls and "GroomWindMax" in pn:
        getMaxW = nid
# gtW/divW = GroomWindMax 게터(사본 포함 전부)의 소비처 (§16 사본 귀속 + 타이틀 한글화 대응)
maxGetters = [nid for nid, n in nodes.items() if "VariableGet" in n.get("class", "") and "GroomWindMax" in P(n)]
for mg in maxGetters:
    for c in (P(nodes[mg]).get("GroomWindMax", {}).get("connected_to") or []):
        cn, cp = c.split(".")
        if cp == "B":
            gtW = cn
            getMaxW = mg
        if cp == "A":
            divW = cn
# eq0 별도 탐색 (int equal, B=0)
if not eq0:
    for nid, n in nodes.items():
        pn = P(n)
        if "CallFunction" in n.get("class", "") and pn.get("A", {}).get("type") == "int" and pn.get("B", {}).get("type") == "int" and "ReturnValue" in pn:
            eq0 = nid
LOG["steps"].append("found: getTargets=%s cont=%s lenT=%s eq0=%s orNew=%s brMatch=%s gaGet=%s loopT=%s getMaxW=%s gtW=%s divW=%s"
                    % (getTargets, cont, lenT, eq0, orNew, brMatch, gaGet, loopT, getMaxW, gtW, divW))
assert all([getTargets, cont, lenT, eq0, orNew, brMatch, gaGet, loopT, getMaxW, gtW, divW]), "탐색 실패"

# ═══ 3) 구 노드 제거 (cont, getTargets) ═══
call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": FN, "node_id": cont})
call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": FN, "node_id": getTargets})
LOG["steps"].append("cont/getTargets removed")

# ═══ 4) 신규 노드 ═══
getEntries = add("VariableGet", 2350, 1650, variable_name="GroomCapEntries")
getEntries2 = add("VariableGet", 2350, 1800, variable_name="GroomCapEntries")
loopE = add("ForEachLoop", 2600, 1100)
brk = add("BreakStruct", 2850, 1250, struct_type="S_GroomWindCap")
eqObj = add("CallFunction", 3050, 1350, function_name="EqualEqual_ObjectObject", target_class="KismetMathLibrary")
brEq = add("Branch", 3250, 1150)
setM0 = add("VariableSet", 2200, 1000, variable_name="WcMatched")
setMM0 = add("VariableSet", 2400, 1000, variable_name="WcMatchedMax")
setM1 = add("VariableSet", 3450, 1150, variable_name="WcMatched")
setMM1 = add("VariableSet", 3650, 1150, variable_name="WcMatchedMax")
getM = add("VariableGet", 2900, 1700, variable_name="WcMatched")
getMM = add("VariableGet", 2900, 1850, variable_name="WcMatchedMax")
call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": FN, "node_id": setM1, "pin_name": "WcMatched", "value": "true"})

# UDS break 실핀명 (GUID 접미사)
bp_pins = pins_of(brk)
pin_ga = pin_mw = None
for p in bp_pins:
    nm = p.get("name", "")
    if nm.startswith("GroomAsset"):
        pin_ga = nm
    if nm.startswith("MaxWind"):
        pin_mw = nm
assert pin_ga and pin_mw, "UDS break 핀 미발견: %s" % [p.get("name") for p in bp_pins]
LOG["steps"].append("break pins: %s / %s" % (pin_ga, pin_mw))

# ═══ 5) 연결 ═══
fails = connect([
    # lenT 재타깃 (배열핀 먼저)
    {"source_node": getEntries2, "source_pin": "GroomCapEntries", "target_node": lenT, "target_pin": "TargetArray"},
    {"source_node": getEntries, "source_pin": "GroomCapEntries", "target_node": loopE, "target_pin": "Array"},
    {"source_node": loopE, "source_pin": "Array Element", "target_node": brk, "target_pin": "InStruct"},
    {"source_node": brk, "source_pin": pin_ga, "target_node": eqObj, "target_pin": "A"},
    {"source_node": gaGet, "source_pin": "GroomAsset", "target_node": eqObj, "target_pin": "B"},
    {"source_node": eqObj, "source_pin": "ReturnValue", "target_node": brEq, "target_pin": "Condition"},
    {"source_node": brk, "source_pin": pin_mw, "target_node": setMM1, "target_pin": "WcMatchedMax"},
    {"source_node": getMaxW, "source_pin": "GroomWindMax", "target_node": setMM0, "target_pin": "WcMatchedMax"},
    # 판정: Matched OR 빈배열
    {"source_node": getM, "source_pin": "WcMatched", "target_node": orNew, "target_pin": "A"},
    # factor Max 소스 리와이어
    {"source_node": getMM, "source_pin": "WcMatchedMax", "target_node": gtW, "target_pin": "B"},
    {"source_node": getMM, "source_pin": "WcMatchedMax", "target_node": divW, "target_pin": "A"},
])
# exec 리와이어: loopT.LoopBody -> setM0 -> setMM0 -> loopE ; loopE.Completed -> brMatch
call("blueprint_query", "disconnect_pins",
     {"asset_path": BP, "graph_name": FN,
      "source_node": loopT, "source_pin": "LoopBody", "target_node": brMatch, "target_pin": "execute"})
fails += connect([
    {"source_node": loopT, "source_pin": "LoopBody", "target_node": setM0, "target_pin": "execute"},
    {"source_node": setM0, "source_pin": "then", "target_node": setMM0, "target_pin": "execute"},
    {"source_node": setMM0, "source_pin": "then", "target_node": loopE, "target_pin": "Exec"},
    {"source_node": loopE, "source_pin": "LoopBody", "target_node": brEq, "target_pin": "execute"},
    {"source_node": brEq, "source_pin": "then", "target_node": setM1, "target_pin": "execute"},
    {"source_node": setM1, "source_pin": "then", "target_node": setMM1, "target_pin": "execute"},
    {"source_node": loopE, "source_pin": "Completed", "target_node": brMatch, "target_pin": "execute"},
])
LOG["steps"].append("links done, fails=%d" % fails)

# ═══ 6) TargetGroomAssets 변수 제거 ═══
call("blueprint_query", "remove_variable", {"asset_path": BP, "name": "TargetGroomAssets"})
LOG["steps"].append("TargetGroomAssets removed")

# ═══ 7) 컴파일 + 감사 ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:400])
g2 = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
for n in g2["nodes"]:
    for p in n.get("pins", []):
        if p.get("direction") != "input" or p.get("connected_to"):
            continue
        nm = p.get("name")
        if nm in ("Condition", "Point", "Array", "TargetArray", "Index", "Item", "ItemToFind", "InStruct", "NewItem", "Object") or (nm == "self" and "VariableGet" in n.get("class", "")):
            LOG["errors"].append({"unconnected": [n["id"], (n.get("title") or "")[:40], nm]})
