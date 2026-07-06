# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/cr_recompile.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
res = []
try:
    bp = unreal.load_asset(DST)
    fns = [a for a in dir(bp) if 'compile' in a.lower()]
    res.append("compile fns: " + ", ".join(fns))
    try:
        bp.recompile_vm()
        res.append("recompile_vm OK")
    except Exception as e:
        res.append(f"recompile_vm FAIL {str(e)[:80]}")
        try:
            unreal.BlueprintEditorLibrary.compile_blueprint(bp)
            res.append("BlueprintEditorLibrary.compile OK")
        except Exception as e2:
            res.append(f"compile FAIL {str(e2)[:80]}")
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    res.append("saved")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
