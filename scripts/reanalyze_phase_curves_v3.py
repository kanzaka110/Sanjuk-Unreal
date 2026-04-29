"""
Phase curve 정확한 무결성 분석 v3.

검증 결과 기반 sawtooth 패턴 정의:
  - normal fall step: v1 < v0, |v0 - v1| ≈ 1.0 (median=1.0)
  - wrap: v0 ≈ -1, v1 ≈ +1, dt ≈ 0.01s (1 frame @30fps)
  - 사이클 1개 = wrap 1번
  - **amp ≈ 2.0인 fall = 비정상** (1 -> -1 직접 점프, wrap 누락)
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path("C:/Dev/Sanjuk-Unreal/dumps/sync_groups")
PHASE_DIR = ROOT / "phase"
RESULTS_PATH = ROOT / "_phase_results.json"
PSD_DIR = ROOT / "psd"

PHASE_PSDS = [
    "PSD_GroundIdleTransit",
    "PSD_GroundMoving",
    "PSD_GroundMovingTransit",
    "PSD_WriggleGroundMoving",
    "PSD_WriggleGroundMovingTransit",
]


def collect_target_clips() -> dict[str, dict[str, Any]]:
    clips: dict[str, dict[str, Any]] = {}
    for psd_name in PHASE_PSDS:
        path = PSD_DIR / f"{psd_name}.json"
        outer = json.loads(path.read_text(encoding="utf-8"))
        inner = json.loads(outer["result"]["content"][0]["text"])
        for seq in inner.get("sequences", []):
            anim = seq["animation"].split(".")[0]
            ent = clips.setdefault(anim, {"psds": [], "samp_ranges": []})
            ent["psds"].append(psd_name)
            ent["samp_ranges"].append(
                (seq.get("sampling_range_start", 0.0), seq.get("sampling_range_end", 0.0))
            )
    return clips


def classify(keys: list[dict[str, Any]]) -> dict[str, Any]:
    if not keys:
        return {"verdict": "missing", "flags": ["no_keys"], "num_keys": 0}

    times = [k["time"] for k in keys]
    values = [k["value"] for k in keys]
    n = len(keys)
    flags: list[str] = []

    if any(times[i] >= times[i + 1] for i in range(n - 1)):
        flags.append("time_disorder")

    vmin, vmax = min(values), max(values)
    if vmin < -1.05 or vmax > 1.05:
        flags.append("out_of_range")

    if n < 3:
        flags.append("too_few_keys")

    wraps = 0
    fall_amps: list[float] = []
    ascents: list[tuple[float, float, float]] = []
    double_falls: list[tuple[float, float, float]] = []  # amp ~ 2.0
    weird_falls: list[tuple[float, float, float, float]] = []  # amp != 1.0 (~)
    same_value: list[tuple[float, float]] = []

    for i in range(n - 1):
        v0, v1 = values[i], values[i + 1]
        dt = times[i + 1] - times[i]
        if v0 <= -0.9 and v1 >= 0.9 and dt < 0.05:
            wraps += 1
            continue
        if abs(v1 - v0) < 1e-3:
            same_value.append((times[i], v0))
            continue
        if v1 > v0 + 1e-3:
            ascents.append((times[i], v0, v1))
            continue
        # fall step
        amp = v0 - v1
        fall_amps.append(amp)
        if amp > 1.5:
            double_falls.append((times[i], v0, v1))
        elif abs(amp - 1.0) > 0.15 and amp < 1.5:
            # 정상 1.0에서 0.15 이상 벗어남
            weird_falls.append((times[i], v0, v1, amp))

    # 사이클 주기 분석
    wrap_times = [
        times[i + 1]
        for i in range(n - 1)
        if values[i] <= -0.9 and values[i + 1] >= 0.9 and (times[i + 1] - times[i]) < 0.05
    ]
    if len(wrap_times) >= 2:
        intervals = [wrap_times[i + 1] - wrap_times[i] for i in range(len(wrap_times) - 1)]
        cycle_min = min(intervals)
        cycle_max = max(intervals)
        cycle_var = (cycle_max - cycle_min) / cycle_min if cycle_min > 0 else 0.0
    else:
        intervals, cycle_min, cycle_max, cycle_var = [], 0.0, 0.0, 0.0

    if ascents:
        flags.append(f"ascent({len(ascents)})")
    if double_falls:
        flags.append(f"double_fall({len(double_falls)})")
    if weird_falls:
        flags.append(f"weird_fall({len(weird_falls)})")
    if cycle_var > 0.3:
        flags.append(f"uneven_cycle({cycle_var:.2f})")
    if same_value:
        flags.append(f"flat({len(same_value)})")
    if wraps == 0 and n >= 5:
        flags.append("no_wrap")

    verdict = "ok" if not flags else "_".join(f.split("(")[0] for f in flags[:1])
    if not flags:
        verdict = "ok"

    return {
        "verdict": verdict,
        "flags": flags,
        "num_keys": n,
        "min": vmin,
        "max": vmax,
        "first": values[0],
        "last": values[-1],
        "first_time": times[0],
        "last_time": times[-1],
        "wraps": wraps,
        "cycle_intervals": intervals,
        "cycle_min": cycle_min,
        "cycle_max": cycle_max,
        "cycle_var": cycle_var,
        "fall_amp_min": min(fall_amps) if fall_amps else None,
        "fall_amp_max": max(fall_amps) if fall_amps else None,
        "ascents": ascents[:5],
        "double_falls": double_falls[:5],
        "weird_falls": weird_falls[:5],
        "same_value_count": len(same_value),
    }


def main() -> None:
    old = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    clips = collect_target_clips()

    new_results: dict[str, dict[str, Any]] = {}
    for path, rec in old.items():
        out: dict[str, Any] = {
            "path": path,
            "psds": clips.get(path, {}).get("psds", []),
            "all_curves": rec.get("all_curves", []),
        }
        if rec.get("verdict") == "missing":
            out.update({"verdict": "missing", "flags": ["no_phase_curve"], "num_keys": 0})
            new_results[path] = out
            continue
        clip_name = path.rsplit("/", 1)[-1]
        raw_path = PHASE_DIR / f"{clip_name}.json"
        if not raw_path.exists():
            out.update({"verdict": "raw_missing", "flags": ["dump_missing"]})
            new_results[path] = out
            continue
        keys = json.loads(raw_path.read_text(encoding="utf-8")).get("keys", [])
        out.update(classify(keys))
        new_results[path] = out

    counts = Counter(r["verdict"] for r in new_results.values())
    flag_combos: Counter[tuple[str, ...]] = Counter()
    for r in new_results.values():
        flag_combos[tuple(r.get("flags", []))] += 1

    summary = {
        "total": len(new_results),
        "verdict_counts": dict(counts),
        "flag_combos_top": [
            {"flags": list(k), "count": v} for k, v in flag_combos.most_common(20)
        ],
    }

    (ROOT / "_phase_summary_v3.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (ROOT / "_phase_results_v3.json").write_text(
        json.dumps(new_results, indent=2), encoding="utf-8"
    )

    priority_kw = [
        "Walk_Loop_F",
        "Jog_Loop_F",
        "Run_Loop_F",
        "Sprint_Loop_F",
        "Walk_Loop",
        "Jog_Loop",
        "Run_Loop",
        "Sprint_Loop",
        "Walk_Circle_Strafe",
        "Battle_Walk",
        "Battle_Jog",
    ]

    def pscore(rec: dict[str, Any]) -> int:
        p = rec["path"]
        for i, kw in enumerate(priority_kw):
            if kw in p:
                return i
        return 99

    anomalies = [r for r in new_results.values() if r["verdict"] != "ok"]
    anomalies.sort(key=lambda r: (pscore(r), r["path"]))
    (ROOT / "phase_anomalies.json").write_text(
        json.dumps(anomalies, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
