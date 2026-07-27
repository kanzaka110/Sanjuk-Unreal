# 경사 Z보정 M1 — 손 타깃을 스플라인 라인 높이에 정렬 (2026-07-24)
# 근거 실측 (c0flat.log): 경사(slope 0.2)에서 라인 좌우 높이차 -2.9cm 인데 타깃 높이차 0.1cm(수평).
#   평지 그립 오프셋 C0 = 그립Z - 스플라인최근접Z: L=-8.66 / R=-8.79 (wallless, 벽은 0.5~0.9cm 차이 무시)
# 설계 (XY 무접촉 — M5 교훈):
#   Dz = (FindLocationClosestToWorldLocation(SplineRef, WorldNow).Z + C0) - WorldNow.Z
#   IsValid(SplineRef) exec 게이트 안에서 LedgeSlopeDzL/R Set (else 0) — M4 패턴
#   LedgeSlopeDzBody = (DzL+DzR)*0.5  (다음 단계 CR 펠비스용, 이번엔 기록만)
#   소비: VInterp.Target = WorldNow + (0,0,Dz)  ← 정지 수렴 경로만. 슬라이드(Phase C)는 무접촉
#   평지에선 Dz=0 (실측 검증) = 회귀 없음
# 실행: py slope_z_m1_hands.py [apply]   (에디터 탭에서 Ledge_HandTarget 그래프 닫을 것! — 동시편집 링크유실)
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"
SPL = "SplineComponent"
BK = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/H---------Claude-Sanjuk-Unreal/ef13a25b-b3a2-4f38-8323-b9b645ac51ec/scratchpad/slopeZ_m1_backup.json"
C0L, C0R = "-8.66", "-8.79"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def bq(action, params):
    p = {"asset_path": ABP}
    p.update(params)
    return call("blueprint_query", action, p)


def pie_on():
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


def graph(g):
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": g})["nodes"]}


def pins(nodes, nid):
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


# ══ 앵커 재탐색 (ID 드리프트 대비) ══════════════════
nodes = graph(GH)

anchors = {}  # side -> {vinterp, worldnow}
for nid, n in nodes.items():
    if n["class"] != "K2Node_CallFunction" or n.get("function") != "VInterpTo":
        continue
    pm = pins(nodes, nid)
    cur = pm.get("Current", {}).get("connected_to", [])
    side = None
    for c in cur:
        src = c.split(".")[0]
        if src in nodes and nodes[src]["class"] == "K2Node_VariableGet":
            outs = [p["name"] for p in nodes[src].get("pins", []) if p["direction"] == "output"]
            if "LedgeHandWorldL" in outs:
                side = "L"
            elif "LedgeHandWorldR" in outs:
                side = "R"
    if side is None:
        continue
    tgt_src = pm["Target"]["connected_to"]
    assert len(tgt_src) == 1, "VInterp Target 소스 다중: " + nid
    wn = tgt_src[0].split(".")[0]
    assert nodes[wn].get("function") == "Add_VectorVector", "WorldNow 앵커 예상불일치: " + nid + " <- " + wn
    anchors[side] = {"vinterp": nid, "worldnow": wn}

assert set(anchors) == {"L", "R"}, "앵커 탐색 실패: " + json.dumps(anchors)
print("[PF] 앵커:", json.dumps(anchors))

# exec 스플라이스 지점: Branch(then→Set LedgeSlideTgtHL) 의 execute 로 들어오는 링크
m4br = None
for nid, n in nodes.items():
    if n["class"] != "K2Node_IfThenElse":
        continue
    pm = pins(nodes, nid)
    for c in pm.get("then", {}).get("connected_to", []):
        t = c.split(".")[0]
        if t in nodes and nodes[t]["class"] == "K2Node_VariableSet":
            outs = [p["name"] for p in nodes[t].get("pins", [])]
            if "LedgeSlideTgtHL" in outs:
                m4br = nid
assert m4br, "M4 게이트 Branch 미발견"
m4_exec_srcs = pins(nodes, m4br)["execute"]["connected_to"]
assert len(m4_exec_srcs) == 1, "M4 Branch exec 소스 다중: " + json.dumps(m4_exec_srcs)
up_node, up_pin = m4_exec_srcs[0].split(".", 1)
print("[PF] exec 스플라이스:", up_node + "." + up_pin, "->", m4br)

# 기존 변수 확인
vnames = {v["name"] for v in bq("get_variables", {}).get("variables", [])}
NEW_VARS = ["LedgeSlopeDzL", "LedgeSlopeDzR", "LedgeSlopeDzBody"]
print("[PF] 신규변수 중복:", [n for n in NEW_VARS if n in vnames] or "없음")

if not APPLY:
    print("== dry-run 종료 (apply 인자로 실행) ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"

# ══ 백업 ══════════════════════════════════════
exp = bq("get_graph_data", {"graph_name": GH})
with open(BK, "w", encoding="utf-8") as f:
    json.dump(exp, f)
print("[BK]", BK)

# ══ 변수 생성 ══════════════════════════════════════
for name in NEW_VARS:
    if name in vnames:
        print("[VAR] skip", name)
        continue
    bq("add_variable", {"name": name, "type": "float", "category": "Ledge|SlopeZ"})
    print("[VAR] +", name)

# ══ 노드 생성 ══════════════════════════════════════
X, Y = 4700, -2100
made = {}


def add(key, ntype, extra, pos):
    p = {"graph_name": GH, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    made[key] = nid
    print("[ADD]", key, "->", nid)
    return nid


add("getSp", "VariableGet", {"variable_name": "LedgeSplineRef"}, [X, Y])
add("isv", "CallFunction", {"function_class": KSL, "function_name": "IsValid"}, [X + 220, Y])
add("br", "Branch", {}, [X + 440, Y])
# L 체인
add("fcl", "CallFunction", {"function_class": SPL, "function_name": "FindLocationClosestToWorldLocation"}, [X + 220, Y + 150])
add("bkCL", "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 470, Y + 150])
add("bkWL", "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 470, Y + 280])
add("addL", "CallFunction", {"function_class": KML, "function_name": "Add_DoubleDouble"}, [X + 680, Y + 150])
add("subL", "CallFunction", {"function_class": KML, "function_name": "Subtract_DoubleDouble"}, [X + 880, Y + 150])
# R 체인
add("fcr", "CallFunction", {"function_class": SPL, "function_name": "FindLocationClosestToWorldLocation"}, [X + 220, Y + 430])
add("bkCR", "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 470, Y + 430])
add("bkWR", "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 470, Y + 560])
add("addR", "CallFunction", {"function_class": KML, "function_name": "Add_DoubleDouble"}, [X + 680, Y + 430])
add("subR", "CallFunction", {"function_class": KML, "function_name": "Subtract_DoubleDouble"}, [X + 880, Y + 430])
# Body 평균
add("addB", "CallFunction", {"function_class": KML, "function_name": "Add_DoubleDouble"}, [X + 1080, Y + 290])
add("mulB", "CallFunction", {"function_class": KML, "function_name": "Multiply_DoubleDouble"}, [X + 1260, Y + 290])
# Set (게이트 True)
add("setL", "VariableSet", {"variable_name": "LedgeSlopeDzL"}, [X + 700, Y - 80])
add("setR", "VariableSet", {"variable_name": "LedgeSlopeDzR"}, [X + 940, Y - 80])
add("setB", "VariableSet", {"variable_name": "LedgeSlopeDzBody"}, [X + 1180, Y - 80])
# Set 0 (게이트 False)
add("setL0", "VariableSet", {"variable_name": "LedgeSlopeDzL"}, [X + 700, Y + 60])
add("setR0", "VariableSet", {"variable_name": "LedgeSlopeDzR"}, [X + 940, Y + 60])
add("setB0", "VariableSet", {"variable_name": "LedgeSlopeDzBody"}, [X + 1180, Y + 60])
# 소비 (L/R): WorldNow + (0,0,Dz)
add("getL", "VariableGet", {"variable_name": "LedgeSlopeDzL"}, [X + 1500, Y + 100])
add("mkL", "CallFunction", {"function_class": KML, "function_name": "MakeVector"}, [X + 1700, Y + 100])
add("avL", "CallFunction", {"function_class": KML, "function_name": "Add_VectorVector"}, [X + 1900, Y + 100])
add("getR", "VariableGet", {"variable_name": "LedgeSlopeDzR"}, [X + 1500, Y + 320])
add("mkR", "CallFunction", {"function_class": KML, "function_name": "MakeVector"}, [X + 1700, Y + 320])
add("avR", "CallFunction", {"function_class": KML, "function_name": "Add_VectorVector"}, [X + 1900, Y + 320])

# ══ 핀 디폴트 ══════════════════════════════════════
def pindef(key, pin, value):
    bq("set_pin_default", {"graph_name": GH, "node_id": made[key], "pin_name": pin, "value": value})
    print("[DEF]", key, pin, "=", value)


pindef("fcl", "CoordinateSpace", "World")
pindef("fcr", "CoordinateSpace", "World")
pindef("addL", "B", C0L)
pindef("addR", "B", C0R)
pindef("mulB", "B", "0.5")

# ══ 배선 ══════════════════════════════════════
def wire(sk, sp, tk, tp):
    src = made.get(sk, sk)
    tgt = made.get(tk, tk)
    bq("connect_pins", {"graph_name": GH, "source_node": src, "source_pin": sp,
                        "target_node": tgt, "target_pin": tp})
    print("[WIRE]", sk + "." + sp, "->", tk + "." + tp)


WNL = anchors["L"]["worldnow"]
WNR = anchors["R"]["worldnow"]
VIL = anchors["L"]["vinterp"]
VIR = anchors["R"]["vinterp"]

# 게이트 조건
wire("getSp", "LedgeSplineRef", "isv", "InputObject")
wire("isv", "ReturnValue", "br", "Condition")
# L 데이터
wire("getSp", "LedgeSplineRef", "fcl", "self")
wire(WNL, "ReturnValue", "fcl", "WorldLocation")
wire("fcl", "ReturnValue", "bkCL", "InVec")
wire(WNL, "ReturnValue", "bkWL", "InVec")
wire("bkCL", "Z", "addL", "A")
wire("addL", "ReturnValue", "subL", "A")
wire("bkWL", "Z", "subL", "B")
wire("subL", "ReturnValue", "setL", "LedgeSlopeDzL")
# R 데이터
wire("getSp", "LedgeSplineRef", "fcr", "self")
wire(WNR, "ReturnValue", "fcr", "WorldLocation")
wire("fcr", "ReturnValue", "bkCR", "InVec")
wire(WNR, "ReturnValue", "bkWR", "InVec")
wire("bkCR", "Z", "addR", "A")
wire("addR", "ReturnValue", "subR", "A")
wire("bkWR", "Z", "subR", "B")
wire("subR", "ReturnValue", "setR", "LedgeSlopeDzR")
# Body 평균
wire("subL", "ReturnValue", "addB", "A")
wire("subR", "ReturnValue", "addB", "B")
wire("addB", "ReturnValue", "mulB", "A")
wire("mulB", "ReturnValue", "setB", "LedgeSlopeDzBody")
# exec: 상류 → br, then → setL→setR→setB → M4브랜치 / else → setL0→setR0→setB0 → M4브랜치
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": GH,
     "source_node": up_node, "source_pin": up_pin, "target_node": m4br, "target_pin": "execute"})
print("[CUT]", up_node + "." + up_pin, "-X->", m4br + ".execute")
wire(up_node, up_pin, "br", "execute")
wire("br", "then", "setL", "execute")
wire("setL", "then", "setR", "execute")
wire("setR", "then", "setB", "execute")
wire("setB", "then", m4br, "execute")
wire("br", "else", "setL0", "execute")
wire("setL0", "then", "setR0", "execute")
wire("setR0", "then", "setB0", "execute")
wire("setB0", "then", m4br, "execute")
# 소비: VInterp.Target 재배선
wire("getL", "LedgeSlopeDzL", "mkL", "Z")
wire(WNL, "ReturnValue", "avL", "A")
wire("mkL", "ReturnValue", "avL", "B")
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": GH,
     "source_node": WNL, "source_pin": "ReturnValue", "target_node": VIL, "target_pin": "Target"})
wire("avL", "ReturnValue", VIL, "Target")
wire("getR", "LedgeSlopeDzR", "mkR", "Z")
wire(WNR, "ReturnValue", "avR", "A")
wire("mkR", "ReturnValue", "avR", "B")
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": GH,
     "source_node": WNR, "source_pin": "ReturnValue", "target_node": VIR, "target_pin": "Target"})
wire("avR", "ReturnValue", VIR, "Target")

# ══ 검증: 링크 실재 확인 (connect_pins 무음드랍 대비) ══
nodes2 = graph(GH)


def haslink(sn, sp, tn, tp):
    pm = pins(nodes2, made.get(tn, tn))
    return any(c == made.get(sn, sn) + "." + sp for c in pm.get(tp, {}).get("connected_to", []))


checks = [
    ("isv", "ReturnValue", "br", "Condition"),
    (WNL, "ReturnValue", "fcl", "WorldLocation"),
    ("subL", "ReturnValue", "setL", "LedgeSlopeDzL"),
    ("avL", "ReturnValue", VIL, "Target"),
    ("avR", "ReturnValue", VIR, "Target"),
    ("mulB", "ReturnValue", "setB", "LedgeSlopeDzBody"),
    (up_node, up_pin, "br", "execute"),
    ("setB", "then", m4br, "execute"),
    ("setB0", "then", m4br, "execute"),
]
ok = True
for c in checks:
    good = haslink(*c)
    ok = ok and good
    print("[CHK]", ("OK " if good else "FAIL "), c[0] + "." + c[1], "->", c[2] + "." + c[3])
# VInterp Target 구링크 제거 확인
for side, VI, WN in (("L", VIL, WNL), ("R", VIR, WNR)):
    tgt_srcs = pins(nodes2, VI)["Target"]["connected_to"]
    good = tgt_srcs == [made["av" + side] + ".ReturnValue"]
    ok = ok and good
    print("[CHK]", ("OK " if good else "FAIL "), "VInterp" + side + ".Target =", tgt_srcs)
assert ok, "링크 검증 실패 — 백업으로 복원 검토"

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:300])
