# AM_SBLedgeIK 인스턴스 파라미터 전수 덤프 (read-only) — 백업 + 수작업 튜닝값 수집
# 용도: 유저 수작업 구간을 ground truth 로 삼아 derive_windows 판정식을 역보정하기 위한 원본.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_params_dump.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
KEYS = ["HandMoveStartL", "HandMoveEndL", "HandMoveStartR", "HandMoveEndR",
        "FootMoveStartL", "FootMoveEndL", "FootMoveStartR", "FootMoveEndR",
        "HandMove2StartL", "HandMove2EndL", "HandMove2StartR", "HandMove2EndR",
        "FootMove2StartL", "FootMove2EndL", "FootMove2StartR", "FootMove2EndR",
        "ReleaseRampTime", "PlantRampTime", "ExitHoldTime", "ExitFadeTime",
        "PelvisMinSpeed", "PelvisFallFrames",
        "PelvisSpringStart", "PelvisSpringFull", "PelvisSpringHoldEnd", "PelvisSpringEnd"]
res = {"anims": {}, "errors": [], "instance_count": {}}
try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    paths = sorted({str(a.package_name) for a in ar.get_assets_by_path(DIR, recursive=True)
                    if str(a.package_name).split("/")[-1].startswith("P_Player_Ledge")})
    for p in paths:
        nm = p.split("/")[-1]
        try:
            seq = unreal.load_asset(p)
            if not isinstance(seq, unreal.AnimSequence):
                continue
            insts = []
            for aud in seq.get_editor_property("asset_user_data") or []:
                if "AnimationModifiersAssetUserData" not in str(type(aud)):
                    continue
                for m in aud.get_editor_property("animation_modifier_instances") or []:
                    if "AM_SBLedgeIK" in str(m.get_class().get_name()):
                        insts.append(m)
            res["instance_count"][nm] = len(insts)
            if not insts:
                continue
            inst = insts[-1]   # 중복 누적 시 마지막이 유효 (dedupe_modifier_stack 이력)
            rec = {"dur": round(float(unreal.AnimationLibrary.get_sequence_length(seq)), 3)}
            for k in KEYS:
                try:
                    rec[k] = round(float(inst.get_editor_property(k)), 4)
                except Exception:
                    pass
            res["anims"][nm] = rec
        except Exception as e:
            res["errors"].append({nm: repr(e)[:120]})
except Exception:
    import traceback
    res["error"] = traceback.format_exc()
with open(OUT, "w") as fp:
    json.dump(res, fp, indent=1)
dupes = {k: v for k, v in res["instance_count"].items() if v != 1}
print("MOD_PARAMS_DUMP anims=%d errors=%d 인스턴스중복=%d" % (len(res["anims"]), len(res["errors"]), len(dupes)))
