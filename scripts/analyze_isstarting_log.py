"""
Analyze ANIM_REC log to find frames where IsStarting (ist) should fire but doesn't,
or fires but Start state doesn't engage.

Log line format example:
[ts][frame]LogBlueprintUserMessages: [PC_01_ABP_C_N] [ANIM_REC] "f"=4322,"sp"=0,"as"=0,...

Key fields:
  f    : frame
  sp   : speed (current cm/s scalar?)
  as   : AnimStance enum
  ms   : MovementState enum (likely 0=Ground/Idle, 1=Ground/Moving, 2=Falling)
  ist  : IsStarting bool (this is what we are debugging)
  he   : HasEvade
  vlen : velocity length (acceleration source magnitude)
  pwm  : PendingWalkMode
  il   : IsLockOn
  isf  : IsFalling
  isc  : IsCrouching
  csh  : ?
  trd  : trajectory dir? signed
  ib   : ?
  rmf  : RuleMoveFlag
  fik  : foot IK alpha
  fca  : foot clamp alpha
  ow   : ?
  ig   : ?
  sc   : speed scalar (cm/s)
  sdt  : (legacy, ignore)
  tta  : trajectory turn angle
  sdpt : (legacy, ignore)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LOG_PATH = Path(r"C:/Dev/Sanjuk-Unreal/Saved/anim_rec_step8_latest.jsonl")

ANIM_REC_RE = re.compile(r"\[ANIM_REC\] (.+)$")
KV_RE = re.compile(r'"([^"]+)"=([^,]+)')


def parse_value(v: str):
    v = v.strip()
    if v == "true":
        return True
    if v == "false":
        return False
    if v == "None":
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


def parse_line(line: str) -> dict | None:
    m = ANIM_REC_RE.search(line)
    if not m:
        return None
    body = m.group(1)
    pairs = KV_RE.findall(body)
    return {k: parse_value(v) for k, v in pairs}


def load_records(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            rec = parse_line(line.rstrip("\n"))
            if rec is not None:
                out.append(rec)
    return out


def dedup_by_frame(records: list[dict]) -> list[dict]:
    """Keep last record per frame so we see end-of-tick state."""
    by_f: dict[int, dict] = {}
    for r in records:
        f = r.get("f")
        if f is None:
            continue
        by_f[f] = r
    return [by_f[k] for k in sorted(by_f.keys())]


def find_starts(records: list[dict]):
    """
    Detect movement-start moments and check IsStarting behavior.

    A 'start' is intuitively: speed goes from ~0 to >threshold (e.g., 5 cm/s).
    For each start, report:
      - whether ist was true at the same frame
      - whether ist was true at the prev frame (latched)
      - duration ist remained true (latch length)
      - whether ms was 0 -> 1 (idle -> moving)
    """
    THRESH_LO = 5.0
    THRESH_HI = 50.0

    starts = []
    for i in range(1, len(records)):
        prev = records[i - 1]
        cur = records[i]
        sp_prev = float(prev.get("sp", 0) or 0)
        sp_cur = float(cur.get("sp", 0) or 0)
        ms_prev = prev.get("ms")
        ms_cur = cur.get("ms")

        is_start_event = (sp_prev <= THRESH_LO and sp_cur > THRESH_LO) or (
            ms_prev == 0 and ms_cur == 1
        )
        if not is_start_event:
            continue

        # Look ahead a window to measure ist behavior
        window = records[i : i + 30]
        ist_seq = [bool(r.get("ist", False)) for r in window]
        ist_true_count = sum(1 for x in ist_seq if x)
        ist_fired = any(ist_seq)
        first_ist_offset = next((k for k, v in enumerate(ist_seq) if v), None)

        starts.append(
            {
                "frame": cur.get("f"),
                "sp_prev": sp_prev,
                "sp_cur": sp_cur,
                "ms_prev": ms_prev,
                "ms_cur": ms_cur,
                "ist_at_start": bool(cur.get("ist", False)),
                "ist_fired_in_30f": ist_fired,
                "ist_first_offset": first_ist_offset,
                "ist_true_count_30f": ist_true_count,
                "vlen": cur.get("vlen"),
                "pwm": cur.get("pwm"),
                "il": cur.get("il"),
                "rmf": cur.get("rmf"),
                "ib": cur.get("ib"),
                "as": cur.get("as"),
            }
        )
    return starts


def main():
    records = load_records(LOG_PATH)
    print(f"loaded {len(records)} ANIM_REC lines")
    deduped = dedup_by_frame(records)
    print(f"unique frames: {len(deduped)} "
          f"(range {deduped[0]['f']} .. {deduped[-1]['f']})")

    starts = find_starts(deduped)
    print(f"\nDetected {len(starts)} movement-start events:\n")
    print(
        f"{'frame':>6}  {'sp_prev':>7}  {'sp_cur':>7}  {'ms':>5}  "
        f"{'ist0':>4}  {'fired30':>7}  {'offset':>6}  {'ist#':>4}  "
        f"{'vlen':>5}  {'pwm':>3}  {'il':>2}  {'as':>2}  {'rmf':>16}"
    )
    for s in starts:
        ms_str = f"{s['ms_prev']}>{s['ms_cur']}"
        ist0 = "T" if s["ist_at_start"] else "F"
        fired = "T" if s["ist_fired_in_30f"] else "F"
        offset = "-" if s["ist_first_offset"] is None else str(s["ist_first_offset"])
        print(
            f"{s['frame']:>6}  {s['sp_prev']:>7.1f}  {s['sp_cur']:>7.1f}  "
            f"{ms_str:>5}  {ist0:>4}  {fired:>7}  {offset:>6}  "
            f"{s['ist_true_count_30f']:>4}  {s['vlen']!s:>5}  "
            f"{s['pwm']!s:>3}  {s['il']!s:>2}  {s['as']!s:>2}  {str(s['rmf']):>16}"
        )

    # Group: starts where ist NEVER fired in 30f window after the event
    bad = [s for s in starts if not s["ist_fired_in_30f"]]
    print(
        f"\n=== Starts where IsStarting NEVER fired within 30 frames: {len(bad)} ==="
    )
    for s in bad:
        print(
            f"  frame={s['frame']} sp:{s['sp_prev']}>{s['sp_cur']} "
            f"ms:{s['ms_prev']}>{s['ms_cur']} vlen={s['vlen']} "
            f"pwm={s['pwm']} il={s['il']} as={s['as']} rmf={s['rmf']}"
        )

    # Group: starts where ist fired but only 1 frame (B trigger only, no latch)
    short = [
        s
        for s in starts
        if s["ist_fired_in_30f"] and s["ist_true_count_30f"] <= 1
    ]
    print(
        f"\n=== Starts where IsStarting was a single-frame blip (latch failed): "
        f"{len(short)} ==="
    )
    for s in short:
        print(
            f"  frame={s['frame']} offset={s['ist_first_offset']} "
            f"sp:{s['sp_prev']}>{s['sp_cur']} vlen={s['vlen']} "
            f"pwm={s['pwm']} il={s['il']} as={s['as']}"
        )


if __name__ == "__main__":
    main()
