# 판정식 역보정 v4 (로컬) — '고정(hold) 구간' 기준 역발상. 유저 수작업 33종이 정답.
#
# 유저 지시(2026-07-21): "IK로 잡아주는 구간은 foot 이 움직임이 거의 없는 구간 기준으로"
#   발은 짚은 채로도 자세를 고쳐 속도가 붙어(잡은구간 p90 281) '움직임' 문턱으로는 안 갈린다.
#   대신 '거의 멈춘 구간'(hold)을 찾고, hold 와 hold 사이를 창으로 본다.
#
# v1 복잡한식 / v2 부호 / v3 단순문턱(움직임 기준) 대비 성능 비교용.
import json, itertools

PROF = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bone_profiles.json"
DUMP = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_params_dump.json"
PRES = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/preserve_list.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/calibration_hold.json"

prof = json.load(open(PROF))
dump = json.load(open(DUMP))["anims"]
preserve = json.load(open(PRES)) + ["P_Player_Ledge_Move_ShortL_Wallless", "P_Player_Ledge_Move_ShortR_Wallless"]


def holds(times, v, low, min_hold):
    """속도가 low 이하로 min_hold 이상 유지되는 구간 = 짚고 있는 구간"""
    out, i, n = [], 0, min(len(v), len(times))
    while i < n:
        if v[i] <= low:
            j = i
            while j + 1 < n and v[j + 1] <= low:
                j += 1
            if times[j] - times[i] >= min_hold:
                out.append((times[i], times[j]))
            i = j + 1
        else:
            i += 1
    return out


def window_from_holds(times, v, low, min_hold):
    """hold 와 hold 사이 = 발이 옮겨지는 창. 가장 긴 것을 1차 창으로."""
    hs = holds(times, v, low, min_hold)
    if len(hs) < 2:
        # hold 가 하나뿐이면: 그 앞/뒤 중 긴 쪽을 창으로
        if len(hs) == 1 and times:
            a = (times[0], hs[0][0])
            b = (hs[0][1], times[-1])
            cand = [c for c in (a, b) if c[1] - c[0] > 0]
            return max(cand, key=lambda c: c[1] - c[0]) if cand else None
        return None
    gaps = [(hs[i][1], hs[i + 1][0]) for i in range(len(hs) - 1)]
    gaps = [g for g in gaps if g[1] > g[0]]
    return max(gaps, key=lambda g: g[1] - g[0]) if gaps else None


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
LOWS = [5, 10, 20, 30, 50, 70, 100]
MINHOLDS = [0.05, 0.10, 0.15, 0.20, 0.30]
PADS_S = [-0.033, 0.0, 0.033]
PADS_E = [-0.033, 0.0, 0.033, 0.067]
MISS_PENALTY = 0.5

for kind in ("hand", "foot"):
    rows = []
    for low, mh, ps, pe in itertools.product(LOWS, MINHOLDS, PADS_S, PADS_E):
        errs, miss = [], 0
        for nm, bone, gs, ge, times, v in cases[kind]:
            w = window_from_holds(times, v, low, mh)
            if w is None:
                miss += 1
                errs += [MISS_PENALTY, MISS_PENALTY]
                continue
            errs += [abs((w[0] + ps) - gs), abs((w[1] + pe) - ge)]
        mae = sum(errs) / len(errs)
        rows.append({"low": low, "min_hold": mh, "pad": [ps, pe], "mae": round(mae, 4), "miss": miss,
                     "p90": round(sorted(errs)[int(len(errs) * 0.9)], 3),
                     "within1f": round(100.0 * sum(1 for e in errs if e <= 0.034) / len(errs), 1),
                     "within2f": round(100.0 * sum(1 for e in errs if e <= 0.067) / len(errs), 1)})
    rows.sort(key=lambda r: r["mae"])
    res["grid"][kind] = rows[:10]
    res["best"][kind] = rows[0]

json.dump(res, open(OUT, "w"), indent=1)
print("[v4 hold 기준] 케이스 hand %d / foot %d" % (res["case_count"]["hand"], res["case_count"]["foot"]))
for kind in ("hand", "foot"):
    b = res["best"][kind]
    print()
    print("[%s] MAE %.3fs / p90 %.3fs / 실패 %d  |  1f내 %.0f%% 2f내 %.0f%%" % (
        kind, b["mae"], b["p90"], b["miss"], b["within1f"], b["within2f"]))
    print("      low=%d min_hold=%.2f pad=(%+.3f,%+.3f)" % (b["low"], b["min_hold"], b["pad"][0], b["pad"][1]))
    for r in res["grid"][kind][1:4]:
        print("        low%3d mh%.2f pad(%+.3f,%+.3f) MAE %.3f 2f내 %.0f%% miss %d" % (
            r["low"], r["min_hold"], r["pad"][0], r["pad"][1], r["mae"], r["within2f"], r["miss"]))
