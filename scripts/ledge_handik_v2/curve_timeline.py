import unreal, json
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/curve_timeline.json"
ANIM = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/P_Player_Ledge_Move_ShortL_Wallless"
log = {}
try:
    seq = unreal.load_asset(ANIM)
    dur = unreal.AnimationLibrary.get_sequence_length(seq)
    log["duration"] = round(dur, 3)
    # 커브 키
    for cname in ("ledge_hand_ik_l", "ledge_hand_ik_r"):
        try:
            times, values = unreal.AnimationLibrary.get_float_keys(seq, cname)
            log[cname] = [[round(t, 3), round(v, 2)] for t, v in zip(times, values)]
        except Exception as e:
            log[cname] = "ERR " + repr(e)[:80]
    # 손 궤적 (0.033s 간격 속도)
    opts = unreal.AnimPoseEvaluationOptions()
    tl = []
    step = 0.033
    prev = {}
    t = 0.0
    while t <= dur + 1e-4:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, min(t, dur), opts)
        row = {"t": round(t, 2)}
        for bone in ("hand_l", "hand_r"):
            loc = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD).translation
            if bone in prev:
                row[bone + "_spd"] = round((loc - prev[bone]).length() / step, 0)
            row[bone + "_y"] = round(loc.y, 1)
            prev[bone] = loc
        tl.append(row)
        t += step
    log["timeline"] = tl
except Exception:
    import traceback
    log["error"] = traceback.format_exc()
with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
