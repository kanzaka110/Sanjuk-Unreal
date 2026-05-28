#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_lockon_evade_gait_staircase.py

락온(il=true) 질주 흐름 중 회피 → 좌/우(strafe) 이동 시 게이트(pwm)가
Sprint→(회피 dip)→Jog→Run→Sprint 로 "계단" 밟히는지 정량 측정.

목적 (사용자 호소: "회피후 좌/우 이동시 jog->Sprint, 바로 sprint 되어야"):
  1) 회피 직전(pre-evade) pwm 이 실제 Sprint(4) 였나     → latch 처방 유효성
  2) 회피 중 pwm 이 어디로 떨어지나 (dip)
  3) 재가속 시 Sprint 복귀까지 Jog/Run 계단 몇 프레임      → latch grace 사이징
  4) ms(MoveSide)=L/R(좌우 strafe) 케이스만 추렸을 때 동일 패턴인가

pwm 인코딩 (ANIM_REC, =Get PendingWalkMode 본체):
  추정 2=Jog, 3=Run, 4=Sprint (Walk=1, Idle=0). 로그 실측값으로 재확인.

사용: py scripts/analyze_lockon_evade_gait_staircase.py [log_path] [--pre N] [--post N]
"""
import re, sys, collections

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1)
        if sys.argv[i].startswith("--")}
LOG = args[0] if args else r"E:/Perforce/SB2/Workspace/Internal/SB2/Saved/Logs/SB2.log"
PRE = int(opts.get("--pre", 12))
POST = int(opts.get("--post", 40))

frame_re = re.compile(r"\]\[(\d+)\]LogBlueprintUserMessages")
kv_re = re.compile(r'"(\w+)"=([^,\s]*)')
KEYS = ("he", "il", "ib", "clip", "rmf", "ms", "sms", "sp", "vlen",
        "ist", "isf", "isc", "pwm", "ppwm", "as", "pms2")

records = []
last_frame = None
with open(LOG, "r", encoding="utf-8", errors="ignore") as fh:
    for line in fh:
        if "ANIM_REC" not in line:
            continue
        m = frame_re.search(line)
        if not m:
            continue
        fr = int(m.group(1))
        if fr == last_frame:        # 프레임당 2x emit dedup
            continue
        last_frame = fr
        d = dict(kv_re.findall(line))
        rec = {"fr": fr, "_i": len(records)}
        for k in KEYS:
            rec[k] = d.get(k, "")
        records.append(rec)

print(f"parsed frames (deduped): {len(records)}")
if not records:
    sys.exit("로그에 ANIM_REC 없음 — PIE 세션 + NOTIFY/REC 활성 확인")

def is_true(v): return v == "true"

# he=true 연속 런 → 에피소드 (인덱스 보존)
episodes = []
cur = None
for r in records:
    if is_true(r["he"]):
        if cur is None:
            cur = {"i0": r["_i"], "frames": []}
        cur["frames"].append(r)
    else:
        if cur is not None:
            cur["i1"] = cur["frames"][-1]["_i"]
            episodes.append(cur); cur = None
if cur is not None:
    cur["i1"] = cur["frames"][-1]["_i"]; episodes.append(cur)

# 락온 회피만 (에피소드 내 il=true 프레임 다수)
lockon = [ep for ep in episodes
          if sum(1 for f in ep["frames"] if f["il"] == "true") >= max(1, len(ep["frames"]) // 2)]
print(f"total he episodes: {len(episodes)}  | lock-on episodes: {len(lockon)}")

def pwm_name(p):
    return {"0": "Idle", "1": "Walk", "2": "Jog", "3": "Run", "4": "Sprint"}.get(p, p or "?")

def collapse(seq):
    out = []
    for x in seq:
        if not out or out[-1][0] != x:
            out.append([x, 1])
        else:
            out[-1][1] += 1
    return ",".join(f"{v}x{n}" if n > 1 else f"{v}" for v, n in out)

# 집계
pre_sprint = staircase_eps = 0
staircase_lens = []
print(f"\n=== 락온 회피 에피소드 (pre={PRE} / evade / post={POST}) ===")
for idx, ep in enumerate(lockon):
    i0, i1 = ep["i0"], ep["i1"]
    pre = records[max(0, i0 - PRE):i0]
    body = ep["frames"]
    post = records[i1 + 1:i1 + 1 + POST]

    pre_pwm = [f["pwm"] for f in pre]
    body_pwm = [f["pwm"] for f in body]
    post_pwm = [f["pwm"] for f in post]

    pre_max = max([int(p) for p in pre_pwm if p.isdigit()] or [-1])
    was_sprint = pre_max >= 4
    if was_sprint:
        pre_sprint += 1

    # 재가속 계단: post 에서 pwm 최저점 이후 4(Sprint) 처음 복귀까지 프레임수
    post_ints = [(j, int(p)) for j, p in enumerate(post_pwm) if p.isdigit()]
    stair = None
    if was_sprint and post_ints:
        # 회피로 떨어진 뒤 다시 Sprint 도달하는 첫 인덱스
        below = [j for j, v in post_ints if v < 4]
        sprint_back = [j for j, v in post_ints if v >= 4]
        if below and sprint_back:
            first_below = below[0]
            after = [j for j in sprint_back if j > first_below]
            if after:
                stair = after[0] - first_below   # Jog/Run 머문 프레임 길이
    if stair and stair >= 2:
        staircase_eps += 1
        staircase_lens.append(stair)

    # ms(MoveSide) 좌우 여부: 2=R, 6=L (strafe)
    ms_body = collapse([f["ms"] for f in body])
    flag = ""
    if was_sprint: flag += " ◀pre=Sprint"
    if stair and stair >= 2: flag += f" ⚠계단{stair}f"
    if idx < 25:
        print(f"[{idx}] f{body[0]['fr']} len={len(body)} ms=[{ms_body}]")
        print(f"     pre  pwm=[{collapse([pwm_name(p) for p in pre_pwm])}]  (max={pwm_name(str(pre_max)) if pre_max>=0 else '?'})")
        print(f"     body pwm=[{collapse([pwm_name(p) for p in body_pwm])}] sms=[{collapse([f['sms'] for f in body])}] clip=[{collapse([f['clip'] for f in body])}]")
        print(f"     post pwm=[{collapse([pwm_name(p) for p in post_pwm])}] clip=[{collapse([f['clip'] for f in post])}]{flag}")

n = len(lockon) or 1
print(f"\n=== 집계 (락온 회피 {len(lockon)}건) ===")
print(f"회피 직전 pwm=Sprint(4) 도달: {pre_sprint} ({100*pre_sprint//n}%)")
print(f"재가속 Jog/Run 계단(>=2f) 발생: {staircase_eps} ({100*staircase_eps//n}%)")
if staircase_lens:
    staircase_lens.sort()
    print(f"계단 길이(f): avg={sum(staircase_lens)/len(staircase_lens):.1f} "
          f"min={staircase_lens[0]} max={staircase_lens[-1]} "
          f"median={staircase_lens[len(staircase_lens)//2]}")
    print(f"  분포: {collections.Counter(staircase_lens)}")
print("\n해석:")
print(" - pre=Sprint% 높고 계단% 높음 → pre-evade Sprint latch 처방 유효 (계단길이=grace 윈도우 하한)")
print(" - pre=Sprint% 낮음 → 사용자 체감과 불일치, 시나리오 재확인 필요")
