"""apply_and_verify — 한 명령으로 수정 → PIE → 로그 → 리포트.

전형 사용:

    from scripts.workflows.apply_and_verify import apply_and_verify

    def my_modification():
        # rpc 호출들
        ...

    report = apply_and_verify(
        apply_fn=my_modification,
        asset='/Game/.../PC_01_ABP',
        graph='UpdateVariables',
        pie_seconds=5.0,
        log_filter='[ANIM_REC]',
        expected_changes={
            'min_lines': 60,
            'fields_present': ['f', 'sp', 'tsa'],
        },
    )
    print(report)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Callable

# lib 모듈 import — repo root에서 실행 가정
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from lib.monolith_client import rpc, call_blueprint  # noqa: E402

STATE_DIR = os.path.join(REPO_ROOT, ".claude", "state")
DEFAULT_LOG_PATH = r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2_2.log"


@dataclass
class VerifyReport:
    success: bool
    timestamp: str
    apply_elapsed_s: float
    compile_ok: bool
    pie_seconds: float
    log_lines_total: int
    log_lines_filtered: int
    sample_lines: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def start_pie() -> bool:
    """`ce StartPIE` console command."""
    r = rpc("editor_query", "console_command", {"command": "ce StartPIE"}, silent=True)
    if r is None or (isinstance(r, dict) and "_error" in r):
        # alt: editor_console_command tool
        r = rpc("editor_console_command", "exec", {"command": "ce StartPIE"}, silent=True)
    return r is not None and not (isinstance(r, dict) and "_error" in r)


def stop_pie() -> bool:
    r = rpc("editor_query", "console_command", {"command": "StopPIE"}, silent=True)
    if r is None or (isinstance(r, dict) and "_error" in r):
        r = rpc("editor_console_command", "exec", {"command": "StopPIE"}, silent=True)
    return r is not None and not (isinstance(r, dict) and "_error" in r)


def capture_log_slice(
    log_path: str,
    duration_s: float,
    prefix: str | None = None,
) -> tuple[list[str], list[str]]:
    """Tail the log for duration_s seconds. Returns (all_new_lines, filtered_lines)."""
    if not os.path.exists(log_path):
        return [], []
    # 시작 시점 파일 크기 기록
    start_size = os.path.getsize(log_path)
    time.sleep(duration_s)
    end_size = os.path.getsize(log_path)
    if end_size <= start_size:
        return [], []
    with open(log_path, "rb") as f:
        f.seek(start_size)
        chunk = f.read(end_size - start_size)
    lines = chunk.decode("utf-8", errors="replace").splitlines()
    if prefix:
        filtered = [ln for ln in lines if prefix in ln]
    else:
        filtered = lines
    return lines, filtered


def parse_anim_rec_fields(line: str) -> dict[str, str]:
    """[ANIM_REC] 한 줄 → {field: value} dict."""
    idx = line.find("[ANIM_REC]")
    if idx < 0:
        return {}
    body = line[idx + len("[ANIM_REC]"):].strip()
    out: dict[str, str] = {}
    parts = re.split(r',?"([a-z_]+)"=', body)
    i = 1
    while i + 1 < len(parts):
        key = parts[i]
        val = re.sub(r'(\d),(\d)', r'\1\2', parts[i + 1]).rstrip(",").strip()
        out[key] = val
        i += 2
    return out


def apply_and_verify(
    apply_fn: Callable,
    *,
    asset: str,
    graph: str | None = None,
    pie_seconds: float = 5.0,
    log_path: str = DEFAULT_LOG_PATH,
    log_filter: str = "[ANIM_REC]",
    expected_changes: dict | None = None,
    skip_pie: bool = False,
    save_report: bool = True,
) -> VerifyReport:
    """Run apply_fn, compile, save, start PIE, capture logs, verify."""
    report = VerifyReport(
        success=False,
        timestamp=datetime.now().isoformat(),
        apply_elapsed_s=0.0,
        compile_ok=False,
        pie_seconds=pie_seconds,
        log_lines_total=0,
        log_lines_filtered=0,
    )

    # Apply
    print(f"[1/5] Apply {apply_fn.__name__}...")
    t0 = time.time()
    try:
        apply_fn()
    except Exception as exc:
        report.errors.append(f"apply_fn raised: {exc}")
        return report
    report.apply_elapsed_s = time.time() - t0
    print(f"  done in {report.apply_elapsed_s:.1f}s")

    # Compile + save
    print(f"[2/5] Compile + save...")
    c = call_blueprint("compile_blueprint", {"asset_path": asset})
    if not c or (isinstance(c, dict) and "_error" in c):
        report.errors.append(f"compile failed: {c}")
        return report
    if isinstance(c, dict) and c.get("error_count", 0) > 0:
        report.errors.append(f"compile errors: {c.get('errors')}")
        return report
    report.compile_ok = True
    s = call_blueprint("save_asset", {"asset_path": asset})
    print(f"  compile ok, save: {s}")

    if skip_pie:
        report.notes.append("PIE skipped (skip_pie=True)")
        report.success = True
        return _finalize(report, save_report)

    # PIE
    print(f"[3/5] Start PIE...")
    if not start_pie():
        report.errors.append("start_pie failed")
        return report

    # Capture
    print(f"[4/5] Capture log for {pie_seconds}s (filter={log_filter!r})...")
    all_lines, filtered = capture_log_slice(log_path, pie_seconds, prefix=log_filter)
    report.log_lines_total = len(all_lines)
    report.log_lines_filtered = len(filtered)
    report.sample_lines = filtered[:5] if filtered else []

    stop_pie()

    # Verify
    print(f"[5/5] Verify expectations...")
    if expected_changes:
        min_lines = expected_changes.get("min_lines")
        if min_lines and len(filtered) < min_lines:
            report.errors.append(f"too few filtered lines: {len(filtered)} < {min_lines}")
        fields_present = expected_changes.get("fields_present", [])
        if fields_present and filtered:
            sample_fields = parse_anim_rec_fields(filtered[0])
            missing = [f for f in fields_present if f not in sample_fields]
            report.missing_fields = missing
            if missing:
                report.errors.append(f"missing fields in log: {missing}")

    report.success = (report.compile_ok and not report.errors)
    return _finalize(report, save_report)


def _finalize(report: VerifyReport, save: bool) -> VerifyReport:
    if save:
        os.makedirs(STATE_DIR, exist_ok=True)
        path = os.path.join(STATE_DIR, "last_verify_report.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        print(f"\n[report] saved → {path}")
    return report


# CLI 모드 — 외부에서 import 안 하고 직접 실행 시
def _cli():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--asset", required=True)
    p.add_argument("--graph")
    p.add_argument("--pie-seconds", type=float, default=5.0)
    p.add_argument("--log-path", default=DEFAULT_LOG_PATH)
    p.add_argument("--log-filter", default="[ANIM_REC]")
    p.add_argument("--skip-pie", action="store_true")
    args = p.parse_args()

    def noop():
        pass

    r = apply_and_verify(
        apply_fn=noop,
        asset=args.asset,
        graph=args.graph,
        pie_seconds=args.pie_seconds,
        log_path=args.log_path,
        log_filter=args.log_filter,
        skip_pie=args.skip_pie,
    )
    print(json.dumps(asdict(r), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    _cli()
