# PC_01_BP ApplyGroomWindCap v3: 하드캡 -> 비율 리맵 (WindScale = base * MatchedMax / WindSystemMax)
# - WindSystemMax(기본 15) 변수 추가
# - 바람 크기 측정 체인(callW/magW/gtW/fmaxW/divW/selW/locO/headO) 제거 -> 상수 비율 팩터로 교체
# - CalcWindAt 함수 자체는 보존 (미호출, 진단/복귀용)
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "ApplyGroomWindCap"
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


# ═══ 1) 변수 ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
if "WindSystemMax" not in existing:
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": "WindSystemMax", "type": "float", "default_value": "15.0",
          "category": "Hair|Groom Wind Cap", "instance_editable": True})
    LOG["steps"].append("var WindSystemMax (15)")

# ═══ 2) 노드 탐색 ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
nodes = {n["id"]: n for n in g["nodes"]}
def P(n): return {p["name"]: p for p in n.get("pins", [])}

# callW = CalcWindAt 셀프콜 (Wind 출력)
callW = mulS = getMM = loopT = None
for nid, n in nodes.items():
    pn = P(n)
    cls = n.get("class", "")
    if "CallFunction" in cls and "Wind" in pn and "Point" in pn:
        callW = nid
    if "VariableGet" in cls and "WcMatchedMax" in pn:
        getMM = nid
    if "MacroInstance" in cls and pn.get("Array Element", {}).get("type") == "object:SBGroomComponent":
        loopT = nid
assert callW and getMM and loopT, "탐색1 실패: %s %s %s" % (callW, getMM, loopT)

# mulS = WcMatchedMax 게터(사본 포함)의 소비처 중 Multiply (wsSet.WindScale 로 이어지는 것)
mmGetters = [nid for nid, n in nodes.items() if "VariableGet" in n.get("class", "") and "WcMatchedMax" in P(n)]
gtW = divW = None
for mg in mmGetters:
    for c in (P(nodes[mg]).get("WcMatchedMax", {}).get("connected_to") or []):
        cn, cp = c.split(".")
        if cp == "B":
            gtW = cn
        if cp == "A":
            divW = cn
# mulS: divW(=MatchedMax/fmax) 의 ReturnValue 소비처를 따라감: divW->selW->mulS
selW = None
if divW:
    for c in (P(nodes[divW]).get("ReturnValue", {}).get("connected_to") or []):
        selW = c.split(".")[0]
if selW:
    for c in (P(nodes[selW]).get("ReturnValue", {}).get("connected_to") or []):
        mulS = c.split(".")[0]
# 제거 대상 역추적: magW(VSize)=callW.Wind 소비처, gtW/fmaxW=magW 소비처, locO/headO=callW.Point 공급처
magW = (P(nodes[callW]).get("Wind", {}).get("connected_to") or [""])[0].split(".")[0] or None
fmaxW = None
if magW:
    for c in (P(nodes[magW]).get("ReturnValue", {}).get("connected_to") or []):
        cn, cp = c.split(".")
        if cn not in (gtW,):
            fmaxW = cn
headO = (P(nodes[callW]).get("Point", {}).get("connected_to") or [""])[0].split(".")[0] or None
locO = None
if headO:
    locO = (P(nodes[headO]).get("A", {}).get("connected_to") or [""])[0].split(".")[0] or None
LOG["steps"].append("found: callW=%s magW=%s gtW=%s fmaxW=%s divW=%s selW=%s mulS=%s headO=%s locO=%s"
                    % (callW, magW, gtW, fmaxW, divW, selW, mulS, headO, locO))
assert all([mulS, magW, gtW, fmaxW, divW, selW, headO, locO]), "탐색2 실패"

# ═══ 3) exec 리와이어: callW 우회 ═══
# 기존: brCached.then->callW / loopB.Completed->callW / callW.then->loopT
exec_srcs = P(nodes[callW]).get("execute", {}).get("connected_to") or []
for s in exec_srcs:
    sn, sp = s.split(".")
    call("blueprint_query", "disconnect_pins",
         {"asset_path": BP, "graph_name": FN, "source_node": sn, "source_pin": sp,
          "target_node": callW, "target_pin": "execute"})
call("blueprint_query", "disconnect_pins",
     {"asset_path": BP, "graph_name": FN, "source_node": callW, "source_pin": "then",
      "target_node": loopT, "target_pin": "Exec"})
conns = []
for s in exec_srcs:
    sn, sp = s.split(".")
    conns.append({"source_node": sn, "source_pin": sp, "target_node": loopT, "target_pin": "Exec"})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"exec_rewire": fails})
LOG["steps"].append("exec bypass: %d srcs -> loopT (fail %d)" % (len(exec_srcs), len(fails)))

# ═══ 4) 팩터 교체: mulS.B <- MatchedMax / FMax(WindSystemMax, 0.001) ═══
getSys = add("VariableGet", 2700, 1950, variable_name="WindSystemMax")
fmaxS = add("CallFunction", 2900, 1950, function_name="FMax", target_class="KismetMathLibrary")
divR = add("CallFunction", 3100, 1900, function_name="Divide_DoubleDouble", target_class="KismetMathLibrary")
call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": FN, "node_id": fmaxS, "pin_name": "B", "value": "0.001"})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": [
    {"source_node": getSys, "source_pin": "WindSystemMax", "target_node": fmaxS, "target_pin": "A"},
    {"source_node": fmaxS, "source_pin": "ReturnValue", "target_node": divR, "target_pin": "B"},
    {"source_node": getMM, "source_pin": "WcMatchedMax", "target_node": divR, "target_pin": "A"},
    {"source_node": divR, "source_pin": "ReturnValue", "target_node": mulS, "target_pin": "B"},
]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"factor": fails})
LOG["steps"].append("factor rewired (fail %d)" % len(fails))

# ═══ 5) 미사용 노드 제거 ═══
for nid in (callW, magW, gtW, fmaxW, divW, selW, headO, locO):
    try:
        call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": FN, "node_id": nid})
    except RuntimeError as e:
        LOG["errors"].append({"remove_" + nid: str(e)[:120]})
LOG["steps"].append("old chain removed (8)")

# ═══ 6) 컴파일 + 감사 ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:400])
g2 = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
for n in g2["nodes"]:
    for p in n.get("pins", []):
        if p.get("direction") != "input" or p.get("connected_to"):
            continue
        nm = p.get("name")
        if nm in ("Condition", "Point", "Array", "TargetArray", "Index", "Item", "InStruct", "S_GroomWindCap", "Object", "NewItem") or (nm in ("A", "B") and not p.get("default_value")) or (nm == "self" and "VariableGet" in n.get("class", "")):
            LOG["errors"].append({"unconnected": [n["id"], (n.get("title") or "")[:40], nm]})
