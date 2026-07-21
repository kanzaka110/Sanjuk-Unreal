# 판정식 역보정 v3 (로컬) — 단순 절대 문턱. 유저 수작업 33종이 정답.
#
# v1(피크기준 국소중앙값+ratio+양방향확장): 손 MAE 0.083 / p90 0.234  — 식이 과해 경계가 뭉개짐
# v2(부호 프로파일): 분류 정확도 50% — 폐기
# v3 근거: 유저 창 안/밖 속도 분포 실측 — 손 잡은구간 중앙 2.9 vs 놓은구간 204.1,
#          단순 문턱 하나로 프레임 분류 정확도 92%. 복잡한 식이 필요 없다.
import json, itertools

PROF = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bone_profiles.json"
DUMP = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_params_dump.json"
PRES = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/preserve_list.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/calibration_simple.json"

prof = json.load(open(PROF))
dump = json.load(open(DUMP))["anims"]
preserve = json.load(open(PRES)) + ["P_Player_Ledge_Move_ShortL_Wallless", "P_Player_Ledge_Move_ShortR_Wallless"]


def segments(times, v, thr, min_len, gap_merge):
    """속도가 thr 를 넘는 연속 구간. gap_merge 이하의 짧은 끊김은 이어붙인다(노이즈 대응)."""
    segs, i, n = [], 0, min(len(v), len(times))
    while i < n:
        if v[i] > thr:
            j = i
            while j + 1 < n and v[j + 1] > thr:
                j += 1
            segs.append([times[i], times[j]])
            i = j + 1
        else:
            i += 1
    if not segs:
        return []
    merged = [segs[0]]
    for s in segs[1:]:
        if s[0] - merged[-1][1] <= gap_merge:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return [tuple(s) for s in merged if s[1] - s[0] >= min_len]


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
        if (abs(gs) < 1e-6 and abs(ge) < 1e-6) or abs(ge - dur) < 0.02 or gs >= ge:
            continue
        kind = "hand" if bone.startswith("hand") else "foot"
        cases[kind].append((nm, bone, gs, ge, p["times"], p["bones"][bone]))

res = {"case_count": {k: len(v) for k, v in cases.items()}, "grid": {}, "best": {}}
THRS = [30, 50, 70, 90, 110, 130, 160, 200]
MINLENS = [0.05, 0.08, 0.12]
GAPS = [0.0, 0.05, 0.10, 0.20]
PADS_S = [-0.067, -0.033, 0.0]
PADS_E = [0.0, 0.033, 0.067]
MISS_PENALTY = 0.5   # 산출 실패를 0.5초 오차로 취급 — 실패를 숨기는 조합이 1등 되는 것 방지

for kind in ("hand", "foot"):
    rows = []
    for thr, ml, gp, ps, pe in itertools.product(THRS, MINLENS, GAPS, PADS_S, PADS_E):
        errs, miss = [], 0
        for nm, bone, gs, ge, times, v in cases[kind]:
            segs = segments(times, v, thr, ml, gp)
            if not segs:
                miss += 1
                errs += [MISS_PENALTY, MISS_PENALTY]
                continue
            a, b = max(segs, key=lambda x: x[1] - x[0])
            errs += [abs((a + ps) - gs), abs((b + pe) - ge)]
        mae = sum(errs) / len(errs)
        rows.append({"thr": thr, "min_len": ml, "gap": gp, "pad": [ps, pe],
                     "mae": round(mae, 4), "miss": miss,
                     "p90": round(sorted(errs)[int(len(errs) * 0.9)], 3),
                     "within1f": round(100.0 * sum(1 for e in errs if e <= 0.034) / len(errs), 1),
                     "within2f": round(100.0 * sum(1 for e in errs if e <= 0.067) / len(errs), 1)})
    rows.sort(key=lambda r: r["mae"])
    res["grid"][kind] = rows[:10]
    res["best"][kind] = rows[0]

json.dump(res, open(OUT, "w"), indent=1)
print("비교 케이스: hand %d / foot %d  (miss 는 %.1fs 오차로 계산)" % (
    res["case_count"]["hand"], res["case_count"]["foot"], MISS_PENALTY))
for kind in ("hand", "foot"):
    b = res["best"][kind]
    print()
    print("[%s] 최적 MAE %.3fs / p90 %.3fs / 실패 %d" % (kind, b["mae"], b["p90"], b["miss"]))
    print("      thr=%d min_len=%.2f gap=%.2f pad=(%+.3f,%+.3f)" % (b["thr"], b["min_len"], b["gap"], b["pad"][0], b["pad"][1]))
    print("      1프레임내 %.0f%% / 2프레임내 %.0f%%" % (b["within1f"], b["within2f"]))
    for r in res["grid"][kind][1:4]:
        print("        thr%3d ml%.2f gap%.2f pad(%+.3f,%+.3f) MAE %.3f 2f내 %.0f%% miss %d" % (
            r["thr"], r["min_len"], r["gap"], r["pad"][0], r["pad"][1], r["mae"], r["within2f"], r["miss"]))
