# -*- coding: utf-8 -*-
import unreal, os
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/check_writable.txt"
res = []
for p in ["/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP",
          "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP",
          "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"]:
    sp = unreal.SystemLibrary.get_system_path(unreal.EditorAssetLibrary.load_asset(p))
    w = os.access(sp, os.W_OK)
    res.append(f"{p} -> writable={w} ({sp})")
open(OUT, "w", encoding="utf-8").write("\n".join(res))
