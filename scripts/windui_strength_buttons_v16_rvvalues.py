# 윈드 강도 UI v16 — Radial/Vortex 별도 규격값 (2026-08-05, Confluence 액터별 강도 표)
#   Directional = 12/9/7.5/6/4 (기존) / Radial·Vortex = 15/13/11/9/7 (신규 SelValueRV)
#   ApplyWind: mul2 = SelValueRV × WindSign -> Radial.WindStrength + Vortex 3성분
#   표시 확장: "DirWind Str = X / RV Y"
#   스테이지 버튼 체인: ev -> SetSelValue -> [신규 SetSelValueRV] -> ApplyWind
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
EG = "EventGraph"
FN = "ApplyWind"
RV = {"Btn_W4": "15", "Btn_W6": "13", "Btn_W7_5": "11", "Btn_W9": "9", "Btn_W12": "7"}  # Extreme..Mild
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


def pmn(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def node_pins(graph: str, nid: str) -> dict:
    det = bpq("get_node_details", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
    return {p.get("name"): p for p in (det.get("pins") or [])}


def follow(nodes: dict, nid: str, pin: str):
    c = pmn(nodes, nid)[pin].get("connected_to") or []
    assert c, "%s.%s 미연결" % (nid, pin)
    s = c[0]
    return (tuple(s.rsplit(".", 1)) if isinstance(s, str)
            else (s.get("node") or s.get("node_id"), s.get("pin") or s.get("pin_name")))


def spawn_ownset(graph: str, x: int, y: int, var: str) -> str:
    nid = add(graph, "VariableSet", x, y, variable_name=var)
    pins = node_pins(graph, nid)
    if var not in pins:
        bpq("set_node_property", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                                  "property_name": "VariableReference",
                                  "value": '(MemberName="%s",bSelfContext=True)' % var})
        bpq("refresh_node", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
        pins = node_pins(graph, nid)
    assert var in pins, "own set %s 파손" % var
    return nid


def setdef(graph: str, nid: str, pin: str, val: str) -> None:
    bpq("set_pin_default", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                            "pin_name": pin, "value": val})


# ═══ ① 변수 ═══
gv = {v["name"] for v in bpq("get_variables", {"asset_path": WBP}).get("variables", [])}
if "SelValueRV" not in gv:
    call("ui_query", "add_widget_variable", {"wbp_path": WBP, "var_name": "SelValueRV",
                                             "var_type": "float", "default_value": "7.0", "var_category": "Wind"})

# ═══ ② ApplyWind: mul2 + 4셋 재배선 + 표시 확장 ═══
fn = graph_nodes(FN)
vsD = next(nid for nid in fn if nid.startswith("K2Node_VariableSet")
           and "WindStrength" in pmn(fn, nid) and "SBDirectionalWindComponent" in pmn(fn, nid)["self"].get("type", ""))
mul, _ = follow(fn, vsD, "WindStrength")
sign_src = follow(fn, mul, "B")  # WindSign VariableGet
# 재배선 대상 4셋: mul.ReturnValue 소비처 중 vsD 제외
targets = []
for nid in fn:
    if not nid.startswith("K2Node_VariableSet") or nid == vsD:
        continue
    p = pmn(fn, nid)
    for pin_name in ("WindStrength", "TangentialStrength", "RadialStrength", "AxialStrength"):
        if pin_name in p:
            c = p[pin_name].get("connected_to") or []
            src = c and (c[0].rsplit(".", 1)[0] if isinstance(c[0], str) else (c[0].get("node") or c[0].get("node_id")))
            if src == mul:
                targets.append((nid, pin_name))
assert len(targets) == 4, "재배선 대상 4셋 특정 실패: %s" % targets
vg_rv = add(FN, "VariableGet", 350, 700, variable_name="SelValueRV")
mul2 = add(FN, "CallFunction", 600, 750, function_name="Multiply_DoubleDouble", target_class="KismetMathLibrary")
cs = [
    {"source_node": vg_rv, "source_pin": "SelValueRV", "target_node": mul2, "target_pin": "A"},
    {"source_node": sign_src[0], "source_pin": sign_src[1], "target_node": mul2, "target_pin": "B"},
]
for nid, pin_name in targets:
    bpq("disconnect_pins", {"asset_path": WBP, "graph_name": FN, "node_id": nid, "pin_name": pin_name})
    cs.append({"source_node": mul2, "source_pin": "ReturnValue", "target_node": nid, "target_pin": pin_name})
f = connect(FN, cs)
assert f == 0, "mul2 재배선 실패"
LOG["steps"].append({"mul2 재배선": targets})

# 표시: ps.InString <- cat.Return  ==>  cat -> cat2(" / RV ") -> cat3(+D2S(radial Output_Get)) -> ps
ps = next(nid for nid in fn if nid.startswith("K2Node_CallFunction") and "InString" in pmn(fn, nid))
cat, _ = follow(fn, ps, "InString")
vsRS = next(nid for nid, pin_name in targets if pin_name == "WindStrength")
d2s2 = add(FN, "CallFunction", 1700, 400, function_name="Conv_DoubleToString", target_class="KismetStringLibrary")
cat2 = add(FN, "CallFunction", 1950, 250, function_name="Concat_StrStr", target_class="KismetStringLibrary")
cat3 = add(FN, "CallFunction", 2200, 250, function_name="Concat_StrStr", target_class="KismetStringLibrary")
setdef(FN, cat2, "B", " / RV ")
bpq("disconnect_pins", {"asset_path": WBP, "graph_name": FN, "node_id": ps, "pin_name": "InString"})
f = connect(FN, [
    {"source_node": cat, "source_pin": "ReturnValue", "target_node": cat2, "target_pin": "A"},
    {"source_node": cat2, "source_pin": "ReturnValue", "target_node": cat3, "target_pin": "A"},
    {"source_node": vsRS, "source_pin": "Output_Get", "target_node": d2s2, "target_pin": "InDouble"},
    {"source_node": d2s2, "source_pin": "ReturnValue", "target_node": cat3, "target_pin": "B"},
    {"source_node": cat3, "source_pin": "ReturnValue", "target_node": ps, "target_pin": "InString"},
])
assert f == 0, "표시 확장 배선 실패"
LOG["steps"].append("표시 확장 OK")

# ═══ ③ 스테이지 버튼 5개: SetSelValueRV 삽입 ═══
wn = graph_nodes(EG)
for nid, n in wn.items():
    if "ComponentBoundEvent" not in nid:
        continue
    title = json.dumps(n.get("title") or n.get("name") or n)
    btn = next((b for b in RV if b in title), None)
    if not btn:
        continue
    ssel, _ = follow(wn, nid, "then")
    assert "SelValue" in pmn(wn, ssel), "%s 체인 구조 예상 불일치" % btn
    ap, _ = follow(wn, ssel, "then")
    srv = spawn_ownset(EG, 600, int(pmn(wn, ssel)[list(pmn(wn, ssel))[0]].get("y", 0) or 0), "SelValueRV")
    setdef(EG, srv, "SelValueRV", RV[btn])
    bpq("disconnect_pins", {"asset_path": WBP, "graph_name": EG, "node_id": ssel, "pin_name": "then"})
    f = connect(EG, [
        {"source_node": ssel, "source_pin": "then", "target_node": srv, "target_pin": "execute"},
        {"source_node": srv, "source_pin": "then", "target_node": ap, "target_pin": "execute"},
    ])
    assert f == 0, "%s 삽입 배선 실패" % btn
    LOG["steps"].append("%s: RV=%s 삽입 OK" % (btn, RV[btn]))

cr = bpq("compile_blueprint", {"asset_path": WBP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:200])
assert not cr.get("errors"), "컴파일 에러: %s" % cr
call("editor_query", "save_asset", {"asset_path": WBP})

# ═══ ④ 검증: 체인 + 핀디폴트 ═══
wn2 = graph_nodes(EG)
verify = {}
for nid, n in wn2.items():
    if "ComponentBoundEvent" not in nid:
        continue
    title = json.dumps(n.get("title") or n.get("name") or n)
    btn = next((b for b in RV if b in title), None)
    if not btn:
        continue
    ssel, _ = follow(wn2, nid, "then")
    srv, _ = follow(wn2, ssel, "then")
    p = pmn(wn2, srv)
    assert "SelValueRV" in p, "%s 체인에 RV셋 없음" % btn
    verify[btn] = [pmn(wn2, ssel)["SelValue"].get("default_value"), p["SelValueRV"].get("default_value")]
LOG["steps"].append({"verify(Dir,RV)": verify})
assert len(verify) == 5, "검증 5개 미달"
LOG["steps"].append("v16 완료 — WBP 저장됨")
