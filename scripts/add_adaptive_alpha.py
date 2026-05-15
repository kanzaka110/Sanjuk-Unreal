#!/usr/bin/env python3
"""
PC_01_ABP — UpdateTargetRotation trd smoothing Adaptive Alpha (2026-05-15).

부작용: Alpha=0.075 가 큰 회전(180°)엔 best지만 빠른 연속 입력 변화 시 mesh lag.

처방: |diff| < 45° 면 Alpha=0.5 (빠른 반응), else Alpha=0.075 (부드러운).

추가 노드:
- Abs_DoubleDouble: CF_11 (NA diff).ReturnValue → AbsDiff
- Less_DoubleDouble: AbsDiff < 45.0 → bIsSmall
- SelectFloat: A=0.5, B=0.075, bPickA=bIsSmall → SelectedAlpha
- CF_12.B 핀: SelectedAlpha (default 0.075 → wire input)
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("adaptive_alpha")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "UpdateTargetRotation"
THRESHOLD = 45.0
ALPHA_SMALL = 0.5
ALPHA_LARGE = 0.075

_msg_id = [9000]


def call(action: str, params: dict[str, Any], allow_error: bool = False) -> Any:
    _msg_id[0] += 1
    body = {
        "jsonrpc": "2.0",
        "id": _msg_id[0],
        "method": "tools/call",
        "params": {
            "name": "blueprint_query",
            "arguments": {"action": action, "params": params},
        },
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8")
    data = json.loads(raw)
    if data.get("result", {}).get("isError"):
        if allow_error:
            log.warning("[WARN] action=%s err=%s", action, raw[:200])
            return None
        log.error("[ERROR] action=%s -> %s", action, raw[:400])
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return txt


def add_call(func_name: str, target_class: str, position: list[int]) -> str:
    out = call("add_node", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_type": "CallFunction", "position": position,
        "function_name": func_name, "target_class": target_class,
    })
    nid = out["id"] if isinstance(out, dict) else out
    log.info("[+] %s -> %s", func_name, nid)
    return nid


def connect(src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    return call("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": src, "source_pin": src_pin,
        "target_node": tgt, "target_pin": tgt_pin,
    })


def set_pin(node_id: str, pin_name: str, value: str) -> Any:
    return call("set_pin_default", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": node_id, "pin_name": pin_name, "value": value,
    })


def main() -> None:
    log.info("\n=== Adaptive Alpha 노드 추가 ===")
    # InRange_FloatFloat 로 |diff| < 45 판정 (Min=-45, Max=45)
    in_range = add_call("InRange_FloatFloat", "KismetMathLibrary", [2380, 600])
    sel_node = add_call("SelectFloat", "KismetMathLibrary", [2520, 600])

    log.info("\n=== wiring ===")
    # InRange(Value=CF_11.ReturnValue, Min=-45, Max=45) → bIsSmall
    connect("K2Node_CallFunction_11", "ReturnValue", in_range, "Value")
    set_pin(in_range, "Min", f"-{THRESHOLD}")
    set_pin(in_range, "Max", str(THRESHOLD))
    # Select(A=0.5, B=0.075, bPickA=bIsSmall)
    set_pin(sel_node, "A", str(ALPHA_SMALL))
    set_pin(sel_node, "B", str(ALPHA_LARGE))
    connect(in_range, "ReturnValue", sel_node, "bPickA")
    # → CF_12.B (Multiply 의 B 핀)
    connect(sel_node, "ReturnValue", "K2Node_CallFunction_12", "B")

    log.info("\n=== compile + save ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: %s", c)
    s = call("save_asset", {"asset_path": ASSET}, allow_error=True)
    log.info("save:    %s", s)
    log.info("\n[DONE] abs=%s less=%s sel=%s", abs_node, less_node, sel_node)


if __name__ == "__main__":
    main()
