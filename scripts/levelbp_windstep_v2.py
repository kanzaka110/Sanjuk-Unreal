# 레벨BP 글로벌 윈드 스텝퍼 v2 — 기존 GlobalWind Debug 체인과 완전 분리
#   PHASE A (원복): v1이 기존 랜덤라이저 체인에 넣은 수정 전부 되돌림
#     - WindStrength 값핀: step conv -> RandomFloatInRange(K2Node_CallFunction_4) 복원
#     - exec: SetStr.then -> inc 제거, SetStr.then -> SetTurbAmount 복원
#     - Delay_8 Duration: Hold 랜덤 소스 재연결
#     - v1 추가 노드 7개 삭제
#   PHASE B (신규 독립 체인): BeginPlay SEQ then_0(비어있음) ->
#     Branch(IsValid(새 리터럴)) -> Set WindStrength((idx%5)+1) ->
#     PrintString("GlobalWindStep Str N") -> idx+1 -> Delay 3.0 -> Branch 루프백
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
EG = "EventGraph"
KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"
KStr = "KismetStringLibrary"
SB_WV = "/Script/SB2.SBWindVolume"
SET_STR = "K2Node_VariableSet_1"
SET_TURB = "K2Node_VariableSet_2"
DELAY_OLD = "K2Node_CallFunction_8"
RAND_STR = "K2Node_CallFunction_4"   # 기존 강도 랜덤 (복원 대상)
SEQ_BP = "K2Node_ExecutionSequence_1"  # BeginPlay 시퀀스 (then_0 비어있음)
ACTOR = ("/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map."
         "SBWind_Weight_TEST01_Map:PersistentLevel.SBGlobalWindVolume")
LOG = {"steps": [], "errors": []}
atexit.register(lambda: print(json.dumps(LOG, ensure_ascii=False, indent=1)))


def call(tool: str, action: str, params: dict, timeout: int = 300) -> dict:
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def nid_of(r: dict) -> str:
    return r.get("node_id") or r.get("id")


def add(ntype: str, x: int, y: int, **kw) -> str:
    p = {"asset_path": BP, "graph_name": EG, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return nid_of(call("blueprint_query", "add_node", p))


def details(nid: str) -> dict:
    return call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": EG, "node_id": nid})


def pin_names(nid: str) -> list:
    det = details(nid)
    return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]


def connect(cs: list) -> int:
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": EG, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


def disconnect(nid: str, pin: str, **kw) -> None:
    p = {"asset_path": BP, "graph_name": EG, "node_id": nid, "pin_name": pin}
    p.update(kw)
    call("blueprint_query", "disconnect_pins", p)


def graph() -> dict:
    g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
    return {n["id"]: n for n in g["nodes"]}


def pm(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


nodes = graph()

# ═══ PHASE A: v1 원복 ═══
# v1 노드 역추적: conv(-> SET_STR.WindStrength 소스), inc(SET_STR.then 타깃)
sp = pm(nodes, SET_STR)
conv = (sp["WindStrength"].get("connected_to") or [""])[0].split(".")[0]
inc = (sp["then"].get("connected_to") or [""])[0].split(".")[0]
assert conv.startswith("K2Node_CallFunction"), "conv 미발견 (이미 원복됨?): %s" % conv
assert inc.startswith("K2Node_VariableSet"), "inc 미발견: %s" % inc
addn = (pm(nodes, conv).get("InInt", {}).get("connected_to") or [""])[0].split(".")[0]
mod = (pm(nodes, addn).get("A", {}).get("connected_to") or [""])[0].split(".")[0]
gidx = (pm(nodes, mod).get("A", {}).get("connected_to") or [""])[0].split(".")[0]
addi = (pm(nodes, inc).get("WindStepIdx", {}).get("connected_to") or [""])[0].split(".")[0]
gidx2 = (pm(nodes, addi).get("A", {}).get("connected_to") or [""])[0].split(".")[0]
v1_nodes = [conv, addn, mod, gidx, inc, addi, gidx2]
LOG["steps"].append("v1 nodes: %s" % v1_nodes)

# Delay_8 의 Hold 랜덤 소스 탐색: ReturnValue 고아 + Min/Max 가 Hold* 변수
hold_rand = None
for nid, n in nodes.items():
    if "Random Float in Range" not in (n.get("title") or "") or nid == RAND_STR:
        continue
    p = pm(nodes, nid)
    if p.get("ReturnValue", {}).get("connected_to"):
        continue
    srcs = []
    for k in ("Min", "Max"):
        for c in (p.get(k, {}).get("connected_to") or []):
            sid = c.split(".")[0]
            srcs.append(nodes.get(sid, {}).get("title") or "")
    if any("Hold" in s for s in srcs):
        hold_rand = nid
        LOG["steps"].append("hold_rand=%s (min/max: %s)" % (nid, srcs))
        break
assert hold_rand, "Hold 랜덤 노드 미발견 — 수동 확인 필요"

disconnect(SET_STR, "WindStrength")
disconnect(SET_STR, "then")
disconnect(inc, "then")
f = connect([
    {"source_node": RAND_STR, "source_pin": "ReturnValue", "target_node": SET_STR, "target_pin": "WindStrength"},
    {"source_node": SET_STR, "source_pin": "then", "target_node": SET_TURB, "target_pin": "execute"},
    {"source_node": hold_rand, "source_pin": "ReturnValue", "target_node": DELAY_OLD, "target_pin": "Duration"},
])
assert f == 0, "원복 배선 실패"
for nid in v1_nodes:
    call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": EG, "node_id": nid})
LOG["steps"].append("PHASE A 원복 완료 (노드 %d 삭제)" % len(v1_nodes))

# ═══ PHASE B: 독립 스텝퍼 체인 (y=9000 신규 존) ═══
nodes = graph()
seq_p = pm(nodes, SEQ_BP)
assert not (seq_p.get("then_0", {}).get("connected_to") or []), "SEQ then_0 이 비어있지 않음: %s" % seq_p.get("then_0", {}).get("connected_to")

BX, BY = 300, 9000
lit = add("K2Node_Literal", BX, BY + 350)
call("blueprint_query", "set_node_property", {"asset_path": BP, "graph_name": EG, "node_id": lit,
     "property_name": "ObjectRef", "value": ACTOR})
call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": lit})
lit_pin = [p for p in pin_names(lit) if p not in ("execute", "then")][0]
assert "GlobalWind" in lit_pin or "SBWind" in lit_pin, "리터럴 핀 이상: %s — 액터 경로 확인 필요" % lit_pin
LOG["steps"].append("literal ok pin=%s" % lit_pin)

isv = add("CallFunction", BX + 250, BY + 300, function_name="IsValid", target_class=KSL)
br = add("Branch", BX + 500, BY)

# Set WindStrength (외부 클래스 T3D §9)
sstr = add("VariableSet", BX + 800, BY, variable_name="WindStrength", target_class="SBWindVolume")
call("blueprint_query", "set_node_property", {"asset_path": BP, "graph_name": EG, "node_id": sstr,
     "property_name": "VariableReference",
     "value": '(MemberParent=%s,MemberName="WindStrength",bSelfContext=False)' % SB_WV})
call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": sstr})
assert "WindStrength" in pin_names(sstr), "WindStrength 셋터 값핀 실패"

# 스텝 계산: (idx % 5) + 1 -> double
g1 = add("VariableGet", BX + 200, BY + 500, variable_name="WindStepIdx")
mod2 = add("CallFunction", BX + 400, BY + 500, function_name="Percent_IntInt", target_class=KML)
add2 = add("CallFunction", BX + 600, BY + 500, function_name="Add_IntInt", target_class=KML)
cnv = add("CallFunction", BX + 800, BY + 500, function_name="Conv_IntToDouble", target_class=KML)

# PrintString: "GlobalWindStep Str N" (Key 고정 = 한 줄 갱신)
i2s = add("CallFunction", BX + 1000, BY + 650, function_name="Conv_IntToString", target_class=KStr)
cat = add("CallFunction", BX + 1200, BY + 650, function_name="Concat_StrStr", target_class=KStr)
prn = add("CallFunction", BX + 1200, BY, function_name="PrintString", target_class=KSL)

# idx 증가
g2 = add("VariableGet", BX + 1450, BY + 500, variable_name="WindStepIdx")
add3 = add("CallFunction", BX + 1600, BY + 500, function_name="Add_IntInt", target_class=KML)
inc2 = add("VariableSet", BX + 1650, BY, variable_name="WindStepIdx")
assert "WindStepIdx" in pin_names(inc2), "inc 셋터 값핀 실패"

dly = add("CallFunction", BX + 1950, BY, function_name="Delay", target_class=KSL)

call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": EG, "defaults": [
    {"node_id": mod2, "pin_name": "B", "value": "5"},
    {"node_id": add2, "pin_name": "B", "value": "1"},
    {"node_id": add3, "pin_name": "B", "value": "1"},
    {"node_id": cat, "pin_name": "A", "value": "GlobalWindStep Str "},
    {"node_id": prn, "pin_name": "Duration", "value": "3.0"},
    {"node_id": prn, "pin_name": "Key", "value": "WindStep"},
    {"node_id": dly, "pin_name": "Duration", "value": "3.0"},
]})

f = connect([
    # 값 체인
    {"source_node": lit, "source_pin": lit_pin, "target_node": isv, "target_pin": "Object"},
    {"source_node": isv, "source_pin": "ReturnValue", "target_node": br, "target_pin": "Condition"},
    {"source_node": lit, "source_pin": lit_pin, "target_node": sstr, "target_pin": "self"},
    {"source_node": g1, "source_pin": "WindStepIdx", "target_node": mod2, "target_pin": "A"},
    {"source_node": mod2, "source_pin": "ReturnValue", "target_node": add2, "target_pin": "A"},
    {"source_node": add2, "source_pin": "ReturnValue", "target_node": cnv, "target_pin": "InInt"},
    {"source_node": cnv, "source_pin": "ReturnValue", "target_node": sstr, "target_pin": "WindStrength"},
    {"source_node": add2, "source_pin": "ReturnValue", "target_node": i2s, "target_pin": "InInt"},
    {"source_node": i2s, "source_pin": "ReturnValue", "target_node": cat, "target_pin": "B"},
    {"source_node": cat, "source_pin": "ReturnValue", "target_node": prn, "target_pin": "InString"},
    {"source_node": g2, "source_pin": "WindStepIdx", "target_node": add3, "target_pin": "A"},
    {"source_node": add3, "source_pin": "ReturnValue", "target_node": inc2, "target_pin": "WindStepIdx"},
    # exec 체인: SEQ.then_0 -> Branch -> SetStr -> Print -> inc -> Delay -> Branch
    {"source_node": SEQ_BP, "source_pin": "then_0", "target_node": br, "target_pin": "execute"},
    {"source_node": br, "source_pin": "then", "target_node": sstr, "target_pin": "execute"},
    {"source_node": sstr, "source_pin": "then", "target_node": prn, "target_pin": "execute"},
    {"source_node": prn, "source_pin": "then", "target_node": inc2, "target_pin": "execute"},
    {"source_node": inc2, "source_pin": "then", "target_node": dly, "target_pin": "execute"},
    {"source_node": dly, "source_pin": "then", "target_node": br, "target_pin": "execute"},
])
LOG["steps"].append("PHASE B connects fail=%d" % f)
assert f == 0, "신규 체인 배선 실패"

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])

# 사후 검증: 원복 + 신규 체인 핵심 배선
nodes = graph()
sp = pm(nodes, SET_STR)
LOG["steps"].append("verify 원복 WindStrength <- %s" % sp["WindStrength"].get("connected_to"))
LOG["steps"].append("verify 원복 then -> %s" % sp["then"].get("connected_to"))
LOG["steps"].append("verify Delay_old Duration <- %s" % pm(nodes, DELAY_OLD)["Duration"].get("connected_to"))
LOG["steps"].append("verify SEQ.then_0 -> %s" % pm(nodes, SEQ_BP)["then_0"].get("connected_to"))
