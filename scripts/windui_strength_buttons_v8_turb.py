# 윈드 강도 UI v8 — Turbulence 5단계 버튼 줄 추가 (2026-08-05 승호 지시)
#   실측: SBDirectionalWindComponent.Turbulence (신규, 라이브 0.5 / Actor10도 세팅됨)
#   5단계 = 0.2/0.4/0.6/0.8/1.0 균등 (⚠ 상한 1.0은 SBWindVolume TurbulenceAmount 0~1 유추 — 가설)
#   UI: WindBtnCol 3번째 줄 WindRowTurb + Btn_T02~T10, 폰트 54
#   그래프: ApplyTurb(Amount) 함수(외부 Set Turbulence + PrintString) + 바운드 이벤트 5개
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
EG = "EventGraph"
FN = "ApplyTurb"
FONT = 54
TURB = [("Btn_T02", "0.2"), ("Btn_T04", "0.4"), ("Btn_T06", "0.6"), ("Btn_T08", "0.8"), ("Btn_T10", "1.0")]
T3D_TURB = '(MemberParent=/Script/SB2.SBDirectionalWindComponent,MemberName="Turbulence",bSelfContext=False)'
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


def spawn_varset(graph: str, x: int, y: int, var: str, target_class: str, t3d: str) -> str:
    nid = add(graph, "VariableSet", x, y, variable_name=var, target_class=target_class)
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


# ═══ ① UI: 3번째 줄 + 버튼 5개 ═══
uiq("add_widget", {"asset_path": WBP, "widget_class": "HorizontalBox", "widget_name": "WindRowTurb",
                   "parent_name": "WindBtnCol", "compile": False})
uiq("set_slot_property", {"asset_path": WBP, "widget_name": "WindRowTurb", "h_align": "Right",
                          "padding": {"left": 0, "top": 12, "right": 0, "bottom": 0}, "compile": False})
for btn, label in TURB:
    uiq("add_widget", {"asset_path": WBP, "widget_class": "Button", "widget_name": btn,
                       "parent_name": "WindRowTurb", "compile": False})
    uiq("add_widget", {"asset_path": WBP, "widget_class": "TextBlock", "widget_name": "Txt_" + btn,
                       "parent_name": btn, "compile": False})
    uiq("set_text", {"asset_path": WBP, "widget_name": "Txt_" + btn, "text": label,
                     "font_size": FONT, "justification": "Center", "compile": False})
    uiq("set_slot_property", {"asset_path": WBP, "widget_name": btn,
                              "padding": {"left": 10, "top": 0, "right": 10, "bottom": 0}, "compile": False})
    uiq("set_widget_is_variable", {"wbp_path": WBP, "widget_name": btn, "is_variable": True})
LOG["steps"].append("WindRowTurb + 버튼 5개 OK")

# ═══ ② ApplyTurb(Amount) 함수 ═══
bpq("add_function", {"asset_path": WBP, "name": FN, "category": "Wind"})
bpq("set_function_params", {"asset_path": WBP, "function_name": FN,
                            "inputs": [{"name": "Amount", "type": "float"}]})
fn_nodes = graph_nodes(FN)
entry = next(nid for nid in fn_nodes if "FunctionEntry" in nid)
vg_t = add(FN, "VariableGet", 100, 250, variable_name="TargetWindComp")
vs = spawn_varset(FN, 450, 0, "Turbulence", "SBDirectionalWindComponent", T3D_TURB)
c2s = add(FN, "CallFunction", 750, 250, function_name="Conv_DoubleToString", target_class="KismetStringLibrary")
cat = add(FN, "CallFunction", 1000, 250, function_name="Concat_StrStr", target_class="KismetStringLibrary")
ps = add(FN, "CallFunction", 1300, 0, function_name="PrintString", target_class="KismetSystemLibrary")
setdef(FN, cat, "A", "DirWind Turb = ")
f = connect(FN, [
    {"source_node": entry, "source_pin": "then", "target_node": vs, "target_pin": "execute"},
    {"source_node": vs, "source_pin": "then", "target_node": ps, "target_pin": "execute"},
    {"source_node": entry, "source_pin": "Amount", "target_node": vs, "target_pin": "Turbulence"},
    {"source_node": vg_t, "source_pin": "TargetWindComp", "target_node": vs, "target_pin": "self"},
    {"source_node": vs, "source_pin": "Output_Get", "target_node": c2s, "target_pin": "InDouble"},
    {"source_node": c2s, "source_pin": "ReturnValue", "target_node": cat, "target_pin": "B"},
    {"source_node": cat, "source_pin": "ReturnValue", "target_node": ps, "target_pin": "InString"},
])
assert f == 0, "ApplyTurb 배선 실패 — LOG.errors 확인"
cr = bpq("compile_blueprint", {"asset_path": WBP})
assert not cr.get("errors"), "ApplyTurb 컴파일 에러: %s" % cr
LOG["steps"].append("ApplyTurb 함수 OK (컴파일 클린)")

# ═══ ③ 바운드 이벤트 5개 -> ApplyTurb(값) ═══
for i, (btn, label) in enumerate(TURB):
    y = 2500 + i * 300
    ev = add(EG, "ComponentBoundEvent", 0, y, component_name=btn, delegate_property_name="OnClicked")
    ap = spawn_selfcall(EG, 400, y, FN)
    setdef(EG, ap, "Amount", label)
    f = connect(EG, [
        {"source_node": ev, "source_pin": "then", "target_node": ap, "target_pin": "execute"},
    ])
    assert f == 0, "%s 체인 배선 실패" % btn
LOG["steps"].append("터뷸런스 5체인 OK")

cr = bpq("compile_blueprint", {"asset_path": WBP})
LOG["steps"].append("compile 최종: %s" % json.dumps(cr, ensure_ascii=False)[:200])
assert not cr.get("errors"), "최종 컴파일 에러: %s" % cr
call("editor_query", "save_asset", {"asset_path": WBP})

# ═══ ④ 검증 ═══
wn = graph_nodes(EG)
evs = [nid for nid in wn if "ComponentBoundEvent" in nid]
wired = all(bool({p["name"]: p for p in wn[nid].get("pins", [])}.get("then", {}).get("connected_to")) for nid in evs)
tree = json.dumps(uiq("get_widget_tree", {"asset_path": WBP}))
checks = {"ev_count": len(evs), "all_wired": wired,
          "turb_row": '"WindRowTurb"' in tree, "btn_count": tree.count('"class": "Button"')}
LOG["steps"].append({"verify": checks})
assert checks["ev_count"] == 12 and wired and checks["btn_count"] == 12, "검증 실패: %s" % checks
LOG["steps"].append("v8 완료 — WBP 저장됨")
