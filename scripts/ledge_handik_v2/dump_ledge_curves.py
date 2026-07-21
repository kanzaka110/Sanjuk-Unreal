# 렛지 커브 전수 백업 (read-only) — 모디파이어 일괄 Apply 전 안전망
# Apply 는 커브를 재생성하므로 수동 튜닝분이 덮인다. 파라미터 백업만으론 복구 불가 → 키까지 저장.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ledge_curves_backup.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
data = {"anims": {}, "errors": []}
try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    paths = sorted({str(a.package_name) for a in ar.get_assets_by_path(DIR, recursive=True)
                    if str(a.package_name).split("/")[-1].startswith("P_Player_Ledge")})
    for path in paths:
        nm = path.split("/")[-1]
        try:
            seq = unreal.load_asset(path)
            if not isinstance(seq, unreal.AnimSequence):
                continue
            names = [str(x) for x in unreal.AnimationLibrary.get_animation_curve_names(
                seq, unreal.RawCurveTrackTypes.RCT_FLOAT)]
            rec = {}
            for c in names:
                if not c.startswith("ledge_"):
                    continue
                try:
                    times, vals = unreal.AnimationLibrary.get_float_keys(seq, c)
                    rec[c] = [[round(float(t), 4), round(float(v), 4)] for t, v in zip(times, vals)]
                except Exception as e:
                    data["errors"].append({nm + "/" + c: repr(e)[:100]})
            if rec:
                data["anims"][nm] = rec
        except Exception as e:
            data["errors"].append({nm: repr(e)[:140]})
except Exception:
    import traceback
    data["error"] = traceback.format_exc()
with open(OUT, "w") as fp:
    json.dump(data, fp)
tot = sum(len(v) for v in data["anims"].values())
print("LEDGE_CURVES_BACKUP anims=%d curves=%d err=%d" % (len(data["anims"]), tot, len(data["errors"])))
