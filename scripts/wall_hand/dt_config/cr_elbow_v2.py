# -*- coding: utf-8 -*-
"""CR ElbowAngle 재건 v2 (7/7): 변수 public 생성 + Y-Z 평면 폴 체인 (0,-sin,cos) 양손 공통.
7/6 교훈 반영: private→public 재수정 불필요하게 처음부터 public, VariableGet 대신 bind_pin_to_variable,
recompile_vm 명시. 0.02 rad(≈1.1°) = 구 폴 (∓50,0,1) 등가."""
import unreal, traceback

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/cr_elbow_v2.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L = []


def step(s):
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


try:
    bp = unreal.load_asset(DST)
    try:
        ok = bp.add_member_variable("ElbowAngle", "double", True, False, "0.02")
        step(f"add var ElbowAngle(public) -> {ok}")
    except Exception as e:
        step(f"add var FAIL {str(e)[:100]}")

    ctrl = bp.get_controller_by_name("RigVMModel")

    def U(s, x, y, nm):
        n = ctrl.add_unit_node_from_struct_path(s, "Execute", unreal.Vector2D(x, y), nm)
        step(f"add {nm} -> {n.get_node_path() if n else 'NONE'}")
        return n

    def sp(p, v):
        ok = ctrl.set_pin_default_value(p, v, False)
        step(f"{'sp' if ok else 'SP-FALSE'} {p}={v}")

    def lk(a, b):
        try:
            ok = ctrl.add_link(a, b)
            step(f"{'lk' if ok else 'LK-FALSE'} {a}->{b}")
        except Exception as e:
            step(f"LK-ERR {a}->{b} {str(e)[:60]}")

    SIN = "/Script/RigVM.RigVMFunction_MathDoubleSin"
    COS = "/Script/RigVM.RigVMFunction_MathDoubleCos"
    MUL = "/Script/RigVM.RigVMFunction_MathDoubleMul"
    VMK = "/Script/RigVM.RigVMFunction_MathVectorMake"

    U(SIN, 1200, -260, "ElbSin")
    U(COS, 1200, -140, "ElbCos")
    U(MUL, 1360, -260, "ElbNeg")
    sp("ElbNeg.B", "-1.000000")
    U(VMK, 1520, -260, "ElbDirR")
    U(VMK, 1520, -110, "ElbDirL")
    sp("ElbDirR.X", "0.000000")
    sp("ElbDirL.X", "0.000000")

    for pin in ("ElbSin.Value", "ElbCos.Value"):
        try:
            ok = ctrl.bind_pin_to_variable(pin, "ElbowAngle", False)
            step(f"{'bind' if ok else 'BIND-FALSE'} {pin}")
        except Exception as e:
            step(f"BIND-ERR {pin} {str(e)[:70]}")

    lk("ElbSin.Result", "ElbNeg.A")
    lk("ElbNeg.Result", "ElbDirR.Y")
    lk("ElbNeg.Result", "ElbDirL.Y")
    lk("ElbCos.Result", "ElbDirR.Z")
    lk("ElbCos.Result", "ElbDirL.Z")
    lk("ElbDirR.Result", "TwoBoneIK_R.PoleVector")
    lk("ElbDirL.Result", "TwoBoneIK_L.PoleVector")

    try:
        bp.recompile_vm()
        step("recompile_vm OK")
    except Exception as e:
        step(f"recompile_vm FAIL {str(e)[:80]}")
    ok = unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    step(f"saved {ok}")
except Exception:
    step("FATAL\n" + traceback.format_exc())
