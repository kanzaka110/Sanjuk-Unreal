"""가드 로직을 우회 — Select → Set 끊고 원래 경로 복원.
가드 노드들은 그대로 두되 Set의 입력만 원래 PromotableOperator_1로 복귀.
"""
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
        capture_output=True, text=True, timeout=30)
    d = json.loads(r.stdout)
    txt = d.get("result", {}).get("content", [{}])[0].get("text", "")
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"_raw": txt}


# 현재 Select_0.ReturnValue → Set_3.TargetRotationDelta 끊기
# 원래 경로 복원: PromotableOperator_1.ReturnValue → Set_3.TargetRotationDelta

print("=== Select → Set 연결 해제 시도 ===")
# disconnect_pins 대신 다른 연결 생성으로 자동 overwrite 시도
r = call("connect_pins", {
    "asset_path": BP, "graph_name": GRAPH,
    "source_node": "K2Node_PromotableOperator_1", "source_pin": "ReturnValue",
    "target_node": "K2Node_VariableSet_3", "target_pin": "TargetRotationDelta"})
print(f"  PromoteOp -> Set: {r.get('success', False)}")

# 확인: Set_3의 TargetRotationDelta 핀이 PromoteOp에 연결됐나
print("\n=== 검증 ===")
r = call("get_graph_data", {"asset_path": BP, "graph_name": GRAPH})
for n in r.get("nodes", []):
    if n.get("id") == "K2Node_VariableSet_3":
        for p in n.get("pins", []):
            if p.get("name") == "TargetRotationDelta":
                conn = p.get("connected_to", [])
                print(f"  Set_3.TargetRotationDelta connected_to: {conn}")

# 컴파일
print("\n=== 컴파일 ===")
r = call("compile_blueprint", {"asset_path": BP})
print(f"  success={r.get('success')}, status={r.get('status')}")
for e in (r.get("errors") or [])[:5]:
    print(f"    [{e.get('node_id')}] {e.get('message','')[:150]}")

# 저장
print("\n=== 저장 ===")
r = call("save_asset", {"asset_path": BP})
print(f"  {r}")
