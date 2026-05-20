"""CircleStrafeHysteresis 진단 dump.

PC_01 ABP의 Circle/Strafe/Hysteresis 관련 변수, 그래프 노드, Chooser/SM transition rule
을 Monolith HTTP API 로 dump.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

MONOLITH = "http://localhost:9316/mcp"
ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
OUT_DIR = Path(r"E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\circle_strafe_diag")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def call(action: str, params: dict | None = None) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "animation_query",
            "arguments": {"action": action, "params": params or {"asset_path": ASSET}},
        },
    }
    req = urllib.request.Request(
        MONOLITH, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = json.loads(r.read())
    if raw.get("result", {}).get("isError"):
        return {"error": raw["result"]["content"][0]["text"]}
    return json.loads(raw["result"]["content"][0]["text"])


def save(name: str, data) -> Path:
    p = OUT_DIR / name
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def main() -> int:
    # 1. variables
    print("[1/5] dump variables...")
    vars_res = call("get_abp_variables")
    all_vars = vars_res.get("variables", vars_res)
    if isinstance(all_vars, dict):
        all_vars = all_vars.get("variables", [])
    pat = re.compile(r"Circle|Strafe|Hyster", re.IGNORECASE)
    filt = [v for v in all_vars if pat.search(v.get("name", ""))]
    save("01_variables_filtered.json", {"count": len(filt), "vars": filt})
    print(f"  -> {len(filt)} variables matched")
    for v in filt:
        print(f"     - {v.get('name'):40} type={v.get('type'):20} default={v.get('default')!r}")

    # 2. graphs list
    print("\n[2/5] list graphs...")
    graphs_res = call("get_graphs")
    graphs = graphs_res.get("graphs", graphs_res)
    if isinstance(graphs, dict):
        graphs = graphs.get("graphs", [])
    save("02_graphs.json", graphs)
    print(f"  -> {len(graphs)} graphs total")
    for g in graphs:
        if isinstance(g, dict):
            name = g.get("name", "?")
            gtype = g.get("type", "?")
            print(f"     - {name:50} {gtype}")

    # 3. UpdateVariables nodes (target the function graph)
    print("\n[3/5] dump UpdateVariables nodes...")
    uv_res = call("get_nodes", {"asset_path": ASSET, "graph_name": "UpdateVariables"})
    save("03_updatevariables_nodes_RAW.json", uv_res)
    nodes = uv_res.get("nodes", []) if isinstance(uv_res, dict) else []
    print(f"  -> {len(nodes)} nodes in UpdateVariables")
    # filter relevant nodes
    rel = []
    for n in nodes:
        blob = json.dumps(n)
        if pat.search(blob):
            rel.append(n)
    save("03_updatevariables_nodes_filtered.json", {"count": len(rel), "nodes": rel})
    print(f"  -> {len(rel)} nodes mention Circle/Strafe/Hyster")
    for n in rel:
        nid = n.get("id") or n.get("node_id") or n.get("name")
        ntype = n.get("class") or n.get("type") or n.get("node_class")
        title = n.get("title") or n.get("display_name") or ""
        print(f"     - {nid:40} {ntype:50} {title}")

    # 4. state machines + transitions
    print("\n[4/5] state machines...")
    sm_res = call("get_state_machines")
    save("04_state_machines.json", sm_res)
    sms = sm_res.get("state_machines", []) if isinstance(sm_res, dict) else []
    print(f"  -> {len(sms)} state machines")
    for sm in sms:
        sm_name = sm.get("name") if isinstance(sm, dict) else str(sm)
        print(f"     - {sm_name}")

    # transitions for MoveStateMachine + Loco
    for sm_name in ("MoveStateMachine", "LocoStateMachine"):
        try:
            tr = call("get_transitions", {"asset_path": ASSET, "state_machine": sm_name})
            save(f"04_transitions_{sm_name}.json", tr)
            count = len(tr.get("transitions", [])) if isinstance(tr, dict) else 0
            print(f"     transitions/{sm_name} -> {count}")
        except Exception as exc:
            print(f"     transitions/{sm_name} FAIL: {exc}")

    # 5. ABP info
    print("\n[5/5] abp info...")
    info = call("get_abp_info")
    save("05_abp_info.json", info)

    print(f"\nDONE. dir: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
