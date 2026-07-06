# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/static_angle_test.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
res = []
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    for a, b in [("VariableNode_6.Value", "ElbCos.Value"), ("VariableNode_9.Value", "ElbSin.Value")]:
        try:
            ok = ctrl.break_link(a, b); res.append(f"brk {a} {ok}")
        except Exception as e:
            res.append(f"brk ERR {str(e)[:50]}")
    ok = ctrl.set_pin_default_value("ElbCos.Value", "1.200000", False); res.append(f"cos=1.2 {ok}")
    ok = ctrl.set_pin_default_value("ElbSin.Value", "1.200000", False); res.append(f"sin=1.2 {ok}")
    bp.recompile_vm()
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    res.append("recompiled+saved")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
