#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""달리기→Stop 반응 지연 측정 (rrt fast-path 검증용).

비락온 게이트에 `OR (NOT(IsLockOn) AND NOT(RunRetransit))` fast-path 적용 후,
달리기→Stop 지연이 rrt=false 정지에서 4→2프레임으로 떨어졌는지 검증.
회귀 체크: 비락온 반전 Stop 끼임 0 유지 / 락온 정지 불변.

지연 = 입력 뗌(bim=true→false 전환점)부터 Stop 모션(seq에 _Stop_) 시작까지 프레임.
버킷: 락온(il=true) / 비락온 rrt=false / 비락온 rrt=true.

사용법:
    python analyze_stop_latency.py --log dumps/anim_stopfix.txt
    python analyze_stop_latency.py --tail 6000      # 활성 로그 마지막 N
"""
from __future__ import annotations

import argparse
import re
import statistics as st
from collections import Counter
from pathlib import Path

DEFAULT_LOG = r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2.log"
PREFIX = "[ANIM_REC]"
SCALAR_RE = re.compile(r'"([a-z_0-9]+)"=([^",\s]+)')


def _f(v: str) -> float:
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return 0.0


def load(path: Path, tail: int | None) -> list[dict]:
    with open(path, encoding="utf-8", errors="ignore") as fh:
        lines = [ln for ln in fh if PREFIX in ln]
    if tail:
        lines = lines[-tail:]
    rows: list[dict] = []
    seen = None
    for raw in lines:
        body = re.sub(r"(\d),(\d)", r"\1\2", raw[raw.find(PREFIX):])
        d = dict(SCALAR_RE.findall(body))
        if "f" not in d:
            continue
        f = int(_f(d["f"]))
        if f == seen:
            continue
        seen = f
        rows.append({
            "f": f, "seq": d.get("seq", ""), "sms": d.get("sms", "?"),
            "bim": d.get("bim"), "il": d.get("il"), "rrt": d.get("rrt"),
            "fv": _f(d.get("fv", "0")), "sp": _f(d.get("sp", "0")),
        })
    return rows


def is_stop(s: str) -> bool:
    return ("_Stop_" in s or s.endswith("_Stop")) and "turn_Stop" not in s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--tail", type=int, default=None)
    args = ap.parse_args()
    rows = load(Path(args.log), args.tail)
    print(f"총 {len(rows)} ticks\n")

    buckets: dict[str, list[int]] = {"락온": [], "비락온 rrt=false": [], "비락온 rrt=true": []}
    reversal_stop_intrusion = 0

    for i in range(8, len(rows) - 1):
        if not (is_stop(rows[i]["seq"]) and not is_stop(rows[i - 1]["seq"])):
            continue
        # 직전이 달리기(고속)였나
        if not (rows[i - 1]["sp"] > 250 or any(rows[i - k]["sp"] > 400 for k in range(1, 6))):
            continue
        # bim=true→false 전환점 (입력 뗌)
        fb = None
        for k in range(1, 16):
            j = i - k
            if j < 0:
                break
            if rows[j]["bim"] == "true":
                fb = j + 1
                break
        if fb is None:
            continue
        lat = i - fb
        if rows[i]["il"] == "true":
            buckets["락온"].append(lat)
        elif rows[i]["rrt"] == "false":
            buckets["비락온 rrt=false"].append(lat)
        else:
            buckets["비락온 rrt=true"].append(lat)

    def summ(x: list[int]) -> str:
        if not x:
            return "표본 없음"
        return f"n={len(x):3} median={st.median(x):.0f} mean={st.mean(x):.1f} dist={Counter(x).most_common(5)}"

    print("=== 달리기→Stop 지연 (입력 뗌 → Stop 모션, 프레임) ===")
    for name, x in buckets.items():
        print(f"  {name:18}: {summ(x)}")

    # 회귀 체크: 비락온 질주 반전에서 1프레임 Stop 끼임
    holes = 0
    for i in range(3, len(rows) - 3):
        r = rows[i]
        if r["il"] == "true" or r["sms"] != "2" or "Stop" not in r["seq"]:
            continue
        if r["sp"] < 200 and r["fv"] < 1:  # fv=0 dip + 고속 클립
            pass
        was_moving = any(rows[i - k]["sms"] == "1" for k in (1, 2, 3))
        recovers = any("Stop" not in rows[i + k]["seq"] for k in (1, 2, 3))
        if was_moving and recovers and rows[i]["sp"] > 200:
            holes += 1
    print(f"\n=== 회귀 체크 ===")
    print(f"  비락온 질주 반전 1프레임 Stop 끼임: {holes}건  (0이어야 정상)")


if __name__ == "__main__":
    main()
