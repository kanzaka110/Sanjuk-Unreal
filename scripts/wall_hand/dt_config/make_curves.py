# -*- coding: utf-8 -*-
"""에디터 내 실행용: CurveFloat 2개 생성 + (0,0)(1,1) 키 시딩 시도.
결과는 파일로 기록 (Monolith 로그 미캡처 대응)."""
import unreal, json, traceback

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/make_curves_result.txt"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
res = []

def make_curve(name):
    at = unreal.AssetToolsHelpers.get_asset_tools()
    existing = unreal.EditorAssetLibrary.does_asset_exist(f"{DIR}/{name}")
    if existing:
        res.append(f"{name}: already exists")
        return unreal.EditorAssetLibrary.load_asset(f"{DIR}/{name}")
    factory = unreal.CurveFloatFactory()
    a = at.create_asset(name, DIR, unreal.CurveFloat, factory)
    res.append(f"{name}: created={a is not None}")
    return a

def seed_keys(curve, name):
    # 키 시딩 API 후보 순차 시도
    try:
        fc = curve.get_editor_property("float_curve")
        res.append(f"{name}: float_curve prop type={type(fc).__name__}")
        # RichCurve가 struct로 노출되면 keys 배열 조작 시도
        keys = fc.get_editor_property("keys")
        res.append(f"{name}: keys prop ok, n={len(keys)}")
        k0 = unreal.RichCurveKey()
        k0.set_editor_property("time", 0.0); k0.set_editor_property("value", 0.0)
        k1 = unreal.RichCurveKey()
        k1.set_editor_property("time", 1.0); k1.set_editor_property("value", 1.0)
        fc.set_editor_property("keys", [k0, k1])
        curve.set_editor_property("float_curve", fc)
        res.append(f"{name}: seeded via float_curve.keys")
        return True
    except Exception as e:
        res.append(f"{name}: float_curve route FAIL {e}")
    try:
        # UCurveBase::ImportFromJSONString 노출 여부
        js = json.dumps([{"time": 0.0, "value": 0.0}, {"time": 1.0, "value": 1.0}])
        curve.import_from_json_string(js)
        res.append(f"{name}: seeded via import_from_json_string")
        return True
    except Exception as e:
        res.append(f"{name}: json route FAIL {e}")
    try:
        curve.reset_curve()
        curve.add_key(0.0, 0.0)
        curve.add_key(1.0, 1.0)
        res.append(f"{name}: seeded via add_key")
        return True
    except Exception as e:
        res.append(f"{name}: add_key route FAIL {e}")
    return False

try:
    for nm in ("C_WallHandAttach", "C_WallHandRelease"):
        c = make_curve(nm)
        if c:
            ok = seed_keys(c, nm)
            if ok:
                v0, v5, v1 = c.get_float_value(0.0), c.get_float_value(0.5), c.get_float_value(1.0)
                res.append(f"{nm}: eval 0/0.5/1 = {v0:.3f}/{v5:.3f}/{v1:.3f}")
            unreal.EditorAssetLibrary.save_asset(f"{DIR}/{nm}", only_if_is_dirty=False)
            res.append(f"{nm}: saved")
except Exception:
    res.append("FATAL " + traceback.format_exc())

open(OUT, "w", encoding="utf-8").write("\n".join(res))
