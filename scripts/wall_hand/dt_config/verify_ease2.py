# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/verify_ease2.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
res = []
try:
    c = unreal.EditorAssetLibrary.load_asset(f"{DIR}/C_WallHandAttachEase")
    if c:
        res.append("eval " + " ".join(f"{x:.2f}:{c.get_float_value(x):.3f}" for x in (0.0, 0.25, 0.5, 0.75, 1.0)))
    else:
        res.append("curve LOAD FAIL")
    da = unreal.EditorAssetLibrary.load_asset(f"{DIR}/DA_WallHandIK")
    da.modify()
    da.set_editor_property("AttachDuration", 0.45)
    unreal.EditorAssetLibrary.save_asset(f"{DIR}/DA_WallHandIK", only_if_is_dirty=False)
    res.append(f"AttachDuration={da.get_editor_property('AttachDuration')}")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
