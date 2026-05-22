#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""회피(HasEvade) 전/후 클립 끼어듦 진단.

증상: 이동중 → Evade → 이동 으로 매끄럽게 안 이어지고, 회피 발동 순간
Stop/Start 등 엉뚱한 클립이 중간에 끼어듦 (스크린샷 2026-05-22 164755 기준
P_Player_Fist_Battle_Jog_Stop_RL_Rfoot 가 LockOn_Evade 중간에 블렌드).

he=false→true→false 에피소드마다 진입 전 ~N 프레임, 회피 중, 종료 후 ~M
프레임의 seq/clip/pwm/rmf/ms/sms/bim/ist 를 덤프해서 어느 변수 상태가
Stop/Jog 클립을 유발했는지 확정한다.

사용법:
    python analyze_evade_intrusion.py --tail 200000 --pre 12 --post 30
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

DEFAULT_LOG = r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2.log"
PREFIX = "[ANIM_REC]"
INSTANCE_RE = re.compile(r"\[PC_01_ABP_C_(\d+)\]")
SCALAR_RE = re.compile(r'"([a-z_0-9]+)"=([^",\s]+)')

# 끼어듦으로 간주할 클립 키워드 (회피 경로가 아닌 것)
INTRUDER_KEYS = ("Stop", "TurnInPlace", "Idle")


@dataclass(frozen=True)
class Tick:
    f: int
    sp: float
    ms: int
    sms: int
    he: bool
    bim: bool
    ist: bool
    ip: bool
    pwm: int
    ppwm: int
    rmf: str
    seq: str
    clip: str
    il: bool

    @property
    def is_intruder(self) -> bool:
        return any(k in self.seq for k in INTRUDER_KEYS)

    @property
    def is_evade_clip(self) -> bool:
        return "Evade" in self.seq


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
    body = re.sub(r"(\d),(\d)", r"\1\2", body)
    fields = {k: v for k, v in SCALAR_RE.findall(body)}
    if "f" not in fields:
        return None
    try:
        return Tick(
            f=int(_f(fields.get("f", "0"))),
            sp=_f(fields.get("sp", "0")),
            ms=int(_f(fields.get("ms", "-1"))),
            sms=int(_f(fields.get("sms", "-1"))),
            he=fields.get("he") == "true",
            bim=fields.get("bim") == "true",
            ist=fields.get("ist") == "true",
            ip=fields.get("ip") == "true",
            pwm=int(_f(fields.get("pwm", "-1"))),
            ppwm=int(_f(fields.get("ppwm", "-1"))),
            rmf=fields.get("rmf", "?"),
            seq=fields.get("seq", "?"),
            clip=fields.get("clip", "?"),
            il=fields.get("il") == "true",
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


def find_episodes(ticks: list[Tick]) -> list[tuple[int, int]]:
    """he=true 연속 구간 (start_idx, end_idx) 리스트."""
    eps = []
    i, n = 0, len(ticks)
    while i < n:
        if ticks[i].he:
            j = i
            while j < n and ticks[j].he:
                j += 1
            eps.append((i, j - 1))
            i = j
        else:
            i += 1
    return eps


def fmt(t: Tick, marker: str = " ") -> str:
    flags = (
        f"he={'T' if t.he else '.'} bim={'T' if t.bim else '.'} "
        f"ist={'T' if t.ist else '.'} ip={'T' if t.ip else '.'} il={'T' if t.il else '.'}"
    )
    return (
        f"{marker}f={t.f} sp={t.sp:6.1f} ms={t.ms} sms={t.sms} "
        f"pwm={t.pwm} ppwm={t.ppwm} rmf={t.rmf:<8} {flags} "
        f"clip={t.clip:<10} seq={t.seq[:46]}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--tail", type=int, default=200000)
    ap.add_argument("--pre", type=int, default=12)
    ap.add_argument("--post", type=int, default=30)
    ap.add_argument("--max", type=int, default=12)
    args = ap.parse_args()

    ticks = list(iter_ticks(Path(args.log), args.tail))
    print(f"총 {len(ticks)} ticks (instance 0)")
    eps = find_episodes(ticks)
    print(f"HasEvade 에피소드 {len(eps)}개\n")

    # 끼어듦 있는 에피소드 우선
    scored = []
    for (s, e) in eps:
        lo = max(0, s - args.pre)
        hi = min(len(ticks) - 1, e + args.post)
        win = ticks[lo:hi + 1]
        intr = [w for w in win if w.is_intruder]
        scored.append((len(intr), s, e, lo, hi, win, intr))
    scored.sort(key=lambda x: -x[0])

    shown = 0
    for ninr, s, e, lo, hi, win, intr in scored:
        if shown >= args.max:
            break
        shown += 1
        dur = ticks[e].f - ticks[s].f + 1
        print("=" * 120)
        print(f"[에피소드] he구간 f={ticks[s].f}~{ticks[e].f} ({dur}f)  "
              f"끼어듦 클립 {ninr}개")
        if intr:
            uniq = sorted({w.seq for w in intr})
            print(f"  끼어든 seq: {uniq}")
        print("-" * 120)
        for w in win:
            mk = ">" if (w.he) else " "
            if w.is_intruder:
                mk = "!"
            print(fmt(w, mk))
        print()


if __name__ == "__main__":
    main()
