# -*- coding: utf-8 -*-
"""훅샷 이동 시작 시 정면(Yaw)을 이동 방향으로 정렬 (2026-08-27)

승호 지시: "이동을 할때 후진을 하는경우가 있어. 이동을 시작하면서 캐릭터를 이동방향으로
            정면을 조게 수정해줘"

- 목표 Yaw 는 **Moving 진입 첫 틱에 1회 래치**한다. 스윙은 진자라 매 틱 재판정하면
  방향이 뒤집힌다([[project-hookshot-swing-0826]] LandDir 래치와 같은 이유).
- delta 는 매 틱 재계산 → C++ 이 액터 Yaw 를 돌려도 메시는 래치된 방향을 유지한다.
- 시각만: ModifyBone(root) 에 들어가는 로테이터에 합성. 캡슐·카메라·C++ 회전 불변.
- 랩(±180) 안전을 위해 float 보간이 아니라 **RInterpTo(로테이터 최단경로)** 를 쓴다.

    gateYaw = (Phase==Moving) AND bHookMoveYawEnable
    래치     : gateYaw AND NOT latched -> HookMoveYawTarget = Yaw(Target − CharLoc)
    해제     : NOT gateYaw -> latched = false
    delta    = NormalizeAxis(HookMoveYawTarget − 현재 액터 Yaw)
    HookMoveYawRot = RInterpTo(cur, MakeRotator(0,0,gateYaw?delta:0), dt, HookMoveYawSpeed)
    최종      = ComposeRotators(HookMoveYawRot, 기존 스윙정렬Rot) -> HookSwingAlignRot

🔴 remove_function 금지 (PropertyAccess 든 그래프 삭제 = 에디터 assert 크래시).

phase: vars | wire | compile | save | all
"""
import json
import sys
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot"
G = "UpdateHookSwingAlign"
CAT = "Hookshot Move Yaw"

# --- 기존 노드 (실측) ---------------------------------------------------
EQ_MOVING = "K2Node_CallFunction_10"   # Equal(Byte): Phase == Moving
SUB_VEC = "K2Node_CallFunction_1"      # Target − CharLoc (3D)
BRK_XFORM = "K2Node_CallFunction_0"    # Break Transform (Rotation 핀 미사용)
PA_DELTA = "K2Node_PropertyAccess_10"  # DeltaTime
SET_ANGLE = "K2Node_VariableSet_0"     # Set HookSwingAlignAngle (exec 상류)
SET_ROT = "K2Node_VariableSet_1"       # Set HookSwingAlignRot   (exec 말단)
ALIGN_ROT = "K2Node_CallFunction_14"   # RotatorFromAxisAndAngle -> SET_ROT

VARS = [
    ("bHookMoveYawEnable", "bool", "true"),
    ("HookMoveYawTarget", "float", "0.0"),
    ("bHookMoveYawLatched", "bool", "false"),
    ("HookMoveYawRot", "struct:Rotator", ""),
    ("HookMoveYawSpeed", "float", "6.0"),
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
        a = {"asset_path": BP, "name": n, "type": t, "category": CAT}
        if d:
            a["default_value"] = d
        call("add_variable", a)
        print("  +var", n, t, d)


def do_wire():
    Y = 1600  # 신규 노드 배치 기준 Y

    # --- 게이트: Phase==Moving AND bHookMoveYawEnable ---------------------
    v_en = node("get", (-900, Y - 200), variable_name="bHookMoveYawEnable")
    gate = fn("BooleanAND", (-700, Y - 240))
    link(EQ_MOVING, "ReturnValue", gate, "A")
    link(v_en, "bHookMoveYawEnable", gate, "B")
    print("  gate:", gate)

    # --- 이동 방향 Yaw (Target − CharLoc) --------------------------------
    dir_rot = fn("Conv_VectorToRotator", (-700, Y))
    link(SUB_VEC, "ReturnValue", dir_rot, "InVec")
    brk_dir = fn("BreakRotator", (-500, Y))
    link(dir_rot, "ReturnValue", brk_dir, "InRot")

    # --- 현재 액터 Yaw ----------------------------------------------------
    brk_cur = fn("BreakRotator", (-500, Y + 180))
    link(BRK_XFORM, "Rotation", brk_cur, "InRot")

    # --- 래치 (Moving 첫 틱 1회) -----------------------------------------
    not_l = fn("Not_PreBool", (-300, Y - 120))
    v_l = node("get", (-500, Y - 120), variable_name="bHookMoveYawLatched")
    link(v_l, "bHookMoveYawLatched", not_l, "A")
    need = fn("BooleanAND", (-120, Y - 160))
    link(gate, "ReturnValue", need, "A")
    link(not_l, "ReturnValue", need, "B")

    br_need = node("Branch", (120, Y - 200))
    set_tgt = node("set", (360, Y - 260), variable_name="HookMoveYawTarget")
    set_on = node("set", (620, Y - 260), variable_name="bHookMoveYawLatched")
    pin(set_on, "bHookMoveYawLatched", "true")
    link(need, "ReturnValue", br_need, "Condition")
    link(br_need, "then", set_tgt, "execute")
    link(brk_dir, "Yaw", set_tgt, "HookMoveYawTarget")
    link(set_tgt, "then", set_on, "execute")

    # 게이트가 닫히면 래치 해제
    br_gate = node("Branch", (120, Y + 60))
    set_off = node("set", (360, Y + 120), variable_name="bHookMoveYawLatched")
    pin(set_off, "bHookMoveYawLatched", "false")
    link(gate, "ReturnValue", br_gate, "Condition")
    link(br_gate, "else", set_off, "execute")
    print("  래치:", set_tgt, "/ 해제:", set_off)

    # exec: SetAngle -> br_need -(else)-> br_gate -> ... -> SetYawRot -> SetRot
    unlink(SET_ANGLE, "then", SET_ROT, "execute")
    link(SET_ANGLE, "then", br_need, "execute")
    link(br_need, "else", br_gate, "execute")
    link(set_on, "then", br_gate, "execute")

    # --- delta = NormalizeAxis(target − 현재 Yaw) -------------------------
    v_tgt = node("get", (-120, Y + 300), variable_name="HookMoveYawTarget")
    sub = fn("Subtract_DoubleDouble", (120, Y + 320))
    link(v_tgt, "HookMoveYawTarget", sub, "A")
    link(brk_cur, "Yaw", sub, "B")
    norm = fn("NormalizeAxis", (340, Y + 320))
    link(sub, "ReturnValue", norm, "A")

    sel = fn("SelectFloat", (560, Y + 320))
    link(norm, "ReturnValue", sel, "A")
    pin(sel, "B", "0.0")
    link(gate, "ReturnValue", sel, "bPickA")

    mk = fn("MakeRotator", (780, Y + 320))
    pin(mk, "Roll", "0.0")
    pin(mk, "Pitch", "0.0")
    link(sel, "ReturnValue", mk, "Yaw")

    # --- RInterpTo (랩 안전) ---------------------------------------------
    v_cur = node("get", (780, Y + 520), variable_name="HookMoveYawRot")
    v_spd = node("get", (780, Y + 600), variable_name="HookMoveYawSpeed")
    rint = fn("RInterpTo", (1020, Y + 400))
    link(v_cur, "HookMoveYawRot", rint, "Current")
    link(mk, "ReturnValue", rint, "Target")
    link(PA_DELTA, "Value", rint, "DeltaTime")
    link(v_spd, "HookMoveYawSpeed", rint, "InterpSpeed")

    set_yaw = node("set", (1280, Y + 60), variable_name="HookMoveYawRot")
    link(rint, "ReturnValue", set_yaw, "HookMoveYawRot")
    link(br_gate, "then", set_yaw, "execute")
    link(set_off, "then", set_yaw, "execute")
    print("  보간:", set_yaw)

    # --- 최종 합성: Yaw 먼저, 그다음 스윙 기울기 --------------------------
    comp = fn("ComposeRotators", (1540, Y + 200))
    link(set_yaw, "Output_Get", comp, "A")
    link(ALIGN_ROT, "ReturnValue", comp, "B")
    unlink(ALIGN_ROT, "ReturnValue", SET_ROT, "HookSwingAlignRot")
    link(comp, "ReturnValue", SET_ROT, "HookSwingAlignRot")
    link(set_yaw, "then", SET_ROT, "execute")
    print("  합성:", comp)


def do_compile():
    o = call("compile_blueprint", {"asset_path": BP, "max_sibling_candidates": 0})
    print("  compile: success=%s errors=%s warnings=%s"
          % (o.get("success"), o.get("error_count"), o.get("warning_count")))
    for g in o.get("error_groups", [])[:6]:
        if "visible but ignored" in g.get("message", ""):
            continue
        print("   *", g.get("message", "")[:120])


def do_save():
    print("  save:", call("save_packages", {"packages": [BP]}, tool="editor_query").get("ok"))


PHASES = {"vars": do_vars, "wire": do_wire, "compile": do_compile, "save": do_save}

if __name__ == "__main__":
    ph = sys.argv[1] if len(sys.argv) > 1 else "all"
    for p in (["vars", "save", "wire", "compile", "save"] if ph == "all" else [ph]):
        print("==", p)
        PHASES[p]()
