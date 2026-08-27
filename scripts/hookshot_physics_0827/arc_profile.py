# -*- coding: utf-8 -*-
"""스윙 정렬 각도를 종모양 곡선으로 교체 (2026-08-27)

승호 지시: "이동 처음부터 회전을 주지말고, 훅샷 이동중 처음부터 당겨지는 최정점까지
            0~최대각으로 꺾이고, 최대각에서 스윙을 푸는 순간까지 최대각->0 으로 스무스하게"

기존(로프 각도를 매 틱 그대로 추종) -> 진행도 기반 프로파일로 변경:

    t       = Clamp(HookSwingElapsed / max(HookSwingArcDuration, 0.01), 0, 1)
    profile = Sin(PI * t)                       # 0 -> 1 -> 0
    angle   = FMin(로프각, MaxDeg) * Scale * profile

축(꺾이는 방향)은 기존 그대로 로프 쪽. 크기만 곡선으로 준다.

🔴 remove_function 금지 — PropertyAccess 가 든 그래프를 삭제하면
   FindBlueprintForNodeChecked assert 로 에디터가 죽는다 (8/27 실측).
   그래서 기존 그래프를 유지한 채 노드 추가 + 재배선으로만 고친다.

phase: vars | wire | compile | save | all
"""
import json
import sys
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot"
G = "UpdateHookSwingAlign"
CAT = "Hookshot Swing Align"

# --- 기존 노드 (실측) ---------------------------------------------------
ENTRY = "K2Node_FunctionEntry_0"
ACOS = "K2Node_CallFunction_7"        # Acos (Degrees) -> 로프각
MUL_SCALE = "K2Node_CallFunction_8"   # float * float (angle * Scale)
GATE = "K2Node_CallFunction_11"       # AND Boolean  (bHookIsSwing AND Phase==Moving)
SEL = "K2Node_CallFunction_12"        # Select Float -> FInterpTo.Target
SET_ANGLE = "K2Node_VariableSet_0"    # Set HookSwingAlignAngle
PA_DELTA = "K2Node_PropertyAccess_10"  # DeltaTime

VARS = [
    ("HookSwingAlignMaxDeg", "float", "60.0"),
    ("HookSwingArcDuration", "float", "1.0"),
    ("HookSwingElapsed", "float", "0.0"),
]


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
        raise RuntimeError("%s: %s" % (action, t[:500]))
    try:
        return json.loads(t)
    except Exception:
        return {"raw": t}


def node(node_type, pos, **kw):
    a = {"asset_path": BP, "graph_name": G, "node_type": node_type, "position": list(pos)}
    a.update(kw)
    o = call("add_node", a)
    return o.get("node_id") or o.get("id")


def fn(name, pos):
    return node("call", pos, function_name=name, target_class="KismetMathLibrary")


def link(sn, sp, tn, tp):
    call("connect_pins", {"asset_path": BP, "graph_name": G, "source_node": sn,
                          "source_pin": sp, "target_node": tn, "target_pin": tp})


def unlink(sn, sp, tn, tp):
    try:
        call("disconnect_pins", {"asset_path": BP, "graph_name": G, "source_node": sn,
                                 "source_pin": sp, "target_node": tn, "target_pin": tp})
    except Exception as e:
        print("    (disconnect skip)", str(e)[:70])


def pin(nid, name, value):
    call("set_pin_default", {"asset_path": BP, "graph_name": G, "node_id": nid,
                             "pin_name": name, "value": str(value)})


def do_vars():
    have = {v.get("name") for v in (call("get_variables", {"asset_path": BP}).get("variables") or [])}
    for n, t, d in VARS:
        if n in have:
            print("  skip", n)
            continue
        call("add_variable", {"asset_path": BP, "name": n, "type": t,
                              "default_value": d, "category": CAT})
        print("  +var", n, t, d)


def do_wire():
    # 1) 로프각 상한 클램프:  Acos -> [FMin] -> MUL_SCALE.A
    v_max = node("get", (-700, -260), variable_name="HookSwingAlignMaxDeg")
    cap = fn("FMin", (-500, -300))
    unlink(ACOS, "ReturnValue", MUL_SCALE, "A")
    link(ACOS, "ReturnValue", cap, "A")
    link(v_max, "HookSwingAlignMaxDeg", cap, "B")
    link(cap, "ReturnValue", MUL_SCALE, "A")
    print("  1) 상한 클램프 삽입:", cap)

    # 2) 경과시간 누적 — 게이트 열린 동안만, 닫히면 0
    v_el = node("get", (-700, 700), variable_name="HookSwingElapsed")
    acc = fn("Add_DoubleDouble", (-480, 720))
    link(v_el, "HookSwingElapsed", acc, "A")
    link(PA_DELTA, "Value", acc, "B")
    sel_el = fn("SelectFloat", (-260, 700))
    link(acc, "ReturnValue", sel_el, "A")
    pin(sel_el, "B", "0.0")
    link(GATE, "ReturnValue", sel_el, "bPickA")
    set_el = node("set", (-40, 620), variable_name="HookSwingElapsed")
    link(sel_el, "ReturnValue", set_el, "HookSwingElapsed")
    print("  2) 경과시간 누적:", set_el)

    # exec: Entry -> SetElapsed -> SetAngle
    unlink(ENTRY, "then", SET_ANGLE, "execute")
    link(ENTRY, "then", set_el, "execute")
    link(set_el, "then", SET_ANGLE, "execute")
    print("  3) exec 재배선 완료")

    # 4) t = Clamp(elapsed / max(Duration,0.01), 0, 1)
    v_dur = node("get", (-40, 860), variable_name="HookSwingArcDuration")
    dur = fn("FMax", (180, 880))
    link(v_dur, "HookSwingArcDuration", dur, "A")
    pin(dur, "B", "0.01")
    div = fn("Divide_DoubleDouble", (400, 760))
    link(set_el, "Output_Get", div, "A")
    link(dur, "ReturnValue", div, "B")
    clp = fn("FClamp", (620, 760))
    link(div, "ReturnValue", clp, "Value")
    pin(clp, "Min", "0.0")
    pin(clp, "Max", "1.0")

    # 5) profile = Sin(PI * t)
    pit = fn("Multiply_DoubleDouble", (840, 760))
    link(clp, "ReturnValue", pit, "A")
    pin(pit, "B", "3.141593")
    sinp = fn("Sin", (1040, 760))
    link(pit, "ReturnValue", sinp, "A")
    print("  4) 곡선 산출:", sinp)

    # 6) angle * profile -> SelectFloat.A
    prof = fn("Multiply_DoubleDouble", (1260, 400))
    unlink(MUL_SCALE, "ReturnValue", SEL, "A")
    link(MUL_SCALE, "ReturnValue", prof, "A")
    link(sinp, "ReturnValue", prof, "B")
    link(prof, "ReturnValue", SEL, "A")
    print("  5) 프로파일 적용:", prof)


def do_compile():
    o = call("compile_blueprint", {"asset_path": BP, "max_sibling_candidates": 0})
    print("  compile: success=%s errors=%s warnings=%s"
          % (o.get("success"), o.get("error_count"), o.get("warning_count")))


def do_save():
    o = call("save_packages", {"packages": [BP]}, tool="editor_query")
    print("  save:", o.get("ok"), o.get("saved"))


PHASES = {"vars": do_vars, "wire": do_wire, "compile": do_compile, "save": do_save}

if __name__ == "__main__":
    ph = sys.argv[1] if len(sys.argv) > 1 else "all"
    for p in (["vars", "save", "wire", "compile", "save"] if ph == "all" else [ph]):
        print("==", p)
        PHASES[p]()
