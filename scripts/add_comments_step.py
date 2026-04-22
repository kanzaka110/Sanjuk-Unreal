"""주석 하나씩 만들고 위치 이동 + 검증. 각 단계 멈춰서 확인 가능."""
import json
import subprocess
import sys

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


def verify_position(node_id):
    r = call("get_graph_data", {"asset_path": BP, "graph_name": GRAPH})
    for n in r.get("nodes", []):
        if n.get("id") == node_id:
            pos = n.get("pos") or n.get("position") or [0, 0]
            return pos
    return None


def make_comment(label, text, x, y):
    # 1. 생성
    r = call("add_comment_node", {
        "asset_path": BP, "graph_name": GRAPH,
        "position": [x, y],
        "text": text,
    })
    nid = r.get("node_id") or r.get("id")
    if not nid:
        print(f"  [FAIL] {label} 생성: {r}")
        return None
    print(f"  [{label}] 생성됨 ID={nid}")

    # 2. 위치 이동 (생성 시 무시될 수 있으므로 강제 이동)
    r2 = call("set_node_position", {
        "asset_path": BP, "graph_name": GRAPH,
        "node_id": nid,
        "position": [x, y],
    })
    ok = r2.get("success", False)
    print(f"  [{label}] 위치 설정 ({x},{y}) → {'OK' if ok else r2}")

    # 3. 검증
    actual = verify_position(nid)
    print(f"  [{label}] 실제 위치 = {actual}")
    return nid


# 가드 노드 좌표 범위: x=2368~3216, y=687~992
COMMENTS = [
    # (label, 위치_x, 위치_y, 내용)
    ("메인", 2340, 640,
     "180° Flip Guard\n\n"
     "락온 스프린트 정지 시 타겟이 등 뒤(~180°)에 있을 때\n"
     "Delta(Rotator)가 +180과 -180 사이를 flip하며\n"
     "캐릭터가 반대 방향으로 도는 버그 방지.\n\n"
     "조건: abs(currentDelta) > 170 AND abs(prevDelta) > 0.1\n"
     "  → TargetRotationDelta = sign(prevDelta) * abs(currentDelta)\n"
     "불만족 → 원래 값 유지.\n\n"
     "이전 프레임 부호를 유지해 최단 경로 모호성 구간에서 일관된 회전."),

    ("조건체크", 2350, 700,
     "조건 체크\n"
     "abs(current) > 170 AND abs(prev) > 0.1"),

    ("가드값", 2490, 920,
     "Guard 값\n"
     "sign(prev) × abs(current)\n"
     "(이전 부호 유지)"),

    ("최종선택", 3180, 650,
     "최종 선택\n"
     "조건 T → Guard값\n"
     "조건 F → 원래값"),
]


print("=" * 60)
print("주석 단계별 생성")
print("=" * 60)

for i, (label, x, y, text) in enumerate(COMMENTS, 1):
    print(f"\n[{i}/4] {label} (목표 위치 {x},{y})")
    nid = make_comment(label, text, x, y)
    if not nid:
        print("  실패 — 중단")
        sys.exit(1)

print("\n" + "=" * 60)
print("저장")
print("=" * 60)
r = call("save_asset", {"asset_path": BP})
print(f"  {r}")
