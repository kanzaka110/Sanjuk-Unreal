# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/seed_curve_keys_result.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
res = []
CSV = "0,0\n1,1"
for nm in ("C_WallHandAttach", "C_WallHandRelease"):
    c = unreal.EditorAssetLibrary.load_asset(f"{DIR}/{nm}")
    try:
        c.modify()
        r = c.call_method("CreateCurveFromCSVString", (CSV,))
        res.append(f"{nm}: call_method CreateCurveFromCSVString OK ret={r}")
    except Exception as e:
        res.append(f"{nm}: CreateCurveFromCSVString FAIL {e}")
        try:
            r = c.call_method("ImportFromJSONString", ('[{"Time":0,"Value":0},{"Time":1,"Value":1}]',))
            res.append(f"{nm}: ImportFromJSONString OK ret={r}")
        except Exception as e2:
            res.append(f"{nm}: ImportFromJSONString FAIL {e2}")
    try:
        v0, v5, v1 = c.get_float_value(0.0), c.get_float_value(0.5), c.get_float_value(1.0)
        res.append(f"{nm}: eval 0/0.5/1 = {v0:.3f}/{v5:.3f}/{v1:.3f}")
        unreal.EditorAssetLibrary.save_asset(f"{DIR}/{nm}", only_if_is_dirty=False)
        res.append(f"{nm}: saved")
    except Exception:
        res.append(f"{nm}: eval/save FAIL " + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
