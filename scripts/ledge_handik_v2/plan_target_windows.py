# TARGET 애님 창 산출 계획서 (로컬, 쓰기 없음) — 적용 전 검토용 표 생성
#
# 캘리브레이션 결과(유저 수작업 33종 기준):
#   손: thr 110 / min_len 0.05 / gap 0.20 / pad(0, +0.033)  → 2프레임 이내 74%, 산출실패 0
#   발: 다섯 신호 전부 실패(2프레임 이내 ~50%) → 수치 자동화 포기. 벽 조합 규칙만 적용.
# 벽 규칙(33종 예외 없음): WalllessToWallless → 0~0 / WalllessTo* → 시작 0 / *ToWallless → 끝 = dur
import json

PROF = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bone_profiles.json"
DUMP = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_params_dump.json"
PRES = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/preserve_list.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/target_plan.json"
H = {"thr": 110, "min_len": 0.05, "gap": 0.20, "pad": (0.0, 0.033)}

prof = json.load(open(PROF))
dump = json.load(open(DUMP))["anims"]
preserve = set(json.load(open(PRES)) + ["P_Player_Ledge_Move_ShortL_Wallless", "P_Player_Ledge_Move_ShortR_Wallless"])


def classify(nm):
    s = nm.replace("P_Player_Ledge_", "")
    if s.startswith(("ToLadder", "End")) or "BackwardJump" in s:
        return "이탈"
    if s.startswith("Idle"):
        return "정지"
    return "이동"


def wall_combo(nm):
    s = nm.replace("P_Player_Ledge_", "")
    for c in ("WalllessToWallless", "WalllessToWall", "WallToWallless", "WallToWall"):
        if s.endswith(c):
            return c
    if s.endswith("Wallless"):
        return "(Wallless)"
    return "(기타)"


def segments(times, v, thr, ml, gap):
    out, i, n = [], 0, min(len(v), len(times))
    while i < n:
        if v[i] > thr:
            j = i
            while j + 1 < n and v[j + 1] > thr:
                j += 1
            out.append([times[i], times[j]])
            i = j + 1
        else:
            i += 1
    if not out:
        return []
    m = [out[0]]
    for s in out[1:]:
        if s[0] - m[-1][1] <= gap:
            m[-1][1] = s[1]
        else:
            m.append(s)
    return [s for s in m if s[1] - s[0] >= ml]


plan = {}
for nm in sorted(dump):
    if nm in preserve:
        continue
    kind = classify(nm)
    u = dump[nm]
    dur = u["dur"]
    rec = {"class": kind, "wall": wall_combo(nm), "dur": dur, "hand": {}, "foot": {}}
    if kind == "이동" and nm in prof and not prof[nm].get("error"):
        p = prof[nm]
        for bone, ks, ke in (("hand_l", "HandMoveStartL", "HandMoveEndL"),
                             ("hand_r", "HandMoveStartR", "HandMoveEndR")):
            if bone not in p.get("bones", {}):
                continue
            segs = segments(p["times"], p["bones"][bone], H["thr"], H["min_len"], H["gap"])
            if not segs:
                rec["hand"][bone] = {"cur": [u.get(ks), u.get(ke)], "new": None, "note": "산출실패"}
                continue
            a, b = max(segs, key=lambda x: x[1] - x[0])
            rec["hand"][bone] = {"cur": [u.get(ks), u.get(ke)],
                                 "new": [round(max(0.0, a + H["pad"][0]), 3), round(min(b + H["pad"][1], dur), 3)]}
    # 발: 벽 규칙만
    wc = rec["wall"]
    for side, ks, ke in (("l", "FootMoveStartL", "FootMoveEndL"), ("r", "FootMoveStartR", "FootMoveEndR")):
        cur = [u.get(ks), u.get(ke)]
        new, note = None, ""
        if kind != "이동":
            note = "창 미사용(" + kind + ")"
        elif wc == "WalllessToWallless" or wc == "(Wallless)":
            new, note = [0.0, 0.0], "벽없음 → 발 IK 끔"
        elif wc == "WallToWallless":
            new, note = [cur[0], round(dur, 3)], "도착 벽없음 → 끝=dur"
        elif wc == "WalllessToWall":
            new, note = [0.0, cur[1]], "출발 벽없음 → 시작=0"
        else:
            note = "수작업 필요(WallToWall)"
        rec["foot"][side] = {"cur": cur, "new": new, "note": note}
    plan[nm] = rec

json.dump(plan, open(OUT, "w"), indent=1, ensure_ascii=False)

move = {k: v for k, v in plan.items() if v["class"] == "이동"}
skip = {k: v for k, v in plan.items() if v["class"] != "이동"}
hand_chg = sum(1 for v in move.values() for b in v["hand"].values() if b.get("new"))
foot_chg = sum(1 for v in move.values() for b in v["foot"].values() if b.get("new") is not None)
print("TARGET %d개 (이동 %d / 이탈·정지 %d = 창 미사용)" % (len(plan), len(move), len(skip)))
print("손 창 산출 %d건 / 발 벽규칙 적용 %d건" % (hand_chg, foot_chg))
print("PRESERVE %d종은 계획에서 제외됨" % len(preserve))
print()
byw = {}
for v in move.values():
    byw[v["wall"]] = byw.get(v["wall"], 0) + 1
print("벽 조합별 이동 애님 수:", byw)
print()
print("발 수작업 필요(WallToWall):", sum(1 for v in move.values() if v["wall"] == "WallToWall"))
