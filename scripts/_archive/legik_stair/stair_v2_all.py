"""Stair Detection v2 — Velocity.Z 기반 (safer version).

- 새 이벤트 추가 없음 (이전 무한 루프 원인 회피)
- GetOwningActor/GetActorLocation 호출 없음 (thread-safe 위반 회피)
- UpdateVariables에서 이미 업데이트되는 `Velocity` 변수의 Z 성분 활용
- BlueprintThreadSafeUpdateAnimation 파이프라인에 UpdateStairAlpha 호출 추가
"""
import json
import subprocess
import sys

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
FN = "UpdateStairAlpha"
TSU = "BlueprintThreadSafeUpdateAnimation"


def call(action, args):
    payload = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
               "params": {"name": "blueprint_query",
                          "arguments": {"action": action, **args}}}
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", MCP,
         "-H", "Content-Type: application/json", "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=60)
    d = json.loads(r.stdout)
    txt = d.get("result", {}).get("content", [{}])[0].get("text", "")
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"_raw": txt}


def pp(label, res):
    ok = res.get("success", False) or ("id" in res) or res.get("removed_node")
    print(f"  [{'OK' if ok else 'FAIL'}] {label}"
          + ("" if ok else f" | {str(res)[:150]}"))


# =========================================================================
# 1. 변수 추가 (4개)
# =========================================================================
print("=== 1. 변수 추가 ===")
VARS = [
    ("StairAlphaRecoveryTimer", "float", "0.0",
     "계단 감지 후 FootPlacementAlpha 복귀까지 남은 시간(초)."),
    ("StairVerticalSpeedThreshold", "float", "300.0",
     "계단 감지 Velocity.Z 임계(cm/s). 이 이상이면 계단 턱으로 판정."),
    ("StairAlphaRecoveryTime", "float", "0.25",
     "FootPlacementAlpha가 1.0으로 복귀하는 시간(초)."),
    ("StairAlphaMin", "float", "0.3",
     "계단 감지 시 FootPlacementAlpha 최저값."),
]
for name, vtype, default, tooltip in VARS:
    r = call("add_variable", {
        "asset_path": BP, "name": name, "type": vtype,
        "default_value": default, "category": "StairDetection",
        "tooltip": tooltip})
    pp(f"var {name}", r)

# =========================================================================
# 2. UpdateStairAlpha 함수 생성 (thread-safe)
# =========================================================================
print("\n=== 2. UpdateStairAlpha 함수 생성 ===")
r = call("add_function", {
    "asset_path": BP, "name": FN, "category": "StairDetection",
    "pure": False, "thread_safe": True,
    "tooltip": "계단 감지 + FootPlacementAlpha 제어. thread-safe. Velocity.Z 기반."})
pp(f"add_function {FN}", r)

r = call("set_function_params", {
    "asset_path": BP, "function_name": FN,
    "inputs": [{"name": "DeltaTime", "type": "float"}],
    "outputs": []})
pp("set_function_params", r)

# =========================================================================
# 3. UpdateStairAlpha 내부 그래프 구축
# =========================================================================
print("\n=== 3. UpdateStairAlpha 내부 노드 ===")

KML = "/Script/Engine.KismetMathLibrary"


def add_vget(name, x, y):
    r = call("add_node", {"asset_path": BP, "graph_name": FN,
                            "node_type": "VariableGet",
                            "variable_name": name,
                            "position": {"x": x, "y": y}})
    pp(f"Get {name}", r)
    return r.get("id")


def add_vset(name, x, y):
    r = call("add_node", {"asset_path": BP, "graph_name": FN,
                            "node_type": "VariableSet",
                            "variable_name": name,
                            "position": {"x": x, "y": y}})
    pp(f"Set {name}", r)
    return r.get("id")


def add_call_math(fn_name, x, y, alias=""):
    r = call("add_node", {"asset_path": BP, "graph_name": FN,
                            "node_type": "CallFunction",
                            "function_name": fn_name, "function_class": KML,
                            "position": {"x": x, "y": y}})
    pp(alias or fn_name, r)
    return r.get("id")


# Entry 확인
g = call("get_graph_data", {"asset_path": BP, "graph_name": FN})
entry_id = None
for n in g.get("nodes", []):
    if n.get("class") == "K2Node_FunctionEntry":
        entry_id = n.get("id")
        break
if not entry_id:
    print("[ERR] Entry not found"); sys.exit(1)

# 노드 생성
get_velocity = add_vget("Velocity", -800, 0)
break_vel = add_call_math("BreakVector", -600, 0, "BreakVector")
abs_z     = add_call_math("Abs",         -450, 0, "Abs")
get_thresh = add_vget("StairVerticalSpeedThreshold", -450, 150)
greater   = add_call_math("Greater_DoubleDouble", -300, 50, "Greater")
branch    = call("add_node", {"asset_path": BP, "graph_name": FN,
                                "node_type": "Branch",
                                "position": {"x": -150, "y": 50}})
pp("Branch", branch); branch_id = branch.get("id")

# True branch
get_rec_time_1 = add_vget("StairAlphaRecoveryTime", 0, -100)
set_timer_t = add_vset("StairAlphaRecoveryTimer", 200, 0)

# False branch
get_timer_fb = add_vget("StairAlphaRecoveryTimer", -100, 350)
sub_timer = add_call_math("Subtract_DoubleDouble", 50, 350, "Sub")
max_timer = add_call_math("FMax", 200, 350, "FMax")
set_timer_f = add_vset("StairAlphaRecoveryTimer", 400, 350)

# 합류
get_timer2 = add_vget("StairAlphaRecoveryTimer", 550, 100)
get_rec_time_2 = add_vget("StairAlphaRecoveryTime", 550, 200)
div_ratio = add_call_math("Divide_DoubleDouble", 700, 150, "Div Ratio")
get_min = add_vget("StairAlphaMin", 850, 100)
lerp_alpha = add_call_math("Lerp", 1000, 100, "Lerp")
get_fp_alpha = add_vget("FootPlacementAlpha", 1150, 100)
finterp = add_call_math("FInterpTo", 1300, 150, "FInterpTo")
set_fp = add_vset("FootPlacementAlpha", 1500, 150)

# =========================================================================
# 4. 연결
# =========================================================================
print("\n=== 4. 연결 ===")


def conn(graph, sn, sp, tn, tp):
    r = call("connect_pins", {
        "asset_path": BP, "graph_name": graph,
        "source_node": sn, "source_pin": sp,
        "target_node": tn, "target_pin": tp})
    ok = r.get("success", False)
    print(f"  [{'OK' if ok else 'FAIL'}] {sn}.{sp} -> {tn}.{tp}"
          + ("" if ok else f" | {str(r)[:120]}"))


def setd(graph, nid, pin, value):
    r = call("set_pin_default", {
        "asset_path": BP, "graph_name": graph,
        "node_id": nid, "pin_name": pin, "value": value})
    ok = r.get("success", False)
    print(f"  [{'OK' if ok else 'FAIL'}] set {nid}.{pin}={value}"
          + ("" if ok else f" | {str(r)[:120]}"))


# 데이터: Velocity → Break.InVec, Break.Z → Abs, Abs → Greater.A, Threshold → Greater.B
conn(FN, get_velocity, "Velocity", break_vel, "InVec")
conn(FN, break_vel, "Z", abs_z, "A")
conn(FN, abs_z, "ReturnValue", greater, "A")
conn(FN, get_thresh, "StairVerticalSpeedThreshold", greater, "B")
conn(FN, greater, "ReturnValue", branch_id, "Condition")

# True
conn(FN, get_rec_time_1, "StairAlphaRecoveryTime", set_timer_t, "StairAlphaRecoveryTimer")

# False
conn(FN, get_timer_fb, "StairAlphaRecoveryTimer", sub_timer, "A")
conn(FN, entry_id, "DeltaTime", sub_timer, "B")
conn(FN, sub_timer, "ReturnValue", max_timer, "A")
conn(FN, max_timer, "ReturnValue", set_timer_f, "StairAlphaRecoveryTimer")

# Ratio
conn(FN, get_timer2, "StairAlphaRecoveryTimer", div_ratio, "A")
conn(FN, get_rec_time_2, "StairAlphaRecoveryTime", div_ratio, "B")

# Lerp(1.0, Min, Ratio)
conn(FN, get_min, "StairAlphaMin", lerp_alpha, "B")
conn(FN, div_ratio, "ReturnValue", lerp_alpha, "Alpha")

# FInterpTo
conn(FN, get_fp_alpha, "FootPlacementAlpha", finterp, "Current")
conn(FN, lerp_alpha, "ReturnValue", finterp, "Target")
conn(FN, entry_id, "DeltaTime", finterp, "DeltaTime")

# Set FP Alpha
conn(FN, finterp, "ReturnValue", set_fp, "FootPlacementAlpha")

# exec chain
conn(FN, entry_id, "then", branch_id, "execute")
conn(FN, branch_id, "then", set_timer_t, "execute")
conn(FN, branch_id, "else", set_timer_f, "execute")
conn(FN, set_timer_t, "then", set_fp, "execute")
conn(FN, set_timer_f, "then", set_fp, "execute")

# defaults
setd(FN, max_timer, "B", "0.0")
setd(FN, lerp_alpha, "A", "1.0")
setd(FN, finterp, "InterpSpeed", "15.0")

# =========================================================================
# 5. 컴파일 (UpdateStairAlpha 단독)
# =========================================================================
print("\n=== 5. UpdateStairAlpha 컴파일 확인 ===")
r = call("compile_blueprint", {"asset_path": BP})
success = r.get("success", False)
print(f"  success = {success}, status = {r.get('status')}")
if not success:
    for e in (r.get("errors") or [])[:5]:
        print(f"    [{e.get('node_id')}] {e.get('message','')[:120]}")
    print("\n⚠️  UpdateStairAlpha 함수 자체에 문제. 여기서 중단.")
    print("    Step 6 (TSU 연결)은 실행 안 함.")
    sys.exit(1)

# =========================================================================
# 6. BlueprintThreadSafeUpdateAnimation에 호출 추가
# =========================================================================
print("\n=== 6. TSU에 UpdateStairAlpha 호출 연결 ===")
g = call("get_graph_data", {"asset_path": BP, "graph_name": TSU})
tsu_entry = None
set_dt = None
last_update_fn = None
for n in g.get("nodes", []):
    if n.get("class") == "K2Node_FunctionEntry":
        tsu_entry = n.get("id")
    if n.get("class") == "K2Node_VariableSet" and "Delta Time" in n.get("title", ""):
        set_dt = n.get("id")
    if n.get("class") == "K2Node_CallFunction" and "Update Target Rotation" in n.get("title", ""):
        last_update_fn = n.get("id")
print(f"  entry={tsu_entry}, set_dt={set_dt}, last_update={last_update_fn}")

# UpdateStairAlpha 호출 노드 추가
r = call("add_node", {"asset_path": BP, "graph_name": TSU,
                        "node_type": "CallFunction",
                        "function_name": FN,
                        "position": {"x": 2200, "y": 200}})
pp("add UpdateStairAlpha call", r)
stair_call = r.get("id")

# 기존 연결 끊기: last_update.then → set_dt.execute
call("disconnect_pins", {
    "asset_path": BP, "graph_name": TSU,
    "source_node": last_update_fn, "source_pin": "then",
    "target_node": set_dt, "target_pin": "execute"})

# 새 체인: last_update → UpdateStairAlpha → set_dt
conn(TSU, last_update_fn, "then", stair_call, "execute")
conn(TSU, stair_call, "then", set_dt, "execute")
conn(TSU, tsu_entry, "DeltaTime", stair_call, "DeltaTime")

# =========================================================================
# 7. 컴파일 + 저장
# =========================================================================
print("\n=== 7. 최종 컴파일 ===")
r = call("compile_blueprint", {"asset_path": BP})
print(f"  success = {r.get('success')}, status = {r.get('status')}")
for e in (r.get("errors") or [])[:5]:
    print(f"    [{e.get('node_id')}] {e.get('message','')[:120]}")

if r.get("success"):
    print("\n=== 저장 ===")
    r2 = call("save_asset", {"asset_path": BP})
    print(f"  {r2}")
