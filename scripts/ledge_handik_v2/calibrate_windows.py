# 판정식 역보정 (로컬) — 유저 수작업 33종을 ground truth 로 삼아 RATIO/PAD/LOCAL 그리드 서치
#
# 배경: derive_windows.py 의 창 판정은 임의 상수(RATIO 0.25 / PAD / LOCAL 0.5)로 굴러왔다.
#       유저가 33종을 수작업 튜닝했으므로, 그 값을 재현하는 상수를 역으로 찾으면
#       나머지 애님에도 '유저 감각'을 옮길 수 있다.
#
# 입력: bone_profiles.json (본 속도 실측, 2026-07-20) + mod_params_dump.json (현재 인스턴스 값)
# 출력: calibration.json  — 조합별 오차표 + 최적값
import json, itertools

PROF = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bone_profiles.json"
DUMP = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_params_dump.json"
PRES = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/preserve_list.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/calibration.json"
MIN_PEAK, MIN_SPAN = 60.0, 25.0

prof = json.load(open(PROF))
dump = json.load(open(DUMP))["anims"]
preserve = json.load(open(PRES))
preserve += ["P_Player_Ledge_Move_ShortL_Wallless", "P_Player_Ledge_Move_ShortR_Wallless"]


def derive(times, sp, ratio, local, pad):
    if len(sp) < 5:
        return None
    peak = max(sp)
    pi = sp.index(peak)
    lo = sorted(sp[i] for i in range(len(sp)) if abs(times[i] - times[pi]) <= local)
    base = lo[len(lo) // 2] if len(lo) % 2 else 0.5 * (lo[len(lo) // 2 - 1] + lo[len(lo) // 2])
    if peak < MIN_PEAK or peak - base < MIN_SPAN:
        return None
    thr = base + ratio * (peak - base)
    i = pi
    while i > 0 and sp[i - 1] >= thr:
        i -= 1
    j = pi
    while j < len(sp) - 1 and sp[j + 1] >= thr:
        j += 1
    s = max(0.0, times[max(i - 1, 0)] + pad[0])
    e = times[j] + pad[1]
    return None if e - s < 0.05 else (round(s, 3), round(e, 3))


# 비교쌍 구성: (애님, 본, 유저값start, 유저값end)
PAIRS = [("hand_l", "HandMoveStartL", "HandMoveEndL"), ("hand_r", "HandMoveStartR", "HandMoveEndR"),
         ("ball_l", "FootMoveStartL", "FootMoveEndL"), ("ball_r", "FootMoveStartR", "FootMoveEndR")]
cases = {"hand": [], "foot": []}
for nm in preserve:
    if nm not in prof or nm not in dump or prof[nm].get("error"):
        continue
    p, u = prof[nm], dump[nm]
    dur = u["dur"]
    for bone, ks, ke in PAIRS:
        if bone not in p.get("bones", {}):
            continue
        gs, ge = u.get(ks), u.get(ke)
        if gs is None or ge is None:
            continue
        # 규칙 케이스(벽 조합)는 판정식 대상이 아니므로 제외:
        #   0~0 (발 IK 없음) / end==dur (도착 후 유지) / start>end (특수)
        if abs(gs) < 1e-6 and abs(ge) < 1e-6:
            continue
        if abs(ge - dur) < 0.02 or gs >= ge:
            continue
        kind = "hand" if bone.startswith("hand") else "foot"
        cases[kind].append((nm, bone, gs, ge, p["times"], p["bones"][bone]))

res = {"case_count": {k: len(v) for k, v in cases.items()}, "grid": {}, "best": {}}
RATIOS = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]
LOCALS = [0.3, 0.5, 0.8]
PADS_S = [-0.10, -0.067, -0.033, 0.0, 0.033]
PADS_E = [0.0, 0.033, 0.067, 0.10, 0.15]

for kind in ("hand", "foot"):
    rows = []
    for ratio, local, ps, pe in itertools.product(RATIOS, LOCALS, PADS_S, PADS_E):
        errs, miss = [], 0
        for nm, bone, gs, ge, times, sp in cases[kind]:
            r = derive(times, sp, ratio, local, (ps, pe))
            if r is None:
                miss += 1
                continue
            errs.append(abs(r[0] - gs))
            errs.append(abs(r[1] - ge))
        if not errs:
            continue
        mae = sum(errs) / len(errs)
        rows.append({"ratio": ratio, "local": local, "pad": [ps, pe],
                     "mae": round(mae, 4), "miss": miss,
                     "p90": round(sorted(errs)[int(len(errs) * 0.9)], 3)})
    rows.sort(key=lambda r: (r["mae"], r["miss"]))
    res["grid"][kind] = rows[:8]
    res["best"][kind] = rows[0] if rows else None

# 현재 설정(RATIO .25 / LOCAL .5 / hand(0,.033) foot(-.033,.067))의 오차도 같이
for kind, pad in (("hand", (0.0, 0.033)), ("foot", (-0.033, 0.067))):
    errs, miss = [], 0
    for nm, bone, gs, ge, times, sp in cases[kind]:
        r = derive(times, sp, 0.25, 0.5, pad)
        if r is None:
            miss += 1
            continue
        errs += [abs(r[0] - gs), abs(r[1] - ge)]
    if errs:
        res["current_" + kind] = {"mae": round(sum(errs) / len(errs), 4), "miss": miss,
                                  "p90": round(sorted(errs)[int(len(errs) * 0.9)], 3)}

json.dump(res, open(OUT, "w"), indent=1)
print("비교 케이스: hand %d / foot %d" % (res["case_count"]["hand"], res["case_count"]["foot"]))
for kind in ("hand", "foot"):
    cur = res.get("current_" + kind)
    best = res["best"][kind]
    print()
    print("[%s] 현재값 MAE %.3fs (p90 %.3f, 산출실패 %d)" % (kind, cur["mae"], cur["p90"], cur["miss"]) if cur else kind)
    if best:
        print("      최적   MAE %.3fs (p90 %.3f, 실패 %d)  ratio=%.2f local=%.1f pad=(%.3f,%.3f)" % (
            best["mae"], best["p90"], best["miss"], best["ratio"], best["local"], best["pad"][0], best["pad"][1]))
    for r in res["grid"][kind][:4]:
        print("        ratio %.2f local %.1f pad(%+.3f,%+.3f) -> MAE %.3f p90 %.3f miss %d" % (
            r["ratio"], r["local"], r["pad"][0], r["pad"][1], r["mae"], r["p90"], r["miss"]))
