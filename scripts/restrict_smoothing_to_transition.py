#!/usr/bin/env python3
"""
PC_01_ABP — wraparound smoothing 적용 범위를 transition 클립 재생 중으로 제한 (2026-05-15).

사용자 호소: "락온 상태에서 180도 커맨드를 넣으면 Turn이 아예 매칭이 안 되는 문제가 있어.
              Transition 에서만 smooth가 들어가야 할 것 같아."

원인: Adaptive Alpha smoothing 이 모든 Strafe 분기에 항시 적용 → 일반 회전 (Turn 매칭이
필요한 시점) 에도 trd가 천천히 따라감 → trajectory cost 부적절 → Turn 클립 매칭 X.

처방: 5/13 ① 게이트 패턴 (변수 bIsPlayingTransitionBack + Contains 3패턴 OR) 부활 + smoothing
출력을 게이트로 선택. 4번째 패턴 (Transition_ AND IsLockOn) 은 이전 부작용 알고 있으므로
처음부터 제외 — 3패턴만.

매칭 룰:
    bIsPlayingTransitionBack =
        Contains(CurrentSequenceName, "Sprint_to_Battle") OR
        Contains(CurrentSequenceName, "Sprint_to_LockOn") OR
        Contains(CurrentSequenceName, "Sprint_to_Jog")

UpdateTargetRotation Strafe 분기:
    if bIsPlayingTransitionBack:
        TargetRotationDelta = SmoothDelta (Adaptive Alpha 처방 결과)
    else:
        TargetRotationDelta = RawDelta (기존 동작 그대로, smoothing 0)

Phases:
    Phase 1: 변수 bIsPlayingTransitionBack (bool, Buffer)
    Phase 2: UpdateVariables — Get×2 (Seq + 기존 Get?) + Contains×3 + OR×2 + Set + exec
    Phase 3: UpdateTargetRotation — SelectFloat 게이트 + Not + Get (3노드)
    Phase 4: compile + save
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("restrict_smoothing")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
VAR_NAME = "bIsPlayingTransitionBack"
PATTERNS = ["Sprint_to_Battle", "Sprint_to_LockOn", "Sprint_to_Jog"]

_msg_id = [10000]


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


def add_node(graph: str, node_type: str, position: list[int], **kwargs: Any) -> str:
    out = call("add_node", {
        "asset_path": ASSET, "graph_name": graph, "node_type": node_type,
        "position": position, **kwargs,
    })
    nid = out["id"] if isinstance(out, dict) else out
    label = kwargs.get("function_name") or kwargs.get("variable_name") or node_type
    log.info("[+] %s %s -> %s", graph, label, nid)
    return nid


def connect(graph: str, src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    return call("connect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "source_node": src, "source_pin": src_pin,
        "target_node": tgt, "target_pin": tgt_pin,
    })


def disconnect(graph: str, src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    return call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "node_id": src, "pin_name": src_pin,
        "target_node": tgt, "target_pin": tgt_pin,
    })


def set_pin(graph: str, node_id: str, pin_name: str, value: str) -> Any:
    return call("set_pin_default", {
        "asset_path": ASSET, "graph_name": graph,
        "node_id": node_id, "pin_name": pin_name, "value": value,
    })


# Phase 1
def phase1_variable() -> None:
    log.info("\n=== Phase 1: variable ===")
    call("add_variable", {
        "asset_path": ASSET, "name": VAR_NAME, "type": "bool",
        "category": "Buffer", "default_value": "false",
        "instance_editable": False, "blueprint_read_only": False,
    })


# Phase 2
def phase2_update_variables() -> dict[str, str]:
    log.info("\n=== Phase 2: UpdateVariables matching chain ===")
    graph = "UpdateVariables"

    seq_get = add_node(graph, "VariableGet", [4800, 2700], variable_name="CurrentSequenceName")
    contains_ids = []
    for i, pat in enumerate(PATTERNS):
        cid = add_node(graph, "CallFunction", [5100, 2600 + i * 80],
                       function_name="Contains", target_class="KismetStringLibrary")
        set_pin(graph, cid, "Substring", pat)
        connect(graph, seq_get, "CurrentSequenceName", cid, "SearchIn")
        contains_ids.append(cid)

    or1 = add_node(graph, "CallFunction", [5400, 2630],
                   function_name="BooleanOR", target_class="KismetMathLibrary")
    connect(graph, contains_ids[0], "ReturnValue", or1, "A")
    connect(graph, contains_ids[1], "ReturnValue", or1, "B")

    or2 = add_node(graph, "CallFunction", [5560, 2700],
                   function_name="BooleanOR", target_class="KismetMathLibrary")
    connect(graph, or1, "ReturnValue", or2, "A")
    connect(graph, contains_ids[2], "ReturnValue", or2, "B")

    set_id = add_node(graph, "VariableSet", [5800, 2700], variable_name=VAR_NAME)
    connect(graph, or2, "ReturnValue", set_id, VAR_NAME)

    # exec: ExecutionSeq_3.then_12 → Set.execute → Knot_1.InputPin (5/13 패턴 그대로)
    disconnect(graph, "K2Node_ExecutionSequence_3", "then_12",
               "K2Node_Knot_1", "InputPin")
    connect(graph, "K2Node_ExecutionSequence_3", "then_12", set_id, "execute")
    connect(graph, set_id, "then", "K2Node_Knot_1", "InputPin")

    log.info("[OK] Phase 2 set_id=%s", set_id)
    return {"set": set_id, "or2": or2}


# Phase 3
def phase3_target_rotation_gate() -> dict[str, str]:
    log.info("\n=== Phase 3: UpdateTargetRotation output gate ===")
    graph = "UpdateTargetRotation"

    get_var = add_node(graph, "VariableGet", [2880, 580], variable_name=VAR_NAME)
    not_node = add_node(graph, "CallFunction", [3020, 600],
                        function_name="Not_PreBool", target_class="KismetMathLibrary")
    sel_node = add_node(graph, "CallFunction", [3160, 680],
                        function_name="SelectFloat", target_class="KismetMathLibrary")

    # 기존 wiring 끊기: CF_14 → Set_3.TargetRotationDelta, CF_14 → SetPrev_0.PrevTargetRotationDelta
    disconnect(graph, "K2Node_CallFunction_14", "ReturnValue",
               "K2Node_VariableSet_3", "TargetRotationDelta")
    disconnect(graph, "K2Node_CallFunction_14", "ReturnValue",
               "K2Node_VariableSet_0", "PrevTargetRotationDelta")

    # SelectFloat data wiring
    # A = Raw (CF_4.ReturnValue) — bIsPlayingTransitionBack=false 시 선택
    connect(graph, "K2Node_CallFunction_4", "ReturnValue", sel_node, "A")
    # B = Smooth (CF_14.ReturnValue) — bIsPlayingTransitionBack=true 시 선택
    connect(graph, "K2Node_CallFunction_14", "ReturnValue", sel_node, "B")
    # bPickA = NOT(bIsPlayingTransitionBack)
    connect(graph, get_var, VAR_NAME, not_node, "A")
    connect(graph, not_node, "ReturnValue", sel_node, "bPickA")

    # 출력
    connect(graph, sel_node, "ReturnValue", "K2Node_VariableSet_3", "TargetRotationDelta")
    connect(graph, sel_node, "ReturnValue", "K2Node_VariableSet_0", "PrevTargetRotationDelta")

    log.info("[OK] Phase 3 sel=%s", sel_node)
    return {"sel": sel_node, "not": not_node, "get_var": get_var}


# Phase 4
def phase4_compile_save() -> None:
    log.info("\n=== Phase 4: compile + save ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: %s", c)
    s = call("save_asset", {"asset_path": ASSET}, allow_error=True)
    log.info("save:    %s", s)


def main() -> None:
    phase1_variable()
    p2 = phase2_update_variables()
    p3 = phase3_target_rotation_gate()
    phase4_compile_save()
    log.info("\n[DONE] p2=%s p3=%s", p2, p3)


if __name__ == "__main__":
    main()
