# bone_profiles.json → 스윙창 판정 (로컬 실행, 재측정 불필요)
# 판정: 피크 주변 국소구간(±LOCAL초)의 최소값을 기준선으로 → thr=base+RATIO*(peak-base)
#       피크에서 양방향 확장, thr 아래로 떨어지는 첫 샘플을 경계로.
#   ※ 전역 문턱 금지: 애님 내 3구간(스윙250 / 그립드리프트110 / 정지4)이 공존 — 국소 기준선이라야 성립
# 발 PAD: 착지 지연(감속 꼬리)을 창에 포함 — 창 종료 후 IK 고정이라 짧으면 '발이 붙잡힌' 증상
import json, sys

SRC = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bone_profiles.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/derived_windows.json"
RATIO = 0.25
LOCAL = 0.5
PAD = {"hand": (0.0, 0.033), "foot": (-0.033, 0.067)}
MIN_PEAK = 60.0
MIN_SPAN = 25.0


def derive(times, sp, kind):
    if len(sp) < 5:
        return None
    peak = max(sp)
    pi = sp.index(peak)
    lo = sorted(sp[i] for i in range(len(sp)) if abs(times[i] - times[pi]) <= LOCAL)
    # 국소 '중앙값' 기준선 — 최소값을 쓰면 정지구간(속도~4)이 반경에 들어올 때 문턱이 무너져
    # 좌우 스윙이 한 덩어리로 뭉개진다 (2026-07-20 실측)
    base = lo[len(lo) // 2] if len(lo) % 2 else 0.5 * (lo[len(lo) // 2 - 1] + lo[len(lo) // 2])
    if peak < MIN_PEAK or peak - base < MIN_SPAN:
        return None
    thr = base + RATIO * (peak - base)
    i = pi
    while i > 0 and sp[i - 1] >= thr:
        i -= 1
    j = pi
    while j < len(sp) - 1 and sp[j + 1] >= thr:
        j += 1
    s = times[max(i - 1, 0)] + PAD[kind][0]
    e = times[j] + PAD[kind][1]
    s = max(0.0, round(s, 3))
    e = round(e, 3)
    return None if e - s < 0.05 else (s, e)


data = json.load(open(SRC))
out = {}
for nm, e in sorted(data.items()):
    if e.get("error"):
        continue
    t = e["times"]
    b = e.get("bones", {})
    dur = e["dur"]
    w = {"dur": dur}
    for bone, kind in (("hand_l", "hand"), ("hand_r", "hand"), ("ball_l", "foot"), ("ball_r", "foot")):
        r = derive(t, b[bone], kind) if bone in b else None
        if r:
            r = (r[0], round(min(r[1], dur), 3))
        w[bone] = r
    out[nm] = w
json.dump(out, open(OUT, "w"), indent=1)

hands = sum(1 for v in out.values() if v["hand_l"] or v["hand_r"])
uniq = len({(str(v["hand_l"]), str(v["hand_r"])) for v in out.values()})
print("anims=%d hand창=%d 고유조합=%d" % (len(out), hands, uniq))
for k in sys.argv[1:]:
    if k in out:
        print(k, {b: out[k][b] for b in ("hand_l", "hand_r", "ball_l", "ball_r")}, "dur", out[k]["dur"])
