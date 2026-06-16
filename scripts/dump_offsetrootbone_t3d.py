#!/usr/bin/env python3
"""PC_01_ABP AnimGraph T3D export -> OffsetRootBone 노드 블록만 추출.

bUseManualRelease 현재값 확인용 (gun mode 통돌이 판별 실험 2026-06-12).
출력: scripts/backups/pc01_abp_animgraph_2026-06-12.t3d (전체) + stdout (노드 블록).
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
ENDPOINT = "http://localhost:9316/mcp"
OUT = Path(__file__).parent / "backups" / "pc01_abp_animgraph_2026-06-12.t3d"


def rpc(action: str, params: dict[str, Any]) -> Any:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "blueprint_query",
            "arguments": {"action": action, "params": params},
        },
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("result", {}).get("isError"):
        print("[ERROR]", data["result"]["content"][0]["text"][:400])
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def main() -> None:
    r = rpc("export_graph", {"asset_path": ASSET, "graph_name": "AnimGraph"})
    t3d = r.get("t3d") or r.get("text") or r if isinstance(r, dict) else r
    if isinstance(t3d, dict):
        print("[keys]", list(t3d.keys()))
        t3d = json.dumps(t3d, ensure_ascii=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(t3d, encoding="utf-8")
    print(f"[saved] {OUT} ({len(t3d)} chars)")

    # OffsetRootBone 노드 블록 추출
    lines = t3d.splitlines()
    in_block = False
    depth = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("Begin Object") and "OffsetRootBone" in s:
            in_block = True
        if in_block:
            if s.startswith("Begin Object"):
                depth += 1
            # 핀 서브오브젝트 줄은 생략, Node= 프로퍼티 줄만 출력
            if depth <= 1 and ("Node=(" in s or "Begin Object" in s or s.startswith("End Object") or "ManualRelease" in s or "bUseManual" in s):
                print(line[:500])
            elif "ManualRelease" in s:
                print(line[:500])
            if s.startswith("End Object"):
                depth -= 1
                if depth == 0:
                    in_block = False
                    print("---")


main()
