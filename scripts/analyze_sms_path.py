#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""반전 Stop 끼임 onset의 SM 스테이트(sms) 진입 경로 추출.

Stop 끼임(seq=*Sprint_turn_Stop* & sv 높음 = 진짜정지 아님)을 찾고,
각 onset 직전 N프레임의 sms 시퀀스를 디코딩해 진입 경로를 확정.

sms index map (get_state_machines, 2026-05-22 실측):
  0 GroundIdle / 1 GroundMoving / 2 TransitToGroundIdle / 3 TransitToGroundMoving
  4 Falling / 5 TransitToFalling / 6 PlayingMontage / 7 _toTTF / 8 _toTTG
  9 _toTTGI / 10 _toPM / 11 SplineMoving
"""
import re
import sys
from collections import Counter

LOG = r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2.log"
SMS_NAME = {
    0: "GroundIdle", 1: "GroundMoving", 2: "TransitToGroundIdle",
    3: "TransitToGroundMoving", 4: "Falling", 5: "TransitToFalling",
    6: "PlayingMontage", 7: "_toTTF", 8: "_toTTG", 9: "_toTTGI",
    10: "_toPM", 11: "SplineMoving",
}

# 필드 추출 정규식 (포맷: "f"=N,... "sms"=N, sv=X=.. Y=.. Z=..)
RE_F   = re.compile(r'"f"=([\d,]+)')
RE_SMS = re.compile(r'"sms"=(-?\d+)')
RE_SEQ = re.compile(r'"seq"=([^,]+)')
RE_RRR = re.compile(r'"rrr"=(\S+)')
RE_FV  = re.compile(r'"fv"=(-?[\d.]+)')
RE_SP  = re.compile(r'"sp"=([\d,]+)')
RE_SV  = re.compile(r'"sv"=X=(-?[\d.]+) Y=(-?[\d.]+) Z=(-?[\d.]+)')


def num(s):
    return int(s.replace(",", "")) if s else None


def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def parse(line):
    f = RE_F.search(line)
    sms = RE_SMS.search(line)
    if not f or not sms:
        return None
    sv = RE_SV.search(line)
    svmag = None
    if sv:
        x, y = float(sv.group(1)), float(sv.group(2))
        svmag = (x * x + y * y) ** 0.5
    seq = RE_SEQ.search(line)
    rrr = RE_RRR.search(line)
    sp = RE_SP.search(line)
    fv = RE_FV.search(line)
    return {
        "f": num(f.group(1)),
        "sms": int(sms.group(1)),
        "seq": seq.group(1).strip() if seq else "",
        "rrr": rrr.group(1).strip() if rrr else "",
        "sp": num(sp.group(1)) if sp else None,
        "svmag": svmag,
        "fv": fnum(fv.group(1)) if fv else None,
    }


def main():
    sv_thresh = float(sys.argv[1]) if len(sys.argv) > 1 else 200.0
    pre = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    rows = []
    with open(LOG, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if "[ANIM_REC]" not in line:
                continue
            r = parse(line)
            if r:
                rows.append(r)

    print(f"총 ANIM_REC 파싱: {len(rows)}")
    sms_dist = Counter(r["sms"] for r in rows)
    print("sms 분포:", {SMS_NAME.get(k, k): v for k, v in sorted(sms_dist.items())})

    # Stop 끼임 = TransitToGroundIdle(sms=2) 진입 & svmag 높음(진짜정지 아님)
    onsets = []
    for i in range(1, len(rows)):
        cur, prev = rows[i], rows[i - 1]
        if cur["sms"] == 2 and prev["sms"] != 2:  # TransitToGroundIdle 진입 엣지
            if cur["svmag"] is not None and cur["svmag"] >= sv_thresh:
                onsets.append(i)

    print(f"\n=== TransitToGroundIdle 진입(sms!=2 → 2) & svmag>={sv_thresh}: {len(onsets)}건 ===")

    def classify(idx):
        win = rows[max(0, idx - pre):idx + 1]
        via9 = any(r["sms"] == 9 for r in win)
        prev_sms = rows[idx - 1]["sms"]
        return via9, prev_sms

    # 전수 집계
    via_all = Counter()
    prev_all = Counter()
    lockon_idx, sprint_idx, lockon_sprint_idx = [], [], []
    for idx in onsets:
        via9, prev_sms = classify(idx)
        via_all["via _toTTGI(9)" if via9 else "직접(9 안거침)"] += 1
        prev_all[SMS_NAME.get(prev_sms, prev_sms)] += 1
        c = rows[idx]
        is_lockon = c["rrr"] == "LockOnTarget"
        is_sprint = "Sprint" in c["seq"]
        if is_lockon:
            lockon_idx.append(idx)
        if is_sprint:
            sprint_idx.append(idx)
        if is_lockon and is_sprint:
            lockon_sprint_idx.append(idx)

    print("진입 경로 전수:", dict(via_all))
    print("직전 스테이트 전수:", dict(prev_all.most_common()))
    print(f"\nrrr=LockOnTarget onset: {len(lockon_idx)} / Sprint seq: {len(sprint_idx)} / 둘다(브리핑 버그): {len(lockon_sprint_idx)}")

    def dump(label, idxs):
        print(f"\n=== {label} (최대 25) ===")
        via = Counter()
        for idx in idxs[:25]:
            seg = rows[max(0, idx - pre): idx + 2]
            path = " → ".join(f"{SMS_NAME.get(r['sms'], r['sms'])}({r['sms']})" for r in seg)
            via9 = any(r["sms"] == 9 for r in rows[max(0, idx - pre):idx + 1])
            via["via9" if via9 else "직접"] += 1
            c = rows[idx]
            sv = c["svmag"] if c["svmag"] is not None else -1
            print(f"f={c['f']} sv={sv:.0f} fv={c['fv']} rrr={c['rrr']} seq={c['seq']}")
            print(f"   {path}")
        print(f"  → 경로: {dict(via)}")

    if lockon_sprint_idx:
        dump("LockOnTarget + Sprint (브리핑 버그 정조준)", lockon_sprint_idx)
    if lockon_idx:
        dump("LockOnTarget 전체", lockon_idx)


if __name__ == "__main__":
    main()
