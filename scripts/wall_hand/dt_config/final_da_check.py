# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/final_da_check.txt"
res = []
try:
    da = unreal.EditorAssetLibrary.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK/DA_WallHandIK")
    for p in ("IKStrengthMax", "AttachStartDist", "AttachFullDist", "AttachSpeedStart", "AttachSpeedEnd",
              "ReleaseSpeedSlow", "ReleaseSpeedFast", "TurnReleaseSpeed", "FrontHandHalfWidth",
              "FrontHandHeight", "RightHandHeight", "JogOffset", "RunOffset", "SprintOffset", "TurnBlockHold"):
        try:
            res.append(f"{p} = {da.get_editor_property(p)}")
        except Exception as e:
            res.append(f"{p} FAIL")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
