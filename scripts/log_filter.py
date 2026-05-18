#!/usr/bin/env python3
"""UE Output Log Filter — LogAnim/LogPoseSearch/LogChooser 등 카테고리 자동 추출.

채널 E (로그·정보 수집 시스템).

사용 예:
    # 카테고리 요약 (어떤 LogXxx 카테고리가 몇 개)
    python scripts/log_filter.py --summary

    # 특정 카테고리만 추출
    python scripts/log_filter.py --category LogPoseSearch

    # 여러 카테고리 동시
    python scripts/log_filter.py --category LogAnim,LogPoseSearch,LogChooser

    # 최근 N개 라인
    python scripts/log_filter.py --category LogPoseSearch --tail 50

    # 특정 키워드 포함
    python scripts/log_filter.py --grep "Sprint_to_Battle"

    # tail -f 모드 (실시간)
    python scripts/log_filter.py --category LogPoseSearch --follow

    # 시간 범위 필터
    python scripts/log_filter.py --since 12:00:00 --until 12:05:00

    # 다른 로그 파일
    python scripts/log_filter.py --log "E:/Perforce/SB2/Workspace/Internal/SB2/Saved/Logs/SB2.log"

기본 카테고리 (PC_01 ABP 진단 용도):
    LogAnim          — Animation runtime (verbose 활성화 필요)
    LogPoseSearch    — Motion Matching cost / 매칭 결정
    LogChooser       — Chooser Table 평가 결과
    LogBlueprintUserMessages — PrintString 출력 (ANIM_REC 등 포함)

verbose 활성화 (UE 콘솔 또는 DefaultEngine.ini):
    Log LogPoseSearch Verbose
    Log LogChooser Verbose
    Log LogAnim Verbose
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from collections import Counter
from pathlib import Path

DEFAULT_LOG = r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2_2.log"

# PC_01 ABP 진단에 자주 쓰는 카테고리
PC01_CATEGORIES = [
    "LogAnim",
    "LogAnimNotify",       # Phase 6 — Notify trigger trace (verbose 활성화 필요)
    "LogAnimMontage",
    "LogAnimation",        # Phase 6 — 일부 Notify event 가 이쪽에 찍힘
    "LogPoseSearch",
    "LogChooser",
    "LogStateTree",
    "LogBlueprintUserMessages",
    "LogBlueprint",
    "LogMotionMatching",
]

# Phase 6 — AnimNotify 진단용 카테고리
NOTIFY_CATEGORIES = ["LogAnimNotify", "LogAnimMontage", "LogAnimation"]

# `[2026.05.15-07.13.05:567][676]LogCategory:  Message...` 패턴
LOG_LINE_RE = re.compile(
    r"^\[(?P<ts>\d+\.\d+\.\d+-\d+\.\d+\.\d+:\d+)\]"
    r"\[(?P<frame>[\s\d]+)\]"
    r"(?P<cat>Log[A-Z][A-Za-z]*)(?P<verbosity>:\s*Verbose:|:\s*Warning:|:\s*Error:|:)?"
    r"\s*(?P<msg>.*)$"
)

# PIE 세션 마커 — Phase 1 표준화
PIE_START_RE = re.compile(
    r"LogWorld: Bringing World (?P<world>/[^ ]+/UEDPIE_\d+_[^ ]+?)(?:\.[^ ]+)? up for play"
)
PIE_END_RE = re.compile(
    r"LogWorld: BeginTearingDown for (?P<world>/[^ ]+/UEDPIE_\d+_[^ ]+)"
)


def parse_line(line: str) -> dict | None:
    """UE 로그 라인 parse. 매치 안 되면 None."""
    m = LOG_LINE_RE.match(line)
    if not m:
        return None
    return m.groupdict()


def find_pie_sessions(log_path: Path) -> list[dict]:
    """로그 안의 PIE 세션 (시작/종료/world) 추출.

    Returns:
        [{'idx': 1, 'start_ts': 'YYYY...', 'end_ts': ..., 'world': '...',
          'start_ts_sec': float, 'end_ts_sec': float}, ...]
        end_ts 가 없으면 None (로그 끝까지 진행 중).
    """
    sessions: list[dict] = []
    active: dict | None = None
    with log_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            parsed = parse_line(line)
            if not parsed:
                continue
            msg = parsed["cat"] + (parsed.get("verbosity") or "") + " " + parsed["msg"]
            m_start = PIE_START_RE.search(msg)
            m_end = PIE_END_RE.search(msg)
            if m_start:
                if active:  # 이전 PIE 미종료 → 강제 마감
                    sessions.append(active)
                active = {
                    "idx": len(sessions) + 1,
                    "world": m_start.group("world"),
                    "start_ts": parsed["ts"],
                    "start_ts_sec": parse_ts(parsed["ts"]),
                    "end_ts": None,
                    "end_ts_sec": None,
                }
            elif m_end and active:
                if active["world"] in m_end.group("world") or m_end.group("world") in active["world"]:
                    active["end_ts"] = parsed["ts"]
                    active["end_ts_sec"] = parse_ts(parsed["ts"])
                    sessions.append(active)
                    active = None
    if active:
        sessions.append(active)
    return sessions


def assign_pie(ts_sec: float, sessions: list[dict]) -> tuple[int | None, float | None]:
    """timestamp 가 어느 PIE 세션에 속하는지 (pie_idx, t_relative_sec) 반환."""
    for s in sessions:
        if ts_sec >= s["start_ts_sec"]:
            if s["end_ts_sec"] is None or ts_sec <= s["end_ts_sec"]:
                return s["idx"], ts_sec - s["start_ts_sec"]
    return None, None


def std_prefix(parsed: dict, sessions: list[dict]) -> str:
    """표준 prefix `[PIE=N frame=X t=T.TTTs]` 생성."""
    ts_sec = parse_ts(parsed["ts"])
    pie_idx, t_rel = assign_pie(ts_sec, sessions)
    frame = parsed["frame"].strip()
    pie_str = f"PIE={pie_idx}" if pie_idx is not None else "PIE=-"
    t_str = f"t={t_rel:7.3f}s" if t_rel is not None else "t=  -.---s"
    return f"[{pie_str} frame={frame:>5} {t_str}]"


def parse_ts(ts: str) -> float:
    """UE timestamp `YYYY.MM.DD-HH.MM.SS:ms` → epoch-ish float (sort용)."""
    try:
        date_part, time_part = ts.split("-")
        h, mn, sms = time_part.split(".")
        s, ms = sms.split(":")
        return int(h) * 3600 + int(mn) * 60 + int(s) + int(ms) / 1000
    except Exception:
        return 0.0


def time_str_to_seconds(s: str) -> float | None:
    """`12:34:56` 또는 `12:34` → seconds-of-day."""
    if not s:
        return None
    parts = s.split(":")
    try:
        if len(parts) == 3:
            h, m, sec = parts
            return int(h) * 3600 + int(m) * 60 + int(sec)
        if len(parts) == 2:
            h, m = parts
            return int(h) * 3600 + int(m) * 60
    except ValueError:
        return None
    return None


def summary(log_path: Path) -> None:
    """전체 로그 카테고리별 라인 수 요약."""
    if not log_path.exists():
        print(f"ERROR: log file not found: {log_path}", file=sys.stderr)
        sys.exit(1)

    counter: Counter[str] = Counter()
    pc01_counter: Counter[str] = Counter()
    total_lines = 0

    with log_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            total_lines += 1
            parsed = parse_line(line)
            if not parsed:
                continue
            cat = parsed["cat"]
            counter[cat] += 1
            if cat in PC01_CATEGORIES:
                pc01_counter[cat] += 1

    print(f"=== {log_path.name} 요약 ===")
    print(f"전체 라인: {total_lines:,}")
    print(f"파싱된 로그 라인: {sum(counter.values()):,}")
    print(f"카테고리 수: {len(counter)}")

    if pc01_counter:
        print("\n=== PC_01 ABP 진단 카테고리 ===")
        for cat, n in pc01_counter.most_common():
            print(f"  {n:>8,}  {cat}")
    else:
        print("\n⚠ PC_01 ABP 진단 카테고리 모두 0건.")
        print("  → UE 콘솔에서 verbosity 활성화 필요:")
        print("    Log LogPoseSearch Verbose")
        print("    Log LogChooser Verbose")
        print("    Log LogAnim Verbose")

    print("\n=== Top 20 카테고리 (전체) ===")
    for cat, n in counter.most_common(20):
        marker = " ★" if cat in PC01_CATEGORIES else ""
        print(f"  {n:>8,}  {cat}{marker}")


def extract(
    log_path: Path,
    categories: list[str] | None,
    grep: str | None,
    since_sec: float | None,
    until_sec: float | None,
    tail: int | None,
    follow: bool,
    fmt: str = "raw",
    pie_filter: int | None = None,
    sessions: list[dict] | None = None,
) -> None:
    """카테고리/grep/시간/PIE 필터로 추출.

    fmt: "raw" (원본 라인) 또는 "std" (표준 prefix 정규화).
    pie_filter: 특정 PIE idx 만.
    """
    if not log_path.exists():
        print(f"ERROR: log file not found: {log_path}", file=sys.stderr)
        sys.exit(1)

    grep_re = re.compile(grep) if grep else None
    cat_set = set(categories) if categories else None
    sessions = sessions or []

    def matches(parsed: dict, raw: str) -> bool:
        if cat_set and parsed["cat"] not in cat_set:
            return False
        if grep_re and not grep_re.search(raw):
            return False
        if since_sec is not None or until_sec is not None or pie_filter is not None:
            ts_sec = parse_ts(parsed["ts"])
            if since_sec is not None and ts_sec < since_sec:
                return False
            if until_sec is not None and ts_sec > until_sec:
                return False
            if pie_filter is not None:
                pie_idx, _ = assign_pie(ts_sec, sessions)
                if pie_idx != pie_filter:
                    return False
        return True

    def format_line(parsed: dict, raw: str) -> str:
        if fmt == "std":
            verb = parsed.get("verbosity") or ":"
            return f"{std_prefix(parsed, sessions)} [{parsed['cat']}{verb}] {parsed['msg']}"
        return raw.rstrip("\n")

    if follow:
        # tail -f 모드
        with log_path.open(encoding="utf-8", errors="replace") as f:
            f.seek(0, 2)  # EOF
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                parsed = parse_line(line)
                if parsed and matches(parsed, line):
                    print(format_line(parsed, line))
        return

    # 일반 모드
    results: list[str] = []
    with log_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            parsed = parse_line(line)
            if not parsed:
                continue
            if matches(parsed, line):
                results.append(format_line(parsed, line))

    if tail:
        results = results[-tail:]

    for r in results:
        print(r)

    if not results:
        print("(매칭 결과 없음)", file=sys.stderr)


def list_pie_sessions(log_path: Path) -> None:
    """PIE 세션 리스트 출력."""
    sessions = find_pie_sessions(log_path)
    if not sessions:
        print("(PIE 세션 감지 없음)")
        return
    print(f"=== {log_path.name} PIE 세션 {len(sessions)}개 ===")
    print(f"{'idx':>3}  {'start':<22}  {'end':<22}  {'duration':>9}  world")
    for s in sessions:
        end = s.get("end_ts") or "(active)"
        if s["end_ts_sec"] is not None:
            dur = f"{s['end_ts_sec'] - s['start_ts_sec']:8.1f}s"
        else:
            dur = "    --   "
        world = s["world"].rsplit("/", 1)[-1]
        print(f"  {s['idx']:>2}  {s['start_ts']:<22}  {end:<22}  {dur}  {world}")


def main() -> None:
    p = argparse.ArgumentParser(
        description="UE Output Log 카테고리 필터 (PC_01 ABP 진단 채널 E)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--log", default=DEFAULT_LOG, help=f"로그 파일 경로 (기본: {DEFAULT_LOG})")
    p.add_argument("--summary", action="store_true", help="카테고리별 요약")
    p.add_argument("--list-pie", action="store_true", help="PIE 세션 리스트")
    p.add_argument(
        "--category", "-c",
        help="추출할 카테고리 (콤마 구분, 예: LogAnim,LogPoseSearch). 미지정 시 PC_01 기본 카테고리"
    )
    p.add_argument("--grep", "-g", help="라인 내 키워드 정규식")
    p.add_argument("--tail", "-n", type=int, help="마지막 N개 라인")
    p.add_argument("--follow", "-f", action="store_true", help="tail -f 모드 (실시간)")
    p.add_argument("--since", help="시작 시간 (HH:MM:SS)")
    p.add_argument("--until", help="종료 시간 (HH:MM:SS)")
    p.add_argument(
        "--format", choices=["raw", "std"], default="raw",
        help="출력 형식: raw=원본, std=[PIE=N frame=X t=T.TTTs] 표준 prefix"
    )
    p.add_argument("--pie", type=int, help="특정 PIE 세션만 (idx, 1-based)")
    p.add_argument(
        "--notify", action="store_true",
        help="AnimNotify trace 모드 — NOTIFY_CATEGORIES 자동 선택 + Notify/Montage 키워드 grep"
    )

    args = p.parse_args()
    log_path = Path(args.log)

    if args.summary:
        summary(log_path)
        return

    if args.list_pie:
        list_pie_sessions(log_path)
        return

    cats: list[str] | None
    if args.notify:
        cats = NOTIFY_CATEGORIES
        if not args.grep:
            args.grep = "Notify|Montage|Section|Branching"
    elif args.category:
        cats = [c.strip() for c in args.category.split(",")]
    else:
        cats = PC01_CATEGORIES  # 기본: PC_01 진단 카테고리

    # PIE 세션 — std 포맷 또는 --pie 사용 시에만 필요
    sessions: list[dict] = []
    if args.format == "std" or args.pie is not None:
        sessions = find_pie_sessions(log_path)

    extract(
        log_path,
        categories=cats,
        grep=args.grep,
        since_sec=time_str_to_seconds(args.since) if args.since else None,
        until_sec=time_str_to_seconds(args.until) if args.until else None,
        tail=args.tail,
        follow=args.follow,
        fmt=args.format,
        pie_filter=args.pie,
        sessions=sessions,
    )


if __name__ == "__main__":
    main()
