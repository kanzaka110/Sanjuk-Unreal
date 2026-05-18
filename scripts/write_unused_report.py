#!/usr/bin/env python3
"""action_catalog.json + action_usage.json → unused_actions.md.

discover_monolith_actions.py 와 별도로, 이미 만들어진 두 파일을 그대로 합쳐
미사용 리포트만 빠르게 갱신한다.
"""
from __future__ import annotations

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(REPO_ROOT, ".claude", "state")
CATALOG_PATH = os.path.join(STATE_DIR, "action_catalog.json")
USAGE_PATH = os.path.join(STATE_DIR, "action_usage.json")
UNUSED_PATH = os.path.join(STATE_DIR, "unused_actions.md")


def main() -> int:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    with open(USAGE_PATH, "r", encoding="utf-8") as f:
        usage = json.load(f)

    used = {ns: set(a) for ns, a in usage.get("by_domain", {}).items()}

    lines = ["# Monolith Unused Actions Report", ""]
    lines.append(f"- discovered_at: {catalog['_meta']['discovered_at']}")
    lines.append(f"- total_actions: {catalog['_meta']['total_actions']}")
    lines.append(f"- domain_count:  {catalog['_meta']['domain_count']}")
    used_total = usage["_meta"]["used_actions_total"]
    lines.append(f"- used_actions:  {used_total}")
    lines.append(
        f"- unused_total:  {catalog['_meta']['total_actions'] - used_total}"
    )
    lines.append("")
    lines.append("## 도메인별 사용/미사용 요약")
    lines.append("")
    lines.append("| 도메인 | 사용 / 전체 | 사용률 |")
    lines.append("|---|---:|---:|")
    for ns in sorted(catalog["domains"]):
        actions = catalog["domains"][ns]["actions"]
        u = len(used.get(ns, set()))
        total = len(actions)
        pct = (u / total * 100) if total else 0.0
        lines.append(f"| {ns} | {u} / {total} | {pct:.1f}% |")
    lines.append("")
    lines.append("## 도메인별 미사용 액션")
    lines.append("")

    for ns in sorted(catalog["domains"]):
        actions = catalog["domains"][ns]["actions"]
        u = used.get(ns, set())
        unused = [a for a in actions if a not in u]
        if not unused:
            continue
        lines.append(f"### {ns} — 미사용 {len(unused)}/{len(actions)}")
        lines.append("")
        # 50개 제한 없이 전체 출력 (도메인이 크면 별도 toc 만들 수도)
        for a in unused:
            lines.append(f"- `{a}`")
        lines.append("")

    os.makedirs(STATE_DIR, exist_ok=True)
    with open(UNUSED_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {UNUSED_PATH}")
    print(f"  used   {used_total}")
    print(
        f"  unused {catalog['_meta']['total_actions'] - used_total} "
        f"({(catalog['_meta']['total_actions'] - used_total) / catalog['_meta']['total_actions'] * 100:.1f}%)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
