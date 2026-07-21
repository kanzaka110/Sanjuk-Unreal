# 렛지 애님 원본 발목(foot 로컬=calf 기준) 회전 범위 실측 — 런타임 probe_ankle.py 값과 대조용
# 목적: PIE 에서 관측된 발목 각도(알파 1 구간 37~107°)가 애님 원본에도 존재하는지 판정.
# 출력: ankle_range.json {anim: {"dur":f, "l":[[r,p,y],...], "r":[...]}}  (프레임별 원시 오일러)
import unreal, json, os, traceback

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ankle_range.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
try:
    OPTS = unreal.AnimPoseEvaluationOptions()
except Exception:
    OPTS = None

assets = sorted(set(a.split(".")[0] for a in unreal.EditorAssetLibrary.list_assets(DIR, recursive=True, include_folder=False)
                   if a.split("/")[-1].startswith("P_Player_Ledge")))
data = {}
if os.path.exists(OUT):
    try:
        data = json.load(open(OUT))
    except Exception:
        data = {}

err = 0
for path in assets:
    nm = path.split("/")[-1]
    if nm in data:
        continue
    try:
        seq = unreal.load_asset(path)
        if not isinstance(seq, unreal.AnimSequence):
            continue
        dur = float(unreal.AnimationLibrary.get_sequence_length(seq))
        nf = int(unreal.AnimationLibrary.get_num_frames(seq))
        step = dur / max(nf, 1)
        rec = {"dur": round(dur, 3), "l": [], "r": []}
        for f in range(nf + 1):
            t = min(f * step, dur)
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, t, OPTS)
            for side, key in (("l", "l"), ("r", "r")):
                try:
                    # LOCAL = 부모(calf) 기준 상대 트랜스폼 → 런타임 calf⁻¹×foot 과 동일 의미
                    xf = unreal.AnimPoseExtensions.get_bone_pose(pose, "foot_" + side, unreal.AnimPoseSpaces.LOCAL)
                except Exception:
                    continue
                q = xf.rotation
                try:
                    rot = q.rotator()
                except Exception:
                    rot = unreal.MathLibrary.quat_rotator(q)
                rec[key].append([round(rot.roll, 1), round(rot.pitch, 1), round(rot.yaw, 1)])
        data[nm] = rec
    except Exception:
        err += 1
        data[nm] = {"error": traceback.format_exc()[-200:]}

with open(OUT, "w") as fp:
    json.dump(data, fp)
print("ANKLE_RANGE_DONE anims=%d err=%d -> %s" % (len(data), err, OUT))
