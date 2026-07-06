# -*- coding: utf-8 -*-
"""플랜B: 포스트-IK 팔꿈치 궤도. 상완을 어깨→손 축 둘레로 회전(손 위치 보존), 손 회전은 역쿼터니언 복원.
angle = ElbowAngle(rad) × IK weight (미부착 시 0 = 무영향). 구 폴 체인 제거+폴 디폴트 원복."""
import unreal, traceback

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/cr_elbow_orbit.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
GETXF = "/Script/ControlRig.RigUnit_GetTransform"
VSUB = "/Script/RigVM.RigVMFunction_MathVectorSub"
VUNIT = "/Script/RigVM.RigVMFunction_MathVectorUnit"
QAXIS = "/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle"
QINV = "/Script/RigVM.RigVMFunction_MathQuaternionInverse"
DMUL = "/Script/RigVM.RigVMFunction_MathDoubleMul"
OFF = "/Script/ControlRig.RigUnit_OffsetTransformForItem"
L = []

def step(s):
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))

try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")

    def U(s, x, y, nm):
        n = ctrl.add_unit_node_from_struct_path(s, "Execute", unreal.Vector2D(x, y), nm)
        step(f"add {nm} → {'OK' if n else 'FAIL'}")
        return n

    def sp(p, v):
        ok = ctrl.set_pin_default_value(p, v, False)
        step(f"{'sp' if ok else 'SP FALSE'} {p}")

    def lk(a, b):
        try:
            ok = ctrl.add_link(a, b)
            step(f"{'lk' if ok else 'LKFALSE'} {a}->{b}")
        except Exception as e:
            step(f"LK ERR {a}->{b} {str(e)[:50]}")

    def brk(a, b):
        try:
            ok = ctrl.break_link(a, b)
            step(f"brk {a} {ok}")
        except Exception as e:
            step(f"brk ERR {str(e)[:40]}")

    # ── 1) 구 폴 체인 정리 + 폴 디폴트 원복
    brk("ElbDirR.Result", "TwoBoneIK_R.PoleVector")
    brk("ElbDirL.Result", "TwoBoneIK_L.PoleVector")
    for nm in ("ElbCos", "ElbSin", "ElbNeg", "ElbDirR", "ElbDirL", "VariableNode_6", "VariableNode_9"):
        try:
            ctrl.remove_node_by_name(nm)
            step(f"rm {nm}")
        except Exception as e:
            step(f"rm {nm} err {str(e)[:40]}")
    sp("TwoBoneIK_R.PoleVector", "(X=-50.000000,Y=0.000000,Z=1.000000)")
    sp("TwoBoneIK_L.PoleVector", "(X=50.000000,Y=0.000000,Z=1.000000)")

    # ── 2) 궤도 체인 (손별)
    for side, UA, HA, WI, X0 in (("R", "upperarm_r", "hand_r", "WInterpR", 1200),
                                 ("L", "upperarm_l", "hand_l", "WInterpL", 1200)):
        y = -300 if side == "R" else 100
        U(GETXF, X0, y, f"OrbSh{side}")
        sp(f"OrbSh{side}.Item", f'(Type=Bone,Name="{UA}")')
        sp(f"OrbSh{side}.Space", "GlobalSpace")
        U(GETXF, X0, y + 80, f"OrbHa{side}")
        sp(f"OrbHa{side}.Item", f'(Type=Bone,Name="{HA}")')
        sp(f"OrbHa{side}.Space", "GlobalSpace")
        U(VSUB, X0 + 150, y, f"OrbSub{side}")
        U(VUNIT, X0 + 280, y, f"OrbAx{side}")
        U(DMUL, X0 + 280, y + 100, f"OrbAng{side}")
        U(QAXIS, X0 + 420, y, f"OrbQ{side}")
        U(QINV, X0 + 560, y + 60, f"OrbQI{side}")
        U(OFF, X0 + 700, y, f"OrbArm{side}")
        sp(f"OrbArm{side}.Item", f'(Type=Bone,Name="{UA}")')
        sp(f"OrbArm{side}.bPropagateToChildren", "True")
        U(OFF, X0 + 900, y, f"OrbHand{side}")
        sp(f"OrbHand{side}.Item", f'(Type=Bone,Name="{HA}")')
        sp(f"OrbHand{side}.bPropagateToChildren", "True")
        lk(f"OrbHa{side}.Transform.Translation", f"OrbSub{side}.A")
        lk(f"OrbSh{side}.Transform.Translation", f"OrbSub{side}.B")
        lk(f"OrbSub{side}.Result", f"OrbAx{side}.Value")
        try:
            ok = ctrl.bind_pin_to_variable(f"OrbAng{side}.A", "ElbowAngle", False)
            step(f"{'bind' if ok else 'BIND FALSE'} OrbAng{side}.A")
        except Exception as e:
            step(f"BIND ERR {str(e)[:50]}")
        lk(f"{WI}.Result", f"OrbAng{side}.B")
        lk(f"OrbAx{side}.Result", f"OrbQ{side}.Axis")
        lk(f"OrbAng{side}.Result", f"OrbQ{side}.Angle")
        lk(f"OrbQ{side}.Result", f"OrbQI{side}.Value")
        lk(f"OrbQ{side}.Result", f"OrbArm{side}.OffsetTransform.Rotation")
        lk(f"OrbQI{side}.Result", f"OrbHand{side}.OffsetTransform.Rotation")

    # ── 3) exec 연결: TwoBoneIK_L → OrbArmR → OrbHandR → OrbArmL → OrbHandL
    lk("TwoBoneIK_L.ExecutePin", "OrbArmR.ExecutePin")
    lk("OrbArmR.ExecutePin", "OrbHandR.ExecutePin")
    lk("OrbHandR.ExecutePin", "OrbArmL.ExecutePin")
    lk("OrbArmL.ExecutePin", "OrbHandL.ExecutePin")

    bp.recompile_vm()
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    step("recompiled+saved")
except Exception:
    step("FATAL\n" + traceback.format_exc())
