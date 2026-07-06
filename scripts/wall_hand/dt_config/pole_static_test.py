# -*- coding: utf-8 -*-
"""분리 실험: 폴 링크 절단 + 정적 45° 직접 세팅 (몸에서 위-바깥)"""
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/pole_static_test.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
res = []
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    for a, b in [("ElbDirR.Result", "TwoBoneIK_R.PoleVector"), ("ElbDirL.Result", "TwoBoneIK_L.PoleVector")]:
        try:
            ok = ctrl.break_link(a, b)
            res.append(f"brk {a} → {ok}")
        except Exception as e:
            res.append(f"brk ERR {str(e)[:60]}")
    ok = ctrl.set_pin_default_value("TwoBoneIK_R.PoleVector", "(X=-0.707,Y=0.000,Z=0.707)", False)
    res.append(f"R static 45 → {ok}")
    ok = ctrl.set_pin_default_value("TwoBoneIK_L.PoleVector", "(X=0.707,Y=0.000,Z=0.707)", False)
    res.append(f"L static 45 → {ok}")
    bp.recompile_vm()
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    res.append("recompiled+saved")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
