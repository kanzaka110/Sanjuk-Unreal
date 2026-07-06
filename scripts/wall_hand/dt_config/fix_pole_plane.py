# -*- coding: utf-8 -*-
"""폴 각도를 유효 평면(Y-Z)으로 재배선: dir=(0, -sin, cos) 양손 공통."""
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/fix_pole_plane.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
res = []
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    def brk(a, b):
        try:
            ok = ctrl.break_link(a, b); res.append(f"brk {a}->{b} {ok}")
        except Exception as e:
            res.append(f"brk ERR {a} {str(e)[:40]}")
    def lk(a, b):
        ok = ctrl.add_link(a, b); res.append(f"{'lk' if ok else 'LKFALSE'} {a}->{b}")
    def sp(p, v):
        ok = ctrl.set_pin_default_value(p, v, False); res.append(f"sp {p}={v} {ok}")
    # 구 X-Z 배선 해체
    brk("ElbNeg.Result", "ElbDirR.X")
    brk("ElbCos.Result", "ElbDirL.X")
    brk("ElbSin.Result", "ElbDirR.Z")
    brk("ElbSin.Result", "ElbDirL.Z")
    # ElbNeg = -sin 으로 전환
    brk("ElbCos.Result", "ElbNeg.A")
    lk("ElbSin.Result", "ElbNeg.A")
    # 신규: X=0, Y=-sin, Z=cos (양손 공통)
    sp("ElbDirR.X", "0.000000")
    sp("ElbDirL.X", "0.000000")
    lk("ElbNeg.Result", "ElbDirR.Y")
    lk("ElbNeg.Result", "ElbDirL.Y")
    lk("ElbCos.Result", "ElbDirR.Z")
    lk("ElbCos.Result", "ElbDirL.Z")
    bp.recompile_vm()
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    res.append("recompiled+saved")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
