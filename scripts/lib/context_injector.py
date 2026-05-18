"""Context Injector — Inspector/Agent 호출 시 7가지 자동 첨부.

채널 L (로그·정보 수집 시스템).

목적: Inspector 답변 정확도 5~10배 향상. AI가 케이스 진단 시 매번 같은 정보를
수집하지 않아도 되게 표준 컨텍스트 자동 생성.

7가지 자동 첨부:
    1. 자산 dump (Monolith) — ABP 그래프 / 변수 / 노드 구조
    2. [ANIM_REC] slice — SB2_2.log 최근 N초 또는 N프레임
    3. [SM_TRACE] slice — 미래 (State Machine trace, Phase 5)
    4. [NOTIFY_TRACE] slice — 미래 (AnimNotify trace, Phase 6)
    5. UE log filter — LogPoseSearch / LogChooser / LogAnim
    6. Briefing — 최근 작업 컨텍스트 (5/14~ 최신 md)
    7. git log — 최근 N개 commit

사용 예 (Python):
    from lib.context_injector import build_context
    ctx = build_context(
        case="락온 + 반대 질주 종료 시 mesh 이중 회전",
        asset_paths=["/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"],
        log_lines=300,
        briefing_count=3,
        git_count=10,
    )
    print(ctx)  # Markdown 문자열

사용 예 (CLI):
    python scripts/lib/context_injector.py --case "..." --asset "/Game/..." --log-lines 300
    python scripts/lib/context_injector.py --case "..." --to-file /tmp/ctx.md

Inspector 통합:
    Inspector 에이전트 호출 전에 context_injector 결과를 프롬프트 앞에 첨부.
    Inspector는 항상 같은 형식 컨텍스트를 받게 됨.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Paths
PROJECT_ROOT = Path(r"C:\Dev\Sanjuk-Unreal")
BRIEFING_DIR = PROJECT_ROOT / "Briefing"
DEFAULT_SB2_LOG = Path(r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2_2.log")
DEFAULT_SB2_LOG_PRIMARY = Path(r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2.log")
MONOLITH_ENDPOINT = "http://localhost:9316/mcp"

# Inspector 기본 카테고리 (log_filter 의 PC01_CATEGORIES 와 동기)
PC01_LOG_CATEGORIES = [
    "LogAnim", "LogAnimMontage", "LogPoseSearch", "LogChooser",
    "LogStateTree", "LogBlueprintUserMessages", "LogMotionMatching",
]


@dataclass
class ContextSection:
    """컨텍스트의 한 섹션 (asset dump / log slice / briefing 등)."""
    title: str
    content: str
    fence_lang: str = ""  # 코드 펜스 언어 (선택)
    truncated: bool = False
    line_count: int = 0

    def render(self) -> str:
        body = self.content
        if self.fence_lang:
            body = f"```{self.fence_lang}\n{body}\n```"
        trunc_note = f" *(truncated, {self.line_count} lines total)*" if self.truncated else ""
        return f"## {self.title}{trunc_note}\n\n{body}\n"


@dataclass
class Context:
    """전체 컨텍스트 — 7개 섹션 + 메타."""
    case: str
    timestamp: str
    sections: list[ContextSection] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            f"# Inspector Context — {self.case}",
            f"",
            f"_Generated: {self.timestamp}_",
            f"",
            "---",
            "",
        ]
        for s in self.sections:
            lines.append(s.render())
            lines.append("---\n")
        return "\n".join(lines)


# ───────────────────────────────────────────────────────────────
# 1. 자산 dump
# ───────────────────────────────────────────────────────────────

def fetch_asset_dump(asset_paths: list[str], graph_names: list[str] | None = None) -> ContextSection:
    """Monolith로 자산 + 그래프 dump."""
    lines = []
    for asset in asset_paths:
        lines.append(f"### {asset}")
        lines.append("")
        # blueprint_info
        info = _monolith_call("blueprint_query", "get_blueprint_info", {"asset_path": asset})
        if info:
            lines.append(f"- parent_class: `{info.get('parent_class', '?')}`")
            lines.append(f"- total_graphs: {info.get('total_graphs', '?')}")
            lines.append(f"- total_nodes: {info.get('total_nodes', '?')}")
        # 그래프별 노드 수
        graphs = _monolith_call("blueprint_query", "list_graphs", {"asset_path": asset})
        if graphs and isinstance(graphs, dict):
            graph_list = graphs.get("graphs", [])
            lines.append(f"- graphs: {len(graph_list)}")
            if graph_names:
                lines.append("")
                lines.append("주요 그래프 노드 수:")
                for gname in graph_names:
                    g = _monolith_call("blueprint_query", "get_graph_data",
                                       {"asset_path": asset, "graph_name": gname})
                    if g and isinstance(g, dict):
                        nodes = g.get("nodes", [])
                        lines.append(f"  - `{gname}`: {len(nodes)} 노드")
        lines.append("")

    return ContextSection(
        title="1️⃣ 자산 Dump",
        content="\n".join(lines) if lines else "(자산 정보 가져오기 실패 — Monolith 미실행?)",
    )


def _monolith_call(tool: str, action: str, params: dict) -> Any:
    """Monolith RPC 호출 (조용히 실패 — context 누락 허용)."""
    try:
        body = {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": tool, "arguments": {"action": action, "params": params}},
        }
        req = urllib.request.Request(
            MONOLITH_ENDPOINT,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8")
        data = json.loads(raw)
        if data.get("result", {}).get("isError"):
            return None
        txt = data["result"]["content"][0]["text"]
        try:
            return json.loads(txt)
        except json.JSONDecodeError:
            return txt
    except Exception:
        return None


# ───────────────────────────────────────────────────────────────
# 2. [ANIM_REC] slice
# ───────────────────────────────────────────────────────────────

def fetch_anim_rec_slice(
    log_path: Path, lines: int = 200, sessions: list[dict] | None = None
) -> ContextSection:
    """SB2 로그에서 [ANIM_REC] 마지막 N개 라인 + Phase 1 std prefix."""
    if not log_path.exists():
        return ContextSection(
            title="2️⃣ [ANIM_REC] Slice",
            content=f"(로그 파일 없음: {log_path})",
        )
    sessions = sessions or []
    matched: list[str] = []
    total = 0
    with log_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if "[ANIM_REC]" in line:
                matched.append(reformat_std(line, sessions) if sessions else line.rstrip("\n"))
                total += 1
    sliced = matched[-lines:]
    body = "\n".join(sliced) if sliced else "(매칭 라인 없음)"
    return ContextSection(
        title=f"2️⃣ [ANIM_REC] Slice (최근 {len(sliced)}/{total} lines, std prefix)",
        content=body,
        fence_lang="",
        truncated=len(sliced) < total,
        line_count=total,
    )


# ───────────────────────────────────────────────────────────────
# 3. [SM_TRACE] slice (placeholder — Phase 5)
# ───────────────────────────────────────────────────────────────

def fetch_sm_trace_slice(
    log_path: Path, lines: int = 100, sessions: list[dict] | None = None
) -> ContextSection:
    """[SM_TRACE] State Machine trace — Phase 5 영구 포기 (AnimGraph thread safety 제약)."""
    sessions = sessions or []
    body = (
        "_Phase 5 영구 포기_. AnimGraph 컨텍스트의 thread safety 제약으로 SM state "
        "직접 추적 불가. 대안: ANIM_REC 의 as/ms/pwm/ist + pas/pms2/ppwm Prev 필드 조합으로 유추."
    )
    if log_path.exists():
        matched = []
        with log_path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                if "[SM_TRACE]" in line:
                    matched.append(reformat_std(line, sessions) if sessions else line.rstrip("\n"))
        if matched:
            body = "\n".join(matched[-lines:])
    return ContextSection(title="3️⃣ [SM_TRACE] Slice (포기 — as/ms/pwm 조합 유추)", content=body)


# ───────────────────────────────────────────────────────────────
# 4. [NOTIFY_TRACE] slice (placeholder — Phase 6)
# ───────────────────────────────────────────────────────────────

def fetch_notify_trace_slice(
    log_path: Path, lines: int = 100, sessions: list[dict] | None = None
) -> ContextSection:
    """[NOTIFY_TRACE] AnimNotify trace — Phase 6.

    1) ABP 안에 [NOTIFY_TRACE] PrintText 가 있으면 그걸 캡처 (없으면 비어있음)
    2) LogAnimNotify / LogAnimMontage / LogAnimation 카테고리도 함께 추출 (UE verbose 활성화 시)
    """
    sessions = sessions or []
    NOTIFY_CATS = {"LogAnimNotify", "LogAnimMontage", "LogAnimation"}

    if not log_path.exists():
        return ContextSection(
            title="4️⃣ [NOTIFY_TRACE] Slice",
            content=f"(로그 파일 없음: {log_path})",
        )

    explicit: list[str] = []   # [NOTIFY_TRACE] PrintText
    cat_hits: list[str] = []   # LogAnimNotify 등
    cat_counter: dict[str, int] = {}

    with log_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if "[NOTIFY_TRACE]" in line:
                explicit.append(reformat_std(line, sessions) if sessions else line.rstrip("\n"))
                continue
            m = LOG_LINE_RE.match(line)
            if m and m.group("cat") in NOTIFY_CATS:
                # Notify 키워드 추가 필터 (모든 LogAnimation 라인이 Notify는 아님)
                msg = m.group("msg") or ""
                if "Notify" in msg or "Montage" in msg or "Section" in msg or "Branching" in msg:
                    cat_hits.append(reformat_std(line, sessions) if sessions else line.rstrip("\n"))
                    cat = m.group("cat")
                    cat_counter[cat] = cat_counter.get(cat, 0) + 1

    body_lines: list[str] = []

    # Explicit channel
    if explicit:
        body_lines.append(f"### Explicit [NOTIFY_TRACE] ({len(explicit)} lines)")
        body_lines.append("")
        body_lines.extend(explicit[-lines:])
        body_lines.append("")
    else:
        body_lines.append("### Explicit [NOTIFY_TRACE]")
        body_lines.append("")
        body_lines.append("_ABP 안 [NOTIFY_TRACE] PrintText 채널 없음 (옵션 — 추가하려면 NotifyState BP 의 NotifyBegin/End 에 PrintText 삽입)._")
        body_lines.append("")

    # Category fallback
    summary = " / ".join(f"{c}: {n}" for c, n in cat_counter.items()) or "(0건 — UE 콘솔에서 `Log LogAnimNotify Verbose` 활성화 필요)"
    body_lines.append(f"### UE Notify 카테고리 ({summary})")
    body_lines.append("")
    if cat_hits:
        body_lines.extend(cat_hits[-lines:])
    else:
        body_lines.append("_LogAnimNotify / LogAnimMontage / LogAnimation 캡처 0건._")
        body_lines.append("")
        body_lines.append("**활성화 방법** (PIE 시작 후 UE 콘솔에서 입력):")
        body_lines.append("```")
        body_lines.append("Log LogAnimNotify Verbose")
        body_lines.append("Log LogAnimMontage Verbose")
        body_lines.append("Log LogAnimation Verbose")
        body_lines.append("```")
        body_lines.append("또는 `DefaultEngine.ini` [Core.Log] 섹션:")
        body_lines.append("```ini")
        body_lines.append("LogAnimNotify=Verbose")
        body_lines.append("LogAnimMontage=Verbose")
        body_lines.append("```")

    return ContextSection(
        title="4️⃣ [NOTIFY_TRACE] Slice (Phase 6, std prefix)",
        content="\n".join(body_lines),
        truncated=len(cat_hits) > lines,
        line_count=len(explicit) + len(cat_hits),
    )


# ───────────────────────────────────────────────────────────────
# 5. UE log filter (LogPoseSearch / LogChooser / LogAnim 등)
# ───────────────────────────────────────────────────────────────

LOG_LINE_RE = re.compile(
    r"^\[(?P<ts>\d+\.\d+\.\d+-\d+\.\d+\.\d+:\d+)\]"
    r"\[(?P<frame>[\s\d]+)\]"
    r"(?P<cat>Log[A-Z][A-Za-z]*)(?P<verbosity>:\s*Verbose:|:\s*Warning:|:\s*Error:|:)?"
    r"\s*(?P<msg>.*)$"
)

# Phase 1 — PIE 세션 마커 + 표준 prefix (log_filter.py 와 동기)
PIE_START_RE = re.compile(
    r"LogWorld: Bringing World (?P<world>/[^ ]+/UEDPIE_\d+_[^ ]+?)(?:\.[^ ]+)? up for play"
)
PIE_END_RE = re.compile(r"LogWorld: BeginTearingDown for (?P<world>/[^ ]+/UEDPIE_\d+_[^ ]+)")


def _parse_ts(ts: str) -> float:
    try:
        _, time_part = ts.split("-")
        h, mn, sms = time_part.split(".")
        s, ms = sms.split(":")
        return int(h) * 3600 + int(mn) * 60 + int(s) + int(ms) / 1000
    except Exception:
        return 0.0


def find_pie_sessions(log_path: Path) -> list[dict]:
    sessions: list[dict] = []
    active: dict | None = None
    with log_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            m = LOG_LINE_RE.match(line)
            if not m:
                continue
            msg = line
            m_start = PIE_START_RE.search(msg)
            m_end = PIE_END_RE.search(msg)
            if m_start:
                if active:
                    sessions.append(active)
                active = {
                    "idx": len(sessions) + 1,
                    "world": m_start.group("world"),
                    "start_ts_sec": _parse_ts(m.group("ts")),
                    "end_ts_sec": None,
                }
            elif m_end and active:
                if active["world"] in m_end.group("world") or m_end.group("world") in active["world"]:
                    active["end_ts_sec"] = _parse_ts(m.group("ts"))
                    sessions.append(active)
                    active = None
    if active:
        sessions.append(active)
    return sessions


def assign_pie(ts_sec: float, sessions: list[dict]) -> tuple[int | None, float | None]:
    for s in sessions:
        if ts_sec >= s["start_ts_sec"]:
            if s["end_ts_sec"] is None or ts_sec <= s["end_ts_sec"]:
                return s["idx"], ts_sec - s["start_ts_sec"]
    return None, None


def std_prefix_for(parsed: dict, sessions: list[dict]) -> str:
    ts_sec = _parse_ts(parsed["ts"])
    pie_idx, t_rel = assign_pie(ts_sec, sessions)
    frame = parsed["frame"].strip()
    pie_str = f"PIE={pie_idx}" if pie_idx is not None else "PIE=-"
    t_str = f"t={t_rel:7.3f}s" if t_rel is not None else "t=  -.---s"
    return f"[{pie_str} frame={frame:>5} {t_str}]"


def reformat_std(raw_line: str, sessions: list[dict]) -> str:
    """원본 UE 로그 라인 → 표준 prefix 라인."""
    m = LOG_LINE_RE.match(raw_line)
    if not m:
        return raw_line.rstrip("\n")
    parsed = m.groupdict()
    verb = parsed.get("verbosity") or ":"
    return f"{std_prefix_for(parsed, sessions)} [{parsed['cat']}{verb}] {parsed['msg']}"


def fetch_ue_log_filter(
    log_path: Path, categories: list[str], lines: int = 100,
    sessions: list[dict] | None = None,
) -> ContextSection:
    """log_filter.py 와 동일 로직 — 카테고리별 추출 + 카운트 + Phase 1 std prefix."""
    if not log_path.exists():
        return ContextSection(
            title="5️⃣ UE Log Filter",
            content=f"(로그 파일 없음: {log_path})",
        )
    sessions = sessions or []
    cat_set = set(categories)
    matched: list[str] = []
    counter: dict[str, int] = {c: 0 for c in categories}
    with log_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            m = LOG_LINE_RE.match(line)
            if not m:
                continue
            cat = m.group("cat")
            if cat in cat_set:
                if sessions:
                    parsed = m.groupdict()
                    verb = parsed.get("verbosity") or ":"
                    matched.append(f"{std_prefix_for(parsed, sessions)} [{cat}{verb}] {parsed['msg']}")
                else:
                    matched.append(line.rstrip("\n"))
                counter[cat] = counter.get(cat, 0) + 1
    summary = " / ".join(f"{c}: {n}" for c, n in counter.items() if n > 0) or "(매칭 0건 — verbose 활성화 필요)"
    body_lines = [f"_카운트: {summary}_", ""]
    sliced = matched[-lines:]
    body_lines.extend(sliced)
    return ContextSection(
        title="5️⃣ UE Log Filter (PC_01 진단 카테고리, std prefix)",
        content="\n".join(body_lines),
        truncated=len(sliced) < len(matched),
        line_count=len(matched),
    )


# ───────────────────────────────────────────────────────────────
# 6. Briefing — 최근 작업 컨텍스트
# ───────────────────────────────────────────────────────────────

def fetch_briefing(count: int = 3, pattern: str = "*.md") -> ContextSection:
    """최근 Briefing md 파일 목록 + 첫 헤더."""
    if not BRIEFING_DIR.exists():
        return ContextSection(title="6️⃣ Briefing", content=f"({BRIEFING_DIR} 없음)")
    files = sorted(BRIEFING_DIR.rglob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    files = files[:count]
    if not files:
        return ContextSection(title="6️⃣ Briefing", content="(매칭 파일 없음)")
    lines = []
    for f in files:
        rel = f.relative_to(PROJECT_ROOT)
        # 첫 30라인만
        head = []
        try:
            with f.open(encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh):
                    if i >= 30: break
                    head.append(line.rstrip("\n"))
        except Exception:
            continue
        lines.append(f"### `{rel}`")
        lines.append("```markdown")
        lines.extend(head)
        lines.append("```")
        lines.append("")
    return ContextSection(title=f"6️⃣ Briefing (최근 {len(files)}개)", content="\n".join(lines))


# ───────────────────────────────────────────────────────────────
# 7. git log
# ───────────────────────────────────────────────────────────────

def fetch_git_log(count: int = 10) -> ContextSection:
    """최근 git commit."""
    try:
        result = subprocess.run(
            ["git", "log", f"-{count}", "--oneline", "--decorate"],
            cwd=PROJECT_ROOT,
            capture_output=True, text=True, timeout=10, encoding="utf-8",
        )
        body = result.stdout.strip() if result.returncode == 0 else f"git log 실패: {result.stderr}"
    except Exception as e:
        body = f"git log 호출 실패: {e}"
    return ContextSection(title=f"7️⃣ git log (최근 {count}개)", content=body, fence_lang="")


# ───────────────────────────────────────────────────────────────
# Build context
# ───────────────────────────────────────────────────────────────

def build_context(
    case: str,
    asset_paths: list[str] | None = None,
    graph_names: list[str] | None = None,
    log_path: Path | None = None,
    log_lines: int = 200,
    log_categories: list[str] | None = None,
    briefing_count: int = 3,
    git_count: int = 10,
) -> Context:
    """7개 섹션 컨텍스트 생성."""
    log_path = log_path or (DEFAULT_SB2_LOG if DEFAULT_SB2_LOG.exists() else DEFAULT_SB2_LOG_PRIMARY)
    asset_paths = asset_paths or ["/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"]
    log_categories = log_categories or PC01_LOG_CATEGORIES

    ctx = Context(case=case, timestamp=datetime.now().isoformat(timespec="seconds"))

    # Phase 1 — PIE 세션 1회 추출 후 모든 로그 섹션이 std prefix 적용
    sessions = find_pie_sessions(log_path) if log_path.exists() else []

    ctx.sections.append(fetch_asset_dump(asset_paths, graph_names))
    ctx.sections.append(fetch_anim_rec_slice(log_path, log_lines, sessions=sessions))
    ctx.sections.append(fetch_sm_trace_slice(log_path, sessions=sessions))
    ctx.sections.append(fetch_notify_trace_slice(log_path, sessions=sessions))
    ctx.sections.append(fetch_ue_log_filter(log_path, log_categories, lines=80, sessions=sessions))
    ctx.sections.append(fetch_briefing(briefing_count))
    ctx.sections.append(fetch_git_log(git_count))

    return ctx


# ───────────────────────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case", required=True, help="진단 케이스 설명 (예: 락온 반대 질주 종료)")
    p.add_argument("--asset", action="append", help="자산 경로 (여러 번 가능)")
    p.add_argument("--graph", action="append", help="그래프명 (여러 번 가능, 자산 dump 시 노드 수 추출)")
    p.add_argument("--log", help="SB2 로그 경로 (기본: SB2_2.log)")
    p.add_argument("--log-lines", type=int, default=200, help="ANIM_REC slice 라인 수")
    p.add_argument("--briefing-count", type=int, default=3, help="최근 brief 파일 수")
    p.add_argument("--git-count", type=int, default=10, help="최근 commit 수")
    p.add_argument("--to-file", help="결과를 파일로 저장 (기본: stdout)")
    args = p.parse_args()

    ctx = build_context(
        case=args.case,
        asset_paths=args.asset,
        graph_names=args.graph,
        log_path=Path(args.log) if args.log else None,
        log_lines=args.log_lines,
        briefing_count=args.briefing_count,
        git_count=args.git_count,
    )
    rendered = ctx.render()

    if args.to_file:
        out = Path(args.to_file)
        out.write_text(rendered, encoding="utf-8")
        size = out.stat().st_size
        print(f"context 저장: {out} ({size:,} bytes)", file=sys.stderr)
    else:
        print(rendered)


if __name__ == "__main__":
    main()
