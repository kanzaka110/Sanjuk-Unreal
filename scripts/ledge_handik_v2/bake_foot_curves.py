# ledge_foot_ik_l/r + ledge_foot_move_l/r 초기 베이크 (FrontBlocked 벽 전용) — v9 Stage 4
# 실측 발 플라이트 창 (2026-07-15, ledge_foot_measure.json 속도 프로파일):
#   ShortL: foot_l 0~0.45s, foot_r 0~0.57s(플랜트 스파이크 f15-16) / ShortR 미러: foot_r 0~0.50, foot_l 0~0.57
# ik커브: 시작 즉시 릴리즈(1->0), 플랜트 시 0->1 (램프 0.1s) / move커브: 창 구간 스무스텝 0->1
# Idle: ik=1 상수, move=0. Wallless는 FrontBlocked=false 게이트라 베이크 불필요.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ledge_foot_curves.json"
BASE = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"


def smoothstep_ramp(t0, t1, up=True):
    # 프레임 정렬 5키 스무스텝 (t0->t1), up=False면 1->0
    ts = [t0, t0 + (t1 - t0) * 0.25, t0 + (t1 - t0) * 0.5, t0 + (t1 - t0) * 0.75, t1]
    vs = [0.0, 0.16, 0.5, 0.84, 1.0]
    if not up:
        vs = [1.0 - v for v in vs]
    return list(zip(ts, vs))


def ik_curve(release_end, plant_start, plant_end):
    # 1 -> (릴리즈) 0 -> (플랜트) 1
    keys = [(0.0, 1.0)] if release_end > 0.05 else []
    keys += smoothstep_ramp(max(0.033, release_end - 0.067), release_end, up=False) if release_end > 0.05 else [(0.0, 1.0), (0.067, 0.0)]
    keys += [(plant_start, 0.0)]
    keys += smoothstep_ramp(plant_start + 0.033, plant_end, up=True)[1:]
    # 시간 오름차순 + 중복 제거
    out, seen = [], set()
    for t, v in sorted(keys):
        ft = round(t * 30)
        if ft in seen:
            continue
        seen.add(ft)
        out.append((t, v))
    return out


# 발별 창: (릴리즈완료, 플랜트시작, 플랜트완료)
SHORT_L = {
    "ledge_foot_ik_l": ik_curve(0.1, 0.35, 0.45),
    "ledge_foot_ik_r": ik_curve(0.1, 0.47, 0.57),
    "ledge_foot_move_l": [(0.0, 0.0)] + smoothstep_ramp(0.067, 0.4)[1:],
    "ledge_foot_move_r": [(0.0, 0.0)] + smoothstep_ramp(0.1, 0.53)[1:],
}
SHORT_R = {
    "ledge_foot_ik_r": ik_curve(0.1, 0.4, 0.5),
    "ledge_foot_ik_l": ik_curve(0.1, 0.47, 0.57),
    "ledge_foot_move_r": [(0.0, 0.0)] + smoothstep_ramp(0.067, 0.45)[1:],
    "ledge_foot_move_l": [(0.0, 0.0)] + smoothstep_ramp(0.1, 0.53)[1:],
}
IDLE = {
    "ledge_foot_ik_l": [(0.0, 1.0)],
    "ledge_foot_ik_r": [(0.0, 1.0)],
    "ledge_foot_move_l": [(0.0, 0.0)],
    "ledge_foot_move_r": [(0.0, 0.0)],
}
FIXES = {
    "P_Player_Ledge_Move_ShortL": SHORT_L,
    "P_Player_Ledge_Move_ShortR": SHORT_R,
    "P_Player_Ledge_Idle": IDLE,
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
            times = [min(t, dur) for t, _ in keys]
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
print("FOOT_CURVES_DONE")
