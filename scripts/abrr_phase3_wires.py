#!/usr/bin/env python3
"""ABRR Phase 3: wire all edges from the backup connected_to lists.

Reads:
  - Backup graph (80 nodes, 67 wires including FT_2 input + Result downstream + backbone)
  - ABRR_id_map.json (old -> new)

For each input pin in the backup that has connected_to, issue connect_pins.
We only iterate input pins to avoid creating each edge twice
(output->input is symmetric).
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from pathlib import Path

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"
BACKUP = Path(r"C:\Dev\Sanjuk-Unreal\Saved\PROBE_AnimRewindRecorderEmit_consolidated_20260514.json")
MAP_IN = Path(r"C:\Dev\Sanjuk-Unreal\Saved\ABRR_id_map.json")

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)
_msg_id = [0]


def rpc(action: str, params: dict) -> dict | str | None:
    _msg_id[0] += 1
    body = {
        "jsonrpc": "2.0", "id": _msg_id[0], "method": "tools/call",
        "params": {"name": "blueprint_query",
                   "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data.get("result", {}).get("isError"):
        return {"_error": data["result"]["content"][0]["text"][:600]}
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def connect(src_node: str, src_pin: str, dst_node: str, dst_pin: str) -> tuple[bool, str]:
    r = rpc("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": src_node, "source_pin": src_pin,
        "target_node": dst_node, "target_pin": dst_pin,
    })
    if isinstance(r, dict) and "_error" in r:
        return False, r["_error"][:200]
    return True, "OK"


def main() -> None:
    backup = json.loads(BACKUP.read_text(encoding="utf-8"))
    id_map: dict[str, str] = json.loads(MAP_IN.read_text(encoding="utf-8-sig"))

    # Collect all edges from input pins.
    edges = []  # list of (src_node_old, src_pin, dst_node_old, dst_pin, dst_pin_dir)
    for node in backup["nodes"]:
        for pin in node["pins"]:
            for ref in pin.get("connected_to", []):
                if "." not in ref:
                    continue
                src_old, src_pin = ref.split(".", 1)
                dst_old = node["id"]
                dst_pin = pin["name"]
                edges.append((src_old, src_pin, dst_old, dst_pin, pin["direction"]))

    # Keep only edges that terminate at input pins (to avoid duplicates).
    input_edges = [e for e in edges if e[4] == "input"]
    log.info("Total edge refs: %d  unique-by-input: %d", len(edges), len(input_edges))

    failures = []
    success = 0
    for i, (s_old, s_pin, d_old, d_pin, _) in enumerate(input_edges, 1):
        s_new = id_map.get(s_old)
        d_new = id_map.get(d_old)
        if not s_new or not d_new:
            log.error("[%2d] MAP miss: %s.%s -> %s.%s (mapped: %s -> %s)",
                      i, s_old, s_pin, d_old, d_pin, s_new, d_new)
            failures.append((s_old, s_pin, d_old, d_pin, "map_miss"))
            continue

        # Special: split-struct vars — pin name on dst already matches new graph
        # (we recreated them as split). On source side, K2Node_GetEnumeratorNameAsString
        # output pin was 'ReturnValue' (string); the replacement GetEnumeratorName
        # function returns 'name' so pin name is the same 'ReturnValue'.

        ok, msg = connect(s_new, s_pin, d_new, d_pin)
        status = "OK" if ok else f"FAIL: {msg}"
        log.info("[%2d/%d] %s.%-30s -> %s.%-15s  [%s]",
                 i, len(input_edges), s_new, s_pin, d_new, d_pin, status)
        if ok:
            success += 1
        else:
            failures.append((s_old, s_pin, d_old, d_pin, msg))

    log.info("\n=== Result: %d OK / %d FAIL ===", success, len(failures))
    if failures:
        for s_old, s_pin, d_old, d_pin, err in failures:
            log.error("  %s.%s -> %s.%s : %s", s_old, s_pin, d_old, d_pin, err)
        sys.exit(2)


if __name__ == "__main__":
    main()
