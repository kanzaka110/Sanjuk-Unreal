#!/usr/bin/env python3
"""monolith.discover() 결과를 catalog 포맷으로 영구화.

discover_monolith_actions.py 의 build_catalog() 가 tools/list 등 여러 fallback을
도는 대신, MCP `monolith.discover` 액션을 직접 호출해 결과를 단일 RPC로 받는다.

출력:
  - .claude/state/action_catalog.json
  - .claude/state/catalog_history/catalog_<timestamp>.json
"""
from __future__ import annotations

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


def rpc(method: str, params: dict | None = None) -> dict:
    body: dict = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params:
        body["params"] = params
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    resp = rpc(
        "tools/call",
        {"name": "monolith_discover", "arguments": {}},
    )
    if resp.get("error"):
        print(f"[FAIL] {resp['error']}", file=sys.stderr)
        return 1
    content = resp.get("result", {}).get("content", [])
    if not content:
        print("[FAIL] empty content", file=sys.stderr)
        return 1
    data = json.loads(content[0]["text"])

    catalog: dict = {
        "_meta": {
            "discovered_at": datetime.now().isoformat(),
            "endpoint": ENDPOINT,
            "method": "monolith.discover",
            "total_actions": data.get("total_actions"),
            "domain_count": len(data.get("namespaces", [])),
        },
        "domains": {},
        "optional_modules": data.get("optional_modules", []),
    }
    for ns in data.get("namespaces", []):
        name = ns["namespace"]
        catalog["domains"][name] = {
            "tool": f"{name}_query" if name != "monolith" else "monolith",
            "actions": ns.get("actions", []),
            "action_count": ns.get("action_count", 0),
        }

    os.makedirs(STATE_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    snap = os.path.join(
        HISTORY_DIR,
        f"catalog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(snap, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Wrote {CATALOG_PATH}")
    print(f"  total_actions = {catalog['_meta']['total_actions']}")
    print(f"  domains       = {catalog['_meta']['domain_count']}")
    print(f"Snapshot       {snap}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
