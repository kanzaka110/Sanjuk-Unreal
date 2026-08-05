# 윈드 강도 UI v11 — 난기류 6단계 프리셋 (2026-08-05, Confluence 「난기류의 세기」 표 확정)
#   기존 터브 4줄(Off/Turb/Spd/Size, 버튼 16개) 철거 -> 한 줄 6버튼 프리셋
#   OFF(T=0) / Extreme(0.2,50,1) / Strong(0.4,100,2.5) / Moderate(0.6,200,5) / Light(0.8,500,10) / Mild(1.0,1000,30)
#   함수 ApplyTurbSet(Label,Turb,Size,Speed) = 3값 일괄 적용 + "Turb Stage = <Label>" 표시
#   OFF 는 기존 ApplyTurb(0.0) 재사용 (Size/Speed 보존)
#   철거 원칙(§25): Btn_T* 바운드 이벤트만 ID 추적 제거 (강도=Btn_W*, Push/Pull 무접촉)
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
EG = "EventGraph"
FONT = 54
LBL_FONT = 40
OLD_ROWS = ["WindRowTurbOff", "WindRowTurb", "WindRowTurbSpd", "WindRowTurbSize"]
PRESETS = [  # (버튼, 라벨, Turb, Size, Speed) — OFF 는 별도
    # 단계명 = 질감 네이밍 (승호 채택 0805). 표 세기 순서 매핑: Extreme->Chaotic ... Mild->Ripple
    ("Btn_TbChaotic", "Chaotic", "0.2", "50", "1"),
    ("Btn_TbGusty", "Gusty", "0.4", "100", "2.5"),
    ("Btn_TbFlutter", "Flutter", "0.6", "200", "5"),
    ("Btn_TbSway", "Sway", "0.8", "500", "10"),
    ("Btn_TbRipple", "Ripple", "1.0", "1000", "30"),
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


def node_pins(graph: str, nid: str) -> dict:
    det = bpq("get_node_details", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
    return {p.get("name"): p for p in (det.get("pins") or [])}


def spawn_varset(graph: str, x: int, y: int, var: str) -> str:
    t3d = '(MemberParent=/Script/SB2.SBDirectionalWindComponent,MemberName="%s",bSelfContext=False)' % var
    nid = add(graph, "VariableSet", x, y, variable_name=var, target_class="SBDirectionalWindComponent")
    pins = node_pins(graph, nid)
    if var not in pins:
        bpq("set_node_property", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                                  "property_name": "VariableReference", "value": t3d})
        bpq("refresh_node", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
        pins = node_pins(graph, nid)
    assert var in pins, "VariableSet %s 핀 미생성: %s" % (var, list(pins))
    return nid


def spawn_selfcall(graph: str, x: int, y: int, fname: str) -> str:
    nid = add(graph, "CallFunction", x, y, function_name=fname)
    bpq("set_node_property", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                              "property_name": "FunctionReference",
                              "value": '(MemberParent=None,MemberName="%s",bSelfContext=True)' % fname})
    bpq("refresh_node", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
    return nid


def setdef(graph: str, nid: str, pin: str, val: str) -> None:
    bpq("set_pin_default", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                            "pin_name": pin, "value": val})


# ═══ ① 구 터브 이벤트 체인 철거 (Btn_T* 만) ═══
wn = graph_nodes(EG)


def pm(nid):
    return {p["name"]: p for p in wn[nid].get("pins", [])}


removed = 0
for nid, n in list(wn.items()):
    if "ComponentBoundEvent" not in nid:
        continue
    title = json.dumps(n.get("title") or n.get("name") or n)
    if "Btn_T" not in title:
        continue
    tc = pm(nid).get("then", {}).get("connected_to") or []
    if tc:
        s = tc[0]
        callee = s.rsplit(".", 1)[0] if isinstance(s, str) else (s.get("node") or s.get("node_id"))
        bpq("remove_node", {"asset_path": WBP, "graph_name": EG, "node_id": callee})
        removed += 1
    bpq("remove_node", {"asset_path": WBP, "graph_name": EG, "node_id": nid})
    removed += 1
LOG["steps"].append("구 터브 체인 노드 %d개 제거" % removed)

# ═══ ② 구 UI 4줄 철거 ═══
for row in OLD_ROWS:
    uiq("remove_widget", {"asset_path": WBP, "widget_name": row})
LOG["steps"].append("구 터브 4줄 제거 OK")

# ═══ ③ ApplyTurbSet(Label,Turb,Size,Speed) ═══
bpq("add_function", {"asset_path": WBP, "name": "ApplyTurbSet", "category": "Wind"})
bpq("set_function_params", {"asset_path": WBP, "function_name": "ApplyTurbSet",
                            "inputs": [{"name": "Label", "type": "string"}, {"name": "Turb", "type": "float"},
                                       {"name": "Size", "type": "float"}, {"name": "Speed", "type": "float"}]})
FN = "ApplyTurbSet"
fn_nodes = graph_nodes(FN)
entry = next(nid for nid in fn_nodes if "FunctionEntry" in nid)
vg_t = add(FN, "VariableGet", 100, 300, variable_name="TargetWindComp")
vs1 = spawn_varset(FN, 400, 0, "Turbulence")
vs2 = spawn_varset(FN, 700, 0, "TurbulenceSize")
vs3 = spawn_varset(FN, 1000, 0, "TurbulenceSpeed")
cat = add(FN, "CallFunction", 1300, 250, function_name="Concat_StrStr", target_class="KismetStringLibrary")
ps = add(FN, "CallFunction", 1600, 0, function_name="PrintString", target_class="KismetSystemLibrary")
setdef(FN, cat, "A", "Turb Stage = ")
f = connect(FN, [
    {"source_node": entry, "source_pin": "then", "target_node": vs1, "target_pin": "execute"},
    {"source_node": vs1, "source_pin": "then", "target_node": vs2, "target_pin": "execute"},
    {"source_node": vs2, "source_pin": "then", "target_node": vs3, "target_pin": "execute"},
    {"source_node": vs3, "source_pin": "then", "target_node": ps, "target_pin": "execute"},
    {"source_node": entry, "source_pin": "Turb", "target_node": vs1, "target_pin": "Turbulence"},
    {"source_node": entry, "source_pin": "Size", "target_node": vs2, "target_pin": "TurbulenceSize"},
    {"source_node": entry, "source_pin": "Speed", "target_node": vs3, "target_pin": "TurbulenceSpeed"},
    {"source_node": vg_t, "source_pin": "TargetWindComp", "target_node": vs1, "target_pin": "self"},
    {"source_node": vg_t, "source_pin": "TargetWindComp", "target_node": vs2, "target_pin": "self"},
    {"source_node": vg_t, "source_pin": "TargetWindComp", "target_node": vs3, "target_pin": "self"},
    {"source_node": entry, "source_pin": "Label", "target_node": cat, "target_pin": "B"},
    {"source_node": cat, "source_pin": "ReturnValue", "target_node": ps, "target_pin": "InString"},
])
assert f == 0, "ApplyTurbSet 배선 실패 — LOG.errors 확인"
cr = bpq("compile_blueprint", {"asset_path": WBP})
assert not cr.get("errors"), "ApplyTurbSet 컴파일 에러: %s" % cr
LOG["steps"].append("ApplyTurbSet OK (컴파일 클린)")

# ═══ ④ 새 줄: Turb  OFF|Extreme|Strong|Moderate|Light|Mild ═══
uiq("add_widget", {"asset_path": WBP, "widget_class": "HorizontalBox", "widget_name": "WindRowTurbStage",
                   "parent_name": "WindBtnCol", "compile": False})
uiq("set_slot_property", {"asset_path": WBP, "widget_name": "WindRowTurbStage", "h_align": "Right",
                          "padding": {"left": 0, "top": 12, "right": 0, "bottom": 0}, "compile": False})
uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": "Lbl_TurbStage",
                   "parent_name": "WindRowTurbStage", "compile": False})
uiq("set_text", {"asset_path": WBP, "widget_name": "Lbl_TurbStage", "text": "Turb",
                 "font_size": LBL_FONT, "compile": False})
uiq("set_slot_property", {"asset_path": WBP, "widget_name": "Lbl_TurbStage", "v_align": "Center",
                          "padding": {"left": 0, "top": 0, "right": 14, "bottom": 0}, "compile": False})
all_btns = [("Btn_TbOff", "OFF")] + [(b, l) for b, l, _t, _z, _s in PRESETS]
for btn, label in all_btns:
    uiq("add_widget", {"asset_path": WBP, "widget_class": "Button", "widget_name": btn,
                       "parent_name": "WindRowTurbStage", "compile": False})
    uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": "Txt_" + btn,
                       "parent_name": btn, "compile": False})
    uiq("set_text", {"asset_path": WBP, "widget_name": "Txt_" + btn, "text": label,
                     "font_size": FONT, "justification": "Center", "compile": False})
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": btn,
                              "padding": {"left": 10, "top": 0, "right": 10, "bottom": 0}, "compile": False})
    uiq("set_widget_is_variable", {"wbp_path": WBP, "widget_name": btn, "is_variable": True})
LOG["steps"].append("WindRowTurbStage 6버튼 OK")

# ═══ ⑤ 이벤트 배선 ═══
# OFF -> ApplyTurb(0.0) (기존 함수 재사용, Size/Speed 보존)
ev = add(EG, "ComponentBoundEvent", 0, 7600, component_name="Btn_TbOff", delegate_property_name="OnClicked")
ap = spawn_selfcall(EG, 400, 7600, "ApplyTurb")
setdef(EG, ap, "Amount", "0.0")
f = connect(EG, [{"source_node": ev, "source_pin": "then", "target_node": ap, "target_pin": "execute"}])
assert f == 0, "OFF 체인 배선 실패"
# 프리셋 5개 -> ApplyTurbSet
for i, (btn, label, t, z, s) in enumerate(PRESETS):
    y = 7900 + i * 300
    ev = add(EG, "ComponentBoundEvent", 0, y, component_name=btn, delegate_property_name="OnClicked")
    ap = spawn_selfcall(EG, 400, y, "ApplyTurbSet")
    for pin, val in (("Label", label), ("Turb", t), ("Size", z), ("Speed", s)):
        setdef(EG, ap, pin, val)
    f = connect(EG, [{"source_node": ev, "source_pin": "then", "target_node": ap, "target_pin": "execute"}])
    assert f == 0, "%s 체인 배선 실패" % btn
LOG["steps"].append("프리셋 6체인 OK")

cr = bpq("compile_blueprint", {"asset_path": WBP})
LOG["steps"].append("compile 최종: %s" % json.dumps(cr, ensure_ascii=False)[:200])
assert not cr.get("errors"), "최종 컴파일 에러: %s" % cr
call("editor_query", "save_asset", {"asset_path": WBP})

# ═══ ⑥ 검증 ═══
wn2 = graph_nodes(EG)
evs = [nid for nid in wn2 if "ComponentBoundEvent" in nid]
wired = all(bool({p["name"]: p for p in wn2[nid].get("pins", [])}.get("then", {}).get("connected_to")) for nid in evs)
tree = json.dumps(uiq("get_widget_tree", {"asset_path": WBP}))
checks = {"ev_count": len(evs), "all_wired": wired, "btn_count": tree.count('"class": "Button"'),
          "old_rows_gone": all(('"%s"' % r) not in tree for r in OLD_ROWS),
          "new_row": '"WindRowTurbStage"' in tree}
LOG["steps"].append({"verify": checks})
assert checks["ev_count"] == 13 and wired and checks["btn_count"] == 13 and checks["old_rows_gone"] and checks["new_row"], \
    "검증 실패: %s" % checks
LOG["steps"].append("v11 완료 — WBP 저장됨")
