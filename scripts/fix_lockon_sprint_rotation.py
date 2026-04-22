"""UpdateTargetRotation의 'Player Input이 없음' 경로에 180° flip 가드 삽입.

기존: PromotableOperator_1.ReturnValue → Set TargetRotationDelta_3.TargetRotationDelta
변경 후: PromotableOperator_1.ReturnValue → [가드 로직] → Set TargetRotationDelta_3

가드 로직 (단순 Select 버전):
  abs(current) > 170 AND abs(prev) > 0.1
    → Set = sign(prev) * abs(current)  (flip 방지, 이전 부호 유지)
    → Set = current                    (원래 값)

exec 흐름 변경 없음. 노드 8개만 추가 + 연결 1개 끊고 4개 연결.
"""
import json
import subprocess
import sys

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "UpdateTargetRotation"

# 기존 노드 ID (현재 그래프 분석으로 확정)
EXISTING_PROMOTE = "K2Node_PromotableOperator_1"       # float * float, 기존 delta 계산 결과
EXISTING_SET = "K2Node_VariableSet_3"                   # Set TargetRotationDelta

KML = "/Script/Engine.KismetMathLibrary"


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


# 롤백용 노드 ID 추적
added_nodes = []


def add_call_math(fn_name, x, y, alias=""):
    r = call("add_node", {"asset_path": BP, "graph_name": GRAPH,
                           "node_type": "CallFunction",
                           "function_name": fn_name, "function_class": KML,
                           "position": {"x": x, "y": y}})
    nid = r.get("id")
    if nid:
        added_nodes.append(nid)
    pp(alias or fn_name, r)
    return nid


def add_variable_get(name, x, y):
    r = call("add_node", {"asset_path": BP, "graph_name": GRAPH,
                           "node_type": "VariableGet",
                           "variable_name": name,
                           "position": {"x": x, "y": y}})
    nid = r.get("id")
    if nid:
        added_nodes.append(nid)
    pp(f"Get {name}", r)
    return nid


def add_select_float(x, y):
    """Select (float) — Index=bool, Option0=False, Option1=True."""
    # K2Node_Select with float type
    r = call("add_node", {"asset_path": BP, "graph_name": GRAPH,
                           "node_type": "Select",
                           "value_type": "float",
                           "position": {"x": x, "y": y}})
    nid = r.get("id")
    if nid:
        added_nodes.append(nid)
    pp("Select(float)", r)
    return nid


# =========================================================================
# 1. 노드 8개 추가
# =========================================================================
print("=== 1. 가드 노드 생성 ===")
X0 = 1500

abs_curr = add_call_math("Abs", X0, 100, "Abs(current)")
greater_170 = add_call_math("Greater_DoubleDouble", X0 + 200, 100, "Greater >170")
get_prev = add_variable_get("TargetRotationDelta", X0, 300)
abs_prev = add_call_math("Abs", X0 + 200, 300, "Abs(prev)")
greater_01 = add_call_math("Greater_DoubleDouble", X0 + 400, 300, "Greater >0.1")
and_both = call("add_node", {"asset_path": BP, "graph_name": GRAPH,
                              "node_type": "CallFunction",
                              "function_name": "BooleanAND",
                              "function_class": "/Script/Engine.KismetMathLibrary",
                              "position": {"x": X0 + 600, "y": 200}})
pp("AND", and_both)
if and_both.get("id"):
    added_nodes.append(and_both["id"])
and_id = and_both.get("id")

sign_prev = add_call_math("SignOfFloat", X0 + 400, 400, "Sign(prev)")
# SignOfFloat이 없다면 fallback 필요 — 나중에 확인
mult = add_call_math("Multiply_DoubleDouble", X0 + 600, 400, "Multiply")
select = add_select_float(X0 + 800, 250)

# =========================================================================
# 2. 기존 연결 끊기
# =========================================================================
print("\n=== 2. 기존 연결 끊기 ===")
r = call("disconnect_pins", {
    "asset_path": BP, "graph_name": GRAPH,
    "source_node": EXISTING_PROMOTE, "source_pin": "ReturnValue",
    "target_node": EXISTING_SET, "target_pin": "TargetRotationDelta"})
pp("disconnect PromoteOp -> Set", r)


# =========================================================================
# 3. 새 연결
# =========================================================================
print("\n=== 3. 새 연결 ===")


def conn(sn, sp, tn, tp):
    r = call("connect_pins", {
        "asset_path": BP, "graph_name": GRAPH,
        "source_node": sn, "source_pin": sp,
        "target_node": tn, "target_pin": tp})
    ok = r.get("success", False)
    print(f"  [{'OK' if ok else 'FAIL'}] {sn}.{sp} -> {tn}.{tp}"
          + ("" if ok else f" | {str(r)[:120]}"))
    return ok


def setd(nid, pin, value):
    r = call("set_pin_default", {
        "asset_path": BP, "graph_name": GRAPH,
        "node_id": nid, "pin_name": pin, "value": value})
    ok = r.get("success", False)
    print(f"  [{'OK' if ok else 'FAIL'}] set {nid}.{pin}={value}")


# abs(current): PromotableOperator_1.ReturnValue → Abs_curr.A
conn(EXISTING_PROMOTE, "ReturnValue", abs_curr, "A")
# abs_curr.Out → Greater_170.A
conn(abs_curr, "ReturnValue", greater_170, "A")
setd(greater_170, "B", "170.0")

# prev: Get TargetRotationDelta → Abs_prev.A & Sign_prev.A
conn(get_prev, "TargetRotationDelta", abs_prev, "A")
conn(get_prev, "TargetRotationDelta", sign_prev, "A")

# abs_prev.Out → Greater_01.A
conn(abs_prev, "ReturnValue", greater_01, "A")
setd(greater_01, "B", "0.1")

# AND: Greater_170 & Greater_01 → AND
conn(greater_170, "ReturnValue", and_id, "A")
conn(greater_01, "ReturnValue", and_id, "B")

# sign * abs_current
conn(sign_prev, "ReturnValue", mult, "A")
conn(abs_curr, "ReturnValue", mult, "B")

# Select 연결
# Select.Index = AND
# Select.Option0 (false) = PromoteOp.ReturnValue (원래 값)
# Select.Option1 (true) = mult.ReturnValue (가드된 값)
conn(and_id, "ReturnValue", select, "Index")
conn(EXISTING_PROMOTE, "ReturnValue", select, "Option 0")
conn(mult, "ReturnValue", select, "Option 1")

# Select 결과 → Set TargetRotationDelta
conn(select, "ReturnValue", EXISTING_SET, "TargetRotationDelta")

# =========================================================================
# 4. 컴파일
# =========================================================================
print("\n=== 4. 컴파일 ===")
r = call("compile_blueprint", {"asset_path": BP})
success = r.get("success", False)
print(f"  success = {success}, status = {r.get('status')}")
for e in (r.get("errors") or [])[:10]:
    print(f"    [{e.get('node_id')}] {e.get('message','')[:200]}")

if not success:
    print("\n⚠️  컴파일 실패. 자동 롤백 시작...")
    # 기존 연결 복구
    conn(EXISTING_PROMOTE, "ReturnValue", EXISTING_SET, "TargetRotationDelta")
    # 추가한 노드 전부 제거
    for nid in reversed(added_nodes):
        r = call("remove_node", {"asset_path": BP, "graph_name": GRAPH, "node_id": nid})
        pp(f"rollback remove {nid}", r)
    print("\n롤백 완료. 에셋은 저장 안 함 (in-memory만).")
    sys.exit(1)

# =========================================================================
# 5. 저장
# =========================================================================
print("\n=== 5. 저장 ===")
r = call("save_asset", {"asset_path": BP})
print(f"  {r}")

print("\n✅ 완료. PIE 재시작 후 락온 스프린트 정지 테스트.")
