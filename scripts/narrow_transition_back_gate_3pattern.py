#!/usr/bin/env python3
"""
PC_01_ABP — ① 처방 4번째 패턴 제거 (Contains "Transition_" AND IsLockOn).

부작용 발견: 4번째 패턴 (Contains("Transition_") AND IsLockOn) 가 락온 sprint 중
재생되는 `Transition_Run_to_Sprint_*`, `Transition_Sprint_to_Run_*` 등 일반 speed
transition까지 잡아서 sprint 내내 bIsPlayingTransitionBack=true → Strafe 회전
보정 항시 0 → trajectory forward stuck → MM이 F 클립만 선택.

처방: 4번째 패턴 노드 4개 제거 + OR2를 Set 입력으로 직결.

제거 노드:
- K2Node_CallFunction_32 (Contains "Transition_")
- K2Node_CallFunction_33 (BooleanAND)
- K2Node_CallFunction_36 (BooleanOR — 최종 단계)
- K2Node_VariableGet_51 (Get IsLockOn — 이 함수용)

재배선:
- before: K2Node_CallFunction_35.ReturnValue → K2Node_CallFunction_36.A
          K2Node_CallFunction_36.ReturnValue → K2Node_VariableSet_69.bIsPlayingTransitionBack
- after:  K2Node_CallFunction_35.ReturnValue → K2Node_VariableSet_69.bIsPlayingTransitionBack
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("narrow_3pattern")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"

NODES_TO_REMOVE = [
    "K2Node_CallFunction_36",  # OR3 (final)
    "K2Node_CallFunction_33",  # AND
    "K2Node_CallFunction_32",  # Contains "Transition_"
    "K2Node_VariableGet_51",   # Get IsLockOn (for this gate)
]

_msg_id = [6000]


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


def step_a_rewire() -> None:
    log.info("\n=== Step A: rewire OR2 -> Set ===")
    graph = "UpdateVariables"
    # disconnect OR3 -> Set
    call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "node_id": "K2Node_CallFunction_36", "pin_name": "ReturnValue",
        "target_node": "K2Node_VariableSet_69", "target_pin": "bIsPlayingTransitionBack",
    })
    log.info("  xlink: OR3.ReturnValue -X- Set_69.bIsPlayingTransitionBack")
    # connect OR2 -> Set
    call("connect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "source_node": "K2Node_CallFunction_35", "source_pin": "ReturnValue",
        "target_node": "K2Node_VariableSet_69", "target_pin": "bIsPlayingTransitionBack",
    })
    log.info("  link: OR2.ReturnValue -> Set_69.bIsPlayingTransitionBack")


def step_b_remove_nodes() -> None:
    log.info("\n=== Step B: remove 4-pattern nodes ===")
    graph = "UpdateVariables"
    for nid in NODES_TO_REMOVE:
        call("remove_node", {
            "asset_path": ASSET, "graph_name": graph, "node_id": nid,
        })
        log.info("  - removed %s", nid)


def step_c_compile_save() -> None:
    log.info("\n=== Step C: compile + save ===")
    out_c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("  compile: %s", out_c)
    out_s = call("save_asset", {"asset_path": ASSET})
    log.info("  save:    %s", out_s)


def main() -> None:
    step_a_rewire()
    step_b_remove_nodes()
    step_c_compile_save()
    log.info("\n[ALL DONE]")


if __name__ == "__main__":
    main()
