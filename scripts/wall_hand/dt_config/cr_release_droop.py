# -*- coding: utf-8 -*-
"""릴리즈 손목 바닥 방향(droop) — CR에 손별 Slerp 삽입.
Effector.Rotation = Slerp(A=팜다운 상수, B=QMul 벽회전, T=WInterp weight)
weight 1(부착)=벽회전 / 릴리즈 페이드 중 바닥 방향으로 기움."""
import unreal, traceback

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/cr_release_droop.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
SLERP = "/Script/RigVM.RigVMFunction_MathQuaternionSlerp"
L = []

def step(s):
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))

def qstr(q):
    return f"(X={q.x:.6f},Y={q.y:.6f},Z={q.z:.6f},W={q.w:.6f})"

def main():
    # 1) 팜다운 후보 quat (메시 컴포넌트 공간, 1차 가설: 메시 fwd=+Y, up=+Z)
    #   R: 손가락(-X)→아래  ⇒ X축→위(0,0,1) / 손바닥(+Y)→전방(0,1,0)
    #   L: 미러 ⇒ Y축→(0,-1,0)
    rotR = unreal.MathLibrary.make_rot_from_xy(unreal.Vector(0, 0, 1), unreal.Vector(0, 1, 0))
    rotL = unreal.MathLibrary.make_rot_from_xy(unreal.Vector(0, 0, 1), unreal.Vector(0, -1, 0))
    qR = rotR.quaternion()
    qL = rotL.quaternion()
    step(f"qR={qstr(qR)}")
    step(f"qL={qstr(qL)}")

    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")

    def U(s, x, y, nm):
        n = ctrl.add_unit_node_from_struct_path(s, "Execute", unreal.Vector2D(x, y), nm)
        step(f"add {nm} -> {n.get_node_path() if n else None}")
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
            step(f"{'brk' if ok else 'BRKFALSE'} {a}->{b}")
        except Exception as e:
            step(f"BRK ERR {str(e)[:50]}")

    U(SLERP, 700, -200, "SlerpRelR")
    U(SLERP, 700, 200, "SlerpRelL")
    sp("SlerpRelR.A", qstr(qR))
    sp("SlerpRelL.A", qstr(qL))
    lk("QMulR.Result", "SlerpRelR.B")
    lk("WInterpR.Result", "SlerpRelR.T")
    lk("QMulL.Result", "SlerpRelL.B")
    lk("WInterpL.Result", "SlerpRelL.T")
    brk("QMulR.Result", "TwoBoneIK_R.Effector.Rotation")
    brk("QMulL.Result", "TwoBoneIK_L.Effector.Rotation")
    lk("SlerpRelR.Result", "TwoBoneIK_R.Effector.Rotation")
    lk("SlerpRelL.Result", "TwoBoneIK_L.Effector.Rotation")
    step("done — 저장은 별도")

try:
    main()
except Exception:
    step("FATAL\n" + traceback.format_exc())
