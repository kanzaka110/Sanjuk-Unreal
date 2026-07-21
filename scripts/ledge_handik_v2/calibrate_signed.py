# 판정식 역보정 v2 (로컬) — '부호' 프로파일 기반. 유저 수작업 33종이 정답.
#
# v1(속도 크기) 실패: 그립 중 드리프트(110)와 스윙(250)이 겹쳐 손 p90 7프레임 / 발 12프레임 오차.
# v2 신호: signed_profiles.json = (본속도 - 펠비스속도)를 이동축에 투영한 부호값.
#          짚음 = 음수(뒤로 흐름) / 놓음·스윙 = 양수  → 유저 기준("놓고 다시 잡는 구간")과 직접 대응.
import json, itertools

SIG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/signed_profiles.json"
DUMP = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_params_dump.json"
PRES = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/preserve_list.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/calibration_signed.json"

sig = json.load(open(SIG))
dump = json.load(open(DUMP))["anims"]
preserve = json.load(open(PRES)) + ["P_Player_Ledge_Move_ShortL_Wallless", "P_Player_Ledge_Move_ShortR_Wallless"]


def segments(times, s, thr, min_len):
    """부호값이 thr 를 넘는(=놓은) 연속 구간들"""
    segs, i, n = [], 0, len(s)
    while i < n:
        if s[i] > thr:
            j = i
            while j + 1 < n and s[j + 1] > thr:
                j += 1
            if times[j] - times[i] >= min_len:
                segs.append((times[i], times[j], j - i))
            i = j + 1
        else:
            i += 1
    return segs


PAIRS = [("hand_l", "HandMoveStartL", "HandMoveEndL"), ("hand_r", "HandMoveStartR", "HandMoveEndR"),
         ("ball_l", "FootMoveStartL", "FootMoveEndL"), ("ball_r", "FootMoveStartR", "FootMoveEndR")]
cases = {"hand": [], "foot": []}
for nm in preserve:
    if nm not in sig or nm not in dump or sig[nm].get("error"):
        continue
    p, u = sig[nm], dump[nm]
    dur = u["dur"]
    for bone, ks, ke in PAIRS:
        if bone not in p.get("bones", {}):
            continue
        gs, ge = u.get(ks), u.get(ke)
        if gs is None or ge is None:
            continue
        if (abs(gs) < 1e-6 and abs(ge) < 1e-6) or abs(ge - dur) < 0.02 or gs >= ge:
            continue   # 벽 조합 규칙 케이스는 판정식 대상 아님
        kind = "hand" if bone.startswith("hand") else "foot"
        cases[kind].append((nm, bone, gs, ge, p["times"], p["bones"][bone]))

res = {"case_count": {k: len(v) for k, v in cases.items()}, "grid": {}, "best": {}}
THRS = [0.0, 5.0, 10.0, 20.0, 30.0, 50.0]
MINLENS = [0.05, 0.08, 0.12]
PADS_S = [-0.067, -0.033, 0.0, 0.033]
PADS_E = [0.0, 0.033, 0.067, 0.10]

for kind in ("hand", "foot"):
    rows = []
    for thr, ml, ps, pe in itertools.product(THRS, MINLENS, PADS_S, PADS_E):
        errs, miss = [], 0
        for nm, bone, gs, ge, times, s in cases[kind]:
            segs = segments(times, s, thr, ml)
            if not segs:
                miss += 1
                continue
            # 유저값과 가장 가까운 구간이 아니라, '가장 긴 구간'을 1차 창으로 본다 (실사용과 동일 조건)
            a, b, _ = max(segs, key=lambda x: x[1] - x[0])
            errs += [abs((a + ps) - gs), abs((b + pe) - ge)]
        if not errs:
            continue
        mae = sum(errs) / len(errs)
        rows.append({"thr": thr, "min_len": ml, "pad": [ps, pe], "mae": round(mae, 4),
                     "miss": miss, "p90": round(sorted(errs)[int(len(errs) * 0.9)], 3),
                     "within1f": round(100.0 * sum(1 for e in errs if e <= 0.034) / len(errs), 1),
                     "within2f": round(100.0 * sum(1 for e in errs if e <= 0.067) / len(errs), 1)})
    rows.sort(key=lambda r: (r["mae"], r["miss"]))
    res["grid"][kind] = rows[:8]
    res["best"][kind] = rows[0] if rows else None

json.dump(res, open(OUT, "w"), indent=1)
print("비교 케이스: hand %d / foot %d" % (res["case_count"]["hand"], res["case_count"]["foot"]))
for kind in ("hand", "foot"):
    b = res["best"][kind]
    if not b:
        print("[%s] 산출 실패" % kind)
        continue
    print()
    print("[%s] 최적: MAE %.3fs / p90 %.3fs / 산출실패 %d" % (kind, b["mae"], b["p90"], b["miss"]))
    print("      thr=%.0f min_len=%.2f pad=(%+.3f,%+.3f)" % (b["thr"], b["min_len"], b["pad"][0], b["pad"][1]))
    print("      1프레임 이내 %.0f%% / 2프레임 이내 %.0f%%" % (b["within1f"], b["within2f"]))
    for r in res["grid"][kind][1:4]:
        print("        thr%3.0f ml%.2f pad(%+.3f,%+.3f) MAE %.3f p90 %.3f miss %d 2f내 %.0f%%" % (
            r["thr"], r["min_len"], r["pad"][0], r["pad"][1], r["mae"], r["p90"], r["miss"], r["within2f"]))
