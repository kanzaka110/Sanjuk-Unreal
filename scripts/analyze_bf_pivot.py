#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B→F vs F→B 질주 반전 시 IsPivoting(ip) 발동 비교.

IsPivoting 함수는 정적으로 방향 대칭(Abs(trd), MoveSide!=Prev)이므로,
B→F 미발동의 원인은 입력값 거동에 있다. 이 스크립트는 SB2.log의 현재
리치 ANIM_REC 포맷에서 질주(isf=false) 반전 onset을 찾아 ip/trd/tta/isc/
sv-heading/seq 궤적을 덤프, F→B(전방→후방)와 B→F(후방→전방)를 구분한다.

반전 onset 정의: SmoothedVelocity(sv) heading이 1~수 프레임에 ~180도 뒤집힘.
방향 판정: 반전 직전 sv heading 이 facing(hed) 대비 전방(±90)인지 후방인지.
  - before 전방 → F→B
  - before 후방 → B→F

사용법:
    python analyze_bf_pivot.py --tail 120000
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
INSTANCE_RE = re.compile(r"\[PC_01_ABP_C_(\d+)\]")

# 스칼라 필드: "key"=value (value 는 다음 " 또는 , 또는 공백 전까지)
SCALAR_RE = re.compile(r'"([a-z_0-9]+)"=([^",\s]+)')
# sv 벡터: "sv"=X=.. Y=.. Z=..
SV_RE = re.compile(r'"sv"=X=(-?[\d.]+) Y=(-?[\d.]+) Z=(-?[\d.]+)')


@dataclass(frozen=True)
class Tick:
    f: int
    sp: float
    isf: bool
    isc: bool
    ip: bool
    il: bool
    trd: float
    tta: float
    svx: float
    svy: float
    hed: float
    seq: str
    sms: int
    rrr: str
    bim: bool

    @property
    def sv_mag(self) -> float:
        return math.hypot(self.svx, self.svy)

    @property
    def sv_heading(self) -> float:
        return math.degrees(math.atan2(self.svy, self.svx))


def _f(v: str) -> float:
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return 0.0


def parse_line(raw: str) -> Tick | None:
    idx = raw.find(PREFIX)
    if idx < 0:
        return None
    body = raw[idx + len(PREFIX):]
    # 천단위 콤마 제거 (예: "f"=3,933,903 → 3933903). 디짓-콤마-디짓만.
    body = re.sub(r"(\d),(\d)", r"\1\2", body)
    fields = {k: v for k, v in SCALAR_RE.findall(body)}
    if "f" not in fields:
        return None
    svm = SV_RE.search(body)
    svx, svy = (float(svm.group(1)), float(svm.group(2))) if svm else (0.0, 0.0)
    try:
        return Tick(
            f=int(_f(fields.get("f", "0"))),
            sp=_f(fields.get("sp", "0")),
            isf=fields.get("isf") == "true",
            isc=fields.get("isc") == "true",
            ip=fields.get("ip") == "true",
            il=fields.get("il") == "true",
            trd=_f(fields.get("trd", "0")),
            tta=_f(fields.get("tta", "0")),
            svx=svx,
            svy=svy,
            hed=_f(fields.get("hed", "0")),
            seq=fields.get("seq", "?"),
            sms=int(_f(fields.get("sms", "-1"))),
            rrr=fields.get("rrr", "None"),
            bim=fields.get("bim") == "true",
        )
    except (ValueError, KeyError):
        return None


def iter_ticks(path: Path, tail: int | None) -> Iterator[Tick]:
    with open(path, encoding="utf-8", errors="ignore") as fh:
        lines = [ln for ln in fh if PREFIX in ln]
    if tail:
        lines = lines[-tail:]
    seen = None
    inst0 = None
    for raw in lines:
        m = INSTANCE_RE.search(raw)
        inst = m.group(1) if m else "?"
        if inst0 is None:
            inst0 = inst
        if inst != inst0:
            continue
        t = parse_line(raw)
        if t is None or t.f == seen:
            continue
        seen = t.f
        yield t


def angdiff(a: float, b: float) -> float:
    """최소 각도차 (-180,180]."""
    d = (a - b) % 360.0
    return d - 360.0 if d > 180.0 else d


def find_reversals(ticks: list[Tick], min_speed: float = 100.0) -> list[dict]:
    """sv heading 이 짧은 구간에 ~180 뒤집히는 질주(isf=false) onset 검출."""
    out: list[dict] = []
    n = len(ticks)
    for i in range(2, n - 3):
        t = ticks[i]
        if t.isf:  # 질주(else 분기)만
            continue
        # 반전 전후 heading: i-2 vs i+3 (dip 관통)
        before = ticks[i - 2]
        after = ticks[i + 3]
        if before.sv_mag < min_speed or after.sv_mag < min_speed:
            continue
        flip = abs(angdiff(after.sv_heading, before.sv_heading))
        if flip < 120.0:  # 충분히 큰 방향 전환만
            continue
        # facing(hed, 라디안→도? hed 단위 불명 → 회피: facing 대신 trd 부호로 대용)
        # before 의 sv heading 이 캐릭터 전방인지 후방인지: trd 로 추정 곤란하므로
        # 일단 before/after heading 과 ip 궤적만 기록, 방향 판정은 후처리.
        win = ticks[i - 3:i + 5]
        ip_any = any(w.ip for w in win)
        out.append({
            "idx": i,
            "f": t.f,
            "flip_deg": round(flip, 1),
            "before_head": round(before.sv_heading, 1),
            "after_head": round(after.sv_heading, 1),
            "ip_fired": ip_any,
            "win": win,
        })
    return out


def fmt(t: Tick) -> str:
    return (
        f"f={t.f} sp={t.sp:6.1f} svM={t.sv_mag:6.1f} svH={t.sv_heading:+7.1f} "
        f"trd={t.trd:+7.1f} tta={t.tta:+7.1f} isc={'T' if t.isc else 'F'} "
        f"ip={'T' if t.ip else 'F'} bim={'T' if t.bim else 'F'} sms={t.sms} "
        f"il={'T' if t.il else 'F'} seq={t.seq[:42]}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--tail", type=int, default=120000)
    ap.add_argument("--max", type=int, default=25, help="출력 윈도우 수")
    args = ap.parse_args()

    ticks = list(iter_ticks(Path(args.log), args.tail))
    print(f"총 {len(ticks)} ticks (instance 0)")
    revs = find_reversals(ticks)
    fired = [r for r in revs if r["ip_fired"]]
    missed = [r for r in revs if not r["ip_fired"]]
    print(f"질주 반전 onset {len(revs)}개  |  ip 발동 {len(fired)}  미발동 {len(missed)}\n")

    print("=" * 110)
    print(f"[ip 미발동 윈도우] 최대 {args.max}개")
    print("=" * 110)
    for r in missed[:args.max]:
        print(f"\n--- f={r['f']} flip={r['flip_deg']} "
              f"beforeH={r['before_head']} afterH={r['after_head']} ip_fired=NO ---")
        for w in r["win"]:
            print("  " + fmt(w))


if __name__ == "__main__":
    main()
