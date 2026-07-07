# -*- coding: utf-8 -*-
"""DA_WallHandIK + PDA CDO의 FrontHand* 현재값 덤프 (read-only)."""
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/dump_da_front.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
L = []
try:
    da = unreal.EditorAssetLibrary.load_asset(f"{DIR}/DA_WallHandIK")
    for p in ("FrontHandHalfWidth", "FrontHandHeight", "AttachSpeed", "ElbowAngleDeg",
              "IKStrengthMax", "AttachStartDist", "AttachFullDist", "RightHandHeight",
              "SpineLeanMaxDeg", "TurnReleaseSpeed", "TurnBlockHold"):
        try:
            L.append(f"DA.{p} = {da.get_editor_property(p)}")
        except Exception as e:
            L.append(f"DA.{p} ERR {e}")
except Exception:
    L.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(L))
unreal.log("[dump_da_front] done")
