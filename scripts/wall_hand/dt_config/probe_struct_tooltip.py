# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/probe_struct_tooltip.txt"
res = []
try:
    S = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK/S_WallHandIKConfig"
    u = unreal.EditorAssetLibrary.load_asset(S)
    res.append(f"loaded={u}")
    if u:
        res.append(f"class={u.get_class().get_name()}")
        for prop in ("EditorData", "editor_data"):
            try:
                ed = u.get_editor_property(prop)
                res.append(f"{prop}: OK {type(ed).__name__}")
            except Exception as e:
                res.append(f"{prop}: FAIL {e}")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
