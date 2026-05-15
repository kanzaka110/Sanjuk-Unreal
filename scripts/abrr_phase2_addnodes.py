#!/usr/bin/env python3
"""ABRR Phase 2: bulk-add 79 nodes to AnimRewindRecorderEmit graph.

Reads backup JSON. FunctionEntry already exists from add_function.
Builds old_id -> new_id mapping.

Class handling:
  - K2Node_FunctionEntry : SKIP (auto-created)
  - K2Node_VariableGet   : node_type=get, variable_name
  - K2Node_VariableSet   : node_type=set, variable_name
  - K2Node_IfThenElse    : node_type=if
  - K2Node_FormatText    : node_type=format_text, format (PHASE-INHERIT format string)
  - K2Node_CallFunction  : node_type=function, function_name, target_class
  - K2Node_GetEnumeratorNameAsString : try class_name then fallback CallFunction
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from pathlib import Path
from typing import Any

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"
BACKUP = Path(r"C:\Dev\Sanjuk-Unreal\Saved\PROBE_AnimRewindRecorderEmit_consolidated_20260514.json")
MAP_OUT = Path(r"C:\Dev\Sanjuk-Unreal\Saved\ABRR_id_map.json")

FORMAT_STR = (
    '[ANIM_REC] "f"={f},"sp"={sp},"as"={as},"ms"={ms},"ist"={ist},"he"={he},'
    '"vlen"={vlen},"pwm"={pwm},"il"={il},"isf"={isf},"isc"={isc},"csh"={csh},'
    '"trd"={trd},"ib"={ib},"rmf"={rmf},"fik"={fik},"fca"={fca},"ow"={ow},'
    '"ig"={ig},"sc"={sc},"clip"={clip},"seq"={seq},"bim"={bim},"bpim"={bpim},'
    '"ms_l"={ms_l},"ms_p"={ms_p},"mm"={mm},"ops"={ops},"fbsw"={fbsw},"fa"={fa},'
    '"rop"={rop},"sba"={sba},"ibk"={ibk},"we"={we},"iw"={iw},"jes"={jes},'
    '"htt"={htt},"stip"={stip},"ip"={ip},"lm"={lm},"dal"={dal},"sset"={sset},'
    '"phase"={phase},"eow"={eow},"eprw"={eprw},"fv"={fv},"acc"={acc},'
    '"isafb"={isafb},"isaub"={isaub},"sswseq"={sswseq},"wt"={wt},"cvco"={cvco},'
    '"ubsw"={ubsw},"rva"={rva},"rvmci"={rvmci},"ifl"={ifl},"rj"={rj},"dog"={dog},'
    '"hd"={hd},"pav_z"={pav_z},"cav_z"={cav_z},"sms"={sms},"vac"={vac},'
    '"na"={na},"rrt"={rrt},"rrr"={rrr}'
)


logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)
_msg_id = [0]


def rpc(action: str, params: dict[str, Any]) -> Any:
    _msg_id[0] += 1
    body = {
        "jsonrpc": "2.0", "id": _msg_id[0], "method": "tools/call",
        "params": {"name": "blueprint_query",
                   "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data.get("result", {}).get("isError"):
        return {"_error": data["result"]["content"][0]["text"][:800]}
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def get_existing_nodes() -> set[str]:
    r = rpc("get_graph_data", {"asset_path": ASSET, "graph_name": GRAPH})
    if isinstance(r, dict) and "_error" in r:
        return set()
    if isinstance(r, dict):
        return {n["id"] for n in r.get("nodes", [])}
    return set()


def add_one(node: dict[str, Any]) -> tuple[str, str | None, str]:
    """Returns (old_id, new_id_or_None, status_message)."""
    old_id = node["id"]
    cls = node["class"]
    pos = node.get("pos", [0, 0])

    base_params: dict[str, Any] = {
        "asset_path": ASSET,
        "graph_name": GRAPH,
        "position": pos,
    }

    if cls == "K2Node_FunctionEntry":
        return (old_id, None, "SKIP_FUNCTION_ENTRY")

    if cls == "K2Node_VariableGet":
        # variable name = first output pin name (could be split, in which case
        # use the underlying variable from id metadata — for ours pin[0] of split
        # nodes is e.g. TrjPastAngularVelocity_X. Use prefix before last _X/_Y/_Z.
        pin0_name = node["pins"][0]["name"]
        var_name = pin0_name
        if pin0_name.endswith("_X") or pin0_name.endswith("_Y") or pin0_name.endswith("_Z"):
            # split vector — base variable name is prefix
            var_name = pin0_name.rsplit("_", 1)[0]
        base_params.update({"node_type": "get", "variable_name": var_name})
        r = rpc("add_node", base_params)
        if isinstance(r, dict) and "_error" not in r:
            return (old_id, r.get("node_id") or r.get("id"), "OK")
        return (old_id, None, f"FAIL: {r}")

    if cls == "K2Node_VariableSet":
        # var name = first non-exec input pin (the variable data pin)
        var_name = None
        for p in node["pins"]:
            if p.get("direction") == "input" and p.get("type") not in ("exec",):
                var_name = p.get("name")
                break
        if not var_name:
            return (old_id, None, "FAIL: cannot infer var name")
        base_params.update({"node_type": "set", "variable_name": var_name})
        r = rpc("add_node", base_params)
        if isinstance(r, dict) and "_error" not in r:
            return (old_id, r.get("node_id") or r.get("id"), "OK")
        return (old_id, None, f"FAIL: {r}")

    if cls == "K2Node_IfThenElse":
        base_params["node_type"] = "if"
        r = rpc("add_node", base_params)
        if isinstance(r, dict) and "_error" not in r:
            return (old_id, r.get("node_id") or r.get("id"), "OK")
        return (old_id, None, f"FAIL: {r}")

    if cls == "K2Node_FormatText":
        base_params.update({"node_type": "format_text", "format": FORMAT_STR})
        r = rpc("add_node", base_params)
        if isinstance(r, dict) and "_error" not in r:
            return (old_id, r.get("node_id") or r.get("id"), "OK")
        return (old_id, None, f"FAIL: {r}")

    if cls == "K2Node_CallFunction":
        fn = node.get("function")
        fcls = node.get("function_class")
        base_params.update({"node_type": "function", "function_name": fn})
        if fcls:
            base_params["target_class"] = fcls
        r = rpc("add_node", base_params)
        if isinstance(r, dict) and "_error" not in r:
            return (old_id, r.get("node_id") or r.get("id"), "OK")
        # retry without target_class
        if fcls:
            base_params.pop("target_class", None)
            r2 = rpc("add_node", base_params)
            if isinstance(r2, dict) and "_error" not in r2:
                return (old_id, r2.get("node_id") or r2.get("id"), "OK_NO_TARGETCLASS")
        return (old_id, None, f"FAIL: {r}")

    if cls == "K2Node_GetEnumeratorNameAsString":
        # Best guess: also a CallFunction in kismet library — Conv_ByteToString
        # delegates to it. Use function_name=GetEnumeratorNameAsString_NEW.
        # If add_node won't accept, fall back to using GetEnumeratorName.
        for fn in ("GetEnumeratorNameAsString_NEW", "GetEnumeratorNameAsString"):
            params = dict(base_params)
            params.update({"node_type": "function", "function_name": fn})
            r = rpc("add_node", params)
            if isinstance(r, dict) and "_error" not in r:
                return (old_id, r.get("node_id") or r.get("id"), f"OK_AS_FUNCTION_{fn}")
        return (old_id, None, f"FAIL_ENUM_NAME: {r}")

    return (old_id, None, f"UNHANDLED_CLASS: {cls}")


def main() -> None:
    nodes = json.loads(BACKUP.read_text(encoding="utf-8"))["nodes"]
    log.info("Backup nodes: %d", len(nodes))

    existing = get_existing_nodes()
    log.info("Already present: %s", sorted(existing))

    id_map: dict[str, str] = {}
    failures: list[tuple[str, str]] = []

    # First, capture the auto-created FunctionEntry mapping
    for n in nodes:
        if n["class"] == "K2Node_FunctionEntry":
            # find a FunctionEntry id in the existing graph
            for ex in existing:
                if "FunctionEntry" in ex:
                    id_map[n["id"]] = ex
                    log.info("MAP    %s -> %s (FunctionEntry pre-existing)", n["id"], ex)
                    break

    for n in nodes:
        if n["class"] == "K2Node_FunctionEntry":
            continue
        old_id, new_id, status = add_one(n)
        if new_id:
            id_map[old_id] = new_id
            log.info("ADD    %-50s -> %-30s [%s] (%s)", old_id, new_id, n["class"], status)
        else:
            failures.append((old_id, status))
            log.error("FAIL   %-50s [%s] (%s)", old_id, n["class"], status)

    MAP_OUT.parent.mkdir(parents=True, exist_ok=True)
    MAP_OUT.write_text(json.dumps(id_map, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("\nMapping written: %s (%d entries)", MAP_OUT, len(id_map))

    if failures:
        log.error("=== %d FAILURES ===", len(failures))
        for oid, st in failures:
            log.error("  %s :: %s", oid, st)
        sys.exit(2)

    log.info("Phase 2 OK: added %d nodes", len(id_map))


if __name__ == "__main__":
    main()
