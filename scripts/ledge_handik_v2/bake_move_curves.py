# ledge_hand_move_l/r 초기 베이크 — IK 타깃 위치 커브 (0=이동전 그립, 1=이동후 그립)
# 각 손 플라이트 창에서 스무스텝 0->1. 이후 에디터 수동 튜닝 전제.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ledge_move_curves.json"
BASE = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"

# (t, v) — 30fps 프레임 정렬, 프레임 중복 없음
WALL_LEAD = [(0.0, 0.0), (0.033, 0.0), (0.067, 0.16), (0.1, 0.5), (0.133, 0.84), (0.2, 1.0)]
WALL_TRAIL = [(0.0, 0.0), (0.1, 0.0), (0.2, 0.16), (0.3, 0.5), (0.4, 0.84), (0.5, 1.0)]
WLLESS_LEAD = [(0.0, 0.0), (0.1, 0.0), (0.133, 0.16), (0.167, 0.5), (0.2, 0.84), (0.267, 1.0)]
WLLESS_TRAIL = [(0.0, 0.0), (0.3, 0.0), (0.333, 0.16), (0.367, 0.5), (0.4, 0.84), (0.467, 1.0)]

FIXES = {
    "P_Player_Ledge_Move_ShortL": {"ledge_hand_move_l": WALL_LEAD, "ledge_hand_move_r": WALL_TRAIL},
    "P_Player_Ledge_Move_ShortR": {"ledge_hand_move_r": WALL_LEAD, "ledge_hand_move_l": WALL_TRAIL},
    "P_Player_Ledge_Move_ShortL_Wallless": {"ledge_hand_move_l": WLLESS_LEAD, "ledge_hand_move_r": WLLESS_TRAIL},
    "P_Player_Ledge_Move_ShortR_Wallless": {"ledge_hand_move_r": WLLESS_LEAD, "ledge_hand_move_l": WLLESS_TRAIL},
}
result = {}
for name, curves in FIXES.items():
    entry = {}
    try:
        seq = unreal.load_asset(BASE + name)
        nf = unreal.AnimationLibrary.get_num_frames(seq)
        dur = unreal.AnimationLibrary.get_sequence_length(seq)
        fps = nf / dur
        for cname, keys in curves.items():
            times = [t for t, _ in keys]
            values = [v for _, v in keys]
            fkeys = [int(round(t * fps)) for t in times]
            if len(set(fkeys)) != len(fkeys):
                entry[cname] = "SKIP dup frames %s" % fkeys
                continue
            try:
                unreal.AnimationLibrary.remove_curve(seq, cname)
            except Exception:
                pass
            unreal.AnimationLibrary.add_curve(seq, cname)
            unreal.AnimationLibrary.add_float_curve_keys(seq, cname, times, values)
            rt, rv = unreal.AnimationLibrary.get_float_keys(seq, cname)
            entry[cname] = [[round(a, 3), round(b, 3)] for a, b in zip(rt, rv)]
        try:
            unreal.EditorAssetLibrary.checkout_asset(BASE + name)
        except Exception:
            pass
        pkg = seq.get_outermost()
        ok = unreal.EditorLoadingAndSavingUtils.save_packages([pkg], only_dirty=False)
        entry["save"] = bool(ok)
    except Exception:
        import traceback
        entry["error"] = traceback.format_exc()
    result[name] = entry
with open(OUT, "w") as fp:
    json.dump(result, fp, indent=1)
print("LEDGE_MOVE_CURVES_DONE")
