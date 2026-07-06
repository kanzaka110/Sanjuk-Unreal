# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/fix_public2.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
res = []
try:
    bp = unreal.load_asset(DST)
    try:
        ok = bp.set_blueprint_variable_instance_editable("ElbowAngle", True)
        res.append(f"instance_editable → {ok}")
    except Exception as e:
        res.append(f"ie FAIL {str(e)[:80]}")
    vars = bp.get_member_variables()
    for v in vars:
        if "Elbow" in str(v.get_editor_property("name")):
            res.append(f"after: public={v.get_editor_property('public')} private={v.get_editor_property('private')}")
    # 실패 시 재생성 폴백
    ok_public = any("public=True" in r for r in res)
    if not ok_public:
        bp.remove_member_variable("ElbowAngle")
        res.append("removed")
        nm = bp.add_member_variable("ElbowAngle", "double", True, False, "0.02")
        res.append(f"re-added → {nm}")
        for v in bp.get_member_variables():
            if "Elbow" in str(v.get_editor_property("name")):
                res.append(f"final: public={v.get_editor_property('public')}")
    unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    res.append("saved")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
