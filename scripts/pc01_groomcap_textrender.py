# PC_01_BP v4.2: DrawDebugString(SB2 HUD 부재로 무음 no-op) -> TextRenderComponent 표시로 교체
#   brDbg.then -> SetVisibility(true) -> K2_SetText(조립 텍스트) -> SetWorldRotation(카메라 바라보기)
#   brDbg.else -> SetVisibility(false)
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "ApplyGroomWindCap"
KML = "KismetMathLibrary"
KTL = "KismetTextLibrary"
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


# ═══ 1) 탐색: brDbg / dstr / c3(텍스트 최종 concat) ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
nodes = {n["id"]: n for n in g["nodes"]}
def P(n): return {p["name"]: p for p in n.get("pins", [])}
dstr = brDbg = c3 = None
for nid, n in nodes.items():
    pn = P(n)
    if "Draw Debug String" in (n.get("title") or ""):
        dstr = nid
        c3 = (pn.get("Text", {}).get("connected_to") or [""])[0].split(".")[0] or None
        brDbg = (pn.get("execute", {}).get("connected_to") or [""])[0].split(".")[0] or None
assert dstr and c3 and brDbg, "탐색 실패: %s %s %s" % (dstr, c3, brDbg)
LOG["steps"].append("found: dstr=%s c3=%s brDbg=%s" % (dstr, c3, brDbg))

# ═══ 2) dstr 제거 ═══
call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": FN, "node_id": dstr})

# ═══ 3) TextRender 체인 ═══
getTxt = add("VariableGet", 5100, 1100, variable_name="GroomWindDebugText")
getTxt2 = add("VariableGet", 5100, 1250, variable_name="GroomWindDebugText")
getTxt3 = add("VariableGet", 5100, 1400, variable_name="GroomWindDebugText")
getTxt4 = add("VariableGet", 5100, 1550, variable_name="GroomWindDebugText")
setVisT = add("CallFunction", 5300, 1050, function_name="SetVisibility", target_class="SceneComponent")
pindef(setVisT, "bNewVisibility", "true")
setVisF = add("CallFunction", 5300, 1700, function_name="SetVisibility", target_class="SceneComponent")
pindef(setVisF, "bNewVisibility", "false")
s2t = add("CallFunction", 5300, 1400, function_name="Conv_StringToText", target_class=KTL)
setText = add("CallFunction", 5550, 1100, function_name="K2_SetText", target_class="TextRenderComponent")
camMgr = add("CallFunction", 5500, 1350, function_name="GetPlayerCameraManager", target_class="GameplayStatics")
pindef(camMgr, "PlayerIndex", "0")
camLoc = add("CallFunction", 5700, 1350, function_name="K2_GetActorLocation", target_class="Actor")
txtLoc = add("CallFunction", 5700, 1500, function_name="K2_GetComponentLocation", target_class="SceneComponent")
lookAt = add("CallFunction", 5900, 1400, function_name="FindLookAtRotation", target_class=KML)
setRot = add("CallFunction", 6100, 1100, function_name="K2_SetWorldRotation", target_class="SceneComponent")

fails = connect([
    {"source_node": getTxt, "source_pin": "GroomWindDebugText", "target_node": setVisT, "target_pin": "self"},
    {"source_node": getTxt, "source_pin": "GroomWindDebugText", "target_node": setVisF, "target_pin": "self"},
    {"source_node": getTxt2, "source_pin": "GroomWindDebugText", "target_node": setText, "target_pin": "self"},
    {"source_node": c3, "source_pin": "ReturnValue", "target_node": s2t, "target_pin": "InString"},
    {"source_node": s2t, "source_pin": "ReturnValue", "target_node": setText, "target_pin": "Value"},
    {"source_node": camMgr, "source_pin": "ReturnValue", "target_node": camLoc, "target_pin": "self"},
    {"source_node": getTxt3, "source_pin": "GroomWindDebugText", "target_node": txtLoc, "target_pin": "self"},
    {"source_node": txtLoc, "source_pin": "ReturnValue", "target_node": lookAt, "target_pin": "Start"},
    {"source_node": camLoc, "source_pin": "ReturnValue", "target_node": lookAt, "target_pin": "Target"},
    {"source_node": getTxt4, "source_pin": "GroomWindDebugText", "target_node": setRot, "target_pin": "self"},
    {"source_node": lookAt, "source_pin": "ReturnValue", "target_node": setRot, "target_pin": "NewRotation"},
])
fails += connect([
    {"source_node": brDbg, "source_pin": "then", "target_node": setVisT, "target_pin": "execute"},
    {"source_node": setVisT, "source_pin": "then", "target_node": setText, "target_pin": "execute"},
    {"source_node": setText, "source_pin": "then", "target_node": setRot, "target_pin": "execute"},
    {"source_node": brDbg, "source_pin": "else", "target_node": setVisF, "target_pin": "execute"},
])
LOG["steps"].append("links fail=%d" % fails)

# K2_SetText Value 핀명 검증 (구버전은 'Text'일 수 있음)
det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": FN, "node_id": setText})
pn = [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]
LOG["steps"].append("setText pins: %s" % pn)
if "Value" not in pn and "Text" in pn:
    connect([{"source_node": s2t, "source_pin": "ReturnValue", "target_node": setText, "target_pin": "Text"}])
    LOG["steps"].append("fallback pin 'Text' connected")

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:400])
