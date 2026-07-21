# ToLadder 손 창 적용 + End_* 모디파이어 제거 (2026-07-21, 유저 지시)
#
#  - ToLadder_Far_* 7종: mod_reclassify 로 '이동' 분류가 됐으므로 손 창을 기록 (발은 수작업 영역)
#  - End_* 8종: 모디파이어 인스턴스 자체를 제거 (커브도 같이 정리)
import unreal, json

PLAN = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/toladder_plan.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/toladder_end.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
log = {"toladder": [], "end_removed": [], "errors": []}


def get_aud_and_insts(seq):
    for aud in seq.get_editor_property("asset_user_data") or []:
        if "AnimationModifiersAssetUserData" not in str(type(aud)):
            continue
        insts = list(aud.get_editor_property("animation_modifier_instances") or [])
        return aud, insts
    return None, []


try:
    plan = json.load(open(PLAN))
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    paths = {str(a.package_name).split("/")[-1]: str(a.package_name)
             for a in ar.get_assets_by_path(DIR, recursive=True)}

    # 1) ToLadder 손 창
    for nm, vals in sorted(plan.items()):
        try:
            seq = unreal.load_asset(paths[nm])
            _, insts = get_aud_and_insts(seq)
            inst = None
            for m in insts:
                if "AM_SBLedgeIK" in str(m.get_class().get_name()):
                    inst = m
            if inst is None:
                log["errors"].append({nm: "no instance"})
                continue
            for k, v in vals.items():
                inst.set_editor_property(k, float(v))
            saved = bool(unreal.EditorAssetLibrary.save_asset(paths[nm], only_if_is_dirty=False))
            log["toladder"].append({nm: {"set": vals, "saved": saved}})
        except Exception as e:
            log["errors"].append({nm: repr(e)[:140]})

    # 2) End_* 모디파이어 제거 — 먼저 Revert(커브 제거) 시도 후 인스턴스 목록에서 제외
    for nm, path in sorted(paths.items()):
        if not nm.startswith("P_Player_Ledge_End"):
            continue
        try:
            seq = unreal.load_asset(path)
            if not isinstance(seq, unreal.AnimSequence):
                continue
            aud, insts = get_aud_and_insts(seq)
            if aud is None or not insts:
                log["end_removed"].append({nm: "인스턴스 없음(이미 정리됨)"})
                continue
            keep, removed = [], 0
            for m in insts:
                if "AM_SBLedgeIK" in str(m.get_class().get_name()):
                    try:
                        # 커브 정리를 위해 Revert 우선 시도 (실패해도 인스턴스는 제거)
                        unreal.AnimationModifier.revert_from_animation_sequence(m, seq)
                    except Exception as e:
                        log["errors"].append({nm + " revert": repr(e)[:100]})
                    removed += 1
                else:
                    keep.append(m)
            aud.set_editor_property("animation_modifier_instances", keep)
            saved = bool(unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False))
            log["end_removed"].append({nm: {"removed": removed, "kept": len(keep), "saved": saved}})
        except Exception as e:
            log["errors"].append({nm: repr(e)[:140]})
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1, ensure_ascii=False)
print("TOLADDER_END_DONE toladder=%d end=%d err=%d" % (
    len(log["toladder"]), len(log["end_removed"]), len(log["errors"])))
