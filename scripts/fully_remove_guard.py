"""가드 로직 완전 제거 — 원래 경로 복원 + 가드 노드/주석 삭제."""
import json
import subprocess

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "UpdateTargetRotation"


def call(action, args):
    payload = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
               "params": {"name": "blueprint_query",
                          "arguments": {"action": action, **args}}}
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", MCP,
         "-H", "Content-Type: application/json", "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=120)
    d = json.loads(r.stdout)
    txt = d.get("result", {}).get("content", [{}])[0].get("text", "")
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"_raw": txt}


# 1. 원래 연결 복원: PromoteOp → Set
print("=== 1. 원래 연결 복원 ===")
r = call("connect_pins", {
    "asset_path": BP, "graph_name": GRAPH,
    "source_node": "K2Node_PromotableOperator_1", "source_pin": "ReturnValue",
    "target_node": "K2Node_VariableSet_3", "target_pin": "TargetRotationDelta"})
print(f"  PromoteOp -> Set: {r}")

# 2. 가드 노드 + Select + 가드 주석 제거
print("\n=== 2. 가드 노드 제거 ===")
GUARD_NODES = [
    "K2Node_CallFunction_13",  # Abs(current)
    "K2Node_CallFunction_14",  # Greater >170
    "K2Node_VariableGet_3",    # Get TargetRotationDelta
    "K2Node_CallFunction_15",  # Abs(prev)
    "K2Node_CallFunction_16",  # Greater >0.1
    "K2Node_CallFunction_17",  # AND
    "K2Node_CallFunction_19",  # Sign
    "K2Node_CallFunction_20",  # Multiply
    "K2Node_Select_0",         # Select
    "EdGraphNode_Comment_13",  # 메인 주석
]
for nid in GUARD_NODES:
    r = call("remove_node", {"asset_path": BP, "graph_name": GRAPH, "node_id": nid})
    ok = r.get("removed_node") or r.get("success")
    print(f"  [{'OK' if ok else 'SKIP'}] remove {nid}")

# 3. 컴파일
print("\n=== 3. 컴파일 ===")
r = call("compile_blueprint", {"asset_path": BP})
print(f"  success={r.get('success')}, status={r.get('status')}")
for e in (r.get("errors") or [])[:5]:
    print(f"    [{e.get('node_id')}] {e.get('message','')[:150]}")

# 4. 저장 (타임아웃 늘림)
print("\n=== 4. 저장 ===")
r = call("save_asset", {"asset_path": BP})
print(f"  {r}")
