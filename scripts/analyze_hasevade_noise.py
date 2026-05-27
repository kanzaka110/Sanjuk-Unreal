#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_hasevade_noise.py
ANIM_REC 로그에서 HasEvade(he) 에피소드를 추출, 비전투/비락온(il=false,ib=false) 회피의
clip 노이즈(None/Stop/Pivot 끼어듦, 깜빡임)를 진단한다.
사용: py scripts/analyze_hasevade_noise.py <log_path>
"""
import re, sys, collections

LOG = sys.argv[1] if len(sys.argv) > 1 else \
    r"E:/Perforce/SB2/Workspace/Internal/SB2/Saved/Logs/SB2.log"

frame_re = re.compile(r"\]\[(\d+)\]LogBlueprintUserMessages")
# "key"=value  (value = 콤마/공백 전까지)
kv_re = re.compile(r'"(\w+)"=([^,\s]*)')

KEYS = ("he", "il", "ib", "clip", "rmf", "ms", "sms", "sp", "vlen", "ist", "isf", "isc",
        "pwm", "ppwm", "as", "pms2")

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
        if fr == last_frame:      # 프레임당 2x emit dedup
            continue
        last_frame = fr
        d = dict(kv_re.findall(line))
        rec = {"fr": fr}
        for k in KEYS:
            rec[k] = d.get(k, "")
        records.append(rec)

print(f"parsed frames (deduped): {len(records)}")

def is_true(v): return v == "true"

# he 에피소드 = 연속 he=true 런
episodes = []
cur = None
for r in records:
    if is_true(r["he"]):
        if cur is None:
            cur = {"start": r["fr"], "frames": []}
        cur["frames"].append(r)
    else:
        if cur is not None:
            cur["end"] = cur["frames"][-1]["fr"]
            episodes.append(cur); cur = None
if cur is not None:
    cur["end"] = cur["frames"][-1]["fr"]; episodes.append(cur)

print(f"total he episodes: {len(episodes)}")

def collapse(seq):
    out = []
    for x in seq:
        if not out or out[-1][0] != x:
            out.append([x, 1])
        else:
            out[-1][1] += 1
    return ",".join(f"{v}x{n}" if n > 1 else v for v, n in out)

# 비전투/비락온 타겟 = 에피소드 내 모든 프레임 il=false & ib=false
target, mixed = [], []
for ep in episodes:
    il_set = {f["il"] for f in ep["frames"]}
    ib_set = {f["ib"] for f in ep["frames"]}
    if il_set <= {"false"} and ib_set <= {"false"}:
        target.append(ep)
    else:
        mixed.append(ep)

print(f"  non-lockon & non-battle episodes: {len(target)}")
print(f"  lockon/battle (or mixed) episodes: {len(mixed)}")

# 노이즈 집계 (타겟만)
none_eps = stop_eps = pivot_eps = flicker_eps = 0
clip_changes = []
print("\n=== 비전투/비락온 회피 에피소드 (clip/rmf 시퀀스) ===")
for i, ep in enumerate(target):
    clips = [f["clip"] for f in ep["frames"]]
    rmfs = [f["rmf"] for f in ep["frames"]]
    sms = [f["sms"] for f in ep["frames"]]
    n = len(clips)
    cset = collections.Counter(clips)
    transitions = sum(1 for a, b in zip(clips, clips[1:]) if a != b)
    clip_changes.append(transitions)
    has_none = cset.get("None", 0)
    has_stop = cset.get("Stop", 0)
    has_pivot = cset.get("Pivot", 0)
    if has_none: none_eps += 1
    if has_stop: stop_eps += 1
    if has_pivot: pivot_eps += 1
    if transitions >= 3: flicker_eps += 1
    flag = ""
    if has_none: flag += " ⚠None"
    if has_stop: flag += " ⚠Stop"
    if has_pivot: flag += " ⚠Pivot"
    if transitions >= 3: flag += f" ⚠flicker({transitions})"
    pwms = collapse([f["pwm"] for f in ep["frames"]])
    if i < 30:
        print(f"[{i}] f{ep['start']}-{ep['end']} len={n} pwm=[{pwms}] sms={collapse(sms)} "
              f"clip=[{collapse(clips)}] rmf=[{collapse(rmfs)}]{flag}")

print("\n=== 락온/배틀(mixed) 회피 에피소드 ===")
for i, ep in enumerate(mixed):
    clips = [f["clip"] for f in ep["frames"]]
    rmfs = [f["rmf"] for f in ep["frames"]]
    sms = [f["sms"] for f in ep["frames"]]
    ils = [f["il"] for f in ep["frames"]]
    if i < 20:
        print(f"[{i}] f{ep['start']}-{ep['end']} len={len(clips)} il={collapse(ils)} "
              f"sms={collapse(sms)} clip=[{collapse(clips)}] rmf=[{collapse(rmfs)}]")

tg = len(target) or 1
print(f"\n=== 타겟({len(target)}) 노이즈 집계 ===")
print(f"clip=None 포함 에피소드: {none_eps} ({100*none_eps//tg}%)")
print(f"clip=Stop 끼어듦 에피소드: {stop_eps} ({100*stop_eps//tg}%)")
print(f"clip=Pivot 끼어듦 에피소드: {pivot_eps} ({100*pivot_eps//tg}%)")
print(f"clip 3회+ 전환(깜빡임) 에피소드: {flicker_eps} ({100*flicker_eps//tg}%)")
if clip_changes:
    print(f"에피소드당 clip 전환수 avg={sum(clip_changes)/len(clip_changes):.1f} max={max(clip_changes)}")

# === 진짜 노이즈: 회피 본체(rmf=Evade) 구간의 clip이 None인가 Start인가 ===
print("\n=== 회피 본체(rmf=Evade) clip 품질 + discriminator ===")
def body_frames(ep):
    return [f for f in ep["frames"] if f["rmf"] == "Evade"] or ep["frames"][:1]
def body_outcome(ep):
    clips = [f["clip"] for f in body_frames(ep)]
    cset = set(clips)
    if "Start" in cset and "None" not in cset:  return "body_Start"      # 회피 구간 내내 Start (정상)
    if cset == {"None"}:                          return "body_None"       # 회피 구간 전부 None (노이즈)
    if "Start" in cset and "None" in cset:        return "body_None2Start" # 섞임
    return "body_other"

cols = collections.defaultdict(lambda: collections.Counter())
counts = collections.Counter()
for ep in target:
    bo = body_outcome(ep)
    counts[bo] += 1
    b0 = body_frames(ep)[0]
    cols[bo][f'pwm={b0["pwm"]}'] += 1
    cols[bo][f'as={b0["as"]}'] += 1
    cols[bo][f'isc={b0["isc"]}'] += 1
    cols[bo][f'isf={b0["isf"]}'] += 1
    cols[bo][f'sms={b0["sms"]}'] += 1
    cols[bo][f'ms={b0["ms"]}'] += 1
    cols[bo][f'ist={b0["ist"]}'] += 1
for bo in ("body_Start", "body_None", "body_None2Start", "body_other"):
    print(f"\n[{bo}] {counts[bo]}건")
    for k, v in sorted(cols[bo].items()):
        print(f"   {k}: {v}")

# === 재진입 여부: 에피소드 내 sms 전환수 (0 = 재진입 없음 = 트리거 미발동) ===
print("\n=== 재진입(sms 전환) 발생 여부 by body outcome ===")
for bo in ("body_Start", "body_None"):
    eps = [ep for ep in target if body_outcome(ep) == bo]
    sms_tr = []
    for ep in eps:
        seq = [f["sms"] for f in ep["frames"]]
        sms_tr.append(sum(1 for a, b in zip(seq, seq[1:]) if a != b))
    if not sms_tr: continue
    zero = sum(1 for t in sms_tr if t == 0)
    nonzero = len(sms_tr) - zero
    print(f"[{bo}] {len(eps)}건: sms 전환 0회(재진입 없음)={zero}, 1회+={nonzero}, "
          f"avg={sum(sms_tr)/len(sms_tr):.2f}")

print("\n=== (구) 전체 outcome 분류 ===")
def outcome(ep):
    clips = {f["clip"] for f in ep["frames"]}
    if clips == {"None"}:           return "None_only"
    if "Start" in clips:            return "has_Start"
    return "other"

# 진입(첫) 프레임 + 회피본체(rmf=Evade 첫 프레임)의 pwm/ppwm/as 비교
buckets = collections.defaultdict(lambda: collections.Counter())
pwm_by_outcome = collections.defaultdict(lambda: collections.Counter())
for ep in target:
    oc = outcome(ep)
    entry = ep["frames"][0]
    # 회피 본체 진입 = rmf가 Evade인 첫 프레임 (없으면 entry)
    body = next((f for f in ep["frames"] if f["rmf"] == "Evade"), entry)
    pwm_by_outcome[oc][f'entry_pwm={entry["pwm"]}'] += 1
    pwm_by_outcome[oc][f'body_pwm={body["pwm"]}'] += 1
    pwm_by_outcome[oc][f'ppwm={entry["ppwm"]}'] += 1
    pwm_by_outcome[oc][f'as={entry["as"]}'] += 1

for oc in ("None_only", "has_Start", "other"):
    cnt = sum(1 for ep in target if outcome(ep) == oc)
    print(f"\n[{oc}] {cnt}건")
    for k, v in sorted(pwm_by_outcome[oc].items()):
        print(f"   {k}: {v}")

# pwm 가 회피 도중 변하는가 (해소 지연 신호)
print("\n=== 회피 에피소드 내 pwm 변화(해소) 여부 ===")
pwm_changed = pwm_stable = 0
for ep in target:
    pwms = [f["pwm"] for f in ep["frames"]]
    if len(set(pwms)) > 1: pwm_changed += 1
    else: pwm_stable += 1
print(f"pwm 에피소드 내 변동: {pwm_changed} / 고정: {pwm_stable}")
# None_only 에피소드의 pwm 시퀀스 샘플
print("\n=== None_only 에피소드 pwm/ppwm 시퀀스 (샘플 10) ===")
shown = 0
for ep in target:
    if outcome(ep) != "None_only": continue
    pwms = collapse([f["pwm"] for f in ep["frames"]])
    ppwms = collapse([f["ppwm"] for f in ep["frames"]])
    print(f"   f{ep['start']}: pwm=[{pwms}] ppwm=[{ppwms}]")
    shown += 1
    if shown >= 10: break
