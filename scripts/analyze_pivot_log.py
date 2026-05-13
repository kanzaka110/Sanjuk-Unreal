"""Pivot 구간 끼어듦 분석.

PC_01_ABP가 SB2_2.log에 쏘는 [ANIM_REC] 23필드 라인에서 Pivot 후보 구간을
TrjTurnAngle(tta) + SearchCost(sc) 변화로 추정. Pivot 도중 다른 모션이
끼어드는 패턴을 자동 검출.

휴리스틱:
- Pivot 시작: |tta| > TTA_PIVOT_THRESHOLD 가 시작
- Pivot 종료: |tta| < TTA_END_THRESHOLD 가 지속
- "끼어듦" 후보:
  (a) Pivot 구간 < MIN_PIVOT_FRAMES (너무 짧음 - 시작 직후 cut)
  (b) sc 급변 (>SC_JUMP) 가 구간 내 발생 (MM이 클립 점프)
  (c) trd 부호 반전 (회전 방향 뒤집힘)

사용법:
    python analyze_pivot_log.py
    python analyze_pivot_log.py --log "<path>" --tail 20000
"""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

DEFAULT_LOG = r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2_2.log"
PREFIX = "[ANIM_REC]"
INSTANCE_RE = re.compile(r"\[PC_01_ABP_C_(\d+)\]")

TTA_PIVOT_THRESHOLD = 45.0
TTA_END_THRESHOLD = 15.0
MIN_PIVOT_FRAMES = 6
SC_JUMP = 15.0
SC_RESELECT = 30.0

ANIMSTANCE = {"0": "NORMAL", "1": "BATTLE", "2": "BATTLE_GUARD", "3": "WRIGGLE"}
MOVEMENTSTATE = {"0": "Idle", "1": "Moving", "2": "Falling"}
PENDINGWALK = {"0": "Walk", "1": "Run", "2": "Sprint"}

log = logging.getLogger("pivot")


@dataclass(frozen=True)
class Tick:
    f: int
    sp: float
    asv: str
    ms: str
    ist: bool
    he: bool
    pwm: str
    il: bool
    isf: bool
    isc: bool
    csh: bool
    trd: float
    rmf: str
    fik: float
    fca: float
    ow: float
    sc: float
    sdt: float
    tta: float
    sdpt: bool


@dataclass
class PivotWindow:
    start_idx: int
    end_idx: int
    ticks: list[Tick]
    sc_jumps: list[tuple[int, float, float]]
    trd_flips: list[tuple[int, float, float]]
    tta_max: float
    tta_min: float


def _to_bool(v: str) -> bool:
    return v.strip().lower() == "true"


def _to_float(v: str) -> float:
    try:
        return float(v)
    except ValueError:
        return 0.0


def parse_line(raw: str) -> Tick | None:
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
    try:
        return Tick(
            f=int(fields.get("f", "0")),
            sp=_to_float(fields.get("sp", "0")),
            asv=ANIMSTANCE.get(fields.get("as", ""), fields.get("as", "?")),
            ms=MOVEMENTSTATE.get(fields.get("ms", ""), fields.get("ms", "?")),
            ist=_to_bool(fields.get("ist", "false")),
            he=_to_bool(fields.get("he", "false")),
            pwm=PENDINGWALK.get(fields.get("pwm", ""), fields.get("pwm", "?")),
            il=_to_bool(fields.get("il", "false")),
            isf=_to_bool(fields.get("isf", "false")),
            isc=_to_bool(fields.get("isc", "false")),
            csh=_to_bool(fields.get("csh", "false")),
            trd=_to_float(fields.get("trd", "0")),
            rmf=fields.get("rmf", "None"),
            fik=_to_float(fields.get("fik", "0")),
            fca=_to_float(fields.get("fca", "0")),
            ow=_to_float(fields.get("ow", "0")),
            sc=_to_float(fields.get("sc", "0")),
            sdt=_to_float(fields.get("sdt", "0")),
            tta=_to_float(fields.get("tta", "0")),
            sdpt=_to_bool(fields.get("sdpt", "false")),
        )
    except (ValueError, KeyError):
        return None


def iter_ticks(path: Path, tail_lines: int | None) -> Iterator[Tick]:
    if not path.exists():
        raise FileNotFoundError(path)
    raw_lines: list[str]
    if tail_lines is None:
        with open(path, encoding="utf-8", errors="ignore") as f:
            raw_lines = [ln for ln in f if PREFIX in ln]
    else:
        with open(path, encoding="utf-8", errors="ignore") as f:
            all_lines = [ln for ln in f if PREFIX in ln]
        raw_lines = all_lines[-tail_lines:]
    seen_frame: int | None = None
    last_instance: str | None = None
    for raw in raw_lines:
        m = INSTANCE_RE.search(raw)
        instance = m.group(1) if m else "?"
        tick = parse_line(raw)
        if tick is None:
            continue
        if last_instance is None:
            last_instance = instance
        if instance != last_instance:
            continue
        if tick.f == seen_frame:
            continue
        seen_frame = tick.f
        yield tick


def find_pivots(ticks: list[Tick]) -> list[PivotWindow]:
    """tta 절댓값 임계로 Pivot 구간 윈도 추출 + 내부 sc/trd 이상치 기록."""
    windows: list[PivotWindow] = []
    n = len(ticks)
    i = 0
    while i < n:
        if abs(ticks[i].tta) < TTA_PIVOT_THRESHOLD:
            i += 1
            continue
        start = i
        j = i + 1
        while j < n and abs(ticks[j].tta) >= TTA_END_THRESHOLD:
            j += 1
        end = j - 1
        sub = ticks[start:end + 1]
        sc_jumps: list[tuple[int, float, float]] = []
        trd_flips: list[tuple[int, float, float]] = []
        for k in range(1, len(sub)):
            prev_sc = sub[k - 1].sc
            cur_sc = sub[k].sc
            if abs(cur_sc - prev_sc) >= SC_JUMP:
                sc_jumps.append((start + k, prev_sc, cur_sc))
            prev_trd = sub[k - 1].trd
            cur_trd = sub[k].trd
            if prev_trd * cur_trd < 0 and abs(prev_trd) > 0.3 and abs(cur_trd) > 0.3:
                trd_flips.append((start + k, prev_trd, cur_trd))
        windows.append(PivotWindow(
            start_idx=start,
            end_idx=end,
            ticks=sub,
            sc_jumps=sc_jumps,
            trd_flips=trd_flips,
            tta_max=max(t.tta for t in sub),
            tta_min=min(t.tta for t in sub),
        ))
        i = j
    return windows


def classify(w: PivotWindow) -> list[str]:
    issues: list[str] = []
    length = w.end_idx - w.start_idx + 1
    if length < MIN_PIVOT_FRAMES:
        issues.append(f"TOO_SHORT({length}f)")
    if w.sc_jumps:
        issues.append(f"SC_JUMPS({len(w.sc_jumps)})")
    if w.trd_flips:
        issues.append(f"TRD_FLIP({len(w.trd_flips)})")
    big_sc = [t for t in w.ticks if t.sc >= SC_RESELECT]
    if big_sc:
        issues.append(f"HIGH_SC({len(big_sc)}/{length})")
    return issues


def fmt_tick(t: Tick) -> str:
    return (
        f"f={t.f} sp={t.sp:6.1f} ms={t.ms:<7} as={t.asv:<13} pwm={t.pwm:<6} "
        f"il={'T' if t.il else 'F'} isf={'T' if t.isf else 'F'} "
        f"isc={'T' if t.isc else 'F'} csh={'T' if t.csh else 'F'} "
        f"trd={t.trd:+6.2f} tta={t.tta:+7.2f} sc={t.sc:6.2f} rmf={t.rmf}"
    )


def print_report(windows: list[PivotWindow], total_ticks: int) -> None:
    print(f"\n총 {total_ticks} ticks, Pivot 후보 구간 {len(windows)}개\n")
    print("=" * 100)
    suspicious: list[tuple[PivotWindow, list[str]]] = []
    for w in windows:
        flags = classify(w)
        if flags:
            suspicious.append((w, flags))

    print(f"\n[요약] 의심 구간 {len(suspicious)}/{len(windows)}\n")
    if suspicious:
        print(f"{'idx':>6} {'len':>4} {'tta_max':>9} {'tta_min':>9} {'issues'}")
        for w, flags in suspicious:
            length = w.end_idx - w.start_idx + 1
            print(f"{w.start_idx:>6} {length:>4} {w.tta_max:+9.2f} {w.tta_min:+9.2f}  {' '.join(flags)}")

    print()
    print("=" * 100)
    print("[상세] 의심 구간 최대 15개")
    print("=" * 100)
    for idx, (w, flags) in enumerate(suspicious[:15]):
        length = w.end_idx - w.start_idx + 1
        print(f"\n--- Pivot #{idx + 1}  idx={w.start_idx}..{w.end_idx}  len={length}f"
              f"  tta=[{w.tta_min:+.2f},{w.tta_max:+.2f}]  issues={' '.join(flags)} ---")
        for k, t in enumerate(w.ticks):
            mark = ""
            tick_idx = w.start_idx + k
            for (ji, prev, cur) in w.sc_jumps:
                if ji == tick_idx:
                    mark += f"  <SC {prev:.1f}->{cur:.1f}>"
            for (fi, prev, cur) in w.trd_flips:
                if fi == tick_idx:
                    mark += f"  <TRD {prev:+.2f}->{cur:+.2f}>"
            print(f"  {fmt_tick(t)}{mark}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--tail", type=int, default=None, help="마지막 N라인만 분석")
    args = ap.parse_args()

    path = Path(args.log)
    ticks = list(iter_ticks(path, args.tail))
    if not ticks:
        log.warning("ANIM_REC 라인 0건")
        return

    windows = find_pivots(ticks)
    print_report(windows, len(ticks))


if __name__ == "__main__":
    main()
