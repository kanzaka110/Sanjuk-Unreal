#!/usr/bin/env python3
"""[SM_TRACE] 채널 신규 — Phase 5.

설계:
  AnimRewindRecorderEmit 그래프 안에 [SM_TRACE] 별도 PrintText 추가.
  매 틱 호출되며, 직전 state와 비교해 status="CHANGED" or "SAME" 마킹.

추가 노드:
  1. CallFunction GetCurrentStateName(MachineName="MoveStateMachine")
  2. VariableGet __SmTracePrevState
  3. CallFunction EqualEqual_NameName
  4. SelectString (bool ? "CHANGED" : "SAME")  ←  반전: cur==prev 이면 SAME
  5. Concat 체인: [SM_TRACE] sm=<state> status=<S/C>
  6. Conv_StringToText → PrintText (level=Log)
  7. VariableSet __SmTracePrevState = current

변수 1개 신규: __SmTracePrevState (Name, default=NAME_None)
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("sm_trace")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "AnimRewindRecorderEmit"
SM_NAME = "MoveStateMachine"
PREV_VAR = "__SmTracePrevState"

_msg_id = [17000]


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


def connect(src: str, src_pin: str, tgt: str, tgt_pin: str, allow_error: bool = False) -> None:
    call("connect_pins", {"asset_path": ASSET, "graph_name": GRAPH,
                          "source_node": src, "source_pin": src_pin,
                          "target_node": tgt, "target_pin": tgt_pin}, allow_error=allow_error)


def set_pin(nid: str, pin: str, value: str) -> None:
    call("set_pin_default", {"asset_path": ASSET, "graph_name": GRAPH,
                             "node_id": nid, "pin_name": pin, "value": value})


def main() -> None:
    log.info("\n=== 1) Add BP variable %s (Name) ===", PREV_VAR)
    r = call("add_variable", {
        "asset_path": ASSET,
        "name": PREV_VAR,
        "type": "Name",
        "default_value": "None",
    }, allow_error=True)
    log.info("  add_variable: %s", r)

    log.info("\n=== 2) Find existing PrintText exec tail in AnimRewindRecorderEmit ===")
    # 기존 PrintText = K2Node_CallFunction_1 의 then(exec out) 노드를 찾아 그 뒤에 chain 연결
    pt = call("get_node_details", {"asset_path": ASSET, "graph_name": GRAPH,
                                   "node_id": "K2Node_CallFunction_1"})
    log.info("  PrintText pins: %s", [p["name"] for p in pt.get("pins", [])])

    log.info("\n=== 3) Add SM_TRACE chain ===")
    Y = 2200
    # 3-1. GetCurrentStateName(MachineIndex=0)  ← SM 1개, index 0
    gcsn = add_node("CallFunction", [200, Y],
                    function_name="GetCurrentStateName")
    set_pin(gcsn, "MachineIndex", "0")

    # 3-2. VariableGet __SmTracePrevState
    vget_prev = add_node("VariableGet", [200, Y + 200], variable_name=PREV_VAR)

    # 3-3. NotEqual_NameName(A, B) → bool (true = CHANGED, false = SAME)
    eq = add_node("CallFunction", [500, Y + 100],
                  function_name="NotEqual_NameName", target_class="KismetMathLibrary")
    connect(gcsn, "ReturnValue", eq, "A")
    connect(vget_prev, PREV_VAR, eq, "B")

    # 3-4. Conv_BoolToString — true → "true" (=CHANGED), false → "false" (=SAME)
    sel = add_node("CallFunction", [700, Y + 100],
                   function_name="Conv_BoolToString", target_class="KismetStringLibrary")
    connect(eq, "ReturnValue", sel, "InBool")

    # 3-5. Convert current state Name → String
    name2str = add_node("CallFunction", [500, Y - 100],
                        function_name="Conv_NameToString", target_class="KismetStringLibrary")
    connect(gcsn, "ReturnValue", name2str, "InName")

    # 3-6. Concat chain — "[SM_TRACE] sm=" + state + " status=" + sel
    cc1 = add_node("CallFunction", [800, Y - 100],
                   function_name="Concat_StrStr", target_class="KismetStringLibrary")
    set_pin(cc1, "A", "sm=")
    connect(name2str, "ReturnValue", cc1, "B")

    cc2 = add_node("CallFunction", [1000, Y - 100],
                   function_name="Concat_StrStr", target_class="KismetStringLibrary")
    connect(cc1, "ReturnValue", cc2, "A")
    set_pin(cc2, "B", " status=")

    cc3 = add_node("CallFunction", [1200, Y - 100],
                   function_name="Concat_StrStr", target_class="KismetStringLibrary")
    connect(cc2, "ReturnValue", cc3, "A")
    connect(sel, "ReturnValue", cc3, "B")

    # 3-7. Conv_StringToText
    s2t = add_node("CallFunction", [1400, Y - 100],
                   function_name="Conv_StringToText", target_class="KismetTextLibrary")
    connect(cc3, "ReturnValue", s2t, "InString")

    # 3-8. PrintText
    ptxt = add_node("CallFunction", [1700, Y - 100],
                    function_name="PrintText", target_class="KismetSystemLibrary")
    connect(s2t, "ReturnValue", ptxt, "InText")
    # PrintText pin defaults — Key prefix
    set_pin(ptxt, "bPrintToScreen", "false")
    set_pin(ptxt, "bPrintToLog", "true")
    set_pin(ptxt, "Key", "[SM_TRACE]")

    # 3-9. SetVariable __SmTracePrevState = currentState
    vset = add_node("VariableSet", [1900, Y + 100], variable_name=PREV_VAR)
    connect(gcsn, "ReturnValue", vset, PREV_VAR)

    # 3-10. Exec chain — 기존 PrintText(CF_1) → ptxt → vset
    # 기존 PrintText "then" pin name = "then"
    connect("K2Node_CallFunction_1", "then", ptxt, "execute", allow_error=True)
    connect(ptxt, "then", vset, "execute")

    log.info("\n=== 4) compile + save ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("  compile: %s", c)
    s = call("save_asset", {"asset_path": ASSET}, allow_error=True)
    log.info("  save: %s", s)


if __name__ == "__main__":
    main()
