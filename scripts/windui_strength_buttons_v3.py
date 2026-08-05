# 윈드 강도 UI 버튼 v3 — 레벨BP 전용 (2026-08-05)
#   v2 완료: WBP OnClicked 체인 5개 + 컴파일 클린 + 저장
#   v2 실패: 0731 노드ID(VariableSet_11/IfThenElse_8) 스테일 — 재탐색 결과:
#     Actor8 체인 = VariableSet_13 / Branch = IfThenElse_10 / 컴포넌트 소스 = CallFunction_138.ReturnValue
#     BeginPlay 헤드 SEQ_1(ExecutionSequence_1) then_4 빈 핀 -> 스플라이스 불필요, 직결
#   v3: ①SEQ_1.then_4 -> CreateWidget -> Cast -> InitWind -> AddToViewport -> bShowMouseCursor
#       ②UseWindStepper(bool, false) AND 게이트를 IfThenElse_10 Condition에 삽입 ③검증
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
MAP_BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
WBP_CLASS = WBP + ".WBP_WindStrengthButtons_C"
EG = "EventGraph"
SETSTR = "K2Node_VariableSet_13"      # Actor8 Set WindStrength
BR = "K2Node_IfThenElse_10"           # Actor8 스텝퍼 Branch
COMP_SRC = ("K2Node_CallFunction_138", "ReturnValue")  # GetComponentByClass(SBDirectionalWindComponent)
SEQ1 = "K2Node_ExecutionSequence_1"
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
        raise RuntimeError(action + ": " + txt[:500])
    return json.loads(txt)


def bpq(action: str, params: dict) -> dict:
    return call("blueprint_query", action, params)


def nid_of(r: dict) -> str:
    return r.get("node_id") or r.get("id")


def add(ntype: str, x: int, y: int, **kw) -> str:
    p = {"asset_path": MAP_BP, "graph_name": EG, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return nid_of(bpq("add_node", p))


def connect(cs: list) -> int:
    rc = bpq("connect_pins_bulk", {"asset_path": MAP_BP, "graph_name": EG, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


def graph_nodes() -> dict:
    g = bpq("get_graph_data", {"asset_path": MAP_BP, "graph_name": EG})
    return {n["id"]: n for n in g["nodes"]}


def pm(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def node_pins(nid: str) -> dict:
    det = bpq("get_node_details", {"asset_path": MAP_BP, "graph_name": EG, "node_id": nid})
    return {p.get("name"): p for p in (det.get("pins") or [])}


def fix_varset(nid: str, t3d: str) -> dict:
    bpq("set_node_property", {"asset_path": MAP_BP, "graph_name": EG, "node_id": nid,
                              "property_name": "VariableReference", "value": t3d})
    bpq("refresh_node", {"asset_path": MAP_BP, "graph_name": EG, "node_id": nid})
    return node_pins(nid)


nodes = graph_nodes()
for nid in (SETSTR, BR, COMP_SRC[0], SEQ1):
    assert nid in nodes, "기준 노드 미발견: %s" % nid
assert not (pm(nodes, SEQ1)["then_4"].get("connected_to")), "SEQ_1.then_4 이미 사용 중 — 재분석 필요"
self_t = pm(nodes, SETSTR)["self"].get("type", "")
assert "SBDirectionalWindComponent" in self_t, "SETSTR 타깃 예상 불일치: %s" % self_t
LOG["steps"].append("preflight ok")

# ═══ ① 위젯 체인 ═══
crt = add("CallFunction", -900, 2400, function_name="Create", target_class="WidgetBlueprintLibrary")
bpq("set_pin_default", {"asset_path": MAP_BP, "graph_name": EG, "node_id": crt,
                        "pin_name": "WidgetType", "value": WBP_CLASS})
cast = add("DynamicCast", -550, 2400, cast_class="WBP_WindStrengthButtons_C")
cast_pins = node_pins(cast)
as_pin = next(p for p in cast_pins if p.startswith("As"))
init = add("CallFunction", -200, 2400, function_name="InitWind", target_class="WBP_WindStrengthButtons_C")
init_pins = node_pins(init)
assert "Comp" in init_pins, "InitWind 노드 핀 이상: %s" % list(init_pins)
atv = add("CallFunction", 150, 2400, function_name="AddToViewport", target_class="UserWidget")
gpc = add("CallFunction", -900, 2700, function_name="GetPlayerController", target_class="GameplayStatics")
setcur = add("VariableSet", 500, 2400, variable_name="bShowMouseCursor", target_class="PlayerController")
cur_pins = node_pins(setcur)
if "bShowMouseCursor" not in cur_pins:
    cur_pins = fix_varset(setcur,
                          '(MemberParent=/Script/Engine.PlayerController,MemberName="bShowMouseCursor",bSelfContext=False)')
assert "bShowMouseCursor" in cur_pins, "bShowMouseCursor 셋 핀 미생성: %s" % list(cur_pins)
bpq("set_pin_default", {"asset_path": MAP_BP, "graph_name": EG, "node_id": setcur,
                        "pin_name": "bShowMouseCursor", "value": "true"})

f1 = connect([
    {"source_node": SEQ1, "source_pin": "then_4", "target_node": crt, "target_pin": "execute"},
    {"source_node": crt, "source_pin": "then", "target_node": cast, "target_pin": "execute"},
    {"source_node": cast, "source_pin": "then", "target_node": init, "target_pin": "execute"},
    {"source_node": init, "source_pin": "then", "target_node": atv, "target_pin": "execute"},
    {"source_node": atv, "source_pin": "then", "target_node": setcur, "target_pin": "execute"},
    {"source_node": crt, "source_pin": "ReturnValue", "target_node": cast, "target_pin": "Object"},
    {"source_node": cast, "source_pin": as_pin, "target_node": init, "target_pin": "self"},
    {"source_node": crt, "source_pin": "ReturnValue", "target_node": atv, "target_pin": "self"},
    {"source_node": COMP_SRC[0], "source_pin": COMP_SRC[1], "target_node": init, "target_pin": "Comp"},
    {"source_node": gpc, "source_pin": "ReturnValue", "target_node": setcur, "target_pin": "self"},
])
assert f1 == 0, "위젯 체인 배선 실패 — LOG.errors 확인"
LOG["steps"].append("위젯 체인 배선 OK")

# ═══ ② 스텝퍼 게이트 (Actor8 체인만) ═══
existing = {v["name"] for v in bpq("get_variables", {"asset_path": MAP_BP}).get("variables", [])}
if "UseWindStepper" not in existing:
    bpq("add_variable", {"asset_path": MAP_BP, "name": "UseWindStepper", "type": "bool",
                         "default_value": "false", "category": "WindStep", "instance_editable": True})
cond_conn = pm(nodes, BR)["Condition"].get("connected_to") or []
assert cond_conn, "Branch Condition 소스 미확인"
cond_node, cond_pin = cond_conn[0].rsplit(".", 1) if isinstance(cond_conn[0], str) else (
    cond_conn[0].get("node") or cond_conn[0].get("node_id"),
    cond_conn[0].get("pin") or cond_conn[0].get("pin_name"))
andn = add("CallFunction", -1500, 1500, function_name="BooleanAND", target_class="KismetMathLibrary")
vg_step = add("VariableGet", -1800, 1600, variable_name="UseWindStepper")
bpq("disconnect_pins", {"asset_path": MAP_BP, "graph_name": EG, "node_id": BR, "pin_name": "Condition"})
f2 = connect([
    {"source_node": cond_node, "source_pin": cond_pin, "target_node": andn, "target_pin": "A"},
    {"source_node": vg_step, "source_pin": "UseWindStepper", "target_node": andn, "target_pin": "B"},
    {"source_node": andn, "source_pin": "ReturnValue", "target_node": BR, "target_pin": "Condition"},
])
assert f2 == 0, "스텝퍼 게이트 배선 실패"
LOG["steps"].append("스텝퍼 게이트 OK (기존 Condition 소스=%s.%s)" % (cond_node, cond_pin))

cr = bpq("compile_blueprint", {"asset_path": MAP_BP})
LOG["steps"].append("compile 레벨BP: %s" % json.dumps(cr, ensure_ascii=False)[:300])
assert not cr.get("errors"), "레벨BP 컴파일 에러: %s" % cr

# ═══ ③ 최종 검증 (§24) ═══
nodes2 = graph_nodes()
checks = {
    "crt<-then_4": pm(nodes2, SEQ1)["then_4"].get("connected_to"),
    "WidgetType": pm(nodes2, crt)["WidgetType"].get("default_object") or pm(nodes2, crt)["WidgetType"].get("default_value"),
    "cast.Object": pm(nodes2, cast)["Object"].get("connected_to"),
    "init.self": pm(nodes2, init)["self"].get("connected_to"),
    "init.Comp": pm(nodes2, init)["Comp"].get("connected_to"),
    "atv.self": pm(nodes2, atv)["self"].get("connected_to"),
    "setcur.self": pm(nodes2, setcur)["self"].get("connected_to"),
    "and.A": pm(nodes2, andn)["A"].get("connected_to"),
    "and.B": pm(nodes2, andn)["B"].get("connected_to"),
    "BR.Condition": pm(nodes2, BR)["Condition"].get("connected_to"),
}
LOG["steps"].append({"verify": {k: (v if isinstance(v, str) else bool(v)) for k, v in checks.items()}})
missing = [k for k, v in checks.items() if not v]
assert not missing, "미연결 검증 실패: %s" % missing
LOG["steps"].append("v3 완료 — 맵 미저장(승호 판단). UseWindStepper=false 라 Actor8 자동 스텝퍼는 잠김")
