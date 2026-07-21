# 모디파이어 일괄 Apply (2026-07-21, 유저 지시 "PRESERVE도 모두 적용")
#
# 전제: 각 애님의 인스턴스 파라미터가 이미 원하는 값으로 기록돼 있어야 한다.
#       (apply_target_windows / apply_toladder / 유저 수작업 33종)
#       그래야 Apply 해도 각자의 안무가 그대로 재생성된다.
# 백업: ledge_curves_backup.json (158종 1330커브) / mod_params_BACKUP_*.json
#
# ⚠ apply_anim_modifier(persist=True) 는 인스턴스를 '추가'한다 → 적용 후 중복 점검 필수 (README v12 함정)
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/apply_modifier_all.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
log = {"applied": 0, "skipped": [], "errors": [], "dupes": {}}
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
            inst = None
            for aud in seq.get_editor_property("asset_user_data") or []:
                if "AnimationModifiersAssetUserData" not in str(type(aud)):
                    continue
                for m in aud.get_editor_property("animation_modifier_instances") or []:
                    if "AM_SBLedgeIK" in str(m.get_class().get_name()):
                        inst = m
            if inst is None:
                log["skipped"].append(nm)          # End_* 8종 = 모디파이어 제거됨
                continue
            inst.call_method("ApplyToAnimationSequence", (seq,))
            unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
            log["applied"] += 1
        except Exception as e:
            log["errors"].append({nm: repr(e)[:160]})

    # 인스턴스 중복 점검
    for path in paths:
        nm = path.split("/")[-1]
        try:
            seq = unreal.load_asset(path)
            if not isinstance(seq, unreal.AnimSequence):
                continue
            cnt = 0
            for aud in seq.get_editor_property("asset_user_data") or []:
                if "AnimationModifiersAssetUserData" not in str(type(aud)):
                    continue
                for m in aud.get_editor_property("animation_modifier_instances") or []:
                    if "AM_SBLedgeIK" in str(m.get_class().get_name()):
                        cnt += 1
            if cnt != 1:
                log["dupes"][nm] = cnt
        except Exception:
            pass
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1, ensure_ascii=False)
print("APPLY_ALL_DONE applied=%d skipped=%d err=%d dupes=%d" % (
    log["applied"], len(log["skipped"]), len(log["errors"]), len(log["dupes"])))
