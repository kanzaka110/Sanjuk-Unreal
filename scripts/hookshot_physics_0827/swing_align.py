# -*- coding: utf-8 -*-
"""스윙 로프 정렬 — 캐릭터 +Z(머리)가 앵커를 향하도록 (2026-08-27)

승호 요구: "스윙에 한정해서 로프를 놓기 전까지는 캐릭터가 목표점을 향해 회전.
            목표점이 향하는 방향의 Z축, 머리 위가 목표점이 되게"

레이어 PC_01_AnimLayer_Hookshot 안에서 완결. 시각만 (캡슐·카메라·C++ 회전 불변).

  dir   = Normal(TargetLocation − CharacterLocation)
  axis  = Normal(Cross(worldZ, dir))                       최소회전 축
  angle = DegAcos(Dot(worldZ, dir)) × HookSwingAlignScale
  gated = (bHookIsSwing AND Phase==Moving) ? angle : 0
  HookSwingAlignAngle = FInterpTo(cur, gated, DeltaTime, HookSwingAlignSpeed)
  HookSwingAlignRot   = RotatorFromAxisAndAngle(axis, HookSwingAlignAngle)

적용은 HookShot 그래프 최후미 ModifyBone(root) / Add to Existing / World Space.

phase: vars | func | copy | wire | chain | compile | save | all
"""
import json
import sys
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot"
G = "UpdateHookSwingAlign"
SRC_G = "UpdateHookshotLand"
CAT = "Hookshot Swing Align"
PHASE_MOVING = "3"

# 복제할 PropertyAccess (경로를 알 수 없어 원본을 복사한다)
PA_TARGET = "K2Node_PropertyAccess_1"    # TargetLocation (Vector)
PA_DELTA = "K2Node_PropertyAccess_10"    # DeltaTime (float)
# CharacterTransform 은 메인 ABP 변수 -> 레이어에서 VariableGet 생성 불가(빈 노드).
# 원본 크로스타깃 Getter 를 복제해서 쓴다.
VG_CT = "K2Node_VariableGet_10"          # Get CharacterTransform (self <- As SBCharacterABP)

VARS = [
    ("HookSwingAlignScale", "float", "1.0"),
    ("HookSwingAlignSpeed", "float", "10.0"),
    ("HookSwingAlignAngle", "float", "0.0"),
    ("HookSwingAlignRot", "struct:Rotator", ""),
    ("HookSwingAlignMaxDeg", "float", "60.0"),    # 각도 상한
    ("HookSwingArcDuration", "float", "1.0"),     # 0 -> 최대 -> 0 한 사이클 시간(초)
    ("HookSwingElapsed", "float", "0.0"),         # 스윙 경과시간(내부)
]

LOG = []


def call(action, args, tool="blueprint_query", timeout=300):
    a = dict(args)
    a["action"] = action
    b = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
         "params": {"name": tool, "arguments": a}}
    r = json.load(urllib.request.urlopen(
        urllib.request.Request(MCP, json.dumps(b).encode(),
                               {"Content-Type": "application/json"}), timeout=timeout))
    res = r["result"]
    t = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError("%s: %s" % (action, t[:600]))
    try:
        return json.loads(t)
    except Exception:
        return {"raw": t}


def node(node_type, pos, **kw):
    a = {"asset_path": BP, "graph_name": G, "node_type": node_type, "position": list(pos)}
    a.update(kw)
    out = call("add_node", a)
    nid = out.get("node_id") or out.get("id")
    if not nid:
        raise RuntimeError("no node_id: %s" % json.dumps(out)[:300])
    LOG.append(nid)
    return nid


def fn(name, pos, cls="KismetMathLibrary"):
    return node("call", pos, function_name=name, target_class=cls)


def link(sn, sp, tn, tp):
    call("connect_pins", {"asset_path": BP, "graph_name": G, "source_node": sn,
                          "source_pin": sp, "target_node": tn, "target_pin": tp})


def pin(nid, name, value):
    call("set_pin_default", {"asset_path": BP, "graph_name": G, "node_id": nid,
                             "pin_name": name, "value": str(value)})


def summary(graph=None):
    return call("get_graph_summary", {"asset_path": BP, "graph_name": graph or G})


def do_vars():
    got = call("get_variables", {"asset_path": BP})
    have = {v.get("name") for v in (got.get("variables") or [])}
    for n, t, d in VARS:
        if n in have:
            print("  skip", n)
            continue
        a = {"asset_path": BP, "name": n, "type": t, "category": CAT}
        if d:
            a["default_value"] = d
        call("add_variable", a)
        print("  +var", n, t, d)


def do_func():
    fns = call("get_functions", {"asset_path": BP})
    names = {f.get("name") if isinstance(f, dict) else f
             for f in (fns.get("functions") or fns.get("graphs") or [])}
    if G not in names:
        call("add_function", {"asset_path": BP, "name": G, "category": CAT,
                              "description": "스윙 중 캐릭터 +Z 를 앵커 방향으로 정렬하는 회전값 산출"})
        print("  +func", G)
    # EventGraph(게임스레드) 체인에서 호출 + 오브젝트 레퍼런스 접근(GetHookshotPhase /
    # As SBCharacterABP)이 있으므로 thread-safe 로 두면 컴파일 에러. 기존 UpdateHookshotLand 와 동일.
    call("set_function_thread_safe", {"asset_path": BP, "function_name": G, "thread_safe": False})
    print("  thread_safe=False")


def do_copy():
    """PropertyAccess 2개를 원본 그래프에서 복제 (경로 보존)"""
    before = {n["id"] for n in summary()["nodes"]}
    call("copy_nodes", {"source_asset": BP, "source_graph": SRC_G,
                        "node_ids": [PA_TARGET, PA_DELTA, VG_CT],
                        "target_asset": BP, "target_graph": G})
    after = summary()["nodes"]
    new = [n for n in after if n["id"] not in before]
    print("  복제된 노드:")
    for n in new:
        d = call("get_node_details", {"blueprint_path": BP, "graph_name": G, "node_id": n["id"]})
        types = [p["type"] for p in d["pins"] if p["direction"] == "output"]
        print("   ", n["id"], "|", n.get("title", "").replace("\n", " "), "| out:", types)


def find_pa():
    """복제된 노드를 출력 타입으로 식별 -> (TargetLocation, DeltaTime, CharacterTransform)"""
    tgt = dt = ct = None
    for n in summary()["nodes"]:
        if n["class"] not in ("K2Node_PropertyAccess", "K2Node_VariableGet"):
            continue
        d = call("get_node_details", {"blueprint_path": BP, "graph_name": G, "node_id": n["id"]})
        for p in d["pins"]:
            if p["direction"] != "output":
                continue
            if n["class"] == "K2Node_PropertyAccess" and p["type"].startswith("struct:Vector"):
                tgt = n["id"]
            elif n["class"] == "K2Node_PropertyAccess" and p["type"] in ("float", "double", "real"):
                dt = n["id"]
            elif p["type"].startswith("struct:Transform"):
                ct = n["id"]
    if not (tgt and dt and ct):
        raise RuntimeError("노드 식별 실패 tgt=%s dt=%s ct=%s" % (tgt, dt, ct))
    return tgt, dt, ct


def do_wire():
    E = [n["id"] for n in summary()["nodes"] if n["class"] == "K2Node_FunctionEntry"][0]
    pa_tgt, pa_dt, v_ct = find_pa()
    print("  entry=%s  PA(target)=%s  PA(delta)=%s  VG(ct)=%s" % (E, pa_tgt, pa_dt, v_ct))

    # 캐릭터 위치 — 복제한 크로스타깃 Getter 에 self 를 물려준다
    v_abp = node("get", (-1960, 380), variable_name="As SBCharacterABP")
    link(v_abp, "As SBCharacterABP", v_ct, "self")
    brk = fn("BreakTransform", (-1480, 300))
    link(v_ct, "CharacterTransform", brk, "InTransform")

    # dir = Normal(Target - CharLoc)
    sub = fn("Subtract_VectorVector", (-1240, 220))
    link(pa_tgt, "Value", sub, "A")
    link(brk, "Location", sub, "B")
    nrm = fn("Normal", (-1040, 220))
    link(sub, "ReturnValue", nrm, "A")

    # worldZ
    upz = fn("MakeVector", (-1040, 420))
    pin(upz, "X", "0.0")
    pin(upz, "Y", "0.0")
    pin(upz, "Z", "1.0")

    # axis = Normal(Cross(Z, dir))
    crs = fn("Cross_VectorVector", (-820, 320))
    link(upz, "ReturnValue", crs, "A")
    link(nrm, "ReturnValue", crs, "B")
    axn = fn("Normal", (-620, 320))
    link(crs, "ReturnValue", axn, "A")

    # rawAngle = DegAcos(Dot(Z, dir)) — 로프가 수직에서 기운 각
    dot = fn("Dot_VectorVector", (-820, 120))
    link(upz, "ReturnValue", dot, "A")
    link(nrm, "ReturnValue", dot, "B")
    acs = fn("DegAcos", (-620, 120))
    link(dot, "ReturnValue", acs, "A")

    # 상한 클램프 + 스케일
    v_max = node("get", (-620, 20), variable_name="HookSwingAlignMaxDeg")
    cap = fn("FMin", (-420, 100))
    link(acs, "ReturnValue", cap, "A")
    link(v_max, "HookSwingAlignMaxDeg", cap, "B")
    v_sc = node("get", (-420, 20), variable_name="HookSwingAlignScale")
    scaled = fn("Multiply_DoubleDouble", (-240, 100))
    link(cap, "ReturnValue", scaled, "A")
    link(v_sc, "HookSwingAlignScale", scaled, "B")

    # 게이트 = bHookIsSwing AND Phase==Moving
    v_sw = node("get", (-1040, -160), variable_name="bHookIsSwing")
    v_mv = node("get", (-1480, -60), variable_name="SBCharacterMovement")
    ph = node("call", (-1240, -60), function_name="GetHookshotPhase",
              target_class="SBCharacterMovementComponent")
    link(v_mv, "SBCharacterMovement", ph, "self")
    eq = fn("EqualEqual_ByteByte", (-1040, -60))
    link(ph, "ReturnValue", eq, "A")
    pin(eq, "B", PHASE_MOVING)
    gate = fn("BooleanAND", (-820, -100))
    link(eq, "ReturnValue", gate, "A")
    link(v_sw, "bHookIsSwing", gate, "B")

    # 경과시간 누적 (게이트 열린 동안만, 닫히면 0)
    v_el = node("get", (-820, 560), variable_name="HookSwingElapsed")
    acc = fn("Add_DoubleDouble", (-600, 580))
    link(v_el, "HookSwingElapsed", acc, "A")
    link(pa_dt, "Value", acc, "B")
    sel_el = fn("SelectFloat", (-380, 560))
    link(acc, "ReturnValue", sel_el, "A")
    pin(sel_el, "B", "0.0")
    link(gate, "ReturnValue", sel_el, "bPickA")
    set_el = node("set", (-120, 400), variable_name="HookSwingElapsed")
    link(E, "then", set_el, "execute")
    link(sel_el, "ReturnValue", set_el, "HookSwingElapsed")

    # t = Clamp(elapsed / max(Duration, 0.01), 0, 1)
    v_dur = node("get", (-120, 640), variable_name="HookSwingArcDuration")
    dur_safe = fn("FMax", (80, 660))
    link(v_dur, "HookSwingArcDuration", dur_safe, "A")
    pin(dur_safe, "B", "0.01")
    div = fn("Divide_DoubleDouble", (280, 560))
    link(set_el, "Output_Get", div, "A")
    link(dur_safe, "ReturnValue", div, "B")
    clp = fn("FClamp", (480, 560))
    link(div, "ReturnValue", clp, "Value")
    pin(clp, "Min", "0.0")
    pin(clp, "Max", "1.0")

    # profile = Sin(PI * t)  -> 0 에서 1 로 올랐다가 다시 0
    pit = fn("Multiply_DoubleDouble", (680, 560))
    link(clp, "ReturnValue", pit, "A")
    pin(pit, "B", "3.141593")
    sinp = fn("Sin", (880, 560))
    link(pit, "ReturnValue", sinp, "A")

    # target = scaled * profile, 게이트 닫히면 0
    prof = fn("Multiply_DoubleDouble", (1080, 300))
    link(scaled, "ReturnValue", prof, "A")
    link(sinp, "ReturnValue", prof, "B")
    sel = fn("SelectFloat", (1280, 260))
    link(prof, "ReturnValue", sel, "A")
    pin(sel, "B", "0.0")
    link(gate, "ReturnValue", sel, "bPickA")

    # 보간
    v_cur = node("get", (1280, 440), variable_name="HookSwingAlignAngle")
    v_spd = node("get", (1280, 520), variable_name="HookSwingAlignSpeed")
    itp = fn("FInterpTo", (1500, 340))
    link(v_cur, "HookSwingAlignAngle", itp, "Current")
    link(sel, "ReturnValue", itp, "Target")
    link(pa_dt, "Value", itp, "DeltaTime")
    link(v_spd, "HookSwingAlignSpeed", itp, "InterpSpeed")

    set_ang = node("set", (1760, 400), variable_name="HookSwingAlignAngle")
    link(set_el, "then", set_ang, "execute")
    link(itp, "ReturnValue", set_ang, "HookSwingAlignAngle")

    rot = fn("RotatorFromAxisAndAngle", (2000, 500))
    link(axn, "ReturnValue", rot, "Axis")
    link(set_ang, "Output_Get", rot, "Angle")

    set_rot = node("set", (2260, 400), variable_name="HookSwingAlignRot")
    link(set_ang, "then", set_rot, "execute")
    link(rot, "ReturnValue", set_rot, "HookSwingAlignRot")
    print("  wired %d nodes" % len(LOG))


def do_chain():
    s = summary("EventGraph")
    last = None
    for n in s["nodes"]:
        if "UpdateHookshotPhysics" in n.get("title", "").replace(" ", ""):
            last = n["id"]
    if not last:
        for n in s["nodes"]:
            if "Physics" in n.get("title", ""):
                last = n["id"]
    if not last:
        raise RuntimeError("체인 끝 노드를 못 찾음")
    out = call("add_node", {"asset_path": BP, "graph_name": "EventGraph", "node_type": "call",
                            "function_name": G, "position": [2600, 0]})
    nid = out.get("node_id") or out.get("id")
    call("connect_pins", {"asset_path": BP, "graph_name": "EventGraph",
                          "source_node": last, "source_pin": "then",
                          "target_node": nid, "target_pin": "execute"})
    print("  chained:", last, "->", nid)


def do_compile():
    o = call("compile_blueprint", {"asset_path": BP, "max_sibling_candidates": 0})
    print("  compile: success=%s errors=%s warnings=%s" %
          (o.get("success"), o.get("error_count"), o.get("warning_count")))


def do_save():
    o = call("save_packages", {"packages": [BP]}, tool="editor_query")
    print("  save:", o.get("ok"), o.get("saved"))


PHASES = {"vars": do_vars, "func": do_func, "copy": do_copy, "wire": do_wire,
          "chain": do_chain, "compile": do_compile, "save": do_save}

if __name__ == "__main__":
    ph = sys.argv[1] if len(sys.argv) > 1 else "all"
    order = (["vars", "func", "save", "copy", "wire", "save",
              "compile", "chain", "compile", "save"] if ph == "all" else [ph])
    for p in order:
        print("==", p)
        PHASES[p]()
