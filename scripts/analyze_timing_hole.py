#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""질주 반전 1프레임 Stop 홀(rrr lag) 검출기.

5/22 가드 `NOT(rrr==LockOnTarget)`는 락온 질주 반전 onset의 Stop 끼임을 막지만,
rrr(RetransitReason)이 반전 inflection 대비 1프레임 늦게 SET되면 그 1틱 동안
가드가 통과 → TransitToGroundIdle 1프레임 진입 → Stop 클립 끼임.

홀 시그니처(진짜 정지 Jog_Stop 과 구분):
  - 직전 1~3프레임에 sms=1(GroundMoving) = 직전까지 이동 중
  - 현재 sms=2(TransitToGroundIdle) + seq에 Stop + 고속(sv 또는 sp > min)
  - 1~3프레임 내 Stop 아닌 seq 로 복귀 (= 자가교정, 진짜 정지가 아님)
검출 시 rrr/bim/fv 타이밍을 출력해 lag 본질(rrr이 inflection보다 늦나) 판정.

사용법:
    python analyze_timing_hole.py                 # 활성 로그 전체
    python analyze_timing_hole.py --log dumps/anim_recent.txt
    python analyze_timing_hole.py --tail 6000     # 마지막 N ANIM_REC 라인
"""
from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

DEFAULT_LOG = r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2.log"
PREFIX = "[ANIM_REC]"
SCALAR_RE = re.compile(r'"([a-z_0-9]+)"=([^",\s]+)')
SV_RE = re.compile(r'"sv"=X=(-?[\d.]+) Y=(-?[\d.]+)')


def _f(v: str) -> float:
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return 0.0


@dataclass(frozen=True)
class Tick:
    f: int
    seq: str
    isf: bool
    bim: bool
    rrr: str
    fv: float
    acc: float
    sms: str
    sp: float
    sv: float
    ip: bool


def parse_line(raw: str) -> Tick | None:
    idx = raw.find(PREFIX)
    if idx < 0:
        return None
    body = re.sub(r"(\d),(\d)", r"\1\2", raw[idx:])
    d = dict(SCALAR_RE.findall(body))
    if "f" not in d:
        return None
    svm = SV_RE.search(body)
    sv = math.hypot(float(svm.group(1)), float(svm.group(2))) if svm else 0.0
    return Tick(
        f=int(_f(d.get("f", "0"))),
        seq=d.get("seq", ""),
        isf=d.get("isf") == "true",
        bim=d.get("bim") == "true",
        rrr=d.get("rrr", "None"),
        fv=_f(d.get("fv", "0")),
        acc=_f(d.get("acc", "0")),
        sms=d.get("sms", "?"),
        sp=_f(d.get("sp", "0")),
        sv=sv,
        ip=d.get("ip") == "true",
    )


def iter_ticks(path: Path, tail: int | None) -> Iterator[Tick]:
    with open(path, encoding="utf-8", errors="ignore") as fh:
        lines = [ln for ln in fh if PREFIX in ln]
    if tail:
        lines = lines[-tail:]
    seen: int | None = None
    for raw in lines:
        t = parse_line(raw)
        if t is None or t.f == seen:
            continue
        seen = t.f
        yield t


def find_holes(ticks: list[Tick], min_speed: float = 200.0) -> list[int]:
    out: list[int] = []
    n = len(ticks)
    for i in range(3, n - 3):
        t = ticks[i]
        if t.isf or t.sms != "2" or "Stop" not in t.seq:
            continue
        if t.sv < min_speed and t.sp < min_speed:
            continue
        was_moving = any(ticks[i - k].sms == "1" for k in (1, 2, 3))
        recovers = any("Stop" not in ticks[i + k].seq for k in (1, 2, 3))
        if was_moving and recovers:
            out.append(i)
    return out


def fmt(t: Tick, mark: str = "") -> str:
    return (
        f"  f={t.f} sms={t.sms} bim={'T' if t.bim else 'F'} fv={t.fv:7.1f} "
        f"acc={t.acc:7.1f} rrr={t.rrr:<12} sv={t.sv:6.1f} sp={t.sp:6.1f} "
        f"ip={'T' if t.ip else 'F'} seq={t.seq[:30]}{mark}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--tail", type=int, default=None)
    ap.add_argument("--max", type=int, default=10)
    args = ap.parse_args()

    ticks = list(iter_ticks(Path(args.log), args.tail))
    holes = find_holes(ticks)
    print(f"총 {len(ticks)} ticks  |  질주 반전 1프레임 Stop 홀 {len(holes)}건\n")

    lag_late = 0   # rrr 이 홀 프레임엔 None, 직후 LockOnTarget (= 1프레임 lag 증거)
    lag_sync = 0   # rrr 이 홀 프레임에 이미 LockOnTarget (= lag 아님)
    for idx in holes:
        t = ticks[idx]
        nxt = ticks[idx + 1]
        if t.rrr == "None" and nxt.rrr == "LockOnTarget":
            lag_late += 1
        elif t.rrr == "LockOnTarget":
            lag_sync += 1

    if holes:
        print(f"[lag 판정] rrr 1프레임 늦음(None→LockOnTarget) {lag_late}  |  "
              f"동기 SET(이미 LockOnTarget) {lag_sync}\n")
        print("=" * 100)
        for idx in holes[:args.max]:
            print(f"--- hole @ f={ticks[idx].f} ---")
            for j in range(idx - 3, idx + 4):
                if 0 <= j < len(ticks):
                    print(fmt(ticks[j], "  <<<" if j == idx else ""))
            print()


if __name__ == "__main__":
    main()
