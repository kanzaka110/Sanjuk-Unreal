# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/check_da_release.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
res = []
try:
    da = unreal.EditorAssetLibrary.load_asset(f"{DIR}/DA_WallHandIK")
    v = da.get_editor_property("ReleaseCurve")
    res.append(f"DA.ReleaseCurve = {v}")
    if not v:
        rc = unreal.EditorAssetLibrary.load_asset(f"{DIR}/C_WallHandRelease")
        da.modify()
        da.set_editor_property("ReleaseCurve", rc)
        res.append(f"set → {da.get_editor_property('ReleaseCurve')}")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
