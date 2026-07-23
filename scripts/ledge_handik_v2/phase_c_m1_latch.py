# Phase C M1 — 곡면(스플라인) 슬라이드: 래치 인프라 구축 (2026-07-23)
# 근거: 원통 실측 — 직선 외삽 도착지 42cm 오차 / 스플라인 dist_along == lmd.CurrentDistance
# 설계 v2 (루프/로컬변수 없음):
#   Td변경 에지 프레임에만 Branch로 래치 —
#   ①오버랩(SBZoneEnvActor 필터) 후보 0/1 최근접 스플라인 → LedgeSplineRef
#   ②Break(LedgeMoveData).UnitMoveStart/TargetDistance → LedgeMoveStartDist/TargetDist
#   ③GetTransformAtDistanceAlongSpline(sd) → LedgeMoveStartT
#   M1은 소비자 없음 = 거동 무변화. M2에서 퍼프레임 샘플링 체인이 소비.
# 실행: py phase_c_m1_latch.py [apply]   (기본 dry-run)
# ⚠ 로컬 python 전용 — 에디터 콘솔(py) 실행 금지 (자기 서버 데드락). apply는 PIE 종료 후.
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
KML = "KismetMathLibrary"
SPL = "SplineComponent"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"
CLEAN_DEBUG_NODES = ["K2Node_CallFunction_35", "K2Node_CallFunction_36", "K2Node_CallArrayFunction_0"]


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


def graph_nodes(g):
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": g})["nodes"]}


def pins(n):
    return {p["name"]: p for p in n.get("pins", [])}


def pie_on():
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


# ══ 프리플라이트 ══════════════════════════════════════
nodes = graph_nodes(GH)

vs_umv = None
for nid, n in nodes.items():
    if n["class"] == "K2Node_VariableSet" and any(p["name"] == "LedgeUnitMoveVec" for p in n.get("pins", [])):
        vs_umv = nid
assert vs_umv, "Set LedgeUnitMoveVec 없음"
umv_then = pins(nodes[vs_umv])["then"]
assert umv_then["connected_to"], "Set UnitMoveVec.then 후속 없음"
next_node, next_pin = umv_then["connected_to"][0].rsplit(".", 1)
print("[PF] Set UnitMoveVec:", vs_umv, "-> next:", next_node + "." + next_pin)

# Td변경 에지: NotEqual_DoubleDouble, 한쪽 입력이 Get LedgeDestTd
desttd_gets = [nid for nid, n in nodes.items()
               if n["class"] == "K2Node_VariableGet" and any(p["name"] == "LedgeDestTd" for p in n.get("pins", []))]
td_edge = None
for nid, n in nodes.items():
    if n["class"] == "K2Node_CallFunction" and n.get("function") == "NotEqual_DoubleDouble":
        for p in n.get("pins", []):
            if p["direction"] == "input" and any(c.split(".")[0] in desttd_gets for c in p.get("connected_to", [])):
                td_edge = nid
assert td_edge, "Td에지 NotEqual 미발견"
td_out = pins(nodes[td_edge])["ReturnValue"]
print("[PF] Td-edge NotEqual:", td_edge, "consumers:", td_out["connected_to"])

vars_d = bq("get_variables", {})
vnames = {v["name"] for v in vars_d["variables"]}
assert "LedgeMoveData" in vnames, "LedgeMoveData 변수 없음"
NEW_VARS = [("LedgeSplineRef", {"type": "object:SplineComponent"}),
            ("LedgeMoveStartDist", {"type": "float"}),
            ("LedgeMoveTargetDist", {"type": "float"}),
            ("LedgeMoveStartT", {"type": "struct:Transform"})]
print("[PF] 신규변수 중복:", [n for n, _ in NEW_VARS if n in vnames] or "없음")

if not APPLY:
    print("== DRY-RUN OK — 'apply' 로 실행 ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply (remove_node/compile 크래시 방지)"

# ══ 백업 ══════════════════════════════════════
for g in (GH, "Ledge_FootTarget"):
    exp = bq("export_graph", {"graph_name": g})
    fn = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/phaseC_backup_%s.json" % g
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(exp, f)
    print("[BK]", fn)

# ══ 디버그 테스트 노드 정리 (LedgeDebugs, PIE off 확인됨) ══
dbg = graph_nodes("LedgeDebugs")
for nid in CLEAN_DEBUG_NODES:
    if nid in dbg:
        bq("remove_node", {"graph_name": "LedgeDebugs", "node_id": nid})
        print("[CLEAN]", nid)

# ══ 변수 생성 ══════════════════════════════════════
for name, spec in NEW_VARS:
    if name in vnames:
        print("[VAR] skip", name)
        continue
    p = {"name": name, "category": "Ledge|PhaseC"}
    p.update(spec)
    bq("add_variable", p)
    print("[VAR] +", name)

# ══ 노드 생성 ══════════════════════════════════════
X, Y = -4600, 3600
made = {}


def add(key, ntype, extra, pos):
    p = {"graph_name": GH, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    made[key] = {"id": nid, "pins": {pp["name"]: pp for pp in r.get("pins", [])}}
    print("[ADD]", key, "->", nid)
    return nid


def arr_get(key, pos, index):
    nid = add(key, "CallArrayFunction", {}, pos)
    bq("set_node_property", {"graph_name": GH, "node_id": nid, "property_name": "FunctionReference",
        "value": "(MemberParent=\"/Script/CoreUObject.Class'/Script/Engine.KismetArrayLibrary'\",MemberName=\"Array_Get\")"})
    if index != 0:
        bq("set_pin_default", {"graph_name": GH, "node_id": nid, "pin_name": "Index", "value": str(index)})
    d = bq("get_node_details", {"graph_name": GH, "node_id": nid})
    made[key]["pins"] = {pp["name"]: pp for pp in d.get("pins", [])}
    return nid


add("owner", "CallFunction", {"function_class": "AnimInstance", "function_name": "TryGetPawnOwner"}, [X, Y])
add("loc", "CallFunction", {"function_class": "Actor", "function_name": "K2_GetActorLocation"}, [X + 250, Y + 150])
add("ov", "CallFunction", {"function_class": "Actor", "function_name": "GetOverlappingActors"}, [X + 250, Y])
arr_get("get0", [X + 550, Y - 50], 0)
arr_get("get1", [X + 550, Y + 100], 1)
add("s0", "CallFunction", {"function_class": "Actor", "function_name": "GetComponentByClass"}, [X + 800, Y - 50])
add("s1", "CallFunction", {"function_class": "Actor", "function_name": "GetComponentByClass"}, [X + 800, Y + 100])
add("c0", "CallFunction", {"function_class": SPL, "function_name": "FindLocationClosestToWorldLocation"}, [X + 1080, Y - 50])
add("c1", "CallFunction", {"function_class": SPL, "function_name": "FindLocationClosestToWorldLocation"}, [X + 1080, Y + 100])
add("d0", "CallFunction", {"function_class": KML, "function_name": "Vector_Distance"}, [X + 1360, Y - 50])
add("d1", "CallFunction", {"function_class": KML, "function_name": "Vector_Distance"}, [X + 1360, Y + 100])
add("le", "CallFunction", {"function_class": KML, "function_name": "LessEqual_DoubleDouble"}, [X + 1580, Y + 20])
add("selI", "CallFunction", {"function_class": KML, "function_name": "SelectInt"}, [X + 1760, Y + 20])
arr_get("get2", [X + 1950, Y + 20], 0)
add("ssel", "CallFunction", {"function_class": "Actor", "function_name": "GetComponentByClass"}, [X + 2200, Y + 20])
add("vlmd", "VariableGet", {"variable_name": "LedgeMoveData"}, [X + 1950, Y + 300])
add("brk", "BreakStruct", {"struct_type": "SBLedgeMoveData"}, [X + 2200, Y + 300])
add("xt", "CallFunction", {"function_class": SPL, "function_name": "GetTransformAtDistanceAlongSpline"}, [X + 2500, Y + 150])
add("br", "Branch", {}, [X + 2500, Y - 250])
add("setSp", "VariableSet", {"variable_name": "LedgeSplineRef"}, [X + 2800, Y - 250])
add("setSd", "VariableSet", {"variable_name": "LedgeMoveStartDist"}, [X + 3100, Y - 250])
add("setTd", "VariableSet", {"variable_name": "LedgeMoveTargetDist"}, [X + 3400, Y - 250])
add("setT", "VariableSet", {"variable_name": "LedgeMoveStartT"}, [X + 3700, Y - 250])

# ══ 핀 디폴트 ══════════════════════════════════════
def pindef(key, pin, value):
    bq("set_pin_default", {"graph_name": GH, "node_id": made[key]["id"], "pin_name": pin, "value": value})
    print("[DEF]", key, pin, "=", value)

pindef("ov", "ClassFilter", "/Script/SB2.SBZoneEnvActor")
for k in ("s0", "s1", "ssel"):
    pindef(k, "ComponentClass", "/Script/Engine.SplineComponent")
for k in ("c0", "c1"):
    pindef(k, "CoordinateSpace", "World")
pindef("xt", "CoordinateSpace", "World")
pindef("selI", "B", "1")

# ══ 배선 ══════════════════════════════════════
def wire(sk, sp, tk, tp):
    src = made[sk]["id"] if sk in made else sk
    tgt = made[tk]["id"] if tk in made else tk
    bq("connect_pins", {"graph_name": GH, "source_node": src, "source_pin": sp,
                        "target_node": tgt, "target_pin": tp})
    print("[WIRE]", sk + "." + sp, "->", tk + "." + tp)

# 데이터
wire("owner", "ReturnValue", "loc", "self")
wire("owner", "ReturnValue", "ov", "self")
wire("ov", "OverlappingActors", "get0", "TargetArray")
wire("ov", "OverlappingActors", "get1", "TargetArray")
wire("get0", "Item", "s0", "self")
wire("get1", "Item", "s1", "self")
wire("s0", "ReturnValue", "c0", "self")
wire("s1", "ReturnValue", "c1", "self")
wire("loc", "ReturnValue", "c0", "WorldLocation")
wire("loc", "ReturnValue", "c1", "WorldLocation")
wire("c0", "ReturnValue", "d0", "V1")
wire("loc", "ReturnValue", "d0", "V2")
wire("c1", "ReturnValue", "d1", "V1")
wire("loc", "ReturnValue", "d1", "V2")
wire("d0", "ReturnValue", "le", "A")
wire("d1", "ReturnValue", "le", "B")
# SelectInt bool 핀 이름 탐지 (bPickA / bSelectA 버전차)
sel_pins = made["selI"]["pins"]
boolpin = next(p for p in sel_pins if sel_pins[p]["type"] == "bool" and sel_pins[p]["direction"] == "input")
wire("le", "ReturnValue", "selI", boolpin)
wire("ov", "OverlappingActors", "get2", "TargetArray")
wire("selI", "ReturnValue", "get2", "Index")
wire("get2", "Item", "ssel", "self")
# Break LedgeMoveData — 입력 struct 핀 이름 탐지
vlmd_out = next(p["name"] for p in made["vlmd"]["pins"].values() if p["direction"] == "output")
brk_in = next(p["name"] for p in made["brk"]["pins"].values()
              if p["direction"] == "input" and "struct" in p.get("type", ""))
wire("vlmd", vlmd_out, "brk", brk_in)
wire("ssel", "ReturnValue", "xt", "self")
wire("brk", "UnitMoveStartDistance", "xt", "Distance")
# 래치 값
wire("ssel", "ReturnValue", "setSp", "LedgeSplineRef")
wire("brk", "UnitMoveStartDistance", "setSd", "LedgeMoveStartDist")
wire("brk", "UnitMoveTargetDistance", "setTd", "LedgeMoveTargetDist")
wire("xt", "ReturnValue", "setT", "LedgeMoveStartT")
# 에지 게이트 + exec 스플라이스
wire(td_edge, "ReturnValue", "br", "Condition")
wire(vs_umv, "then", "br", "execute")
wire("br", "then", "setSp", "execute")
wire("setSp", "then", "setSd", "execute")
wire("setSd", "then", "setTd", "execute")
wire("setTd", "then", "setT", "execute")
wire("setT", "then", next_node, next_pin)
wire("br", "else", next_node, next_pin)

# ══ 검증: 링크 실재 확인 (connect_pins 무음드랍 대비) ══
after = graph_nodes(GH)
MUST = [
    (made["ov"]["id"], "OverlappingActors", made["get0"]["id"]),
    (made["get2"]["id"], "Item", made["ssel"]["id"]),
    (made["ssel"]["id"], "ReturnValue", made["setSp"]["id"]),
    (made["brk"]["id"], "UnitMoveStartDistance", made["setSd"]["id"]),
    (made["brk"]["id"], "UnitMoveTargetDistance", made["setTd"]["id"]),
    (made["xt"]["id"], "ReturnValue", made["setT"]["id"]),
    (vs_umv, "then", made["br"]["id"]),
    (made["setT"]["id"], "then", next_node),
]
fails = []
for src, pin, tgt in MUST:
    p = pins(after[src]).get(pin, {})
    if not any(c.startswith(tgt + ".") for c in p.get("connected_to", [])):
        fails.append((src, pin, tgt))
if fails:
    print("!! 링크 검증 실패:", fails)
    sys.exit(1)
print("[VERIFY] 필수 링크 전부 확인")

# 핀 디폴트 검증 (무음 no-op 대비)
chk = pins(after[made["ov"]["id"]]).get("ClassFilter", {})
print("[VERIFY] ClassFilter =", chk.get("default_value", "?"))
chk2 = pins(after[made["ssel"]["id"]]).get("ComponentClass", {})
print("[VERIFY] ssel.ComponentClass =", chk2.get("default_value", "?"))

# ══ 컴파일 ══════════════════════════════════════
r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r, ensure_ascii=False)[:300])
