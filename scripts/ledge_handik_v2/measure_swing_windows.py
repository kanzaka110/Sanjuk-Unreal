# LedgeClimbing 전 시퀀스 손/발 스윙창 실측 (에디터 py 전용)
# 문제: 고정 속도문턱은 못 씀 — in-place 애님은 그립 중에도 캐릭터속도(~110)로 관측되고
#       루트모션 애님은 그립 중 ~0. (README v8 '자동창검출 폐기'의 원인)
# 해법: 애님별·본별 적응 문턱 — thr = median + RATIO*(max-median), 피크 포함 연속구간을 스윙으로.
# 출력: swing_windows.json {anim: {bone: [start,end] or None, ...}}
import unreal, json, os, traceback

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/swing_windows.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
BONES = ["hand_l", "hand_r", "ball_l", "ball_r"]
RATIO = 0.40
try:
    OPTS = unreal.AnimPoseEvaluationOptions()
except Exception:
    OPTS = None


def median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def window(samples):
    """samples=[(t,speed)] → (start,end) 스윙구간 or None"""
    if len(samples) < 5:
        return None
    sp = [s for _, s in samples]
    mx = max(sp)
    md = median(sp)
    if mx < 40.0 or mx - md < 25.0:      # 정지/등속 = 스윙 없음
        return None
    thr = md + RATIO * (mx - md)
    pi = sp.index(mx)
    i = pi
    while i > 0 and sp[i - 1] >= thr:
        i -= 1
    j = pi
    while j < len(sp) - 1 and sp[j + 1] >= thr:
        j += 1
    start = samples[max(i - 1, 0)][0]
    end = samples[min(j + 1, len(samples) - 1)][0]
    if end - start < 0.03:
        return None
    return (round(start, 3), round(end, 3))


assets = []
for off in (0, 100):
    r = unreal.EditorAssetLibrary.list_assets(DIR, recursive=False, include_folder=False)
    assets = [a.split(".")[0] for a in r]
    break
assets = sorted(set(a for a in assets if a.split("/")[-1].startswith("P_Player_Ledge")))

data = {}
if os.path.exists(OUT):
    try:
        data = json.load(open(OUT))
    except Exception:
        data = {}
done = 0
for path in assets:
    nm = path.split("/")[-1]
    if nm in data:
        continue
    e = {}
    try:
        seq = unreal.load_asset(path)
        if not isinstance(seq, unreal.AnimSequence):
            continue
        dur = float(unreal.AnimationLibrary.get_sequence_length(seq))
        nf = int(unreal.AnimationLibrary.get_num_frames(seq))
        step = dur / max(nf, 1)
        prof = {b: [] for b in BONES}
        prev = {}
        for f in range(nf + 1):
            t = min(f * step, dur)
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, t, OPTS)
            for b in BONES:
                try:
                    loc = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
                except Exception:
                    continue
                if b in prev:
                    prof[b].append((round(t, 3), float((loc - prev[b]).length() / step)))
                prev[b] = loc
        e = {b: window(v) for b, v in prof.items()}
        e["dur"] = round(dur, 3)
    except Exception:
        e["error"] = traceback.format_exc()[-200:]
    data[nm] = e
    done += 1
    if done % 10 == 0:
        json.dump(data, open(OUT, "w"))
json.dump(data, open(OUT, "w"))
print("MEASURE_DONE %d" % len(data))
