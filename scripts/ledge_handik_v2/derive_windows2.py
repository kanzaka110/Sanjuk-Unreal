# bone_profiles.json → 스윙창 판정 (1차 + 2차) — 로컬 실행
# 1차: 최대 피크 주변 (derive_windows.py 와 동일 판정)
# 2차: 1차 창을 마스킹한 뒤 남은 구간의 최대 피크. 유효조건 = 피크가 1차 피크의 SECOND_MIN 이상
#      + 1차 창과 GAP 이상 떨어짐 (인접 노이즈를 2차로 오인 방지, 같은프레임 키 충돌도 회피)
import json, sys

SRC = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bone_profiles.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/derived_windows.json"
# 손/발 노브 분리 (2026-07-20 실측 피드백)
#  손: 넓게 — 후행 손이 늦게 풀리면 팔이 쫙 펴진 채 딸려감
#  발: 좁게 — 창이 길면 타깃 lerp가 느려져 발이 기계적으로 끌림('딱딱함')
# 시작/끝 문턱 분리 (2026-07-20): 같은 문턱을 쓰면 '늦게 풀림'(시작↑) 과 '딱딱함'(창 길어짐) 을
#   동시에 만족시킬 수 없다. 시작=낮은 문턱(움직이는 즉시 릴리즈) / 끝=높은 문턱(창 짧게 유지)
RATIO = {"hand": (0.14, 0.20), "foot": (0.08, 0.35)}
LOCAL = 0.5
# 2026-07-20: 후행 팔다리가 늦게 풀려 "쫙 펴진 채 딸려감" → 시작 패드를 음수로 (조기 릴리즈)
# 발: 시작만 크게 당긴다(-0.08). 끝을 늘리면 타깃 lerp 가 길어져 '딱딱'해지므로 유지
#   (0.40→붙잡힘 / 0.18+넓게→딱딱 / 0.32+앞당김 = 현재)
# 발: 창을 '통째로' 앞당긴다 — move 커브(타깃 lerp)가 창 구간에 걸쳐 진행되므로,
#   시작만 당기면 lerp 가 길어져 타깃 도착이 여전히 늦다. 시작/끝 동시 이동 = 도착 시점이 앞당겨짐
# 발 시작 패드: 릴리즈 전 '묶여있는 시간' 을 줄이는 노브 (유저 요청 2026-07-20 저녁: 조금만 더 짧게)
PAD = {"hand": (-0.067, 0.033), "foot": (-0.17, -0.07)}
MIN_START = 0.08       # 창 시작 하한 — start-ReleaseRamp(0.07)가 음수가 되면 음수 시각 키가 생김
MIN_PEAK = 60.0
MIN_SPAN = 25.0
SECOND_MIN = 0.55      # 2차 피크 / 1차 피크 최소 비율
GAP = 0.22             # 1차 창과 2차 창 최소 간격(초)
#   ⚠ ReleaseRamp(0.07)+PlantRamp(0.10) 합보다 커야 함 — 두 창의 램프 키가 같은 시각에 겹치면
#     SetCurveControlKey 어설션 즉사 (README 함정)


def med(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def one(times, sp, kind, mask):
    cand = [(sp[i], i) for i in range(len(sp)) if not mask[i]]
    if len(cand) < 5:
        return None, 0.0
    peak, pi = max(cand)
    lo = [sp[i] for i in range(len(sp)) if abs(times[i] - times[pi]) <= LOCAL]
    base = med(lo)
    if peak < MIN_PEAK or peak - base < MIN_SPAN:
        return None, peak
    thr_s = base + RATIO[kind][0] * (peak - base)
    thr_e = base + RATIO[kind][1] * (peak - base)
    i = pi
    while i > 0 and sp[i - 1] >= thr_s and not mask[i - 1]:
        i -= 1
    j = pi
    while j < len(sp) - 1 and sp[j + 1] >= thr_e and not mask[j + 1]:
        j += 1
    s = max(MIN_START, round(times[max(i - 1, 0)] + PAD[kind][0], 3))
    e = round(times[j] + PAD[kind][1], 3)
    for x in range(max(i - 1, 0), min(j + 1, len(sp) - 1) + 1):
        mask[x] = True
    return (None if e - s < 0.05 else (s, e)), peak


def derive(times, sp, kind, dur):
    mask = [False] * len(sp)
    w1, p1 = one(times, sp, kind, mask)
    if not w1:
        return None, None
    w1 = (w1[0], round(min(w1[1], dur), 3))
    w2, p2 = one(times, sp, kind, mask)
    if w2:
        w2 = (w2[0], round(min(w2[1], dur), 3))
        far = w2[0] >= w1[1] + GAP or w2[1] + GAP <= w1[0]
        if not (p2 >= p1 * SECOND_MIN and far and w2[1] > w2[0]):
            w2 = None
    return w1, w2


data = json.load(open(SRC))
out = {}
n2 = 0
for nm, e in sorted(data.items()):
    if e.get("error"):
        continue
    t, b, dur = e["times"], e.get("bones", {}), e["dur"]
    w = {"dur": dur}
    for bone, kind in (("hand_l", "hand"), ("hand_r", "hand"), ("ball_l", "foot"), ("ball_r", "foot")):
        w1 = w2 = None
        if bone in b:
            w1, w2 = derive(t, b[bone], kind, dur)
        w[bone] = w1
        w[bone + "_2"] = w2
        if w2:
            n2 += 1
    out[nm] = w
json.dump(out, open(OUT, "w"), indent=1)
print("anims=%d 2차창=%d" % (len(out), n2))
for k in sys.argv[1:]:
    if k in out:
        print(k, {x: out[k][x] for x in out[k] if x != "dur"}, "dur", out[k]["dur"])
