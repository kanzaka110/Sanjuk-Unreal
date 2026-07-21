# 죽은 파라미터 값 정리 (2026-07-21)
#
# 1) 정지 분류(Idle/LedgeSeeking/MoveToIdle) 38종의 창 값 → 0
#    WriteIdleCurves 는 창을 읽지 않는다(커브 4개에 1.0/0.0 키만). 남은 값은 혼선만 준다.
# 2) HandMove2 잔재 6종 → 0
#    derive_windows2.py 일괄 산출이 남은 것. 0.600~0.833 이 5종에 동일하고 PRESERVE 밖.
#
# 건드리지 않는 것:
#   - PelvisSpring* : BakePelvisSpring 이 분기 '앞'에서 실행되므로 정지 애님에도 유효
#   - 값이 dur 인 스프링 : "스프링 off" 를 뜻하는 의도된 표기
#   - FootMove2 : 8종 중 4종이 유저 수작업(PRESERVE)
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/clear_dead_params.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
WIN = ["HandMoveStartL", "HandMoveEndL", "HandMoveStartR", "HandMoveEndR",
       "FootMoveStartL", "FootMoveEndL", "FootMoveStartR", "FootMoveEndR"]
H2 = ["HandMove2StartL", "HandMove2EndL", "HandMove2StartR", "HandMove2EndR"]
log = {"idle_cleared": [], "hand2_cleared": [], "errors": []}


def is_idle_class(nm):
    s = nm.lower()
    if "end" in s or "backwardjump" in s:
        return False          # 이탈 (현재 해당 애님은 모디파이어 제거됨)
    return "idle" in s or "ledgeseeking" in s


try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    paths = {str(a.package_name).split("/")[-1]: str(a.package_name)
             for a in ar.get_assets_by_path(DIR, recursive=True)}
    for nm, path in sorted(paths.items()):
        if not nm.startswith("P_Player_Ledge"):
            continue
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
                continue
            changed = False
            if is_idle_class(nm):
                before = {k: round(float(inst.get_editor_property(k)), 3) for k in WIN}
                if any(abs(v) > 1e-6 for v in before.values()):
                    for k in WIN:
                        inst.set_editor_property(k, 0.0)
                    log["idle_cleared"].append({nm: before})
                    changed = True
            b2 = {k: round(float(inst.get_editor_property(k)), 3) for k in H2}
            if any(abs(v) > 1e-6 for v in b2.values()):
                for k in H2:
                    inst.set_editor_property(k, 0.0)
                log["hand2_cleared"].append({nm: b2})
                changed = True
            if changed:
                unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
        except Exception as e:
            log["errors"].append({nm: repr(e)[:140]})
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1, ensure_ascii=False)
print("CLEAR_DEAD_PARAMS idle=%d hand2=%d err=%d" % (
    len(log["idle_cleared"]), len(log["hand2_cleared"]), len(log["errors"])))
