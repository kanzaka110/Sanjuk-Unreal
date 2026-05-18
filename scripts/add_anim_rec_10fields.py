#!/usr/bin/env python3
"""ANIM_REC unmapped 10필드 일괄 추가 — Concat_StrStr 패턴.

Phase 3+ — ★★★ 4 + ★★ Sprint 3 + ★★ Prev 3.

기존 chain 끝:  CF_40 (Concat) → CF_25 (Conv_StringToText) → PrintText.InText
삽입 위치:      CF_40 뒤에서 새 필드들 (10개) chain → CF_25 앞으로 다시 연결.

각 필드 패턴 (예: ptrd, PrevTargetRotationDelta, double):
    Get PrevTargetRotationDelta → Conv_DoubleToString → s
    PrevChainTail → Concat(A=tail, B=' "ptrd"=') → c1
    c1 → Concat(A=c1, B=s) → c2  (= 새 chain tail)
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("anim_rec_10")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "AnimRewindRecorderEmit"

_msg_id = [16000]


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
            log.warning("[WARN] %s err=%s", action, str(data)[:200])
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
    log.info("  + %-30s -> %s", label, nid)
    return nid


def connect(src: str, src_pin: str, tgt: str, tgt_pin: str) -> None:
    call("connect_pins", {"asset_path": ASSET, "graph_name": GRAPH,
                          "source_node": src, "source_pin": src_pin,
                          "target_node": tgt, "target_pin": tgt_pin})


def set_pin(nid: str, pin: str, value: str) -> None:
    call("set_pin_default", {"asset_path": ASSET, "graph_name": GRAPH,
                             "node_id": nid, "pin_name": pin, "value": value})


# (var_name, abbrev, conv_func, conv_in_pin, conv_out_pin, str_lib)
# str_lib: "KismetStringLibrary" or "KismetTextLibrary"
FIELDS = [
    ("PrevTargetRotationDelta",    "ptrd", "Conv_DoubleToString", "InDouble", "ReturnValue", "KismetStringLibrary"),
    ("TrjTurnAngle",               "tta",  "Conv_DoubleToString", "InDouble", "ReturnValue", "KismetStringLibrary"),
    ("HasEvadeDuration",           "hed",  "Conv_DoubleToString", "InDouble", "ReturnValue", "KismetStringLibrary"),
    ("SmoothedVelocity",           "sv",   "Conv_VectorToString", "InVec",    "ReturnValue", "KismetStringLibrary"),
    ("bIsSprintEndTransition",     "ise",  "Conv_BoolToString",   "InBool",   "ReturnValue", "KismetStringLibrary"),
    ("SprintEndTransitionRemain",  "setr", "Conv_DoubleToString", "InDouble", "ReturnValue", "KismetStringLibrary"),
    ("SprintEndTransitionDuration","seta", "Conv_DoubleToString", "InDouble", "ReturnValue", "KismetStringLibrary"),
    ("PrevAnimStance",             "pas",  "Conv_ByteToString",   "InByte",   "ReturnValue", "KismetStringLibrary"),
    ("PrevMovementState",          "pms2", "Conv_ByteToString",   "InByte",   "ReturnValue", "KismetStringLibrary"),
    ("PrevPendingWalkMode",        "ppwm", "Conv_ByteToString",   "InByte",   "ReturnValue", "KismetStringLibrary"),
]


def main() -> None:
    log.info("\n=== ANIM_REC +10 필드 (★★★ 4 + Sprint 3 + Prev 3) ===")

    # 기존 chain tail = K2Node_CallFunction_40 (Concat for ps_db value)
    # 우리는 CF_40.ReturnValue 에서 시작해서 새 chain 으로 이어간 뒤
    # 마지막을 K2Node_CallFunction_25 (Conv_StringToText) 의 InString 으로 연결.

    # 먼저 CF_40 → CF_25 사이의 기존 wire 끊기 (있으면)
    call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": "K2Node_CallFunction_40", "pin_name": "ReturnValue",
        "target_node": "K2Node_CallFunction_25", "target_pin": "InString",
    }, allow_error=True)

    prev_tail_node = "K2Node_CallFunction_40"
    prev_tail_pin = "ReturnValue"
    y = 400

    for i, (var, abbr, conv, in_pin, out_pin, lib) in enumerate(FIELDS):
        log.info("\n--- [%d/10] %s (%s) ---", i + 1, abbr, var)
        x_base = 7800 + i * 600

        # Get variable
        vget = add_node("VariableGet", [x_base, y + 200], variable_name=var)
        # Conv → string
        conv_id = add_node("CallFunction", [x_base + 200, y + 200],
                           function_name=conv, target_class=lib)
        connect(vget, var, conv_id, in_pin)

        # Concat1 (prev_tail + literal)
        cc1 = add_node("CallFunction", [x_base + 200, y],
                       function_name="Concat_StrStr", target_class="KismetStringLibrary")
        connect(prev_tail_node, prev_tail_pin, cc1, "A")
        set_pin(cc1, "B", f' "{abbr}"=')

        # Concat2 (cc1 + conv value)
        cc2 = add_node("CallFunction", [x_base + 400, y + 100],
                       function_name="Concat_StrStr", target_class="KismetStringLibrary")
        connect(cc1, "ReturnValue", cc2, "A")
        connect(conv_id, out_pin, cc2, "B")

        prev_tail_node = cc2
        prev_tail_pin = "ReturnValue"

    # 최종 tail → CF_25.InString
    log.info("\n--- Final wire: %s.%s -> CF_25.InString ---", prev_tail_node, prev_tail_pin)
    connect(prev_tail_node, prev_tail_pin, "K2Node_CallFunction_25", "InString")

    log.info("\n=== compile + save ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: %s", c)
    s = call("save_asset", {"asset_path": ASSET}, allow_error=True)
    log.info("save: %s", s)


if __name__ == "__main__":
    main()
