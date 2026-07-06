# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/revert_elbow_cr.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
res = []
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    for nm in ("OrbArmR", "OrbHandR", "OrbArmL", "OrbHandL",
               "OrbShR", "OrbHaR", "OrbSubR", "OrbAxR", "OrbAngR", "OrbQR", "OrbQIR",
               "OrbShL", "OrbHaL", "OrbSubL", "OrbAxL", "OrbAngL", "OrbQL", "OrbQIL"):
        try:
            ctrl.remove_node_by_name(nm)
            res.append(f"rm {nm}")
        except Exception as e:
            res.append(f"rm {nm} err {str(e)[:30]}")
    # 폴 디폴트 원본 확인 (이미 원복돼 있어야 함)
    for p, v in (("TwoBoneIK_R.PoleVector", "(X=-50.000000,Y=0.000000,Z=1.000000)"),
                 ("TwoBoneIK_L.PoleVector", "(X=50.000000,Y=0.000000,Z=1.000000)")):
        ok = ctrl.set_pin_default_value(p, v, False)
        res.append(f"pole {p} {ok}")
    try:
        bp.remove_member_variable("ElbowAngle")
        res.append("rm var ElbowAngle")
    except Exception as e:
        res.append(f"rm var err {str(e)[:40]}")
    bp.recompile_vm()
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    res.append("recompiled+saved")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
