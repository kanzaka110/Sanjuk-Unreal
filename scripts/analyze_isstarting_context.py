"""
Dump full context around the two failing IsStarting frames (85719, 85728).
Show ~40 frames before/after each event so we can see speed/ms transitions.
"""

from __future__ import annotations

import re
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


def parse_line(line: str):
    m = ANIM_REC_RE.search(line)
    if not m:
        return None
    return {k: parse_value(v) for k, v in KV_RE.findall(m.group(1))}


def load_dedup():
    by_f: dict[int, dict] = {}
    with LOG_PATH.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            r = parse_line(line.rstrip("\n"))
            if r and "f" in r:
                by_f[r["f"]] = r
    return [by_f[k] for k in sorted(by_f.keys())]


def dump_window(records, center, before=40, after=40):
    idx_by_f = {r["f"]: i for i, r in enumerate(records)}
    if center not in idx_by_f:
        # find nearest
        keys = sorted(idx_by_f.keys())
        for k in keys:
            if k >= center:
                center = k
                break
    i = idx_by_f[center]
    s = max(0, i - before)
    e = min(len(records), i + after + 1)
    print(f"\n===== window around frame {center} [{s}..{e}] =====")
    print(
        f"{'f':>6} {'sp':>6} {'vlen':>7} {'ms':>2} {'ist':>3} "
        f"{'pwm':>3} {'il':>2} {'as':>2} {'he':>2} {'isf':>3} "
        f"{'rmf':>10} {'tta':>6}"
    )
    for r in records[s:e]:
        flag = " <==" if r["f"] == center else ""
        print(
            f"{r['f']:>6} {float(r.get('sp', 0)):>6.1f} "
            f"{float(r.get('vlen', 0)):>7.2f} "
            f"{r.get('ms')!s:>2} "
            f"{'T' if r.get('ist') else 'F':>3} "
            f"{r.get('pwm')!s:>3} "
            f"{'T' if r.get('il') else 'F':>2} "
            f"{r.get('as')!s:>2} "
            f"{'T' if r.get('he') else 'F':>2} "
            f"{'T' if r.get('isf') else 'F':>3} "
            f"{str(r.get('rmf')):>10} "
            f"{float(r.get('tta', 0)):>6.1f}"
            f"{flag}"
        )


def main():
    recs = load_dedup()
    dump_window(recs, 85522, before=2, after=8)   # known-good baseline
    dump_window(recs, 85719, before=40, after=20)  # bad case 1
    dump_window(recs, 85728, before=15, after=20)  # bad case 2


if __name__ == "__main__":
    main()
