# -*- coding: utf-8 -*-
"""훅샷 피직스 BP 배선 (2026-08-27)

레이어: PC_01_AnimLayer_Hookshot
신규 함수 UpdateHookshotPhysics 를 EventGraph 체인(UpdateHookshotMontage 뒤)에 연결.

구조 (렛지 PC_01_AnimLayer_Ledge 패턴 복제):
  wanted = bHookPhysEnable AND (GetHookshotPhase() == Moving[3])
  Sequence
    then_0 [엣지] Branch(wanted != bHookPhysProfileOn)
             then -> Branch(wanted)
                       then -> EnableProfile("HookshotAir", BlendIn, BlendOut)
                       else -> EnableProfile("Kinematic", 0.3, 0.0) -> DisableProfile()
                     -> Set bHookPhysProfileOn = wanted
    then_1 [매틱] Branch(wanted)
             then -> SetControlAngularData x3 (Spine / LegLeft / LegRight)

게임스레드 전용 (물리 컴포넌트 조작) — thread-safe 로 만들지 않는다.

phase: vars | func | wire | chain | compile | all
"""
import json
import sys
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot"
G = "UpdateHookshotPhysics"
CAT = "Hookshot Physics"
PHASE_MOVING = "3"   # ESBHookshotPhase: None0 Casting1 PendingStart2 Moving3 PendingEnd4

VARS = [
    ("bHookPhysEnable",       "bool",  "true"),
    ("bHookPhysProfileOn",    "bool",  "false"),
    ("HookPhysSpineStrength", "float", "6.0"),
    ("HookPhysLegStrength",   "float", "3.0"),
    ("HookPhysDampingRatio",  "float", "1.5"),
    ("HookPhysExtraDamping",  "float", "0.5"),
    ("HookPhysBlendIn",       "float", "0.4"),
    ("HookPhysBlendOut",      "float", "0.3"),
]

LOG = []


def call(action, args, tool="blueprint_query", timeout=180):
    args = dict(args)
    args["action"] = action
    b = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
         "params": {"name": tool, "arguments": args}}
    r = json.load(urllib.request.urlopen(
        urllib.request.Request(MCP, json.dumps(b).encode(),
                               {"Content-Type": "application/json"}), timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError("%s: %s" % (action, txt[:600]))
    try:
        return json.loads(txt)
    except Exception:
        return {"raw": txt}


def node(node_type, pos, **kw):
    a = {"asset_path": BP, "graph_name": G, "node_type": node_type, "position": list(pos)}
    a.update(kw)
    out = call("add_node", a)
    nid = out.get("node_id") or out.get("id")
    if not nid:
        raise RuntimeError("no node_id: %s" % json.dumps(out)[:300])
    LOG.append((node_type, kw.get("function_name") or kw.get("variable_name") or "", nid))
    return nid


def link(sn, sp, tn, tp):
    call("connect_pins", {"asset_path": BP, "graph_name": G,
                          "source_node": sn, "source_pin": sp,
                          "target_node": tn, "target_pin": tp})


def pin(nid, name, value):
    call("set_pin_default", {"asset_path": BP, "graph_name": G,
                             "node_id": nid, "pin_name": name, "value": str(value)})


def do_vars():
    got = call("get_variables", {"asset_path": BP})
    have = set()
    for v in (got.get("variables") or []):
        have.add(v.get("name"))
    for n, t, d in VARS:
        if n in have:
            print("  skip(exists)", n)
            continue
        call("add_variable", {"asset_path": BP, "name": n, "type": t,
                              "default_value": d, "category": CAT})
        print("  +var", n, t, d)


def do_func():
    fns = call("get_functions", {"asset_path": BP})
    names = set()
    for f in (fns.get("functions") or fns.get("graphs") or []):
        names.add(f.get("name") if isinstance(f, dict) else f)
    if G in names:
        print("  skip(exists)", G)
        return
    call("add_function", {"asset_path": BP, "name": G, "category": CAT,
                          "description": "훅샷 Moving 구간 피직스 프로파일 on/off + 컨트롤 세기 갱신 (게임스레드)"})
    print("  +func", G)


def entry_id():
    s = call("get_graph_summary", {"asset_path": BP, "graph_name": G})
    for n in s["nodes"]:
        if n["class"] == "K2Node_FunctionEntry":
            return n["id"]
    raise RuntimeError("no FunctionEntry in %s" % G)


def do_wire():
    E = entry_id()
    print("  entry:", E)

    # ---- 순수 입력 ------------------------------------------------------
    v_char = node("get", (-1400, 480), variable_name="As SBCharacter")
    n_feat = node("call", (-1150, 480), function_name="GetPhysicsFeature",
                  target_class="SBCharacter")
    link(v_char, "As SBCharacter", n_feat, "self")

    n_pcc = node("call", (-900, 560), function_name="GetPhysicsControlComponent",
                 target_class="SBCharacterPhysicsFeature")
    link(n_feat, "ReturnValue", n_pcc, "self")

    v_move = node("get", (-1400, 180), variable_name="SBCharacterMovement")
    n_phase = node("call", (-1150, 180), function_name="GetHookshotPhase",
                   target_class="SBCharacterMovementComponent")
    link(v_move, "SBCharacterMovement", n_phase, "self")

    n_eq = node("call", (-900, 180), function_name="EqualEqual_ByteByte",
                target_class="KismetMathLibrary")
    link(n_phase, "ReturnValue", n_eq, "A")
    pin(n_eq, "B", PHASE_MOVING)

    v_en = node("get", (-900, 300), variable_name="bHookPhysEnable")
    n_and = node("call", (-680, 200), function_name="BooleanAND",
                 target_class="KismetMathLibrary")
    link(n_eq, "ReturnValue", n_and, "A")
    link(v_en, "bHookPhysEnable", n_and, "B")           # = wanted

    v_on = node("get", (-680, 330), variable_name="bHookPhysProfileOn")
    n_neq = node("call", (-460, 260), function_name="NotEqual_BoolBool",
                 target_class="KismetMathLibrary")
    link(n_and, "ReturnValue", n_neq, "A")
    link(v_on, "bHookPhysProfileOn", n_neq, "B")        # = changed

    v_bin = node("get", (-460, 700), variable_name="HookPhysBlendIn")
    v_bout = node("get", (-460, 780), variable_name="HookPhysBlendOut")
    v_sstr = node("get", (-460, 980), variable_name="HookPhysSpineStrength")
    v_lstr = node("get", (-460, 1060), variable_name="HookPhysLegStrength")
    v_damp = node("get", (-460, 1140), variable_name="HookPhysDampingRatio")
    v_extr = node("get", (-460, 1220), variable_name="HookPhysExtraDamping")

    # ---- exec ------------------------------------------------------------
    n_seq = node("ExecutionSequence", (-200, 0))
    link(E, "then", n_seq, "execute")

    n_br_ch = node("Branch", (60, 0))
    link(n_seq, "then_0", n_br_ch, "execute")
    link(n_neq, "ReturnValue", n_br_ch, "Condition")

    n_br_w = node("Branch", (300, 0))
    link(n_br_ch, "then", n_br_w, "execute")
    link(n_and, "ReturnValue", n_br_w, "Condition")

    n_en_hook = node("call", (560, -80), function_name="EnableProfile",
                     target_class="SBCharacterPhysicsFeature")
    link(n_br_w, "then", n_en_hook, "execute")
    link(n_feat, "ReturnValue", n_en_hook, "self")
    pin(n_en_hook, "InProfileName", "HookshotAir")
    link(v_bin, "HookPhysBlendIn", n_en_hook, "InBlendInTime")
    link(v_bout, "HookPhysBlendOut", n_en_hook, "InBlendOutTime")

    n_en_kin = node("call", (560, 220), function_name="EnableProfile",
                    target_class="SBCharacterPhysicsFeature")
    link(n_br_w, "else", n_en_kin, "execute")
    link(n_feat, "ReturnValue", n_en_kin, "self")
    pin(n_en_kin, "InProfileName", "Kinematic")
    pin(n_en_kin, "InBlendInTime", "0.3")
    pin(n_en_kin, "InBlendOutTime", "0.0")

    n_dis = node("call", (860, 220), function_name="DisableProfile",
                 target_class="SBCharacterPhysicsFeature")
    link(n_en_kin, "then", n_dis, "execute")
    link(n_feat, "ReturnValue", n_dis, "self")

    n_set_on = node("set", (1160, 40), variable_name="bHookPhysProfileOn")
    link(n_en_hook, "then", n_set_on, "execute")
    link(n_dis, "then", n_set_on, "execute")
    link(n_and, "ReturnValue", n_set_on, "bHookPhysProfileOn")

    n_br_t = node("Branch", (60, 900))
    link(n_seq, "then_1", n_br_t, "execute")
    link(n_and, "ReturnValue", n_br_t, "Condition")

    ctrls = [("ParentSpace_Spine", v_sstr, "HookPhysSpineStrength", 900),
             ("ParentSpace_LegLeft", v_lstr, "HookPhysLegStrength", 1120),
             ("ParentSpace_LegRight", v_lstr, "HookPhysLegStrength", 1340)]
    prev, prev_pin = n_br_t, "then"
    for name, vnode, vpin, y in ctrls:
        nid = node("call", (420, y), function_name="SetControlAngularData",
                   target_class="PhysicsControlComponent")
        link(prev, prev_pin, nid, "execute")
        link(n_pcc, "ReturnValue", nid, "self")
        pin(nid, "Name", name)
        link(vnode, vpin, nid, "Strength")
        link(v_damp, "HookPhysDampingRatio", nid, "DampingRatio")
        link(v_extr, "HookPhysExtraDamping", nid, "ExtraDamping")
        pin(nid, "MaxTorque", "0.0")
        pin(nid, "bEnableControl", "true")
        pin(nid, "bApplyToControlsWithName", "false")
        pin(nid, "bApplyToSetsWithName", "false")
        prev, prev_pin = nid, "then"
    print("  wired %d nodes" % len(LOG))


def do_chain():
    s = call("get_graph_summary", {"asset_path": BP, "graph_name": "EventGraph"})
    montage = None
    for n in s["nodes"]:
        if "UpdateHookshotMontage" in n.get("title", ""):
            montage = n["id"]
    if not montage:
        raise RuntimeError("UpdateHookshotMontage node not found")
    out = call("add_node", {"asset_path": BP, "graph_name": "EventGraph", "node_type": "call",
                            "function_name": G,
                            "position": [2200, 0]})
    nid = out.get("node_id") or out.get("id")
    call("connect_pins", {"asset_path": BP, "graph_name": "EventGraph",
                          "source_node": montage, "source_pin": "then",
                          "target_node": nid, "target_pin": "execute"})
    print("  chained:", montage, "->", nid)


def do_compile():
    out = call("compile_blueprint", {"asset_path": BP})
    print("  compile:", json.dumps(out, ensure_ascii=False)[:500])


def do_save():
    out = call("save_packages", {"packages": [BP]}, tool="editor_query", timeout=300)
    print("  save:", json.dumps(out, ensure_ascii=False)[:300])


PHASES = {"vars": do_vars, "func": do_func, "wire": do_wire,
          "chain": do_chain, "compile": do_compile, "save": do_save}

if __name__ == "__main__":
    ph = sys.argv[1] if len(sys.argv) > 1 else "all"
    order = (["vars", "func", "save", "wire", "save", "compile",
              "chain", "compile", "save"] if ph == "all" else [ph])
    for p in order:
        print("==", p)
        PHASES[p]()
