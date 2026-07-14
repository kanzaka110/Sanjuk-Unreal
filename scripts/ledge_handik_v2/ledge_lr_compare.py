# 렛지 좌/우 이동 애님 대칭 분석 — 커브 타이밍 + 손 궤적 + 플랜트엣지 손위치
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ledge_lr_compare.json"
BASE = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
ANIMS = [
    "P_Player_Ledge_Move_ShortL",
    "P_Player_Ledge_Move_ShortR",
    "P_Player_Ledge_Move_ShortL_Wallless",
    "P_Player_Ledge_Move_ShortR_Wallless",
    "P_Player_Ledge_MoveToIdle_L",
    "P_Player_Ledge_MoveToIdle_R",
    "P_Player_Ledge_MoveToIdle_Wallless_L",
    "P_Player_Ledge_MoveToIdle_Wallless_R",
]

def curve_val(keys, t):
    """선형 보간 커브 평가."""
    if not keys:
        return 1.0
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            t0, v0 = keys[i - 1]
            t1, v1 = keys[i]
            if t1 <= t0:
                return v1
            a = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * a
    return keys[-1][1]

result = {}
for name in ANIMS:
    entry = {}
    try:
        seq = unreal.load_asset(BASE + name)
        if seq is None:
            entry["error"] = "load failed"
            result[name] = entry
            continue
        dur = unreal.AnimationLibrary.get_sequence_length(seq)
        nf = unreal.AnimationLibrary.get_num_frames(seq)
        fps = nf / dur
        entry["duration"] = round(dur, 3)
        entry["frames"] = int(nf)
        curves = {}
        for cn in ("ledge_hand_ik_l", "ledge_hand_ik_r"):
            try:
                times, values = unreal.AnimationLibrary.get_float_keys(seq, cn)
                curves[cn] = [[round(t, 3), round(v, 3)] for t, v in zip(times, values)]
            except Exception as e:
                curves[cn] = []
            entry[cn] = curves[cn]
        # 손 궤적 (프레임별, 컴포넌트=WORLD anim space)
        opts = unreal.AnimPoseEvaluationOptions()
        traj = {"hand_l": [], "hand_r": [], "root": []}
        for f in range(int(nf) + 1):
            t = dur * f / max(1, nf)
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, min(t, dur), opts)
            for bone in ("hand_l", "hand_r", "root"):
                loc = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD).translation
                traj[bone].append((round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)))
        # 요약: 손별 시작/끝/이동량, 프레임별 손간 거리
        summ = {}
        for bone in ("hand_l", "hand_r", "root"):
            p0, p1 = traj[bone][0], traj[bone][-1]
            summ[bone + "_start"] = p0
            summ[bone + "_end"] = p1
            summ[bone + "_travel"] = round(((p1[0]-p0[0])**2+(p1[1]-p0[1])**2+(p1[2]-p0[2])**2) ** 0.5, 1)
        spreads = []
        for i in range(len(traj["hand_l"])):
            l, r = traj["hand_l"][i], traj["hand_r"][i]
            spreads.append(round(((l[0]-r[0])**2+(l[1]-r[1])**2+(l[2]-r[2])**2) ** 0.5, 1))
        summ["spread_min"] = min(spreads)
        summ["spread_max"] = max(spreads)
        summ["spread_start"] = spreads[0]
        summ["spread_end"] = spreads[-1]
        entry["summary"] = summ
        entry["spread_per_frame"] = spreads
        # 플랜트/릴리즈 엣지 검출 (0.5 크로싱) + 그 시점 손위치
        edges = {}
        for cn, bone in (("ledge_hand_ik_l", "hand_l"), ("ledge_hand_ik_r", "hand_r")):
            ev = []
            prev = curve_val(curves.get(cn, []), 0.0)
            for f in range(1, int(nf) + 1):
                t = dur * f / nf
                v = curve_val(curves.get(cn, []), t)
                if prev < 0.5 <= v:
                    ev.append({"f": f, "t": round(t, 3), "type": "plant", "pos": traj[bone][f]})
                elif prev >= 0.5 > v:
                    ev.append({"f": f, "t": round(t, 3), "type": "release", "pos": traj[bone][f]})
                prev = v
            edges[cn] = ev
        entry["edges"] = edges
        # 손별 프레임 속도 피크 (플라이트 구간 확인)
        for bone in ("hand_l", "hand_r"):
            sp = []
            for i in range(1, len(traj[bone])):
                a, b = traj[bone][i - 1], traj[bone][i]
                sp.append(round((((b[0]-a[0])**2+(b[1]-a[1])**2+(b[2]-a[2])**2) ** 0.5) * fps, 0))
            entry[bone + "_speed"] = sp
    except Exception:
        import traceback
        entry["error"] = traceback.format_exc()
    result[name] = entry

with open(OUT, "w") as fp:
    json.dump(result, fp, indent=1)
print("LEDGE_LR_COMPARE_DONE")
