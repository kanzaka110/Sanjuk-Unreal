# MoveToIdle_Wallless_L/R 펠비스 Z 정합 (2026-07-21, 유저 요청)
#
# 실측 단차: Short끝 82.7 -> MoveToIdle시작 90.9 (+8.2cm) = "쓰윽" 상승의 정체
#            MoveToIdle_R 끝 87.7 vs Idle 84.9 (+2.9cm) = 2차 단차
# 수정: 머리 = Short끝(82.7)에서 출발해 18프레임(0.6s) 스무스스텝으로 원궤적 복귀
#       꼬리 = 마지막 12프레임에 걸쳐 Idle 시작(84.89)으로 수렴
#       Z만 변경. 회전/XY/스케일 불변. Short/Idle 은 건드리지 않음.
# 백업: movetoidle_pelvis_backup.json (pos/rot 풀 트랙)
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/fix_movetoidle.json"
BAK = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/movetoidle_pelvis_backup.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
SHORT_END_Z = 82.70    # Move_ShortL/R_Wallless 끝 실측 (82.69 / 82.72)
IDLE_Z = 84.89         # Idle_Wallless 시작 실측
HEAD_FRAMES = 18       # 0.6s @30fps
TAIL_FRAMES = 12       # 0.4s
log = {}
bak = {}


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


for nm in ("P_Player_Ledge_MoveToIdle_Wallless_L", "P_Player_Ledge_MoveToIdle_Wallless_R"):
    try:
        seq = unreal.load_asset(DIR + nm)
        nf = int(unreal.AnimationLibrary.get_num_frames(seq))
        nkeys = nf + 1
        pos, rot = [], []
        for f in range(nkeys):
            t = unreal.AnimationLibrary.get_bone_pose_for_frame(seq, "pelvis", f, False)
            pos.append(t.translation)
            rot.append(t.rotation)
        bak[nm] = {"pos": [[round(p.x, 4), round(p.y, 4), round(p.z, 4)] for p in pos],
                   "rot": [[round(q.x, 6), round(q.y, 6), round(q.z, 6), round(q.w, 6)] for q in rot]}

        orig_z = [float(p.z) for p in pos]
        new_z = list(orig_z)
        # 머리: Short끝에서 출발해 HEAD_FRAMES 에 걸쳐 원궤적 복귀
        off_head = SHORT_END_Z - orig_z[0]
        for f in range(min(HEAD_FRAMES, nkeys)):
            new_z[f] = orig_z[f] + off_head * (1.0 - smooth(f / float(HEAD_FRAMES)))
        # 꼬리: 마지막 TAIL_FRAMES 에 걸쳐 Idle 로 수렴
        off_tail = IDLE_Z - orig_z[-1]
        for f in range(max(0, nkeys - TAIL_FRAMES), nkeys):
            w = smooth((f - (nkeys - 1 - TAIL_FRAMES)) / float(TAIL_FRAMES))
            new_z[f] = new_z[f] + off_tail * w

        new_pos = [unreal.Vector(p.x, p.y, new_z[i]) for i, p in enumerate(pos)]
        scales = [unreal.Vector(1.0, 1.0, 1.0) for _ in range(nkeys)]
        ctrl = seq.get_editor_property("controller")
        ok = ctrl.set_bone_track_keys("pelvis", new_pos, rot, scales)
        saved = bool(unreal.EditorAssetLibrary.save_asset(DIR + nm, only_if_is_dirty=False))
        log[nm] = {"set": bool(ok), "saved": saved, "keys": nkeys,
                   "head": [round(orig_z[0], 2), round(new_z[0], 2)],
                   "tail": [round(orig_z[-1], 2), round(new_z[-1], 2)]}
    except Exception as e:
        import traceback
        log[nm] = {"error": traceback.format_exc()[-300:]}

json.dump(bak, open(BAK, "w"))
json.dump(log, open(OUT, "w"), indent=1)
print("FIX_MOVETOIDLE " + json.dumps(log, ensure_ascii=False)[:400])
