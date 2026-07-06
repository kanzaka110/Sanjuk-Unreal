# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/make_attach_ease.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
CSV = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/curve_attach_ease.csv"
res = []
try:
    f = unreal.CSVImportFactory()
    s = f.get_editor_property("automated_import_settings")
    s.set_editor_property("import_type", unreal.CSVImportType.ECSV_CURVE_FLOAT)
    f.set_editor_property("automated_import_settings", s)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", CSV)
    t.set_editor_property("destination_path", DIR)
    t.set_editor_property("destination_name", "C_WallHandAttachEase")
    t.set_editor_property("factory", f)
    t.set_editor_property("automated", True)
    t.set_editor_property("save", True)
    t.set_editor_property("replace_existing", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    c = unreal.EditorAssetLibrary.load_asset(f"{DIR}/C_WallHandAttachEase")
    res.append("eval " + " ".join(f"{x:.2f}:{c.get_float_value(x):.3f}" for x in (0.0, 0.25, 0.5, 0.75, 1.0)))
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
