# 윈드 강도 UI 버튼 5개 (2026-08-05)
#   A) WBP_WindStrengthButtons 신규: HorizontalBox + Button 5개(4/6/7.5/9/12)
#      OnClicked(ComponentBoundEvent) -> Set WindStrength(외부 VariableSet §9 복구) + PrintString
#      InitWind(Comp) 함수로 레벨BP에서 타깃 컴포넌트 주입
#   B) 레벨BP: BeginPlay 스플라이스 Sequence -> CreateWidget -> Cast -> InitWind -> AddToViewport
#      + PlayerController.bShowMouseCursor=true
#   C) 기존 3초 스텝퍼 게이트: UseWindStepper(bool, 기본 false) AND 삽입 — 버튼과 충돌 방지
# 레시피: reference-monolith-bp-rpc-recipes-0723 §9/§10/§19/§20/§22/§23/§24
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
MAP_BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
WBP_CLASS = WBP + ".WBP_WindStrengthButtons_C"
EG = "EventGraph"
SETSTR = "K2Node_VariableSet_11"     # 기존 Set WindStrength (Directional 컴포넌트)
BR = "K2Node_IfThenElse_8"           # 스텝퍼 Branch
VALUES = [("Btn_W4", "4", "4.0"), ("Btn_W6", "6", "6.0"), ("Btn_W7_5", "7.5", "7.5"),
          ("Btn_W9", "9", "9.0"), ("Btn_W12", "12", "12.0")]
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


def uiq(action: str, params: dict) -> dict:
    return call("ui_query", action, params)


def nid_of(r: dict) -> str:
    return r.get("node_id") or r.get("id")


def add(bp: str, graph: str, ntype: str, x: int, y: int, **kw) -> str:
    p = {"asset_path": bp, "graph_name": graph, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return nid_of(bpq("add_node", p))


def connect(bp: str, graph: str, cs: list) -> int:
    rc = bpq("connect_pins_bulk", {"asset_path": bp, "graph_name": graph, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"graph": graph, "conns": fails})
    return len(fails)


def graph_nodes(bp: str, graph: str) -> dict:
    g = bpq("get_graph_data", {"asset_path": bp, "graph_name": graph})
    return {n["id"]: n for n in g["nodes"]}


def pm(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def node_pins(bp: str, graph: str, nid: str) -> dict:
    det = bpq("get_node_details", {"asset_path": bp, "graph_name": graph, "node_id": nid})
    return {p.get("name"): p for p in (det.get("pins") or [])}


def fix_varset(bp: str, graph: str, nid: str, t3d: str) -> dict:
    """§9/§16: 파손 VariableSet에 VariableReference 주입 + refresh."""
    pins = node_pins(bp, graph, nid)
    bpq("set_node_property", {"asset_path": bp, "graph_name": graph, "node_id": nid,
                              "property_name": "VariableReference", "value": t3d})
    bpq("refresh_node", {"asset_path": bp, "graph_name": graph, "node_id": nid})
    pins = node_pins(bp, graph, nid)
    return pins


def compile_bp(bp: str, tag: str) -> None:
    cr = bpq("compile_blueprint", {"asset_path": bp})
    LOG["steps"].append("compile %s: %s" % (tag, json.dumps(cr, ensure_ascii=False)[:300]))
    assert not cr.get("errors"), "%s 컴파일 에러: %s" % (tag, cr)


# ═══════════════ A) 위젯 빌드 ═══════════════
r = uiq("create_widget_blueprint", {"save_path": WBP})
LOG["steps"].append("WBP 생성: %s" % json.dumps(r, ensure_ascii=False)[:200])

tree = uiq("get_widget_tree", {"asset_path": WBP})
LOG["steps"].append("tree: %s" % json.dumps(tree, ensure_ascii=False)[:300])
# 루트(CanvasPanel) 이름 추출
root = None
tw = tree.get("widgets") or tree.get("tree") or []
if isinstance(tw, list):
    for w in tw:
        if "Canvas" in (w.get("class") or w.get("type") or ""):
            root = w.get("name")
            break
root = root or tree.get("root_widget") or tree.get("root")
assert root, "루트 위젯 미확인: %s" % tree

uiq("add_widget", {"asset_path": WBP, "widget_class": "HorizontalBox", "widget_name": "WindBtnRow",
                   "parent_name": root, "anchor_preset": "bottom_center", "auto_size": True,
                   "position": {"x": 0, "y": -120}, "compile": False})
uiq("set_slot_property", {"asset_path": WBP, "widget_name": "WindBtnRow",
                          "alignment": {"x": 0.5, "y": 1.0}, "auto_size": True, "compile": False})

for btn, label, _v in VALUES:
    uiq("add_widget", {"asset_path": WBP, "widget_class": "Button", "widget_name": btn,
                       "parent_name": "WindBtnRow", "padding": {"left": 6, "top": 0, "right": 6, "bottom": 0},
                       "compile": False})
    uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": "Txt_" + btn,
                       "parent_name": btn, "compile": False})
    uiq("set_text", {"asset_path": WBP, "widget_name": "Txt_" + btn, "text": label,
                     "font_size": 22, "justification": "Center", "compile": False})
    uiq("set_widget_is_variable", {"wbp_path": WBP, "widget_name": btn, "is_variable": True})
LOG["steps"].append("버튼 5개 + 텍스트 배치 완료")

uiq("add_widget_variable", {"wbp_path": WBP, "var_name": "TargetWindComp",
                            "var_type": "object:SBDirectionalWindComponent"})

# InitWind(Comp) 함수
bpq("add_function", {"asset_path": WBP, "name": "InitWind", "category": "Wind"})
bpq("set_function_params", {"asset_path": WBP, "function_name": "InitWind",
                            "inputs": [{"name": "Comp", "type": "object:SBDirectionalWindComponent"}]})
fn_nodes = graph_nodes(WBP, "InitWind")
entry = next(nid for nid, n in fn_nodes.items() if "FunctionEntry" in nid)
vs_t = add(WBP, "InitWind", "VariableSet", 400, 0, variable_name="TargetWindComp")
pins = node_pins(WBP, "InitWind", vs_t)
if "TargetWindComp" not in pins:  # 파손 시 복구 (§16)
    pins = fix_varset(WBP, "InitWind", vs_t, '(MemberName="TargetWindComp",bSelfContext=True)')
assert "TargetWindComp" in pins, "InitWind VariableSet 파손 복구 실패: %s" % list(pins)
f = connect(WBP, "InitWind", [
    {"source_node": entry, "source_pin": "then", "target_node": vs_t, "target_pin": "execute"},
    {"source_node": entry, "source_pin": "Comp", "target_node": vs_t, "target_pin": "TargetWindComp"},
])
assert f == 0, "InitWind 배선 실패"
compile_bp(WBP, "WBP(InitWind)")

# EventGraph: 버튼별 OnClicked -> Get TargetWindComp -> Set WindStrength(외부) -> PrintString
T3D_WS = '(MemberParent=/Script/SB2.SBDirectionalWindComponent,MemberName="WindStrength",bSelfContext=False)'
for i, (btn, label, val) in enumerate(VALUES):
    y = i * 400
    ev = add(WBP, EG, "ComponentBoundEvent", 0, y, component_name=btn, delegate_property_name="OnClicked")
    vg = add(WBP, EG, "VariableGet", 250, y + 150, variable_name="TargetWindComp")
    vs = add(WBP, EG, "VariableSet", 550, y)
    pins = fix_varset(WBP, EG, vs, T3D_WS)
    assert "WindStrength" in pins, "%s Set WindStrength 핀 미생성: %s" % (btn, list(pins))
    ps = add(WBP, EG, "CallFunction", 900, y, function_name="PrintString", target_class="KismetSystemLibrary")
    bpq("set_pin_default", {"asset_path": WBP, "graph_name": EG, "node_id": vs,
                            "pin_name": "WindStrength", "value": val})
    bpq("set_pin_default", {"asset_path": WBP, "graph_name": EG, "node_id": ps,
                            "pin_name": "InString", "value": "DirWind Str = " + label})
    f = connect(WBP, EG, [
        {"source_node": ev, "source_pin": "then", "target_node": vs, "target_pin": "execute"},
        {"source_node": vg, "source_pin": "TargetWindComp", "target_node": vs, "target_pin": "self"},
        {"source_node": vs, "source_pin": "then", "target_node": ps, "target_pin": "execute"},
    ])
    assert f == 0, "%s OnClicked 체인 배선 실패" % btn
    LOG["steps"].append("%s 체인 OK (val=%s)" % (btn, val))

compile_bp(WBP, "WBP(최종)")
call("editor_query", "save_asset", {"asset_path": WBP})
LOG["steps"].append("WBP 저장 완료")

# ═══════════════ B) 레벨BP ═══════════════
nodes = graph_nodes(MAP_BP, EG)
assert SETSTR in nodes and BR in nodes, "레벨BP 기준 노드 미발견 — 재분석 필요"

# BeginPlay 노드 + 후속 진입점
bps = [nid for nid, n in nodes.items() if nid.startswith("K2Node_Event")
       and "BeginPlay" in json.dumps(n.get("title") or n.get("name") or n)]
assert len(bps) == 1, "BeginPlay 이벤트 특정 실패: %s" % bps
bp_ev = bps[0]
then_conn = pm(nodes, bp_ev)["then"].get("connected_to") or []
assert then_conn, "BeginPlay.then 미연결?"
head = then_conn[0]  # {"node": ..., "pin": ...} 형태 가정
head_node = head.get("node") or head.get("node_id")
head_pin = head.get("pin") or head.get("pin_name") or "execute"
LOG["steps"].append("BeginPlay=%s -> head=%s.%s" % (bp_ev, head_node, head_pin))

# 기존 컴포넌트 소스 (SETSTR.self 의 공급원 재사용, §19)
self_conn = pm(nodes, SETSTR)["self"].get("connected_to") or []
assert self_conn, "SETSTR.self 미연결 — 컴포넌트 소스 미확인"
comp_node = self_conn[0].get("node") or self_conn[0].get("node_id")
comp_pin = self_conn[0].get("pin") or self_conn[0].get("pin_name")
LOG["steps"].append("컴포넌트 소스 = %s.%s" % (comp_node, comp_pin))

# 위젯 체인 노드
ns = add(MAP_BP, EG, "Sequence", -1200, 2400)
crt = add(MAP_BP, EG, "CallFunction", -900, 2400, function_name="Create", target_class="WidgetBlueprintLibrary")
bpq("set_pin_default", {"asset_path": MAP_BP, "graph_name": EG, "node_id": crt,
                        "pin_name": "WidgetType", "value": WBP_CLASS})
cast = add(MAP_BP, EG, "DynamicCast", -550, 2400, cast_class="WBP_WindStrengthButtons_C")
cast_pins = node_pins(MAP_BP, EG, cast)
as_pin = next(p for p in cast_pins if p.startswith("As"))
init = add(MAP_BP, EG, "CallFunction", -200, 2400, function_name="InitWind",
           target_class="WBP_WindStrengthButtons_C")
init_pins = node_pins(MAP_BP, EG, init)
assert "Comp" in init_pins, "InitWind 노드 핀 이상: %s" % list(init_pins)
atv = add(MAP_BP, EG, "CallFunction", 150, 2400, function_name="AddToViewport", target_class="UserWidget")
gpc = add(MAP_BP, EG, "CallFunction", -900, 2700, function_name="GetPlayerController",
          target_class="GameplayStatics")
setcur = add(MAP_BP, EG, "VariableSet", 500, 2400)
fix_varset(MAP_BP, EG, setcur, '(MemberParent=/Script/Engine.PlayerController,MemberName="bShowMouseCursor",bSelfContext=False)')
cur_pins = node_pins(MAP_BP, EG, setcur)
assert "bShowMouseCursor" in cur_pins, "bShowMouseCursor 셋 핀 미생성: %s" % list(cur_pins)
bpq("set_pin_default", {"asset_path": MAP_BP, "graph_name": EG, "node_id": setcur,
                        "pin_name": "bShowMouseCursor", "value": "true"})

# BeginPlay 스플라이스 + 체인 배선
bpq("disconnect_pins", {"asset_path": MAP_BP, "graph_name": EG, "node_id": bp_ev, "pin_name": "then"})
f1 = connect(MAP_BP, EG, [
    {"source_node": bp_ev, "source_pin": "then", "target_node": ns, "target_pin": "execute"},
    {"source_node": ns, "source_pin": "then_0", "target_node": head_node, "target_pin": head_pin},
    {"source_node": ns, "source_pin": "then_1", "target_node": crt, "target_pin": "execute"},
    {"source_node": crt, "source_pin": "then", "target_node": cast, "target_pin": "execute"},
    {"source_node": cast, "source_pin": "then", "target_node": init, "target_pin": "execute"},
    {"source_node": init, "source_pin": "then", "target_node": atv, "target_pin": "execute"},
    {"source_node": atv, "source_pin": "then", "target_node": setcur, "target_pin": "execute"},
    {"source_node": crt, "source_pin": "ReturnValue", "target_node": cast, "target_pin": "Object"},
    {"source_node": cast, "source_pin": as_pin, "target_node": init, "target_pin": "self"},
    {"source_node": crt, "source_pin": "ReturnValue", "target_node": atv, "target_pin": "self"},
    {"source_node": comp_node, "source_pin": comp_pin, "target_node": init, "target_pin": "Comp"},
    {"source_node": gpc, "source_pin": "ReturnValue", "target_node": setcur, "target_pin": "self"},
])
assert f1 == 0, "레벨BP 위젯 체인 배선 실패 — LOG.errors 확인"
LOG["steps"].append("위젯 체인 배선 OK")

# ═══════════════ C) 스텝퍼 게이트 ═══════════════
existing = {v["name"] for v in bpq("get_variables", {"asset_path": MAP_BP}).get("variables", [])}
if "UseWindStepper" not in existing:
    bpq("add_variable", {"asset_path": MAP_BP, "name": "UseWindStepper", "type": "bool",
                         "default_value": "false", "category": "WindStep", "instance_editable": True})
cond_conn = pm(nodes, BR)["Condition"].get("connected_to") or []
assert cond_conn, "Branch Condition 소스 미확인"
cond_node = cond_conn[0].get("node") or cond_conn[0].get("node_id")
cond_pin = cond_conn[0].get("pin") or cond_conn[0].get("pin_name")
andn = add(MAP_BP, EG, "CallFunction", -1500, 1500, function_name="BooleanAND",
           target_class="KismetMathLibrary")
vg_step = add(MAP_BP, EG, "VariableGet", -1800, 1600, variable_name="UseWindStepper")
bpq("disconnect_pins", {"asset_path": MAP_BP, "graph_name": EG, "node_id": BR, "pin_name": "Condition"})
f2 = connect(MAP_BP, EG, [
    {"source_node": cond_node, "source_pin": cond_pin, "target_node": andn, "target_pin": "A"},
    {"source_node": vg_step, "source_pin": "UseWindStepper", "target_node": andn, "target_pin": "B"},
    {"source_node": andn, "source_pin": "ReturnValue", "target_node": BR, "target_pin": "Condition"},
])
assert f2 == 0, "스텝퍼 게이트 배선 실패"
LOG["steps"].append("스텝퍼 게이트 OK (기존 Condition 소스=%s.%s)" % (cond_node, cond_pin))

compile_bp(MAP_BP, "레벨BP")

# ═══════════════ 최종 검증 (§24 미연결 인풋 감사) ═══════════════
nodes2 = graph_nodes(MAP_BP, EG)
checks = {
    "ns<-BeginPlay": pm(nodes2, ns)["execute"].get("connected_to"),
    "head<-then_0": pm(nodes2, ns)["then_0"].get("connected_to"),
    "crt<-then_1": pm(nodes2, ns)["then_1"].get("connected_to"),
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
LOG["steps"].append("전체 빌드 완료 — 맵은 미저장(승호 판단), WBP는 디스크 저장됨")
