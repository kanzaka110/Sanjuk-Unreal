"""Stair Detection 구현 롤백:
- EventGraph의 내가 추가한 노드들 제거 (GetOwningActor, GetActorLocation, BreakVector, Set CapturedActorZ, Call UpdateStairAlpha, BlueprintUpdateAnimation 이벤트)
- UpdateStairAlpha 함수는 유지 (호출되지 않으면 영향 없음)
- 변수는 유지 (사용 안 되면 영향 없음)
"""
import json
import subprocess

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"


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
    ok = res.get("success", False) or res.get("removed_node")
    print(f"  [{'OK' if ok else 'FAIL'}] {label}"
          + ("" if ok else f" | {str(res)[:120]}"))


# EventGraph에서 내가 추가한 노드들 찾아 제거
print("=== EventGraph 스캔 ===")
g = call("get_graph_data", {"asset_path": BP, "graph_name": "EventGraph"})
targets = []
for n in g.get("nodes", []):
    cls = n.get("class", "")
    title = n.get("title", "")
    nid = n.get("id")
    # 내가 추가한 것: Update Animation 이벤트, Get Owning Actor, Get Actor Location, Break Vector, Set CapturedActorZ, UpdateStairAlpha 호출
    if (cls == "K2Node_Event" and "Update Animation" in title and "Initialize" not in title and "Post Evaluate" not in title):
        targets.append((nid, "Event BlueprintUpdateAnimation"))
    elif cls == "K2Node_CallFunction" and any(k in title for k in ("Get Owning Actor", "Get Actor Location", "Break Vector", "Update Stair Alpha")):
        targets.append((nid, title[:50]))
    elif cls == "K2Node_VariableSet" and "CapturedActorZ" in title:
        targets.append((nid, title[:50]))

print(f"제거 대상: {len(targets)}개")
for nid, label in targets:
    print(f"  - {nid}: {label}")

print("\n=== 노드 제거 ===")
for nid, label in targets:
    res = call("remove_node", {"asset_path": BP, "graph_name": "EventGraph", "node_id": nid})
    pp(f"remove {nid} ({label})", res)

# 컴파일
print("\n=== 컴파일 ===")
res = call("compile_blueprint", {"asset_path": BP})
print(f"  success = {res.get('success')}, status = {res.get('status')}")
for e in (res.get("errors") or [])[:5]:
    print(f"    [{e.get('node_id')}] {e.get('message','')[:120]}")

# 저장
print("\n=== 저장 ===")
res = call("save_asset", {"asset_path": BP})
print(f"  {res}")
