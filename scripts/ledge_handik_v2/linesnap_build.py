# Ledge_LineSnap (2026-07-25) — 핸드타깃(재래치 후보)을 스플라인 라인 Z에 직접 투영
# 배경: 앵커 주입이 DzHold(정지 프레임 동결값)라 경사 이동 중 재래치 타깃이 라인에서 뜸.
#   타깃 자기 XY 기준 최근접 라인 Z로 Dz를 래치 시점에 계산하면 출렁임 없음(타깃은 고정점).
# 구조: 함수 Ledge_LineSnap(CandL, CandR) — IsValid exec 게이트(M4 None스팸 방지)
#   손별: FindLocationClosestToWorldLocation → (Z+C0) − CandZ → Distance<45 게이트 → FClamp ±35
#   → LedgeSnapDzL/R Set. HandTarget의 MakeVector Z(구 DzHold)를 SnapDz로 교체 + Set 직전 호출.
# C0/게이트/클램프 = Ledge_SlopeZ 실측 동일값 (L −8.66 / R −8.79 / 45 / ±35)
# 실행: py linesnap_build.py         (사전 점검)
#       py linesnap_build.py apply   (적용)
import json
import sys
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GF = "Ledge_LineSnap"
GT = "Ledge_HandTarget"
KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"
SPL = "SplineComponent"
C0 = {"L": "-8.66", "R": "-8.79"}
GATE_DIST = "45.0"
CLAMP = ("-35.0", "35.0")
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

# HandTarget 기존 노드 (anchor_probe.py 2026-07-25 실측)
CAND = {"L": "K2Node_CallFunction_200", "R": "K2Node_CallFunction_201"}   # 재래치 후보 소스
MKVEC = {"L": "K2Node_CallFunction_259", "R": "K2Node_CallFunction_260"}  # MakeVector(0,0,Dz)
GET_HOLD = {"L": "K2Node_VariableGet_85", "R": "K2Node_VariableGet_86"}   # DzHold getter (구)
HOLD_PIN = {"L": "LedgeSlopeDzHoldL", "R": "LedgeSlopeDzHoldR"}
SET_ANCHOR_L = "K2Node_VariableSet_25"    # exec 삽입점: VariableSet_33.then → 여기
EXEC_PREV = "K2Node_VariableSet_33"


def call(tool: str, action: str, params: dict, timeout: int = 300) -> dict:
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def bq(action: str, params: dict) -> dict:
    p = {"asset_path": ABP}
    p.update(params)
    return call("blueprint_query", action, p)


def graph(g: str) -> dict:
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": g})["nodes"]}


def pins(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def pie_on() -> bool:
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


# ── 사전 점검 ──
ht = graph(GT)
checks = []
for s in ("L", "R"):
    z_src = pins(ht, MKVEC[s])["Z"]["connected_to"]
    checks.append((z_src == [GET_HOLD[s] + "." + HOLD_PIN[s]], f"MakeVector{s}.Z ← DzHold{s} (교체 전)"))
    checks.append((CAND[s] in ht, f"재래치 소스 {CAND[s]}"))
exec_link = pins(ht, SET_ANCHOR_L)["execute"]["connected_to"]
checks.append((exec_link == [EXEC_PREV + ".then"], f"SetAnchorL.execute ← {EXEC_PREV}.then (삽입 전)"))
ok = True
for good, label in checks:
    print("[PF]", "OK " if good else "FAIL", label)
    ok = ok and good
if not APPLY:
    print("[PF] 사전 점검", "통과 — apply로 실행" if ok else "실패")
    sys.exit(0 if ok else 1)
assert ok, "사전 점검 실패"
assert not pie_on(), "PIE 실행 중 — 종료 후 재실행"

# ── 1) 변수 ──
existing = {v["name"] for v in bq("get_variables", {}).get("variables", [])}
for v in ("LedgeSnapDzL", "LedgeSnapDzR"):
    if v not in existing:
        bq("add_variable", {"name": v, "type": "float", "category": "Ledge|SlopeZ"})
        print("[VAR] +", v)

# ── 2) 함수 생성 ──
try:
    bq("add_function", {"function_name": GF})
    print("[F] +", GF)
except RuntimeError as e:
    print("[F]", str(e)[:100])
bq("set_function_params", {"function_name": GF,
    "inputs": [{"name": "CandL", "type": "struct:Vector"}, {"name": "CandR", "type": "struct:Vector"}]})

fn = graph(GF)
entry = next(nid for nid, n in fn.items() if "FunctionEntry" in n["class"])
made = {}


def add(key: str, ntype: str, extra: dict, pos: list) -> str:
    p = {"graph_name": GF, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    made[key] = nid
    return nid


def wire(sk: str, sp: str, tk: str, tp: str) -> None:
    bq("connect_pins", {"graph_name": GF,
                        "source_node": made.get(sk, sk), "source_pin": sp,
                        "target_node": made.get(tk, tk), "target_pin": tp})


def pindef(key: str, pin: str, value: str) -> None:
    bq("set_pin_default", {"graph_name": GF, "node_id": made[key], "pin_name": pin, "value": value})


X, Y = 300, 0
add("getSp", "VariableGet", {"variable_name": "LedgeSplineRef"}, [X, Y - 150])
add("isv", "CallFunction", {"function_class": KSL, "function_name": "IsValid"}, [X + 200, Y - 150])
add("br", "Branch", {}, [X + 400, Y - 150])
wire("getSp", "LedgeSplineRef", "isv", "Object")
wire("isv", "ReturnValue", "br", "Condition")
wire(entry, "then", "br", "execute")

for i, s in enumerate(("L", "R")):
    yo = Y + 150 + i * 400
    add("cls" + s, "CallFunction", {"function_class": SPL, "function_name": "FindLocationClosestToWorldLocation"}, [X + 300, yo])
    add("bkC" + s, "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 550, yo])
    add("bkH" + s, "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 550, yo + 120])
    add("c0" + s, "CallFunction", {"function_class": KML, "function_name": "Add_DoubleDouble"}, [X + 720, yo])
    add("dz" + s, "CallFunction", {"function_class": KML, "function_name": "Subtract_DoubleDouble"}, [X + 880, yo])
    add("dist" + s, "CallFunction", {"function_class": KML, "function_name": "Vector_Distance"}, [X + 720, yo + 220])
    add("lt" + s, "CallFunction", {"function_class": KML, "function_name": "Less_DoubleDouble"}, [X + 880, yo + 220])
    add("clp" + s, "CallFunction", {"function_class": KML, "function_name": "FClamp"}, [X + 1040, yo])
    add("sel" + s, "CallFunction", {"function_class": KML, "function_name": "SelectFloat"}, [X + 1200, yo])
    pindef("cls" + s, "CoordinateSpace", "World")
    pindef("c0" + s, "B", C0[s])
    pindef("lt" + s, "B", GATE_DIST)
    pindef("clp" + s, "Min", CLAMP[0])
    pindef("clp" + s, "Max", CLAMP[1])
    pindef("sel" + s, "B", "0.0")
    wire("getSp", "LedgeSplineRef", "cls" + s, "self")
    wire(entry, "Cand" + s, "cls" + s, "WorldLocation")
    wire("cls" + s, "ReturnValue", "bkC" + s, "InVec")
    wire(entry, "Cand" + s, "bkH" + s, "InVec")
    wire("bkC" + s, "Z", "c0" + s, "A")
    wire("c0" + s, "ReturnValue", "dz" + s, "A")
    wire("bkH" + s, "Z", "dz" + s, "B")
    wire("cls" + s, "ReturnValue", "dist" + s, "V1")
    wire(entry, "Cand" + s, "dist" + s, "V2")
    wire("dist" + s, "ReturnValue", "lt" + s, "A")
    wire("dz" + s, "ReturnValue", "clp" + s, "Value")
    wire("clp" + s, "ReturnValue", "sel" + s, "A")
    wire("lt" + s, "ReturnValue", "sel" + s, "bPickA")

add("setL", "VariableSet", {"variable_name": "LedgeSnapDzL"}, [X + 1450, Y - 200])
add("setR", "VariableSet", {"variable_name": "LedgeSnapDzR"}, [X + 1650, Y - 200])
add("setL0", "VariableSet", {"variable_name": "LedgeSnapDzL"}, [X + 1450, Y - 50])
add("setR0", "VariableSet", {"variable_name": "LedgeSnapDzR"}, [X + 1650, Y - 50])
wire("selL", "ReturnValue", "setL", "LedgeSnapDzL")
wire("selR", "ReturnValue", "setR", "LedgeSnapDzR")
bq("set_pin_default", {"graph_name": GF, "node_id": made["setL0"], "pin_name": "LedgeSnapDzL", "value": "0.0"})
bq("set_pin_default", {"graph_name": GF, "node_id": made["setR0"], "pin_name": "LedgeSnapDzR", "value": "0.0"})
wire("br", "then", "setL", "execute")
wire("setL", "then", "setR", "execute")
wire("br", "else", "setL0", "execute")
wire("setL0", "then", "setR0", "execute")
print("[F] 내부 배선 완료")

r = bq("compile_blueprint", {})
print("[COMPILE-1]", json.dumps(r)[:150])

# ── 3) HandTarget: 호출 삽입 + MakeVector Z 교체 ──
r = bq("add_node", {"graph_name": GT, "node_type": "CallFunction",
                    "function_class": "PC_01_ABP_C", "function_name": GF, "position": [-9000, 4000]})
callnid = r.get("id") or r.get("node_id")
print("[CALL]", callnid)
for s in ("L", "R"):
    bq("connect_pins", {"graph_name": GT, "source_node": CAND[s], "source_pin": "ReturnValue",
                        "target_node": callnid, "target_pin": "Cand" + s})
# exec 삽입: EXEC_PREV.then → call → SET_ANCHOR_L
bq("disconnect_pins", {"graph_name": GT, "source_node": EXEC_PREV, "source_pin": "then",
                       "target_node": SET_ANCHOR_L, "target_pin": "execute"})
bq("connect_pins", {"graph_name": GT, "source_node": EXEC_PREV, "source_pin": "then",
                    "target_node": callnid, "target_pin": "execute"})
bq("connect_pins", {"graph_name": GT, "source_node": callnid, "source_pin": "then",
                    "target_node": SET_ANCHOR_L, "target_pin": "execute"})
# MakeVector Z 교체
snap_get = {}
for s in ("L", "R"):
    r = bq("add_node", {"graph_name": GT, "node_type": "VariableGet",
                        "variable_name": "LedgeSnapDz" + s, "position": [-8800, 4200 if s == "L" else 4350]})
    gv = r.get("id") or r.get("node_id")
    snap_get[s] = gv
    bq("disconnect_pins", {"graph_name": GT, "source_node": GET_HOLD[s], "source_pin": HOLD_PIN[s],
                           "target_node": MKVEC[s], "target_pin": "Z"})
    bq("connect_pins", {"graph_name": GT, "source_node": gv, "source_pin": "LedgeSnapDz" + s,
                        "target_node": MKVEC[s], "target_pin": "Z"})
    print("[HT] MakeVector", s, ".Z ← LedgeSnapDz" + s)

# ── 4) 컴파일 + 링크 검증 ──
r = bq("compile_blueprint", {})
print("[COMPILE-2]", json.dumps(r)[:200])

fn2 = graph(GF)
ht2 = graph(GT)
v = []
v.append((pins(fn2, made["setL"])["LedgeSnapDzL"]["connected_to"] == [made["selL"] + ".ReturnValue"], "FN SetL ← selL"))
v.append((pins(fn2, made["setR"])["LedgeSnapDzR"]["connected_to"] == [made["selR"] + ".ReturnValue"], "FN SetR ← selR"))
v.append((pins(fn2, made["setL"])["execute"]["connected_to"] == [made["br"] + ".then"], "FN br.then → SetL"))
v.append((pins(fn2, made["setL0"])["execute"]["connected_to"] == [made["br"] + ".else"], "FN br.else → SetL0"))
for s in ("L", "R"):
    v.append((pins(fn2, made["cls" + s])["WorldLocation"]["connected_to"] == [entry + ".Cand" + s], f"FN cls{s} ← Cand{s}"))
    v.append((pins(ht2, MKVEC[s])["Z"]["connected_to"] == [snap_get[s] + ".LedgeSnapDz" + s], f"HT MakeVector{s}.Z ← SnapDz{s}"))
    v.append((pins(ht2, callnid)["Cand" + s]["connected_to"] == [CAND[s] + ".ReturnValue"], f"HT call.Cand{s} ← {CAND[s]}"))
v.append((pins(ht2, callnid)["execute"]["connected_to"] == [EXEC_PREV + ".then"], "HT exec 삽입 (prev→call)"))
v.append((pins(ht2, SET_ANCHOR_L)["execute"]["connected_to"] == [callnid + ".then"], "HT exec 삽입 (call→SetAnchorL)"))
allok = True
for good, label in v:
    print("[CHK]", "OK " if good else "FAIL", label)
    allok = allok and good
assert allok, "링크 검증 실패"
print("[DONE] 컴파일+검증 통과 — PIE 실측 대기")
