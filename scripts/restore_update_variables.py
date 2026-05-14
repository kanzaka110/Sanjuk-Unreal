#!/usr/bin/env python3
"""Restore UpdateVariables graph in PC_01_ABP from 5/14 backup JSON.

Source:
  scripts/backup/UpdateVariables_post_sprint_start_20260514.json
    - 353 nodes (VariableGet 80, VariableSet 79, CallFunction 44, Comment 36,
      Knot 29, PromotableOperator 23, PropertyAccess 20, ...)

Strategy:
  1) Load backup JSON.
  2) (Optional) Clear existing UpdateVariables graph nodes.
  3) Pass 1: Create all nodes (build id_map[old_id] = new_id).
  4) Pass 2: Restore default_values via set_pin_default.
  5) Pass 3: Wire connections (parse "K2Node_X.pin_name" from connected_to).
  6) compile_blueprint + save_asset.

PropertyAccess limitations:
  - Backup JSON lacks the property path/binding metadata. Created as placeholder;
    user must manually re-bind. Names logged for follow-up.

Usage:
  py C:/Dev/Sanjuk-Unreal/scripts/restore_update_variables.py
  py C:/Dev/Sanjuk-Unreal/scripts/restore_update_variables.py --dry-run
  py C:/Dev/Sanjuk-Unreal/scripts/restore_update_variables.py --keep-existing   # don't clear graph first
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "UpdateVariables"
ENDPOINT = "http://localhost:9316/mcp"
BACKUP_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "backup",
    "UpdateVariables_post_sprint_start_20260514.json",
)

# Node classes that need special add_node parameters
VAR_CLASSES = {"K2Node_VariableGet", "K2Node_VariableSet"}
FUNC_CLASSES = {
    "K2Node_CallFunction",
    "K2Node_CallArrayFunction",
    "K2Node_CommutativeAssociativeBinaryOperator",
    "K2Node_PromotableOperator",
}
COMMENT_CLASS = "EdGraphNode_Comment"
# Classes generally created as-is (no extra params beyond class + position)
PLAIN_CLASSES = {
    "K2Node_Knot",
    "K2Node_IfThenElse",
    "K2Node_ExecutionSequence",
    "K2Node_EnumEquality",
    "K2Node_EnumInequality",
    "K2Node_Select",
    "K2Node_SwitchEnum",
    "K2Node_GetArrayItem",
}
# Classes we cannot fully restore (need manual binding)
LIMITED_CLASSES = {"K2Node_PropertyAccess", "K2Node_AnimNodeReference"}
# Classes we skip entirely (graph entry point is fixed)
SKIP_CLASSES = {"K2Node_FunctionEntry", "K2Node_FunctionResult"}


logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)
_msg_id = [0]


def rpc(action: str, params: dict, silent_error: bool = False) -> dict | str | None:
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
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        log.error("RPC %s failed: %s", action, exc)
        return None
    if data.get("result", {}).get("isError"):
        msg = data["result"]["content"][0]["text"]
        if not silent_error:
            log.error("!! %s ERROR: %s", action, msg[:300])
        return {"_error": msg}
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def load_backup() -> dict:
    with open(BACKUP_PATH, "r", encoding="utf-8") as f:
        outer = json.load(f)
    text = outer["result"]["content"][0]["text"]
    return json.loads(text)


def get_variable_name(n: dict) -> str | None:
    """K2Node_VariableGet 'Get Speed2D' -> 'Speed2D'. Or use first non-exec pin."""
    title = n.get("title", "")
    for prefix in ("Get ", "Set "):
        if title.startswith(prefix):
            return title[len(prefix):]
    # Fallback: first non-exec, non-Output_Get pin
    for p in n.get("pins", []):
        if p.get("type") != "exec" and p.get("name") not in ("Output_Get",):
            return p.get("name")
    return None


def add_node_for(n: dict, keep_id: bool = False) -> str | None:
    """Add one node based on backup spec. Returns new node_id or None."""
    cls = n.get("class", "")
    if cls in SKIP_CLASSES:
        log.info("  SKIP %s (%s)", n["id"], cls)
        return n["id"]  # use original id; FunctionEntry already exists

    pos = n.get("pos", [0, 0])
    params = {"asset_path": ASSET, "graph_name": GRAPH, "position": pos}

    if cls in VAR_CLASSES:
        vname = get_variable_name(n)
        if not vname:
            log.error("  FAIL %s — could not parse variable_name from title=%r", n["id"], n.get("title"))
            return None
        params["node_type"] = "VariableGet" if cls == "K2Node_VariableGet" else "VariableSet"
        params["variable_name"] = vname

    elif cls in FUNC_CLASSES:
        fn = n.get("function")
        fc = n.get("function_class")
        if not fn or not fc:
            log.error("  FAIL %s — missing function/function_class", n["id"])
            return None
        params["node_type"] = "CallFunction"
        params["function_name"] = fn
        params["target_class"] = fc

    elif cls == COMMENT_CLASS:
        params["node_type"] = "Comment"
        params["comment"] = n.get("comment", "")

    elif cls in PLAIN_CLASSES:
        # Use class short name as node_type — Monolith may accept it
        params["node_type"] = cls.replace("K2Node_", "")

    elif cls in LIMITED_CLASSES:
        log.warning("  LIMITED %s (%s) — created as placeholder, MANUAL BINDING NEEDED (title=%r)",
                    n["id"], cls, n.get("title", "")[:60])
        params["node_type"] = cls.replace("K2Node_", "").replace("EdGraphNode_", "")

    else:
        log.warning("  UNKNOWN class %s for %s — attempting raw add", cls, n["id"])
        params["node_type"] = cls.replace("K2Node_", "").replace("EdGraphNode_", "")

    r = rpc("add_node", params, silent_error=True)
    if r is None or (isinstance(r, dict) and "_error" in r):
        err = r.get("_error", "(no resp)") if isinstance(r, dict) else "(no resp)"
        log.error("  FAIL %s (%s) — %s", n["id"], cls, err[:200])
        return None
    new_id = r.get("node_id") if isinstance(r, dict) else None
    if not new_id:
        new_id = r.get("id") if isinstance(r, dict) else None
    log.info("  OK   %s -> %s (%s)", n["id"], new_id, cls)
    return new_id


def restore_default(node_id: str, pin_name: str, value: str):
    rpc("set_pin_default", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": node_id, "pin_name": pin_name, "value": value,
    }, silent_error=True)


def parse_connection(conn: str) -> tuple[str, str] | None:
    """'K2Node_VariableGet_72.Velocity' -> ('K2Node_VariableGet_72', 'Velocity')."""
    if "." not in conn:
        return None
    idx = conn.rfind(".")
    return conn[:idx], conn[idx + 1:]


def connect(src_node: str, src_pin: str, tgt_node: str, tgt_pin: str) -> bool:
    r = rpc("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": src_node, "source_pin": src_pin,
        "target_node": tgt_node, "target_pin": tgt_pin,
    }, silent_error=True)
    return r is not None and not (isinstance(r, dict) and "_error" in r)


def clear_graph():
    """Remove all non-essential nodes from UpdateVariables. Keep FunctionEntry."""
    log.info("=== Clearing UpdateVariables graph ===")
    r = rpc("get_graph_data", {"asset_path": ASSET, "graph_name": GRAPH})
    if not r or (isinstance(r, dict) and "_error" in r):
        log.warning("  Could not dump graph — skipping clear")
        return
    nodes = r.get("nodes", []) if isinstance(r, dict) else []
    for n in nodes:
        if n.get("class") in SKIP_CLASSES:
            continue
        rpc("remove_node", {"asset_path": ASSET, "graph_name": GRAPH,
                            "node_id": n["id"]}, silent_error=True)
    log.info("  Removed %d nodes", len(nodes))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-existing", action="store_true", help="Don't clear graph first")
    args = parser.parse_args()

    log.info("=== Loading backup ===")
    backup = load_backup()
    nodes = backup["nodes"]
    log.info("Backup nodes: %d", len(nodes))

    if args.dry_run:
        from collections import Counter
        classes = Counter(n["class"] for n in nodes)
        log.info("\n[DRY] Would create %d nodes:", len(nodes))
        for cls, c in classes.most_common():
            tag = ""
            if cls in LIMITED_CLASSES:
                tag = " (LIMITED — needs manual binding)"
            elif cls in SKIP_CLASSES:
                tag = " (skip)"
            log.info("  %s: %d%s", cls, c, tag)
        return

    if not args.keep_existing:
        clear_graph()

    # Pass 1: Create nodes
    log.info("\n=== PASS 1: Creating %d nodes ===", len(nodes))
    id_map: dict[str, str] = {}
    fail_create = 0
    for i, n in enumerate(nodes, 1):
        new_id = add_node_for(n)
        if new_id:
            id_map[n["id"]] = new_id
        else:
            fail_create += 1
        if i % 50 == 0:
            log.info("  ... %d/%d", i, len(nodes))
    log.info("Created: %d / %d (%d failures)", len(id_map), len(nodes), fail_create)

    # Pass 2: Restore default_values
    log.info("\n=== PASS 2: Restoring default values ===")
    default_count = 0
    for n in nodes:
        new_id = id_map.get(n["id"])
        if not new_id:
            continue
        for p in n.get("pins", []):
            dv = p.get("default_value")
            if dv and p.get("direction") == "input" and not p.get("connected_to"):
                restore_default(new_id, p["name"], str(dv))
                default_count += 1
    log.info("Restored %d default values", default_count)

    # Pass 3: Connect wires
    log.info("\n=== PASS 3: Connecting wires ===")
    wire_ok = 0
    wire_fail = 0
    for n in nodes:
        src_new = id_map.get(n["id"])
        if not src_new:
            continue
        for p in n.get("pins", []):
            if p.get("direction") != "output":
                continue
            for conn in p.get("connected_to", []):
                parsed = parse_connection(conn)
                if not parsed:
                    continue
                tgt_old, tgt_pin = parsed
                tgt_new = id_map.get(tgt_old)
                if not tgt_new:
                    log.debug("  skip wire to %s (target not created)", tgt_old)
                    wire_fail += 1
                    continue
                if connect(src_new, p["name"], tgt_new, tgt_pin):
                    wire_ok += 1
                else:
                    wire_fail += 1
    log.info("Connected: %d / %d failed", wire_ok, wire_fail)

    # Compile + save
    log.info("\n=== Compiling ===")
    c = rpc("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: %s", c)
    log.info("\n=== Saving ===")
    s = rpc("save_asset", {"asset_path": ASSET})
    log.info("save: %s", s)

    log.info("\n=== Summary ===")
    log.info("  Nodes created: %d / %d (failures: %d)", len(id_map), len(nodes), fail_create)
    log.info("  Defaults restored: %d", default_count)
    log.info("  Wires: %d ok, %d failed", wire_ok, wire_fail)

    # Limited-class manual binding list
    limited = [n for n in nodes if n["class"] in LIMITED_CLASSES and n["id"] in id_map]
    if limited:
        log.warning("\n=== MANUAL BINDING NEEDED for %d node(s) ===", len(limited))
        for n in limited:
            log.warning("  %s (%s) title=%r", id_map[n["id"]], n["class"], n.get("title", "")[:60])


if __name__ == "__main__":
    main()
