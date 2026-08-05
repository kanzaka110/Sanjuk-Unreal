# 윈드 강도 UI v5b — v5 이어서 (ButtonSlot padding 미지원 대응) — 우상단 이동 + 대형화 + Push/Pull (2026-08-05 승호 지시)
#   ① WindBtnRow 우상단 앵커 + 폰트 36/버튼 패딩 대형화
#   ② Btn_Push/Btn_Pull 추가
#   ③ 리팩토링: SelValue(강도)·WindSign(±1) 변수 + ApplyWind() 함수(Sign×Value 적용+표시)
#      값 버튼 = Set SelValue -> ApplyWind / Push·Pull = Set WindSign(1/-1) -> ApplyWind
#      기존 5체인의 vs/ps/vg 제거(내가 만든 것만, ev는 재사용)
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
EG = "EventGraph"
FN = "ApplyWind"
VALUES = {"Btn_W4": "4.0", "Btn_W6": "6.0", "Btn_W7_5": "7.5", "Btn_W9": "9.0", "Btn_W12": "12.0"}
FONT = 36
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


def add(graph: str, ntype: str, x: int, y: int, **kw) -> str:
    p = {"asset_path": WBP, "graph_name": graph, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return nid_of(bpq("add_node", p))


def connect(graph: str, cs: list) -> int:
    rc = bpq("connect_pins_bulk", {"asset_path": WBP, "graph_name": graph, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"graph": graph, "conns": fails})
    return len(fails)


def graph_nodes(graph: str) -> dict:
    g = bpq("get_graph_data", {"asset_path": WBP, "graph_name": graph})
    return {n["id"]: n for n in g["nodes"]}


def pm(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def node_pins(graph: str, nid: str) -> dict:
    det = bpq("get_node_details", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
    return {p.get("name"): p for p in (det.get("pins") or [])}


def spawn_varset(graph: str, x: int, y: int, var: str, target_class: str = None, t3d: str = None) -> str:
    kw = {"variable_name": var}
    if target_class:
        kw["target_class"] = target_class
    nid = add(graph, "VariableSet", x, y, **kw)
    pins = node_pins(graph, nid)
    if var not in pins and t3d:
        bpq("set_node_property", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                                  "property_name": "VariableReference", "value": t3d})
        bpq("refresh_node", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
        pins = node_pins(graph, nid)
    assert var in pins, "VariableSet %s 핀 미생성: %s" % (var, list(pins))
    return nid


def spawn_selfcall(graph: str, x: int, y: int, fname: str) -> str:
    """자기 함수 호출 — §23: FunctionReference 자기컨텍스트 명시 + refresh 후 연결"""
    nid = add(graph, "CallFunction", x, y, function_name=fname)
    bpq("set_node_property", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                              "property_name": "FunctionReference",
                              "value": '(MemberParent=None,MemberName="%s",bSelfContext=True)' % fname})
    bpq("refresh_node", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
    return nid


def setdef(graph: str, nid: str, pin: str, val: str) -> None:
    bpq("set_pin_default", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                            "pin_name": pin, "value": val})


T3D_WS = '(MemberParent=/Script/SB2.SBDirectionalWindComponent,MemberName="WindStrength",bSelfContext=False)'

# ═══ ① 레이아웃: 우상단 + 대형화 ═══
uiq("set_anchor_preset", {"asset_path": WBP, "widget_name": "WindBtnRow", "preset": "top_right"})
uiq("set_slot_property", {"asset_path": WBP, "widget_name": "WindBtnRow",
                          "position": {"x": -40, "y": 40}, "alignment": {"x": 1.0, "y": 0.0},
                          "auto_size": True})
LOG["steps"].append("WindBtnRow 우상단 앵커 OK")

# ═══ ② Push/Pull 버튼 추가 (v5에서 이미 추가됨 -> 존재 체크) ═══
tree_json = json.dumps(uiq("get_widget_tree", {"asset_path": WBP}))
for btn, label in (("Btn_Push", "Push"), ("Btn_Pull", "Pull")):
    if '"%s"' % btn in tree_json:
        LOG["steps"].append("%s 이미 존재 — 스킵" % btn)
        continue
    uiq("add_widget", {"asset_path": WBP, "widget_class": "Button", "widget_name": btn,
                       "parent_name": "WindBtnRow", "padding": {"left": 6, "top": 0, "right": 6, "bottom": 0},
                       "compile": False})
    uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": "Txt_" + btn,
                       "parent_name": btn, "compile": False})
    uiq("set_text", {"asset_path": WBP, "widget_name": "Txt_" + btn, "text": label,
                     "font_size": FONT, "justification": "Center", "compile": False})
    uiq("set_widget_is_variable", {"wbp_path": WBP, "widget_name": btn, "is_variable": True})
LOG["steps"].append("Push/Pull 버튼 추가 OK")

# 전체 대형화: 폰트 + 버튼 내부 패딩(ButtonSlot) + 버튼 간격
all_btns = list(VALUES) + ["Btn_Push", "Btn_Pull"]
for btn in all_btns:
    txt = "Txt_" + btn
    uiq("set_text", {"asset_path": WBP, "widget_name": txt, "font_size": FONT, "compile": False})
    try:  # ButtonSlot padding 은 Monolith 미지원 (v5 실측) — 실패해도 무해
        uiq("set_slot_property", {"asset_path": WBP, "widget_name": txt,
                                  "padding": {"left": 22, "top": 12, "right": 22, "bottom": 12}, "compile": False})
    except Exception as e:
        LOG["steps"].append("%s ButtonSlot padding 스킵: %s" % (txt, str(e)[:80]))
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": btn,
                              "padding": {"left": 8, "top": 0, "right": 8, "bottom": 0}, "compile": False})
LOG["steps"].append("대형화(폰트 %d + 패딩) OK" % FONT)

# ═══ ③ 변수 + ApplyWind 함수 ═══
gv = {v["name"] for v in bpq("get_variables", {"asset_path": WBP}).get("variables", [])}
if "SelValue" not in gv:
    uiq("add_widget_variable", {"wbp_path": WBP, "var_name": "SelValue", "var_type": "float",
                                "default_value": "4.0", "var_category": "Wind"})
if "WindSign" not in gv:
    uiq("add_widget_variable", {"wbp_path": WBP, "var_name": "WindSign", "var_type": "float",
                                "default_value": "1.0", "var_category": "Wind"})

bpq("add_function", {"asset_path": WBP, "name": FN, "category": "Wind"})
fn_nodes = graph_nodes(FN)
entry = next(nid for nid in fn_nodes if "FunctionEntry" in nid)
vg_t = add(FN, "VariableGet", 100, 250, variable_name="TargetWindComp")
vg_v = add(FN, "VariableGet", 100, 400, variable_name="SelValue")
vg_s = add(FN, "VariableGet", 100, 500, variable_name="WindSign")
mul = add(FN, "CallFunction", 350, 400, function_name="Multiply_DoubleDouble", target_class="KismetMathLibrary")
vs = spawn_varset(FN, 650, 0, "WindStrength", "SBDirectionalWindComponent", T3D_WS)
c2s = add(FN, "CallFunction", 950, 250, function_name="Conv_DoubleToString", target_class="KismetStringLibrary")
cat = add(FN, "CallFunction", 1200, 250, function_name="Concat_StrStr", target_class="KismetStringLibrary")
ps = add(FN, "CallFunction", 1500, 0, function_name="PrintString", target_class="KismetSystemLibrary")
setdef(FN, cat, "A", "DirWind Str = ")
f = connect(FN, [
    {"source_node": entry, "source_pin": "then", "target_node": vs, "target_pin": "execute"},
    {"source_node": vs, "source_pin": "then", "target_node": ps, "target_pin": "execute"},
    {"source_node": vg_t, "source_pin": "TargetWindComp", "target_node": vs, "target_pin": "self"},
    {"source_node": vg_v, "source_pin": "SelValue", "target_node": mul, "target_pin": "A"},
    {"source_node": vg_s, "source_pin": "WindSign", "target_node": mul, "target_pin": "B"},
    {"source_node": mul, "source_pin": "ReturnValue", "target_node": vs, "target_pin": "WindStrength"},
    {"source_node": vs, "source_pin": "Output_Get", "target_node": c2s, "target_pin": "InDouble"},
    {"source_node": c2s, "source_pin": "ReturnValue", "target_node": cat, "target_pin": "B"},
    {"source_node": cat, "source_pin": "ReturnValue", "target_node": ps, "target_pin": "InString"},
])
assert f == 0, "ApplyWind 배선 실패 — LOG.errors 확인"
cr = bpq("compile_blueprint", {"asset_path": WBP})
assert not cr.get("errors"), "ApplyWind 컴파일 에러: %s" % cr
LOG["steps"].append("ApplyWind 함수 OK (컴파일 클린)")

# ═══ ④ EventGraph 재배선 ═══
# 기존 체인 해체: ev(유지) -> vs(제거) -> ps(제거), vs.self <- vg(제거) — 전부 내가 만든 노드 (§25 구조 한정)
wn = graph_nodes(EG)
evs = {}   # 버튼명 -> ev 노드
kill = []
for nid, n in wn.items():
    if "ComponentBoundEvent" not in nid:
        continue
    title = json.dumps(n.get("title") or n.get("name") or n)
    btn = next((b for b in VALUES if b in title), None)
    ppins = pm(wn, nid)
    tc = ppins.get("then", {}).get("connected_to") or []
    if tc:
        s = tc[0]
        vs_old = s.rsplit(".", 1)[0] if isinstance(s, str) else (s.get("node") or s.get("node_id"))
        vsp = pm(wn, vs_old)
        if "WindStrength" in vsp:
            kill.append(vs_old)
            sc = vsp["self"].get("connected_to") or []
            if sc:
                s2 = sc[0]
                kill.append(s2.rsplit(".", 1)[0] if isinstance(s2, str) else (s2.get("node") or s2.get("node_id")))
            tc2 = vsp["then"].get("connected_to") or []
            if tc2:
                s3 = tc2[0]
                kill.append(s3.rsplit(".", 1)[0] if isinstance(s3, str) else (s3.get("node") or s3.get("node_id")))
    if btn:
        evs[btn] = nid
assert len(evs) == 5, "기존 바운드 이벤트 5개 특정 실패: %s" % evs
for nid in set(kill):
    bpq("remove_node", {"asset_path": WBP, "graph_name": EG, "node_id": nid})
LOG["steps"].append("구 체인 노드 %d개 제거, ev 5개 재사용" % len(set(kill)))

# 값 버튼 5개: ev -> Set SelValue(val) -> ApplyWind
for i, (btn, val) in enumerate(VALUES.items()):
    y = i * 350
    ssel = spawn_varset(EG, 400, y, "SelValue", t3d='(MemberName="SelValue",bSelfContext=True)')
    ap = spawn_selfcall(EG, 750, y, FN)
    setdef(EG, ssel, "SelValue", val)
    f = connect(EG, [
        {"source_node": evs[btn], "source_pin": "then", "target_node": ssel, "target_pin": "execute"},
        {"source_node": ssel, "source_pin": "then", "target_node": ap, "target_pin": "execute"},
    ])
    assert f == 0, "%s 체인 배선 실패" % btn
LOG["steps"].append("값 버튼 5체인 OK")

# Push/Pull: ev -> Set WindSign(±1) -> ApplyWind
for i, (btn, sign) in enumerate((("Btn_Push", "1.0"), ("Btn_Pull", "-1.0"))):
    y = 1750 + i * 350
    ev = add(EG, "ComponentBoundEvent", 0, y, component_name=btn, delegate_property_name="OnClicked")
    ssign = spawn_varset(EG, 400, y, "WindSign", t3d='(MemberName="WindSign",bSelfContext=True)')
    ap = spawn_selfcall(EG, 750, y, FN)
    setdef(EG, ssign, "WindSign", sign)
    f = connect(EG, [
        {"source_node": ev, "source_pin": "then", "target_node": ssign, "target_pin": "execute"},
        {"source_node": ssign, "source_pin": "then", "target_node": ap, "target_pin": "execute"},
    ])
    assert f == 0, "%s 체인 배선 실패" % btn
LOG["steps"].append("Push/Pull 2체인 OK")

cr = bpq("compile_blueprint", {"asset_path": WBP})
LOG["steps"].append("compile 최종: %s" % json.dumps(cr, ensure_ascii=False)[:250])
assert not cr.get("errors"), "최종 컴파일 에러: %s" % cr
call("editor_query", "save_asset", {"asset_path": WBP})

# ═══ ⑤ 검증 ═══
wn2 = graph_nodes(EG)
audit = []
for nid in wn2:
    if "ComponentBoundEvent" in nid:
        tc = pm(wn2, nid).get("then", {}).get("connected_to")
        audit.append({"ev": nid, "wired": bool(tc)})
LOG["steps"].append({"ev_audit": audit})
assert len(audit) == 7 and all(a["wired"] for a in audit), "이벤트 7개 배선 검증 실패"
fn2 = graph_nodes(FN)
vsp = pm(fn2, vs)
LOG["steps"].append({"apply_verify": {
    "WindStrength<-mul": bool(vsp["WindStrength"].get("connected_to")),
    "self<-target": bool(vsp["self"].get("connected_to")),
    "display<-Output_Get": bool(vsp["Output_Get"].get("connected_to")),
}})
LOG["steps"].append("v5 완료 — WBP 저장됨 (레벨BP 무변경)")
