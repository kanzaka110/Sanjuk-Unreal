#!/usr/bin/env python3
"""STEP 2: Wire 65 sources to the new FT (K2Node_FormatText_2) and set vac default.

Wire map mirrors the Inspector handoff exactly.
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from dataclasses import dataclass

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"
NEW_FT = "K2Node_FormatText_2"

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Wire:
    dest_pin: str
    src_node: str
    src_pin: str


# All wires per Inspector handoff (vac intentionally omitted -> default "-1").
WIRES: tuple[Wire, ...] = (
    Wire("f",      "K2Node_CallFunction_3",                "ReturnValue"),
    Wire("sp",     "K2Node_VariableGet_2",                 "Speed2D"),
    Wire("as",     "K2Node_CallFunction_7",                "ReturnValue"),
    Wire("ms",     "K2Node_CallFunction_8",                "ReturnValue"),
    Wire("ist",    "K2Node_VariableGet_5",                 "bIsStart"),
    Wire("he",     "K2Node_VariableGet_6",                 "HasEvade"),
    Wire("vlen",   "K2Node_CallFunction_13",               "ReturnValue"),
    Wire("pwm",    "K2Node_CallFunction_14",               "ReturnValue"),
    Wire("il",     "K2Node_VariableGet_10",                "IsLockOn"),
    Wire("isf",    "K2Node_VariableGet_32",                "IsStrafe"),
    Wire("isc",    "K2Node_VariableGet_33",                "TrjIsCircling"),
    Wire("csh",    "K2Node_VariableGet_34",                "CircleStrafeHysteresis"),
    Wire("trd",    "K2Node_VariableGet_14",                "TargetRotationDelta"),
    Wire("ib",     "K2Node_VariableGet_25",                "IsBattle"),
    Wire("rmf",    "K2Node_VariableGet_16",                "RuleMoveFlag"),
    Wire("fik",    "K2Node_VariableGet_35",                "FootIKWeight"),
    Wire("fca",    "K2Node_VariableGet_18",                "FootClampAlpha"),
    Wire("ow",     "K2Node_VariableGet_19",                "OverlayWeight"),
    Wire("ig",     "K2Node_VariableGet_36",                "IsGuarding"),
    Wire("sc",     "K2Node_VariableGet_7",                 "SearchCost"),
    Wire("clip",   "K2Node_VariableGet_26",                "CurrAnimTag"),
    Wire("seq",    "K2Node_VariableGet_37",                "CurrentSequenceName"),
    Wire("bim",    "K2Node_VariableGet_39",                "bIsMoving"),
    Wire("bpim",   "K2Node_VariableGet_15",                "bPrevIsMoving"),
    Wire("ms_l",   "K2Node_CallFunction_0",                "ReturnValue"),
    Wire("ms_p",   "K2Node_CallFunction_1",                "ReturnValue"),
    Wire("mm",     "K2Node_GetEnumeratorNameAsString_6",   "ReturnValue"),
    Wire("ops",    "K2Node_GetEnumeratorNameAsString_3",   "ReturnValue"),
    Wire("fbsw",   "K2Node_VariableGet_28",                "FullBodySlotWeight"),
    Wire("fa",     "K2Node_VariableGet_29",                "IsFullBodySlotActive"),
    Wire("rop",    "K2Node_VariableGet_59",                "ResetOffsetPulse"),
    Wire("sba",    "K2Node_VariableGet_20",                "IsSequenceBindingActor"),
    Wire("ibk",    "K2Node_VariableGet_17",                "IsBlocked"),
    Wire("we",     "K2Node_VariableGet_43",                "WriggleEnd"),
    Wire("iw",     "K2Node_VariableGet_38",                "InWriggle"),
    Wire("jes",    "K2Node_VariableGet_11",                "JustExitedSprint"),
    Wire("htt",    "K2Node_VariableGet_56",                "HoldTimeThreshold"),
    Wire("stip",   "K2Node_CallFunction_9",                "ReturnValue"),
    Wire("ip",     "K2Node_CallFunction_52",               "ReturnValue"),
    Wire("lm",     "K2Node_CallFunction_118",              "ReturnValue"),
    Wire("dal",    "K2Node_CallFunction_121",              "ReturnValue"),
    Wire("sset",   "K2Node_VariableGet_41",                "bIsSprintEndTransition"),
    Wire("phase",  "K2Node_CallFunction_46",               "ReturnValue"),
    Wire("eow",    "K2Node_CallFunction_48",               "ReturnValue"),
    Wire("eprw",   "K2Node_CallFunction_18",               "ReturnValue"),
    Wire("fv",     "K2Node_CallFunction_119",              "ReturnValue"),
    Wire("acc",    "K2Node_CallFunction_120",              "ReturnValue"),
    Wire("isafb",  "K2Node_CallFunction_40",               "ReturnValue"),
    Wire("isaub",  "K2Node_CallFunction_16",               "ReturnValue"),
    Wire("sswseq", "K2Node_CallFunction_44",               "ReturnValue"),
    Wire("wt",     "K2Node_GetEnumeratorNameAsString_7",   "ReturnValue"),
    Wire("cvco",   "K2Node_CallFunction_11",               "ReturnValue"),
    Wire("ubsw",   "K2Node_VariableGet_30",                "UpperBodyBlendWeight"),
    Wire("rva",    "K2Node_GetEnumeratorNameAsString_5",   "ReturnValue"),
    Wire("rvmci",  "K2Node_CallFunction_43",               "ReturnValue_MatchedConfigIndex"),
    Wire("ifl",    "K2Node_CallFunction_43",               "ReturnValue_bIsFalling"),
    Wire("rj",     "K2Node_CallFunction_43",               "ReturnValue_bRequiresJump"),
    Wire("dog",    "K2Node_CallFunction_43",               "ReturnValue_DiffOnGround"),
    Wire("hd",     "K2Node_CallFunction_43",               "ReturnValue_HeightDiff"),
    Wire("pav_z",  "K2Node_VariableGet_46",                "TrjPastAngularVelocity_Z"),
    Wire("cav_z",  "K2Node_VariableGet_13",                "TrjCurrentAngularVelocity_Z"),
    Wire("sms",    "K2Node_CallFunction_6",                "ReturnValue"),
    # "vac" intentionally skipped — DEFAULT "-1"
    Wire("na",     "K2Node_VariableGet_42",                "NullAnim"),
    Wire("rrt",    "K2Node_VariableGet_44",                "RunRetransit"),
    Wire("rrr",    "K2Node_VariableGet_45",                "RetransitReason"),
)


def rpc(action: str, params: dict) -> dict | None:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "blueprint_query",
            "arguments": {"action": action, "params": params},
        },
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    if data.get("result", {}).get("isError"):
        log.error("!! %s ERROR: %s", action, data["result"]["content"][0]["text"][:800])
        return None
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def connect(src_node: str, src_pin: str, dest_node: str, dest_pin: str) -> bool:
    r = rpc(
        "connect_pins",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "source_node": src_node,
            "source_pin": src_pin,
            "target_node": dest_node,
            "target_pin": dest_pin,
        },
    )
    return r is not None


def main() -> None:
    failures: list[tuple[Wire, str]] = []
    for i, w in enumerate(WIRES, 1):
        ok = connect(w.src_node, w.src_pin, NEW_FT, w.dest_pin)
        status = "OK" if ok else "FAIL"
        log.info("[%2d/65] %-7s -> %-40s.%-30s [%s]", i, w.dest_pin, w.src_node, w.src_pin, status)
        if not ok:
            failures.append((w, "connect failed"))

    log.info("=== set vac default to '-1' ===")
    r = rpc(
        "set_pin_default",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_id": NEW_FT,
            "pin_name": "vac",
            "value": "-1",
        },
    )
    log.info("set_pin_default(vac, -1) -> %s", r)

    if failures:
        log.error("=== FAILURES (%d) ===", len(failures))
        for w, err in failures:
            log.error("  %s -> %s.%s : %s", w.dest_pin, w.src_node, w.src_pin, err)
        sys.exit(2)
    log.info("All 65 wires connected successfully.")


if __name__ == "__main__":
    main()
