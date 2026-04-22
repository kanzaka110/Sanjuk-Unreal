"""뭉쳐있는 가드 코멘트 4개를 제자리로 이동 + 크기 조정."""
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


# 4개 코멘트 노드와 목표 위치/크기
# 가드 로직 범위: x=1500~2350, y=100~450
# 실제 노드 좌표 (앞에서 만든 것):
#   abs_curr        (1500, 100)
#   greater_170     (1700, 100)
#   get_prev        (1500, 300)
#   abs_prev        (1700, 300)
#   greater_01      (1900, 300)
#   AND             (2100, 200)
#   sign_prev       (1900, 400)
#   mult            (2100, 400)
#   select          (2300, 250)

MOVES = [
    # (node_id, new_pos, new_size?)
    ("EdGraphNode_Comment_2", {"x": 1480, "y": 20},   {"width": 900, "height": 500}),  # 메인
    ("EdGraphNode_Comment_5", {"x": 1480, "y": 60},   {"width": 520, "height": 320}),  # 조건 체크
    ("EdGraphNode_Comment_6", {"x": 1880, "y": 360},  {"width": 280, "height": 140}),  # Guard 값
    ("EdGraphNode_Comment_7", {"x": 2260, "y": 200},  {"width": 180, "height": 160}),  # 최종 선택
]

print("=== Comment 노드 위치 이동 ===")
for nid, pos, size in MOVES:
    # 위치 이동
    r = call("set_node_position", {
        "asset_path": BP, "graph_name": GRAPH,
        "node_id": nid,
        "position": [pos["x"], pos["y"]],
    })
    ok = r.get("success", False)
    print(f"  [{'OK' if ok else 'FAIL'}] move {nid} -> ({pos['x']}, {pos['y']})"
          + ("" if ok else f" | {str(r)[:120]}"))

    # 크기 조정 시도 (가능한 경우)
    r2 = call("set_pin_default", {
        "asset_path": BP, "graph_name": GRAPH,
        "node_id": nid,
        "pin_name": "NodeWidth",
        "value": str(size["width"]),
    })
    # 이건 Comment node에선 안 먹을 가능성 높음 — 에디터에서 수동 조정 필요

print("\n=== 저장 ===")
r = call("save_asset", {"asset_path": BP})
print(f"  {r}")
