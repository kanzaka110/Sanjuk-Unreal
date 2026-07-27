# SlopeZ 체인 함수 분리 (2026-07-24) — Ledge_SlopeZ(WorldNowL, WorldNowR) 신설
# 프로듀서 체인(게이트/거리/클램프/FMax/스무딩/Set)만 이동. 소비측(getDz→MakeVec→Add→VInterp)은 잔류
# 현재값 보존: C0L -8.66 / C0R -8.79 / 게이트3D 45 / 클램프 ±35 / K 0.25 / 등속 45
# 실행: py slopez_extract_fn.py apply
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
GF = "Ledge_SlopeZ"
KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"
SPL = "SplineComponent"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

# 구 프로듀서 체인 (오늘 세션 ID — 재조회로 검증)
OLD = {
    "br": "K2Node_IfThenElse_5", "isv": "K2Node_CallFunction_36", "getSp": "K2Node_VariableGet_15",
    "fcl": "K2Node_CallFunction_42", "bkCL": "K2Node_CallFunction_139", "bkWL": "K2Node_CallFunction_140",
    "addL": "K2Node_CallFunction_141", "subL": "K2Node_CallFunction_142",
    "fcr": "K2Node_CallFunction_157", "bkCR": "K2Node_CallFunction_158", "bkWR": "K2Node_CallFunction_179",
    "addR": "K2Node_CallFunction_180", "subR": "K2Node_CallFunction_181",
    "setL": "K2Node_VariableSet_15", "setR": "K2Node_VariableSet_16", "setB": "K2Node_VariableSet_19",
    "setL0": "K2Node_VariableSet_22", "setR0": "K2Node_VariableSet_23", "setB0": "K2Node_VariableSet_24",
    "ndL": "K2Node_CallFunction_234", "ndR": "K2Node_CallFunction_235",
    "leL": "K2Node_CallFunction_194", "leR": "K2Node_CallFunction_216",
    "clL": "K2Node_CallFunction_195", "clR": "K2Node_CallFunction_217",
    "selL": "K2Node_CallFunction_197", "selR": "K2Node_CallFunction_233",
    "fmax": "K2Node_CallFunction_251", "dsub": "K2Node_CallFunction_252", "dabs": "K2Node_CallFunction_253",
    "mulK": "K2Node_CallFunction_254", "addF": "K2Node_CallFunction_255",
    "clB": "K2Node_CallFunction_242", "selB": "K2Node_CallFunction_243",
    "getTA": "K2Node_VariableGet_78", "getPrev": "K2Node_VariableGet_79", "fint": "K2Node_CallFunction_246",
}
WNL, WNR = "K2Node_CallFunction_55", "K2Node_CallFunction_91"
M4BR = "K2Node_IfThenElse_4"


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


nodes = graph(GH)
missing = [k for k, v in OLD.items() if v not in nodes]
assert not missing, "구 노드 미발견: " + json.dumps(missing)
# exec 전제: 상류 → br, setB/setB0 → M4BR
ups = pins(nodes, OLD["br"])["execute"]["connected_to"]
assert len(ups) == 1, "br exec 소스 다중: " + json.dumps(ups)
UP_N, UP_P = ups[0].split(".", 1)
print("[PF] 상류:", UP_N + "." + UP_P, "| M4:", M4BR)

if not APPLY:
    print("== dry-run 종료 ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중"

# ══ 1) 함수 생성 ══
try:
    bq("add_function", {"function_name": GF})
    print("[F] +", GF)
except RuntimeError as e:
    print("[F] add_function:", str(e)[:100])
bq("set_function_params", {"function_name": GF,
    "inputs": [{"name": "WorldNowL", "type": "struct:Vector"}, {"name": "WorldNowR", "type": "struct:Vector"}]})
print("[F] params set")

fn = graph(GF)
entry = next(nid for nid, n in fn.items() if "FunctionEntry" in n["class"])
print("[F] entry:", entry)

# ══ 2) 함수 내부 빌드 ══
made = {}
X, Y = 300, 0


def add(key, ntype, extra, pos):
    p = {"graph_name": GF, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    made[key] = nid
    print("[ADD]", key, "->", nid)
    return nid


add("getSp", "VariableGet", {"variable_name": "LedgeSplineRef"}, [X, Y - 150])
add("isv", "CallFunction", {"function_class": KSL, "function_name": "IsValid"}, [X + 200, Y - 150])
add("br", "Branch", {}, [X + 400, Y - 150])
for side, yo in (("L", 100), ("R", 420)):
    add("fc" + side, "CallFunction", {"function_class": SPL, "function_name": "FindLocationClosestToWorldLocation"}, [X + 200, Y + yo])
    add("bkC" + side, "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 450, Y + yo])
    add("bkW" + side, "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 450, Y + yo + 120])
    add("add" + side, "CallFunction", {"function_class": KML, "function_name": "Add_DoubleDouble"}, [X + 650, Y + yo])
    add("sub" + side, "CallFunction", {"function_class": KML, "function_name": "Subtract_DoubleDouble"}, [X + 830, Y + yo])
    add("nd" + side, "CallFunction", {"function_class": KML, "function_name": "Vector_Distance"}, [X + 650, Y + yo + 150])
    add("le" + side, "CallFunction", {"function_class": KML, "function_name": "LessEqual_DoubleDouble"}, [X + 830, Y + yo + 150])
    add("cl" + side, "CallFunction", {"function_class": KML, "function_name": "FClamp"}, [X + 1010, Y + yo])
    add("sel" + side, "CallFunction", {"function_class": KML, "function_name": "SelectFloat"}, [X + 1190, Y + yo])
add("fmax", "CallFunction", {"function_class": KML, "function_name": "FMax"}, [X + 1400, Y + 200])
add("dsub", "CallFunction", {"function_class": KML, "function_name": "Subtract_DoubleDouble"}, [X + 1400, Y + 330])
add("dabs", "CallFunction", {"function_class": KML, "function_name": "Abs"}, [X + 1560, Y + 330])
add("mulK", "CallFunction", {"function_class": KML, "function_name": "Multiply_DoubleDouble"}, [X + 1720, Y + 330])
add("addF", "CallFunction", {"function_class": KML, "function_name": "Add_DoubleDouble"}, [X + 1880, Y + 250])
add("clB", "CallFunction", {"function_class": KML, "function_name": "FClamp"}, [X + 2040, Y + 250])
add("getTA", "VariableGet", {"variable_name": "LedgeTransitActive"}, [X + 2040, Y + 380])
add("selB", "CallFunction", {"function_class": KML, "function_name": "SelectFloat"}, [X + 2220, Y + 250])
add("getPrev", "VariableGet", {"variable_name": "LedgeSlopeDzBody"}, [X + 2220, Y + 120])
add("dt", "CallFunction", {"function_class": "KismetSystemLibrary", "function_name": "K2_GetWorldDeltaSeconds"}, [X + 2220, Y + 500])
add("fint", "CallFunction", {"function_class": KML, "function_name": "FInterpTo_Constant"}, [X + 2420, Y + 250])
add("setL", "VariableSet", {"variable_name": "LedgeSlopeDzL"}, [X + 700, Y - 250])
add("setR", "VariableSet", {"variable_name": "LedgeSlopeDzR"}, [X + 950, Y - 250])
add("setB", "VariableSet", {"variable_name": "LedgeSlopeDzBody"}, [X + 1200, Y - 250])
add("setL0", "VariableSet", {"variable_name": "LedgeSlopeDzL"}, [X + 700, Y - 80])
add("setR0", "VariableSet", {"variable_name": "LedgeSlopeDzR"}, [X + 950, Y - 80])
add("setB0", "VariableSet", {"variable_name": "LedgeSlopeDzBody"}, [X + 1200, Y - 80])


def pindef(key, pin, value):
    bq("set_pin_default", {"graph_name": GF, "node_id": made[key], "pin_name": pin, "value": value})


pindef("fcL", "CoordinateSpace", "World")
pindef("fcR", "CoordinateSpace", "World")
pindef("addL", "B", "-8.66")
pindef("addR", "B", "-8.79")
for s in ("L", "R"):
    pindef("le" + s, "B", "45.0")
    pindef("cl" + s, "Min", "-35.0")
    pindef("cl" + s, "Max", "35.0")
    pindef("sel" + s, "B", "0.0")
pindef("mulK", "B", "0.25")
pindef("clB", "Min", "-35.0")
pindef("clB", "Max", "35.0")
pindef("selB", "A", "0.0")
pindef("fint", "InterpSpeed", "45.0")
print("[DEF] 완료")


def wire(sk, sp, tk, tp):
    src = made.get(sk, sk)
    tgt = made.get(tk, tk)
    bq("connect_pins", {"graph_name": GF, "source_node": src, "source_pin": sp,
                        "target_node": tgt, "target_pin": tp})


# 데이터
wire("getSp", "LedgeSplineRef", "isv", "Object")
wire("isv", "ReturnValue", "br", "Condition")
for side, WN in (("L", "WorldNowL"), ("R", "WorldNowR")):
    wire("getSp", "LedgeSplineRef", "fc" + side, "self")
    wire(entry, WN, "fc" + side, "WorldLocation")
    wire("fc" + side, "ReturnValue", "bkC" + side, "InVec")
    wire(entry, WN, "bkW" + side, "InVec")
    wire("bkC" + side, "Z", "add" + side, "A")
    wire("add" + side, "ReturnValue", "sub" + side, "A")
    wire("bkW" + side, "Z", "sub" + side, "B")
    wire("fc" + side, "ReturnValue", "nd" + side, "V1")
    wire(entry, WN, "nd" + side, "V2")
    wire("nd" + side, "ReturnValue", "le" + side, "A")
    wire("sub" + side, "ReturnValue", "cl" + side, "Value")
    wire("cl" + side, "ReturnValue", "sel" + side, "A")
    wire("le" + side, "ReturnValue", "sel" + side, "bPickA")
wire("selL", "ReturnValue", "setL", "LedgeSlopeDzL")
wire("selR", "ReturnValue", "setR", "LedgeSlopeDzR")
wire("selL", "ReturnValue", "fmax", "A")
wire("selR", "ReturnValue", "fmax", "B")
wire("selL", "ReturnValue", "dsub", "A")
wire("selR", "ReturnValue", "dsub", "B")
wire("dsub", "ReturnValue", "dabs", "A")
wire("dabs", "ReturnValue", "mulK", "A")
wire("fmax", "ReturnValue", "addF", "A")
wire("mulK", "ReturnValue", "addF", "B")
wire("addF", "ReturnValue", "clB", "Value")
wire("clB", "ReturnValue", "selB", "B")
wire("getTA", "LedgeTransitActive", "selB", "bPickA")
wire("getPrev", "LedgeSlopeDzBody", "fint", "Current")
wire("selB", "ReturnValue", "fint", "Target")
wire("dt", "ReturnValue", "fint", "DeltaTime")
wire("fint", "ReturnValue", "setB", "LedgeSlopeDzBody")
# exec: entry → br / then → setL→setR→setB / else → setL0→setR0→setB0
wire(entry, "then", "br", "execute")
wire("br", "then", "setL", "execute")
wire("setL", "then", "setR", "execute")
wire("setR", "then", "setB", "execute")
wire("br", "else", "setL0", "execute")
wire("setL0", "then", "setR0", "execute")
wire("setR0", "then", "setB0", "execute")
print("[WIRE] 함수 내부 완료")

# ══ 3) HandTarget: 호출 스플라이스 ══
r = bq("add_node", {"graph_name": GH, "node_type": "CallFunction",
                    "function_class": "PC_01_ABP_C", "function_name": GF, "position": [4700, -2100]})
callnid = r.get("id") or r.get("node_id")
print("[CALL] +", callnid)
bq("connect_pins", {"graph_name": GH, "source_node": WNL, "source_pin": "ReturnValue",
                    "target_node": callnid, "target_pin": "WorldNowL"})
bq("connect_pins", {"graph_name": GH, "source_node": WNR, "source_pin": "ReturnValue",
                    "target_node": callnid, "target_pin": "WorldNowR"})
bq("disconnect_pins", {"graph_name": GH, "source_node": UP_N, "source_pin": UP_P,
                       "target_node": OLD["br"], "target_pin": "execute"})
bq("connect_pins", {"graph_name": GH, "source_node": UP_N, "source_pin": UP_P,
                    "target_node": callnid, "target_pin": "execute"})
bq("connect_pins", {"graph_name": GH, "source_node": callnid, "source_pin": "then",
                    "target_node": M4BR, "target_pin": "execute"})
print("[CALL] 스플라이스 완료:", UP_N + "." + UP_P, "->", callnid, "->", M4BR)

# ══ 4) 구 체인 삭제 (Set→브랜치→피더 순, 개별 재조회) ══
del_order = ["setL", "setR", "setB", "setL0", "setR0", "setB0", "br",
             "fint", "getPrev", "selB", "getTA", "clB", "addF", "mulK", "dabs", "dsub", "fmax",
             "selL", "selR", "leL", "leR", "ndL", "ndR", "clL", "clR",
             "subL", "subR", "addL", "addR", "bkCL", "bkCR", "bkWL", "bkWR",
             "fcl", "fcr", "isv", "getSp"]
for key in del_order:
    nid = OLD[key]
    cur = graph(GH)
    if nid not in cur:
        print("[DEL] 이미 없음:", key)
        continue
    outs = [c for p in cur[nid]["pins"] if p["direction"] == "output" and not (p.get("is_exec") or p.get("type") == "exec")
            for c in p.get("connected_to", [])]
    if outs:
        print("[DEL] SKIP", key, "데이터 소비자:", outs[:3])
        continue
    bq("remove_node", {"graph_name": GH, "node_id": nid})
    print("[DEL]", key, nid)

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:300])
