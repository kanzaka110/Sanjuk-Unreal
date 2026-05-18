#!/usr/bin/env python3
"""ANIM_REC 카테고리 재배치 롤백 — wire 8개 복원.

원인: 신13필드 chain 이 ABP 안에 이중 존재 (Chain 1 + Chain 2). 매핑 오류로 재배치
      후 chain 이 CF_25 까지 도달 안 함. 즉시 원상복귀.
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("rollback")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "AnimRewindRecorderEmit"

_msg_id = [20000]


def call(action: str, params: dict[str, Any], allow_error: bool = False) -> Any:
    _msg_id[0] += 1
    body = {
        "jsonrpc": "2.0", "id": _msg_id[0], "method": "tools/call",
        "params": {"name": "blueprint_query", "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data.get("result", {}).get("isError"):
        if allow_error: return None
        log.error("[ERR] %s -> %s", action, str(data)[:300])
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return txt


def disconnect(src, src_pin, tgt, tgt_pin):
    call("disconnect_pins", {"asset_path": ASSET, "graph_name": GRAPH,
                             "node_id": src, "pin_name": src_pin,
                             "target_node": tgt, "target_pin": tgt_pin}, allow_error=True)


def connect(src, src_pin, tgt, tgt_pin):
    call("connect_pins", {"asset_path": ASSET, "graph_name": GRAPH,
                          "source_node": src, "source_pin": src_pin,
                          "target_node": tgt, "target_pin": tgt_pin})


# (src, src_pin, current_target, current_pin, restore_target, restore_pin)
# = 재배치 결과 → 원래 wire 로 복원
WIRES = [
    ("K2Node_CallFunction_15", "ReturnValue", "K2Node_CallFunction_93", "A",
     "K2Node_CallFunction_23", "A"),
    ("K2Node_CallFunction_91", "ReturnValue", "K2Node_CallFunction_23", "A",
     "K2Node_CallFunction_93", "A"),
    ("K2Node_CallFunction_100", "ReturnValue", "K2Node_CallFunction_84", "A",
     "K2Node_CallFunction_25", "InString"),
    ("K2Node_CallFunction_40", "ReturnValue", "K2Node_CallFunction_67", "A",
     "K2Node_CallFunction_61", "A"),
    ("K2Node_CallFunction_69", "ReturnValue", "K2Node_CallFunction_61", "A",
     "K2Node_CallFunction_73", "A"),
    ("K2Node_CallFunction_63", "ReturnValue", "K2Node_CallFunction_79", "A",
     "K2Node_CallFunction_67", "A"),
    ("K2Node_CallFunction_81", "ReturnValue", "K2Node_CallFunction_73", "A",
     "K2Node_CallFunction_84", "A"),
    ("K2Node_CallFunction_75", "ReturnValue", "K2Node_CallFunction_25", "InString",
     "K2Node_CallFunction_79", "A"),
]


def main():
    log.info("\n=== 카테고리 재배치 wire 8개 롤백 ===")
    for i, (src, sp, cur_t, cur_p, restore_t, restore_p) in enumerate(WIRES, 1):
        log.info("\n--- [%d/%d] %s.%s ---", i, len(WIRES), src, sp)
        log.info("  disconnect %s.%s → %s.%s", src, sp, cur_t, cur_p)
        disconnect(src, sp, cur_t, cur_p)
        log.info("  reconnect  %s.%s → %s.%s", src, sp, restore_t, restore_p)
        connect(src, sp, restore_t, restore_p)

    log.info("\n=== compile ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: success=%s errors=%s warnings=%s",
             c.get("success"), c.get("error_count"), c.get("warning_count"))
    if c.get("errors"):
        for e in c["errors"][:5]: log.error("  ! %s", e)


if __name__ == "__main__":
    main()
