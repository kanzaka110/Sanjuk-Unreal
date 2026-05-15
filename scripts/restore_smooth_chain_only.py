#!/usr/bin/env python3
"""
PC_01_ABP — smooth chain 만 복원 (게이트 없이 모든 시점 smooth, 2026-05-15).

사용자 결정: 게이트/SelectFloat 폐기. smooth chain 만 살림. 모든 strafe 시점 smooth 적용.

데이터 흐름:
    CF_32 (Raw NormalizeAxis) → [Subtract Raw - Prev] → [NA diff]
    → [Multiply * 0.075 literal] → [Add Prev + Half] → [NA smooth] → Set TargetRotationDelta
    NA smooth → Set PrevTargetRotationDelta (다음 프레임용)

exec:
    Set TargetRotationDelta.then → Set PrevTargetRotationDelta.execute

Phases:
    1. PrevTargetRotationDelta 변수 추가
    2. smooth chain 7노드 추가 (Get×2 + Subtract + NA + Multiply + Add + NA + Set)
    3. wiring
    4. CF_32 → Set_3 직결 끊기 + smooth 결과 → Set_3 새 wire
    5. compile + save
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("restore_smooth")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "UpdateTargetRotation"
ALPHA = "0.075"

_msg_id = [14000]


def call(action: str, params: dict[str, Any], allow_error: bool = False) -> Any:
    _msg_id[0] += 1
    body = {
        "jsonrpc": "2.0", "id": _msg_id[0], "method": "tools/call",
        "params": {"name": "blueprint_query", "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
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


def add_node(node_type: str, position: list[int], **kwargs: Any) -> str:
    out = call("add_node", {
        "asset_path": ASSET, "graph_name": GRAPH, "node_type": node_type,
        "position": position, **kwargs,
    })
    nid = out["id"] if isinstance(out, dict) else out
    label = kwargs.get("function_name") or kwargs.get("variable_name") or node_type
    log.info("[+] %s -> %s", label, nid)
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
    # Phase 1: variable
    log.info("\n=== Phase 1: PrevTargetRotationDelta 변수 ===")
    call("add_variable", {
        "asset_path": ASSET,
        "name": "PrevTargetRotationDelta",
        "type": "double",
        "category": "Buffer",
        "default_value": "0.0",
        "instance_editable": False,
        "blueprint_read_only": False,
    })

    # Phase 2: smooth chain nodes
    log.info("\n=== Phase 2: smooth chain 7노드 ===")
    get_prev_a = add_node("VariableGet", [2080, 700], variable_name="PrevTargetRotationDelta")
    get_prev_b = add_node("VariableGet", [2400, 800], variable_name="PrevTargetRotationDelta")
    sub_node = add_node("CallFunction", [2240, 700],
                        function_name="Subtract_DoubleDouble", target_class="KismetMathLibrary")
    na_diff = add_node("CallFunction", [2400, 700],
                       function_name="NormalizeAxis", target_class="KismetMathLibrary")
    mul_node = add_node("CallFunction", [2560, 700],
                        function_name="Multiply_DoubleDouble", target_class="KismetMathLibrary")
    add_node_smooth = add_node("CallFunction", [2720, 720],
                               function_name="Add_DoubleDouble", target_class="KismetMathLibrary")
    na_smooth = add_node("CallFunction", [2880, 720],
                         function_name="NormalizeAxis", target_class="KismetMathLibrary")
    set_prev = add_node("VariableSet", [3120, 720], variable_name="PrevTargetRotationDelta")

    # Phase 3: data wiring
    log.info("\n=== Phase 3: data wiring ===")
    # Subtract: A = CF_32 (Raw NA), B = PrevTargetRotationDelta
    connect("K2Node_CallFunction_32", "ReturnValue", sub_node, "A")
    connect(get_prev_a, "PrevTargetRotationDelta", sub_node, "B")
    # NA(diff) ← Subtract
    connect(sub_node, "ReturnValue", na_diff, "Angle")
    # Multiply: A = NA(diff), B = 0.075 literal
    connect(na_diff, "ReturnValue", mul_node, "A")
    set_pin(mul_node, "B", ALPHA)
    # Add: A = PrevTargetRotationDelta, B = Multiply
    connect(get_prev_b, "PrevTargetRotationDelta", add_node_smooth, "A")
    connect(mul_node, "ReturnValue", add_node_smooth, "B")
    # NA(smooth) ← Add
    connect(add_node_smooth, "ReturnValue", na_smooth, "Angle")
    # Smooth → Set TargetRotationDelta + Set PrevTargetRotationDelta
    connect(na_smooth, "ReturnValue", set_prev, "PrevTargetRotationDelta")

    # Phase 4: replace Raw → Set_3 with Smooth → Set_3
    log.info("\n=== Phase 4: rewire Set_3 input ===")
    # disconnect CF_32 → Set_3
    call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": "K2Node_CallFunction_32", "pin_name": "ReturnValue",
        "target_node": "K2Node_VariableSet_3", "target_pin": "TargetRotationDelta",
    })
    # connect na_smooth → Set_3
    connect(na_smooth, "ReturnValue", "K2Node_VariableSet_3", "TargetRotationDelta")

    # exec: Set_3.then → set_prev.execute (Set_3.then 이 비어있을 경우)
    connect("K2Node_VariableSet_3", "then", set_prev, "execute")

    # Phase 5: compile + save
    log.info("\n=== Phase 5: compile + save ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: %s", c)
    s = call("save_asset", {"asset_path": ASSET}, allow_error=True)
    log.info("save:    %s", s)


if __name__ == "__main__":
    main()
