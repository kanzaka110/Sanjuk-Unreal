# BakePelvisSpring v3 — 속도 엔벨로프 폐기, 파라미터 템플릿 베이크로 교체
# 모양: (0,0) (Start,0) (Full,1) (HoldEnd,1) (End,0) (dur,0) — 이동구간 애님100%, 도착반동만 스프링
# 파라미터(인스턴스): PelvisSpringStart 0.40 / PelvisSpringFull 0.55 / PelvisSpringHoldEnd 0.90 / PelvisSpringEnd 1.25
# 유지: 패스1 max속도 + PelvisMinSpeed 가드 (Idle/저속 애님 → 상수 0 그대로)
# 구 패스2(loop2 엔벨로프)는 exec 절단만 (dead, 추후 graph_cleanup) — 각 키는 dur 미만일 때만 추가(동일프레임 키 어설션 방지)
# ⚠ 로컬 python 전용 — 에디터 콘솔(py) 실행 금지.
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeIK"  # 구명칭 AM_SBLedgeHandIK — 유저 rename
FN = "BakePelvisSpring"
CURVE = "ledge_pelvis_spring"
KML = "KismetMathLibrary"
ABL = "AnimationBlueprintLibrary"
TEMPLATE = [("PelvisSpringStart", "0.40", "0.0"), ("PelvisSpringFull", "0.55", "1.0"),
            ("PelvisSpringHoldEnd", "0.90", "1.0"), ("PelvisSpringEnd", "1.25", "0.0")]


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


# ── 1) 파라미터 변수 ──
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
for name, dv, _ in TEMPLATE:
    if name in existing:
        continue
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": name, "type": "float", "category": "Pelvis",
          "instance_editable": True, "default_value": dv})
    print("var+", name, dv)

# ── 2) 기존 그래프 파악 ──
ns = {n["id"]: n for n in call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})["nodes"]}


def pins(n):
    return {p["name"]: p for p in n.get("pins", [])}


entry = [i for i, n in ns.items() if "FunctionEntry" in n["class"]][0]
dur = [i for i, n in ns.items() if n["class"] == "K2Node_CallFunction" and "Sequence Length" in n.get("title", "").replace("Get ", "")][0]
# brG: Branch <- Less <- Get PsMax
g_psmax = [i for i, n in ns.items() if n["class"] == "K2Node_VariableGet" and pins(n).get("PsMax")]
brG = less = None
for gid in g_psmax:
    for c in (pins(ns[gid])["PsMax"].get("connected_to") or []):
        tid = c.split(".")[0]
        if tid in ns and ("Less" in ns[tid].get("title", "") or "<" in ns[tid].get("title", "")):
            less = tid
            for c2 in (pins(ns[tid])["ReturnValue"].get("connected_to") or []):
                bid = c2.split(".")[0]
                if bid in ns and ns[bid]["class"] == "K2Node_IfThenElse":
                    brG = bid
assert brG, "brG(MinSpeed 가드 Branch) 미발견"
old_else = (pins(ns[brG]).get("Else", pins(ns[brG]).get("else", {})).get("connected_to") or [])
print("entry=%s dur=%s brG=%s old_else=%s" % (entry, dur, brG, old_else))

# ── 3) 템플릿 클러스터 생성 ──
nodes, defaults, conns = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(nid, pin, val):
    defaults.append({"node_id": nid, "pin_name": pin, "value": val})


N("tk0", "CallFunction", 3300, 900, function_name="AddFloatCurveKey", target_class=ABL)
D("tk0", "CurveName", CURVE)
D("tk0", "Time", "0.0")
D("tk0", "Value", "0.0")
for k, (var, _, val) in enumerate(TEMPLATE):
    x = 3600 + 500 * k
    N("g%d" % k, "VariableGet", x, 1150, variable_name=var)
    N("ls%d" % k, "CallFunction", x + 130, 1050, function_name="Less_DoubleDouble", target_class=KML)
    C("g%d" % k, var, "ls%d" % k, "A")
    C(dur, "Length", "ls%d" % k, "B")
    N("br%d" % k, "Branch", x + 260, 900)
    C("ls%d" % k, "ReturnValue", "br%d" % k, "Condition")
    N("k%d" % k, "CallFunction", x + 390, 900, function_name="AddFloatCurveKey", target_class=ABL)
    D("k%d" % k, "CurveName", CURVE)
    D("k%d" % k, "Value", val)
    C("g%d" % k, var, "k%d" % k, "Time")
N("kEnd", "CallFunction", 5700, 900, function_name="AddFloatCurveKey", target_class=ABL)
D("kEnd", "CurveName", CURVE)
D("kEnd", "Value", "0.0")
C(dur, "Length", "kEnd", "Time")
for t in ["tk0", "kEnd"] + ["k%d" % k for k in range(4)]:
    C(entry, "Seq", t, "AnimationSequenceBase")

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


harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": FN, "nodes": nodes}))
if len(tm) != len(nodes):
    raise SystemExit("노드 %d/%d: missing=%s" % (len(tm), len(nodes), [n["temp_id"] for n in nodes if n["temp_id"] not in tm]))
for d in defaults:
    d["node_id"] = tm[d["node_id"]]
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": FN, "defaults": defaults})
dfails = [x for x in (rd.get("results") or []) if not x.get("success", True)]
print("defaults fails:", dfails if dfails else 0)

# exec 배선: brG.else 절단 → tk0 → br0 … br3 → kEnd
call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": FN, "node_id": brG, "pin_name": "Else"})
ex = [{"source_node": brG, "source_pin": "Else", "target_node": tm["tk0"], "target_pin": "execute"},
      {"source_node": tm["tk0"], "source_pin": "then", "target_node": tm["br0"], "target_pin": "execute"}]
for k in range(4):
    ex.append({"source_node": tm["br%d" % k], "source_pin": "then", "target_node": tm["k%d" % k], "target_pin": "execute"})
    nxt = tm["br%d" % (k + 1)] if k < 3 else tm["kEnd"]
    ex.append({"source_node": tm["k%d" % k], "source_pin": "then", "target_node": nxt, "target_pin": "execute"})
    ex.append({"source_node": tm["br%d" % k], "source_pin": "else", "target_node": nxt, "target_pin": "execute"})
for c in conns:
    c["source_node"] = tm.get(c["source_node"], c["source_node"])
    c["target_node"] = tm.get(c["target_node"], c["target_node"])
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": conns + ex})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
print("links: %d req %d fail" % (len(conns) + len(ex), len(fails)))
for f in fails[:10]:
    print("  FAIL:", json.dumps(f, ensure_ascii=False)[:180])

# ── 4) 컴파일 ──
r = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
print("compile:", json.dumps(r, ensure_ascii=False)[:200])
