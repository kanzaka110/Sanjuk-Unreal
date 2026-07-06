# -*- coding: utf-8 -*-
"""CR: ElbowAngle(rad) 변수 + 폴 방향 계산 (R=(-cos,0,sin), L=(+cos,0,sin))"""
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/cr_elbow.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L = []
def step(s):
    L.append(str(s)); open(OUT, "w", encoding="utf-8").write("\n".join(L))
try:
    bp = unreal.load_asset(DST)
    # 1) 멤버 변수
    try:
        ok = bp.add_member_variable("ElbowAngle", "double", False, False, "0.02")
        step(f"add var ElbowAngle → {ok}")
    except Exception as e:
        step(f"add var FAIL {str(e)[:80]}")
    ctrl = bp.get_controller_by_name("RigVMModel")
    def U(s, x, y, nm):
        n = ctrl.add_unit_node_from_struct_path(s, "Execute", unreal.Vector2D(x, y), nm)
        step(f"add {nm} → {n.get_node_path() if n else None}")
        return n
    def sp(p, v):
        ok = ctrl.set_pin_default_value(p, v, False)
        step(f"{'sp' if ok else 'SP FALSE'} {p}={v}")
    def lk(a, b):
        try:
            ok = ctrl.add_link(a, b)
            step(f"{'lk' if ok else 'LKFALSE'} {a}->{b}")
        except Exception as e:
            step(f"LK ERR {a}->{b} {str(e)[:50]}")
    COS = "/Script/RigVM.RigVMFunction_MathDoubleCos"
    SIN = "/Script/RigVM.RigVMFunction_MathDoubleSin"
    MUL = "/Script/RigVM.RigVMFunction_MathDoubleMul"
    VMK = "/Script/RigVM.RigVMFunction_MathVectorMake"
    U(COS, 1200, -300, "ElbCos"); U(SIN, 1200, -200, "ElbSin")
    U(MUL, 1350, -300, "ElbNeg"); sp("ElbNeg.B", "-1.000000")
    U(VMK, 1500, -300, "ElbDirR"); U(VMK, 1500, -150, "ElbDirL")
    sp("ElbDirR.Y", "0.000000"); sp("ElbDirL.Y", "0.000000")
    # 변수 바인딩 (VariableGet 함정 회피)
    for pin in ("ElbCos.Value", "ElbSin.Value"):
        try:
            ok = ctrl.bind_pin_to_variable(pin, "ElbowAngle", False)
            step(f"{'bind' if ok else 'BIND FALSE'} {pin}")
        except Exception as e:
            step(f"BIND ERR {pin} {str(e)[:60]}")
    lk("ElbCos.Result", "ElbNeg.A")
    lk("ElbNeg.Result", "ElbDirR.X")
    lk("ElbSin.Result", "ElbDirR.Z")
    lk("ElbCos.Result", "ElbDirL.X")
    lk("ElbSin.Result", "ElbDirL.Z")
    lk("ElbDirR.Result", "TwoBoneIK_R.PoleVector")
    lk("ElbDirL.Result", "TwoBoneIK_L.PoleVector")
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    step("saved")
except Exception:
    step("FATAL\n" + traceback.format_exc())
