# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/orbit_static_r.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
res = []
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    try:
        ok = ctrl.unbind_pin_from_variable("OrbAngR.A")
        res.append(f"unbind {ok}")
    except Exception as e:
        res.append(f"unbind ERR {str(e)[:60]}")
    ok = ctrl.set_pin_default_value("OrbAngR.A", "0.800000", False)
    res.append(f"static 0.8 {ok}")
    bp.recompile_vm()
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    res.append("recompiled+saved")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
