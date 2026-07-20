# LedgeClimbing 전 시퀀스 손/발 본 속도 프로파일 원시 덤프 (에디터 py 전용)
# 측정과 판정을 분리 — 이 파일은 순수 측정만. 창 판정은 derive_windows.py 에서 (재측정 없이 반복 튜닝)
# 출력: bone_profiles.json {anim: {"dur":float, "bones":{bone:[speed,...]}, "times":[t,...]}}
import unreal, json, os, traceback

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bone_profiles.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
BONES = ["hand_l", "hand_r", "ball_l", "ball_r", "foot_l", "foot_r"]
try:
    OPTS = unreal.AnimPoseEvaluationOptions()
except Exception:
    OPTS = None

assets = sorted(set(a.split(".")[0] for a in unreal.EditorAssetLibrary.list_assets(DIR, recursive=False, include_folder=False)
                    if a.split("/")[-1].startswith("P_Player_Ledge")))
data = {}
if os.path.exists(OUT):
    try:
        data = json.load(open(OUT))
    except Exception:
        data = {}
n = 0
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
        times, prof, prev = [], {b: [] for b in BONES}, {}
        for f in range(nf + 1):
            t = min(f * step, dur)
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, t, OPTS)
            first = not prev
            for b in BONES:
                try:
                    loc = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
                except Exception:
                    continue
                if b in prev:
                    prof[b].append(round(float((loc - prev[b]).length() / step), 1))
                prev[b] = loc
            if not first:
                times.append(round(t, 3))
        data[nm] = {"dur": round(dur, 3), "times": times,
                    "bones": {b: v for b, v in prof.items() if v}}
    except Exception:
        data[nm] = {"error": traceback.format_exc()[-200:]}
    n += 1
    if n % 10 == 0:
        json.dump(data, open(OUT, "w"))
json.dump(data, open(OUT, "w"))
print("PROFILES_DONE %d" % len(data))
