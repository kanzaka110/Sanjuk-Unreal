# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/del_old_assets.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
res = []
try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for nm in ("DT_WallHandIK", "S_WallHandIKConfig", "C_WallHandRelease"):
        p = f"{DIR}/{nm}"
        if not unreal.EditorAssetLibrary.does_asset_exist(p):
            res.append(f"{nm}: 이미 없음")
            continue
        refs = ar.get_referencers(unreal.Name(p), unreal.AssetRegistryDependencyOptions())
        refs = [str(r) for r in (refs or []) if "/Game/" in str(r)]
        if refs:
            res.append(f"{nm}: 참조 잔존 → 삭제 보류 {refs}")
        else:
            ok = unreal.EditorAssetLibrary.delete_asset(p)
            res.append(f"{nm}: 참조 0 → 삭제 {ok}")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
