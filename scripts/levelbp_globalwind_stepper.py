# 레벨BP: SBGlobalWindVolume(클래스 SBWindVolume) WindStrength 를 3초 단위 1->2->3->4->5 반복 스텝으로 교체
#   대상 = 글로벌 랜덤라이저 루프의 K2Node_VariableSet_1 (유일한 SBWindVolume Set WindStrength)
#   1) int 변수 WindStepIdx 추가
#   2) 값핀: RandomFloatInRange -> (WindStepIdx % 5) + 1 -> IntToDouble
#   3) exec: SetStrength.then 에 WindStepIdx += 1 스플라이스
#   4) 글로벌 Delay Duration: 랜덤 -> 3.0 고정
#   존별 랜덤라이저(Directional/Radial/Vortex)는 무손상. 저장은 하지 않음(승호 수동).
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
EG = "EventGraph"
KML = "KismetMathLibrary"
SET_STR = "K2Node_VariableSet_1"   # Set WindStrength (self=SBWindVolume)
SET_TURB = "K2Node_VariableSet_2"  # Set TurbulenceAmount (기존 then 타깃)
SET_FREQ = "K2Node_VariableSet_3"  # Set TurbulenceFrequency (Delay 탐색 시작점)
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


# ═══ 0) 프리플라이트: 대상 노드 실재 + 배선 확인 ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
nodes = {n["id"]: n for n in g["nodes"]}
assert SET_STR in nodes and SET_TURB in nodes and SET_FREQ in nodes, "대상 노드 미발견 — 그래프 변동, 분석 재실행 필요"


def pins_map(nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


sp = pins_map(SET_STR)
then_ct = sp.get("then", {}).get("connected_to") or []
assert any(SET_TURB in c for c in then_ct), "SetStrength.then -> SetTurbAmount 배선 불일치: %s" % then_ct
str_src = sp.get("WindStrength", {}).get("connected_to") or []
LOG["steps"].append("preflight ok. WindStrength 현재 소스: %s" % str_src)

pos = nodes[SET_STR].get("position") or [800, -400]
bx, by = int(pos[0]), int(pos[1]) + 500

# 글로벌 Delay 탐색: SET_FREQ 부터 exec 체인 5홉 내 Delay
cur, delay_id = SET_FREQ, None
for _ in range(6):
    nxt = None
    for p in nodes[cur].get("pins", []):
        if p.get("direction") == "output" and p.get("type") == "exec" and (p.get("connected_to") or []):
            nxt = p["connected_to"][0].split(".")[0]
            break
    if not nxt:
        break
    if "Delay" in (nodes.get(nxt, {}).get("title") or ""):
        delay_id = nxt
        break
    cur = nxt
assert delay_id, "글로벌 Delay 미발견"
LOG["steps"].append("global delay = %s" % delay_id)

# ═══ 1) 변수 WindStepIdx ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
if "WindStepIdx" not in existing:
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": "WindStepIdx", "type": "int", "default_value": "0",
          "category": "WindStep", "instance_editable": True})
LOG["steps"].append("var WindStepIdx ok")

# ═══ 2) 스텝 계산 노드: (idx % 5) + 1 -> IntToDouble ═══
gidx = add("VariableGet", bx - 700, by, variable_name="WindStepIdx")
mod = add("CallFunction", bx - 500, by, function_name="Percent_IntInt", target_class=KML)
addn = add("CallFunction", bx - 300, by, function_name="Add_IntInt", target_class=KML)
conv = None
for fn in ("Conv_IntToDouble", "Conv_IntToFloat"):
    try:
        conv = add("CallFunction", bx - 100, by, function_name=fn, target_class=KML)
        conv_in = next(p for p in pin_names(conv) if p not in ("ReturnValue", "self", "execute", "then"))
        LOG["steps"].append("conv=%s in=%s" % (fn, conv_in))
        break
    except Exception as e:
        LOG["errors"].append({"conv_try": fn, "err": str(e)[:200]})
        conv = None
assert conv, "Int->Float 변환 노드 스폰 실패"

call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": EG, "defaults": [
    {"node_id": mod, "pin_name": "B", "value": "5"},
    {"node_id": addn, "pin_name": "B", "value": "1"},
]})

# ═══ 3) 증가 노드: WindStepIdx = WindStepIdx + 1 ═══
inc = add("VariableSet", bx + 150, by, variable_name="WindStepIdx")
assert "WindStepIdx" in pin_names(inc), "inc 셋터 값핀 미생성"
gidx2 = add("VariableGet", bx - 100, by + 150, variable_name="WindStepIdx")
addi = add("CallFunction", bx + 50, by + 150, function_name="Add_IntInt", target_class=KML)
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": EG, "defaults": [
    {"node_id": addi, "pin_name": "B", "value": "1"},
]})

# ═══ 4) 기존 배선 해제 (랜덤 값핀 / then 스플라이스 지점 / Delay Duration) ═══
disconnect(SET_STR, "WindStrength")
disconnect(SET_STR, "then", target_node=SET_TURB, target_pin="execute")
disconnect(delay_id, "Duration")
call("blueprint_query", "set_pin_default",
     {"asset_path": BP, "graph_name": EG, "node_id": delay_id, "pin_name": "Duration", "value": "3.0"})
LOG["steps"].append("disconnect + Duration=3.0 ok")

# ═══ 5) 신규 배선 ═══
fails = connect([
    {"source_node": gidx, "source_pin": "WindStepIdx", "target_node": mod, "target_pin": "A"},
    {"source_node": mod, "source_pin": "ReturnValue", "target_node": addn, "target_pin": "A"},
    {"source_node": addn, "source_pin": "ReturnValue", "target_node": conv, "target_pin": conv_in},
    {"source_node": conv, "source_pin": "ReturnValue", "target_node": SET_STR, "target_pin": "WindStrength"},
    {"source_node": gidx2, "source_pin": "WindStepIdx", "target_node": addi, "target_pin": "A"},
    {"source_node": addi, "source_pin": "ReturnValue", "target_node": inc, "target_pin": "WindStepIdx"},
    {"source_node": SET_STR, "source_pin": "then", "target_node": inc, "target_pin": "execute"},
    {"source_node": inc, "source_pin": "then", "target_node": SET_TURB, "target_pin": "execute"},
])
LOG["steps"].append("connects fail=%d" % fails)
assert fails == 0, "배선 실패 있음 — LOG.errors 확인"

# ═══ 6) 컴파일 + 사후 검증 ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])

det = details(SET_STR)
pins = det.get("pins") or det.get("node", {}).get("pins") or []
for p in pins:
    if p.get("name") in ("WindStrength", "then"):
        LOG["steps"].append("verify %s.%s -> %s" % (SET_STR, p["name"], p.get("connected_to")))
dd = details(delay_id)
for p in (dd.get("pins") or dd.get("node", {}).get("pins") or []):
    if p.get("name") == "Duration":
        LOG["steps"].append("verify Delay.Duration default=%s conn=%s" % (p.get("default_value"), p.get("connected_to")))
