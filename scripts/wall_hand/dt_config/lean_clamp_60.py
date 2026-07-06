# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/lean_clamp_60.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
res = []
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    for pin, v in [("Yaw.Minimum", "-1.047198"), ("Yaw.Maximum", "1.047198")]:
        ok = ctrl.set_pin_default_value(pin, v, False)
        res.append(f"{pin} = {v} → {'OK' if ok else 'FALSE'}")
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    res.append("saved")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
