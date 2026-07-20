# 모디파이어 "창 자동검출" 버튼 훅 (에디터 py — BP의 ExecutePythonCommand 가 호출)
# 동작: bAutoDetectRequest=true 인 AM_SBLedgeIK 인스턴스를 가진 시퀀스를 찾아
#       ① 본 속도 프로파일 실측 ② 창 판정(derive 로직 동일) ③ 파라미터 기록 ④ 플래그 해제
#   ※ 선택(selection)에 의존하지 않는다 — 버튼이 켠 플래그가 대상 지정자
# 결과 로그: auto_detect_result.json
import unreal, json, traceback

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/auto_detect_result.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
BONES = {"hand_l": "hand", "hand_r": "hand", "ball_l": "foot", "ball_r": "foot"}
PARAM = {"hand_l": ("HandMoveStartL", "HandMoveEndL", "HandMove2StartL", "HandMove2EndL"),
         "hand_r": ("HandMoveStartR", "HandMoveEndR", "HandMove2StartR", "HandMove2EndR"),
         "ball_l": ("FootMoveStartL", "FootMoveEndL", "FootMove2StartL", "FootMove2EndL"),
         "ball_r": ("FootMoveStartR", "FootMoveEndR", "FootMove2StartR", "FootMove2EndR")}
# 판정 노브 — derive_windows2.py 와 동일하게 유지할 것
RATIO = {"hand": 0.18, "foot": 0.32}
PAD = {"hand": (-0.067, 0.033), "foot": (-0.017, 0.033)}
LOCAL, MIN_START, MIN_PEAK, MIN_SPAN = 0.5, 0.08, 60.0, 25.0
SECOND_MIN, GAP = 0.55, 0.22
try:
    OPTS = unreal.AnimPoseEvaluationOptions()
except Exception:
    OPTS = None


def med(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def one(times, sp, kind, mask):
    cand = [(sp[i], i) for i in range(len(sp)) if not mask[i]]
    if len(cand) < 5:
        return None, 0.0
    peak, pi = max(cand)
    base = med([sp[i] for i in range(len(sp)) if abs(times[i] - times[pi]) <= LOCAL])
    if peak < MIN_PEAK or peak - base < MIN_SPAN:
        return None, peak
    thr = base + RATIO[kind] * (peak - base)
    i = pi
    while i > 0 and sp[i - 1] >= thr and not mask[i - 1]:
        i -= 1
    j = pi
    while j < len(sp) - 1 and sp[j + 1] >= thr and not mask[j + 1]:
        j += 1
    s = max(MIN_START, round(times[max(i - 1, 0)] + PAD[kind][0], 3))
    e = round(times[j] + PAD[kind][1], 3)
    for x in range(max(i - 1, 0), min(j + 1, len(sp) - 1) + 1):
        mask[x] = True
    return (None if e - s < 0.05 else (s, e)), peak


def windows(seq):
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
                prof[b].append(float((loc - prev[b]).length() / step))
            prev[b] = loc
        if not first:
            times.append(round(t, 3))
    out = {}
    for b, kind in BONES.items():
        sp = prof.get(b) or []
        if not sp:
            out[b] = (None, None)
            continue
        mask = [False] * len(sp)
        w1, p1 = one(times, sp, kind, mask)
        w2 = None
        if w1:
            w1 = (w1[0], round(min(w1[1], dur), 3))
            cand, p2 = one(times, sp, kind, mask)
            if cand:
                cand = (cand[0], round(min(cand[1], dur), 3))
                far = cand[0] >= w1[1] + GAP or cand[1] + GAP <= w1[0]
                if p2 >= p1 * SECOND_MIN and far:
                    w2 = cand
        out[b] = (w1, w2)
    return out, dur


res = {"processed": [], "error": {}}
try:
    for path in unreal.EditorAssetLibrary.list_assets(DIR, recursive=False, include_folder=False):
        p = path.split(".")[0]
        try:
            # find_asset = 메모리에 로드된 것만 (일괄 적용 시 전체 로드 방지 — O(n^2) 회피)
            seq = unreal.find_asset(p)
            if not isinstance(seq, unreal.AnimSequence):
                continue
            inst = None
            for a in (seq.get_editor_property("asset_user_data") or []):
                if a and "AnimationModifiers" in str(a.get_class().get_name()):
                    for i in (a.get_editor_property("animation_modifier_instances") or []):
                        if i and "SBLedge" in str(i.get_class().get_name()):
                            inst = i
            if inst is None or not bool(inst.get_editor_property("bAutoDetectRequest")):
                continue
            w, dur = windows(seq)
            vals = {}
            for b, (w1, w2) in w.items():
                s1, e1, s2, e2 = PARAM[b]
                vals[s1] = w1[0] if w1 else 0.0
                vals[e1] = w1[1] if w1 else 0.0
                vals[s2] = w2[0] if w2 else 0.0
                vals[e2] = w2[1] if w2 else 0.0
            ends = [w[b][0][1] for b in ("hand_l", "hand_r") if w[b][0]]
            if ends:
                base = max(ends)
                for k, d in (("PelvisSpringStart", 0.05), ("PelvisSpringFull", 0.20),
                             ("PelvisSpringHoldEnd", 0.55), ("PelvisSpringEnd", 0.90)):
                    vals[k] = round(min(base + d, dur), 3)
            for k, v in vals.items():
                inst.set_editor_property(k, float(v))
            inst.set_editor_property("bAutoDetectRequest", False)
            seq.modify()   # 저장은 적용 흐름에 맡긴다 (OnApply 중 save_packages 는 트랜잭션 충돌 위험)
            res["processed"].append({"anim": p.split("/")[-1], "values": {k: round(v, 3) for k, v in vals.items()}})
        except Exception:
            res["error"][p.split("/")[-1]] = traceback.format_exc()[-200:]
except Exception:
    res["fatal"] = traceback.format_exc()[-300:]

with open(OUT, "w") as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
print("AUTO_DETECT_DONE processed=%d err=%d" % (len(res["processed"]), len(res["error"])))
