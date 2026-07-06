# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/fix_da_curve.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
res = []
try:
    da = unreal.EditorAssetLibrary.load_asset(f"{DIR}/DA_WallHandIK")
    fc = unreal.EditorAssetLibrary.load_asset(f"{DIR}/C_WallHandFrontAttach")
    ac = unreal.EditorAssetLibrary.load_asset(f"{DIR}/C_WallHandAttach")
    da.modify()
    da.set_editor_property("FrontAttachCurve", fc)
    if not da.get_editor_property("AttachCurve"):
        da.set_editor_property("AttachCurve", ac)
    res.append(f"FrontAttachCurve = {da.get_editor_property('FrontAttachCurve')}")
    res.append(f"AttachCurve = {da.get_editor_property('AttachCurve')}")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
