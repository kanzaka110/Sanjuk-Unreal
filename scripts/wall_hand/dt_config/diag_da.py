# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/diag_da.txt"
res = []
try:
    da = unreal.EditorAssetLibrary.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK/DA_WallHandIK")
    res.append(f"da={da}")
    if da:
        cls = da.get_class()
        res.append(f"class={cls.get_name()} path={cls.get_path_name()}")
        gen = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK/PDA_WallHandIKConfig")
        res.append(f"current gen class={gen.get_path_name() if gen else None}")
        res.append(f"same={cls == gen}")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
