# Phase C M1b — 스플라인 참조 스티키 래치 수정 (2026-07-23)
# 문제: Td에지 프레임 = 트랜짓 시작 = 콜리전 억제(collision_off) → 오버랩 length 0 → SplineRef 항상 None
# 수정: SplineRef는 매 프레임 IsValid 게이트 스티키 래치 (유효할 때만 덮어씀),
#       sd/td/StartT만 Td에지 래치 유지. StartT의 스플라인 소스 = 스티키 변수(Get LedgeSplineRef).
# 실행: py phase_c_m1b_sticky.py [apply]
# ⚠ 로컬 python 전용. apply 전 PIE 종료.
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

VS6 = "K2Node_VariableSet_6"        # Set LedgeUnitMoveVec
NEXT = "K2Node_VariableSet_30"      # 원래 후속 (McBase)
SSEL = "K2Node_CallFunction_112"    # GetComponentByClass (선택 스플라인)
XT = "K2Node_CallFunction_114"      # GetTransformAtDistanceAlongSpline
BRT = "K2Node_IfThenElse_0"         # Td에지 Branch
SETSP = "K2Node_VariableSet_9"      # Set LedgeSplineRef
SETSD = "K2Node_VariableSet_10"
SETT = "K2Node_VariableSet_12"


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


def linked(nid, pin):
    for p in nodes[nid].get("pins", []):
        if p["name"] == pin:
            return p.get("connected_to", [])
    return []


# 프리플라이트: 현 배선 확인
assert VS6 + ".then" and linked(VS6, "then") == [BRT + ".execute"], "VS6.then 배선 상이: " + str(linked(VS6, "then"))
assert linked(BRT, "then") == [SETSP + ".execute"], "BRT.then 배선 상이"
assert linked(SETSP, "then") == [SETSD + ".execute"], "SETSP.then 배선 상이"
assert any(c == XT + ".self" for c in linked(SSEL, "ReturnValue")), "ssel->xt.self 배선 상이"
print("[PF] 현 배선 OK")

if not APPLY:
    print("== DRY-RUN OK ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"

X, Y = -4600, 3300


def add(ntype, extra, pos):
    p = {"graph_name": GH, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    print("[ADD]", ntype, extra.get("function_name", extra.get("variable_name", "")), "->", nid)
    return nid


brv = add("Branch", {}, [X, Y])
isv = add("CallFunction", {"function_class": "KismetSystemLibrary", "function_name": "IsValid"}, [X - 250, Y + 100])
vgs = add("VariableGet", {"variable_name": "LedgeSplineRef"}, [X + 900, Y + 200])


def disc(sn, sp, tn, tp):
    bq("disconnect_pins", {"graph_name": GH, "source_node": sn, "source_pin": sp,
                           "target_node": tn, "target_pin": tp})
    print("[DISC]", sn + "." + sp, "x", tn + "." + tp)


def wire(sn, sp, tn, tp):
    bq("connect_pins", {"graph_name": GH, "source_node": sn, "source_pin": sp,
                        "target_node": tn, "target_pin": tp})
    print("[WIRE]", sn + "." + sp, "->", tn + "." + tp)


# exec 재배선
disc(VS6, "then", BRT, "execute")
disc(BRT, "then", SETSP, "execute")
disc(SETSP, "then", SETSD, "execute")
wire(VS6, "then", brv, "execute")
wire(brv, "then", SETSP, "execute")
wire(SETSP, "then", BRT, "execute")
wire(brv, "else", BRT, "execute")
wire(BRT, "then", SETSD, "execute")
# 데이터
wire(SSEL, "ReturnValue", isv, "Object")
wire(isv, "ReturnValue", brv, "Condition")
disc(SSEL, "ReturnValue", XT, "self")
wire(vgs, "LedgeSplineRef", XT, "self")

# 검증
nodes = {n["id"]: n for n in bq("get_graph_data", {"graph_name": GH})["nodes"]}
MUST = [
    (VS6, "then", brv + ".execute"),
    (brv, "then", SETSP + ".execute"),
    (SETSP, "then", BRT + ".execute"),
    (brv, "else", BRT + ".execute"),
    (BRT, "then", SETSD + ".execute"),
    (vgs, "LedgeSplineRef", XT + ".self"),
    (isv, "ReturnValue", brv + ".Condition"),
]
fails = [m for m in MUST if m[2] not in linked(m[0], m[1])]
xt_self = [c for c in linked(SSEL, "ReturnValue") if c == XT + ".self"]
if fails or xt_self:
    print("!! 검증 실패:", fails, "잔존:", xt_self)
    sys.exit(1)
print("[VERIFY] 재배선 전부 확인")

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r, ensure_ascii=False)[:200])
