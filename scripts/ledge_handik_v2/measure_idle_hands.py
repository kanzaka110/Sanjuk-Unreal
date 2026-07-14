import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/idle_hands.json"
BASE = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
TARGETS = {"wall": "P_Player_Ledge_Idle", "wallless": "P_Player_Ledge_Idle_Wallless"}
result = {}
try:
    opts = unreal.AnimPoseEvaluationOptions()
    for mode, name in TARGETS.items():
        seq = unreal.load_asset(BASE + name)
        if seq is None:
            result[mode] = "LOAD_FAIL"
            continue
        nf = unreal.AnimationLibrary.get_num_frames(seq)
        dur = unreal.AnimationLibrary.get_sequence_length(seq)
        # 루프 애님이라 여러 프레임 평균 (호흡 스웨이 상쇄)
        entry = {}
        for bone in ("hand_l", "hand_r"):
            acc = unreal.Vector(0, 0, 0)
            n = 0
            for f in range(0, int(nf), max(1, int(nf) // 10)):
                pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, dur * f / nf, opts)
                loc = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD).translation
                acc = acc + loc
                n += 1
            avg = acc / n
            entry[bone] = [round(avg.x, 2), round(avg.y, 2), round(avg.z, 2)]
        result[mode] = entry
except Exception:
    import traceback
    result["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(result, fp, indent=1)
print("IDLE_HANDS_DONE")
