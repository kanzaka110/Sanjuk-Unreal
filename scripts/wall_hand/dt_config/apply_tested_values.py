# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/apply_tested_values.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
CSV = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/curve_release_exp.csv"
res = []
try:
    # 1) ReleaseCurve 지수 모양 재임포트
    f = unreal.CSVImportFactory()
    s = f.get_editor_property("automated_import_settings")
    s.set_editor_property("import_type", unreal.CSVImportType.ECSV_CURVE_FLOAT)
    f.set_editor_property("automated_import_settings", s)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", CSV)
    t.set_editor_property("destination_path", DIR)
    t.set_editor_property("destination_name", "C_WallHandRelease")
    t.set_editor_property("factory", f)
    t.set_editor_property("automated", True)
    t.set_editor_property("save", True)
    t.set_editor_property("replace_existing", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    c = unreal.EditorAssetLibrary.load_asset(f"{DIR}/C_WallHandRelease")
    vals = [f"{x:.2f}:{c.get_float_value(x):.3f}" for x in (0.0, 0.25, 0.5, 0.75, 1.0)]
    res.append("ReleaseCurve eval " + " ".join(vals))
    # 재임포트로 오브젝트가 교체됐을 수 있음 → DA/CDO 참조 재확인·재세팅
    da = unreal.EditorAssetLibrary.load_asset(f"{DIR}/DA_WallHandIK")
    da.modify()
    da.set_editor_property("ReleaseCurve", c)
    # 2) AttachDuration 0.4 (구 3→12 가속 등가)
    da.set_editor_property("AttachDuration", 0.4)
    res.append(f"DA.ReleaseCurve={da.get_editor_property('ReleaseCurve').get_name()}")
    res.append(f"DA.AttachDuration={da.get_editor_property('AttachDuration')}")
    unreal.EditorAssetLibrary.save_asset(f"{DIR}/DA_WallHandIK", only_if_is_dirty=False)
    res.append("DA saved")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
