# CR 손 IK 디버그 기즈모 — 포즈 평가 시점 드로우 (지연 0)
#  DebugTransformMutable x2: 솔브 후 hand_l/r 글로벌 트랜스폼에 축 기즈모
#  색 = MathColorLerp(어두움, 밝음, HandPinAlpha) — L=시안, R=마젠타
#  exec: FootIKR 뒤 체인 꼬리에 부착. 롤백 = DbgHandL/R + HandDbgT/Clr 노드 삭제
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_debug_gizmo.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
ALPHA_GET = {"L": "VariableNode_4", "R": "VariableNode_3"}  # Get HandPinAlphaL / R
COLORS = {"L": ("(R=0.0,G=0.12,B=0.12,A=1.0)", "(R=0.0,G=1.0,B=1.0,A=1.0)"),
          "R": ("(R=0.12,G=0.0,B=0.12,A=1.0)", "(R=1.0,G=0.0,B=1.0,A=1.0)")}
log = {"steps": []}


def step(m):
    log["steps"].append(str(m))


try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()
    existing = {str(n.get_node_path()) for n in g.get_nodes()}

    def add_unit(path, name, pos):
        if name in existing:
            step("reuse " + name)
            return name
        n = c.add_unit_node_from_struct_path(path, "Execute", unreal.Vector2D(pos[0], pos[1]), name)
        if n is None:
            raise RuntimeError("add fail " + name + " (" + path + ")")
        step("created " + name + " pins=" + ",".join(str(p.get_name()) for p in n.get_pins()))
        return str(n.get_node_path())

    def setdef(pin, val):
        try:
            c.set_pin_default_value(pin, val, False)
        except Exception as e:
            step("DEF ERR " + pin + " : " + repr(e)[:80])

    def link(a, b, brk=False):
        if brk:
            try:
                c.break_all_links(b, True)
            except Exception:
                pass
        ok = c.add_link(a, b)
        step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)
        if not ok:
            raise RuntimeError("link fail " + a + " -> " + b)

    prev_exec = "FootIKR.ExecutePin"
    for s, sock in (("L", "hand_l"), ("R", "hand_r")):
        y = 3000 if s == "L" else 3250
        gt = add_unit("/Script/ControlRig.RigUnit_GetTransform", "HandDbgT" + s, (1300, y))
        setdef(gt + ".Item", '(Type=Bone,Name="%s")' % sock)
        setdef(gt + ".Space", "GlobalSpace")
        setdef(gt + ".bInitial", "False")
        try:
            clr = add_unit("/Script/RigVM.RigVMFunction_MathColorLerp", "HandDbgClr" + s, (1450, y + 90))
            setdef(clr + ".A", COLORS[s][0])
            setdef(clr + ".B", COLORS[s][1])
            link(ALPHA_GET[s] + ".Value", clr + ".T")
            clr_out = clr + ".Result"
        except Exception as e:
            step("colorlerp fallback " + repr(e)[:100])
            clr_out = None
        dbg = add_unit("/Script/ControlRig.RigUnit_DebugTransformMutable", "DbgHand" + s, (1650, y))
        link(gt + ".Transform", dbg + ".Transform")
        if clr_out:
            link(clr_out, dbg + ".Color")
        else:
            setdef(dbg + ".Color", COLORS[s][1])
        setdef(dbg + ".Scale", "8.0")
        setdef(dbg + ".Thickness", "1.5")
        setdef(dbg + ".Mode", "Axes")
        link(prev_exec, dbg + ".ExecutePin")
        prev_exec = dbg + ".ExecutePin"

    bp.recompile_vm()
    step("recompiled")
    log["saved"] = bool(unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False))
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("CR_DEBUG_GIZMO_DONE")
