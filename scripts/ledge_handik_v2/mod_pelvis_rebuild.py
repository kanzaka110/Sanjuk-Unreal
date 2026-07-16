# BakePelvisSpring 재구축 v2 — 배열/와일드카드 제거 (컴파일러가 와일드카드 링크 정리하는 함정 회피)
# 2패스: 패스1=max속도, 패스2=엔벨로프+프레임별 AddFloatCurveKey 직접 쓰기. 스크래치=PsMax/PsPrev/PsPrevPos
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeHandIK"
FN = "BakePelvisSpring"
CURVE = "ledge_pelvis_spring"
KML = "KismetMathLibrary"
ABL = "AnimationBlueprintLibrary"


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


gf = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
entry = [n["id"] for n in gf["nodes"] if "FunctionEntry" in n.get("class", "")][0]

nodes, defaults, conns = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(nid, pin, val):
    defaults.append({"node_id": nid, "pin_name": pin, "value": val})


# ── 메타 (퓨어) ──
N("nf", "CallFunction", 100, 400, function_name="GetNumFrames", target_class=ABL)
N("dur", "CallFunction", 100, 500, function_name="GetSequenceLength", target_class=ABL)
N("nf_f", "CallFunction", 280, 400, function_name="Conv_IntToDouble", target_class=KML)
C("nf", "NumFrames", "nf_f", "InInt")
N("fps", "CallFunction", 460, 430, function_name="Divide_DoubleDouble", target_class=KML)
C("nf_f", "ReturnValue", "fps", "A")
C("dur", "Length", "fps", "B")
N("step", "CallFunction", 460, 530, function_name="Divide_DoubleDouble", target_class=KML)
C("dur", "Length", "step", "A")
C("nf_f", "ReturnValue", "step", "B")
N("ffmax", "CallFunction", 100, 650, function_name="Max", target_class=KML)
N("g_ff", "VariableGet", 100, 750, variable_name="PelvisFallFrames")
C("g_ff", "PelvisFallFrames", "ffmax", "A")
D("ffmax", "B", "1")
N("ff_f", "CallFunction", 280, 650, function_name="Conv_IntToDouble", target_class=KML)
C("ffmax", "ReturnValue", "ff_f", "InInt")
N("fall", "CallFunction", 460, 650, function_name="Divide_DoubleDouble", target_class=KML)
D("fall", "A", "1.0")
C("ff_f", "ReturnValue", "fall", "B")
# ── 리셋 + 커브 준비 ──
N("setMax0", "VariableSet", 200, 0, variable_name="PsMax")
N("setPrev0", "VariableSet", 380, 0, variable_name="PsPrev")
N("exG", "CallFunction", 560, 0, function_name="DoesCurveExist", target_class=ABL)
D("exG", "CurveName", CURVE)
N("brEx", "Branch", 740, 0)
C("exG", "ReturnValue", "brEx", "Condition")
N("rmC", "CallFunction", 920, -100, function_name="RemoveCurve", target_class=ABL)
D("rmC", "CurveName", CURVE)
N("addC", "CallFunction", 1100, 0, function_name="AddCurve", target_class=ABL)
D("addC", "CurveName", CURVE)
# ── 패스1: max 속도 ──
N("loop1", "ForLoop", 1350, 0)
D("loop1", "FirstIndex", "0")
C("nf", "NumFrames", "loop1", "LastIndex")
N("i1f", "CallFunction", 1350, 300, function_name="Conv_IntToDouble", target_class=KML)
C("loop1", "Index", "i1f", "InInt")
N("t1", "CallFunction", 1520, 300, function_name="Multiply_DoubleDouble", target_class=KML)
C("i1f", "ReturnValue", "t1", "A")
C("step", "ReturnValue", "t1", "B")
N("pose1", "CallFunction", 1700, 100, function_name="GetAnimPoseAtTime", target_class="AnimPoseExtensions")
C("t1", "ReturnValue", "pose1", "Time")
N("bone1", "CallFunction", 1880, 300, function_name="GetBonePose", target_class="AnimPoseExtensions")
D("bone1", "BoneName", "pelvis")
D("bone1", "Space", "World")
C("pose1", "Pose", "bone1", "Pose")
N("bt1", "CallFunction", 2060, 300, function_name="BreakTransform", target_class=KML)
C("bone1", "ReturnValue", "bt1", "InTransform")
N("g_pp1", "VariableGet", 2060, 450, variable_name="PsPrevPos")
N("dist1", "CallFunction", 2240, 350, function_name="Vector_Distance", target_class=KML)
C("bt1", "Location", "dist1", "V1")
C("g_pp1", "PsPrevPos", "dist1", "V2")
N("spd1", "CallFunction", 2420, 350, function_name="Multiply_DoubleDouble", target_class=KML)
C("dist1", "ReturnValue", "spd1", "A")
C("fps", "ReturnValue", "spd1", "B")
N("gz1", "CallFunction", 2060, 200, function_name="Greater_IntInt", target_class=KML)
C("loop1", "Index", "gz1", "A")
D("gz1", "B", "0")
N("br1", "Branch", 2240, 100)
C("gz1", "ReturnValue", "br1", "Condition")
N("mx1", "CallFunction", 2600, 350, function_name="FMax", target_class=KML)
N("g_max1", "VariableGet", 2600, 480, variable_name="PsMax")
C("g_max1", "PsMax", "mx1", "A")
C("spd1", "ReturnValue", "mx1", "B")
N("setMaxN", "VariableSet", 2600, 100, variable_name="PsMax")
C("mx1", "ReturnValue", "setMaxN", "PsMax")
N("setPP1", "VariableSet", 2800, 100, variable_name="PsPrevPos")
C("bt1", "Location", "setPP1", "PsPrevPos")
# ── 가드 ──
N("brG", "Branch", 3050, 0)
N("less", "CallFunction", 3050, 200, function_name="Less_DoubleDouble", target_class=KML)
N("g_max2", "VariableGet", 3050, 320, variable_name="PsMax")
N("g_min", "VariableGet", 3050, 410, variable_name="PelvisMinSpeed")
C("g_max2", "PsMax", "less", "A")
C("g_min", "PelvisMinSpeed", "less", "B")
C("less", "ReturnValue", "brG", "Condition")
N("key00", "CallFunction", 3250, -120, function_name="AddFloatCurveKey", target_class=ABL)
D("key00", "CurveName", CURVE)
D("key00", "Time", "0.0")
D("key00", "Value", "0.0")
# ── 패스2: 엔벨로프 + 키 ──
N("loop2", "ForLoop", 3300, 100)
D("loop2", "FirstIndex", "0")
C("nf", "NumFrames", "loop2", "LastIndex")
N("i2f", "CallFunction", 3300, 400, function_name="Conv_IntToDouble", target_class=KML)
C("loop2", "Index", "i2f", "InInt")
N("t2", "CallFunction", 3470, 400, function_name="Multiply_DoubleDouble", target_class=KML)
C("i2f", "ReturnValue", "t2", "A")
C("step", "ReturnValue", "t2", "B")
N("pose2", "CallFunction", 3650, 200, function_name="GetAnimPoseAtTime", target_class="AnimPoseExtensions")
C("t2", "ReturnValue", "pose2", "Time")
N("bone2", "CallFunction", 3830, 400, function_name="GetBonePose", target_class="AnimPoseExtensions")
D("bone2", "BoneName", "pelvis")
D("bone2", "Space", "World")
C("pose2", "Pose", "bone2", "Pose")
N("bt2", "CallFunction", 4010, 400, function_name="BreakTransform", target_class=KML)
C("bone2", "ReturnValue", "bt2", "InTransform")
N("g_pp2", "VariableGet", 4010, 550, variable_name="PsPrevPos")
N("dist2", "CallFunction", 4190, 450, function_name="Vector_Distance", target_class=KML)
C("bt2", "Location", "dist2", "V1")
C("g_pp2", "PsPrevPos", "dist2", "V2")
N("spd2", "CallFunction", 4370, 450, function_name="Multiply_DoubleDouble", target_class=KML)
C("dist2", "ReturnValue", "spd2", "A")
C("fps", "ReturnValue", "spd2", "B")
N("vv", "CallFunction", 4550, 450, function_name="Divide_DoubleDouble", target_class=KML)
C("spd2", "ReturnValue", "vv", "A")
N("g_max3", "VariableGet", 4550, 570, variable_name="PsMax")
C("g_max3", "PsMax", "vv", "B")
N("g_prev1", "VariableGet", 4730, 570, variable_name="PsPrev")
N("gtv", "CallFunction", 4730, 380, function_name="Greater_DoubleDouble", target_class=KML)
C("vv", "ReturnValue", "gtv", "A")
C("g_prev1", "PsPrev", "gtv", "B")
N("pf", "CallFunction", 4730, 480, function_name="Subtract_DoubleDouble", target_class=KML)
C("g_prev1", "PsPrev", "pf", "A")
C("fall", "ReturnValue", "pf", "B")
N("mxvf", "CallFunction", 4910, 480, function_name="FMax", target_class=KML)
C("vv", "ReturnValue", "mxvf", "A")
C("pf", "ReturnValue", "mxvf", "B")
N("selp", "CallFunction", 5090, 380, function_name="SelectFloat", target_class=KML)
C("vv", "ReturnValue", "selp", "A")
C("mxvf", "ReturnValue", "selp", "B")
C("gtv", "ReturnValue", "selp", "bPickA")
N("gz2", "CallFunction", 3650, 100, function_name="Greater_IntInt", target_class=KML)
C("loop2", "Index", "gz2", "A")
D("gz2", "B", "0")
N("br2", "Branch", 3830, 100)
C("gz2", "ReturnValue", "br2", "Condition")
N("setPrevN", "VariableSet", 5090, 100, variable_name="PsPrev")
C("selp", "ReturnValue", "setPrevN", "PsPrev")
N("g_prev2", "VariableGet", 5270, 300, variable_name="PsPrev")
N("keyN", "CallFunction", 5270, 100, function_name="AddFloatCurveKey", target_class=ABL)
D("keyN", "CurveName", CURVE)
C("t2", "ReturnValue", "keyN", "Time")
C("g_prev2", "PsPrev", "keyN", "Value")
# frame1에서 (0, env) 키도 (python speeds[0]=speeds[1] 재현)
N("eq1", "CallFunction", 5450, 300, function_name="EqualEqual_IntInt", target_class=KML)
C("loop2", "Index", "eq1", "A")
D("eq1", "B", "1")
N("br3", "Branch", 5450, 100)
C("eq1", "ReturnValue", "br3", "Condition")
N("key0e", "CallFunction", 5630, 20, function_name="AddFloatCurveKey", target_class=ABL)
D("key0e", "CurveName", CURVE)
D("key0e", "Time", "0.0")
C("g_prev2", "PsPrev", "key0e", "Value")
N("setPP2", "VariableSet", 5850, 100, variable_name="PsPrevPos")
C("bt2", "Location", "setPP2", "PsPrevPos")
# Seq 연결
for t in ("nf", "dur", "pose1", "pose2", "exG", "rmC", "addC", "key00", "keyN", "key0e"):
    C(entry, "Seq", t, "AnimationSequenceBase")

res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": FN, "nodes": nodes})
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
harvest(res)
if len(tm) != len(nodes):
    made = set(tm)
    raise SystemExit("노드 %d/%d missing=%s" % (len(tm), len(nodes), [n["temp_id"] for n in nodes if n["temp_id"] not in made]))
for d in defaults:
    d["node_id"] = tm.get(d["node_id"], d["node_id"])
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": FN, "defaults": defaults})
dfails = [x for x in (rd.get("results") or []) if not x.get("success", True)]
print("defaults fails:", dfails if dfails else 0)
for c in conns:
    c["source_node"] = tm.get(c["source_node"], c["source_node"])
    c["target_node"] = tm.get(c["target_node"], c["target_node"])
ex = []
def E(a, ap, b, tp="execute"):
    ex.append({"source_node": tm.get(a, a), "source_pin": ap, "target_node": tm.get(b, b), "target_pin": tp})
E(entry, "then", "setMax0"); E("setMax0", "then", "setPrev0"); E("setPrev0", "then", "exG")
E("exG", "then", "brEx"); E("brEx", "then", "rmC"); E("rmC", "then", "addC"); E("brEx", "else", "addC")
E("addC", "then", "loop1")
E("loop1", "LoopBody", "pose1"); E("pose1", "then", "br1")
E("br1", "then", "setMaxN"); E("setMaxN", "then", "setPP1"); E("br1", "else", "setPP1")
E("loop1", "Completed", "brG")
E("brG", "then", "key00")
E("brG", "else", "loop2")
E("loop2", "LoopBody", "pose2"); E("pose2", "then", "br2")
E("br2", "then", "setPrevN"); E("setPrevN", "then", "keyN"); E("keyN", "then", "br3")
E("br3", "then", "key0e"); E("key0e", "then", "setPP2"); E("br3", "else", "setPP2")
E("br2", "else", "setPP2")
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": conns + ex})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
print("links: %d req %d fail" % (len(conns) + len(ex), len(fails)))
for f in fails[:10]:
    print("  FAIL:", json.dumps(f, ensure_ascii=False)[:180])
