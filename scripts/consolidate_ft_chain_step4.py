#!/usr/bin/env python3
"""STEP 4: Swap downstream from old K2Node_FormatText_1.Result to new K2Node_FormatText_2.Result.

Old FT_1.Result feeds:
  - K2Node_CallFunction_4.InText
  - K2Node_VariableSet_1.RewindMonitorLine
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"
OLD_FT = "K2Node_FormatText_1"
NEW_FT = "K2Node_FormatText_2"

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)


def rpc(action: str, params: dict) -> dict | None:
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
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    if data.get("result", {}).get("isError"):
        log.error("!! %s ERROR: %s", action, data["result"]["content"][0]["text"][:800])
        return None
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def disconnect(src_node: str, src_pin: str, dest_node: str, dest_pin: str) -> bool:
    r = rpc(
        "disconnect_pins",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "source_node": src_node,
            "source_pin": src_pin,
            "target_node": dest_node,
            "target_pin": dest_pin,
        },
    )
    return r is not None


def connect(src_node: str, src_pin: str, dest_node: str, dest_pin: str) -> bool:
    r = rpc(
        "connect_pins",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "source_node": src_node,
            "source_pin": src_pin,
            "target_node": dest_node,
            "target_pin": dest_pin,
        },
    )
    return r is not None


def main() -> None:
    log.info("=== disconnect FT_1.Result -> CallFunction_4.InText ===")
    log.info("  %s", disconnect(OLD_FT, "Result", "K2Node_CallFunction_4", "InText"))
    log.info("=== disconnect FT_1.Result -> VariableSet_1.RewindMonitorLine ===")
    log.info("  %s", disconnect(OLD_FT, "Result", "K2Node_VariableSet_1", "RewindMonitorLine"))
    log.info("=== connect new FT.Result -> CallFunction_4.InText ===")
    log.info("  %s", connect(NEW_FT, "Result", "K2Node_CallFunction_4", "InText"))
    log.info("=== connect new FT.Result -> VariableSet_1.RewindMonitorLine ===")
    log.info("  %s", connect(NEW_FT, "Result", "K2Node_VariableSet_1", "RewindMonitorLine"))


if __name__ == "__main__":
    main()
