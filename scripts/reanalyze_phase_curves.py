"""
Phase curve 재분석 (raw dump 사용, 네트워크 호출 없음).

실측 패턴 (P_Player_Run_Loop_F):
  -0.165 -> 0.0
   0.187 -> -1.0
   0.197 -> +1.0   (wrap: -1->+1, dt~0.01s)
   0.560 -> 0.0
   0.925 -> -1.0
   ...
즉 sawtooth 하강 (값이 0->-1 감소, wrap, 1->0 감소).

- normal step: v1 < v0 (감소)
- wrap: v0 ~ -1, v1 ~ +1, dt < 0.05s
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


@dataclass
class Verdict:
    name: str
    flags: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


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


def classify(keys: list[dict[str, Any]], duration: float) -> Verdict:
    if not keys:
        return Verdict("missing", flags=["no_keys"])

    times = [k["time"] for k in keys]
    values = [k["value"] for k in keys]
    n = len(keys)

    flags: list[str] = []

    # 1) 시간 단조성
    if any(times[i] >= times[i + 1] for i in range(n - 1)):
        flags.append("time_disorder")

    # 2) 범위
    vmin, vmax = min(values), max(values)
    if vmin < -1.05 or vmax > 1.05:
        flags.append("out_of_range")

    if vmax - vmin < 0.5:
        flags.append("range_too_narrow")

    # 3) sawtooth 하강 패턴 + wrap
    descent_steps = 0
    ascent_violations: list[tuple[float, float, float]] = []  # (t, v0, v1)
    wraps = 0
    near_zero_jumps: list[tuple[float, float, float]] = []  # 큰 점프 중 wrap 아닌 것

    for i in range(n - 1):
        v0, v1 = values[i], values[i + 1]
        dt = times[i + 1] - times[i]
        is_wrap = v0 <= -0.95 and v1 >= 0.95 and dt < 0.05
        if is_wrap:
            wraps += 1
            continue
        if v1 > v0 + 1e-3:  # 비-wrap에서 상승은 비정상
            ascent_violations.append((times[i], v0, v1))
        else:
            descent_steps += 1
        if abs(v1 - v0) > 0.4 and not is_wrap:
            near_zero_jumps.append((times[i], v0, v1))

    if ascent_violations:
        flags.append(f"ascent_violation({len(ascent_violations)})")
    if near_zero_jumps:
        flags.append(f"big_step({len(near_zero_jumps)})")

    # 4) wrap 개수 = 사이클 수 추정. duration 대비 평균 보폭 시간 계산
    cycle_period = duration / wraps if wraps > 0 and duration > 0 else 0.0

    # 5) duration 커버리지: 마지막 키 시간이 duration의 80% 이상
    end_coverage = times[-1] / duration if duration > 0 else 0.0
    start_coverage = times[0] / duration if duration > 0 else 0.0
    if duration > 0:
        # 양 끝이 클립 범위를 살짝 넘는 건 정상(보간용 여유키). 너무 좁으면 의심.
        if times[-1] < duration * 0.8:
            flags.append(f"short_end_coverage({end_coverage:.2f})")
        if times[0] > duration * 0.2:
            flags.append(f"late_start({start_coverage:.2f})")

    # 6) 키 너무 적음
    if n < 3:
        flags.append("too_few_keys")

    # 7) 사이클 수 sanity: duration에 비해 사이클 0개면 의심
    if duration > 0.4 and wraps == 0:
        flags.append("no_cycle_wrap")

    name = "ok" if not flags else flags[0].split("(")[0]
    return Verdict(
        name=name,
        flags=flags,
        metrics={
            "num_keys": n,
            "min": vmin,
            "max": vmax,
            "first": values[0],
            "last": values[-1],
            "first_time": times[0],
            "last_time": times[-1],
            "wraps": wraps,
            "cycle_period": cycle_period,
            "duration": duration,
            "end_coverage": end_coverage,
            "start_coverage": start_coverage,
            "ascent_violations": ascent_violations[:5],
            "big_steps": near_zero_jumps[:5],
        },
    )


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
            out.update({"verdict": "missing", "flags": ["no_phase_curve"]})
            new_results[path] = out
            continue

        clip_name = path.rsplit("/", 1)[-1]
        raw_path = PHASE_DIR / f"{clip_name}.json"
        if not raw_path.exists():
            out.update({"verdict": "raw_missing", "flags": ["dump_missing"]})
            new_results[path] = out
            continue
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        # raw에는 seq_length(=0인 경우 있음) 저장됨. 정확한 duration은 다시 못얻음
        # → 대신 마지막 키 시간을 ceiling으로 사용 (보존적), 또는 raw에 duration 없으면 0
        # 새로 가져와야 한다면 별도 호출. 여기서는 마지막 키 시간을 duration proxy로.
        # short_end_coverage는 duration 정보 부족하면 평가 안 함.
        keys = raw.get("keys", [])
        # duration proxy: 라스트 키 시간 + 0.05 (그냥 키 자체가 클립 범위라고 가정)
        proxy_duration = max(k["time"] for k in keys) + 0.01 if keys else 0.0
        verdict = classify(keys, proxy_duration)
        out.update(
            {
                "verdict": verdict.name,
                "flags": verdict.flags,
                **verdict.metrics,
            }
        )
        new_results[path] = out

    # 요약
    counts = Counter(r["verdict"] for r in new_results.values())
    flag_combos = Counter()
    for r in new_results.values():
        flag_combos[tuple(r.get("flags", []))] += 1

    summary = {
        "total": len(new_results),
        "verdict_counts": dict(counts),
        "flag_combos_top": flag_combos.most_common(20),
    }

    (ROOT / "_phase_summary_v2.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (ROOT / "_phase_results_v2.json").write_text(
        json.dumps(new_results, indent=2), encoding="utf-8"
    )

    # 이상 우선순위 (자주 사용되는 Walk/Jog/Sprint/Run Loop 우선)
    priority_kw = [
        "Walk_Loop",
        "Jog_Loop",
        "Run_Loop",
        "Sprint_Loop",
        "Battle_Walk",
        "Battle_Jog",
        "Walk_Circle_Strafe",
        "Jog_Circle_Strafe",
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
