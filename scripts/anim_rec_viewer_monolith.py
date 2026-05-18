#!/usr/bin/env python3
"""Anim Rewind Recorder Live Viewer — Monolith backend.

PoC: anim_rec_viewer.py 의 파일 tail 로직을
editor.search_logs Monolith RPC 로 교체.

장점:
  - 파일 경로 / 로그 회전 / Perforce 잠금 신경 X
  - 에디터 내부 로그 버퍼만 봄 (PIE 동작 중일 때 신선함 보장)
  - 다른 모노리스 도구와 한 워크플로우 (editor.run_console_command 와 연동 가능)

한계 (2026-05-18 확인):
  - Monolith 로그 버퍼는 현재 error/warning 만 capture (log/verbose=0).
    ANIM_REC 가 Display/Log verbosity 의 PrintString 이면 잡히지 않음.
  - 검출 안 될 때 본 스크립트는 진단 메시지 표시.
  - 폴백 필요 시 --fallback-file 로 파일 tail 모드 전환.

사용법:
    py scripts/anim_rec_viewer_monolith.py
    py scripts/anim_rec_viewer_monolith.py --interval 0.2
    py scripts/anim_rec_viewer_monolith.py --pattern "ANIM_REC"
    py scripts/anim_rec_viewer_monolith.py --fallback-file <path.log>
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

# 기존 viewer 의 parse/render 로직 재사용
sys.path.insert(0, str(Path(__file__).resolve().parent))
from anim_rec_viewer import (  # type: ignore
    FIELD_LABELS,
    PREFIX,
    build_table,
    parse_line,
)

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

ENDPOINT = "http://localhost:9316/mcp"
DEFAULT_PATTERN = "ANIM_REC"
DEFAULT_FETCH_LIMIT = 200


class MonolithError(RuntimeError):
    pass


def rpc(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("error"):
        raise MonolithError(str(data["error"]))
    result = data.get("result", {})
    if result.get("isError"):
        raise MonolithError(result["content"][0]["text"][:400])
    txt = result["content"][0]["text"]
    return json.loads(txt)


def fetch_anim_rec(pattern: str, limit: int) -> list[str]:
    """editor.search_logs 로 [ANIM_REC] 라인 가져옴."""
    resp = rpc(
        "editor_query",
        {"action": "search_logs", "params": {"pattern": pattern, "limit": limit}},
    )
    entries = resp.get("entries", [])
    # entries 는 dict 일 수도 있고 raw 라인일 수도. 두 케이스 모두 처리.
    lines: list[str] = []
    for e in entries:
        if isinstance(e, str):
            lines.append(e)
        elif isinstance(e, dict):
            # 후보 키: message / line / text / raw
            for k in ("message", "line", "text", "raw"):
                if k in e:
                    lines.append(str(e[k]))
                    break
            else:
                lines.append(json.dumps(e, ensure_ascii=False))
    return lines


def fetch_log_stats() -> dict[str, Any]:
    try:
        return rpc("editor_query", {"action": "get_log_stats", "params": {}})
    except Exception:
        return {}


def file_tail_lines(path: Path, pos: int) -> tuple[list[str], int]:
    """폴백 모드: 파일 tail. 새 줄 + 새 pos 반환."""
    if not path.exists():
        return [], pos
    size = path.stat().st_size
    if size < pos:
        pos = 0
    if size <= pos:
        return [], pos
    with open(path, "rb") as f:
        f.seek(pos)
        chunk = f.read(size - pos).decode("utf-8", errors="ignore")
    return chunk.splitlines(), size


def diagnostic_panel(stats: dict[str, Any], match_count: int, source: str) -> Panel:
    t = Text()
    t.append("Monolith 로그 버퍼 상태\n\n", style="bold cyan")
    if stats:
        t.append(f"  total   {stats.get('total', '?')}\n")
        t.append(
            f"  error   {stats.get('error', 0)}   "
            f"warning {stats.get('warning', 0)}   "
            f"log {stats.get('log', 0)}   "
            f"verbose {stats.get('verbose', 0)}\n"
        )
        if stats.get("log", 0) == 0 and stats.get("verbose", 0) == 0:
            t.append(
                "\n  ⚠ log/verbose=0 → Monolith가 error/warning만 캡처 중.\n"
                "    PrintString(Display/Log) 출력은 안 잡힘.\n"
                "    PIE 시작 후 ANIM_REC 가 안 나오면 --fallback-file 사용 권장.\n",
                style="yellow",
            )
    t.append(f"\n  [ANIM_REC] 매칭   {match_count}\n", style="green" if match_count else "red")
    t.append(f"  source           {source}", style="dim")
    return Panel(t, title="[bold]진단[/bold]", border_style="yellow")


def run_loop(
    pattern: str,
    interval: float,
    fallback_path: Path | None,
) -> None:
    console = Console()
    current: dict[str, str] = {}
    prev: dict[str, str] = {}
    change_age: dict[str, int] = {}
    line_count = 0
    last_seen_lines: set[str] = set()
    fallback_pos = 0

    source = "monolith://editor.search_logs"
    if fallback_path:
        source = f"file://{fallback_path}"
        if fallback_path.exists():
            fallback_pos = fallback_path.stat().st_size

    stats = fetch_log_stats() if not fallback_path else {}

    with Live(
        diagnostic_panel(stats, 0, source),
        console=console,
        refresh_per_second=10,
        screen=False,
    ) as live:
        while True:
            try:
                # 라인 수집
                if fallback_path:
                    raws, fallback_pos = file_tail_lines(fallback_path, fallback_pos)
                    raws = [r for r in raws if PREFIX in r]
                else:
                    raws = fetch_anim_rec(pattern, DEFAULT_FETCH_LIMIT)

                # 중복 제거 (search_logs 는 동일 범위 반복 반환)
                new_lines: list[str] = []
                for raw in raws:
                    if raw in last_seen_lines:
                        continue
                    last_seen_lines.add(raw)
                    new_lines.append(raw)
                # buffer 크기 제한
                if len(last_seen_lines) > 2000:
                    last_seen_lines = set(list(last_seen_lines)[-1000:])

                for raw in new_lines:
                    parsed = parse_line(raw)
                    if not parsed:
                        continue
                    line_count += 1
                    for k in change_age:
                        change_age[k] += 1
                    for k, v in parsed.items():
                        if current.get(k) != v:
                            change_age[k] = 0
                    prev = current
                    current = parsed

                if line_count == 0:
                    live.update(diagnostic_panel(fetch_log_stats() if not fallback_path else {}, 0, source))
                else:
                    live.update(build_table(current, prev, change_age, line_count, source))
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except MonolithError as exc:
                live.update(
                    Panel(
                        Text(f"Monolith RPC 실패\n\n{exc}", style="red"),
                        title="[bold red]오류[/bold red]",
                        border_style="red",
                    )
                )
                time.sleep(max(interval, 1.0))


def smoke_test(pattern: str, fallback_path: Path | None) -> int:
    """Live 화면 없이 한 사이클 수행. CI / non-TTY 검증용."""
    print(f"[smoke] backend={'file' if fallback_path else 'monolith'}")
    if fallback_path:
        if not fallback_path.exists():
            print(f"[smoke] fallback file 없음: {fallback_path}")
            return 1
        # 큰 백업도 ANIM_REC 위치가 파일 끝에서 멀 수 있으므로 전체 스캔
        size = fallback_path.stat().st_size
        raws, _ = file_tail_lines(fallback_path, 0)
        raws = [r for r in raws if PREFIX in r]
        print(
            f"[smoke] 파일 전체 {size:,} bytes 에서 ANIM_REC 라인 {len(raws)} 개"
        )
        raws = raws[-3:]  # 마지막 3개만 sample
    else:
        stats = fetch_log_stats()
        print(f"[smoke] log_stats = {stats}")
        try:
            raws = fetch_anim_rec(pattern, DEFAULT_FETCH_LIMIT)
            print(f"[smoke] search_logs pattern={pattern!r} → {len(raws)} 라인")
        except MonolithError as exc:
            print(f"[smoke] RPC 실패: {exc}")
            return 2
    sample = raws[:2] if raws else []
    for s in sample:
        print(f"  > {s[:200]}")
        parsed = parse_line(s)
        if parsed:
            keys = list(parsed.keys())[:5]
            print(f"    parsed: {len(parsed)} fields, first={keys}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--pattern", default=DEFAULT_PATTERN, help="search_logs pattern")
    ap.add_argument("--interval", type=float, default=0.3, help="폴링 주기 초")
    ap.add_argument(
        "--fallback-file",
        type=Path,
        default=None,
        help="Monolith 못 잡으면 파일 tail 폴백 (path)",
    )
    ap.add_argument(
        "--smoke",
        action="store_true",
        help="Live 화면 없이 1 사이클 검증",
    )
    args = ap.parse_args()

    if args.smoke:
        return smoke_test(args.pattern, args.fallback_file)

    print(f"backend : {'file' if args.fallback_file else 'monolith'}")
    if args.fallback_file:
        print(f"file    : {args.fallback_file}")
    else:
        print(f"endpoint: {ENDPOINT}")
        print(f"pattern : {args.pattern}")
    print(f"interval: {args.interval}s")
    print("Ctrl+C로 종료\n")
    run_loop(args.pattern, args.interval, args.fallback_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
