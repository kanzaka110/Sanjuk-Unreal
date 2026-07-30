# 테스트맵 레벨BP: PlayerGroomWindText 라벨을 플레이어 머리 위로 구동
#   Tick 헤드 스플라이스: GetAllActorsOfClass(PC_01_BP_C) 루프 ->
#     K2_SetText(라벨, PC_01.GroomWindDebugString) -> SetActorLocation(머리+300) -> SetActorRotation(카메라 페이싱)
# 라벨 참조 = K2Node_Literal(§10), BP 클래스 프로퍼티 ext get(§9)
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SBWind_Weight_TEST01_Map"
EG = "EventGraph"
KML = "KismetMathLibrary"
LABEL = "/Game/Developers/SHIFTUP/CSH/SBWind_Weight_TEST01_Map.SBWind_Weight_TEST01_Map:PersistentLevel.TextRenderActor_UAID_30560F6BCAE536F302_1134197607"
PC01C = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP.PC_01_BP_C"
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


def nid_of(r):
    return r.get("node_id") or r.get("id")


def add(ntype, x, y, **kw):
    p = {"asset_path": BP, "graph_name": EG, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return nid_of(call("blueprint_query", "add_node", p))


def pindef(nid, pin, val):
    call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": EG, "node_id": nid, "pin_name": pin, "value": val})


def node_pins(nid):
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": EG, "node_id": nid})
    return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]


def ext_var(var, parents, x, y):
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": EG, "node_type": "VariableGet",
              "variable_name": var, "position": [x, y]})
    nid = nid_of(r)
    for parent in parents:
        call("blueprint_query", "set_node_property",
             {"asset_path": BP, "graph_name": EG, "node_id": nid,
              "property_name": "VariableReference",
              "value": '(MemberParent=%s,MemberName="%s",bSelfContext=False)' % (parent, var)})
        call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": nid})
        if var in node_pins(nid):
            LOG["steps"].append("ext %s OK (%s)" % (var, parent[:50]))
            return nid
    raise SystemExit("ext %s 실패" % var)


# ═══ 1) Tick 이벤트 + 기존 첫 노드 ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
tick = first = None
for n in g["nodes"]:
    if "K2Node_Event" in n.get("class", "") and "Tick" in (n.get("title") or ""):
        tick = n["id"]
        for p in n.get("pins", []):
            if p.get("name") == "then":
                ct = p.get("connected_to") or []
                first = ct[0] if ct else None
assert tick, "Tick 미발견"
LOG["steps"].append("tick=%s first=%s" % (tick, first))

# ═══ 2) 노드 ═══
gaaP = add("CallFunction", 100, 5000, function_name="GetAllActorsOfClass", target_class="GameplayStatics")
pindef(gaaP, "ActorClass", PC01C)
loopP = add("ForEachLoop", 400, 5000)
lit = add("K2Node_Literal", 700, 5300)
call("blueprint_query", "set_node_property", {"asset_path": BP, "graph_name": EG, "node_id": lit, "property_name": "ObjectRef", "value": LABEL})
call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": lit})
lit_pins = node_pins(lit)
lit_out = [p for p in lit_pins if p not in ("execute", "then")][0]
LOG["steps"].append("literal out pin: %s" % lit_out)
trGet = ext_var("TextRender", ["/Script/Engine.TextRenderActor"], 900, 5300)
gwds = ext_var("GroomWindDebugString", [PC01C, "BlueprintGeneratedClass'%s'" % PC01C], 700, 5150)
s2t = add("CallFunction", 950, 5150, function_name="Conv_StringToText", target_class="KismetTextLibrary")
setTxt = add("CallFunction", 1200, 5000, function_name="K2_SetText", target_class="TextRenderComponent")
locP = add("CallFunction", 1200, 5250, function_name="K2_GetActorLocation", target_class="Actor")
headP = add("CallFunction", 1400, 5250, function_name="Add_VectorVector", target_class=KML)
pindef(headP, "B", "0,0,300")
setLoc = add("CallFunction", 1650, 5000, function_name="K2_SetActorLocation", target_class="Actor")
cam = add("CallFunction", 1650, 5350, function_name="GetPlayerCameraManager", target_class="GameplayStatics")
pindef(cam, "PlayerIndex", "0")
camLoc = add("CallFunction", 1850, 5350, function_name="K2_GetActorLocation", target_class="Actor")
look = add("CallFunction", 2050, 5300, function_name="FindLookAtRotation", target_class=KML)
setRot = add("CallFunction", 2300, 5000, function_name="K2_SetActorRotation", target_class="Actor")

conns = [
    {"source_node": gaaP, "source_pin": "OutActors", "target_node": loopP, "target_pin": "Array"},
    {"source_node": loopP, "source_pin": "Array Element", "target_node": gwds, "target_pin": "self"},
    {"source_node": loopP, "source_pin": "Array Element", "target_node": locP, "target_pin": "self"},
    {"source_node": lit, "source_pin": lit_out, "target_node": trGet, "target_pin": "self"},
    {"source_node": trGet, "source_pin": "TextRender", "target_node": setTxt, "target_pin": "self"},
    {"source_node": gwds, "source_pin": "GroomWindDebugString", "target_node": s2t, "target_pin": "InString"},
    {"source_node": s2t, "source_pin": "ReturnValue", "target_node": setTxt, "target_pin": "Value"},
    {"source_node": locP, "source_pin": "ReturnValue", "target_node": headP, "target_pin": "A"},
    {"source_node": lit, "source_pin": lit_out, "target_node": setLoc, "target_pin": "self"},
    {"source_node": headP, "source_pin": "ReturnValue", "target_node": setLoc, "target_pin": "NewLocation"},
    {"source_node": cam, "source_pin": "ReturnValue", "target_node": camLoc, "target_pin": "self"},
    {"source_node": headP, "source_pin": "ReturnValue", "target_node": look, "target_pin": "Start"},
    {"source_node": camLoc, "source_pin": "ReturnValue", "target_node": look, "target_pin": "Target"},
    {"source_node": lit, "source_pin": lit_out, "target_node": setRot, "target_pin": "self"},
    {"source_node": look, "source_pin": "ReturnValue", "target_node": setRot, "target_pin": "NewRotation"},
    # exec
    {"source_node": tick, "source_pin": "then", "target_node": gaaP, "target_pin": "execute"},
    {"source_node": gaaP, "source_pin": "then", "target_node": loopP, "target_pin": "Exec"},
    {"source_node": loopP, "source_pin": "LoopBody", "target_node": setTxt, "target_pin": "execute"},
    {"source_node": setTxt, "source_pin": "then", "target_node": setLoc, "target_pin": "execute"},
    {"source_node": setLoc, "source_pin": "then", "target_node": setRot, "target_pin": "execute"},
]
if first:
    fn_node, fn_pin = first.split(".")
    call("blueprint_query", "disconnect_pins",
         {"asset_path": BP, "graph_name": EG,
          "source_node": tick, "source_pin": "then", "target_node": fn_node, "target_pin": fn_pin})
    conns.append({"source_node": loopP, "source_pin": "Completed", "target_node": fn_node, "target_pin": fn_pin})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": EG, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"conns": fails})
LOG["steps"].append("links: %d req %d fail" % (len(conns), len(fails)))

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])
