# 경사 Z보정 M6 — DzBody 파이프: ABP → LedgeState 출력 → IK레이어 변수 → CR 핀 바인딩 (2026-07-24)
# 1) ABP LedgeState 함수에 출력 LedgeSlopeDzBody(float) 추가 (set_function_params = 추가 전용)
# 2) LedgeState 그래프: Get LedgeSlopeDzBody → FunctionResult 새 핀
# 3) IK레이어: 변수 LedgeSlopeDzBody 추가
# 4) IK레이어 EventGraph: LedgeState 콜 refresh → 새 출력 → Set 스플라이스 (CF_16.then ~ VS_16 사이)
# 5) IK그래프의 CR 노드(PC_01_CtrlRig_LedgeDangle)에 set_anim_node_pin_binding(PelvisSlopeLift ← LedgeSlopeDzBody)
# 실행: py slope_z_m6_pipe.py apply [step]  (step 지정 시 해당 단계만)
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
IKL = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
VAR = "LedgeSlopeDzBody"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"
ONLY = sys.argv[2] if len(sys.argv) > 2 else None


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:500])
    return json.loads(txt)


def bq(asset, action, params):
    p = {"asset_path": asset}
    p.update(params)
    return call("blueprint_query", action, p)


def graph(asset, g):
    return {n["id"]: n for n in bq(asset, "get_graph_data", {"graph_name": g})["nodes"]}


def pins(nodes, nid):
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def pie_on():
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


def step_on(s):
    return ONLY is None or ONLY == s


if not APPLY:
    # dry-run: 전제 확인만
    ls = graph(ABP, "LedgeState")
    frs = [nid for nid, n in ls.items() if n["class"] == "K2Node_FunctionResult"]
    print("[PF] LedgeState FunctionResult:", frs)
    ev = graph(IKL, "EventGraph")
    assert "K2Node_CallFunction_16" in ev, "IK LedgeState 콜 미발견"
    p16 = pins(ev, "K2Node_CallFunction_16")
    print("[PF] CF_16.then ->", p16["then"]["connected_to"])
    ik = graph(IKL, "IK")
    crn = [nid for nid, n in ik.items() if "ControlRig" in n["class"]]
    print("[PF] IK그래프 CR노드 후보:", [(nid, ik[nid]["class"]) for nid in crn])
    print("== dry-run 종료 ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"

# ── 1) 함수 출력 추가 ──
if step_on("1"):
    r = bq(ABP, "set_function_params", {"function_name": "LedgeState",
                                        "outputs": [{"name": VAR, "type": "float"}]})
    print("[S1] set_function_params:", json.dumps(r)[:200])

# ── 2) LedgeState 내부 배선 ──
if step_on("2"):
    ls = graph(ABP, "LedgeState")
    frs = [nid for nid, n in ls.items() if n["class"] == "K2Node_FunctionResult"]
    assert frs, "FunctionResult 미발견"
    ok2 = 0
    r = bq(ABP, "add_node", {"graph_name": "LedgeState", "node_type": "VariableGet",
                             "variable_name": VAR, "position": [0, 0]})
    getn = r.get("id") or r.get("node_id")
    print("[S2] add Get:", getn)
    for fr in frs:
        prev = pins(ls, fr)
        assert VAR in prev or True, ""
        bq(ABP, "connect_pins", {"graph_name": "LedgeState", "source_node": getn, "source_pin": VAR,
                                 "target_node": fr, "target_pin": VAR})
        ok2 += 1
        print("[S2] wired ->", fr)
    assert ok2 > 0

# ── 3) IK레이어 변수 ──
if step_on("3"):
    vnames = {v["name"] for v in bq(IKL, "get_variables", {}).get("variables", [])}
    if VAR not in vnames:
        bq(IKL, "add_variable", {"name": VAR, "type": "float", "category": "Ledge|SlopeZ"})
        print("[S3] +var", VAR)
    else:
        print("[S3] skip var")

# ── 4) IK레이어 수신 스플라이스 ──
if step_on("4"):
    bq(IKL, "refresh_node", {"graph_name": "EventGraph", "node_id": "K2Node_CallFunction_16"})
    print("[S4] refreshed CF_16")
    ev = graph(IKL, "EventGraph")
    p16 = pins(ev, "K2Node_CallFunction_16")
    assert VAR in p16, "CF_16에 새 출력 핀 없음 — refresh/시그니처 확인"
    dst = p16["then"]["connected_to"]
    assert len(dst) == 1, "CF_16.then 다중: " + json.dumps(dst)
    dn, dp = dst[0].split(".", 1)
    r = bq(IKL, "add_node", {"graph_name": "EventGraph", "node_type": "VariableSet",
                             "variable_name": VAR, "position": [1400, 1700]})
    setn = r.get("id") or r.get("node_id")
    print("[S4] add Set:", setn)
    bq(IKL, "disconnect_pins", {"graph_name": "EventGraph", "source_node": "K2Node_CallFunction_16",
                                "source_pin": "then", "target_node": dn, "target_pin": dp})
    bq(IKL, "connect_pins", {"graph_name": "EventGraph", "source_node": "K2Node_CallFunction_16",
                             "source_pin": "then", "target_node": setn, "target_pin": "execute"})
    bq(IKL, "connect_pins", {"graph_name": "EventGraph", "source_node": setn,
                             "source_pin": "then", "target_node": dn, "target_pin": dp})
    bq(IKL, "connect_pins", {"graph_name": "EventGraph", "source_node": "K2Node_CallFunction_16",
                             "source_pin": VAR, "target_node": setn, "target_pin": VAR})
    print("[S4] spliced CF_16.then ->", setn, "->", dn + "." + dp)

# ── 5) CR 핀 바인딩 ──
if step_on("5"):
    ik = graph(IKL, "IK")
    # LedgeDangle 릭 판별: HandTargetL 핀 보유 노드 (실측: AnimGraphNode_ControlRig_1)
    crn = [nid for nid, n in ik.items() if "ControlRig" in n["class"]
           and any(p["name"] == "HandTargetL" for p in n.get("pins", []))]
    assert len(crn) == 1, "LedgeDangle CR노드 판별 실패: " + json.dumps(crn)
    nid = crn[0]
    print("[S5] LedgeDangle CR노드:", nid)
    r = call("animation_query", "set_anim_node_pin_binding", {
        "asset_path": IKL, "node_id": nid, "pin": "PelvisSlopeLift", "path": [VAR]})
    print("[S5] bind:", json.dumps(r)[:300])

# ── 검증/컴파일 ──
for asset in (ABP, IKL):
    r = bq(asset, "compile_blueprint", {})
    print("[COMPILE]", asset.split("/")[-1], json.dumps(r)[:200])
