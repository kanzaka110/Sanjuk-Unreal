"""PC_01_ABP에 계단 감지용 변수 5개 추가. Monolith blueprint_query 사용."""
import json
import subprocess

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"

VARIABLES = [
    # name, type, default, tooltip
    ("LastCapsuleZ", "float", "0.0",
     "직전 프레임 액터 Z 위치. 계단 감지용 DeltaZ 계산 기준."),
    ("StairAlphaRecoveryTimer", "float", "0.0",
     "계단 감지 후 FootPlacementAlpha 복귀까지 남은 시간(초). 감지 시 StairAlphaRecoveryTime으로 리셋됨."),
    ("StairVerticalSpeedThreshold", "float", "300.0",
     "계단 감지 임계 속도(cm/s). 프레임간 Z 변화량의 절대값이 이 값을 넘으면 계단 턱 점프로 판정."),
    ("StairAlphaRecoveryTime", "float", "0.25",
     "FootPlacementAlpha가 계단 감지 후 1.0으로 복귀하는 데 걸리는 시간(초)."),
    ("StairAlphaMin", "float", "0.3",
     "계단 감지 직후 FootPlacementAlpha 최소값. 0에 가까울수록 계단에서 FootPlacement 영향 약화."),
]


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


print("=== 변수 추가 ===")
for name, vtype, default, tooltip in VARIABLES:
    res = call("add_variable", {
        "asset_path": BP,
        "name": name,
        "type": vtype,
        "default_value": default,
        "category": "StairDetection",
        "tooltip": tooltip,
    })
    ok = res.get("success", False) or "created" in str(res).lower()
    mark = "[OK]" if ok else "[FAIL]"
    print(f"  {mark} {name} ({vtype}, def={default})")
    if not ok:
        print(f"        {res}")

print("\n=== 검증 ===")
res = call("get_variables", {"asset_path": BP})
var_names = [v.get("name") for v in res.get("variables", [])]
added = [n for n, *_ in VARIABLES if n in var_names]
missing = [n for n, *_ in VARIABLES if n not in var_names]
print(f"  추가됨: {len(added)}/{len(VARIABLES)}")
for n in added:
    print(f"    [OK] {n}")
for n in missing:
    print(f"    [MISSING] {n}")
