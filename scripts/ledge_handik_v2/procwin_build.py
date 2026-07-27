# 절차적 릴리즈 창 (2026-07-24) — 대각 버킷 이동 시 손갈이 리듬 합성 (애님 추가 없음)
# Ledge_ProcWindow 함수: 유닛무브+대각(22.5<|ang|<67.5 | 112.5~157.5)+스플라인 유효+스팬>1 이면
#   진행도 p=(da-sd)/(td-sd) 기준 L창 0.10~0.45 / R창 0.50~0.85 에서 ProcWin=0 (그 외 1)
# 소비: Ledge_HandAlpha 커브알파(FClamp 출력)에 곱 — 기존 FInterp가 에지 스무딩
# 실행: py procwin_build.py apply
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GF = "Ledge_ProcWindow"
GA = "Ledge_HandAlpha"
KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"
SPL = "SplineComponent"
WINL = ("0.10", "0.45")
WINR = ("0.50", "0.85")
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


def graph(g):
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": g})["nodes"]}


def pins(nodes, nid):
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def pie_on():
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


if not APPLY:
    ha = graph(GA)
    assert pins(ha, "K2Node_CallFunction_194")["A"]["connected_to"] == ["K2Node_CallFunction_95.ReturnValue"]
    assert pins(ha, "K2Node_CallFunction_195")["A"]["connected_to"] == ["K2Node_CallFunction_110.ReturnValue"]
    print("[PF] HandAlpha 삽입점 OK — apply로 실행")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중"

# ══ 변수 ══
vnames = {v["name"] for v in bq("get_variables", {}).get("variables", [])}
for v in ("LedgeProcWinL", "LedgeProcWinR"):
    if v not in vnames:
        bq("add_variable", {"name": v, "type": "float", "category": "Ledge|ProcWin"})
        bq("set_variable_defaults", {"name": v, "default_value": "1.0"}) if False else None
        print("+var", v)

# ══ 함수 생성 ══
try:
    bq("add_function", {"function_name": GF})
    print("[F] +", GF)
except RuntimeError as e:
    print("[F]", str(e)[:100])

fn = graph(GF)
entry = next(nid for nid, n in fn.items() if "FunctionEntry" in n["class"])
made = {}


def add(key, ntype, extra, pos):
    p = {"graph_name": GF, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    made[key] = nid
    return nid


X, Y = 300, 0
add("vlmd", "VariableGet", {"variable_name": "LedgeMoveData"}, [X, Y + 300])
brk = add("brk", "BreakStruct", {"struct_type": "SBLedgeMoveData"}, [X + 200, Y + 300])
d = bq("get_node_details", {"graph_name": GF, "node_id": brk})
brk_pins = [p["name"] for p in d["pins"] if p["direction"] == "output"]
ang_pin = next(p for p in brk_pins if "Angle" in p)
prog_pin = next(p for p in brk_pins if "UnitMoveInProgress" in p or ("InProgress" in p))
print("[BRK]", ang_pin, "/", prog_pin)

add("getSp", "VariableGet", {"variable_name": "LedgeSplineRef"}, [X, Y - 100])
add("isv", "CallFunction", {"function_class": KSL, "function_name": "IsValid"}, [X + 200, Y - 100])
add("aAbs", "CallFunction", {"function_class": KML, "function_name": "Abs"}, [X + 450, Y + 300])
add("g1", "CallFunction", {"function_class": KML, "function_name": "Greater_DoubleDouble"}, [X + 620, Y + 240])
add("l1", "CallFunction", {"function_class": KML, "function_name": "Less_DoubleDouble"}, [X + 620, Y + 320])
add("g2", "CallFunction", {"function_class": KML, "function_name": "Greater_DoubleDouble"}, [X + 620, Y + 400])
add("l2", "CallFunction", {"function_class": KML, "function_name": "Less_DoubleDouble"}, [X + 620, Y + 480])
add("and1", "CallFunction", {"function_class": KML, "function_name": "BooleanAND"}, [X + 800, Y + 270])
add("and2", "CallFunction", {"function_class": KML, "function_name": "BooleanAND"}, [X + 800, Y + 440])
add("orD", "CallFunction", {"function_class": KML, "function_name": "BooleanOR"}, [X + 960, Y + 350])
add("andA", "CallFunction", {"function_class": KML, "function_name": "BooleanAND"}, [X + 1120, Y + 100])
add("andB", "CallFunction", {"function_class": KML, "function_name": "BooleanAND"}, [X + 1280, Y + 100])
# 스팬/진행도
add("gSd", "VariableGet", {"variable_name": "LedgeMoveStartDist"}, [X, Y + 600])
add("gTd", "VariableGet", {"variable_name": "LedgeMoveTargetDist"}, [X, Y + 680])
add("span", "CallFunction", {"function_class": KML, "function_name": "Subtract_DoubleDouble"}, [X + 200, Y + 620])
add("spanAbs", "CallFunction", {"function_class": KML, "function_name": "Abs"}, [X + 360, Y + 620])
add("spanOk", "CallFunction", {"function_class": KML, "function_name": "Greater_DoubleDouble"}, [X + 520, Y + 620])
add("owner", "CallFunction", {"function_class": "AnimInstance", "function_name": "TryGetPawnOwner"}, [X + 200, Y + 800])
add("loc", "CallFunction", {"function_class": "Actor", "function_name": "K2_GetActorLocation"}, [X + 400, Y + 800])
add("key", "CallFunction", {"function_class": SPL, "function_name": "FindInputKeyClosestToWorldLocation"}, [X + 600, Y + 800])
add("da", "CallFunction", {"function_class": SPL, "function_name": "GetDistanceAlongSplineAtSplineInputKey"}, [X + 800, Y + 800])
add("num", "CallFunction", {"function_class": KML, "function_name": "Subtract_DoubleDouble"}, [X + 1000, Y + 700])
add("div", "CallFunction", {"function_class": KML, "function_name": "Divide_DoubleDouble"}, [X + 1160, Y + 660])
add("prog", "CallFunction", {"function_class": KML, "function_name": "FClamp"}, [X + 1320, Y + 660])
# 창 판정 L/R
for s, yo in (("L", 900), ("R", 1100)):
    add("wg" + s, "CallFunction", {"function_class": KML, "function_name": "Greater_DoubleDouble"}, [X + 1500, Y + yo])
    add("wl" + s, "CallFunction", {"function_class": KML, "function_name": "Less_DoubleDouble"}, [X + 1500, Y + yo + 70])
    add("wand" + s, "CallFunction", {"function_class": KML, "function_name": "BooleanAND"}, [X + 1660, Y + yo + 30])
    add("sel" + s, "CallFunction", {"function_class": KML, "function_name": "SelectFloat"}, [X + 1820, Y + yo + 30])
# 게이트/Set
add("br", "Branch", {}, [X + 1450, Y - 100])
add("setL", "VariableSet", {"variable_name": "LedgeProcWinL"}, [X + 2050, Y - 150])
add("setR", "VariableSet", {"variable_name": "LedgeProcWinR"}, [X + 2250, Y - 150])
add("setL1", "VariableSet", {"variable_name": "LedgeProcWinL"}, [X + 2050, Y + 20])
add("setR1", "VariableSet", {"variable_name": "LedgeProcWinR"}, [X + 2250, Y + 20])


def pindef(key, pin, value):
    bq("set_pin_default", {"graph_name": GF, "node_id": made[key], "pin_name": pin, "value": value})


pindef("g1", "B", "22.5")
pindef("l1", "B", "67.5")
pindef("g2", "B", "112.5")
pindef("l2", "B", "157.5")
pindef("spanOk", "B", "1.0")
pindef("prog", "Min", "0.0")
pindef("prog", "Max", "1.0")
pindef("wgL", "B", WINL[0])
pindef("wlL", "B", WINL[1])
pindef("wgR", "B", WINR[0])
pindef("wlR", "B", WINR[1])
for s in ("L", "R"):
    pindef("sel" + s, "A", "0.0")
    pindef("sel" + s, "B", "1.0")
for k in ("setL1", "setR1"):
    pass  # 값 1.0 은 아래 set_pin_default
bq("set_pin_default", {"graph_name": GF, "node_id": made["setL1"], "pin_name": "LedgeProcWinL", "value": "1.0"})
bq("set_pin_default", {"graph_name": GF, "node_id": made["setR1"], "pin_name": "LedgeProcWinR", "value": "1.0"})


def wire(sk, sp, tk, tp):
    bq("connect_pins", {"graph_name": GF, "source_node": made.get(sk, sk), "source_pin": sp,
                        "target_node": made.get(tk, tk), "target_pin": tp})


wire("vlmd", "LedgeMoveData", "brk", "LedgeMoveData") if False else None
# BreakStruct 입력 핀명 확인 후 연결
bd = bq("get_node_details", {"graph_name": GF, "node_id": made["brk"]})
in_pin = next(p["name"] for p in bd["pins"] if p["direction"] == "input")
wire("vlmd", "LedgeMoveData", "brk", in_pin)
wire("getSp", "LedgeSplineRef", "isv", "Object")
wire("brk", ang_pin, "aAbs", "A")
wire("aAbs", "ReturnValue", "g1", "A")
wire("aAbs", "ReturnValue", "l1", "A")
wire("aAbs", "ReturnValue", "g2", "A")
wire("aAbs", "ReturnValue", "l2", "A")
wire("g1", "ReturnValue", "and1", "A")
wire("l1", "ReturnValue", "and1", "B")
wire("g2", "ReturnValue", "and2", "A")
wire("l2", "ReturnValue", "and2", "B")
wire("and1", "ReturnValue", "orD", "A")
wire("and2", "ReturnValue", "orD", "B")
wire("brk", prog_pin, "andA", "A")
wire("orD", "ReturnValue", "andA", "B")
wire("andA", "ReturnValue", "andB", "A")
wire("isv", "ReturnValue", "andB", "B")
wire("gTd", "LedgeMoveTargetDist", "span", "A")
wire("gSd", "LedgeMoveStartDist", "span", "B")
wire("span", "ReturnValue", "spanAbs", "A")
wire("spanAbs", "ReturnValue", "spanOk", "A")
# 최종 게이트 = andB AND spanOk
add("andC", "CallFunction", {"function_class": KML, "function_name": "BooleanAND"}, [X + 1360, Y - 40])
wire("andB", "ReturnValue", "andC", "A")
wire("spanOk", "ReturnValue", "andC", "B")
wire("andC", "ReturnValue", "br", "Condition")
# 진행도
wire("owner", "ReturnValue", "loc", "self")
wire("getSp", "LedgeSplineRef", "key", "self")
wire("loc", "ReturnValue", "key", "WorldLocation")
wire("getSp", "LedgeSplineRef", "da", "self")
wire("key", "ReturnValue", "da", "InKey")
wire("da", "ReturnValue", "num", "A")
wire("gSd", "LedgeMoveStartDist", "num", "B")
wire("num", "ReturnValue", "div", "A")
wire("span", "ReturnValue", "div", "B")
wire("div", "ReturnValue", "prog", "Value")
for s in ("L", "R"):
    wire("prog", "ReturnValue", "wg" + s, "A")
    wire("prog", "ReturnValue", "wl" + s, "A")
    wire("wg" + s, "ReturnValue", "wand" + s, "A")
    wire("wl" + s, "ReturnValue", "wand" + s, "B")
    wire("wand" + s, "ReturnValue", "sel" + s, "bPickA")
wire("selL", "ReturnValue", "setL", "LedgeProcWinL")
wire("selR", "ReturnValue", "setR", "LedgeProcWinR")
# exec
wire(entry, "then", "br", "execute")
wire("br", "then", "setL", "execute")
wire("setL", "then", "setR", "execute")
wire("br", "else", "setL1", "execute")
wire("setL1", "then", "setR1", "execute")
print("[F] 내부 배선 완료")

r = bq("compile_blueprint", {})
print("[COMPILE-1]", json.dumps(r)[:120])

# ══ HandAlpha: 호출 + 곱 삽입 ══
r = bq("add_node", {"graph_name": GA, "node_type": "CallFunction",
                    "function_class": "PC_01_ABP_C", "function_name": GF, "position": [-300, 0]})
callnid = r.get("id") or r.get("node_id")
print("[CALL]", callnid)
ha = graph(GA)
E = "K2Node_FunctionEntry_0"
first = pins(ha, E)["then"]["connected_to"][0]
fn_, fp_ = first.split(".", 1)
bq("disconnect_pins", {"graph_name": GA, "source_node": E, "source_pin": "then", "target_node": fn_, "target_pin": fp_})
bq("connect_pins", {"graph_name": GA, "source_node": E, "source_pin": "then", "target_node": callnid, "target_pin": "execute"})
bq("connect_pins", {"graph_name": GA, "source_node": callnid, "source_pin": "then", "target_node": fn_, "target_pin": fp_})
made2 = {}
for s, clampn, seln in (("L", "K2Node_CallFunction_95", "K2Node_CallFunction_194"),
                        ("R", "K2Node_CallFunction_110", "K2Node_CallFunction_195")):
    r = bq("add_node", {"graph_name": GA, "node_type": "VariableGet", "variable_name": "LedgeProcWin" + s, "position": [700, 300 if s == "L" else 500]})
    gv = r.get("id") or r.get("node_id")
    r = bq("add_node", {"graph_name": GA, "node_type": "CallFunction", "function_class": KML,
                        "function_name": "Multiply_DoubleDouble", "position": [850, 300 if s == "L" else 500]})
    mul = r.get("id") or r.get("node_id")
    bq("disconnect_pins", {"graph_name": GA, "source_node": clampn, "source_pin": "ReturnValue", "target_node": seln, "target_pin": "A"})
    bq("connect_pins", {"graph_name": GA, "source_node": clampn, "source_pin": "ReturnValue", "target_node": mul, "target_pin": "A"})
    bq("connect_pins", {"graph_name": GA, "source_node": gv, "source_pin": "LedgeProcWin" + s, "target_node": mul, "target_pin": "B"})
    bq("connect_pins", {"graph_name": GA, "source_node": mul, "source_pin": "ReturnValue", "target_node": seln, "target_pin": "A"})
    made2[s] = (gv, mul, seln)
    print("[MUL]", s, mul)
ha2 = graph(GA)
ok = True
for s, (gv, mul, seln) in made2.items():
    got = pins(ha2, seln)["A"]["connected_to"]
    good = got == [mul + ".ReturnValue"]
    ok = ok and good
    print("[CHK]", "OK " if good else "FAIL", s, got)
assert ok
r = bq("compile_blueprint", {})
print("[COMPILE-2]", json.dumps(r)[:250])
