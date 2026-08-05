# PC_01_BP ApplyGroomAirborneHold v2: 점프/낙하 중 헤어 뒤집힘 잔존 대응
#   실측 근거: 낙하 중 VelCap 0.30->0.066 정상 압축 + 시뮬 리셋 미발화 -> 주입속도 아닌 형태 유지 문제
#   처방: 공중(IsFalling) 동안 BendStiffnessScale 부스트(SB2 AutoResetBend와 동일 계열), 착지 후 FInterpTo 이징 복귀
#   체인: EventGraph ApplyGroomVelCap.then -> ApplyGroomAirborneHold
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "ApplyGroomAirborneHold"
KML = "KismetMathLibrary"
SBG = "/Script/SB2.SBCharacterGroomComponent"
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
    return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]


def pindef(nid, pin, val, graph=FN):
    call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": graph, "node_id": nid, "pin_name": pin, "value": val})


def connect(cs, graph=FN):
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": graph, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


def ext_var(node_type, var, x, y):
    nid = add(node_type, x, y, variable_name=var, target_class=SBG.split(".")[-1])
    call("blueprint_query", "set_node_property",
         {"asset_path": BP, "graph_name": FN, "node_id": nid,
          "property_name": "VariableReference",
          "value": '(MemberParent=%s,MemberName="%s",bSelfContext=False)' % (SBG, var)})
    call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": FN, "node_id": nid})
    if var not in pins_of(nid):
        raise SystemExit("%s %s 값핀 미생성" % (node_type, var))
    return nid


# ═══ 0) 프리플라이트 ═══
gnames = [g["name"] for g in call("blueprint_query", "list_graphs", {"asset_path": BP})["graphs"]]
if FN in gnames:
    raise SystemExit("%s 이미 존재 — 중복 실행 방지 중단" % FN)
assert "ApplyGroomVelCap" in gnames, "ApplyGroomVelCap 없음"

# ═══ 1) 변수 ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
for nm, ty, dv, ed in [
    ("AirHoldEnabled", "bool", "true", True),
    ("AirborneBendBoost", "float", "30.0", True),
    ("AirHoldBendBase", "float", "1.0", True),
    ("AirHoldReleaseSpeed", "float", "2.0", True),
]:
    if nm in existing:
        continue
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": nm, "type": ty, "default_value": dv,
          "category": "Hair|Groom Vel Cap", "instance_editable": ed})
LOG["steps"].append("vars ok")

# ═══ 2) 함수 + 게이트 ═══
call("blueprint_query", "add_function", {"asset_path": BP, "name": FN})
gf = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
entry = [n["id"] for n in gf["nodes"] if "FunctionEntry" in n.get("class", "")][0]

getEn = add("VariableGet", 200, 400, variable_name="AirHoldEnabled")
brEn = add("Branch", 400, 200)
# GetCharacterMovement는 UFUNCTION 아님 -> CharacterMovement 프로퍼티 겟 (self 컨텍스트)
getCMC = add("VariableGet", 300, 600, variable_name="CharacterMovement", target_class="Character")
call("blueprint_query", "set_node_property",
     {"asset_path": BP, "graph_name": FN, "node_id": getCMC,
      "property_name": "VariableReference",
      "value": '(MemberParent=/Script/Engine.Character,MemberName="CharacterMovement",bSelfContext=True)'})
call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": FN, "node_id": getCMC})
if "CharacterMovement" not in pins_of(getCMC):
    raise SystemExit("CharacterMovement 값핀 미생성")
isFall = add("CallFunction", 550, 600, function_name="IsFalling", target_class="PawnMovementComponent")
brFall = add("Branch", 800, 200)

# 공중: 수동 벤드 온 + 부스트 즉시 적용
setManual = ext_var("VariableSet", "bUseManualBendScales", 1100, 100)
pindef(setManual, "bUseManualBendScales", "true")
setBoost = ext_var("VariableSet", "BendStiffnessScale", 1400, 100)
getBoost = add("VariableGet", 1200, 350, variable_name="AirborneBendBoost")
getHairA = add("VariableGet", 900, 450, variable_name="Hair")

# 지상: FInterpTo 로 베이스 이징 복귀
getCur = ext_var("VariableGet", "BendStiffnessScale", 1100, 800)
getHairB = add("VariableGet", 900, 950, variable_name="Hair")
getBase = add("VariableGet", 1100, 1000, variable_name="AirHoldBendBase")
getDt = add("CallFunction", 1100, 1150, function_name="GetWorldDeltaSeconds", target_class="GameplayStatics")
getRel = add("VariableGet", 1100, 1300, variable_name="AirHoldReleaseSpeed")
interp = add("CallFunction", 1450, 900, function_name="FInterpTo", target_class=KML)
setRelease = ext_var("VariableSet", "BendStiffnessScale", 1750, 700)

f = connect([
    {"source_node": entry, "source_pin": "then", "target_node": brEn, "target_pin": "execute"},
    {"source_node": getEn, "source_pin": "AirHoldEnabled", "target_node": brEn, "target_pin": "Condition"},
    {"source_node": brEn, "source_pin": "then", "target_node": brFall, "target_pin": "execute"},
    {"source_node": getCMC, "source_pin": "CharacterMovement", "target_node": isFall, "target_pin": "self"},
    {"source_node": isFall, "source_pin": "ReturnValue", "target_node": brFall, "target_pin": "Condition"},
    # True: 부스트
    {"source_node": brFall, "source_pin": "then", "target_node": setManual, "target_pin": "execute"},
    {"source_node": setManual, "source_pin": "then", "target_node": setBoost, "target_pin": "execute"},
    {"source_node": getHairA, "source_pin": "Hair", "target_node": setManual, "target_pin": "self"},
    {"source_node": getHairA, "source_pin": "Hair", "target_node": setBoost, "target_pin": "self"},
    {"source_node": getBoost, "source_pin": "AirborneBendBoost", "target_node": setBoost, "target_pin": "BendStiffnessScale"},
    # False: 이징 복귀
    {"source_node": brFall, "source_pin": "else", "target_node": setRelease, "target_pin": "execute"},
    {"source_node": getHairB, "source_pin": "Hair", "target_node": getCur, "target_pin": "self"},
    {"source_node": getHairB, "source_pin": "Hair", "target_node": setRelease, "target_pin": "self"},
    {"source_node": getCur, "source_pin": "BendStiffnessScale", "target_node": interp, "target_pin": "Current"},
    {"source_node": getBase, "source_pin": "AirHoldBendBase", "target_node": interp, "target_pin": "Target"},
    {"source_node": getDt, "source_pin": "ReturnValue", "target_node": interp, "target_pin": "DeltaTime"},
    {"source_node": getRel, "source_pin": "AirHoldReleaseSpeed", "target_node": interp, "target_pin": "InterpSpeed"},
    {"source_node": interp, "source_pin": "ReturnValue", "target_node": setRelease, "target_pin": "BendStiffnessScale"},
])
LOG["steps"].append("links fail=%d" % f)

# ═══ 3) 컴파일 -> EventGraph 스플라이스 ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile1: %s" % json.dumps(cr, ensure_ascii=False)[:250])

# ApplyGroomVelCap 호출 노드 탐색 (테일)
sr = call("blueprint_query", "search_nodes", {"asset_path": BP, "query": "ApplyGroomVelCap"})
velCall = None
for r in sr.get("results", []):
    if r.get("graph") == "EventGraph" and r.get("class") == "K2Node_CallFunction":
        velCall = r["node_id"]
assert velCall, "velCall 미발견"

airCall = add("CallFunction", 1100, 1232, graph="EventGraph", function_name=FN)
call("blueprint_query", "set_node_property",
     {"asset_path": BP, "graph_name": "EventGraph", "node_id": airCall,
      "property_name": "FunctionReference",
      "value": '(MemberParent=None,MemberGuid=00000000000000000000000000000000,MemberName="%s",bSelfContext=True)' % FN})
call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": "EventGraph", "node_id": airCall})
f = connect([{"source_node": velCall, "source_pin": "then", "target_node": airCall, "target_pin": "execute"}], graph="EventGraph")
LOG["steps"].append("tick splice fail=%d velCall=%s airCall=%s" % (f, velCall, airCall))

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile2: %s" % json.dumps(cr, ensure_ascii=False)[:250])
