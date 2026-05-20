#!/usr/bin/env python3
"""TrjIsCircling 펄싱 분석.

SB2_2.log의 [ANIM_REC] 라인에서 isc(TrjIsCircling) 시퀀스를 추출,
펄싱(true↔false 토글)이 일어나는 구간에서 관련 필드를 함께 덤프해
원인 후보(csh/tta/sp/pwm/il/isf)를 짚는다.
"""
from __future__ import annotations

import re
from pathlib import Path

LOG = Path(r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2.log")
PREFIX = "[ANIM_REC]"

# 관심 필드
WATCH = ["f", "sp", "pwm", "il", "isf", "isc", "csh", "trd", "tta", "ms", "sdt", "sdpt"]


def parse_line(raw: str) -> dict[str, str] | None:
    idx = raw.find(PREFIX)
    if idx < 0:
        return None
    body = raw[idx + len(PREFIX):].strip()
    parts = re.split(r',?"([a-z]+)"=', body)
    if len(parts) < 3:
        return None
    fields: dict[str, str] = {}
    i = 1
    while i + 1 < len(parts):
        key = parts[i]
        val = re.sub(r"(\d),(\d)", r"\1\2", parts[i + 1]).rstrip(",").strip()
        fields[key] = val
        i += 2
    return fields


def main() -> None:
    recs: list[dict[str, str]] = []
    with LOG.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if PREFIX in line:
                rec = parse_line(line)
                if rec and "isc" in rec:
                    recs.append(rec)

    print(f"총 ANIM_REC 라인(isc 포함): {len(recs)}")
    if not recs:
        return

    # isc 토글 카운트
    toggles = 0
    runs: list[tuple[str, int]] = []  # (value, run_length)
    cur = recs[0]["isc"]
    run = 0
    for r in recs:
        v = r["isc"]
        if v == cur:
            run += 1
        else:
            runs.append((cur, run))
            toggles += 1
            cur = v
            run = 1
    runs.append((cur, run))

    print(f"isc 토글 횟수: {toggles}")
    print(f"isc run 분포 (값, 연속프레임수):")
    for v, ln in runs:
        bar = "#" * min(ln, 60)
        print(f"  isc={v:<5} x{ln:<4} {bar}")

    # true run 중 매우 짧은 것(<=3) = 펄스, false run 중 짧은 것 = 끊김
    print("\n--- 짧은 false 끊김 구간 주변 덤프 (회전 유지 중 isc가 false로 떨어진 순간) ---")
    # 인덱스 재구성
    idx = 0
    boundaries = []
    for v, ln in runs:
        boundaries.append((v, idx, idx + ln))
        idx += ln

    dumped = 0
    for bi, (v, start, end) in enumerate(boundaries):
        ln = end - start
        # false run 이면서 양옆이 true(=회전 중 잠깐 끊김)
        if v == "false" and 0 < bi < len(boundaries) - 1:
            prev_v = boundaries[bi - 1][0]
            next_v = boundaries[bi + 1][0]
            if prev_v == "true" and next_v == "true" and ln <= 8:
                if dumped >= 6:
                    break
                dumped += 1
                print(f"\n[끊김 #{dumped}] false {ln}프레임 (true→false→true)")
                lo = max(0, start - 2)
                hi = min(len(recs), end + 2)
                hdr = " | ".join(f"{k:>6}" for k in WATCH)
                print("  " + hdr)
                for r in recs[lo:hi]:
                    mark = "<<" if start <= recs.index(r) < end else "  "
                    row = " | ".join(f"{r.get(k,'-'):>6}" for k in WATCH)
                    print(f"  {row} {mark}")

    if dumped == 0:
        print("  (true→false→true 짧은 끊김 패턴 없음 — 전체 시퀀스 샘플 출력)")
        hdr = " | ".join(f"{k:>6}" for k in WATCH)
        print("  " + hdr)
        for r in recs[: min(40, len(recs))]:
            row = " | ".join(f"{r.get(k,'-'):>6}" for k in WATCH)
            print("  " + row)


if __name__ == "__main__":
    main()
