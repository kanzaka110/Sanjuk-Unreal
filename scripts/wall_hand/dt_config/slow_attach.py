# -*- coding: utf-8 -*-
import unreal
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/slow_attach.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
da = unreal.EditorAssetLibrary.load_asset(f"{DIR}/DA_WallHandIK")
da.modify()
da.set_editor_property("AttachDuration", 0.6)
unreal.EditorAssetLibrary.save_asset(f"{DIR}/DA_WallHandIK", only_if_is_dirty=False)
open(OUT, "w").write(f"AttachDuration={da.get_editor_property('AttachDuration')}")
