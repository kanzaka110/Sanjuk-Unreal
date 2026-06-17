"""snapshot → 네이티브 EUW TextBlock 에 그대로 꽂을 포맷 텍스트 생성 + 파일 기록.

EUW 는 Tick 마다 이 파일을 LoadFileToString 으로 읽어 단일 TextBlock 에 SetText 한다.
파싱 부담을 EUW(BP)에 주지 않으려고, 여기서 정렬·그룹·상태태그까지 끝낸 완성 텍스트를 쓴다.
"""
from __future__ import annotations

import os
import tempfile

from config import Config, Metric

_GROUP_TITLE = {
    "frame": "프레임 / GPU",
    "anim": "애니메이션",
    "physics": "물리 / 시뮬",
    "memory": "메모리",
    "general": "기타",
}
_STATUS_TAG = {"crit": "  ◀ CRIT", "warn": "  ◀ WARN", "ok": "", "na": ""}


def _fmt_value(v: float | None, unit: str) -> str:
    if v is None:
        return "—"
    num = f"{v:,.0f}" if abs(v) >= 1000 else f"{v:.2f}"
    return f"{num} {unit}".strip()


def format_display(cfg: Config, snapshot: dict) -> str:
    """snapshot dict → 여러 줄 표시 텍스트."""
    values = snapshot.get("values", {})
    status = snapshot.get("status", {})
    lines: list[str] = []
    if not snapshot.get("monitoring"):
        lines.append("● 정지됨 — 모니터링이 꺼져 있습니다.")
    elif snapshot.get("error"):
        lines.append(f"⚠ {snapshot['error']}")
    elif not snapshot.get("last_file"):
        lines.append("첫 캡처 대기 중…  (~3.5초)")
    else:
        lines.append(f"● 모니터링 중   (#{snapshot.get('t', 0)})")

    by_group: dict[str, list[Metric]] = {}
    for m in cfg.metrics:
        by_group.setdefault(m.group, []).append(m)

    for group, metrics in by_group.items():
        lines.append("")
        lines.append(f"── {_GROUP_TITLE.get(group, group)} ──")
        for m in metrics:
            val = _fmt_value(values.get(m.key), m.unit)
            tag = _STATUS_TAG.get(status.get(m.key, "na"), "")
            lines.append(f"  {m.label:<18} {val:>12}{tag}")
    return "\n".join(lines)


def write_display(cfg: Config, snapshot: dict) -> None:
    """표시 텍스트를 display_path 에 원자적으로 기록 (EUW 가 읽는 중 깨짐 방지)."""
    path = cfg.display_path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = format_display(cfg, snapshot)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)  # 원자적 교체
    except OSError:
        if os.path.exists(tmp):
            os.remove(tmp)
