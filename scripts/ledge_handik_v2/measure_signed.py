# 발/손의 '몸 기준 전후 속도' 부호 프로파일 실측 (에디터 py 전용)
# 배경: in-place 애님에선 벽을 짚고 있는 발도 애님공간에서 캐릭터 속도만큼 뒤로 흐른다.
#       → 속도 '크기' 문턱으로는 이탈 순간을 못 찾는다 (2026-07-20 실측 확인)
# 신호: v_rel = (본속도 - 펠비스속도) 를 이동축(펠비스 진행방향)에 투영한 **부호값**
#       짚음 = 음수(뒤로 흐름) / 이탈·스윙 = 양수(앞으로). 부호 반전 = 릴리즈/플랜트 경계
# 출력: signed_profiles.json {anim:{dur, times, bones:{bone:[signed,...]}}}
import unreal, json, os, traceback

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/signed_profiles.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
BONES = ["hand_l", "hand_r", "ball_l", "ball_r"]
try:
    OPTS = unreal.AnimPoseEvaluationOptions()
except Exception:
    OPTS = None


def loc(pose, b):
    return unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation


data = {}
if os.path.exists(OUT):
    try:
        data = json.load(open(OUT))
    except Exception:
        data = {}

assets = sorted(set(a.split(".")[0] for a in unreal.EditorAssetLibrary.list_assets(DIR, recursive=False, include_folder=False)
                    if a.split("/")[-1].startswith("P_Player_Ledge")))
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
        times, prof = [], {b: [] for b in BONES}
        prev = {}
        for f in range(nf + 1):
            t = min(f * step, dur)
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, t, OPTS)
            cur = {"pelvis": loc(pose, "pelvis")}
            for b in BONES:
                try:
                    cur[b] = loc(pose, b)
                except Exception:
                    pass
            if prev:
                pv = (cur["pelvis"] - prev["pelvis"]) / step      # 몸 속도
                pv.z = 0.0
                axis = pv.normal() if pv.length() > 1.0 else unreal.Vector(0, 0, 0)
                for b in BONES:
                    if b not in cur or b not in prev:
                        continue
                    bv = (cur[b] - prev[b]) / step
                    bv.z = 0.0
                    rel = bv - pv                                  # 몸 기준 상대속도
                    prof[b].append(round(float(rel.x * axis.x + rel.y * axis.y), 1))  # 진행축 투영(부호)
                times.append(round(t, 3))
            prev = cur
        data[nm] = {"dur": round(dur, 3), "times": times, "bones": {b: v for b, v in prof.items() if v}}
    except Exception:
        data[nm] = {"error": traceback.format_exc()[-200:]}
    n += 1
    if n % 10 == 0:
        json.dump(data, open(OUT, "w"))
json.dump(data, open(OUT, "w"))
print("SIGNED_DONE %d" % len(data))
