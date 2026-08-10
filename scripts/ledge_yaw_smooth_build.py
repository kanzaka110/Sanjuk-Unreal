# -*- coding: utf-8 -*-
"""렛지 코너 요 스냅 시각 스무딩 빌드 드라이버 (2026-08-10)

배경: 렛지 코너(탄젠트/노멀 90°)에서 캡슐 요가 1틱에 회전 -> 캐릭터가 '탁' 틘다.
  스플라인 탄젠트 라운딩 PIE 실측으로도 잔존(회전 소스가 스플라인이 아님) -> C++ 회전은 못 건드림.
설계: PC_01_AnimLayer_Ledge 서브 ABP에서 액터 요 델타를 누적 역회전(RotateRootBone)으로 상쇄,
  FInterpTo(speed=LedgeYawSmoothSpeed, 기본 12)로 0까지 감쇠 -> 빠르되 틱 스냅 없는 회전.
페이즈: func | eg | anim | finish
"""
import json
import sys
import urllib.request

MCP = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"
FN = "UpdateLedgeYawSmooth"
LOG = {"steps": [], "errors": []}


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(MCP, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:500])
    try:
        return json.loads(txt)
    except Exception:
        return {"raw": txt}


def node_id_of(r):
    nid = r.get("node_id") or r.get("id")
    if nid:
        return nid

    def hv(o):
        if isinstance(o, dict):
            if o.get("node_id") or o.get("id"):
                return o.get("node_id") or o.get("id")
            for v in o.values():
                x = hv(v)
                if x:
                    return x
        elif isinstance(o, list):
            for e in o:
                x = hv(e)
                if x:
                    return x
    return hv(r)


def add(graph, ntype, x, y, **kw):
    p = {"asset_path": BP, "graph_name": graph, "node_type": ntype, "position": [x, y]}
    if "function" in kw:
        kw["function_name"] = kw.pop("function")
    p.update(kw)
    nid = node_id_of(call("blueprint_query", "add_node", p))
    print(f"  + {ntype}({kw.get('function') or kw.get('variable_name') or ''}) -> {nid}")
    return nid


def pindef(graph, nid, pin, val):
    call("blueprint_query", "set_pin_default",
         {"asset_path": BP, "graph_name": graph, "node_id": nid, "pin_name": pin, "value": val})


def connect(graph, cs):
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": graph, "connections": [
        {"source_node": a, "source_pin": b, "target_node": c, "target_pin": d} for a, b, c, d in cs]})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    for fl in fails:
        print("  !! conn fail:", json.dumps(fl, ensure_ascii=False)[:200])
    return len(fails)


def compile_bp():
    r = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
    print("[COMPILE] errors=%s %s" % (r.get("error_count"), json.dumps(r.get("errors"), ensure_ascii=False)[:400] if r.get("error_count") else ""))
    return r


def phase_func():
    try:
        call("blueprint_query", "add_function", {"asset_path": BP, "name": FN})
    except RuntimeError as e:
        print("add_function skip:", e)
    g = call("blueprint_query", "get_graph_summary", {"asset_path": BP, "graph_name": FN})
    for n in g["nodes"]:
        if n["class"] not in ("K2Node_FunctionEntry", "K2Node_FunctionResult"):
            call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": FN, "node_id": n["id"]})
            print("  - cleanup", n["id"])
    entry = [n["id"] for n in g["nodes"] if n["class"] == "K2Node_FunctionEntry"][0]
    print("entry =", entry)

    KM = "KismetMathLibrary"
    getChar = add(FN, "VariableGet", -200, 300, variable_name="As SBCharacter")
    rot = add(FN, "CallFunction", 0, 300, function="K2_GetActorRotation", target_class="Actor")
    brk = add(FN, "CallFunction", 200, 300, function="BreakRotator", target_class=KM)
    getInit = add(FN, "VariableGet", 0, 100, variable_name="bLedgeYawInit")
    br = add(FN, "Branch", 250, 0)
    # 초기화 경로 (else)
    sPrev0 = add(FN, "VariableSet", 550, 250, variable_name="LedgeYawPrev")
    sOff0 = add(FN, "VariableSet", 800, 250, variable_name="LedgeYawSmoothOffset")
    sInit1 = add(FN, "VariableSet", 1050, 250, variable_name="bLedgeYawInit")
    sTick0 = add(FN, "VariableSet", 1300, 250, variable_name="LedgeYawTicked")
    pindef(FN, sOff0, "LedgeYawSmoothOffset", "0.0")
    pindef(FN, sInit1, "bLedgeYawInit", "true")
    pindef(FN, sTick0, "LedgeYawTicked", "true")
    # 본 경로 (then): offset = FInterpTo(offset - NormalizeAxis(yaw - prev), 0, dt, speed)
    getPrev = add(FN, "VariableGet", 200, 550, variable_name="LedgeYawPrev")
    sub1 = add(FN, "CallFunction", 400, 500, function="Subtract_DoubleDouble", target_class=KM)
    norm = add(FN, "CallFunction", 560, 500, function="NormalizeAxis", target_class=KM)
    getOff = add(FN, "VariableGet", 400, 650, variable_name="LedgeYawSmoothOffset")
    sub2 = add(FN, "CallFunction", 720, 550, function="Subtract_DoubleDouble", target_class=KM)
    dt = add(FN, "CallFunction", 720, 700, function="GetWorldDeltaSeconds", target_class="GameplayStatics")
    getSpd = add(FN, "VariableGet", 720, 800, variable_name="LedgeYawSmoothSpeed")
    interp = add(FN, "CallFunction", 900, 550, function="FInterpTo", target_class=KM)
    sOff1 = add(FN, "VariableSet", 1150, -50, variable_name="LedgeYawSmoothOffset")
    sPrev1 = add(FN, "VariableSet", 1400, -50, variable_name="LedgeYawPrev")
    sTick1 = add(FN, "VariableSet", 1650, -50, variable_name="LedgeYawTicked")
    pindef(FN, interp, "Target", "0.0")
    pindef(FN, sTick1, "LedgeYawTicked", "true")

    f = connect(FN, [
        (getChar, "As SBCharacter", rot, "self"),
        (rot, "ReturnValue", brk, "InRot"),
        (entry, "then", br, "execute"),
        (getInit, "bLedgeYawInit", br, "Condition"),
        # else = init
        (br, "else", sPrev0, "execute"),
        (brk, "Yaw", sPrev0, "LedgeYawPrev"),
        (sPrev0, "then", sOff0, "execute"),
        (sOff0, "then", sInit1, "execute"),
        (sInit1, "then", sTick0, "execute"),
        # then = main
        (brk, "Yaw", sub1, "A"),
        (getPrev, "LedgeYawPrev", sub1, "B"),
        (sub1, "ReturnValue", norm, "Angle"),
        (getOff, "LedgeYawSmoothOffset", sub2, "A"),
        (norm, "ReturnValue", sub2, "B"),
        (sub2, "ReturnValue", interp, "Current"),
        (dt, "ReturnValue", interp, "DeltaTime"),
        (getSpd, "LedgeYawSmoothSpeed", interp, "InterpSpeed"),
        (br, "then", sOff1, "execute"),
        (interp, "ReturnValue", sOff1, "LedgeYawSmoothOffset"),
        (sOff1, "then", sPrev1, "execute"),
        (brk, "Yaw", sPrev1, "LedgeYawPrev"),
        (sPrev1, "then", sTick1, "execute"),
    ])
    LOG["steps"].append("func built, conn fails=%d" % f)
    compile_bp()


def phase_eg():
    G = "EventGraph"
    # 1) 렛지 체인 꼬리: UpdateLedgeLook 뒤에 자기함수 호출 (compile 선행됨)
    cy = add(G, "CallFunction", 2600, 1500, function=FN, target_class="PC_01_AnimLayer_Ledge_C")
    f1 = connect(G, [("K2Node_CallFunction_4", "then", cy, "execute")])
    # 2) 프리스위치 스플라이스: VS_40 -> [Branch(Ticked)] -> Switch
    getTick = add(G, "VariableGet", 380, 700, variable_name="LedgeYawTicked")
    brT = add(G, "Branch", 560, 620)
    sTickF = add(G, "VariableSet", 800, 560, variable_name="LedgeYawTicked")
    sInitF = add(G, "VariableSet", 800, 760, variable_name="bLedgeYawInit")
    sOffZ = add(G, "VariableSet", 1050, 760, variable_name="LedgeYawSmoothOffset")
    pindef(G, sTickF, "LedgeYawTicked", "false")
    pindef(G, sInitF, "bLedgeYawInit", "false")
    pindef(G, sOffZ, "LedgeYawSmoothOffset", "0.0")
    call("blueprint_query", "disconnect_pins",
         {"asset_path": BP, "graph_name": G, "source_node": "K2Node_VariableSet_40", "source_pin": "then",
          "target_node": "K2Node_SwitchEnum_0", "target_pin": "execute"})
    f2 = connect(G, [
        ("K2Node_VariableSet_40", "then", brT, "execute"),
        (getTick, "LedgeYawTicked", brT, "Condition"),
        (brT, "then", sTickF, "execute"),
        (sTickF, "then", "K2Node_SwitchEnum_0", "execute"),
        (brT, "else", sInitF, "execute"),
        (sInitF, "then", sOffZ, "execute"),
        (sOffZ, "then", "K2Node_SwitchEnum_0", "execute"),
    ])
    LOG["steps"].append("eg spliced, fails=%d/%d" % (f1, f2))
    compile_bp()


def phase_anim():
    # RotateRootBone: AnimGraph에서 빌드+바인딩 -> Ledge 그래프로 copy_nodes -> 원본 제거 -> CR와 Root 사이 배선
    r = call("animation_query", "add_anim_graph_node",
             {"asset_path": BP, "graph_name": "AnimGraph", "node_class": "AnimGraphNode_RotateRootBone"})
    nid = r.get("node_name") or node_id_of(r)
    print("RotateRootBone(AnimGraph) =", nid)
    call("animation_query", "set_anim_node_pin_binding",
         {"asset_path": BP, "graph_name": "AnimGraph", "node_id": nid, "pin": "Yaw",
          "path": ["LedgeYawSmoothOffset"]})
    call("blueprint_query", "copy_nodes",
         {"source_asset": BP, "source_graph": "AnimGraph", "node_ids": [nid],
          "target_asset": BP, "target_graph": "Ledge"})
    call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": "AnimGraph", "node_id": nid})
    # 복사본 id 확인
    g = call("blueprint_query", "get_graph_summary", {"asset_path": BP, "graph_name": "Ledge"})
    rrb = [n["id"] for n in g["nodes"] if n["class"] == "AnimGraphNode_RotateRootBone"]
    assert rrb, "Ledge 그래프에 RotateRootBone 복사본 없음"
    rrb = rrb[0]
    print("RotateRootBone(Ledge) =", rrb)
    # 현재 CR -> Root 연결 확인 후 사이에 삽입
    root = call("blueprint_query", "get_node_details",
                {"asset_path": BP, "graph_name": "Ledge", "node_id": "AnimGraphNode_Root_0"})
    rpin = [p for p in root["pins"] if p["direction"] == "input" and p.get("connected_to")]
    print("Root input:", json.dumps(rpin, ensure_ascii=False)[:300])
    src = rpin[0]["connected_to"][0]
    src_node, src_pin = src.rsplit(".", 1)
    rin = rpin[0]["name"]
    call("blueprint_query", "disconnect_pins",
         {"asset_path": BP, "graph_name": "Ledge", "source_node": src_node, "source_pin": src_pin,
          "target_node": "AnimGraphNode_Root_0", "target_pin": rin})
    rrb_d = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": "Ledge", "node_id": rrb})
    pose_in = [p["name"] for p in rrb_d["pins"] if p["direction"] == "input" and "pose" in p["name"].lower()]
    pose_out = [p["name"] for p in rrb_d["pins"] if p["direction"] == "output"]
    print("RRB pins in/out:", pose_in, pose_out)
    f = connect("Ledge", [
        (src_node, src_pin, rrb, pose_in[0]),
        (rrb, pose_out[0], "AnimGraphNode_Root_0", rin),
    ])
    LOG["steps"].append("anim wired fails=%d (src=%s.%s)" % (f, src_node, src_pin))
    compile_bp()


def phase_finish():
    compile_bp()
    r = call("blueprint_query", "save_asset", {"asset_path": BP})
    print("[SAVE]", json.dumps(r, ensure_ascii=False)[:300])


if __name__ == "__main__":
    ph = sys.argv[1] if len(sys.argv) > 1 else ""
    {"func": phase_func, "eg": phase_eg, "anim": phase_anim, "finish": phase_finish}[ph]()
    print(json.dumps(LOG, ensure_ascii=False))
