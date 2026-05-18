#!/usr/bin/env python3
"""ANIM_REC fpa 필드 추가 — Concat_StrStr 패턴 (FormatText pin 추가 한계 우회).

Phase 3a — 1필드 (fpa = FootPlacementAlpha) 먼저 검증.

설계:
    FT_11.Result (text) → Conv_TextToString → s1
    " \"fpa\"=" literal → s2
    Get FootPlacementAlpha → Conv_DoubleToString → s3
    Concat_StrStr(s1, s2) → c1
    Concat_StrStr(c1, s3) → c2
    Conv_StringToText(c2) → t
    PrintText.InText ← t  (기존 FT_11.Result wire 교체)
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("anim_rec_fpa")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "AnimRewindRecorderEmit"

_msg_id = [15000]


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
    log.info("\n=== Phase 3a: fpa 1필드 추가 ===")
    # 1) Conv_TextToString — FT_11.Result → string
    t2s = add_node("CallFunction", [7000, 50],
                   function_name="Conv_TextToString", target_class="KismetTextLibrary")

    # 2) Get FootPlacementAlpha
    get_fpa = add_node("VariableGet", [7000, 200], variable_name="FootPlacementAlpha")

    # 3) Conv_DoubleToString — float → string
    d2s = add_node("CallFunction", [7200, 200],
                   function_name="Conv_DoubleToString", target_class="KismetStringLibrary")

    # 4) Concat_StrStr — A: t2s result, B: " \"fpa\"="
    concat1 = add_node("CallFunction", [7200, 80],
                       function_name="Concat_StrStr", target_class="KismetStringLibrary")

    # 5) Concat_StrStr — A: concat1, B: d2s (= fpa value)
    concat2 = add_node("CallFunction", [7400, 100],
                       function_name="Concat_StrStr", target_class="KismetStringLibrary")

    # 6) Conv_StringToText
    s2t = add_node("CallFunction", [7600, 100],
                   function_name="Conv_StringToText", target_class="KismetTextLibrary")

    log.info("\n=== Wiring ===")
    # FT_11.Result → t2s.InText
    connect("K2Node_FormatText_11", "Result", t2s, "InText")
    # t2s.ReturnValue → concat1.A
    connect(t2s, "ReturnValue", concat1, "A")
    # concat1.B = ' "fpa"='
    set_pin(concat1, "B", ' "fpa"=')
    # FootPlacementAlpha → d2s
    connect(get_fpa, "FootPlacementAlpha", d2s, "InDouble")
    # concat1.ReturnValue → concat2.A
    connect(concat1, "ReturnValue", concat2, "A")
    # d2s.ReturnValue → concat2.B
    connect(d2s, "ReturnValue", concat2, "B")
    # concat2.ReturnValue → s2t.InString
    connect(concat2, "ReturnValue", s2t, "InString")

    # PrintText 의 InText: FT_11.Result -X- + s2t.ReturnValue 새로
    call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": "K2Node_FormatText_11", "pin_name": "Result",
        "target_node": "K2Node_CallFunction_1", "target_pin": "InText",
    }, allow_error=True)
    connect(s2t, "ReturnValue", "K2Node_CallFunction_1", "InText")

    log.info("\n=== compile + save ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: %s", c)
    s = call("save_asset", {"asset_path": ASSET}, allow_error=True)
    log.info("save: %s", s)


if __name__ == "__main__":
    main()
