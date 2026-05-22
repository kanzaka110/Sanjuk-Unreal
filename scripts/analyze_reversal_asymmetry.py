"""질주 반전 F<->B 비대칭 분석.

PC_01_ABP [ANIM_REC] 로그에서 MoveSide(ms_l) 전환으로 반전 이벤트를 자동 검출하고,
각 윈도우의 핵심 필드를 프레임별로 덤프한다. F->B(Stop 끼임)와 B->F(피봇 정상)가
어디서 갈리는지(특히 fv=TrjFutureVelocity, acc=Acceleration, ip, seq, ms)를 비교용.

ms_l 매핑(확정): 0=F(전방), 2=R(우), 4=B(후방), 6=L(좌)

사용법:
    python analyze_reversal_asymmetry.py                    # SB2.log tail 자동
    python analyze_reversal_asymmetry.py --tail 60000
    python analyze_reversal_asymmetry.py --log "<path>" --window 12

주의: 다중 PIE 세션 분리 필수. SB2.log 는 세션이 누적되고 "f" tick 이
세션마다 리셋됨. 특정 세션만 보려면 'up for play' 라인 기준으로 슬라이스
(grep -n "up for play") 후 --log 로 전달. dedup 은 연속 중복줄만 skip
(글로벌 dedup 금지 — 세션간 tick 충돌로 데이터 붕괴).
"""
from __future__ import annotations
import argparse, math, re
from pathlib import Path

DEFAULT_LOG = r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2.log"
KEY_RE = re.compile(r'"([a-zA-Z_0-9]+)"\s*=')
MS_L = {"0": "F", "2": "R", "4": "B", "6": "L"}
# 관심 방향: 전방(0) <-> 후방(4) 반전만 (F<->B). 좌우는 무시 옵션
FWD, BWD = "0", "4"

# 출력 컬럼
COLS = ["f", "ms", "ms_l", "sp", "svxy", "fv", "acc", "trd", "ip", "isf", "isc",
        "na", "rrt", "rrr", "sc", "ch_mm", "seq"]


def parse_line(line: str) -> dict | None:
    if "[ANIM_REC]" not in line:
        return None
    body = line.split("[ANIM_REC]", 1)[1]
    keys = [(m.group(1), m.start(), m.end()) for m in KEY_RE.finditer(body)]
    if not keys:
        return None
    d = {}
    for i, (name, _s, e) in enumerate(keys):
        nxt = keys[i + 1][1] if i + 1 < len(keys) else len(body)
        val = body[e:nxt].strip().strip(",").strip()
        d[name] = val
    return d


def sv_xy(raw: str) -> float:
    # "sv" value form: X=0.000 Y=0.000 Z=0.000
    mx = re.search(r"X=(-?[\d.]+)", raw or "")
    my = re.search(r"Y=(-?[\d.]+)", raw or "")
    if not (mx and my):
        return 0.0
    return math.hypot(float(mx.group(1)), float(my.group(1)))


def frame_no(d: dict) -> int:
    # "f"=324,122  -> tick number = second part
    f = d.get("f", "")
    parts = f.split(",")
    try:
        return int(parts[-1])
    except ValueError:
        return -1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--tail", type=int, default=80000, help="마지막 N줄만")
    ap.add_argument("--window", type=int, default=14, help="반전 전후 프레임")
    args = ap.parse_args()

    path = Path(args.log)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if args.tail:
        lines = lines[-args.tail:]

    # 로그 순서 유지(글로벌 정렬 금지 — 세션간 tick 리셋으로 뒤섞임).
    # dedup 은 연속 중복줄만 skip (메모리: 전역 frame-dedup 금지).
    rows = []
    prev_f = None
    for ln in lines:
        d = parse_line(ln)
        if not d:
            continue
        fn = frame_no(d)
        if fn < 0:
            continue
        f_full = d.get("f", "")
        if f_full == prev_f:  # 연속 중복줄만 skip
            continue
        prev_f = f_full
        d["_f"] = fn
        d["svxy"] = f"{sv_xy(d.get('sv','')):.0f}"
        rows.append(d)
    print(f"[parsed] {len(rows)} frames from {path.name} (tail={args.tail}, log-order)")

    # 반전 이벤트: ms_l 가 F(0) <-> B(4) 로 바뀌는 지점.
    # 세션 경계(tick 하락)에서 prev 리셋 → 세션간 가짜 반전 방지.
    events = []
    prev, prev_tick = None, -1
    for i, r in enumerate(rows):
        tick = r["_f"]
        if tick < prev_tick - 50:  # 큰 하락 = 새 PIE 세션
            prev = None
        prev_tick = tick
        cur = r.get("ms_l")
        if prev in (FWD, BWD) and cur in (FWD, BWD) and cur != prev:
            kind = "F->B" if (prev == FWD and cur == BWD) else "B->F"
            events.append((i, kind))
        if cur in (FWD, BWD):
            prev = cur

    if not events:
        print("반전 이벤트(F<->B) 미검출. ms_l 분포:",
              {MS_L.get(k, k): sum(1 for r in rows if r.get('ms_l') == k)
               for k in set(r.get('ms_l') for r in rows)})
        return

    print(f"[events] {len(events)} F<->B reversals\n")
    w = args.window
    hdr = " ".join(f"{c:>7}" if c != "seq" else "  seq" for c in COLS)
    for idx, kind in events:
        lo, hi = max(0, idx - w), min(len(rows), idx + w)
        print("=" * 120)
        print(f"### {kind}  @frame {rows[idx]['_f']}  (window {rows[lo]['_f']}~{rows[hi-1]['_f']})")
        print(hdr)
        for r in rows[lo:hi]:
            mark = " <REV" if r is rows[idx] else ""
            seq = r.get("seq", "")[:46]
            stop = " *STOP*" if "Stop" in seq else ""
            vals = []
            for c in COLS:
                if c == "seq":
                    continue
                vals.append(f"{r.get(c, ''):>7}")
            print(" ".join(vals) + f"  {seq}{stop}{mark}")
        print()


if __name__ == "__main__":
    main()
