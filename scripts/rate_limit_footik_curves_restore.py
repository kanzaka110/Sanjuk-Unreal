"""
rate_limit_footik_curves.py 적용분 복원.
dumps/footik_curves/ 의 가장 최근 backup_*.json 으로 두 anim의 curve를 원상태로 set.

실행: PIE 종료 후 UE 에디터 Python 모드에서
  exec(open(r"C:\Dev\Sanjuk-Unreal\scripts\rate_limit_footik_curves_restore.py", encoding="utf-8").read(), {"__name__": "__main__"})
"""
import unreal
import json
import os
import glob

BACKUP_DIR = r"C:\Dev\Sanjuk-Unreal\dumps\footik_curves"
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT


def restore_curve(seq, curve_name, keys):
    try:
        if unreal.AnimationLibrary.does_curve_exist(seq, curve_name, RCT_FLOAT):
            unreal.AnimationLibrary.remove_curve(seq, curve_name)
        unreal.AnimationLibrary.add_curve(seq, curve_name)
        times = [float(t) for t, _ in keys]
        values = [float(v) for _, v in keys]
        unreal.AnimationLibrary.add_float_curve_keys(seq, curve_name, times, values)
        return True
    except Exception as e:
        unreal.log_error(f"  restore fail [{curve_name}]: {e}")
        return False


def main():
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.json")))
    # 빈 backup (curves={}) 은 건너뜀
    files = [f for f in files if json.load(open(f, "r", encoding="utf-8"))
             ["anims"] and any(a.get("curves") for a in json.load(open(f, "r", encoding="utf-8"))["anims"].values())]
    if not files:
        unreal.log_error(f"유효한 백업 없음: {BACKUP_DIR}")
        return
    latest = files[-1]
    unreal.log(f"[BACKUP] {latest}")

    with open(latest, "r", encoding="utf-8") as f:
        backup = json.load(f)

    for anim_path, anim_data in backup["anims"].items():
        seq = unreal.load_asset(anim_path)
        if not seq:
            unreal.log_error(f"[FAIL] load {anim_path}")
            continue
        unreal.log(f"[ANIM] {anim_path}")
        for curve_name, keys in anim_data["curves"].items():
            ok = restore_curve(seq, curve_name, keys)
            unreal.log(f"  [{'OK' if ok else 'FAIL'}] {curve_name}  keys={len(keys)}")
        try:
            unreal.EditorAssetLibrary.save_asset(anim_path)
            unreal.log(f"  [SAVE] {anim_path}")
        except Exception as e:
            unreal.log_error(f"  [SAVE_FAIL] {e}")


if __name__ == "__main__":
    main()
