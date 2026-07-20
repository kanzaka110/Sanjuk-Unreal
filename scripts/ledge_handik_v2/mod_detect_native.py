# AM_SBLedgeIK v11 — 창 자동검출을 네이티브 BP 노드로 (파이썬 커맨드 폐기)
# 구조: DetectWindow(BoneName, Ratio, PadStart, PadEnd) -> (OutStart, OutEnd)  재사용 함수
#   패스1: 프레임 샘플 → 최대속도/피크시각/평균(스트리밍)
#          ⚠ 배열 금지(Kismet 와일드카드 RPC 함정) → 중앙값 대신 '평균'을 기준선으로 (스트리밍 계산 가능)
#   패스2: thr=base+Ratio*(max-base) 기준으로 피크 이전 마지막 미달시각=start, 이후 최초 미달시각=end
#   가드: max<60 또는 (max-base)<25 → (0,0) = 창 없음 / 길이<0.05 → (0,0)
# AutoDetectCurves: DetectWindow ×4(hand_l/r, ball_l/r) → 파라미터 기록
# ⚠ 로컬 python 전용
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeIK"
FN = "DetectWindow"
KML = "KismetMathLibrary"
ABL = "AnimationBlueprintLibrary"
APE = "AnimPoseExtensions"
LOG = []


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:250])
    return json.loads(txt)


# ── 0) 스크래치 변수 ──
have = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
for nm, ty in (("DwMax", "float"), ("DwSum", "float"), ("DwCount", "float"), ("DwPeakT", "float"),
               ("DwPrevPos", "struct:Vector"), ("DwStart", "float"), ("DwEnd", "float"), ("DwEndSet", "bool")):
    if nm not in have:
        call("blueprint_query", "add_variable", {"asset_path": BP, "name": nm, "type": ty,
                                                 "category": "Internal", "instance_editable": False, "transient": True})
        LOG.append("var+" + nm)

# ── 1) 함수 + 시그니처 ──
graphs = [g.get("name", g) if isinstance(g, dict) else g for g in call("blueprint_query", "list_graphs", {"asset_path": BP}).get("graphs", [])]
if FN not in graphs:
    call("blueprint_query", "add_function", {"asset_path": BP, "name": FN})
call("blueprint_query", "set_function_params", {"asset_path": BP, "function_name": FN,
     "inputs": [{"name": "Seq", "type": "object:AnimSequence"}, {"name": "BoneName", "type": "name"},
                {"name": "Ratio", "type": "float"}, {"name": "PadStart", "type": "float"}, {"name": "PadEnd", "type": "float"}],
     "outputs": [{"name": "OutStart", "type": "float"}, {"name": "OutEnd", "type": "float"}]})
LOG.append("fn " + FN + " signature set")

ns = {n["id"]: n for n in call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})["nodes"]}
entry = [i for i, n in ns.items() if "FunctionEntry" in n["class"]][0]
result = [i for i, n in ns.items() if "FunctionResult" in n["class"]]
result = result[0] if result else None
LOG.append("entry=%s result=%s" % (entry, result))

nodes, defaults, data = [], [], []


def N(t, nt, x, y, **kw):
    d = {"temp_id": t, "node_type": nt, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    data.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(n, p, v):
    defaults.append({"node_id": n, "pin_name": p, "value": v})


# 메타: nf, dur, step
N("nf", "CallFunction", -1200, 600, function_name="GetNumFrames", target_class=ABL)
N("dur", "CallFunction", -1200, 700, function_name="GetSequenceLength", target_class=ABL)
C(entry, "Seq", "nf", "AnimationSequenceBase")
C(entry, "Seq", "dur", "AnimationSequenceBase")
N("nff", "CallFunction", -1000, 600, function_name="Conv_IntToDouble", target_class=KML)
C("nf", "NumFrames", "nff", "InInt")
N("step", "CallFunction", -820, 650, function_name="Divide_DoubleDouble", target_class=KML)
C("dur", "Length", "step", "A")
C("nff", "ReturnValue", "step", "B")

# 리셋
for k, (var, val) in enumerate((("DwMax", "0.0"), ("DwSum", "0.0"), ("DwCount", "0.0"), ("DwPeakT", "0.0"))):
    N("r" + var, "VariableSet", -1000 + 200 * k, 0, variable_name=var)
    D("r" + var, var, val)
N("rpos", "VariableSet", -200, 0, variable_name="DwPrevPos")

# ── 패스1 ──
N("loop1", "ForLoop", 0, 0)
D("loop1", "FirstIndex", "0")
C("nf", "NumFrames", "loop1", "LastIndex")
N("i1", "CallFunction", 0, 300, function_name="Conv_IntToDouble", target_class=KML)
C("loop1", "Index", "i1", "InInt")
N("t1", "CallFunction", 180, 300, function_name="Multiply_DoubleDouble", target_class=KML)
C("i1", "ReturnValue", "t1", "A")
C("step", "ReturnValue", "t1", "B")
N("pose1", "CallFunction", 360, 100, function_name="GetAnimPoseAtTime", target_class=APE)
C(entry, "Seq", "pose1", "AnimationSequenceBase")
C("t1", "ReturnValue", "pose1", "Time")
N("bone1", "CallFunction", 540, 300, function_name="GetBonePose", target_class=APE)
C("pose1", "Pose", "bone1", "Pose")
C(entry, "BoneName", "bone1", "BoneName")
D("bone1", "Space", "World")
N("bt1", "CallFunction", 720, 300, function_name="BreakTransform", target_class=KML)
C("bone1", "ReturnValue", "bt1", "InTransform")
N("gp1", "VariableGet", 720, 450, variable_name="DwPrevPos")
N("d1", "CallFunction", 900, 350, function_name="Vector_Distance", target_class=KML)
C("bt1", "Location", "d1", "V1")
C("gp1", "DwPrevPos", "d1", "V2")
N("sp1", "CallFunction", 1080, 350, function_name="Divide_DoubleDouble", target_class=KML)
C("d1", "ReturnValue", "sp1", "A")
C("step", "ReturnValue", "sp1", "B")
N("gz1", "CallFunction", 360, 0, function_name="Greater_IntInt", target_class=KML)
C("loop1", "Index", "gz1", "A")
D("gz1", "B", "0")
N("br1", "Branch", 540, 0)
C("gz1", "ReturnValue", "br1", "Condition")
# max 갱신
N("gmax", "VariableGet", 1260, 480, variable_name="DwMax")
N("gtmax", "CallFunction", 1260, 350, function_name="Greater_DoubleDouble", target_class=KML)
C("sp1", "ReturnValue", "gtmax", "A")
C("gmax", "DwMax", "gtmax", "B")
N("brmax", "Branch", 1440, 0)
C("gtmax", "ReturnValue", "brmax", "Condition")
N("smax", "VariableSet", 1620, -100, variable_name="DwMax")
C("sp1", "ReturnValue", "smax", "DwMax")
N("speak", "VariableSet", 1800, -100, variable_name="DwPeakT")
C("t1", "ReturnValue", "speak", "DwPeakT")
# sum/count
N("gsum", "VariableGet", 2000, 300, variable_name="DwSum")
N("addsum", "CallFunction", 2160, 250, function_name="Add_DoubleDouble", target_class=KML)
C("gsum", "DwSum", "addsum", "A")
C("sp1", "ReturnValue", "addsum", "B")
N("ssum", "VariableSet", 2160, 0, variable_name="DwSum")
C("addsum", "ReturnValue", "ssum", "DwSum")
N("gcnt", "VariableGet", 2340, 300, variable_name="DwCount")
N("addcnt", "CallFunction", 2500, 250, function_name="Add_DoubleDouble", target_class=KML)
C("gcnt", "DwCount", "addcnt", "A")
D("addcnt", "B", "1.0")
N("scnt", "VariableSet", 2500, 0, variable_name="DwCount")
C("addcnt", "ReturnValue", "scnt", "DwCount")
N("spos1", "VariableSet", 2700, 0, variable_name="DwPrevPos")
C("bt1", "Location", "spos1", "DwPrevPos")

# ── 기준선/문턱 ──
N("gsum2", "VariableGet", 0, 900, variable_name="DwSum")
N("gcnt2", "VariableGet", 0, 980, variable_name="DwCount")
N("cntmax", "CallFunction", 180, 980, function_name="FMax", target_class=KML)
C("gcnt2", "DwCount", "cntmax", "A")
D("cntmax", "B", "1.0")
N("base", "CallFunction", 360, 900, function_name="Divide_DoubleDouble", target_class=KML)
C("gsum2", "DwSum", "base", "A")
C("cntmax", "ReturnValue", "base", "B")
N("gmax2", "VariableGet", 360, 1060, variable_name="DwMax")
N("span", "CallFunction", 540, 950, function_name="Subtract_DoubleDouble", target_class=KML)
C("gmax2", "DwMax", "span", "A")
C("base", "ReturnValue", "span", "B")
N("mul", "CallFunction", 720, 950, function_name="Multiply_DoubleDouble", target_class=KML)
C("span", "ReturnValue", "mul", "A")
C(entry, "Ratio", "mul", "B")
N("thr", "CallFunction", 900, 900, function_name="Add_DoubleDouble", target_class=KML)
C("base", "ReturnValue", "thr", "A")
C("mul", "ReturnValue", "thr", "B")
# 가드: max>=60 AND span>=25
N("gA", "CallFunction", 540, 1150, function_name="GreaterEqual_DoubleDouble", target_class=KML)
C("gmax2", "DwMax", "gA", "A")
D("gA", "B", "60.0")
N("gB", "CallFunction", 720, 1150, function_name="GreaterEqual_DoubleDouble", target_class=KML)
C("span", "ReturnValue", "gB", "A")
D("gB", "B", "25.0")
N("gAnd", "CallFunction", 900, 1150, function_name="BooleanAND", target_class=KML)
C("gA", "ReturnValue", "gAnd", "A")
C("gB", "ReturnValue", "gAnd", "B")
N("brGuard", "Branch", 1080, 800)
C("gAnd", "ReturnValue", "brGuard", "Condition")

# 패스2 리셋
N("r2pos", "VariableSet", 1260, 800, variable_name="DwPrevPos")
N("r2st", "VariableSet", 1440, 800, variable_name="DwStart")
D("r2st", "DwStart", "0.0")
N("r2en", "VariableSet", 1620, 800, variable_name="DwEnd")
C("dur", "Length", "r2en", "DwEnd")
N("r2fl", "VariableSet", 1800, 800, variable_name="DwEndSet")
D("r2fl", "DwEndSet", "false")

# ── 패스2 ──
N("loop2", "ForLoop", 2000, 800)
D("loop2", "FirstIndex", "0")
C("nf", "NumFrames", "loop2", "LastIndex")
N("i2", "CallFunction", 2000, 1100, function_name="Conv_IntToDouble", target_class=KML)
C("loop2", "Index", "i2", "InInt")
N("t2", "CallFunction", 2180, 1100, function_name="Multiply_DoubleDouble", target_class=KML)
C("i2", "ReturnValue", "t2", "A")
C("step", "ReturnValue", "t2", "B")
N("pose2", "CallFunction", 2360, 900, function_name="GetAnimPoseAtTime", target_class=APE)
C(entry, "Seq", "pose2", "AnimationSequenceBase")
C("t2", "ReturnValue", "pose2", "Time")
N("bone2", "CallFunction", 2540, 1100, function_name="GetBonePose", target_class=APE)
C("pose2", "Pose", "bone2", "Pose")
C(entry, "BoneName", "bone2", "BoneName")
D("bone2", "Space", "World")
N("bt2", "CallFunction", 2720, 1100, function_name="BreakTransform", target_class=KML)
C("bone2", "ReturnValue", "bt2", "InTransform")
N("gp2", "VariableGet", 2720, 1250, variable_name="DwPrevPos")
N("d2", "CallFunction", 2900, 1150, function_name="Vector_Distance", target_class=KML)
C("bt2", "Location", "d2", "V1")
C("gp2", "DwPrevPos", "d2", "V2")
N("sp2", "CallFunction", 3080, 1150, function_name="Divide_DoubleDouble", target_class=KML)
C("d2", "ReturnValue", "sp2", "A")
C("step", "ReturnValue", "sp2", "B")
N("gz2", "CallFunction", 2360, 800, function_name="Greater_IntInt", target_class=KML)
C("loop2", "Index", "gz2", "A")
D("gz2", "B", "0")
N("br2", "Branch", 2540, 800)
C("gz2", "ReturnValue", "br2", "Condition")
# 미달 판정
N("lt", "CallFunction", 3260, 1150, function_name="Less_DoubleDouble", target_class=KML)
C("sp2", "ReturnValue", "lt", "A")
C("thr", "ReturnValue", "lt", "B")
N("brlt", "Branch", 3440, 800)
C("lt", "ReturnValue", "brlt", "Condition")
# 피크 이전 → start 갱신 / 이후 → end 1회
N("gpk", "VariableGet", 3620, 1100, variable_name="DwPeakT")
N("le", "CallFunction", 3620, 1000, function_name="LessEqual_DoubleDouble", target_class=KML)
C("t2", "ReturnValue", "le", "A")
C("gpk", "DwPeakT", "le", "B")
N("brle", "Branch", 3800, 800)
C("le", "ReturnValue", "brle", "Condition")
N("sst", "VariableSet", 3980, 700, variable_name="DwStart")
C("t2", "ReturnValue", "sst", "DwStart")
N("gfl", "VariableGet", 3980, 1000, variable_name="DwEndSet")
N("notfl", "CallFunction", 4140, 950, function_name="Not_PreBool", target_class=KML)
C("gfl", "DwEndSet", "notfl", "A")
N("brfl", "Branch", 4300, 900)
C("notfl", "ReturnValue", "brfl", "Condition")
N("sen", "VariableSet", 4480, 850, variable_name="DwEnd")
C("t2", "ReturnValue", "sen", "DwEnd")
N("sfl", "VariableSet", 4660, 850, variable_name="DwEndSet")
D("sfl", "DwEndSet", "true")
N("spos2", "VariableSet", 4840, 1000, variable_name="DwPrevPos")
C("bt2", "Location", "spos2", "DwPrevPos")

# ── 출력 계산 ──
N("gst", "VariableGet", 0, 1500, variable_name="DwStart")
N("gen", "VariableGet", 0, 1600, variable_name="DwEnd")
N("adds", "CallFunction", 180, 1500, function_name="Add_DoubleDouble", target_class=KML)
C("gst", "DwStart", "adds", "A")
C(entry, "PadStart", "adds", "B")
N("maxs", "CallFunction", 360, 1500, function_name="FMax", target_class=KML)
C("adds", "ReturnValue", "maxs", "A")
D("maxs", "B", "0.08")
N("adde", "CallFunction", 180, 1600, function_name="Add_DoubleDouble", target_class=KML)
C("gen", "DwEnd", "adde", "A")
C(entry, "PadEnd", "adde", "B")
N("mine", "CallFunction", 360, 1600, function_name="FMin", target_class=KML)
C("adde", "ReturnValue", "mine", "A")
C("dur", "Length", "mine", "B")
# 길이 가드
N("wspan", "CallFunction", 540, 1600, function_name="Subtract_DoubleDouble", target_class=KML)
C("mine", "ReturnValue", "wspan", "A")
C("maxs", "ReturnValue", "wspan", "B")
N("wok", "CallFunction", 720, 1600, function_name="GreaterEqual_DoubleDouble", target_class=KML)
C("wspan", "ReturnValue", "wok", "A")
D("wok", "B", "0.05")
N("selS", "CallFunction", 900, 1500, function_name="SelectFloat", target_class=KML)
C("maxs", "ReturnValue", "selS", "A")
D("selS", "B", "0.0")
C("wok", "ReturnValue", "selS", "bPickA")
N("selE", "CallFunction", 900, 1620, function_name="SelectFloat", target_class=KML)
C("mine", "ReturnValue", "selE", "A")
D("selE", "B", "0.0")
C("wok", "ReturnValue", "selE", "bPickA")

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
missing = [n["temp_id"] for n in nodes if n["temp_id"] not in tm]
if missing:
    raise SystemExit("노드 생성 실패: %s" % missing)
LOG.append("nodes %d" % len(tm))
for d in defaults:
    d["node_id"] = tm[d["node_id"]]
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": FN, "defaults": defaults})
LOG.append("default fails: %s" % ([x for x in (rd.get("results") or []) if not x.get("success", True)] or 0))
for c in data:
    c["source_node"] = tm.get(c["source_node"], c["source_node"])
    c["target_node"] = tm.get(c["target_node"], c["target_node"])

ex = []


def E(a, ap, b):
    ex.append({"source_node": tm.get(a, a), "source_pin": ap, "target_node": tm.get(b, b), "target_pin": "execute"})


E(entry, "then", "rDwMax")
E("rDwMax", "then", "rDwSum")
E("rDwSum", "then", "rDwCount")
E("rDwCount", "then", "rDwPeakT")
E("rDwPeakT", "then", "rpos")
E("rpos", "then", "loop1")
E("loop1", "LoopBody", "br1")
E("br1", "then", "brmax")
E("brmax", "then", "smax")
E("smax", "then", "speak")
E("speak", "then", "ssum")
E("brmax", "else", "ssum")
E("ssum", "then", "scnt")
E("scnt", "then", "spos1")
E("br1", "else", "spos1")
E("loop1", "Completed", "brGuard")
E("brGuard", "then", "r2pos")
E("r2pos", "then", "r2st")
E("r2st", "then", "r2en")
E("r2en", "then", "r2fl")
E("r2fl", "then", "loop2")
E("loop2", "LoopBody", "br2")
E("br2", "then", "brlt")
E("brlt", "then", "brle")
E("brle", "then", "sst")
E("sst", "then", "spos2")
E("brle", "else", "brfl")
E("brfl", "then", "sen")
E("sen", "then", "sfl")
E("sfl", "then", "spos2")
E("brfl", "else", "spos2")
E("brlt", "else", "spos2")
E("br2", "else", "spos2")
if result:
    E("loop2", "Completed", result)
    E("brGuard", "else", result)
    data.append({"source_node": tm["selS"], "source_pin": "ReturnValue", "target_node": result, "target_pin": "OutStart"})
    data.append({"source_node": tm["selE"], "source_pin": "ReturnValue", "target_node": result, "target_pin": "OutEnd"})

rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": data + ex})
LOG.append("bulk fails: %s" % ([x for x in (rc.get("results") or []) if not x.get("success", True)][:5] or 0))
ns2 = {n["id"]: n for n in call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})["nodes"]}


def has(a, ap, b):
    for p in ns2.get(a, {}).get("pins", []):
        if p["name"] == ap:
            return any(x.split(".")[0] == b for x in (p.get("connected_to") or []))
    return False


miss = [(c["source_node"], c["source_pin"], c["target_node"]) for c in data + ex
        if not has(c["source_node"], c["source_pin"], c["target_node"])]
LOG.append("silent-drop: %s" % (miss if miss else "none"))
r = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG.append("compile: %s errors=%s %s" % (r.get("success"), r.get("error_count"), (r.get("errors") or [])[:2]))
print("\n".join(str(x) for x in LOG))
