#!/usr/bin/env python3
"""ANIM_REC에 sm=<state> 필드 1개 추가 (4 노드만) — 옵션 X.

SM_TRACE 별도 채널 시도가 SB2 crash 유발 → 최소 침습 접근.
저장은 사용자 Ctrl+S — script 에서 save_asset 호출 안 함.

Chain:
  GetCurrentStateName(MachineIndex=0) → Name
  Conv_NameToString                    → String
  Concat(CF_100.ReturnValue, ' "sm"=') → c1
  Concat(c1, NameToString.ReturnValue) → c2
  c2 → CF_25.InString (기존 wire 끊고)
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("anim_rec_sm")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "AnimRewindRecorderEmit"

_msg_id = [18000]


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
        if allow_error:
            return None
        log.error("[ERR] %s -> %s", action, str(data)[:400])
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
    log.info("  + %-25s -> %s", label, nid)
    return nid


def connect(src: str, src_pin: str, tgt: str, tgt_pin: str, allow_error: bool = False) -> None:
    call("connect_pins", {"asset_path": ASSET, "graph_name": GRAPH,
                          "source_node": src, "source_pin": src_pin,
                          "target_node": tgt, "target_pin": tgt_pin}, allow_error=allow_error)


def set_pin(nid: str, pin: str, value: str) -> None:
    call("set_pin_default", {"asset_path": ASSET, "graph_name": GRAPH,
                             "node_id": nid, "pin_name": pin, "value": value})


def main() -> None:
    log.info("\n=== sm 필드 1개 추가 (MachineIndex=0) ===")

    Y = 500
    gcsn = add_node("CallFunction", [8400, Y + 200],
                    function_name="GetCurrentStateName")
    set_pin(gcsn, "MachineIndex", "0")

    n2s = add_node("CallFunction", [8600, Y + 200],
                   function_name="Conv_NameToString", target_class="KismetStringLibrary")
    connect(gcsn, "ReturnValue", n2s, "InName")

    cc1 = add_node("CallFunction", [8600, Y],
                   function_name="Concat_StrStr", target_class="KismetStringLibrary")
    connect("K2Node_CallFunction_100", "ReturnValue", cc1, "A")
    set_pin(cc1, "B", ' "sm"=')

    cc2 = add_node("CallFunction", [8800, Y + 100],
                   function_name="Concat_StrStr", target_class="KismetStringLibrary")
    connect(cc1, "ReturnValue", cc2, "A")
    connect(n2s, "ReturnValue", cc2, "B")

    # CF_100 -> CF_25 기존 wire 끊기
    call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": "K2Node_CallFunction_100", "pin_name": "ReturnValue",
        "target_node": "K2Node_CallFunction_25", "target_pin": "InString",
    }, allow_error=True)
    # cc2 -> CF_25 새 wire
    connect(cc2, "ReturnValue", "K2Node_CallFunction_25", "InString")

    log.info("\n=== compile (save 생략 — Ctrl+S 수동) ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: success=%s errors=%s warnings=%s",
             c.get("success"), c.get("error_count"), c.get("warning_count"))
    log.info("\n>>> SB2 에디터에서 PC_01_ABP 탭 활성화 후 Ctrl+S 로 저장해주세요.")


if __name__ == "__main__":
    main()
