# 윈드 강도 UI v14 — GlobalWind 섹션 (2026-08-05 승호 지시)
#   최상단: GlobalWind 헤더 / TEST: Off·Random / 단계: Mild~Extreme (글로벌 규격 1.2/2.4/3.6/4.8/6.0)
#   타깃 = SBGlobalWindVolume (SBWindVolume, 액터 직접 프로퍼티 WindStrength/WindDirection — 0729 실측)
#   Off = Str 0 / Random = 원클릭 랜덤 (Str 1.2~6.0 + 방향 yaw 0~360)
#   InitWind에 GlobalVolume 입력 추가(set_function_params 추가전용) + 레벨BP 리터럴 주입
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
MAP_BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
EG = "EventGraph"
FONT = 54
LBL_FONT = 40
SEQ1 = "K2Node_ExecutionSequence_1"
GVOL = ("/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map.SBWind_Weight_TEST01_Map"
        ":PersistentLevel.SBWindVolume_UAID_30560F6BCAE5D3F202_1767786249")
T3D_GS = '(MemberParent=/Script/SB2.SBWindVolume,MemberName="WindStrength",bSelfContext=False)'
T3D_GD = '(MemberParent=/Script/SB2.SBWindVolume,MemberName="WindDirection",bSelfContext=False)'
STAGES = [  # (버튼, 라벨, 값) — 글로벌 규격 (Confluence 1692467785)
    ("Btn_GMild", "Mild", "1.2"), ("Btn_GLight", "Light", "2.4"), ("Btn_GModerate", "Moderate", "3.6"),
    ("Btn_GStrong", "Strong", "4.8"), ("Btn_GExtreme", "Extreme", "6.0"),
]
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


def pmn(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def node_pins(bp: str, graph: str, nid: str) -> dict:
    det = bpq("get_node_details", {"asset_path": bp, "graph_name": graph, "node_id": nid})
    return {p.get("name"): p for p in (det.get("pins") or [])}


def spawn_extset(bp: str, graph: str, x: int, y: int, var: str, tclass: str, t3d: str) -> str:
    nid = add(bp, graph, "VariableSet", x, y, variable_name=var, target_class=tclass)
    pins = node_pins(bp, graph, nid)
    if var not in pins:
        bpq("set_node_property", {"asset_path": bp, "graph_name": graph, "node_id": nid,
                                  "property_name": "VariableReference", "value": t3d})
        bpq("refresh_node", {"asset_path": bp, "graph_name": graph, "node_id": nid})
        pins = node_pins(bp, graph, nid)
    assert var in pins, "VariableSet %s 핀 미생성: %s" % (var, list(pins))
    return nid


def spawn_selfcall(graph: str, x: int, y: int, fname: str) -> str:
    nid = add(WBP, graph, "CallFunction", x, y, function_name=fname)
    bpq("set_node_property", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                              "property_name": "FunctionReference",
                              "value": '(MemberParent=None,MemberName="%s",bSelfContext=True)' % fname})
    bpq("refresh_node", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
    return nid


def setdef(bp: str, graph: str, nid: str, pin: str, val: str) -> None:
    bpq("set_pin_default", {"asset_path": bp, "graph_name": graph, "node_id": nid,
                            "pin_name": pin, "value": val})


# ═══ ① 위젯 변수 + InitWind 확장 ═══
gv = {v["name"] for v in bpq("get_variables", {"asset_path": WBP}).get("variables", [])}
if "TargetGlobalWind" not in gv:
    uiq("add_widget_variable", {"wbp_path": WBP, "var_name": "TargetGlobalWind",
                                "var_type": "object:SBWindVolume", "var_category": "Wind"})
bpq("set_function_params", {"asset_path": WBP, "function_name": "InitWind",
                            "inputs": [{"name": "GlobalVolume", "type": "object:SBWindVolume"}]})
fn = graph_nodes(WBP, "InitWind")
entry = next(nid for nid in fn if "FunctionEntry" in nid)
vs_t = next(nid for nid in fn if nid.startswith("K2Node_VariableSet") and "TargetWindComp" in pmn(fn, nid))
vs_g = add(WBP, "InitWind", "VariableSet", 700, 0, variable_name="TargetGlobalWind")
pins = node_pins(WBP, "InitWind", vs_g)
if "TargetGlobalWind" not in pins:
    bpq("set_node_property", {"asset_path": WBP, "graph_name": "InitWind", "node_id": vs_g,
                              "property_name": "VariableReference",
                              "value": '(MemberName="TargetGlobalWind",bSelfContext=True)'})
    bpq("refresh_node", {"asset_path": WBP, "graph_name": "InitWind", "node_id": vs_g})
    pins = node_pins(WBP, "InitWind", vs_g)
assert "TargetGlobalWind" in pins, "TargetGlobalWind 셋 핀 미생성"
f = connect(WBP, "InitWind", [
    {"source_node": vs_t, "source_pin": "then", "target_node": vs_g, "target_pin": "execute"},
    {"source_node": entry, "source_pin": "GlobalVolume", "target_node": vs_g, "target_pin": "TargetGlobalWind"},
])
assert f == 0, "InitWind 확장 배선 실패"
LOG["steps"].append("InitWind + GlobalVolume 입력 OK")

# ═══ ② ApplyGlobalWind(Label, Strength) ═══
bpq("add_function", {"asset_path": WBP, "name": "ApplyGlobalWind", "category": "Wind"})
bpq("set_function_params", {"asset_path": WBP, "function_name": "ApplyGlobalWind",
                            "inputs": [{"name": "Label", "type": "string"}, {"name": "Strength", "type": "float"}]})
FN = "ApplyGlobalWind"
fng = graph_nodes(WBP, FN)
entry_g = next(nid for nid in fng if "FunctionEntry" in nid)
vg = add(WBP, FN, "VariableGet", 100, 250, variable_name="TargetGlobalWind")
vs = spawn_extset(WBP, FN, 450, 0, "WindStrength", "SBWindVolume", T3D_GS)
cat = add(WBP, FN, "CallFunction", 800, 250, function_name="Concat_StrStr", target_class="KismetStringLibrary")
ps = add(WBP, FN, "CallFunction", 1100, 0, function_name="PrintString", target_class="KismetSystemLibrary")
setdef(WBP, FN, cat, "A", "GlobalWind = ")
f = connect(WBP, FN, [
    {"source_node": entry_g, "source_pin": "then", "target_node": vs, "target_pin": "execute"},
    {"source_node": vs, "source_pin": "then", "target_node": ps, "target_pin": "execute"},
    {"source_node": entry_g, "source_pin": "Strength", "target_node": vs, "target_pin": "WindStrength"},
    {"source_node": vg, "source_pin": "TargetGlobalWind", "target_node": vs, "target_pin": "self"},
    {"source_node": entry_g, "source_pin": "Label", "target_node": cat, "target_pin": "B"},
    {"source_node": cat, "source_pin": "ReturnValue", "target_node": ps, "target_pin": "InString"},
])
assert f == 0, "ApplyGlobalWind 배선 실패"
LOG["steps"].append("ApplyGlobalWind OK")

# ═══ ③ ApplyGlobalRandom() — Str 1.2~6.0 + 방향 yaw 0~360 ═══
bpq("add_function", {"asset_path": WBP, "name": "ApplyGlobalRandom", "category": "Wind"})
FN = "ApplyGlobalRandom"
fnr = graph_nodes(WBP, FN)
entry_r = next(nid for nid in fnr if "FunctionEntry" in nid)
vg_r = add(WBP, FN, "VariableGet", 100, 300, variable_name="TargetGlobalWind")
rf1 = add(WBP, FN, "CallFunction", 100, 450, function_name="RandomFloatInRange", target_class="KismetMathLibrary")
rf2 = add(WBP, FN, "CallFunction", 100, 600, function_name="RandomFloatInRange", target_class="KismetMathLibrary")
mkr = add(WBP, FN, "CallFunction", 400, 600, function_name="MakeRotator", target_class="KismetMathLibrary")
fwd = add(WBP, FN, "CallFunction", 650, 600, function_name="GetForwardVector", target_class="KismetMathLibrary")
vsS = spawn_extset(WBP, FN, 450, 0, "WindStrength", "SBWindVolume", T3D_GS)
vsD = spawn_extset(WBP, FN, 800, 0, "WindDirection", "SBWindVolume", T3D_GD)
c2s = add(WBP, FN, "CallFunction", 1100, 300, function_name="Conv_DoubleToString", target_class="KismetStringLibrary")
cat_r = add(WBP, FN, "CallFunction", 1350, 300, function_name="Concat_StrStr", target_class="KismetStringLibrary")
ps_r = add(WBP, FN, "CallFunction", 1650, 0, function_name="PrintString", target_class="KismetSystemLibrary")
setdef(WBP, FN, rf1, "Min", "1.2")
setdef(WBP, FN, rf1, "Max", "6.0")
setdef(WBP, FN, rf2, "Min", "0.0")
setdef(WBP, FN, rf2, "Max", "360.0")
setdef(WBP, FN, cat_r, "A", "GlobalWind Rnd = ")
f = connect(WBP, FN, [
    {"source_node": entry_r, "source_pin": "then", "target_node": vsS, "target_pin": "execute"},
    {"source_node": vsS, "source_pin": "then", "target_node": vsD, "target_pin": "execute"},
    {"source_node": vsD, "source_pin": "then", "target_node": ps_r, "target_pin": "execute"},
    {"source_node": rf1, "source_pin": "ReturnValue", "target_node": vsS, "target_pin": "WindStrength"},
    {"source_node": rf2, "source_pin": "ReturnValue", "target_node": mkr, "target_pin": "Yaw"},
    {"source_node": mkr, "source_pin": "ReturnValue", "target_node": fwd, "target_pin": "InRot"},
    {"source_node": fwd, "source_pin": "ReturnValue", "target_node": vsD, "target_pin": "WindDirection"},
    {"source_node": vg_r, "source_pin": "TargetGlobalWind", "target_node": vsS, "target_pin": "self"},
    {"source_node": vg_r, "source_pin": "TargetGlobalWind", "target_node": vsD, "target_pin": "self"},
    {"source_node": vsS, "source_pin": "Output_Get", "target_node": c2s, "target_pin": "InDouble"},
    {"source_node": c2s, "source_pin": "ReturnValue", "target_node": cat_r, "target_pin": "B"},
    {"source_node": cat_r, "source_pin": "ReturnValue", "target_node": ps_r, "target_pin": "InString"},
])
assert f == 0, "ApplyGlobalRandom 배선 실패 — LOG.errors 확인"
cr = bpq("compile_blueprint", {"asset_path": WBP})
assert not cr.get("errors"), "함수 컴파일 에러: %s" % cr
LOG["steps"].append("ApplyGlobalRandom OK (컴파일 클린)")

# ═══ ④ UI: 헤더 + TEST줄 + 단계줄 ═══
uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": "Hdr_GlobalWind",
                   "parent_name": "WindBtnCol", "compile": False})
uiq("set_text", {"asset_path": WBP, "widget_name": "Hdr_GlobalWind", "text": "GlobalWind",
                 "font_size": 44, "text_color": "#FFD34D", "compile": False})
rows = [("WindRowGTest", "TEST", [("Btn_GOff", "Off"), ("Btn_GRnd", "Random")]),
        ("WindRowGStage", None, [(b, l) for b, l, _v in STAGES])]
for row, lbl_text, btns in rows:
    uiq("add_widget", {"asset_path": WBP, "widget_class": "HorizontalBox", "widget_name": row,
                       "parent_name": "WindBtnCol", "compile": False})
    if lbl_text:
        lbl = "Lbl_" + row
        uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": lbl,
                           "parent_name": row, "compile": False})
        uiq("set_text", {"asset_path": WBP, "widget_name": lbl, "text": lbl_text,
                         "font_size": LBL_FONT, "compile": False})
        uiq("set_slot_property", {"asset_path": WBP, "widget_name": lbl, "v_align": "Center",
                                  "padding": {"left": 0, "top": 0, "right": 14, "bottom": 0}, "compile": False})
    for btn, label in btns:
        uiq("add_widget", {"asset_path": WBP, "widget_class": "Button", "widget_name": btn,
                           "parent_name": row, "compile": False})
        uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": "Txt_" + btn,
                           "parent_name": btn, "compile": False})
        uiq("set_text", {"asset_path": WBP, "widget_name": "Txt_" + btn, "text": label,
                         "font_size": FONT, "justification": "Center", "compile": False})
        uiq("set_slot_property", {"asset_path": WBP, "widget_name": btn,
                                  "padding": {"left": 10, "top": 0, "right": 10, "bottom": 0}, "compile": False})
        uiq("set_widget_is_variable", {"wbp_path": WBP, "widget_name": btn, "is_variable": True})
LOG["steps"].append("GlobalWind UI OK")

# 순서: [HdrG, GTest, GStage, HdrWS, Top, Num, HdrTb, TurbStage]
for w in ("Hdr_WindStrength", "WindRowTop", "WindRowNum", "Hdr_Turbulence", "WindRowTurbStage"):
    uiq("move_widget", {"asset_path": WBP, "widget_name": w, "new_parent_name": "WindBtnCol"})
for row in ("WindRowGTest", "WindRowGStage", "WindRowTop", "WindRowNum", "WindRowTurbStage"):
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": row, "h_align": "Right",
                              "padding": {"left": 0, "top": 8, "right": 0, "bottom": 0}, "compile": False})
for hdr, top in (("Hdr_GlobalWind", 0), ("Hdr_WindStrength", 24), ("Hdr_Turbulence", 24)):
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": hdr, "h_align": "Right",
                              "padding": {"left": 0, "top": top, "right": 4, "bottom": 2}, "compile": False})
LOG["steps"].append("순서 재배치 OK")

# ═══ ⑤ 바운드 이벤트 7개 ═══
y = 9600
ev = add(WBP, EG, "ComponentBoundEvent", 0, y, component_name="Btn_GOff", delegate_property_name="OnClicked")
ap = spawn_selfcall(EG, 400, y, "ApplyGlobalWind")
setdef(WBP, EG, ap, "Label", "OFF")
setdef(WBP, EG, ap, "Strength", "0.0")
f = connect(WBP, EG, [{"source_node": ev, "source_pin": "then", "target_node": ap, "target_pin": "execute"}])
assert f == 0, "GOff 배선 실패"
y += 300
ev = add(WBP, EG, "ComponentBoundEvent", 0, y, component_name="Btn_GRnd", delegate_property_name="OnClicked")
ap = spawn_selfcall(EG, 400, y, "ApplyGlobalRandom")
f = connect(WBP, EG, [{"source_node": ev, "source_pin": "then", "target_node": ap, "target_pin": "execute"}])
assert f == 0, "GRnd 배선 실패"
for btn, label, val in STAGES:
    y += 300
    ev = add(WBP, EG, "ComponentBoundEvent", 0, y, component_name=btn, delegate_property_name="OnClicked")
    ap = spawn_selfcall(EG, 400, y, "ApplyGlobalWind")
    setdef(WBP, EG, ap, "Label", label)
    setdef(WBP, EG, ap, "Strength", val)
    f = connect(WBP, EG, [{"source_node": ev, "source_pin": "then", "target_node": ap, "target_pin": "execute"}])
    assert f == 0, "%s 배선 실패" % btn
LOG["steps"].append("글로벌 7체인 OK")

cr = bpq("compile_blueprint", {"asset_path": WBP})
assert not cr.get("errors"), "위젯 최종 컴파일 에러: %s" % cr
call("editor_query", "save_asset", {"asset_path": WBP})
LOG["steps"].append("WBP 컴파일+저장 OK")

# ═══ ⑥ 레벨BP: 글로벌 볼륨 리터럴 -> InitWind.GlobalVolume ═══
nodes = graph_nodes(MAP_BP, EG)


def follow(nid, pin):
    c = pmn(nodes, nid)[pin].get("connected_to") or []
    assert c, "%s.%s 미연결" % (nid, pin)
    s = c[0]
    return (tuple(s.rsplit(".", 1)) if isinstance(s, str)
            else (s.get("node") or s.get("node_id"), s.get("pin") or s.get("pin_name")))


crt, _ = follow(SEQ1, "then_4")
cast, _ = follow(crt, "then")
init, _ = follow(cast, "then")
# 새 핀 노출 전 기존 연결 스냅샷
before = {p: (pmn(nodes, init)[p].get("connected_to") or None) for p in pmn(nodes, init)}
bpq("refresh_node", {"asset_path": MAP_BP, "graph_name": EG, "node_id": init})
init_pins = node_pins(MAP_BP, EG, init)
assert "GlobalVolume" in init_pins, "InitWind 새 핀 미노출: %s" % list(init_pins)
lit = add(MAP_BP, EG, "K2Node_Literal", -1250, 2850)
bpq("set_node_property", {"asset_path": MAP_BP, "graph_name": EG, "node_id": lit,
                          "property_name": "ObjectRef", "value": GVOL})
bpq("refresh_node", {"asset_path": MAP_BP, "graph_name": EG, "node_id": lit})
lit_pins = node_pins(MAP_BP, EG, lit)
out_pin = next(p for p in lit_pins if lit_pins[p].get("direction") != "input" and p not in ("execute", "then"))
f = connect(MAP_BP, EG, [{"source_node": lit, "source_pin": out_pin, "target_node": init, "target_pin": "GlobalVolume"}])
assert f == 0, "리터럴 배선 실패"
# refresh로 끊긴 연결 복구
nodes = graph_nodes(MAP_BP, EG)
ip = pmn(nodes, init)
relink = []
for pin, conn in before.items():
    if conn and pin in ip and not (ip[pin].get("connected_to") or []):
        s = conn[0]
        src_n, src_p = (tuple(s.rsplit(".", 1)) if isinstance(s, str)
                        else (s.get("node") or s.get("node_id"), s.get("pin") or s.get("pin_name")))
        if ip[pin].get("direction") == "input" or pin in ("execute", "self", "Comp"):
            relink.append({"source_node": src_n, "source_pin": src_p, "target_node": init, "target_pin": pin})
        else:
            relink.append({"source_node": init, "source_pin": pin, "target_node": src_n, "target_pin": src_p})
if relink:
    f = connect(MAP_BP, EG, relink)
    LOG["steps"].append({"refresh 복구 재배선": relink, "fail": f})
cr = bpq("compile_blueprint", {"asset_path": MAP_BP})
assert not cr.get("errors"), "레벨BP 컴파일 에러: %s" % cr
LOG["steps"].append("레벨BP OK (컴파일 클린)")

# ═══ ⑦ 검증 ═══
nodes = graph_nodes(MAP_BP, EG)
ip = pmn(nodes, init)
lvl_checks = {p: bool(ip[p].get("connected_to")) for p in ("execute", "then", "self", "Comp", "GlobalVolume")}
wn = graph_nodes(WBP, EG)
evn = sum(1 for n in wn if "ComponentBoundEvent" in n)
wired = all(bool({p["name"]: p for p in wn[n].get("pins", [])}.get("then", {}).get("connected_to"))
            for n in wn if "ComponentBoundEvent" in n)
LOG["steps"].append({"verify": {"init_pins": lvl_checks, "ev_count": evn, "all_wired": wired}})
assert all(lvl_checks.values()) and evn == 20 and wired, "검증 실패"
LOG["steps"].append("v14 완료 — WBP 저장됨, 맵 미저장")
