# Phase C M5 — 정지/도착 몸기준을 스플라인에 스냅 (2026-07-23)
# 실측 근거: 경사에서 몸기준(메시 상대 고정점 ~167cm)이 바에서 +57cm 이탈 (몸기준 Z 1019.5 vs 바 962)
#            → 가드 A경로(정지 추종) 타깃이 바를 벗어나 리치클램프(55)가 손을 끊음 = "팔 안따라감"
# 수정: LedgeIdleSnapL/R = FindLocationClosest(SplineRef, 몸기준L/R) 를 exec 게이트(IsValid)에서 Set,
#       CF_78.A / CF_84.A ← Select(SnapValid ? Snap : 몸기준raw). 슬라이드(B경로)는 무변경.
# 실행: py phase_c_m5_idlesnap.py [apply]
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
KML = "KismetMathLibrary"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

BODY_L = "K2Node_CallFunction_96"   # 몸기준 L TransformLocation
BODY_R = "K2Node_CallFunction_92"
GUARD_L = "K2Node_CallFunction_78"  # 가드 SelectVector L (.A ← 몸기준)
GUARD_R = "K2Node_CallFunction_84"
PRED = ("K2Node_VariableSet_3", "then")  # Set WorldL 앞 exec 선행 (M4 확인값)


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


nodes = {n["id"]: n for n in bq("get_graph_data", {"graph_name": GH})["nodes"]}


def pinsof(nid):
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


# 프리플라이트
brS = pinsof(PRED[0])["then"]["connected_to"]
assert len(brS) == 1, "PRED.then 소스 상이: " + str(brS)
BRS = brS[0].split(".")[0]
assert nodes[BRS]["class"] == "K2Node_IfThenElse", "PRED 후속이 Branch 아님: " + BRS
assert pinsof(GUARD_L)["A"]["connected_to"] == [BODY_L + ".ReturnValue"], "GUARD_L.A 상이"
assert pinsof(GUARD_R)["A"]["connected_to"] == [BODY_R + ".ReturnValue"], "GUARD_R.A 상이"
print("[PF] brS =", BRS, "| GUARD A 배선 확인")

if not APPLY:
    print("== DRY-RUN OK ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"
exp = bq("export_graph", {"graph_name": GH})
with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/phaseC_m5_backup_%s.json" % GH, "w", encoding="utf-8") as f:
    json.dump(exp, f)
print("[BK] 백업 완료")

vars_d = bq("get_variables", {})
vnames = {v["name"] for v in vars_d["variables"]}
for name, t in (("LedgeIdleSnapL", "struct:Vector"), ("LedgeIdleSnapR", "struct:Vector"),
                ("LedgeSnapValid", "bool")):
    if name not in vnames:
        bq("add_variable", {"name": name, "type": t, "category": "Ledge|PhaseC"})
        print("[VAR] +", name)


def add(ntype, extra, pos):
    p = {"graph_name": GH, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    return r.get("id") or r.get("node_id")


def wire(sn, sp, tn, tp):
    bq("connect_pins", {"graph_name": GH, "source_node": sn, "source_pin": sp,
                        "target_node": tn, "target_pin": tp})


def disc(sn, sp, tn, tp):
    bq("disconnect_pins", {"graph_name": GH, "source_node": sn, "source_pin": sp,
                           "target_node": tn, "target_pin": tp})


X, Y = -5000, 6400
vgs = add("VariableGet", {"variable_name": "LedgeSplineRef"}, [X, Y])
isv = add("CallFunction", {"function_class": "KismetSystemLibrary", "function_name": "IsValid"}, [X + 200, Y])
wire(vgs, "LedgeSplineRef", isv, "Object")
brSnap = add("Branch", {}, [X + 400, Y - 120])
wire(isv, "ReturnValue", brSnap, "Condition")
fL = add("CallFunction", {"function_class": "SplineComponent", "function_name": "FindLocationClosestToWorldLocation"}, [X + 400, Y + 100])
fR = add("CallFunction", {"function_class": "SplineComponent", "function_name": "FindLocationClosestToWorldLocation"}, [X + 400, Y + 260])
for f in (fL, fR):
    wire(vgs, "LedgeSplineRef", f, "self")
    bq("set_pin_default", {"graph_name": GH, "node_id": f, "pin_name": "CoordinateSpace", "value": "World"})
wire(BODY_L, "ReturnValue", fL, "WorldLocation")
wire(BODY_R, "ReturnValue", fR, "WorldLocation")
sL = add("VariableSet", {"variable_name": "LedgeIdleSnapL"}, [X + 700, Y - 120])
sR = add("VariableSet", {"variable_name": "LedgeIdleSnapR"}, [X + 950, Y - 120])
wire(fL, "ReturnValue", sL, "LedgeIdleSnapL")
wire(fR, "ReturnValue", sR, "LedgeIdleSnapR")
svT = add("VariableSet", {"variable_name": "LedgeSnapValid"}, [X + 1200, Y - 120])
bq("set_pin_default", {"graph_name": GH, "node_id": svT, "pin_name": "LedgeSnapValid", "value": "true"})
svF = add("VariableSet", {"variable_name": "LedgeSnapValid"}, [X + 700, Y - 280])
bq("set_pin_default", {"graph_name": GH, "node_id": svF, "pin_name": "LedgeSnapValid", "value": "false"})

# exec 스플라이스: PRED → brSnap → (then: sL→sR→svT→BRS / else: svF→BRS)
disc(PRED[0], PRED[1], BRS, "execute")
wire(PRED[0], PRED[1], brSnap, "execute")
wire(brSnap, "then", sL, "execute")
wire(sL, "then", sR, "execute")
wire(sR, "then", svT, "execute")
wire(svT, "then", BRS, "execute")
wire(brSnap, "else", svF, "execute")
wire(svF, "then", BRS, "execute")

# 소비: GUARD.A ← Select(SnapValid ? Snap : 몸기준raw)
gvv = add("VariableGet", {"variable_name": "LedgeSnapValid"}, [X + 700, Y + 420])
for side, body, guard, var, yy in (("L", BODY_L, GUARD_L, "LedgeIdleSnapL", 480),
                                   ("R", BODY_R, GUARD_R, "LedgeIdleSnapR", 620)):
    gv = add("VariableGet", {"variable_name": var}, [X + 850, Y + yy])
    sel = add("CallFunction", {"function_class": KML, "function_name": "SelectVector"}, [X + 1100, Y + yy])
    wire(gv, var, sel, "A")
    wire(body, "ReturnValue", sel, "B")
    wire(gvv, "LedgeSnapValid", sel, "bPickA")
    disc(body, "ReturnValue", guard, "A")
    wire(sel, "ReturnValue", guard, "A")
    print("[SNAP]", side, "GUARD.A ← Select(SnapValid ? Snap : raw)")

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r, ensure_ascii=False)[:200])
