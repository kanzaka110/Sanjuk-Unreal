# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260703_opt/cr_release_bind.txt"
L = []
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    for nm in ("fSelRelR", "fSelRelL"):
        try:
            ctrl.bind_pin_to_variable(nm + ".Condition", "bWallHandLeft", True)
            L.append("bind %s OK" % nm)
        except Exception as e:
            L.append("bind %s FAIL %s" % (nm, e))
    L.append("DONE")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(L))
