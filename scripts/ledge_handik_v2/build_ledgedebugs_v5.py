# LedgeDebugs v5 노드 빌드 — 파이썬 드로어 폐기, ABP 그래프 네이티브화
#  구체: LedgeHandWorldL/R(IK 구속점)에 DrawDebugSphere, 색=SelectColor(밝/어둠, α≥0.5)
#  박스: bTransitMoving 게이트 (Idle 스테일 래치 숨김)
#  Dest 박스+경로 라인: |Dest-Anchor|>20 (v14 게이트 통과=커밋) 시만
# ⚠ 로컬 python 전용 — 에디터 콘솔(py) 실행 금지.
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "LedgeDebugs"
KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"
L_BRT = "(R=0.0,G=1.0,B=1.0,A=1.0)"
L_DIM = "(R=0.0,G=0.15,B=0.15,A=1.0)"
R_BRT = "(R=1.0,G=0.0,B=1.0,A=1.0)"
R_DIM = "(R=0.15,G=0.0,B=0.15,A=1.0)"


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:300])
    return json.loads(txt)


ns = {n["id"]: n for n in call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": G})["nodes"]}


def pins(n):
    return {p["name"]: p for p in n.get("pins", [])}


def out_exec(nid):
    return (pins(ns[nid]).get("then", {}).get("connected_to") or [])


# 기존 앵커: 14(스트링)→15..18(손박스)→IfThenElse_0→20..23(발박스)→31(스트링)
after18 = out_exec("K2Node_CallFunction_18")[0].split(".")  # IfThenElse_0
print("18.then ->", after18)

nodes, defaults, conns = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(nid, pin, val):
    defaults.append({"node_id": nid, "pin_name": pin, "value": val})


# ── 구체 (IK 구속점 + 활성색) ──
for s, brt, dim, y in (("L", L_BRT, L_DIM, 2400), ("R", R_BRT, R_DIM, 2650)):
    N("gw" + s, "VariableGet", -400, y, variable_name="LedgeHandWorld" + s)
    N("ga" + s, "VariableGet", -400, y + 90, variable_name="LedgeHandIKAlpha" + s)
    N("ge" + s, "CallFunction", -220, y + 90, function_name="GreaterEqual_DoubleDouble", target_class=KML)
    C("ga" + s, "LedgeHandIKAlpha" + s, "ge" + s, "A")
    N("sel" + s, "CallFunction", -40, y + 60, function_name="SelectColor", target_class=KML)
    C("ge" + s, "ReturnValue", "sel" + s, "bPickA")
    N("sph" + s, "CallFunction", 140, y, function_name="DrawDebugSphere", target_class=KSL)
    C("gw" + s, "LedgeHandWorld" + s, "sph" + s, "Center")
    C("sel" + s, "ReturnValue", "sph" + s, "LineColor")
    D("ge" + s, "B", "0.5")
    D("sel" + s, "A", brt)
    D("sel" + s, "B", dim)
    D("sph" + s, "Radius", "6.0")
    D("sph" + s, "Segments", "12")
    D("sph" + s, "Duration", "0.0")
    D("sph" + s, "Thickness", "1.0")
# ── mv 게이트 ──
N("gmv", "VariableGet", 300, 2500, variable_name="bTransitMoving")
N("brmv", "Branch", 480, 2400)
C("gmv", "bTransitMoving", "brmv", "Condition")
# ── Dest 커밋 게이트 + 경로 라인 (손) ──
for s, ga, gd, brt, y in (("L", "K2Node_VariableGet_4", "K2Node_VariableGet_6", L_BRT, 2900),
                          ("R", "K2Node_VariableGet_5", "K2Node_VariableGet_9", R_BRT, 3150)):
    av = "LedgeHandAnchor" + s
    dv = "LedgeHandDest" + s
    N("dist" + s, "CallFunction", -400, y, function_name="Vector_Distance", target_class=KML)
    C(gd, dv, "dist" + s, "V1")
    C(ga, av, "dist" + s, "V2")
    N("gt" + s, "CallFunction", -220, y, function_name="Greater_DoubleDouble", target_class=KML)
    C("dist" + s, "ReturnValue", "gt" + s, "A")
    D("gt" + s, "B", "20.0")
    N("brd" + s, "Branch", -40, y)
    C("gt" + s, "ReturnValue", "brd" + s, "Condition")
    N("line" + s, "CallFunction", 140, y, function_name="DrawDebugLine", target_class=KSL)
    C(ga, av, "line" + s, "LineStart")
    C(gd, dv, "line" + s, "LineEnd")
    D("line" + s, "LineColor", brt)
    D("line" + s, "Duration", "0.0")
    D("line" + s, "Thickness", "0.2")

tm = {}


def harvest(o):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tm[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v)
    elif isinstance(o, list):
        for e in o:
            harvest(e)


harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G, "nodes": nodes}))
if len(tm) != len(nodes):
    raise SystemExit("노드 %d/%d missing=%s" % (len(tm), len(nodes), [n["temp_id"] for n in nodes if n["temp_id"] not in tm]))
for d in defaults:
    d["node_id"] = tm[d["node_id"]]
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": G, "defaults": defaults})
dfails = [x for x in (rd.get("results") or []) if not x.get("success", True)]
print("defaults fails:", dfails if dfails else 0)

# ── exec 절단 + 재배선 ──
# 절단: 14.then(→15), 16.then(→17), 17.then(→18), 18.then(→IfThenElse_0)
for nid in ("K2Node_CallFunction_14", "K2Node_CallFunction_16", "K2Node_CallFunction_17", "K2Node_CallFunction_18"):
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": nid, "pin_name": "then"})
ex = []


def E(a, ap, b, bp="execute"):
    ex.append({"source_node": tm.get(a, a), "source_pin": ap, "target_node": tm.get(b, b), "target_pin": bp})


E("K2Node_CallFunction_14", "then", "sphL")
E("sphL", "then", "sphR")
E("sphR", "then", "brmv")
E("brmv", "then", "K2Node_CallFunction_15")           # 손 Anchor 박스 15→16 기존 유지
E("brmv", "else", "K2Node_CallFunction_31")           # 박스 전체 스킵
E("K2Node_CallFunction_16", "then", "brdL")
E("brdL", "then", "K2Node_CallFunction_17")           # DestL 박스
E("K2Node_CallFunction_17", "then", "lineL")
E("lineL", "then", "brdR")
E("brdL", "else", "brdR")
E("brdR", "then", "K2Node_CallFunction_18")           # DestR 박스
E("K2Node_CallFunction_18", "then", "lineR")
E("lineR", "then", after18[0], after18[1])
E("brdR", "else", after18[0], after18[1])
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G, "connections": conns + ex})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
print("links: %d req %d fail" % (len(conns) + len(ex), len(fails)))
for f in fails[:12]:
    print("  FAIL:", json.dumps(f, ensure_ascii=False)[:200])

r = call("blueprint_query", "compile_blueprint", {"asset_path": ABP})
print("compile:", r.get("success"), "errors:", r.get("error_count"), (r.get("errors") or [])[:3])
if r.get("success") and not fails:
    s = call("editor_query", "save_asset", {"asset_path": ABP})
    print("save:", s.get("saved"))
