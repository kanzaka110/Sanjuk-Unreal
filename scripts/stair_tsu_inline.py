"""Stair detection을 TSU(BlueprintThreadSafeUpdateAnimation) 내부에 직접 인라인.

기반:
- Velocity 변수가 이미 thread-safe 업데이트됨 (UpdateVariables에서 Set)
- DeltaTime은 TSU entry 핀에서 바로 얻음
- 새 이벤트/새 함수 불필요 → thread-safe 이슈, 무한 루프 리스크 모두 회피
"""
import json
import subprocess
import sys

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
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
    ok = res.get("success", False) or ("id" in res) or res.get("removed_node") or res.get("removed_graph")
    print(f"  [{'OK' if ok else 'FAIL'}] {label}"
          + ("" if ok else f" | {str(res)[:150]}"))


KML = "/Script/Engine.KismetMathLibrary"

# =========================================================================
# 1. 기존 UpdateStairAlpha 호출 + 함수 정리
# =========================================================================
print("=== 1. TSU에서 UpdateStairAlpha 호출 제거 + 원래 체인 복구 ===")
g = call("get_graph_data", {"asset_path": BP, "graph_name": TSU})
stair_call_id = None
set_dt_id = None
last_update = None
for n in g.get("nodes", []):
    title = n.get("title", "")
    cls = n.get("class", "")
    if cls == "K2Node_CallFunction" and "Update Stair Alpha" in title:
        stair_call_id = n.get("id")
    if cls == "K2Node_VariableSet" and "Delta Time" in title:
        set_dt_id = n.get("id")
    if cls == "K2Node_CallFunction" and "Update Target Rotation" in title:
        last_update = n.get("id")

print(f"  stair_call={stair_call_id}, set_dt={set_dt_id}, last_update={last_update}")

if stair_call_id:
    r = call("remove_node", {"asset_path": BP, "graph_name": TSU, "node_id": stair_call_id})
    pp("remove stair call", r)

# UpdateStairAlpha 함수 제거
print("\n=== UpdateStairAlpha 함수 제거 ===")
r = call("remove_function", {"asset_path": BP, "name": "UpdateStairAlpha"})
pp("remove function", r)

# =========================================================================
# 2. TSU에 인라인 노드 추가
# =========================================================================
print("\n=== 2. TSU 인라인 노드 생성 ===")


def add_vget(name, x, y):
    r = call("add_node", {"asset_path": BP, "graph_name": TSU,
                           "node_type": "VariableGet",
                           "variable_name": name,
                           "position": {"x": x, "y": y}})
    pp(f"Get {name}", r)
    return r.get("id")


def add_vset(name, x, y):
    r = call("add_node", {"asset_path": BP, "graph_name": TSU,
                           "node_type": "VariableSet",
                           "variable_name": name,
                           "position": {"x": x, "y": y}})
    pp(f"Set {name}", r)
    return r.get("id")


def add_math(fn, x, y, alias=""):
    r = call("add_node", {"asset_path": BP, "graph_name": TSU,
                           "node_type": "CallFunction",
                           "function_name": fn, "function_class": KML,
                           "position": {"x": x, "y": y}})
    pp(alias or fn, r)
    return r.get("id")


# 좌표는 기존 TSU 노드들 오른쪽에 배치
X0 = 2200

# 속도 계산
get_velocity = add_vget("Velocity", X0, 0)
break_vel = add_math("BreakVector", X0 + 200, 0, "BreakVector")
abs_z = add_math("Abs", X0 + 400, 0, "Abs")
get_thresh = add_vget("StairVerticalSpeedThreshold", X0 + 400, 150)
greater = add_math("Greater_DoubleDouble", X0 + 600, 75, "Greater")
branch = call("add_node", {"asset_path": BP, "graph_name": TSU,
                             "node_type": "Branch",
                             "position": {"x": X0 + 800, "y": 75}})
pp("Branch", branch); branch_id = branch.get("id")

# True
get_rec_t1 = add_vget("StairAlphaRecoveryTime", X0 + 900, -100)
set_timer_t = add_vset("StairAlphaRecoveryTimer", X0 + 1050, 0)

# False
get_timer_fb = add_vget("StairAlphaRecoveryTimer", X0 + 900, 300)
sub_timer = add_math("Subtract_DoubleDouble", X0 + 1050, 300, "Sub")
max_timer = add_math("FMax", X0 + 1200, 300, "FMax")
set_timer_f = add_vset("StairAlphaRecoveryTimer", X0 + 1350, 300)

# 합류 — Ratio, Lerp, FInterpTo, Set FootPlacementAlpha
get_timer2 = add_vget("StairAlphaRecoveryTimer", X0 + 1500, 100)
get_rec_t2 = add_vget("StairAlphaRecoveryTime", X0 + 1500, 200)
div_ratio = add_math("Divide_DoubleDouble", X0 + 1650, 150, "DivRatio")
get_min = add_vget("StairAlphaMin", X0 + 1800, 50)
lerp_a = add_math("Lerp", X0 + 1950, 100, "Lerp")
get_fp = add_vget("FootPlacementAlpha", X0 + 2100, 50)
finterp = add_math("FInterpTo", X0 + 2250, 150, "FInterpTo")
set_fp = add_vset("FootPlacementAlpha", X0 + 2450, 150)

# =========================================================================
# 3. 연결
# =========================================================================
print("\n=== 3. 연결 ===")


def conn(sn, sp, tn, tp):
    r = call("connect_pins", {
        "asset_path": BP, "graph_name": TSU,
        "source_node": sn, "source_pin": sp,
        "target_node": tn, "target_pin": tp})
    ok = r.get("success", False)
    print(f"  [{'OK' if ok else 'FAIL'}] {sn}.{sp} -> {tn}.{tp}"
          + ("" if ok else f" | {str(r)[:120]}"))


def setd(nid, pin, value):
    r = call("set_pin_default", {
        "asset_path": BP, "graph_name": TSU,
        "node_id": nid, "pin_name": pin, "value": value})
    ok = r.get("success", False)
    print(f"  [{'OK' if ok else 'FAIL'}] {nid}.{pin}={value}")


# Entry 찾기
g = call("get_graph_data", {"asset_path": BP, "graph_name": TSU})
entry_id = None
for n in g.get("nodes", []):
    if n.get("class") == "K2Node_FunctionEntry":
        entry_id = n.get("id")
        break

# 데이터
conn(get_velocity, "Velocity", break_vel, "InVec")
conn(break_vel, "Z", abs_z, "A")
conn(abs_z, "ReturnValue", greater, "A")
conn(get_thresh, "StairVerticalSpeedThreshold", greater, "B")
conn(greater, "ReturnValue", branch_id, "Condition")
conn(get_rec_t1, "StairAlphaRecoveryTime", set_timer_t, "StairAlphaRecoveryTimer")
conn(get_timer_fb, "StairAlphaRecoveryTimer", sub_timer, "A")
conn(entry_id, "DeltaTime", sub_timer, "B")
conn(sub_timer, "ReturnValue", max_timer, "A")
conn(max_timer, "ReturnValue", set_timer_f, "StairAlphaRecoveryTimer")
conn(get_timer2, "StairAlphaRecoveryTimer", div_ratio, "A")
conn(get_rec_t2, "StairAlphaRecoveryTime", div_ratio, "B")
conn(get_min, "StairAlphaMin", lerp_a, "B")
conn(div_ratio, "ReturnValue", lerp_a, "Alpha")
conn(get_fp, "FootPlacementAlpha", finterp, "Current")
conn(lerp_a, "ReturnValue", finterp, "Target")
conn(entry_id, "DeltaTime", finterp, "DeltaTime")
conn(finterp, "ReturnValue", set_fp, "FootPlacementAlpha")

# defaults
setd(max_timer, "B", "0.0")
setd(lerp_a, "A", "1.0")
setd(finterp, "InterpSpeed", "15.0")

# exec 체인 재구성: UpdateTargetRotation → Branch → (T/F) → Set FP Alpha → Set Delta Time
# 기존 연결 (UpdateTargetRotation → SetDeltaTime) 끊기
call("disconnect_pins", {
    "asset_path": BP, "graph_name": TSU,
    "source_node": last_update, "source_pin": "then",
    "target_node": set_dt_id, "target_pin": "execute"})
# 복구 시도 중 이미 연결됐을 수 있음 — 강제 제거 후 새 체인
conn(last_update, "then", branch_id, "execute")
conn(branch_id, "then", set_timer_t, "execute")
conn(branch_id, "else", set_timer_f, "execute")
conn(set_timer_t, "then", set_fp, "execute")
conn(set_timer_f, "then", set_fp, "execute")
conn(set_fp, "then", set_dt_id, "execute")

# =========================================================================
# 4. 컴파일 + 저장
# =========================================================================
print("\n=== 4. 컴파일 ===")
r = call("compile_blueprint", {"asset_path": BP})
print(f"  success = {r.get('success')}, status = {r.get('status')}")
for e in (r.get("errors") or [])[:5]:
    print(f"    [{e.get('node_id')}] {e.get('message','')[:150]}")

if r.get("success"):
    print("\n=== 저장 ===")
    r2 = call("save_asset", {"asset_path": BP})
    print(f"  {r2}")
else:
    print("\n⚠️ 컴파일 실패. 저장 안 함.")
