#!/usr/bin/env python3
"""ANIM_REC +Chooser 6필드 — Phase 3++ Chooser info.

전제: __LastChooserOut (instance var, struct:SBStateMachineChooserOut) 가
SetStateMachineBlendStackAnim 함수에서 매 state 진입 시 set 됨 (이미 작업 완료).

ANIM_REC chain 끝 (CF_75 hed value 뒤) 에 6필드 sub-chain 삽입:
    ch_tag (Tag[0] Name → String)
    ch_bp  (BlendProfile Name → String)
    ch_mm  (UseMotionMatching bool)
    ch_mmcl (MotionMatchingCostLimit double)
    ch_bt  (BlendTime double)
    ch_st  (StartTime double)

위치: Motion 그룹 뒤, CF_25(StringToText) 앞에 새 chain 삽입.
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("chooser_fields")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "AnimRewindRecorderEmit"

_msg_id = [22000]


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


def add_node(node_type: str, position: list[int], **kw: Any) -> str:
    out = call("add_node", {"asset_path": ASSET, "graph_name": GRAPH,
                            "node_type": node_type, "position": position, **kw})
    nid = out["id"] if isinstance(out, dict) else out
    label = kw.get("function_name") or kw.get("variable_name") or node_type
    log.info("  + %-30s -> %s", label, nid)
    return nid


def connect(src, src_pin, tgt, tgt_pin, allow_error=False):
    call("connect_pins", {"asset_path": ASSET, "graph_name": GRAPH,
                          "source_node": src, "source_pin": src_pin,
                          "target_node": tgt, "target_pin": tgt_pin}, allow_error=allow_error)


def set_pin(nid, pin, value):
    call("set_pin_default", {"asset_path": ASSET, "graph_name": GRAPH,
                             "node_id": nid, "pin_name": pin, "value": value})


def add_concat_pair(prev_node: str, prev_pin: str, literal: str, value_src: str, value_pin: str,
                    y: int, x: int) -> tuple[str, str]:
    """prev → Concat1(prev+lit) → Concat2(c1+value) → return (c2, "ReturnValue")"""
    c1 = add_node("CallFunction", [x, y - 50],
                  function_name="Concat_StrStr", target_class="KismetStringLibrary")
    connect(prev_node, prev_pin, c1, "A")
    set_pin(c1, "B", literal)
    c2 = add_node("CallFunction", [x + 200, y],
                  function_name="Concat_StrStr", target_class="KismetStringLibrary")
    connect(c1, "ReturnValue", c2, "A")
    connect(value_src, value_pin, c2, "B")
    return c2, "ReturnValue"


def main():
    log.info("\n=== Step 3: Chooser 6필드 sub-chain ===")

    # 1) Get __LastChooserOut + BreakStruct
    log.info("\n--- 1) Get + BreakStruct ---")
    Y = 700
    X0 = 12000
    vget = add_node("VariableGet", [X0, Y + 400], variable_name="__LastChooserOut")
    brk = add_node("BreakStruct", [X0 + 200, Y + 400],
                   struct_type="SBStateMachineChooserOut")
    connect(vget, "__LastChooserOut", brk, "SBStateMachineChooserOut")

    # 2) 각 필드 Conv 노드
    log.info("\n--- 2) Conv 노드 ---")
    # Tag[0] — array<Name> 의 첫 element 만
    arr_get = add_node("CallFunction", [X0 + 400, Y + 300],
                       function_name="Array_Get", target_class="KismetArrayLibrary")
    # Tag array source pin 이름 = "Tag_10_..." (struct 멤버명 + GUID). 우선 추측 후 fail 시 다른 pin 이름 시도
    # Break struct output pin 이름은 "Tag_..." prefix. 전체 이름이 어떻게 되는지 확인
    # 일단 일반적 패턴 — set_pin Index=0
    set_pin(arr_get, "Index", "0")

    name_to_str_tag = add_node("CallFunction", [X0 + 600, Y + 300],
                               function_name="Conv_NameToString", target_class="KismetStringLibrary")
    connect(arr_get, "Item", name_to_str_tag, "InName")

    name_to_str_bp = add_node("CallFunction", [X0 + 400, Y + 400],
                              function_name="Conv_NameToString", target_class="KismetStringLibrary")
    bool_to_str = add_node("CallFunction", [X0 + 400, Y + 450],
                           function_name="Conv_BoolToString", target_class="KismetStringLibrary")
    d2s_mmcl = add_node("CallFunction", [X0 + 400, Y + 500],
                        function_name="Conv_DoubleToString", target_class="KismetStringLibrary")
    d2s_bt = add_node("CallFunction", [X0 + 400, Y + 550],
                      function_name="Conv_DoubleToString", target_class="KismetStringLibrary")
    d2s_st = add_node("CallFunction", [X0 + 400, Y + 600],
                      function_name="Conv_DoubleToString", target_class="KismetStringLibrary")

    # 3) BreakStruct output pin 이름은 GUID suffix 포함 → 정확한 이름 동적 확보 필요
    # 우선 get_node_details 로 pin 이름 알아내기
    d = call("get_node_details", {"asset_path": ASSET, "graph_name": GRAPH, "node_id": brk})
    pin_map = {}
    for p in d.get("pins", []):
        if p.get("direction") == "output":
            name = p["name"]
            # "Tag_10_..." → "Tag"
            short = name.split("_")[0]
            pin_map[short] = name
    log.info("\n  Break struct pin map: %s", pin_map)

    # BreakStruct 출력 → Array_Get / Conv 입력
    if "Tag" in pin_map:
        connect(brk, pin_map["Tag"], arr_get, "TargetArray")
    if "BlendProfile" in pin_map:
        connect(brk, pin_map["BlendProfile"], name_to_str_bp, "InName")
    if "UseMotionMatching" in pin_map:
        connect(brk, pin_map["UseMotionMatching"], bool_to_str, "InBool")
    if "MotionMatchingCostLimit" in pin_map:
        connect(brk, pin_map["MotionMatchingCostLimit"], d2s_mmcl, "InDouble")
    if "BlendTime" in pin_map:
        connect(brk, pin_map["BlendTime"], d2s_bt, "InDouble")
    if "StartTime" in pin_map:
        connect(brk, pin_map["StartTime"], d2s_st, "InDouble")

    # 4) Chain 끝 (CF_75) 에서 새 chain 으로 연결
    # 기존: CF_75.ReturnValue → CF_25.InString
    log.info("\n--- 4) Chain 끝 wire 재배치 + Concat chain ---")
    call("disconnect_pins", {"asset_path": ASSET, "graph_name": GRAPH,
        "node_id": "K2Node_CallFunction_75", "pin_name": "ReturnValue",
        "target_node": "K2Node_CallFunction_25", "target_pin": "InString"}, allow_error=True)

    # Chooser sub-chain: ch_tag → ch_bp → ch_mm → ch_mmcl → ch_bt → ch_st
    fields = [
        (' "ch_tag"=',  name_to_str_tag),
        (' "ch_bp"=',   name_to_str_bp),
        (' "ch_mm"=',   bool_to_str),
        (' "ch_mmcl"=', d2s_mmcl),
        (' "ch_bt"=',   d2s_bt),
        (' "ch_st"=',   d2s_st),
    ]

    tail_node = "K2Node_CallFunction_75"
    tail_pin = "ReturnValue"
    x_pos = X0 + 1000
    for i, (literal, value_src) in enumerate(fields):
        log.info("\n  field %d: %s", i + 1, literal)
        tail_node, tail_pin = add_concat_pair(
            tail_node, tail_pin, literal, value_src, "ReturnValue",
            y=Y + i * 100, x=x_pos + i * 400,
        )

    # 최종 → CF_25.InString
    connect(tail_node, tail_pin, "K2Node_CallFunction_25", "InString")
    log.info("\n  Final wire: %s → CF_25.InString", tail_node)

    log.info("\n=== compile ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: success=%s errors=%s warnings=%s",
             c.get("success"), c.get("error_count"), c.get("warning_count"))
    if c.get("errors"):
        for e in c["errors"][:5]: log.error("  ! %s", e)


if __name__ == "__main__":
    main()
