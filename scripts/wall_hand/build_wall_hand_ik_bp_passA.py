"""PC_01_BP 'UpdateWallHandIK' 함수 — Pass A: 함수 생성 + 전 노드 추가 + 핀 덤프.

연결/디폴트/컴파일은 Pass B(핀명 확인 후). 출력은 scratch 파일로 회수.
설계: 양쪽 SphereTrace(Visibility) -> nearest 선택 -> SetWallHandData(ABP) 호출.
"""
import json
import subprocess

MCP = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "UpdateWallHandIK"
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_passA.txt"

KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"


def call(action: str, args: dict) -> dict:
    payload = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
               "params": {"name": "blueprint_query",
                          "arguments": {"action": action, **args}}}
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", MCP,
         "-H", "Content-Type: application/json", "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=40)
    try:
        d = json.loads(r.stdout)
        txt = d.get("result", {}).get("content", [{}])[0].get("text", "")
        return json.loads(txt)
    except Exception:
        return {"_raw": r.stdout[:400]}


log = []


def p(s):
    log.append(s)
    print(s)


def add(node_type: str, pos, **kw) -> str:
    res = call("add_node", {"asset_path": BP, "graph_name": FN,
                            "node_type": node_type, "position": pos, **kw})
    nid = res.get("id") or res.get("node_id")
    p(f"ADD {node_type} {kw} -> {nid} | {res if not nid else ''}")
    return nid


# === 1. 함수 생성 (game-thread, thread_safe=False) ===
p("=== add_function ===")
p(str(call("add_function", {"asset_path": BP, "name": FN,
                            "category": "WallHandIK", "pure": False,
                            "thread_safe": False,
                            "tooltip": "좁은 통로 벽 짚기: 양쪽 SphereTrace->nearest->SetWallHandData. Tick에서 호출."})))

# === 2. 노드 추가 ===
p("\n=== nodes ===")
ids = {}
ids["mesh"] = add("VariableGet", [-1600, 0], variable_name="Mesh")
ids["socket"] = add("CallFunction", [-1350, 0], function_name="GetSocketLocation", target_class="SceneComponent")
ids["right"] = add("CallFunction", [-1350, 250], function_name="GetActorRightVector", target_class="Actor")
ids["mulR"] = add("CallFunction", [-1100, 250], function_name="Multiply_VectorFloat", target_class=KML)
ids["addR"] = add("CallFunction", [-850, 100], function_name="Add_VectorVector", target_class=KML)
ids["subL"] = add("CallFunction", [-850, 350], function_name="Subtract_VectorVector", target_class=KML)
ids["traceR"] = add("CallFunction", [-550, 0], function_name="SphereTraceSingle", target_class=KSL)
ids["traceL"] = add("CallFunction", [-550, 450], function_name="SphereTraceSingle", target_class=KSL)
ids["breakR"] = add("BreakStruct", [-250, 0], struct_type="HitResult")
ids["breakL"] = add("BreakStruct", [-250, 450], struct_type="HitResult")
ids["effR"] = add("CallFunction", [0, 100], function_name="SelectFloat", target_class=KML)
ids["effL"] = add("CallFunction", [0, 350], function_name="SelectFloat", target_class=KML)
ids["bRight"] = add("CallFunction", [250, 200], function_name="LessEqual_DoubleDouble", target_class=KML)
ids["selImpact"] = add("CallFunction", [500, 0], function_name="SelectVector", target_class=KML)
ids["selNormal"] = add("CallFunction", [500, 300], function_name="SelectVector", target_class=KML)
ids["mulOff"] = add("CallFunction", [750, 300], function_name="Multiply_VectorFloat", target_class=KML)
ids["addTgt"] = add("CallFunction", [1000, 0], function_name="Add_VectorVector", target_class=KML)
ids["orHit"] = add("CallFunction", [250, 500], function_name="BooleanOR", target_class=KML)
ids["selAlpha"] = add("CallFunction", [500, 500], function_name="SelectFloat", target_class=KML)
ids["animInst"] = add("CallFunction", [1000, 600], function_name="GetAnimInstance", target_class="SkeletalMeshComponent")
ids["cast"] = add("DynamicCast", [1250, 600], cast_class="PC_01_ABP")
ids["setter"] = add("CallFunction", [1550, 400], function_name="SetWallHandData", target_class="PC_01_ABP")

# === 3. Entry 노드 + 핀 덤프 ===
p("\n=== graph nodes (entry 찾기) ===")
gd = call("get_graph_data", {"asset_path": BP, "graph_name": FN})
for n in gd.get("nodes", []):
    if n.get("class") == "K2Node_FunctionEntry":
        p(f"ENTRY = {n.get('id')}")

p("\n=== PIN DUMPS ===")
for key, nid in ids.items():
    if not nid:
        p(f"\n## {key}: <NO ID>")
        continue
    det = call("get_node_details", {"asset_path": BP, "graph_name": FN, "node_id": nid})
    pins = det.get("pins", [])
    brief = [f"{pn['name']}({pn['direction']},{pn.get('type')}{',EXEC' if pn.get('is_exec') else ''})" for pn in pins]
    p(f"\n## {key} [{nid}] {det.get('class')}")
    for b in brief:
        p(f"   {b}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(log))
    f.write("\n\nIDS=" + json.dumps(ids))
print(f"\nWROTE {OUT}")
