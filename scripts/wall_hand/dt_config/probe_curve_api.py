# -*- coding: utf-8 -*-
import unreal
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/probe_curve_api.txt"
c = unreal.EditorAssetLibrary.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK/C_WallHandAttach")
lines = []
lines.append("== dir(CurveFloat) non-dunder ==")
lines.append(", ".join(a for a in dir(c) if not a.startswith("_")))
lines.append("== editor properties? ==")
for p in ("FloatCurve", "float_curve", "Keys"):
    try:
        v = c.get_editor_property(p)
        lines.append(f"prop {p}: OK {type(v).__name__}")
    except Exception as e:
        lines.append(f"prop {p}: FAIL {e}")
open(OUT, "w", encoding="utf-8").write("\n".join(lines))
