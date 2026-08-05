# 윈드 강도 UI v9 — Turbulence 3옵션 × 5단계 (2026-08-05 승호 "옵션은 3개")
#   실측: Turbulence 0.5 / TurbulenceSpeed 1.0 / TurbulenceSize 100 (Actor8 WindComponent)
#   기존 WindRowTurb(0.2~1.0) 유지 + 줄 라벨(Turb/Spd/Size) + 신규 2줄:
#     Spd  = 0.5/1/2/4/8      (기본 1 중심 배수, ⚠ 가설)
#     Size = 25/50/100/200/400 (기본 100 중심 배수, ⚠ 가설)
#   함수 ApplyTurbSpeed/ApplyTurbSize (ApplyTurb 동형) + 바운드 이벤트 10개
#   기존 터브 줄 라벨은 add 후 move_widget 재부모화(같은 부모 재append)로 맨 앞 배치 시도 — 실패 시 스킵
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
EG = "EventGraph"
FONT = 54
LBL_FONT = 40
ROWS = [
    # (row_name, 라벨위젯, 라벨텍스트, 함수명, 외부프로퍼티, 프린트 접두어, [(버튼, 라벨=값str)])
    ("WindRowTurbSpd", "Lbl_TurbSpd", "Spd", "ApplyTurbSpeed", "TurbulenceSpeed", "DirWind TurbSpd = ",
     [("Btn_TS05", "0.5"), ("Btn_TS1", "1"), ("Btn_TS2", "2"), ("Btn_TS4", "4"), ("Btn_TS8", "8")]),
    ("WindRowTurbSize", "Lbl_TurbSize", "Size", "ApplyTurbSize", "TurbulenceSize", "DirWind TurbSize = ",
     [("Btn_TZ25", "25"), ("Btn_TZ50", "50"), ("Btn_TZ100", "100"), ("Btn_TZ200", "200"), ("Btn_TZ400", "400")]),
]
TURB_BTNS = ["Btn_T02", "Btn_T04", "Btn_T06", "Btn_T08", "Btn_T10"]
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


def add_row_label(row: str, lbl: str, text: str) -> None:
    uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": lbl,
                       "parent_name": row, "compile": False})
    uiq("set_text", {"asset_path": WBP, "widget_name": lbl, "text": text,
                     "font_size": LBL_FONT, "compile": False})
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": lbl, "v_align": "Center",
                              "padding": {"left": 0, "top": 0, "right": 14, "bottom": 0}, "compile": False})


def build_apply_fn(fname: str, var: str, prefix: str) -> None:
    bpq("add_function", {"asset_path": WBP, "name": fname, "category": "Wind"})
    bpq("set_function_params", {"asset_path": WBP, "function_name": fname,
                                "inputs": [{"name": "Amount", "type": "float"}]})
    fn_nodes = graph_nodes(fname)
    entry = next(nid for nid in fn_nodes if "FunctionEntry" in nid)
    vg_t = add(fname, "VariableGet", 100, 250, variable_name="TargetWindComp")
    vs = spawn_varset(fname, 450, 0, var)
    c2s = add(fname, "CallFunction", 750, 250, function_name="Conv_DoubleToString", target_class="KismetStringLibrary")
    cat = add(fname, "CallFunction", 1000, 250, function_name="Concat_StrStr", target_class="KismetStringLibrary")
    ps = add(fname, "CallFunction", 1300, 0, function_name="PrintString", target_class="KismetSystemLibrary")
    setdef(fname, cat, "A", prefix)
    f = connect(fname, [
        {"source_node": entry, "source_pin": "then", "target_node": vs, "target_pin": "execute"},
        {"source_node": vs, "source_pin": "then", "target_node": ps, "target_pin": "execute"},
        {"source_node": entry, "source_pin": "Amount", "target_node": vs, "target_pin": var},
        {"source_node": vg_t, "source_pin": "TargetWindComp", "target_node": vs, "target_pin": "self"},
        {"source_node": vs, "source_pin": "Output_Get", "target_node": c2s, "target_pin": "InDouble"},
        {"source_node": c2s, "source_pin": "ReturnValue", "target_node": cat, "target_pin": "B"},
        {"source_node": cat, "source_pin": "ReturnValue", "target_node": ps, "target_pin": "InString"},
    ])
    assert f == 0, "%s 배선 실패" % fname


# ═══ ① 기존 터브 줄 라벨 (맨 앞 배치 = 라벨 add 후 버튼 5개 재append) ═══
add_row_label("WindRowTurb", "Lbl_Turb", "Turb")
try:
    for btn in TURB_BTNS:
        uiq("move_widget", {"asset_path": WBP, "widget_name": btn, "new_parent_name": "WindRowTurb"})
    LOG["steps"].append("Turb 줄 라벨 선두 배치 OK")
except Exception as e:
    LOG["steps"].append("같은 부모 재append 실패(라벨이 줄 끝에 남음, 무해): %s" % str(e)[:100])

# ═══ ② 신규 2줄 (라벨 + 버튼 5개) ═══
for row, lbl, lbl_text, fname, var, prefix, btns in ROWS:
    uiq("add_widget", {"asset_path": WBP, "widget_class": "HorizontalBox", "widget_name": row,
                       "parent_name": "WindBtnCol", "compile": False})
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": row, "h_align": "Right",
                              "padding": {"left": 0, "top": 12, "right": 0, "bottom": 0}, "compile": False})
    add_row_label(row, lbl, lbl_text)
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
    LOG["steps"].append("%s (%s) OK" % (row, lbl_text))

# ═══ ③ 함수 2개 + 컴파일 ═══
for row, lbl, lbl_text, fname, var, prefix, btns in ROWS:
    build_apply_fn(fname, var, prefix)
cr = bpq("compile_blueprint", {"asset_path": WBP})
assert not cr.get("errors"), "함수 컴파일 에러: %s" % cr
LOG["steps"].append("ApplyTurbSpeed/ApplyTurbSize OK (컴파일 클린)")

# ═══ ④ 바운드 이벤트 10개 ═══
y0 = 4200
for row, lbl, lbl_text, fname, var, prefix, btns in ROWS:
    for i, (btn, label) in enumerate(btns):
        y = y0 + i * 300
        ev = add(EG, "ComponentBoundEvent", 0, y, component_name=btn, delegate_property_name="OnClicked")
        ap = spawn_selfcall(EG, 400, y, fname)
        setdef(EG, ap, "Amount", label)
        f = connect(EG, [
            {"source_node": ev, "source_pin": "then", "target_node": ap, "target_pin": "execute"},
        ])
        assert f == 0, "%s 체인 배선 실패" % btn
    y0 += 1600
    LOG["steps"].append("%s 5체인 OK" % fname)

cr = bpq("compile_blueprint", {"asset_path": WBP})
LOG["steps"].append("compile 최종: %s" % json.dumps(cr, ensure_ascii=False)[:200])
assert not cr.get("errors"), "최종 컴파일 에러: %s" % cr
call("editor_query", "save_asset", {"asset_path": WBP})

# ═══ ⑤ 검증 ═══
wn = graph_nodes(EG)
evs = [nid for nid in wn if "ComponentBoundEvent" in nid]
wired = all(bool({p["name"]: p for p in wn[nid].get("pins", [])}.get("then", {}).get("connected_to")) for nid in evs)
tree = json.dumps(uiq("get_widget_tree", {"asset_path": WBP}))
checks = {"ev_count": len(evs), "all_wired": wired, "btn_count": tree.count('"class": "Button"'),
          "rows": all(('"%s"' % r[0]) in tree for r in ROWS)}
LOG["steps"].append({"verify": checks})
assert checks["ev_count"] == 22 and wired and checks["btn_count"] == 22 and checks["rows"], "검증 실패: %s" % checks
LOG["steps"].append("v9 완료 — WBP 저장됨")
