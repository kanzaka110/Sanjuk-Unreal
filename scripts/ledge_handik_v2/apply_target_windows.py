# TARGET 창 적용 (2026-07-21) — target_plan.json 을 모디파이어 인스턴스에 기록
#
# 손: 캘리브레이션(유저 수작업 33종 기준) thr110/gap0.20/pad(0,+0.033) 산출값 — 2프레임 이내 74%
# 발: 벽 조합 규칙만 (WalllessToWallless→0~0 / WalllessTo*→시작0 / *ToWallless→끝=dur)
#     WallToWall 및 이름에 벽조합 없는 계열은 건드리지 않음(수작업 영역)
# PRESERVE 33종은 plan 생성 단계에서 이미 제외됨.
# 백업: mod_params_BACKUP_*.json (적용 전 전수 덤프)
#
# ⚠ 이 스크립트는 '인스턴스 파라미터'만 바꾼다. 실제 커브는 모디파이어 Apply 시 재생성된다.
import unreal, json

PLAN = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/target_plan.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/apply_target.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
HAND_KEYS = {"hand_l": ("HandMoveStartL", "HandMoveEndL"), "hand_r": ("HandMoveStartR", "HandMoveEndR")}
FOOT_KEYS = {"l": ("FootMoveStartL", "FootMoveEndL"), "r": ("FootMoveStartR", "FootMoveEndR")}

plan = json.load(open(PLAN))
log = {"set_hand": 0, "set_foot": 0, "anims_changed": 0, "saved": 0, "skipped": [], "errors": []}
try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    paths = {str(a.package_name).split("/")[-1]: str(a.package_name)
             for a in ar.get_assets_by_path(DIR, recursive=True)}
    for nm, rec in sorted(plan.items()):
        if rec["class"] != "이동":
            continue
        if nm not in paths:
            log["skipped"].append({nm: "asset not found"})
            continue
        try:
            seq = unreal.load_asset(paths[nm])
            inst = None
            for aud in seq.get_editor_property("asset_user_data") or []:
                if "AnimationModifiersAssetUserData" not in str(type(aud)):
                    continue
                for m in aud.get_editor_property("animation_modifier_instances") or []:
                    if "AM_SBLedgeIK" in str(m.get_class().get_name()):
                        inst = m
            if inst is None:
                log["skipped"].append({nm: "no modifier instance"})
                continue
            changed = False
            for bone, (ks, ke) in HAND_KEYS.items():
                new = (rec["hand"].get(bone) or {}).get("new")
                if not new:
                    continue
                inst.set_editor_property(ks, float(new[0]))
                inst.set_editor_property(ke, float(new[1]))
                log["set_hand"] += 1
                changed = True
            for side, (ks, ke) in FOOT_KEYS.items():
                new = rec["foot"][side].get("new")
                if new is None:
                    continue
                inst.set_editor_property(ks, float(new[0]))
                inst.set_editor_property(ke, float(new[1]))
                log["set_foot"] += 1
                changed = True
            if changed:
                log["anims_changed"] += 1
                if unreal.EditorAssetLibrary.save_asset(paths[nm], only_if_is_dirty=False):
                    log["saved"] += 1
        except Exception as e:
            log["errors"].append({nm: repr(e)[:150]})
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1, ensure_ascii=False)
print("APPLY_TARGET_DONE hand=%d foot=%d anims=%d saved=%d err=%d" % (
    log["set_hand"], log["set_foot"], log["anims_changed"], log["saved"], len(log["errors"])))
