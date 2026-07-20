# AM_SBLedgeIK v10 — 2차 릴리즈 창 (다중 스윙 애님 대응)
# 배경: Crossing_Far 계열 등 긴 애님은 한 클립 안에서 손/발이 2회 스윙하는데
#       모디파이어가 본당 창 1개만 지원 → 2번째 스윙 때 IK가 이미 재고정 = "발이 붙잡힘" (2026-07-20 유저 리포트)
# 설계: **IK 알파 커브에만** 2차 릴리즈 창 추가. move(타깃 lerp) 커브는 1창 유지
#       — move를 두 번 리셋하면 Anchor/Dest 재래치와 어긋나 그립 점프 위험
# 파라미터(인스턴스, 기본 0=비활성): Hand/FootMove2Start·End × L/R
# 키 패턴(창1과 동일): (S2-Release,1) (S2,0) (E2,0) (E2+Plant,1)
# ⚠ 배열 금지(Kismet 와일드카드 RPC 함정) — 스칼라 파라미터 8개로 평면 구성
# ⚠ 로컬 python 전용
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeIK"
G = "WriteMoveCurves"
KML = "KismetMathLibrary"
ABL = "AnimationBlueprintLibrary"
ENTRY = "K2Node_FunctionEntry_0"
TAIL = "K2Node_CallFunction_47"
LIMBS = [("HandMove2StartL", "HandMove2EndL", "ledge_hand_ik_l", 6000),
         ("HandMove2StartR", "HandMove2EndR", "ledge_hand_ik_r", 6400),
         ("FootMove2StartL", "FootMove2EndL", "ledge_foot_ik_l", 6800),
         ("FootMove2StartR", "FootMove2EndR", "ledge_foot_ik_r", 7200)]


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


existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
for s, e, _, _ in LIMBS:
    for nm in (s, e):
        if nm not in existing:
            call("blueprint_query", "add_variable", {"asset_path": BP, "name": nm, "type": "float",
                                                     "category": "Choreo 2nd Window", "instance_editable": True,
                                                     "default_value": "0.0"})
            print("var+", nm)

nodes, defaults, data = [], [], []


def N(t, nt, x, y, **kw):
    d = {"temp_id": t, "node_type": nt, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    data.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(n, p, v):
    defaults.append({"node_id": n, "pin_name": p, "value": v})


for idx, (ps, pe, curve, y) in enumerate(LIMBS):
    k = "w%d" % idx
    N(k + "gs", "VariableGet", -600, y, variable_name=ps)
    N(k + "ge", "VariableGet", -600, y + 60, variable_name=pe)
    N(k + "gt", "CallFunction", -430, y, function_name="Greater_DoubleDouble", target_class=KML)
    C(k + "ge", pe, k + "gt", "A")
    C(k + "gs", ps, k + "gt", "B")
    N(k + "br", "Branch", -260, y)
    C(k + "gt", "ReturnValue", k + "br", "Condition")
    N(k + "grr", "VariableGet", -600, y + 120, variable_name="ReleaseRampTime")
    N(k + "gpr", "VariableGet", -600, y + 180, variable_name="PlantRampTime")
    N(k + "sub", "CallFunction", -430, y + 120, function_name="Subtract_DoubleDouble", target_class=KML)
    C(k + "gs", ps, k + "sub", "A")
    C(k + "grr", "ReleaseRampTime", k + "sub", "B")
    N(k + "add", "CallFunction", -430, y + 180, function_name="Add_DoubleDouble", target_class=KML)
    C(k + "ge", pe, k + "add", "A")
    C(k + "gpr", "PlantRampTime", k + "add", "B")
    for j, (tsrc, tpin, val) in enumerate(((k + "sub", "ReturnValue", "1.0"),
                                           (k + "gs", ps, "0.0"),
                                           (k + "ge", pe, "0.0"),
                                           (k + "add", "ReturnValue", "1.0"))):
        kn = "%sk%d" % (k, j)
        N(kn, "CallFunction", -80 + 190 * j, y, function_name="AddFloatCurveKey", target_class=ABL)
        D(kn, "CurveName", curve)
        D(kn, "Value", val)
        C(tsrc, tpin, kn, "Time")
        C(ENTRY, "Seq", kn, "AnimationSequenceBase")

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


harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": G, "nodes": nodes}))
if len(tm) != len(nodes):
    raise SystemExit("노드 %d/%d missing=%s" % (len(tm), len(nodes), [n["temp_id"] for n in nodes if n["temp_id"] not in tm]))
for d in defaults:
    d["node_id"] = tm[d["node_id"]]
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": G, "defaults": defaults})
print("defaults fails:", [x for x in (rd.get("results") or []) if not x.get("success", True)] or 0)
for c in data:
    c["source_node"] = tm.get(c["source_node"], c["source_node"])
    c["target_node"] = tm.get(c["target_node"], c["target_node"])

# exec: TAIL → w0br → (then: k0..k3 → w1br) (else: w1br) → ... → w3 끝
ex = []


def E(a, ap, b):
    ex.append({"source_node": tm.get(a, a), "source_pin": ap, "target_node": tm.get(b, b), "target_pin": "execute"})


E(TAIL, "then", "w0br")
for idx in range(len(LIMBS)):
    k = "w%d" % idx
    nxt = "w%dbr" % (idx + 1) if idx + 1 < len(LIMBS) else None
    E(k + "br", "then", k + "k0")
    for j in range(3):
        E("%sk%d" % (k, j), "then", "%sk%d" % (k, j + 1))
    if nxt:
        E("%sk3" % k, "then", nxt)
        E(k + "br", "else", nxt)

for c in data + ex:
    call("blueprint_query", "connect_pins", {"asset_path": BP, "graph_name": G,
                                             "source_node": c["source_node"], "source_pin": c["source_pin"],
                                             "target_node": c["target_node"], "target_pin": c["target_pin"]})
# 전수 검증 (무음 드랍 방지)
ns = {n["id"]: n for n in call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": G})["nodes"]}


def has(a, ap, b):
    n = ns.get(a)
    if not n:
        return False
    for p in n.get("pins", []):
        if p["name"] == ap:
            return any(x.split(".")[0] == b for x in (p.get("connected_to") or []))
    return False


miss = [(c["source_node"], c["source_pin"], c["target_node"]) for c in data + ex
        if not has(c["source_node"], c["source_pin"], c["target_node"])]
print("silent-drop:", miss if miss else "none")
r = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
print("compile:", r.get("success"), "errors:", r.get("error_count"), (r.get("errors") or [])[:3])
if not miss and r.get("success"):
    print("save:", call("editor_query", "save_asset", {"asset_path": BP}).get("saved"))
