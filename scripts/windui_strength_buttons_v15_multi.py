# 윈드 강도 UI v15 — WindActor 버튼 -> Vortex2/Radial4 동시 적용 (2026-08-05 승호 지시)
#   실측: Radial=WindStrength+Turb3종 / Vortex=WindStrength 없음(Tangential/Radial/Axial)+Turb3종
#   방침: 강도 = Dir.WindStrength + Radial.WindStrength + Vortex.(Tan/Rad/Ax) 전부 Sign×SelValue
#         터브 프리셋/OFF = 3컴포넌트 모두 동일 적용
#   위젯: 변수 2 + InitWind 입력 2 + ApplyWind/ApplyTurb/ApplyTurbSet 체인 확장
#   레벨BP: 리터럴 2 + GetComponentByClass 2 -> InitWind 신핀
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
MAP_BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
WBP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/WBP_WindStrengthButtons"
EG = "EventGraph"
MAPQ = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map.SBWind_Weight_TEST01_Map:PersistentLevel."
LIT_VORTEX = MAPQ + "SBVortexWindActor_UAID_30560F6BCAE51DF502_1651166348"
LIT_RADIAL = MAPQ + "SBRadialWindActor_UAID_30560F6BCAE51DF502_1584215331"
RC = "SBRadialWindComponent"
VC = "SBVortexWindComponent"
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


def follow(nodes: dict, nid: str, pin: str):
    c = pmn(nodes, nid)[pin].get("connected_to") or []
    assert c, "%s.%s 미연결" % (nid, pin)
    s = c[0]
    return (tuple(s.rsplit(".", 1)) if isinstance(s, str)
            else (s.get("node") or s.get("node_id"), s.get("pin") or s.get("pin_name")))


def spawn_extset(graph: str, x: int, y: int, var: str, tclass: str) -> str:
    t3d = '(MemberParent=/Script/SB2.%s,MemberName="%s",bSelfContext=False)' % (tclass, var)
    nid = add(WBP, graph, "VariableSet", x, y, variable_name=var, target_class=tclass)
    pins = node_pins(WBP, graph, nid)
    if var not in pins:
        bpq("set_node_property", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                                  "property_name": "VariableReference", "value": t3d})
        bpq("refresh_node", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
        pins = node_pins(WBP, graph, nid)
    assert var in pins, "%s Set %s 핀 미생성: %s" % (graph, var, list(pins))
    return nid


def spawn_ownset(graph: str, x: int, y: int, var: str) -> str:
    nid = add(WBP, graph, "VariableSet", x, y, variable_name=var)
    pins = node_pins(WBP, graph, nid)
    if var not in pins:
        bpq("set_node_property", {"asset_path": WBP, "graph_name": graph, "node_id": nid,
                                  "property_name": "VariableReference",
                                  "value": '(MemberName="%s",bSelfContext=True)' % var})
        bpq("refresh_node", {"asset_path": WBP, "graph_name": graph, "node_id": nid})
        pins = node_pins(WBP, graph, nid)
    assert var in pins, "own set %s 파손" % var
    return nid


# ═══ ① 위젯 변수 + InitWind 확장 ═══
gv = {v["name"] for v in bpq("get_variables", {"asset_path": WBP}).get("variables", [])}
if "TargetRadialComp" not in gv:
    uiq("add_widget_variable", {"wbp_path": WBP, "var_name": "TargetRadialComp",
                                "var_type": "object:" + RC, "var_category": "Wind"})
if "TargetVortexComp" not in gv:
    uiq("add_widget_variable", {"wbp_path": WBP, "var_name": "TargetVortexComp",
                                "var_type": "object:" + VC, "var_category": "Wind"})
bpq("set_function_params", {"asset_path": WBP, "function_name": "InitWind",
                            "inputs": [{"name": "RadialComp", "type": "object:" + RC},
                                       {"name": "VortexComp", "type": "object:" + VC}]})
fn = graph_nodes(WBP, "InitWind")
entry = next(nid for nid in fn if "FunctionEntry" in nid)
vs_g = next(nid for nid in fn if nid.startswith("K2Node_VariableSet") and "TargetGlobalWind" in pmn(fn, nid))
vs_r = spawn_ownset("InitWind", 1000, 0, "TargetRadialComp")
vs_v = spawn_ownset("InitWind", 1300, 0, "TargetVortexComp")
f = connect(WBP, "InitWind", [
    {"source_node": vs_g, "source_pin": "then", "target_node": vs_r, "target_pin": "execute"},
    {"source_node": vs_r, "source_pin": "then", "target_node": vs_v, "target_pin": "execute"},
    {"source_node": entry, "source_pin": "RadialComp", "target_node": vs_r, "target_pin": "TargetRadialComp"},
    {"source_node": entry, "source_pin": "VortexComp", "target_node": vs_v, "target_pin": "TargetVortexComp"},
])
assert f == 0, "InitWind 확장 배선 실패"
LOG["steps"].append("InitWind + Radial/Vortex 입력 OK")

# ═══ ② ApplyWind: 강도 -> Radial.WindStrength + Vortex 3성분 ═══
FN = "ApplyWind"
fn = graph_nodes(WBP, FN)
vsD = next(nid for nid in fn if nid.startswith("K2Node_VariableSet")
           and "WindStrength" in pmn(fn, nid) and "SBDirectionalWindComponent" in pmn(fn, nid)["self"].get("type", ""))
mul, _ = follow(fn, vsD, "WindStrength")
ps, _ = follow(fn, vsD, "then")
vgR = add(WBP, FN, "VariableGet", 600, 450, variable_name="TargetRadialComp")
vgV = add(WBP, FN, "VariableGet", 600, 600, variable_name="TargetVortexComp")
vsRS = spawn_extset(FN, 800, -300, "WindStrength", RC)
vsT = spawn_extset(FN, 1050, -300, "TangentialStrength", VC)
vsR2 = spawn_extset(FN, 1300, -300, "RadialStrength", VC)
vsA = spawn_extset(FN, 1550, -300, "AxialStrength", VC)
bpq("disconnect_pins", {"asset_path": WBP, "graph_name": FN, "node_id": vsD, "pin_name": "then"})
f = connect(WBP, FN, [
    {"source_node": vsD, "source_pin": "then", "target_node": vsRS, "target_pin": "execute"},
    {"source_node": vsRS, "source_pin": "then", "target_node": vsT, "target_pin": "execute"},
    {"source_node": vsT, "source_pin": "then", "target_node": vsR2, "target_pin": "execute"},
    {"source_node": vsR2, "source_pin": "then", "target_node": vsA, "target_pin": "execute"},
    {"source_node": vsA, "source_pin": "then", "target_node": ps, "target_pin": "execute"},
    {"source_node": mul, "source_pin": "ReturnValue", "target_node": vsRS, "target_pin": "WindStrength"},
    {"source_node": mul, "source_pin": "ReturnValue", "target_node": vsT, "target_pin": "TangentialStrength"},
    {"source_node": mul, "source_pin": "ReturnValue", "target_node": vsR2, "target_pin": "RadialStrength"},
    {"source_node": mul, "source_pin": "ReturnValue", "target_node": vsA, "target_pin": "AxialStrength"},
    {"source_node": vgR, "source_pin": "TargetRadialComp", "target_node": vsRS, "target_pin": "self"},
    {"source_node": vgV, "source_pin": "TargetVortexComp", "target_node": vsT, "target_pin": "self"},
    {"source_node": vgV, "source_pin": "TargetVortexComp", "target_node": vsR2, "target_pin": "self"},
    {"source_node": vgV, "source_pin": "TargetVortexComp", "target_node": vsA, "target_pin": "self"},
])
assert f == 0, "ApplyWind 확장 배선 실패"
LOG["steps"].append("ApplyWind -> Radial+Vortex(3성분) OK")

# ═══ ③ ApplyTurb: Turbulence -> Radial+Vortex ═══
FN = "ApplyTurb"
fn = graph_nodes(WBP, FN)
entry_t = next(nid for nid in fn if "FunctionEntry" in nid)
vsTD = next(nid for nid in fn if nid.startswith("K2Node_VariableSet")
            and "Turbulence" in pmn(fn, nid) and "SBDirectionalWindComponent" in pmn(fn, nid)["self"].get("type", ""))
ps, _ = follow(fn, vsTD, "then")
vgR = add(WBP, FN, "VariableGet", 600, 450, variable_name="TargetRadialComp")
vgV = add(WBP, FN, "VariableGet", 600, 600, variable_name="TargetVortexComp")
vsTR = spawn_extset(FN, 800, -300, "Turbulence", RC)
vsTV = spawn_extset(FN, 1050, -300, "Turbulence", VC)
bpq("disconnect_pins", {"asset_path": WBP, "graph_name": FN, "node_id": vsTD, "pin_name": "then"})
f = connect(WBP, FN, [
    {"source_node": vsTD, "source_pin": "then", "target_node": vsTR, "target_pin": "execute"},
    {"source_node": vsTR, "source_pin": "then", "target_node": vsTV, "target_pin": "execute"},
    {"source_node": vsTV, "source_pin": "then", "target_node": ps, "target_pin": "execute"},
    {"source_node": entry_t, "source_pin": "Amount", "target_node": vsTR, "target_pin": "Turbulence"},
    {"source_node": entry_t, "source_pin": "Amount", "target_node": vsTV, "target_pin": "Turbulence"},
    {"source_node": vgR, "source_pin": "TargetRadialComp", "target_node": vsTR, "target_pin": "self"},
    {"source_node": vgV, "source_pin": "TargetVortexComp", "target_node": vsTV, "target_pin": "self"},
])
assert f == 0, "ApplyTurb 확장 배선 실패"
LOG["steps"].append("ApplyTurb(OFF 포함) -> Radial+Vortex OK")

# ═══ ④ ApplyTurbSet: 3프로퍼티 -> Radial+Vortex ═══
FN = "ApplyTurbSet"
fn = graph_nodes(WBP, FN)
entry_s = next(nid for nid in fn if "FunctionEntry" in nid)
vs3 = next(nid for nid in fn if nid.startswith("K2Node_VariableSet")
           and "TurbulenceSpeed" in pmn(fn, nid) and "SBDirectionalWindComponent" in pmn(fn, nid)["self"].get("type", ""))
ps, _ = follow(fn, vs3, "then")
vgR = add(WBP, FN, "VariableGet", 900, 500, variable_name="TargetRadialComp")
vgV = add(WBP, FN, "VariableGet", 900, 650, variable_name="TargetVortexComp")
chain = [vs3]
conns = []
x = 1250
for tclass, vg in ((RC, vgR), (VC, vgV)):
    tvar = "TargetRadialComp" if tclass == RC else "TargetVortexComp"
    for var, param in (("Turbulence", "Turb"), ("TurbulenceSize", "Size"), ("TurbulenceSpeed", "Speed")):
        vs = spawn_extset(FN, x, -300, var, tclass)
        conns += [
            {"source_node": chain[-1], "source_pin": "then", "target_node": vs, "target_pin": "execute"},
            {"source_node": entry_s, "source_pin": param, "target_node": vs, "target_pin": var},
            {"source_node": vg, "source_pin": tvar, "target_node": vs, "target_pin": "self"},
        ]
        chain.append(vs)
        x += 250
conns.append({"source_node": chain[-1], "source_pin": "then", "target_node": ps, "target_pin": "execute"})
bpq("disconnect_pins", {"asset_path": WBP, "graph_name": FN, "node_id": vs3, "pin_name": "then"})
f = connect(WBP, FN, conns)
assert f == 0, "ApplyTurbSet 확장 배선 실패"
LOG["steps"].append("ApplyTurbSet -> Radial+Vortex (6셋) OK")

cr = bpq("compile_blueprint", {"asset_path": WBP})
assert not cr.get("errors"), "위젯 컴파일 에러: %s" % cr
call("editor_query", "save_asset", {"asset_path": WBP})
LOG["steps"].append("위젯 컴파일+저장 OK")

# ═══ ⑤ 레벨BP: 리터럴 2 + GetComponentByClass 2 -> InitWind ═══
nodes = graph_nodes(MAP_BP, EG)
inits = [nid for nid in nodes if nid.startswith("K2Node_CallFunction")
         and "Comp" in pmn(nodes, nid) and "GlobalVolume" in pmn(nodes, nid)]
assert len(inits) == 1, "InitWind 호출 노드 특정 실패: %s" % inits
init = inits[0]
before = {p: (pmn(nodes, init)[p].get("connected_to") or None) for p in pmn(nodes, init)}
bpq("refresh_node", {"asset_path": MAP_BP, "graph_name": EG, "node_id": init})
ipins = node_pins(MAP_BP, EG, init)
assert "RadialComp" in ipins and "VortexComp" in ipins, "InitWind 신핀 미노출: %s" % list(ipins)

new_conns = []
for lit_path, comp_class, pin, ybase in ((LIT_RADIAL, RC, "RadialComp", 3050), (LIT_VORTEX, VC, "VortexComp", 3250)):
    lit = add(MAP_BP, EG, "K2Node_Literal", -1250, ybase)
    bpq("set_node_property", {"asset_path": MAP_BP, "graph_name": EG, "node_id": lit,
                              "property_name": "ObjectRef", "value": lit_path})
    bpq("refresh_node", {"asset_path": MAP_BP, "graph_name": EG, "node_id": lit})
    lp = node_pins(MAP_BP, EG, lit)
    out_pin = next(p for p in lp if lp[p].get("direction") != "input" and p not in ("execute", "then"))
    gcbc = add(MAP_BP, EG, "CallFunction", -950, ybase, function_name="GetComponentByClass", target_class="Actor")
    bpq("set_pin_default", {"asset_path": MAP_BP, "graph_name": EG, "node_id": gcbc,
                            "pin_name": "ComponentClass", "value": "/Script/SB2." + comp_class})
    new_conns += [
        {"source_node": lit, "source_pin": out_pin, "target_node": gcbc, "target_pin": "self"},
        {"source_node": gcbc, "source_pin": "ReturnValue", "target_node": init, "target_pin": pin},
    ]
    LOG["steps"].append("Literal %s (핀=%s)" % (comp_class, out_pin))
f = connect(MAP_BP, EG, new_conns)
assert f == 0, "레벨BP 신규 배선 실패"

# refresh 유실 복구
nodes = graph_nodes(MAP_BP, EG)
ip = pmn(nodes, init)
relink = []
for pin, conn in before.items():
    if conn and pin in ip and not (ip[pin].get("connected_to") or []):
        s = conn[0]
        src_n, src_p = (tuple(s.rsplit(".", 1)) if isinstance(s, str)
                        else (s.get("node") or s.get("node_id"), s.get("pin") or s.get("pin_name")))
        if pin == "then":
            relink.append({"source_node": init, "source_pin": pin, "target_node": src_n, "target_pin": src_p})
        else:
            relink.append({"source_node": src_n, "source_pin": src_p, "target_node": init, "target_pin": pin})
if relink:
    f = connect(MAP_BP, EG, relink)
    LOG["steps"].append({"refresh 복구": relink, "fail": f})
    assert f == 0, "복구 재배선 실패"

cr = bpq("compile_blueprint", {"asset_path": MAP_BP})
assert not cr.get("errors"), "레벨BP 컴파일 에러: %s" % cr

# ═══ ⑥ 검증 ═══
nodes = graph_nodes(MAP_BP, EG)
ip = pmn(nodes, init)
lvl = {p: bool(ip[p].get("connected_to")) for p in ("execute", "then", "self", "Comp", "GlobalVolume",
                                                    "RadialComp", "VortexComp")}
LOG["steps"].append({"init_pins": lvl})
assert all(lvl.values()), "init 핀 검증 실패: %s" % lvl
LOG["steps"].append("v15 완료 — WBP 저장됨, ⚠ 맵 미저장 (레벨BP 변경 있음 — 저장 필요)")
