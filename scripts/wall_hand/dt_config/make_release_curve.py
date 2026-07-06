# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/make_release_curve.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
CSV = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/curve_linear.csv"
res = []
try:
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
    res.append(f"eval 0/0.5/1 = {c.get_float_value(0.0):.2f}/{c.get_float_value(0.5):.2f}/{c.get_float_value(1.0):.2f}")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
