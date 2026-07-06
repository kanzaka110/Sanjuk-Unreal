# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/pole_restore.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
res = []
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    for a, b in [("ElbDirR.Result", "TwoBoneIK_R.PoleVector"), ("ElbDirL.Result", "TwoBoneIK_L.PoleVector")]:
        ok = ctrl.add_link(a, b)
        res.append(f"relink {a} → {ok}")
    bp.recompile_vm()
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    res.append("recompiled+saved")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
