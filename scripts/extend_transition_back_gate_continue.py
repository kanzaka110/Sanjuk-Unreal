#!/usr/bin/env python3
"""
Continue extend_transition_back_gate after Phase 1/2 partial completion.

상황: extend_transition_back_gate.py 실행 중 Phase 2 마지막에
ExecutionSequence_3.then_13 핀 부재로 exec wiring 실패.
- Phase 1 변수 추가 ✓
- Phase 2 노드 13개 추가 ✓ (Set = K2Node_VariableSet_69)
- Phase 2 exec wiring ✗ (then_13 미존재)
- Phase 3 미실행
- Phase 4 미실행

이 스크립트:
1. then_12 leg에 Set 노드 insert (then_12 -> Set.execute -> Set.then -> Knot_1.InputPin)
2. Phase 3 (UpdateTargetRotation 게이트)
3. validate + compile + save
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("phase1_continue")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
VAR_NAME = "bIsPlayingTransitionBack"
SET_NODE = "K2Node_VariableSet_69"  # phase 2에서 추가된 Set bIsPlayingTransitionBack

_msg_id = [5000]


def call(action: str, params: dict[str, Any]) -> Any:
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
        log.error("[ERROR] action=%s params=%s -> %s", action, params, raw)
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return txt


def add_node(graph: str, node_type: str, position: list[int], **kwargs: Any) -> str:
    out = call(
        "add_node",
        {
            "asset_path": ASSET,
            "graph_name": graph,
            "node_type": node_type,
            "position": position,
            **kwargs,
        },
    )
    nid = out["id"] if isinstance(out, dict) else out
    label = kwargs.get("function_name") or kwargs.get("variable_name") or node_type
    log.info("[+] %s %s -> %s", graph, label, nid)
    return nid


def connect(graph: str, src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    out = call(
        "connect_pins",
        {
            "asset_path": ASSET,
            "graph_name": graph,
            "source_node": src,
            "source_pin": src_pin,
            "target_node": tgt,
            "target_pin": tgt_pin,
        },
    )
    log.info("  link %s: %s.%s -> %s.%s", graph, src, src_pin, tgt, tgt_pin)
    return out


def disconnect(graph: str, src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    out = call(
        "disconnect_pins",
        {
            "asset_path": ASSET,
            "graph_name": graph,
            "node_id": src,
            "pin_name": src_pin,
            "target_node": tgt,
            "target_pin": tgt_pin,
        },
    )
    log.info("  xlink %s: %s.%s -X- %s.%s", graph, src, src_pin, tgt, tgt_pin)
    return out


def set_pin(graph: str, node_id: str, pin_name: str, value: str) -> Any:
    out = call(
        "set_pin_default",
        {
            "asset_path": ASSET,
            "graph_name": graph,
            "node_id": node_id,
            "pin_name": pin_name,
            "value": value,
        },
    )
    log.info("  set %s: %s.%s = %r", graph, node_id, pin_name, value)
    return out


# ---------------------------------------------------------------------------
# Step A: insert Set into then_12 leg
# ---------------------------------------------------------------------------
def step_a_insert_exec() -> None:
    log.info("\n=== Step A: insert Set into then_12 leg ===")
    graph = "UpdateVariables"
    # before:  ExecutionSequence_3.then_12 -> Knot_1.InputPin
    # after:   ExecutionSequence_3.then_12 -> Set_69.execute
    #          Set_69.then                  -> Knot_1.InputPin
    disconnect(graph, "K2Node_ExecutionSequence_3", "then_12", "K2Node_Knot_1", "InputPin")
    connect(graph, "K2Node_ExecutionSequence_3", "then_12", SET_NODE, "execute")
    connect(graph, SET_NODE, "then", "K2Node_Knot_1", "InputPin")


# ---------------------------------------------------------------------------
# Step B: Phase 3 UpdateTargetRotation gate
# ---------------------------------------------------------------------------
def step_b_target_rotation() -> dict[str, str]:
    log.info("\n=== Step B: UpdateTargetRotation gate ===")
    graph = "UpdateTargetRotation"
    sel = add_node(graph, "CallFunction", [2080, 720],
                   function_name="SelectFloat", target_class="KismetMathLibrary")
    get_back = add_node(graph, "VariableGet", [1840, 568], variable_name=VAR_NAME)
    not_id = add_node(graph, "CallFunction", [1990, 596],
                      function_name="Not_PreBool", target_class="KismetMathLibrary")

    disconnect(graph, "K2Node_CallFunction_4", "ReturnValue",
               "K2Node_VariableSet_3", "TargetRotationDelta")
    connect(graph, "K2Node_CallFunction_4", "ReturnValue", sel, "A")
    set_pin(graph, sel, "B", "0.0")
    connect(graph, get_back, VAR_NAME, not_id, "A")
    connect(graph, not_id, "ReturnValue", sel, "bPickA")
    connect(graph, sel, "ReturnValue", "K2Node_VariableSet_3", "TargetRotationDelta")
    return {"sel": sel, "not": not_id, "get_back": get_back}


# ---------------------------------------------------------------------------
# Step C: validate + compile + save
# ---------------------------------------------------------------------------
def step_c_compile_save() -> None:
    log.info("\n=== Step C: validate + compile + save ===")
    out_v = call("validate_blueprint", {"asset_path": ASSET})
    log.info("  validate: %s", out_v)
    out_c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("  compile:  %s", out_c)
    out_s = call("save_asset", {"asset_path": ASSET})
    log.info("  save:     %s", out_s)


def main() -> None:
    step_a_insert_exec()
    p3 = step_b_target_rotation()
    step_c_compile_save()
    log.info("\n[ALL DONE] phase3=%s", p3)


if __name__ == "__main__":
    main()
