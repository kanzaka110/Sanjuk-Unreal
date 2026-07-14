# ShortR / ShortR_Wallless 핸드IK 커브를 ShortL 계열(유저 승인 기준)의 미러로 재작성
# 미러 규칙: 우측이동 선행손(hand_r) <- 좌측이동 선행손(hand_l) 커브, 후행손도 교차 복사
# 원본 키 백업: ledge_lr_compare.json (2026-07-14 실측 덤프)
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ledge_fix_shortr.json"
BASE = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"

FIXES = {
    "P_Player_Ledge_Move_ShortR": {
        # ShortL ledge_hand_ik_l (상수 1) 미러
        "ledge_hand_ik_r": [(0.0, 1.0)],
        # ShortL ledge_hand_ik_r 미러 (중복 t=0 키 정리)
        "ledge_hand_ik_l": [(0.0, 1.0), (0.067, 0.5), (0.167, 0.0),
                            (0.467, 0.0), (0.5, 0.259), (0.533, 0.741), (0.567, 1.0)],
    },
    "P_Player_Ledge_Move_ShortR_Wallless": {
        # ShortL_Wallless ledge_hand_ik_l 미러
        "ledge_hand_ik_r": [(0.0, 1.0), (0.067, 1.0), (0.1, 0.3),
                            (0.233, 0.3), (0.267, 1.0)],
        # ShortL_Wallless ledge_hand_ik_r 미러 (+t=0 시작키 명시)
        "ledge_hand_ik_l": [(0.0, 1.0), (0.267, 1.0), (0.3, 0.3),
                            (0.433, 0.3), (0.467, 1.0)],
    },
}

result = {}
for name, curves in FIXES.items():
    entry = {}
    try:
        seq = unreal.load_asset(BASE + name)
        if seq is None:
            entry["error"] = "load failed"
            result[name] = entry
            continue
        nf = unreal.AnimationLibrary.get_num_frames(seq)
        dur = unreal.AnimationLibrary.get_sequence_length(seq)
        fps = nf / dur
        for cname, keys in curves.items():
            times = [t for t, _ in keys]
            values = [v for _, v in keys]
            # 같은 프레임 키 2개 = SetCurveControlKey 어설션 즉사 — 사전 차단
            fkeys = [int(round(t * fps)) for t in times]
            if len(set(fkeys)) != len(fkeys):
                entry[cname] = "SKIP duplicate frames %s" % fkeys
                continue
            try:
                unreal.AnimationLibrary.remove_curve(seq, cname)
            except Exception:
                pass
            unreal.AnimationLibrary.add_curve(seq, cname)
            unreal.AnimationLibrary.add_float_curve_keys(seq, cname, times, values)
            # 재검증 읽기
            rt, rv = unreal.AnimationLibrary.get_float_keys(seq, cname)
            entry[cname] = [[round(t, 3), round(v, 3)] for t, v in zip(rt, rv)]
    except Exception:
        import traceback
        entry["error"] = traceback.format_exc()
    result[name] = entry

with open(OUT, "w") as fp:
    json.dump(result, fp, indent=1)
print("LEDGE_FIX_SHORTR_DONE")
