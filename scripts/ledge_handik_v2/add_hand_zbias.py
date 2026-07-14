import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/hand_zbias.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {"steps": []}


def step(m):
    log["steps"].append(str(m))


try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()

    def add_unit(path, name, pos):
        n = c.add_unit_node_from_struct_path(path, "Execute", unreal.Vector2D(pos[0], pos[1]), name)
        if n is None:
            raise RuntimeError("add fail " + name)
        step("created " + name)
        return str(n.get_node_path())

    def setdef(pin, val):
        try:
            c.set_pin_default_value(pin, val, False)
            step("DEF " + pin + " = " + val)
        except Exception as e:
            step("DEF ERR " + pin + " : " + repr(e)[:100])

    def link(a, b):
        try:
            ok = c.add_link(a, b)
            step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)
        except Exception as e:
            step("LINK ERR " + a + " -> " + b + " : " + repr(e)[:100])

    def brk(a, b):
        try:
            c.break_link(a, b)
            step("BREAK " + a + " -> " + b)
        except Exception as e:
            step("BREAK ERR " + repr(e)[:80])

    sbL = add_unit("/Script/RigVM.RigVMFunction_MathVectorSub", "HandZBiasL", (400, 1100))
    sbR = add_unit("/Script/RigVM.RigVMFunction_MathVectorSub", "HandZBiasR", (400, 1400))
    # A <- LatchToWorld 결과, B = (0,0,Bias) — 기본 0 (유저 캡슐 인상량과 세트로 설정)
    brk("LatchToWorldL.Result", "LatchSelL.IfTrue")
    brk("LatchToWorldR.Result", "LatchSelR.IfTrue")
    link("LatchToWorldL.Result", sbL + ".A")
    link("LatchToWorldR.Result", sbR + ".A")
    setdef(sbL + ".B", "(X=0.0,Y=0.0,Z=0.0)")
    setdef(sbR + ".B", "(X=0.0,Y=0.0,Z=0.0)")
    link(sbL + ".Result", "LatchSelL.IfTrue")
    link(sbR + ".Result", "LatchSelR.IfTrue")

    bp.recompile_vm()
    step("recompiled")
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("ZBIAS_DONE")
