"""
PC_01 Foot IK On->Off jump 해결.
DisableFootLock_L/R, DisableFootIK_L/R curve에 rate-limit + frame 0/last 키 강제.

대상: P_Player_Run_Stop_F_{Lfoot, Rfoot}
실행: PIE 종료 후 UE 에디터 Python 모드에서
  exec(open(r"C:\Dev\Sanjuk-Unreal\scripts\rate_limit_footik_curves.py", encoding="utf-8").read(), {"__name__": "__main__"})

알고리즘:
  1. abs(인접 키 차) > MAX_STEP 이면 ceil(delta/MAX_STEP) 개 중간 키 lerp 삽입
  2. 첫 키 time>0.001 -> (0.0, 첫키.value) 삽입
  3. 끝 키 time<duration-0.001 -> (duration, 끝키.value) 삽입

API (UE 5.7 SB2 확정):
  read : unreal.AnimationLibrary.get_float_keys(seq, name) -> (times[], values[])
  write: remove_curve -> add_curve -> add_float_curve_keys

백업: dumps/footik_curves/backup_<timestamp>.json
복원: scripts/rate_limit_footik_curves_restore.py (자동 갱신)
"""
import unreal
import json
import os
import math
from datetime import datetime

ANIMS = [
    "/Game/Art/Character/PC/PC_01/Animation/Body/Run/P_Player_Run_Stop_F_Lfoot",
    "/Game/Art/Character/PC/PC_01/Animation/Body/Run/P_Player_Run_Stop_F_Rfoot",
]
CURVES = ["DisableFootLock_L", "DisableFootLock_R", "DisableFootIK_L", "DisableFootIK_R"]
MAX_STEP = 0.2
EPS = 0.001
BACKUP_DIR = r"C:\Dev\Sanjuk-Unreal\dumps\footik_curves"
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT


def rate_limit(keys, max_step):
    if len(keys) < 2:
        return list(keys)
    new = [keys[0]]
    for i in range(len(keys) - 1):
        t1, v1 = keys[i]
        t2, v2 = keys[i + 1]
        delta = abs(v2 - v1)
        if delta > max_step:
            n = int(math.ceil(delta / max_step))
            for s in range(1, n):
                f = s / n
                new.append((t1 + (t2 - t1) * f, v1 + (v2 - v1) * f))
        new.append((t2, v2))
    return new


def force_endpoints(keys, duration):
    if not keys:
        return keys
    out = list(keys)
    if out[0][0] > EPS:
        out.insert(0, (0.0, out[0][1]))
    if out[-1][0] < duration - EPS:
        out.append((duration, out[-1][1]))
    return out


def max_delta(keys):
    if len(keys) < 2:
        return 0.0
    return max(abs(keys[i + 1][1] - keys[i][1]) for i in range(len(keys) - 1))


def get_float_keys(seq, curve_name):
    if not unreal.AnimationLibrary.does_curve_exist(seq, curve_name, RCT_FLOAT):
        return []
    try:
        times, values = unreal.AnimationLibrary.get_float_keys(seq, curve_name)
        return [(float(t), float(v)) for t, v in zip(times, values)]
    except Exception as e:
        unreal.log_warning(f"  read fail [{curve_name}]: {e}")
        return []


def write_float_keys(seq, curve_name, keys):
    try:
        if unreal.AnimationLibrary.does_curve_exist(seq, curve_name, RCT_FLOAT):
            unreal.AnimationLibrary.remove_curve(seq, curve_name)
        unreal.AnimationLibrary.add_curve(seq, curve_name)
        times = [float(t) for t, _ in keys]
        values = [float(v) for _, v in keys]
        unreal.AnimationLibrary.add_float_curve_keys(seq, curve_name, times, values)
        return True
    except Exception as e:
        unreal.log_error(f"  write fail [{curve_name}]: {e}")
        return False


def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = {"timestamp": ts, "max_step": MAX_STEP, "anims": {}}
    report_rows = []

    for anim_path in ANIMS:
        seq = unreal.load_asset(anim_path)
        if not seq:
            unreal.log_error(f"[FAIL] load {anim_path}")
            continue
        duration = float(seq.get_play_length())
        unreal.log(f"[ANIM] {anim_path}  duration={duration:.4f}")
        anim_data = {"duration": duration, "curves": {}}

        for curve_name in CURVES:
            before = get_float_keys(seq, curve_name)
            if not before:
                unreal.log_warning(f"  [SKIP] {curve_name}: no keys")
                continue
            anim_data["curves"][curve_name] = before
            md_before = max_delta(before)

            processed = rate_limit(before, MAX_STEP)
            processed = force_endpoints(processed, duration)
            md_after = max_delta(processed)

            ok = write_float_keys(seq, curve_name, processed)
            tag = "OK" if ok else "WRITE_FAIL"
            report_rows.append({
                "anim": anim_path.split("/")[-1],
                "curve": curve_name,
                "before": len(before),
                "after": len(processed),
                "md_before": round(md_before, 3),
                "md_after": round(md_after, 3),
                "tag": tag,
            })
            unreal.log(
                f"  [{tag}] {curve_name:20s} keys {len(before):3d}->{len(processed):3d}  "
                f"max_delta {md_before:.3f}->{md_after:.3f}"
            )

        backup["anims"][anim_path] = anim_data
        try:
            unreal.EditorAssetLibrary.save_asset(anim_path)
            unreal.log(f"  [SAVE] {anim_path}")
        except Exception as e:
            unreal.log_error(f"  [SAVE_FAIL] {anim_path}: {e}")

    backup_file = os.path.join(BACKUP_DIR, f"backup_{ts}.json")
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2)

    unreal.log("=" * 70)
    unreal.log(f"BACKUP: {backup_file}")
    unreal.log(f"{'anim':32s} {'curve':20s} {'keys':>11s}  {'max_delta':>20s} tag")
    for r in report_rows:
        keys_str = f"{r['before']:3d}->{r['after']:3d}"
        md_str = f"{r['md_before']:.3f}->{r['md_after']:.3f}"
        unreal.log(
            f"{r['anim']:32s} {r['curve']:20s} {keys_str:>11s}  {md_str:>20s} {r['tag']}"
        )
    unreal.log("=" * 70)
    unreal.log("RESTORE: scripts/rate_limit_footik_curves_restore.py 로 복원")


if __name__ == "__main__":
    main()
