# 윈드 강도 UI 버튼 v2 — v1 이어서 (2026-08-05)
#   v1 완료: WBP 생성 + 버튼5(변수화) + TargetWindComp + InitWind (컴파일 클린, 디스크 저장)
#   v1 실패: EventGraph 외부 VariableSet 스폰에 variable_name 누락 -> Btn_W4 고아 ev/vg 잔류
#   v2: ①고아 정리 ②OnClicked 체인 5개(variable_name+target_class 스폰, §9 복구 폴백)
#       ③레벨BP CreateWidget 체인 ④스텝퍼 UseWindStepper 게이트 ⑤검증(§24)
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
    bpq("set_node_property", {"asset_path": bp, "graph_name": graph, "node_id": nid,
                              "property_name": "VariableReference", "value": t3d})
    bpq("refresh_node", {"asset_path": bp, "graph_name": graph, "node_id": nid})
    return node_pins(bp, graph, nid)


def compile_bp(bp: str, tag: str) -> None:
    cr = bpq("compile_blueprint", {"asset_path": bp})
    LOG["steps"].append("compile %s: %s" % (tag, json.dumps(cr, ensure_ascii=False)[:300]))
    assert not cr.get("errors"), "%s 컴파일 에러: %s" % (tag, cr)


T3D_WS = '(MemberParent=/Script/SB2.SBDirectionalWindComponent,MemberName="WindStrength",bSelfContext=False)'

# ═══ ① v1 고아 정리 — v1이 만든 것만 ID/구조로 한정 (§25 킬필터 사고 방지) ═══
wn = graph_nodes(WBP, EG)
for nid in list(wn):
    ps = pm(wn, nid)
    is_orphan_ev = "ComponentBoundEvent" in nid
    is_orphan_vg = nid.startswith("K2Node_VariableGet") and "TargetWindComp" in ps
    if is_orphan_ev or is_orphan_vg:
        bpq("remove_node", {"asset_path": WBP, "graph_name": EG, "node_id": nid})
        LOG["steps"].append("고아 제거: %s" % nid)

# ═══ ② OnClicked 체인 5개 ═══
for i, (btn, label, val) in enumerate(VALUES):
    y = i * 400
    ev = add(WBP, EG, "ComponentBoundEvent", 0, y, component_name=btn, delegate_property_name="OnClicked")
    vg = add(WBP, EG, "VariableGet", 250, y + 150, variable_name="TargetWindComp")
    vs = add(WBP, EG, "VariableSet", 550, y, variable_name="WindStrength",
             target_class="SBDirectionalWindComponent")
    pins = node_pins(WBP, EG, vs)
    if "WindStrength" not in pins:  # §9 파손 복구
        pins = fix_varset(WBP, EG, vs, T3D_WS)
    assert "WindStrength" in pins, "%s Set WindStrength 핀 미생성: %s" % (btn, list(pins))
    ps_n = add(WBP, EG, "CallFunction", 900, y, function_name="PrintString", target_class="KismetSystemLibrary")
    bpq("set_pin_default", {"asset_path": WBP, "graph_name": EG, "node_id": vs,
                            "pin_name": "WindStrength", "value": val})
    bpq("set_pin_default", {"asset_path": WBP, "graph_name": EG, "node_id": ps_n,
                            "pin_name": "InString", "value": "DirWind Str = " + label})
    f = connect(WBP, EG, [
        {"source_node": ev, "source_pin": "then", "target_node": vs, "target_pin": "execute"},
        {"source_node": vg, "source_pin": "TargetWindComp", "target_node": vs, "target_pin": "self"},
        {"source_node": vs, "source_pin": "then", "target_node": ps_n, "target_pin": "execute"},
    ])
    assert f == 0, "%s OnClicked 체인 배선 실패" % btn
    LOG["steps"].append("%s 체인 OK (val=%s)" % (btn, val))

compile_bp(WBP, "WBP(최종)")
call("editor_query", "save_asset", {"asset_path": WBP})
LOG["steps"].append("WBP 저장 완료")

# ═══ ③ 레벨BP: BeginPlay 스플라이스 + CreateWidget 체인 ═══
nodes = graph_nodes(MAP_BP, EG)
assert SETSTR in nodes and BR in nodes, "레벨BP 기준 노드 미발견 — 재분석 필요"

bps = [nid for nid, n in nodes.items() if nid.startswith("K2Node_Event")
       and "BeginPlay" in json.dumps(n.get("title") or n.get("name") or n)]
assert len(bps) == 1, "BeginPlay 이벤트 특정 실패: %s" % bps
bp_ev = bps[0]
then_conn = pm(nodes, bp_ev)["then"].get("connected_to") or []
assert then_conn, "BeginPlay.then 미연결?"
head = then_conn[0]
head_node = head.get("node") or head.get("node_id")
head_pin = head.get("pin") or head.get("pin_name") or "execute"
LOG["steps"].append("BeginPlay=%s -> head=%s.%s" % (bp_ev, head_node, head_pin))

self_conn = pm(nodes, SETSTR)["self"].get("connected_to") or []
assert self_conn, "SETSTR.self 미연결 — 컴포넌트 소스 미확인"
comp_node = self_conn[0].get("node") or self_conn[0].get("node_id")
comp_pin = self_conn[0].get("pin") or self_conn[0].get("pin_name")
LOG["steps"].append("컴포넌트 소스 = %s.%s" % (comp_node, comp_pin))

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
setcur = add(MAP_BP, EG, "VariableSet", 500, 2400, variable_name="bShowMouseCursor",
             target_class="PlayerController")
cur_pins = node_pins(MAP_BP, EG, setcur)
if "bShowMouseCursor" not in cur_pins:
    cur_pins = fix_varset(MAP_BP, EG, setcur,
                          '(MemberParent=/Script/Engine.PlayerController,MemberName="bShowMouseCursor",bSelfContext=False)')
assert "bShowMouseCursor" in cur_pins, "bShowMouseCursor 셋 핀 미생성: %s" % list(cur_pins)
bpq("set_pin_default", {"asset_path": MAP_BP, "graph_name": EG, "node_id": setcur,
                        "pin_name": "bShowMouseCursor", "value": "true"})

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

# ═══ ④ 스텝퍼 게이트 ═══
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

# ═══ ⑤ 최종 검증 (§24) ═══
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

# 위젯 쪽 미연결 인풋 감사
wn2 = graph_nodes(WBP, EG)
ws_audit = []
for nid in wn2:
    if nid.startswith("K2Node_VariableSet"):
        p = pm(wn2, nid)
        if "WindStrength" in p:
            ws_audit.append({"node": nid, "self": bool(p["self"].get("connected_to")),
                             "val": p["WindStrength"].get("default_value"),
                             "exec_in": bool(p["execute"].get("connected_to"))})
LOG["steps"].append({"widget_audit": ws_audit})
assert len(ws_audit) == 5 and all(a["self"] and a["exec_in"] for a in ws_audit), "위젯 체인 감사 실패"
LOG["steps"].append("전체 빌드 완료 — 맵은 미저장(승호 판단), WBP는 디스크 저장됨")
