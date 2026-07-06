# -*- coding: utf-8 -*-
import unreal
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/verify_ease.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
c = unreal.EditorAssetLibrary.load_asset(f"{DIR}/C_WallHandAttachEase")
r = "eval " + " ".join(f"{x:.2f}:{c.get_float_value(x):.3f}" for x in (0.0, 0.25, 0.5, 0.75, 1.0)) if c else "LOAD FAIL"
# DA에 AttachDuration 0.45 (구형 등가) 반영
da = unreal.EditorAssetLibrary.load_asset(f"{DIR}/DA_WallHandIK")
da.modify()
da.set_editor_property("AttachDuration", 0.45)
unreal.EditorAssetLibrary.save_asset(f"{DIR}/DA_WallHandIK", only_if_is_dirty=False)
open(OUT, "w").write(r + f"\nAttachDuration={da.get_editor_property('AttachDuration')}")
