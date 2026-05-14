#!/usr/bin/env python3
"""STEP 1: Consolidate 8 FormatText into a single FormatText.

Strategy:
  - Add new K2Node_FormatText with full 66-arg format string.
  - Try in-line `format` extra. If add_node rejects (size), fall back to
    a small placeholder then set_pin_default on Format pin.
  - Dump the new node's pins to confirm 66 argument pins were created.
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


FORMAT_STR = (
    '[ANIM_REC] "f"={f},"sp"={sp},"as"={as},"ms"={ms},"ist"={ist},"he"={he},'
    '"vlen"={vlen},"pwm"={pwm},"il"={il},"isf"={isf},"isc"={isc},"csh"={csh},'
    '"trd"={trd},"ib"={ib},"rmf"={rmf},"fik"={fik},"fca"={fca},"ow"={ow},'
    '"ig"={ig},"sc"={sc},"clip"={clip},"seq"={seq},"bim"={bim},"bpim"={bpim},'
    '"ms_l"={ms_l},"ms_p"={ms_p},"mm"={mm},"ops"={ops},"fbsw"={fbsw},"fa"={fa},'
    '"rop"={rop},"sba"={sba},"ibk"={ibk},"we"={we},"iw"={iw},"jes"={jes},'
    '"htt"={htt},"stip"={stip},"ip"={ip},"lm"={lm},"dal"={dal},"sset"={sset},'
    '"phase"={phase},"eow"={eow},"eprw"={eprw},"fv"={fv},"acc"={acc},'
    '"isafb"={isafb},"isaub"={isaub},"sswseq"={sswseq},"wt"={wt},"cvco"={cvco},'
    '"ubsw"={ubsw},"rva"={rva},"rvmci"={rvmci},"ifl"={ifl},"rj"={rj},"dog"={dog},'
    '"hd"={hd},"pav_z"={pav_z},"cav_z"={cav_z},"sms"={sms},"vac"={vac},'
    '"na"={na},"rrt"={rrt},"rrr"={rrr}'
)


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
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    if data.get("result", {}).get("isError"):
        msg = data["result"]["content"][0]["text"]
        log.error("!! %s ERROR: %s", action, msg[:800])
        return None
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def main() -> None:
    log.info("Format string length: %d bytes", len(FORMAT_STR))

    log.info("=== Attempt 1: add_node with full format extra ===")
    r = rpc(
        "add_node",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_type": "format_text",
            "position": [7280, 1500],
            "format": FORMAT_STR,
        },
    )
    if not r:
        log.error("Attempt 1 failed. Try placeholder fallback manually.")
        sys.exit(2)
    nid = r.get("node_id") or r.get("id")
    log.info("new FT -> %s", nid)
    log.info("full add_node result: %s", json.dumps(r, indent=2)[:2000])

    log.info("=== Inspect node pins ===")
    info = rpc(
        "get_node_info",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_id": nid,
        },
    )
    if info:
        log.info("node_info: %s", json.dumps(info, indent=2)[:6000])


if __name__ == "__main__":
    main()
