#!/usr/bin/env python3
"""Anim Rewind Recorder Live Viewer

PC_01_ABP가 SB2_2.log에 매 틱 쏘는 [ANIM_REC] 라인을 tail해서
23필드를 표 형태로 실시간 표시. 변경된 필드는 하이라이트.

사용법:
    python anim_rec_viewer.py
    python anim_rec_viewer.py --log "E:/Perforce/SB2/Workspace/Internal/SB2/Saved/Logs/SB2.log"
    python anim_rec_viewer.py --interval 0.05
"""

from __future__ import annotations

import argparse
import re
import time
from collections import deque
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


DEFAULT_LOG = r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2_2.log"
PREFIX = "[ANIM_REC]"

# field key → display label (한글 보조설명)
FIELD_LABELS: dict[str, str] = {
    "f":    "f      (frame)",
    "sp":   "sp     (Speed2D)",
    "as":   "as     (AnimStance enum)",
    "ms":   "ms     (MovementState enum)",
    "ist":  "ist    (bIsStart)",
    "he":   "he     (HasEvade)",
    "vlen": "vlen   (Velocity XY)",
    "pwm":  "pwm    (PendingWalkMode enum)",
    "il":   "il     (IsLockOn)",
    "isf":  "isf    (IsStrafe)",
    "isc":  "isc    (TrjIsCircling)",
    "csh":  "csh    (CircleStrafeHysteresis)",
    "trd":  "trd    (TargetRotationDelta)",
    "ib":   "ib     (IsBattle)",
    "rmf":  "rmf    (RuleMoveFlag)",
    "fik":  "fik    (FootIKWeight)",
    "fca":  "fca    (FootClampAlpha)",
    "ow":   "ow     (OverlayWeight)",
    "ig":   "ig     (IsGuarding)",
    "sc":   "sc     (SearchCost)",
    "sdt":  "sdt    (SustainedDirTime)",
    "tta":  "tta    (TrjTurnAngle)",
    "sdpt": "sdpt   (bSustainedDirPivotTrigger)",
}

# 키 패턴: "key"=value (콤마로 구분, value는 콤마 포함 가능 — 천단위)
# 따옴표 키 + = + value (다음 ',"' 또는 줄끝까지)
LINE_RE = re.compile(r'"([a-z]+)"=([^,]+(?:,\d{3})*)')


def parse_line(raw: str) -> dict[str, str] | None:
    """[ANIM_REC] 한 줄에서 23필드 dict 추출. 천단위 콤마 strip."""
    idx = raw.find(PREFIX)
    if idx < 0:
        return None
    body = raw[idx + len(PREFIX):].strip()
    fields: dict[str, str] = {}
    # 정규식보다 안전한 split: "key"=value 단위로 쪼개기
    # 입력 예: "f"=3,493,989,"sp"=350.5,"as"=1,...
    # 천단위 콤마와 필드 구분 콤마 둘 다 콤마라 정규식 까다로움.
    # 전략: '"key"=' 패턴으로 split하면 value+(다음 key 앞 콤마들) 남음.
    parts = re.split(r',?"([a-z]+)"=', body)
    # parts: ['', 'f', '3,493,989', 'sp', '350.5', 'as', '1', ...]
    if not parts or len(parts) < 3:
        return None
    i = 1
    while i + 1 < len(parts):
        key = parts[i]
        val = parts[i + 1]
        # 천단위 콤마 strip (숫자 사이 콤마만)
        val_clean = re.sub(r'(\d),(\d)', r'\1\2', val)
        # 다음 필드의 prefix가 섞이는 경우 cut
        val_clean = val_clean.rstrip(',').strip()
        fields[key] = val_clean
        i += 2
    return fields if fields else None


def colorize(key: str, value: str, prev: Optional[str], changed_recent: bool) -> Text:
    """값 + 색상 결정. bool, enum=0/None은 회색, 변경 시 하이라이트."""
    txt = Text(value)
    # 변경 직후면 강조
    if changed_recent:
        txt.stylize("bold bright_yellow on grey15")
        return txt
    # 타입별 컬러
    v = value.lower()
    if v in ("true",):
        txt.stylize("bold bright_green")
    elif v in ("false",):
        txt.stylize("grey50")
    elif v in ("none", "0", "0.0"):
        txt.stylize("grey50")
    elif key in ("trd", "tta") and v.startswith("-"):
        txt.stylize("orange3")
    elif key in ("sp", "vlen") and v not in ("0", "0.0"):
        txt.stylize("cyan")
    elif key == "rmf" and v not in ("none",):
        txt.stylize("magenta")
    elif key == "sc" and v not in ("0", "0.0"):
        txt.stylize("yellow")
    else:
        txt.stylize("white")
    return txt


def build_table(
    current: dict[str, str],
    prev: dict[str, str],
    change_age: dict[str, int],
    line_count: int,
    log_path: str,
) -> Panel:
    """현재 라인 → 표 렌더링."""
    table = Table(
        title=f"[bold]리와인드 로그[/bold]  (lines: {line_count})  · 변경 직후 노란 하이라이트",
        title_style="bold cyan",
        show_header=True,
        header_style="bold magenta",
        expand=False,
        padding=(0, 1),
    )
    table.add_column("Key", style="dim", width=30, no_wrap=True)
    table.add_column("Value", style="white", min_width=24)

    for key in FIELD_LABELS:
        label = FIELD_LABELS[key]
        val = current.get(key, "-")
        prev_val = prev.get(key)
        recent = change_age.get(key, 99) < 5  # 최근 5 line 안에 변한 필드
        value_text = colorize(key, val, prev_val, recent)
        table.add_row(label, value_text)

    panel = Panel(
        table,
        title=f"[dim]source: {log_path}[/dim]",
        title_align="left",
        border_style="cyan",
    )
    return panel


def tail_log(path: Path, interval: float) -> None:
    """log file을 매 interval초 tail. 새 [ANIM_REC] 라인을 화면에 반영."""
    console = Console()
    current: dict[str, str] = {}
    prev: dict[str, str] = {}
    change_age: dict[str, int] = {}  # 마지막 변경 후 라인 수
    line_count = 0

    # 시작 시점 파일 끝 위치
    if not path.exists():
        console.print(f"[red]로그 파일이 없음:[/red] {path}")
        console.print("[yellow]PIE 시작하면 자동 생성됨. 대기 중...[/yellow]")

    # tail은 sleep+seek 패턴
    pos = 0
    if path.exists():
        pos = path.stat().st_size

    with Live(
        build_table(current, prev, change_age, line_count, str(path)),
        console=console,
        refresh_per_second=10,
        screen=False,
    ) as live:
        while True:
            try:
                if path.exists():
                    size = path.stat().st_size
                    if size < pos:
                        # 로그 파일 회전 (truncate)
                        pos = 0
                    if size > pos:
                        with open(path, "rb") as f:
                            f.seek(pos)
                            chunk = f.read(size - pos).decode("utf-8", errors="ignore")
                            pos = size
                        for raw in chunk.splitlines():
                            if PREFIX not in raw:
                                continue
                            parsed = parse_line(raw)
                            if not parsed:
                                continue
                            line_count += 1
                            # change_age 증가
                            for k in change_age:
                                change_age[k] += 1
                            # 변경 감지
                            for k, v in parsed.items():
                                if current.get(k) != v:
                                    change_age[k] = 0
                            prev = current
                            current = parsed
                live.update(build_table(current, prev, change_age, line_count, str(path)))
                time.sleep(interval)
            except KeyboardInterrupt:
                break


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", default=DEFAULT_LOG, help=f"로그 파일 경로 (default: {DEFAULT_LOG})")
    ap.add_argument("--interval", type=float, default=0.1, help="폴링 주기 초 (default: 0.1)")
    args = ap.parse_args()

    log_path = Path(args.log)
    print(f"watching: {log_path}")
    print(f"polling: {args.interval}s")
    print("Ctrl+C로 종료\n")
    tail_log(log_path, args.interval)


if __name__ == "__main__":
    main()
