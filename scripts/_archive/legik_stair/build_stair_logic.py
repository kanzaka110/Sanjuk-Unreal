"""PC_01_ABP에 UpdateStairAlpha 함수 생성 + 내부 로직 구축 + 호출 연결."""
import json
import subprocess

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
FN = "UpdateStairAlpha"


def call(action: str, args: dict) -> dict:
    payload = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {"name": "blueprint_query",
                   "arguments": {"action": action, **args}}
    }
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", MCP,
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=30)
    d = json.loads(r.stdout)
    txt = d.get("result", {}).get("content", [{}])[0].get("text", "")
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"_raw": txt}


# === 1. 함수 생성 ===
print("=== 함수 생성 ===")
res = call("add_function", {
    "asset_path": BP,
    "name": FN,
    "category": "StairDetection",
    "pure": False,
    "thread_safe": True,   # BlueprintThreadSafeUpdateAnimation에서 호출하려면 thread-safe
    "tooltip": "계단 감지 및 FootPlacementAlpha 제어. BlueprintThreadSafeUpdateAnimation에서 호출.",
})
print(f"  {res}")

# 함수 시그니처 설정: DeltaTime, CurrentCapsuleZ 입력
print("\n=== 함수 파라미터 설정 ===")
res = call("set_function_params", {
    "asset_path": BP,
    "function_name": FN,
    "inputs": [
        {"name": "DeltaTime", "type": "float"},
        {"name": "CurrentCapsuleZ", "type": "float"},
    ],
    "outputs": [],
})
print(f"  {res}")
