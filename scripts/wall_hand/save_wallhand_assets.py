# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260703_opt/save_result2.txt"
ASSETS = [
    "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP",
    "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP",
    "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK",
    "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK",
]
L = []
for a in ASSETS:
    try:
        obj = unreal.load_asset(a)
        pkg = obj.get_outermost()
        ok = unreal.EditorLoadingAndSavingUtils.save_packages([pkg], False)
        L.append("%s save=%s" % (a.split('/')[-1], ok))
    except Exception:
        L.append("%s FAIL %s" % (a, traceback.format_exc(limit=1)))
open(OUT, "w", encoding="utf-8").write("\n".join(L))
