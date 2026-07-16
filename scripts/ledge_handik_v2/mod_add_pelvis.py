# AM_SBLedgeHandIK에 ledge_pelvis_spring 베이크 통합 (v9.9)
# 레거시 파이썬 코어의 샘플링 엔벨로프를 네이티브 함수 BakePelvisSpring으로 이식:
#   펠비스 월드속도 프레임샘플 -> max 정규화 -> 상승 즉시/하강 1/FallFrames 스텝, max<MinSpeed면 0
# 신규 파라미터: PelvisMinSpeed(60)/PelvisFallFrames(6). 스크래치는 멤버변수(Ps*) — 함수 시작 시 Clear
# 콜사이트: OnApply 전처리 제거체인 꼬리 -> BakePelvisSpring -> 모드분기 (전 모드 공통)
# OnRevert: 펠비스 커브 제거 세그먼트 추가
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeHandIK"
FN = "BakePelvisSpring"
CURVE = "ledge_pelvis_spring"
KML = "KismetMathLibrary"
KAL = "KismetArrayLibrary"
ABL = "AnimationBlueprintLibrary"
LOG = {"steps": [], "errors": []}


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


def harvest(o, tm):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tm[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v, tm)
    elif isinstance(o, list):
        for e in o:
            harvest(e, tm)


# ── 1) 변수 ──
VARS = [
    ("PelvisMinSpeed", "float", "60.0", True, "Pelvis Spring"),
    ("PelvisFallFrames", "int", "6", True, "Pelvis Spring"),
    ("PsPositions", "array:struct:Vector", None, False, "Internal"),
    ("PsSpeeds", "array:float", None, False, "Internal"),
    ("PsTimes", "array:float", None, False, "Internal"),
    ("PsValues", "array:float", None, False, "Internal"),
    ("PsMax", "float", None, False, "Internal"),
    ("PsPrev", "float", None, False, "Internal"),
]
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
for name, typ, dv, edit, cat in VARS:
    if name in existing:
        continue
    p = {"asset_path": BP, "name": name, "type": typ, "category": cat, "instance_editable": edit}
    if dv:
        p["default_value"] = dv
    call("blueprint_query", "add_variable", p)
    LOG["steps"].append("var: " + name)

# ── 2) 함수 생성 + 파라미터 ──
graphs = [str(x.get("name", x) if isinstance(x, dict) else x) for x in call("blueprint_query", "list_graphs", {"asset_path": BP}).get("graphs", [])]
if FN not in graphs:
    call("blueprint_query", "add_function", {"asset_path": BP, "name": FN})
    call("blueprint_query", "set_function_params",
         {"asset_path": BP, "function_name": FN,
          "inputs": [{"name": "Seq", "type": "object:AnimSequenceBase"}]})
    LOG["steps"].append("function created")
gf = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
entry = None
for n in gf["nodes"]:
    if "FunctionEntry" in n.get("class", ""):
        entry = n["id"]
assert entry, "entry 미발견"

# ── 3) 함수 그래프 빌드 ──
nodes, defaults, conns = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(nid, pin, val):
    defaults.append({"node_id": nid, "pin_name": pin, "value": val})


def GET(tid, var, x, y):
    N(tid, "VariableGet", x, y, variable_name=var)


def SET(tid, var, x, y):
    N(tid, "VariableSet", x, y, variable_name=var)


# 스크래치 리셋
for i, arr in enumerate(("PsPositions", "PsSpeeds", "PsTimes", "PsValues")):
    N("clr%d" % i, "CallFunction", 200 + i * 180, 0, function_name="Array_Clear", target_class=KAL)
    GET("g_clr%d" % i, arr, 200 + i * 180, 120)
    C("g_clr%d" % i, arr, "clr%d" % i, "TargetArray")
SET("set_max0", "PsMax", 950, 0)
SET("set_prev0", "PsPrev", 1120, 0)
# 시퀀스 메타 (퓨어)
N("nf", "CallFunction", 200, 300, function_name="GetNumFrames", target_class=ABL)
N("dur", "CallFunction", 200, 400, function_name="GetSequenceLength", target_class=ABL)
N("nf_f", "CallFunction", 380, 300, function_name="Conv_IntToDouble", target_class=KML)
C("nf", "NumFrames", "nf_f", "InInt")
N("fps", "CallFunction", 560, 340, function_name="Divide_DoubleDouble", target_class=KML)
C("nf_f", "ReturnValue", "fps", "A")
C("dur", "Length", "fps", "B")
N("step", "CallFunction", 560, 440, function_name="Divide_DoubleDouble", target_class=KML)
C("dur", "Length", "step", "A")
C("nf_f", "ReturnValue", "step", "B")
# 루프1: 0..NumFrames — 포즈 샘플 -> PsPositions
N("loop1", "ForLoop", 1300, 0)
D("loop1", "FirstIndex", "0")
C("nf", "NumFrames", "loop1", "LastIndex")
N("idx1_f", "CallFunction", 1300, 250, function_name="Conv_IntToDouble", target_class=KML)
C("loop1", "Index", "idx1_f", "InInt")
N("t1", "CallFunction", 1480, 250, function_name="Multiply_DoubleDouble", target_class=KML)
C("idx1_f", "ReturnValue", "t1", "A")
C("step", "ReturnValue", "t1", "B")
N("poseAt", "CallFunction", 1650, 100, function_name="GetAnimPoseAtTime", target_class="AnimPoseExtensions")
C("t1", "ReturnValue", "poseAt", "Time")
N("bonePose", "CallFunction", 1850, 250, function_name="GetBonePose", target_class="AnimPoseExtensions")
D("bonePose", "Bone", "pelvis")
D("bonePose", "Space", "World")
C("poseAt", "Pose", "bonePose", "Pose")
N("loc", "CallFunction", 2030, 250, function_name="Conv_TransformToVector", target_class=KML)
N("addPos", "CallFunction", 2050, 100, function_name="Array_Add", target_class=KAL)
GET("g_pos1", "PsPositions", 2050, 400)
C("g_pos1", "PsPositions", "addPos", "TargetArray")
# 루프2: 1..NumFrames — 속도 + max
N("loop2", "ForLoop", 2500, 0)
D("loop2", "FirstIndex", "1")
C("nf", "NumFrames", "loop2", "LastIndex")
GET("g_pos2", "PsPositions", 2500, 500)
N("getA", "CallFunction", 2680, 300, function_name="Array_Get", target_class=KAL)
N("getB", "CallFunction", 2680, 430, function_name="Array_Get", target_class=KAL)
C("g_pos2", "PsPositions", "getA", "TargetArray")
C("g_pos2", "PsPositions", "getB", "TargetArray")
C("loop2", "Index", "getA", "Index")
N("im1", "CallFunction", 2500, 380, function_name="Subtract_IntInt", target_class=KML)
C("loop2", "Index", "im1", "A")
D("im1", "B", "1")
C("im1", "ReturnValue", "getB", "Index")
N("dist2", "CallFunction", 2880, 350, function_name="Vector_Distance", target_class=KML)
C("getA", "Item", "dist2", "V1")
C("getB", "Item", "dist2", "V2")
N("spd", "CallFunction", 3060, 350, function_name="Multiply_DoubleDouble", target_class=KML)
C("dist2", "ReturnValue", "spd", "A")
C("fps", "ReturnValue", "spd", "B")
N("addSpd", "CallFunction", 2900, 100, function_name="Array_Add", target_class=KAL)
GET("g_spd1", "PsSpeeds", 2900, 550)
C("g_spd1", "PsSpeeds", "addSpd", "TargetArray")
C("spd", "ReturnValue", "addSpd", "NewItem")
N("mx", "CallFunction", 3200, 350, function_name="FMax", target_class=KML)
GET("g_max1", "PsMax", 3200, 480)
C("g_max1", "PsMax", "mx", "A")
C("spd", "ReturnValue", "mx", "B")
SET("set_max", "PsMax", 3150, 100)
C("mx", "ReturnValue", "set_max", "PsMax")
# 루프2 후: speeds[0] 복제 삽입
N("ins0", "CallFunction", 3600, 0, function_name="Array_Insert", target_class=KAL)
GET("g_spd2", "PsSpeeds", 3600, 250)
N("get0", "CallFunction", 3600, 380, function_name="Array_Get", target_class=KAL)
C("g_spd2", "PsSpeeds", "ins0", "TargetArray")
C("g_spd2", "PsSpeeds", "get0", "TargetArray")
D("get0", "Index", "0")
C("get0", "Item", "ins0", "NewItem")
D("ins0", "Index", "0")
# 가드 분기: PsMax < PelvisMinSpeed
N("less", "CallFunction", 3850, 250, function_name="Less_DoubleDouble", target_class=KML)
GET("g_max2", "PsMax", 3850, 380)
GET("g_min", "PelvisMinSpeed", 3850, 470)
C("g_max2", "PsMax", "less", "A")
C("g_min", "PelvisMinSpeed", "less", "B")
N("guard", "Branch", 3850, 0)
C("less", "ReturnValue", "guard", "Condition")
# TRUE(아이들): (0,0) 단일키
N("addT0", "CallFunction", 4050, -150, function_name="Array_Add", target_class=KAL)
N("addV0", "CallFunction", 4250, -150, function_name="Array_Add", target_class=KAL)
GET("g_t0", "PsTimes", 4050, -20)
GET("g_v0", "PsValues", 4250, -20)
C("g_t0", "PsTimes", "addT0", "TargetArray")
C("g_v0", "PsValues", "addV0", "TargetArray")
D("addT0", "NewItem", "0.0")
D("addV0", "NewItem", "0.0")
# FALSE: 엔벨로프 루프 (ForEach PsSpeeds)
N("loop3", "ForEachLoop", 4100, 200)
GET("g_spd3", "PsSpeeds", 4100, 400)
C("g_spd3", "PsSpeeds", "loop3", "Array")
# fall = 1 / max(1, FallFrames)
GET("g_ff", "PelvisFallFrames", 4100, 500)
N("ffmax", "CallFunction", 4280, 500, function_name="Max", target_class=KML)
C("g_ff", "PelvisFallFrames", "ffmax", "A")
D("ffmax", "B", "1")
N("ff_f", "CallFunction", 4450, 500, function_name="Conv_IntToDouble", target_class=KML)
C("ffmax", "ReturnValue", "ff_f", "InInt")
N("fall", "CallFunction", 4620, 500, function_name="Divide_DoubleDouble", target_class=KML)
D("fall", "A", "1.0")
C("ff_f", "ReturnValue", "fall", "B")
# v = spd / PsMax
N("vv", "CallFunction", 4450, 300, function_name="Divide_DoubleDouble", target_class=KML)
C("loop3", "Array Element", "vv", "A")
GET("g_max3", "PsMax", 4450, 400)
C("g_max3", "PsMax", "vv", "B")
# prev' = v>prev ? v : max(v, prev-fall)
GET("g_prev1", "PsPrev", 4620, 380)
N("gtv", "CallFunction", 4800, 300, function_name="Greater_DoubleDouble", target_class=KML)
C("vv", "ReturnValue", "gtv", "A")
C("g_prev1", "PsPrev", "gtv", "B")
N("pf", "CallFunction", 4800, 440, function_name="Subtract_DoubleDouble", target_class=KML)
C("g_prev1", "PsPrev", "pf", "A")
C("fall", "ReturnValue", "pf", "B")
N("mxvf", "CallFunction", 4980, 440, function_name="FMax", target_class=KML)
C("vv", "ReturnValue", "mxvf", "A")
C("pf", "ReturnValue", "mxvf", "B")
N("selp", "CallFunction", 5160, 300, function_name="SelectFloat", target_class=KML)
C("vv", "ReturnValue", "selp", "A")
C("mxvf", "ReturnValue", "selp", "B")
C("gtv", "ReturnValue", "selp", "bPickA")
SET("set_prev", "PsPrev", 5340, 150)
C("selp", "ReturnValue", "set_prev", "PsPrev")
N("addV", "CallFunction", 5520, 150, function_name="Array_Add", target_class=KAL)
GET("g_v1", "PsValues", 5520, 300)
GET("g_prev2", "PsPrev", 5520, 400)
C("g_v1", "PsValues", "addV", "TargetArray")
C("g_prev2", "PsPrev", "addV", "NewItem")
N("idx3_f", "CallFunction", 5520, 500, function_name="Conv_IntToDouble", target_class=KML)
C("loop3", "Array Index", "idx3_f", "InInt")
N("tt", "CallFunction", 5700, 400, function_name="Divide_DoubleDouble", target_class=KML)
C("idx3_f", "ReturnValue", "tt", "A")
C("fps", "ReturnValue", "tt", "B")
N("addT", "CallFunction", 5700, 150, function_name="Array_Add", target_class=KAL)
GET("g_t1", "PsTimes", 5700, 550)
C("g_t1", "PsTimes", "addT", "TargetArray")
C("tt", "ReturnValue", "addT", "NewItem")
# 커브 쓰기: exists->remove -> add -> keys
N("exG", "CallFunction", 6000, 0, function_name="DoesCurveExist", target_class=ABL)
D("exG", "CurveName", CURVE)
N("brEx", "Branch", 6200, 0)
C("exG", "ReturnValue", "brEx", "Condition")
N("rmC", "CallFunction", 6400, -100, function_name="RemoveCurve", target_class=ABL)
D("rmC", "CurveName", CURVE)
N("addC", "CallFunction", 6600, 0, function_name="AddCurve", target_class=ABL)
D("addC", "CurveName", CURVE)
N("keys", "CallFunction", 6800, 0, function_name="AddFloatCurveKeys", target_class=ABL)
D("keys", "CurveName", CURVE)
GET("g_t2", "PsTimes", 6800, 200)
GET("g_v2", "PsValues", 6800, 300)
C("g_t2", "PsTimes", "keys", "Times")
C("g_v2", "PsValues", "keys", "Values")
# Seq 연결 (엔트리 파라미터)
for t in ("nf", "dur", "poseAt", "exG", "rmC", "addC", "keys"):
    C(entry, "Seq", t, "AnimationSequenceBase" if t != "poseAt" else "AnimationSequenceBase")

res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": FN, "nodes": nodes})
tm = {}
harvest(res, tm)
if len(tm) != len(nodes):
    raise SystemExit("노드 %d/%d: %s" % (len(tm), len(nodes), json.dumps(res)[:400]))
LOG["steps"].append("fn nodes: %d" % len(tm))
for d in defaults:
    d["node_id"] = tm.get(d["node_id"], d["node_id"])
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": FN, "defaults": defaults})
dfails = [x for x in (rd.get("results") or []) if not x.get("success", True)]
if dfails:
    LOG["errors"].append({"defaults": dfails})
# exec 체인
ex = []
def E(a, ap, b):
    ex.append({"source_node": a, "source_pin": ap, "target_node": b, "target_pin": "execute"})
E(entry, "then", tm["clr0"]); E(tm["clr0"], "then", tm["clr1"]); E(tm["clr1"], "then", tm["clr2"])
E(tm["clr2"], "then", tm["clr3"]); E(tm["clr3"], "then", tm["set_max0"]); E(tm["set_max0"], "then", tm["set_prev0"])
E(tm["set_prev0"], "then", tm["loop1"])
E(tm["loop1"], "LoopBody", tm["poseAt"]); E(tm["poseAt"], "then", tm["addPos"])
E(tm["loop1"], "Completed", tm["loop2"])
E(tm["loop2"], "LoopBody", tm["addSpd"]); E(tm["addSpd"], "then", tm["set_max"])
E(tm["loop2"], "Completed", tm["ins0"])
E(tm["ins0"], "then", tm["guard"])
E(tm["guard"], "then", tm["addT0"]); E(tm["addT0"], "then", tm["addV0"]); E(tm["addV0"], "then", tm["exG"])
E(tm["guard"], "else", tm["loop3"])
E(tm["loop3"], "LoopBody", tm["set_prev"]); E(tm["set_prev"], "then", tm["addV"]); E(tm["addV"], "then", tm["addT"])
E(tm["loop3"], "Completed", tm["exG"])
E(tm["exG"], "then", tm["brEx"])
E(tm["brEx"], "then", tm["rmC"]); E(tm["rmC"], "then", tm["addC"])
E(tm["brEx"], "else", tm["addC"])
E(tm["addC"], "then", tm["keys"])
# 데이터 (배열핀 우선 배치된 conns) + 나머지
for c in conns:
    c["source_node"] = tm.get(c["source_node"], c["source_node"])
    c["target_node"] = tm.get(c["target_node"], c["target_node"])
c1 = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": conns + ex})
fails = [x for x in (c1.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"fn_conns": fails})
LOG["steps"].append("fn links: %d req %d fail" % (len(conns) + len(ex), len(fails)))

# ── 4) OnApply 콜사이트: 전처리 꼬리 -> Bake -> 모드분기 / OnRevert: 펠비스 제거 세그 ──
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": "EventGraph"})
nodes_e = {n["id"]: n for n in g["nodes"]}
def pins_e(n): return {p["name"]: p for p in n.get("pins", [])}
def conn_e(n, pin): return (pins_e(n).get(pin, {}).get("connected_to") or [])
# 전처리 마지막 발 세그(frm: RemoveCurve ledge_foot_move_r) + BR_EXIT + 리버트 꼬리
br_exit = None
pre_tails = []   # (node,pin) -> BR_EXIT.execute
rev_tails = []   # 리버트 열린 꼬리
for nid, n in nodes_e.items():
    if "IfThenElse" in n.get("class", ""):
        cond = (conn_e(n, "Condition") or [""])[0]
        if "CommutativeAssociativeBinaryOperator" in cond:
            br_exit = nid
assert br_exit, "br_exit 미발견"
for p in pins_e(nodes_e[br_exit]).get("execute", {}).get("connected_to") or []:
    pre_tails.append((p.split(".")[0], p.split(".")[1]))
# 리버트: ledge_foot_move_r 제거 세그의 rm.then / br.else (연결 없는 꼬리)
for nid, n in nodes_e.items():
    t = (n.get("title") or "")
    P = pins_e(n)
    if t.startswith("Remove Curve") and P.get("CurveName", {}).get("default_value") == "ledge_foot_move_r":
        if not conn_e(n, "then"):
            rev_tails.append((nid, "then"))
    if "IfThenElse" in n.get("class", ""):
        cond = (conn_e(n, "Condition") or [""])[0]
        src = nodes_e.get(cond.split(".")[0], {})
        if pins_e(src).get("CurveName", {}).get("default_value") == "ledge_foot_move_r" and not conn_e(n, "else"):
            rev_tails.append((nid, "else"))
LOG["steps"].append("pre_tails=%s rev_tails=%s" % (pre_tails, rev_tails))
spec2 = [
    {"temp_id": "callBake", "node_type": "CallFunction", "function_name": FN, "position": [2200, 1650]},
    {"temp_id": "rex4", "node_type": "CallFunction", "function_name": "DoesCurveExist", "target_class": ABL, "position": [2300, 2900]},
    {"temp_id": "rbr4", "node_type": "Branch", "position": [2450, 2900]},
    {"temp_id": "rrm4", "node_type": "CallFunction", "function_name": "RemoveCurve", "target_class": ABL, "position": [2600, 2850]},
]
tm2 = {}
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": "EventGraph", "nodes": spec2})
harvest(res, tm2)
assert len(tm2) == 4, res
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": "EventGraph", "defaults": [
    {"node_id": tm2["rex4"], "pin_name": "CurveName", "value": CURVE},
    {"node_id": tm2["rrm4"], "pin_name": "CurveName", "value": CURVE},
]})
cs = []
for a, p in pre_tails:
    call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": "EventGraph", "node_id": a, "pin_name": p})
    cs.append({"source_node": a, "source_pin": p, "target_node": tm2["callBake"], "target_pin": "execute"})
cs += [
    {"source_node": tm2["callBake"], "source_pin": "then", "target_node": br_exit, "target_pin": "execute"},
    {"source_node": "K2Node_Event_0", "source_pin": "AnimationSequence", "target_node": tm2["callBake"], "target_pin": "Seq"},
    {"source_node": "K2Node_Event_1", "source_pin": "AnimationSequence", "target_node": tm2["rex4"], "target_pin": "AnimationSequenceBase"},
    {"source_node": "K2Node_Event_1", "source_pin": "AnimationSequence", "target_node": tm2["rrm4"], "target_pin": "AnimationSequenceBase"},
    {"source_node": tm2["rex4"], "source_pin": "ReturnValue", "target_node": tm2["rbr4"], "target_pin": "Condition"},
    {"source_node": tm2["rex4"], "source_pin": "then", "target_node": tm2["rbr4"], "target_pin": "execute"},
    {"source_node": tm2["rbr4"], "source_pin": "then", "target_node": tm2["rrm4"], "target_pin": "execute"},
]
for a, p in rev_tails:
    cs.append({"source_node": a, "source_pin": p, "target_node": tm2["rex4"], "target_pin": "execute"})
c2 = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": "EventGraph", "connections": cs})
fails2 = [x for x in (c2.get("results") or []) if not x.get("success", True)]
if fails2:
    LOG["errors"].append({"splice": fails2})
LOG["steps"].append("splice: %d req %d fail" % (len(cs), len(fails2)))

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_pelvis.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("MOD_PELVIS_DONE errors=%s" % ("none" if not LOG["errors"] else json.dumps(LOG["errors"])[:400]))
