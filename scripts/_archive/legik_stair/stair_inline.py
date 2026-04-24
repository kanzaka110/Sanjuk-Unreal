"""Inline 버전 — UpdateVariables 내부에 계단 감지 로직 직접 삽입.

선행 정리:
1. TSU에서 UpdateStairAlpha 호출 노드 제거 + 원래 exec 체인 복구
2. UpdateStairAlpha 함수 삭제

본 작업:
3. UpdateVariables의 exec 체인 끝 찾기
4. 끝 노드에 stair detection 체인 append
5. 컴파일 + 저장
"""
import json
import subprocess
import sys

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
UPDATE_VARS = "UpdateVariables"
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
          + ("" if ok else f" | {str(res)[:120]}"))


# =========================================================================
# 1. TSU 원복
# =========================================================================
print("=== 1. TSU 원복 ===")
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

if last_update and set_dt_id:
    r = call("connect_pins", {
        "asset_path": BP, "graph_name": TSU,
        "source_node": last_update, "source_pin": "then",
        "target_node": set_dt_id, "target_pin": "execute"})
    pp("restore UpdateTargetRotation -> SetDeltaTime", r)

# =========================================================================
# 2. UpdateStairAlpha 함수 삭제
# =========================================================================
print("\n=== 2. UpdateStairAlpha 함수 삭제 ===")
r = call("remove_function", {"asset_path": BP, "name": "UpdateStairAlpha"})
pp("remove UpdateStairAlpha", r)

# =========================================================================
# 3. UpdateVariables exec 체인 끝 찾기
# =========================================================================
print("\n=== 3. UpdateVariables 분석 ===")
g = call("get_graph_data", {"asset_path": BP, "graph_name": UPDATE_VARS})
nodes = g.get("nodes", [])
print(f"  total nodes = {len(nodes)}")

# exec 체인 끝 찾기: then 핀에 연결이 없는 노드 중 Entry 아닌 것
# 더 쉬운 방법: FunctionResult 또는 Return 노드 찾기
entry_id = None
result_nodes = []
for n in nodes:
    cls = n.get("class", "")
    if cls == "K2Node_FunctionEntry":
        entry_id = n.get("id")
    if cls == "K2Node_FunctionResult":
        result_nodes.append(n.get("id"))

print(f"  entry = {entry_id}")
print(f"  result nodes = {len(result_nodes)}")

# exec 흐름상 Result 노드 직전의 노드가 "현재 마지막 exec" 노드
# Result가 여러 개면 첫 번째만 쓰거나, 가장 단순한 접근: Result 노드 앞에 삽입
if not result_nodes:
    print("  [ERR] FunctionResult 노드 없음. UpdateVariables에 직접 append 불가 — 중단")
    sys.exit(1)

tail_result = result_nodes[0]
print(f"  삽입 대상 Result = {tail_result}")

# Result 직전 노드 찾기 (execute 핀에 뭐가 연결되어 있는지)
# get_graph_data가 connections 안 주면 직접 쿼리
r = call("get_node_details", {"asset_path": BP, "graph_name": UPDATE_VARS, "node_id": tail_result})
# 이 노드의 execute 핀의 linked_to 확인
pre_result = None
for p in r.get("pins", []):
    if p.get("name") == "execute" or "exec" in p.get("name", "").lower():
        linked = p.get("connected_to") or p.get("linked_to") or []
        for lp in linked:
            # lp가 dict면 node id 추출
            if isinstance(lp, dict):
                pre_result = lp.get("node_id") or lp.get("owning_node")
            else:
                pre_result = lp
            break
        break

print(f"  Result 앞 노드 = {pre_result}")

# =========================================================================
# 4. UpdateVariables 내부에 stair detection 체인 추가
# =========================================================================
print("\n=== 4. Stair detection 체인 추가 ===")

KML = "/Script/Engine.KismetMathLibrary"


def add_vget(name, x, y):
    r = call("add_node", {"asset_path": BP, "graph_name": UPDATE_VARS,
                           "node_type": "VariableGet",
                           "variable_name": name,
                           "position": {"x": x, "y": y}})
    return r.get("id")


def add_vset(name, x, y):
    r = call("add_node", {"asset_path": BP, "graph_name": UPDATE_VARS,
                           "node_type": "VariableSet",
                           "variable_name": name,
                           "position": {"x": x, "y": y}})
    return r.get("id")


def add_call(fn, x, y):
    r = call("add_node", {"asset_path": BP, "graph_name": UPDATE_VARS,
                           "node_type": "CallFunction",
                           "function_name": fn, "function_class": KML,
                           "position": {"x": x, "y": y}})
    return r.get("id")


# DeltaTime: UpdateVariables에 DeltaTime 인풋 없음. 함수 내부 다른 변수 활용 필요.
# 'Delta Time' 변수가 PC_01_ABP에 있나 확인 (UpdateAnimation에서 Set하는 듯)
# 또는 World delta seconds — GetWorldDeltaSeconds
delta_seconds_node = add_call("GetWorldDeltaSeconds", 2500, 0)
print(f"  DeltaSeconds node = {delta_seconds_node}")

# Velocity 읽기
get_velocity = add_vget("Velocity", 2500, 100)
break_vel = call("add_node", {"asset_path": BP, "graph_name": UPDATE_VARS,
                                "node_type": "CallFunction",
                                "function_name": "BreakVector", "function_class": KML,
                                "position": {"x": 2650, "y": 100}}).get("id")
abs_z = add_call("Abs", 2800, 100)
get_thresh = add_vget("StairVerticalSpeedThreshold", 2800, 250)
greater = add_call("Greater_DoubleDouble", 2950, 150)
branch = call("add_node", {"asset_path": BP, "graph_name": UPDATE_VARS,
                             "node_type": "Branch",
                             "position": {"x": 3100, "y": 150}}).get("id")

# True branch
get_rec_t1 = add_vget("StairAlphaRecoveryTime", 3250, 0)
set_timer_t = add_vset("StairAlphaRecoveryTimer", 3400, 50)

# False branch
get_timer_fb = add_vget("StairAlphaRecoveryTimer", 3250, 300)
sub_timer = add_call("Subtract_DoubleDouble", 3400, 300)
max_timer = add_call("FMax", 3550, 300)
set_timer_f = add_vset("StairAlphaRecoveryTimer", 3700, 300)

# 합류
get_timer2 = add_vget("StairAlphaRecoveryTimer", 3850, 100)
get_rec_t2 = add_vget("StairAlphaRecoveryTime", 3850, 200)
div_ratio = add_call("Divide_DoubleDouble", 4000, 150)
get_min = add_vget("StairAlphaMin", 4150, 100)
lerp_a = add_call("Lerp", 4300, 100)
get_fp = add_vget("FootPlacementAlpha", 4450, 100)
finterp = add_call("FInterpTo", 4600, 150)
set_fp = add_vset("FootPlacementAlpha", 4800, 150)

# =========================================================================
# 5. 연결
# =========================================================================
print("\n=== 5. 연결 ===")


def conn(sn, sp, tn, tp):
    r = call("connect_pins", {
        "asset_path": BP, "graph_name": UPDATE_VARS,
        "source_node": sn, "source_pin": sp,
        "target_node": tn, "target_pin": tp})
    ok = r.get("success", False)
    print(f"  [{'OK' if ok else 'FAIL'}] {sn}.{sp} -> {tn}.{tp}"
          + ("" if ok else f" | {str(r)[:120]}"))


def setd(nid, pin, value):
    r = call("set_pin_default", {
        "asset_path": BP, "graph_name": UPDATE_VARS,
        "node_id": nid, "pin_name": pin, "value": value})
    ok = r.get("success", False)
    print(f"  [{'OK' if ok else 'FAIL'}] {nid}.{pin}={value}")


# 데이터
conn(get_velocity, "Velocity", break_vel, "InVec")
conn(break_vel, "Z", abs_z, "A")
conn(abs_z, "ReturnValue", greater, "A")
conn(get_thresh, "StairVerticalSpeedThreshold", greater, "B")
conn(greater, "ReturnValue", branch, "Condition")

conn(get_rec_t1, "StairAlphaRecoveryTime", set_timer_t, "StairAlphaRecoveryTimer")

conn(get_timer_fb, "StairAlphaRecoveryTimer", sub_timer, "A")
conn(delta_seconds_node, "ReturnValue", sub_timer, "B")
conn(sub_timer, "ReturnValue", max_timer, "A")
conn(max_timer, "ReturnValue", set_timer_f, "StairAlphaRecoveryTimer")

conn(get_timer2, "StairAlphaRecoveryTimer", div_ratio, "A")
conn(get_rec_t2, "StairAlphaRecoveryTime", div_ratio, "B")
conn(get_min, "StairAlphaMin", lerp_a, "B")
conn(div_ratio, "ReturnValue", lerp_a, "Alpha")
conn(get_fp, "FootPlacementAlpha", finterp, "Current")
conn(lerp_a, "ReturnValue", finterp, "Target")
conn(delta_seconds_node, "ReturnValue", finterp, "DeltaTime")
conn(finterp, "ReturnValue", set_fp, "FootPlacementAlpha")

# defaults
setd(max_timer, "B", "0.0")
setd(lerp_a, "A", "1.0")
setd(finterp, "InterpSpeed", "15.0")

# exec 체인: pre_result → branch → (True/False) → set_fp → tail_result
# pre_result 앞단에서 Result로 가는 연결 끊기
if pre_result:
    call("disconnect_pins", {
        "asset_path": BP, "graph_name": UPDATE_VARS,
        "source_node": pre_result, "source_pin": "then",
        "target_node": tail_result, "target_pin": "execute"})
    conn(pre_result, "then", branch, "execute")
else:
    # pre_result 없으면 entry에 직접 (비정상)
    conn(entry_id, "then", branch, "execute")

conn(branch, "then", set_timer_t, "execute")
conn(branch, "else", set_timer_f, "execute")
conn(set_timer_t, "then", set_fp, "execute")
conn(set_timer_f, "then", set_fp, "execute")
conn(set_fp, "then", tail_result, "execute")

# =========================================================================
# 6. 컴파일 + 저장
# =========================================================================
print("\n=== 6. 컴파일 ===")
r = call("compile_blueprint", {"asset_path": BP})
print(f"  success = {r.get('success')}, status = {r.get('status')}")
for e in (r.get("errors") or [])[:5]:
    print(f"    [{e.get('node_id')}] {e.get('message','')[:120]}")

if r.get("success"):
    print("\n=== 저장 ===")
    r2 = call("save_asset", {"asset_path": BP})
    print(f"  {r2}")
