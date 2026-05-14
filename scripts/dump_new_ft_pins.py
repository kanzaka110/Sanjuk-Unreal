#!/usr/bin/env python3
"""Dump the new FT node pins and verify 66 argument pins exist."""
from __future__ import annotations

import json
import logging
import sys
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"
NEW_FT = "K2Node_FormatText_2"

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)


EXPECTED_PINS = [
    "f", "sp", "as", "ms", "ist", "he", "vlen", "pwm", "il", "isf",
    "isc", "csh", "trd", "ib", "rmf", "fik", "fca", "ow", "ig", "sc",
    "clip", "seq", "bim", "bpim", "ms_l", "ms_p", "mm", "ops", "fbsw", "fa",
    "rop", "sba", "ibk", "we", "iw", "jes", "htt", "stip", "ip", "lm",
    "dal", "sset", "phase", "eow", "eprw", "fv", "acc", "isafb", "isaub",
    "sswseq", "wt", "cvco", "ubsw", "rva", "rvmci", "ifl", "rj", "dog",
    "hd", "pav_z", "cav_z", "sms", "vac", "na", "rrt", "rrr",
]


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
        log.error("!! %s ERROR: %s", action, data["result"]["content"][0]["text"][:600])
        return None
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def main() -> None:
    info = rpc(
        "get_node_details",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_id": NEW_FT,
        },
    )
    if not info:
        log.error("get_node_details failed")
        sys.exit(1)
    pins = info.get("pins", [])
    pin_names = [p["name"] for p in pins if p["direction"] == "input" and p["name"] != "Format"]
    log.info("Total pins: %d", len(pins))
    log.info("Input arg pins (excluding Format): %d", len(pin_names))
    log.info("Pins found: %s", pin_names)

    missing = [p for p in EXPECTED_PINS if p not in pin_names]
    extra = [p for p in pin_names if p not in EXPECTED_PINS]
    log.info("Missing pins: %s", missing)
    log.info("Extra pins: %s", extra)
    if not missing and not extra:
        log.info("OK: all 66 argument pins match.")


if __name__ == "__main__":
    main()
