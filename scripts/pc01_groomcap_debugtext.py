# PC_01_BP ApplyGroomWindCap v4.1: 매칭된 그룸의 수신 윈드값 머리 위 표시
#   wsSet.then -> Branch(ShowGroomWindDebug) -> DrawDebugString("<그룸명> <받는값> / W <실제값>")
#   받는값 = fMin(factor) × magW(W)  — 소프트니 통과 후 소스 바람
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "ApplyGroomWindCap"
KML = "KismetMathLibrary"
KTL = "KismetTextLibrary"
KSL = "KismetSystemLibrary"
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
if "ShowGroomWindDebug" not in existing:
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": "ShowGroomWindDebug", "type": "bool", "default_value": "true",
          "category": "Hair|Groom Wind Cap", "instance_editable": True})
    LOG["steps"].append("var ShowGroomWindDebug (true)")

# ═══ 2) 탐색: wsSet / loopT / fMin / magW ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
nodes = {n["id"]: n for n in g["nodes"]}
def P(n): return {p["name"]: p for p in n.get("pins", [])}
wsSet = loopT = fMin = magW = mulS = None
for nid, n in nodes.items():
    pn = P(n)
    cls = n.get("class", "")
    if "VariableSet" in cls and "WindScale" in pn and pn.get("self", {}).get("type") == "object:SBGroomComponent":
        wsSet = nid
    if "MacroInstance" in cls and pn.get("Array Element", {}).get("type") == "object:SBGroomComponent":
        loopT = nid
    if "CallFunction" in cls and "Wind" in pn and "Point" in pn:
        callW = nid
# magW = callW.Wind 소비처(VSize), fMin = mulS.B 공급처; mulS = wsSet.WindScale 공급처
mulS = (P(nodes[wsSet]).get("WindScale", {}).get("connected_to") or [""])[0].split(".")[0] or None
fMin = (P(nodes[mulS]).get("B", {}).get("connected_to") or [""])[0].split(".")[0] if mulS else None
magW = (P(nodes[callW]).get("Wind", {}).get("connected_to") or [""])[0].split(".")[0] or None
LOG["steps"].append("found: wsSet=%s loopT=%s mulS=%s fMin=%s magW=%s" % (wsSet, loopT, mulS, fMin, magW))
assert all([wsSet, loopT, mulS, fMin, magW]), "탐색 실패"

# ═══ 3) 표시 체인 ═══
brDbg = add("Branch", 3700, 1100)
getShow = add("VariableGet", 3700, 1250, variable_name="ShowGroomWindDebug")
# 받는값 = factor × W
mulRecv = add("CallFunction", 4000, 1400, function_name="Multiply_DoubleDouble", target_class=KML)
# 텍스트 조립: "<그룸명> <recv> / W <raw>"
objName = add("CallFunction", 4000, 1550, function_name="GetObjectName", target_class=KSL)
convR = add("CallFunction", 4200, 1400, function_name="Conv_DoubleToText", target_class=KTL)
pindef(convR, "MaximumFractionalDigits", "1")
strR = add("CallFunction", 4400, 1400, function_name="Conv_TextToString", target_class=KTL)
convW = add("CallFunction", 4200, 1600, function_name="Conv_DoubleToText", target_class=KTL)
pindef(convW, "MaximumFractionalDigits", "1")
strW = add("CallFunction", 4400, 1600, function_name="Conv_TextToString", target_class=KTL)
c1 = add("CallFunction", 4600, 1450, function_name="Concat_StrStr", target_class="KismetStringLibrary")
c2 = add("CallFunction", 4780, 1450, function_name="Concat_StrStr", target_class="KismetStringLibrary")
c3 = add("CallFunction", 4960, 1450, function_name="Concat_StrStr", target_class="KismetStringLibrary")
c4 = add("CallFunction", 5140, 1450, function_name="Concat_StrStr", target_class="KismetStringLibrary")
pindef(c2, "B", " ")
pindef(c4, "B", " / W ")
# c1 = name + " " ... 조립 순서: c1=name&" "  -> 대신: c1(A=name,B=" ")? pindef 로는 안 되고 concat B는 연결/디폴트 —
# 구성: c1(A=objName, B=" ")  c3(A=c1+strR ... ) — 단순화: c1(A=objName,B=" "), c2 미사용 대신:
#   text = c1 & strR & " / W " & strW  => c1(A=objName,B=" ") -> cA(A=c1,B=strR) -> c4(A=cA,B=" / W ") -> cB(A=c4,B=strW)
# 위 노드 재활용: c2=cA, c3=cB 로 사용
pindef(c1, "B", " ")
locD = add("CallFunction", 4600, 1250, function_name="K2_GetActorLocation", target_class="Actor")
addD = add("CallFunction", 4800, 1250, function_name="Add_VectorVector", target_class=KML)
pindef(addD, "B", "0,0,230")
dstr = add("CallFunction", 5400, 1100, function_name="DrawDebugString", target_class=KSL)
pindef(dstr, "TextColor", "(R=0.100000,G=1.000000,B=1.000000,A=1.000000)")
pindef(dstr, "Duration", "0.0")

fails = connect([
    {"source_node": getShow, "source_pin": "ShowGroomWindDebug", "target_node": brDbg, "target_pin": "Condition"},
    {"source_node": fMin, "source_pin": "ReturnValue", "target_node": mulRecv, "target_pin": "A"},
    {"source_node": magW, "source_pin": "ReturnValue", "target_node": mulRecv, "target_pin": "B"},
    {"source_node": loopT, "source_pin": "Array Element", "target_node": objName, "target_pin": "Object"},
    {"source_node": mulRecv, "source_pin": "ReturnValue", "target_node": convR, "target_pin": "Value"},
    {"source_node": convR, "source_pin": "ReturnValue", "target_node": strR, "target_pin": "InText"},
    {"source_node": magW, "source_pin": "ReturnValue", "target_node": convW, "target_pin": "Value"},
    {"source_node": convW, "source_pin": "ReturnValue", "target_node": strW, "target_pin": "InText"},
    {"source_node": objName, "source_pin": "ReturnValue", "target_node": c1, "target_pin": "A"},
    {"source_node": c1, "source_pin": "ReturnValue", "target_node": c2, "target_pin": "A"},
    {"source_node": strR, "source_pin": "ReturnValue", "target_node": c2, "target_pin": "B"},
    {"source_node": c2, "source_pin": "ReturnValue", "target_node": c4, "target_pin": "A"},
    {"source_node": c4, "source_pin": "ReturnValue", "target_node": c3, "target_pin": "A"},
    {"source_node": strW, "source_pin": "ReturnValue", "target_node": c3, "target_pin": "B"},
    {"source_node": c3, "source_pin": "ReturnValue", "target_node": dstr, "target_pin": "Text"},
    {"source_node": locD, "source_pin": "ReturnValue", "target_node": addD, "target_pin": "A"},
    {"source_node": addD, "source_pin": "ReturnValue", "target_node": dstr, "target_pin": "TextLocation"},
])
# exec: wsSet.then -> brDbg.then -> dstr
fails += connect([
    {"source_node": wsSet, "source_pin": "then", "target_node": brDbg, "target_pin": "execute"},
    {"source_node": brDbg, "source_pin": "then", "target_node": dstr, "target_pin": "execute"},
])
LOG["steps"].append("links fail=%d" % fails)

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])
