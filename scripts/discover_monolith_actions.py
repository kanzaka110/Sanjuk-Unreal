#!/usr/bin/env python3
"""Monolith 액션 카탈로그 발견 (MVP-1).

호출 흐름:
  1. monolith.discover() → 전체 도메인/액션 리스트
  2. (fallback) 모듈별 *.discover() 또는 *.list_actions()
  3. (fallback) 알려진 도메인 enumerate

출력:
  - .claude/state/action_catalog.json   (전체 카탈로그)
  - .claude/state/unused_actions.md     (미사용 액션 리포트)

사용:
  py C:/Dev/Sanjuk-Unreal/scripts/discover_monolith_actions.py
  py C:/Dev/Sanjuk-Unreal/scripts/discover_monolith_actions.py --usage <usage.json>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime

ENDPOINT = "http://localhost:9316/mcp"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(REPO_ROOT, ".claude", "state")
HISTORY_DIR = os.path.join(STATE_DIR, "catalog_history")
CATALOG_PATH = os.path.join(STATE_DIR, "action_catalog.json")
UNUSED_PATH = os.path.join(STATE_DIR, "unused_actions.md")

# 알려진 도메인 (fallback enumerate용 — 실제 monolith.discover() 결과로 갱신될 것)
KNOWN_DOMAINS = (
    "monolith",
    "animation_query",
    "blueprint_query",
    "material_query",
    "niagara_query",
    "config_query",
    "editor_query",
    "physics_query",
    "chooser_query",
    "logic_driver_query",
    "mesh_query",
    "gas_query",
    "ai_query",
    "ui_query",
    "audio_query",
    "control_rig_query",
)

_msg_id = [0]


def rpc(method: str, params: dict | None = None, silent: bool = False) -> dict | None:
    _msg_id[0] += 1
    body = {
        "jsonrpc": "2.0",
        "id": _msg_id[0],
        "method": method,
    }
    if params:
        body["params"] = params
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        if not silent:
            print(f"  [RPC FAIL] {method}: {exc}", file=sys.stderr)
        return None


def call_tool(name: str, arguments: dict, silent: bool = False) -> dict | None:
    """Standard MCP tools/call wrapper."""
    return rpc("tools/call", {"name": name, "arguments": arguments}, silent=silent)


def try_discover_top_level() -> dict | None:
    """1차 시도: monolith.discover() 같은 top-level 메타 액션."""
    candidates = [
        ("tools/list", None),                   # MCP 표준
        ("tools/call", {"name": "monolith", "arguments": {"action": "discover"}}),
        ("tools/call", {"name": "monolith.discover", "arguments": {}}),
        ("tools/call", {"name": "discover", "arguments": {}}),
    ]
    for method, params in candidates:
        print(f"[try] {method} {params}")
        r = rpc(method, params, silent=True)
        if r and not r.get("error"):
            print(f"  ✓ {method} succeeded")
            return r
    return None


def enumerate_domain_actions(domain: str) -> list[str]:
    """도메인별 action 리스트 받기. 여러 패턴 시도."""
    candidates = [
        {"action": "discover"},
        {"action": "list_actions"},
        {"action": "help"},
        {"action": "list"},
    ]
    for args in candidates:
        r = call_tool(domain, args, silent=True)
        if not r or r.get("error"):
            continue
        result = r.get("result", {})
        if result.get("isError"):
            continue
        # MCP content[0].text 파싱
        content = result.get("content", [])
        if not content:
            continue
        text = content[0].get("text", "")
        try:
            data = json.loads(text)
        except Exception:
            continue
        # 다양한 응답 형식 시도
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("actions", "available_actions", "list", "items"):
                if key in data and isinstance(data[key], list):
                    return data[key]
    return []


def build_catalog() -> dict:
    """전체 카탈로그 구축."""
    print("=" * 60)
    print("Phase 1: top-level discover")
    print("=" * 60)
    top = try_discover_top_level()

    catalog = {
        "_meta": {
            "discovered_at": datetime.now().isoformat(),
            "endpoint": ENDPOINT,
            "method": "unknown",
        },
        "domains": {},
        "raw_top_level": top,
    }

    # tools/list 응답이면 파싱
    if top and "result" in top and "tools" in top.get("result", {}):
        tools = top["result"]["tools"]
        catalog["_meta"]["method"] = "tools/list"
        print(f"  found {len(tools)} tools")
        for t in tools:
            name = t.get("name", "?")
            catalog["domains"][name] = {
                "description": t.get("description", ""),
                "schema": t.get("inputSchema"),
                "actions": [],   # 도메인별 추가 enumerate 필요
            }

    # 도메인별 추가 enumerate
    print()
    print("=" * 60)
    print("Phase 2: per-domain enumerate")
    print("=" * 60)
    target_domains = list(catalog["domains"].keys()) or list(KNOWN_DOMAINS)
    for d in target_domains:
        actions = enumerate_domain_actions(d)
        if actions:
            print(f"  {d:30s} -> {len(actions)} actions")
            if d not in catalog["domains"]:
                catalog["domains"][d] = {"actions": []}
            catalog["domains"][d]["actions"] = actions
        else:
            print(f"  {d:30s} -> (no actions)")

    # 통계
    total_actions = sum(len(v.get("actions", [])) for v in catalog["domains"].values())
    catalog["_meta"]["total_actions"] = total_actions
    catalog["_meta"]["domain_count"] = len(catalog["domains"])
    return catalog


def load_usage_data(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_unused_report(catalog: dict, usage: dict | None) -> None:
    """미사용 액션 강조 리포트 .md."""
    lines = ["# Monolith Unused Actions Report", ""]
    lines.append(f"- discovered_at: {catalog['_meta']['discovered_at']}")
    lines.append(f"- total_actions: {catalog['_meta']['total_actions']}")
    lines.append(f"- domain_count: {catalog['_meta']['domain_count']}")
    if usage:
        used_total = sum(len(v) for v in usage.get("by_domain", {}).values())
        lines.append(f"- used_actions: {used_total}")
        lines.append(f"- usage_data: provided")
    else:
        lines.append(f"- usage_data: NONE (모든 액션을 미사용으로 표시)")
    lines.append("")
    lines.append("## 도메인별 미사용 액션")
    lines.append("")

    for domain, info in sorted(catalog["domains"].items()):
        actions = info.get("actions", [])
        if not actions:
            continue
        used = set()
        if usage:
            used = set(usage.get("by_domain", {}).get(domain, []))
        unused = [a for a in actions if a not in used]
        if not unused:
            continue
        lines.append(f"### {domain} — 미사용 {len(unused)}/{len(actions)}")
        lines.append("")
        for a in unused[:50]:  # 너무 길면 50개까지
            lines.append(f"- `{a}`")
        if len(unused) > 50:
            lines.append(f"- ... ({len(unused) - 50} more)")
        lines.append("")

    os.makedirs(os.path.dirname(UNUSED_PATH), exist_ok=True)
    with open(UNUSED_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nWrote unused report: {UNUSED_PATH}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usage", help=".claude/state/action_usage.json 경로 (선택)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    catalog = build_catalog()

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  total domains:  {catalog['_meta']['domain_count']}")
    print(f"  total actions:  {catalog['_meta']['total_actions']}")
    for d, info in sorted(catalog["domains"].items()):
        n = len(info.get("actions", []))
        print(f"    {d:30s} {n:5d}")

    if args.dry_run:
        print("\n[DRY-RUN] Skipping file writes.")
        return

    # 저장
    os.makedirs(STATE_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"\nWrote catalog: {CATALOG_PATH}")

    # 히스토리 스냅샷
    snap_name = f"catalog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    snap_path = os.path.join(HISTORY_DIR, snap_name)
    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"Wrote snapshot: {snap_path}")

    # 미사용 리포트
    usage = load_usage_data(args.usage) if args.usage else None
    write_unused_report(catalog, usage)


if __name__ == "__main__":
    main()
