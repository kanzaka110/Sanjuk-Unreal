#!/usr/bin/env python3
"""STEP 6: Delete 8 old FormatText nodes. Compile between each delete."""
from __future__ import annotations

import json
import logging
import sys
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"

OLD_FT_IDS: tuple[str, ...] = (
    "K2Node_FormatText_8",
    "K2Node_FormatText_4",
    "K2Node_FormatText_0",
    "K2Node_FormatText_5",
    "K2Node_FormatText_11",
    "K2Node_FormatText_13",
    "K2Node_FormatText_12",
    "K2Node_FormatText_1",
)

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)


def rpc(action: str, params: dict) -> dict | None:
    body = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "blueprint_query", "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("result", {}).get("isError"):
        log.error("!! %s ERROR: %s", action, data["result"]["content"][0]["text"][:600])
        return None
    return json.loads(data["result"]["content"][0]["text"])


def main() -> None:
    for nid in OLD_FT_IDS:
        r = rpc(
            "remove_node",
            {"asset_path": ASSET, "graph_name": GRAPH, "node_id": nid},
        )
        log.info("remove %s -> %s", nid, r)
        if r is None:
            log.error("delete failed; abort")
            sys.exit(2)
        c = rpc("compile_blueprint", {"asset_path": ASSET})
        log.info("compile after %s -> errors=%s, warnings=%s",
                 nid, c.get("error_count"), c.get("warning_count"))
        if c and c.get("error_count", 0) > 0:
            log.error("compile errors detected; abort")
            log.error("errors: %s", c.get("errors"))
            sys.exit(3)


if __name__ == "__main__":
    main()
