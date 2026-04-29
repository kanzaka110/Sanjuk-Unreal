"""
PC_01 Locomotion 클립 Phase curve 무결성 점검.

- _anim_to_psd.json + PSD dump 5종(Phase 트래킹)에서 대상 클립 추출.
- Monolith HTTP API로 list_curves + get_curve_keys 호출.
- 분류:
    missing  : phase curve 없음
    too_few  : 키 개수 < 4
    range_bad: |min|>1.05 또는 |max|>1.05 또는 max<0.5
    nonmono  : -1->1 jump 제외한 인접 키가 단조 증가가 아님
    big_jump : -1->1 cycle wrap 외에 0.4 이상 점프
    ok       : 위 모두 통과
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

ROOT = Path("C:/Dev/Sanjuk-Unreal/dumps/sync_groups")
PSD_DIR = ROOT / "psd"
PHASE_DIR = ROOT / "phase"
PHASE_DIR.mkdir(exist_ok=True)

PHASE_PSDS = [
    "PSD_GroundIdleTransit",
    "PSD_GroundMoving",
    "PSD_GroundMovingTransit",
    "PSD_WriggleGroundMoving",
    "PSD_WriggleGroundMovingTransit",
]

MONOLITH_URL = "http://localhost:9316/mcp"


def call_monolith(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "animation_query",
            "arguments": {"action": action, "params": params},
        },
    }
    r = requests.post(MONOLITH_URL, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()
    if "result" not in data:
        return {"isError": True, "raw": data}
    res = data["result"]
    if res.get("isError"):
        return {"isError": True, "raw": res}
    txt = res["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"isError": True, "raw_text": txt}


def collect_target_clips() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, int]]:
    """{clip_path: {psds:[...], samp_ranges:[...]}}, psd_counts"""
    clips: Dict[str, Dict[str, Any]] = {}
    psd_counts: Dict[str, int] = {}
    for psd_name in PHASE_PSDS:
        path = PSD_DIR / f"{psd_name}.json"
        if not path.exists():
            print(f"[WARN] missing {path}", file=sys.stderr)
            continue
        outer = json.loads(path.read_text(encoding="utf-8"))
        inner = json.loads(outer["result"]["content"][0]["text"])
        psd_counts[psd_name] = inner.get("sequence_count", 0)
        for seq in inner.get("sequences", []):
            anim = seq["animation"].split(".")[0]  # strip .AssetName suffix
            ent = clips.setdefault(anim, {"psds": [], "samp_ranges": []})
            ent["psds"].append(psd_name)
            ent["samp_ranges"].append(
                (seq.get("sampling_range_start", 0.0), seq.get("sampling_range_end", 0.0))
            )
    return clips, psd_counts


def find_phase_curve(curves: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    for c in curves:
        if c.get("name", "").lower() == "phase":
            return c
    return None


def analyze_keys(keys: List[Dict[str, Any]], seq_len: float) -> Dict[str, Any]:
    """SB2 phase 컨벤션: -1과 1은 동일 위상(cycle 경계). sawtooth.

    대표 패턴(P_Player_Run_Arc_Small_L 21keys):
      0.0 -> -1.0 -> 1.0 -> 0.0 -> -1.0 -> 1.0 -> ...
    즉 [-1, 1] 점프는 wrap이며 정상.
    """
    if not keys:
        return {"verdict": "missing_keys"}

    times = [k["time"] for k in keys]
    values = [k["value"] for k in keys]
    n = len(keys)

    flags: List[str] = []

    # 시간 단조성
    if any(times[i] >= times[i + 1] for i in range(n - 1)):
        flags.append("time_disorder")

    # 범위
    vmin, vmax = min(values), max(values)
    if vmin < -1.05 or vmax > 1.05:
        flags.append("out_of_range")
    if vmax - vmin < 0.5:
        flags.append("range_too_narrow")

    # 단조성 + jump (cycle wrap 제외)
    nonmono = 0
    big_jumps: List[Tuple[float, float, float]] = []  # (t, dv, t_next)
    cycle_wraps = 0
    for i in range(n - 1):
        v0, v1 = values[i], values[i + 1]
        dt = times[i + 1] - times[i]
        # cycle wrap: -1 직후 1 (또는 매우 가까이)
        is_wrap = v0 <= -0.95 and v1 >= 0.95 and dt < 0.1
        if is_wrap:
            cycle_wraps += 1
            continue
        # 그 외 진행은 v0 <= v1 + eps 가 정상 (sawtooth 상승 구간)
        if v1 < v0 - 1e-3:
            nonmono += 1
        if abs(v1 - v0) > 0.4 and not is_wrap:
            big_jumps.append((times[i], v1 - v0, times[i + 1]))

    if nonmono:
        flags.append(f"nonmono({nonmono})")
    if big_jumps:
        flags.append(f"big_jump({len(big_jumps)})")

    # 끝점 정합: 클립 끝 근처에 cycle 경계 또는 특정 위상 있어야 loop 자연
    # 단순 체크: 마지막 키 시간이 시퀀스 길이의 80% 이전이면 의심
    end_coverage = times[-1] / seq_len if seq_len > 0 else 0.0
    if seq_len > 0 and end_coverage < 0.8:
        flags.append(f"short_coverage({end_coverage:.2f})")

    verdict = "ok" if not flags else flags[0].split("(")[0]
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
        "cycle_wraps": cycle_wraps,
        "nonmono": nonmono,
        "big_jumps": big_jumps[:5],
        "seq_length": seq_len,
        "end_coverage": end_coverage,
    }


def main() -> int:
    clips, psd_counts = collect_target_clips()
    print(f"[INFO] PSD totals: {psd_counts}", file=sys.stderr)
    print(f"[INFO] unique target clips: {len(clips)}", file=sys.stderr)

    results: Dict[str, Dict[str, Any]] = {}
    failures: List[str] = []

    for i, (path, meta) in enumerate(sorted(clips.items()), 1):
        if i % 25 == 0 or i == 1:
            print(f"[{i}/{len(clips)}] {path}", file=sys.stderr)
        rec: Dict[str, Any] = {"path": path, "psds": meta["psds"]}

        lc = call_monolith("list_curves", {"asset_path": path})
        if lc.get("isError"):
            rec["verdict"] = "list_curves_failed"
            rec["error"] = str(lc)[:300]
            failures.append(path)
            results[path] = rec
            continue

        seq_info = call_monolith("get_sequence_info", {"asset_path": path})
        seq_len = seq_info.get("length", 0.0) if not seq_info.get("isError") else 0.0
        rec["seq_length"] = seq_len

        phase_meta = find_phase_curve(lc.get("curves", []))
        rec["all_curves"] = [c["name"] for c in lc.get("curves", [])]
        if phase_meta is None:
            rec["verdict"] = "missing"
            rec["num_keys"] = 0
            results[path] = rec
            continue

        rec["phase_meta"] = phase_meta
        gk = call_monolith(
            "get_curve_keys",
            {"asset_path": path, "curve_name": phase_meta["name"]},
        )
        if gk.get("isError"):
            rec["verdict"] = "get_keys_failed"
            rec["error"] = str(gk)[:300]
            failures.append(path)
            results[path] = rec
            continue

        keys = gk.get("keys", [])
        analysis = analyze_keys(keys, seq_len)
        rec.update(analysis)

        # 개별 raw dump
        clip_name = path.rsplit("/", 1)[-1]
        (PHASE_DIR / f"{clip_name}.json").write_text(
            json.dumps({"path": path, "seq_length": seq_len, "curve_meta": phase_meta, "keys": keys}, indent=2),
            encoding="utf-8",
        )

        results[path] = rec

    # 요약
    counts: Dict[str, int] = {}
    anomalies: List[Dict[str, Any]] = []
    for path, rec in results.items():
        v = rec.get("verdict", "unknown")
        counts[v] = counts.get(v, 0) + 1
        if v != "ok":
            anomalies.append(rec)

    summary = {
        "psd_counts": psd_counts,
        "unique_clip_count": len(clips),
        "verdict_counts": counts,
        "failures": failures,
    }
    (ROOT / "_phase_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (ROOT / "_phase_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    (ROOT / "phase_anomalies.json").write_text(
        json.dumps(anomalies, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
