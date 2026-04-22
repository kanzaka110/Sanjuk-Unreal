"""가드 로직에 Comment 블록 + 개별 주석 추가."""
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


def pp(label, res):
    ok = res.get("success", False) or ("id" in res)
    print(f"  [{'OK' if ok else 'FAIL'}] {label}"
          + ("" if ok else f" | {str(res)[:150]}"))


# 가드 로직 노드들의 대략적 위치 (앞 스크립트 좌표 기준)
# X0 = 1500, Y 범위 100~400
# 노드들: x=1500~2300, y=100~400

# === 1. 메인 코멘트 블록 (전체 가드 로직 감싸기) ===
print("=== 메인 Comment 블록 ===")
r = call("add_comment_node", {
    "asset_path": BP, "graph_name": GRAPH,
    "position": {"x": 1450, "y": 50},
    "size": {"width": 900, "height": 450},
    "text": (
        "180° Flip Guard\n"
        "\n"
        "락온 스프린트 정지 시 타겟이 등 뒤(~180°)에 있을 때\n"
        "Delta(Rotator)가 +180과 -180 사이를 flip하며\n"
        "캐릭터가 반대 방향으로 도는 버그 방지.\n"
        "\n"
        "조건: abs(currentDelta) > 170 AND abs(prevDelta) > 0.1\n"
        "  → TargetRotationDelta = sign(prevDelta) * abs(currentDelta)\n"
        "조건 불만족:\n"
        "  → TargetRotationDelta = 원래 PromotableOperator_1 결과\n"
        "\n"
        "이전 프레임의 회전 방향 부호를 유지해\n"
        "최단 경로 모호성 구간(±170° ~ ±180°)에서 일관된 회전 유지."
    ),
    "comment_color": {"R": 0.2, "G": 0.5, "B": 0.8, "A": 0.4},
})
pp("Main guard comment", r)

# === 2. 세부 코멘트 (옵션) ===
# 조건 계산 영역
print("\n=== 세부 Comment — 조건 계산 ===")
r = call("add_comment_node", {
    "asset_path": BP, "graph_name": GRAPH,
    "position": {"x": 1480, "y": 80},
    "size": {"width": 420, "height": 280},
    "text": "조건 체크\nabs(current) > 170 AND abs(prev) > 0.1",
    "comment_color": {"R": 0.8, "G": 0.7, "B": 0.2, "A": 0.3},
})
pp("조건 체크 comment", r)

# 값 계산 영역
print("\n=== 세부 Comment — Guard 값 ===")
r = call("add_comment_node", {
    "asset_path": BP, "graph_name": GRAPH,
    "position": {"x": 1880, "y": 250},
    "size": {"width": 320, "height": 200},
    "text": "Guard 값\nsign(prev) × abs(current)\n(이전 부호 유지)",
    "comment_color": {"R": 0.3, "G": 0.7, "B": 0.3, "A": 0.3},
})
pp("Guard 값 comment", r)

# Select 영역
print("\n=== 세부 Comment — Select ===")
r = call("add_comment_node", {
    "asset_path": BP, "graph_name": GRAPH,
    "position": {"x": 2220, "y": 200},
    "size": {"width": 200, "height": 160},
    "text": "최종 선택\n조건 T → Guard값\n조건 F → 원래값",
    "comment_color": {"R": 0.6, "G": 0.3, "B": 0.6, "A": 0.3},
})
pp("Select comment", r)

# === 3. 컴파일 + 저장 ===
print("\n=== 컴파일 ===")
r = call("compile_blueprint", {"asset_path": BP})
print(f"  success = {r.get('success')}, status = {r.get('status')}")

print("\n=== 저장 ===")
r = call("save_asset", {"asset_path": BP})
print(f"  {r}")
