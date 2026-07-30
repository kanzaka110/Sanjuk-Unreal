# PC_01_BP v4.3: TextRender 표시 제거 -> DrawDebugString 복귀 (사용자 지정)
#   brDbg.then -> DrawDebugString(Text=c3, TextLocation=액터+230, cyan, dur 0)
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


g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
nodes = {n["id"]: n for n in g["nodes"]}
def P(n): return {p["name"]: p for p in n.get("pins", [])}

# TextRender 체인 노드 수집
kill = []
brDbg = c3 = addD = None
for nid, n in nodes.items():
    t = (n.get("title") or "")
    pn = P(n)
    cls = n.get("class", "")
    if any(k in t for k in ("Set Visibility", "Set Text", "Set World Rotation", "Find Look at Rotation", "Get Player Camera Manager", "To Text (String)")):
        kill.append(nid)
    if "VariableGet" in cls and "GroomWindDebugText" in pn:
        kill.append(nid)
    # camLoc/txtLoc: self 가 CameraManager/TextRender 에서 오는 위치 게터
    if "CallFunction" in cls and "GetActorLocation" in t.replace(" ", "") + n.get("class", ""):
        pass
for nid, n in nodes.items():
    pn = P(n)
    src = (pn.get("self", {}).get("connected_to") or [""])[0]
    if src and src.split(".")[0] in kill and nid not in kill:
        kill.append(nid)  # camLoc(셀프<-camMgr) / txtLoc(셀프<-getTxt)
# brDbg / c3 / addD(0,0,230)
for nid, n in nodes.items():
    pn = P(n)
    if "IfThenElse" in n.get("class", ""):
        cond = (pn.get("Condition", {}).get("connected_to") or [""])[0]
        if cond and "ShowGroomWindDebug" in str(P(nodes.get(cond.split(".")[0], {})).keys()):
            brDbg = nid
    if pn.get("B", {}).get("type") == "struct:Vector" and "230" in (pn.get("B", {}).get("default_value") or ""):
        addD = nid
for nid, n in nodes.items():
    pn = P(n)
    # c3 = InString 공급자 였던 최종 concat — To Text(String) 의 InString 소스
    if "To Text (String)" in (n.get("title") or ""):
        src = (pn.get("InString", {}).get("connected_to") or [""])[0]
        if src:
            c3 = src.split(".")[0]
assert brDbg and c3 and addD, "탐색 실패: brDbg=%s c3=%s addD=%s" % (brDbg, c3, addD)
LOG["steps"].append("brDbg=%s c3=%s addD=%s kill=%d" % (brDbg, c3, addD, len(kill)))

for nid in set(kill):
    try:
        call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": FN, "node_id": nid})
    except RuntimeError as e:
        LOG["errors"].append({"rm_" + nid: str(e)[:100]})
LOG["steps"].append("textrender chain removed")

# DrawDebugString 스폰 + 연결
r = call("blueprint_query", "add_node",
         {"asset_path": BP, "graph_name": FN, "node_type": "CallFunction",
          "function_name": "DrawDebugString", "target_class": "KismetSystemLibrary", "position": [5400, 1100]})
dstr = node_id_of(r)
for pin, val in (("TextColor", "(R=0.100000,G=1.000000,B=1.000000,A=1.000000)"), ("Duration", "0.0")):
    call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": FN, "node_id": dstr, "pin_name": pin, "value": val})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": [
    {"source_node": c3, "source_pin": "ReturnValue", "target_node": dstr, "target_pin": "Text"},
    {"source_node": addD, "source_pin": "ReturnValue", "target_node": dstr, "target_pin": "TextLocation"},
    {"source_node": brDbg, "source_pin": "then", "target_node": dstr, "target_pin": "execute"},
]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"conns": fails})
LOG["steps"].append("dstr wired (fail %d)" % len(fails))

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])
