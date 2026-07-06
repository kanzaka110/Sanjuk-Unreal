# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/import_curves_result.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
CSV = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/curve_linear.csv"
res = []
try:
    # 기존 빈 커브 삭제 후 CSV 임포트로 재생성
    for nm in ("C_WallHandAttach", "C_WallHandRelease"):
        p = f"{DIR}/{nm}"
        if unreal.EditorAssetLibrary.does_asset_exist(p):
            ok = unreal.EditorAssetLibrary.delete_asset(p)
            res.append(f"{nm}: deleted empty={ok}")
        f = unreal.CSVImportFactory()
        s = f.get_editor_property("automated_import_settings")
        s.set_editor_property("import_type", unreal.CSVImportType.ECSV_CURVE_FLOAT)
        f.set_editor_property("automated_import_settings", s)
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", CSV)
        t.set_editor_property("destination_path", DIR)
        t.set_editor_property("destination_name", nm)
        t.set_editor_property("factory", f)
        t.set_editor_property("automated", True)
        t.set_editor_property("save", True)
        t.set_editor_property("replace_existing", True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        objs = t.get_editor_property("imported_object_paths")
        res.append(f"{nm}: imported={list(objs) if objs else None}")
        c = unreal.EditorAssetLibrary.load_asset(f"{DIR}/{nm}")
        if c:
            res.append(f"{nm}: eval 0/0.5/1 = {c.get_float_value(0.0):.3f}/{c.get_float_value(0.5):.3f}/{c.get_float_value(1.0):.3f}")
except Exception:
    res.append("FATAL " + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
