# CR 내부 팔 신전 클램프 (v5.8) — 이펙터 최종단, 현재프레임 어깨 기준 (지연 0)
# 이펙터' = 어깨 + ClampLength(이펙터 - 어깨, 0, MaxReach 42)
# ABP측 클램프(1프레임 지연)의 잔여 신전 스파이크를 근본 차단. 알파 상태 무관 상시 작동.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_reach_clamp.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
MAX_REACH = "42.000000"
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
            step("DEF " + pin)
        except Exception as e:
            step("DEF ERR " + pin + " : " + repr(e)[:100])

    def relink(a, b, brk=True):
        if brk:
            try:
                c.break_all_links(b, True)
                step("BREAK " + b)
            except Exception as e:
                step("BREAK ERR " + b + " : " + repr(e)[:80])
        try:
            ok = c.add_link(a, b)
            step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)
        except Exception as e:
            step("LINK ERR " + a + " -> " + b + " : " + repr(e)[:100])

    for side, sfx, lerp, make in (("l", "L", "RigVMFunction_MathVectorLerp", "RigVMFunction_MathTransformMake"),
                                  ("r", "R", "RigVMFunction_MathVectorLerp_1", "RigVMFunction_MathTransformMake_1")):
        sh = add_unit("/Script/ControlRig.RigUnit_GetTransform", "ReachShoulder" + sfx, (500, 1700 if sfx == "L" else 1850))
        setdef(sh + ".Item", '(Type=Bone,Name="upperarm_%s")' % side)
        setdef(sh + ".Space", "GlobalSpace")
        setdef(sh + ".bInitial", "False")
        sub = add_unit("/Script/RigVM.RigVMFunction_MathVectorSub", "ReachSub" + sfx, (650, 1700 if sfx == "L" else 1850))
        clp = add_unit("/Script/RigVM.RigVMFunction_MathVectorClampLength", "ReachClamp" + sfx, (800, 1700 if sfx == "L" else 1850))
        add = add_unit("/Script/RigVM.RigVMFunction_MathVectorAdd", "ReachAdd" + sfx, (950, 1700 if sfx == "L" else 1850))
        setdef(clp + ".MinimumLength", "0.000000")
        setdef(clp + ".MaximumLength", MAX_REACH)
        relink(lerp + ".Result", sub + ".A", brk=False)
        relink(sh + ".Transform.Translation", sub + ".B", brk=False)
        relink(sub + ".Result", clp + ".Value", brk=False)
        relink(sh + ".Transform.Translation", add + ".A", brk=False)
        relink(clp + ".Result", add + ".B", brk=False)
        relink(add + ".Result", make + ".Translation")

    bp.recompile_vm()
    step("recompiled")
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("CR_REACH_CLAMP_DONE")
