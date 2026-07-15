# AM_SBLedgeHandIK 발 커브 확장 (v9.2) — ledge_foot_ik_l/r + ledge_foot_move_l/r
# 손과 동일 3분류에 발 클러스터 추가:
#   preamble/revert: 발 4커브 exists->remove 세그먼트
#   exit: 발 ik 1(0)->1(Hold)->0(Hold+Fade)   idle: 발 ik 상수1
#   move: 발 ik 창(FMax(FootStart-RR,0)->FootStart 릴리즈, FootEnd->FootEnd+PR 플랜트) + move 램프
# 신규 인스턴스 파라미터: FootMoveStartL/EndL/StartR/EndR (RR/PR/ExitHold/Fade는 손과 공유)
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeHandIK"
G = "EventGraph"
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


# 앵커 (라이브 덤프 2026-07-15 검증)
EV_A, EV_R = "K2Node_Event_0", "K2Node_Event_1"
BR_EXIT = "K2Node_IfThenElse_4"
A_BOUND = [("K2Node_CallFunction_22", "then"), ("K2Node_IfThenElse_3", "else")]  # -> BR_EXIT.execute
EXIT_TAIL = ("K2Node_CallFunction_31", "then")
IDLE_TAIL = ("K2Node_CallFunction_35", "then")
MOVE_TAIL = ("K2Node_CallFunction_45", "then")
R_BOUND = [("K2Node_CallFunction_53", "then"), ("K2Node_IfThenElse_9", "else")]  # revert 꼬리 (열림)
G_HOLD, G_HF = "K2Node_VariableGet_4", "K2Node_CallFunction_23"  # ExitHoldTime / Hold+Fade
G_RR, G_PR = "K2Node_VariableGet_6", "K2Node_VariableGet_7"      # ReleaseRampTime / PlantRampTime

g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": G})
ids_now = {n["id"] for n in g["nodes"]}
need = [EV_A, EV_R, BR_EXIT, EXIT_TAIL[0], IDLE_TAIL[0], MOVE_TAIL[0], R_BOUND[0][0], R_BOUND[1][0], G_HOLD, G_HF, G_RR, G_PR] + [a for a, _ in A_BOUND]
miss = [x for x in need if x not in ids_now]
if miss:
    raise SystemExit("앵커 소실: " + str(miss))
LOG["steps"].append("preflight OK (%d nodes)" % len(ids_now))

# ── 변수 4개 ──
for v in ("FootMoveStartL", "FootMoveEndL", "FootMoveStartR", "FootMoveEndR"):
    try:
        call("blueprint_query", "add_variable",
             {"asset_path": BP, "name": v, "type": "float", "category": "FootIK",
              "instance_editable": True, "default_value": "0.1" if "Start" in v else "0.4"})
        LOG["steps"].append("var added: " + v)
    except Exception as e:
        LOG["steps"].append("var skip %s: %s" % (v, repr(e)[:80]))

ABL = "AnimationBlueprintLibrary"
KML = "KismetMathLibrary"
FCURVES = ["ledge_foot_ik_l", "ledge_foot_ik_r", "ledge_foot_move_l", "ledge_foot_move_r"]
nodes, defaults, conns = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(nid, pin, val):
    defaults.append({"node_id": nid, "pin_name": pin, "value": val})


def SEQA(t):  # OnApply 시퀀스 연결
    C(EV_A, "AnimationSequence", t, "AnimationSequenceBase")


# 게터
for v in ("FootMoveStartL", "FootMoveEndL", "FootMoveStartR", "FootMoveEndR"):
    N("g_" + v, "VariableGet", 3000, 2600, variable_name=v)

# A) preamble 발 제거체인 4세그
px = 400
for i, c in enumerate(FCURVES):
    N("fex%d" % i, "CallFunction", px, 1700, function_name="DoesCurveExist", target_class=ABL)
    N("fbr%d" % i, "Branch", px + 150, 1700)
    N("frm%d" % i, "CallFunction", px + 300, 1650, function_name="RemoveCurve", target_class=ABL)
    D("fex%d" % i, "CurveName", c)
    D("frm%d" % i, "CurveName", c)
    SEQA("fex%d" % i)
    SEQA("frm%d" % i)
    C("fex%d" % i, "ReturnValue", "fbr%d" % i, "Condition")
    C("fex%d" % i, "then", "fbr%d" % i, "execute")
    C("fbr%d" % i, "then", "frm%d" % i, "execute")
    if i > 0:
        C("fbr%d" % (i - 1), "else", "fex%d" % i, "execute")
        C("frm%d" % (i - 1), "then", "fex%d" % i, "execute")
    px += 480

# B) exit 발 ik (1,1@Hold,0@HF) ×2
bx = 400
for s in ("l", "r"):
    cn = "ledge_foot_ik_" + s
    N("xfac_" + s, "CallFunction", bx, 2000, function_name="AddCurve", target_class=ABL)
    D("xfac_" + s, "CurveName", cn)
    SEQA("xfac_" + s)
    for k, (tsrc, val) in enumerate((("0.0", "1.0"), ("HOLD", "1.0"), ("HF", "0.0"))):
        t = "xfk%d_%s" % (k, s)
        N(t, "CallFunction", bx + 190 * (k + 1), 2000, function_name="AddFloatCurveKey", target_class=ABL)
        D(t, "CurveName", cn)
        D(t, "Value", val)
        SEQA(t)
        if tsrc == "HOLD":
            C(G_HOLD, "ExitHoldTime", t, "Time")
        elif tsrc == "HF":
            C(G_HF, "ReturnValue", t, "Time")
        else:
            D(t, "Time", tsrc)
    C("xfac_" + s, "then", "xfk0_" + s, "execute")
    C("xfk0_" + s, "then", "xfk1_" + s, "execute")
    C("xfk1_" + s, "then", "xfk2_" + s, "execute")
    bx += 1000

# C) idle 발 ik 상수1 ×2
bx = 400
for s in ("l", "r"):
    cn = "ledge_foot_ik_" + s
    N("ifac_" + s, "CallFunction", bx, 2200, function_name="AddCurve", target_class=ABL)
    N("ifk_" + s, "CallFunction", bx + 190, 2200, function_name="AddFloatCurveKey", target_class=ABL)
    D("ifac_" + s, "CurveName", cn)
    D("ifk_" + s, "CurveName", cn)
    D("ifk_" + s, "Time", "0.0")
    D("ifk_" + s, "Value", "1.0")
    SEQA("ifac_" + s)
    SEQA("ifk_" + s)
    C("ifac_" + s, "then", "ifk_" + s, "execute")
    bx += 500

# D) move 발 ik 창 + move 램프 ×2
bx = 400
for s, S in (("l", "L"), ("r", "R")):
    cn = "ledge_foot_ik_" + s
    gs, ge = "g_FootMoveStart" + S, "g_FootMoveEnd" + S
    # 산술: rel = FMax(Start-RR, 0), pe = End+PR
    N("fsub_" + s, "CallFunction", bx, 2650, function_name="Subtract_DoubleDouble", target_class=KML)
    N("fmax_" + s, "CallFunction", bx + 150, 2650, function_name="FMax", target_class=KML)
    N("fpad_" + s, "CallFunction", bx + 300, 2650, function_name="Add_DoubleDouble", target_class=KML)
    C(gs, "FootMoveStart" + S, "fsub_" + s, "A")
    C(G_RR, "ReleaseRampTime", "fsub_" + s, "B")
    C("fsub_" + s, "ReturnValue", "fmax_" + s, "A")
    D("fmax_" + s, "B", "0.0")
    C(ge, "FootMoveEnd" + S, "fpad_" + s, "A")
    C(G_PR, "PlantRampTime", "fpad_" + s, "B")
    # ik: (0,1) (rel,1) (Start,0) (End,0) (pe,1)
    N("mfac_" + s, "CallFunction", bx, 2400, function_name="AddCurve", target_class=ABL)
    D("mfac_" + s, "CurveName", cn)
    SEQA("mfac_" + s)
    keyspec = [("0.0", "1.0"), ("REL", "1.0"), ("START", "0.0"), ("END", "0.0"), ("PE", "1.0")]
    for k, (tsrc, val) in enumerate(keyspec):
        t = "mfk%d_%s" % (k, s)
        N(t, "CallFunction", bx + 170 * (k + 1), 2400, function_name="AddFloatCurveKey", target_class=ABL)
        D(t, "CurveName", cn)
        D(t, "Value", val)
        SEQA(t)
        if tsrc == "REL":
            C("fmax_" + s, "ReturnValue", t, "Time")
        elif tsrc == "START":
            C(gs, "FootMoveStart" + S, t, "Time")
        elif tsrc == "END":
            C(ge, "FootMoveEnd" + S, t, "Time")
        elif tsrc == "PE":
            C("fpad_" + s, "ReturnValue", t, "Time")
        else:
            D(t, "Time", tsrc)
    C("mfac_" + s, "then", "mfk0_" + s, "execute")
    for k in range(4):
        C("mfk%d_%s" % (k, s), "then", "mfk%d_%s" % (k + 1, s), "execute")
    # move 램프: (Start,0) (End,1)
    cm = "ledge_foot_move_" + s
    N("mvfac_" + s, "CallFunction", bx + 1100, 2400, function_name="AddCurve", target_class=ABL)
    N("mvfk0_" + s, "CallFunction", bx + 1290, 2400, function_name="AddFloatCurveKey", target_class=ABL)
    N("mvfk1_" + s, "CallFunction", bx + 1480, 2400, function_name="AddFloatCurveKey", target_class=ABL)
    D("mvfac_" + s, "CurveName", cm)
    D("mvfk0_" + s, "CurveName", cm)
    D("mvfk0_" + s, "Value", "0.0")
    D("mvfk1_" + s, "CurveName", cm)
    D("mvfk1_" + s, "Value", "1.0")
    SEQA("mvfac_" + s)
    SEQA("mvfk0_" + s)
    SEQA("mvfk1_" + s)
    C(gs, "FootMoveStart" + S, "mvfk0_" + s, "Time")
    C(ge, "FootMoveEnd" + S, "mvfk1_" + s, "Time")
    C("mvfac_" + s, "then", "mvfk0_" + s, "execute")
    C("mvfk0_" + s, "then", "mvfk1_" + s, "execute")
    bx += 2000

# E) revert 발 제거체인 4세그
px = 400
for i, c in enumerate(FCURVES):
    N("rfex%d" % i, "CallFunction", px, 2900, function_name="DoesCurveExist", target_class=ABL)
    N("rfbr%d" % i, "Branch", px + 150, 2900)
    N("rfrm%d" % i, "CallFunction", px + 300, 2850, function_name="RemoveCurve", target_class=ABL)
    D("rfex%d" % i, "CurveName", c)
    D("rfrm%d" % i, "CurveName", c)
    C(EV_R, "AnimationSequence", "rfex%d" % i, "AnimationSequenceBase")
    C(EV_R, "AnimationSequence", "rfrm%d" % i, "AnimationSequenceBase")
    C("rfex%d" % i, "ReturnValue", "rfbr%d" % i, "Condition")
    C("rfex%d" % i, "then", "rfbr%d" % i, "execute")
    C("rfbr%d" % i, "then", "rfrm%d" % i, "execute")
    if i > 0:
        C("rfbr%d" % (i - 1), "else", "rfex%d" % i, "execute")
        C("rfrm%d" % (i - 1), "then", "rfex%d" % i, "execute")
    px += 480

# ── 생성/디폴트 ──
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": G, "nodes": nodes})
tmap = {}
def harvest(obj):
    if isinstance(obj, dict):
        if obj.get("temp_id") and (obj.get("node_id") or obj.get("id")):
            tmap[obj["temp_id"]] = obj.get("node_id") or obj.get("id")
        else:
            for v in obj.values():
                harvest(v)
    elif isinstance(obj, list):
        for e in obj:
            harvest(e)
harvest(res)
if len(tmap) != len(nodes):
    raise SystemExit("노드 생성 %d/%d — 중단: %s" % (len(tmap), len(nodes), json.dumps(res)[:300]))
LOG["steps"].append("nodes: %d" % len(tmap))
for d in defaults:
    d["node_id"] = tmap.get(d["node_id"], d["node_id"])
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": G, "defaults": defaults})

# ── 스플라이스 연결 ──
splice = []
# A: 경계 재배선 (CF_22.then / IfThenElse_3.else -> fex0, frm3/fbr3 -> BR_EXIT)
call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": G, "node_id": A_BOUND[0][0], "pin_name": A_BOUND[0][1]})
call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": G, "node_id": A_BOUND[1][0], "pin_name": A_BOUND[1][1]})
for a, p in A_BOUND:
    splice.append({"source_node": a, "source_pin": p, "target_node": tmap["fex0"], "target_pin": "execute"})
splice.append({"source_node": tmap["frm3"], "source_pin": "then", "target_node": BR_EXIT, "target_pin": "execute"})
splice.append({"source_node": tmap["fbr3"], "source_pin": "else", "target_node": BR_EXIT, "target_pin": "execute"})
# B/C/D: 모드 꼬리 -> 발 클러스터
splice.append({"source_node": EXIT_TAIL[0], "source_pin": EXIT_TAIL[1], "target_node": tmap["xfac_l"], "target_pin": "execute"})
splice.append({"source_node": tmap["xfk2_l"], "source_pin": "then", "target_node": tmap["xfac_r"], "target_pin": "execute"})
splice.append({"source_node": IDLE_TAIL[0], "source_pin": IDLE_TAIL[1], "target_node": tmap["ifac_l"], "target_pin": "execute"})
splice.append({"source_node": tmap["ifk_l"], "source_pin": "then", "target_node": tmap["ifac_r"], "target_pin": "execute"})
splice.append({"source_node": MOVE_TAIL[0], "source_pin": MOVE_TAIL[1], "target_node": tmap["mfac_l"], "target_pin": "execute"})
splice.append({"source_node": tmap["mfk4_l"], "source_pin": "then", "target_node": tmap["mfac_r"], "target_pin": "execute"})
splice.append({"source_node": tmap["mfk4_r"], "source_pin": "then", "target_node": tmap["mvfac_l"], "target_pin": "execute"})
splice.append({"source_node": tmap["mvfk1_l"], "source_pin": "then", "target_node": tmap["mvfac_r"], "target_pin": "execute"})
# E: revert 꼬리 -> 발 제거체인
for a, p in R_BOUND:
    splice.append({"source_node": a, "source_pin": p, "target_node": tmap["rfex0"], "target_pin": "execute"})

for c in conns:
    c["source_node"] = tmap.get(c["source_node"], c["source_node"])
    c["target_node"] = tmap.get(c["target_node"], c["target_node"])
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": G, "connections": conns + splice})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append(fails)
LOG["steps"].append("links: %d req, %d fail" % (len(conns) + len(splice), len(fails)))
LOG["tmap_size"] = len(tmap)

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_foot.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("MOD_FOOT_DONE fails=%d errors=%s" % (len(fails), "yes" if LOG["errors"] else "none"))
