# -*- coding: utf-8 -*-
"""증상 진단용 현재 상태 전체 덤프 (bk_* 와 동일 범위)."""
import json, subprocess, io, os
MCP = "http://localhost:9316/mcp"
HERE = os.path.dirname(os.path.abspath(__file__))
BP  = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
LAY = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"

def call(action, args):
    p = {"jsonrpc":"2.0","method":"tools/call","id":1,
         "params":{"name":"blueprint_query","arguments":{"action":action, **args}}}
    r = subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],
                       capture_output=True, text=True, timeout=60)
    return r.stdout

JOBS = [
    ("post_bp.json",    BP,  "UpdateWallHandIK"),
    ("post_ik.json",    LAY, "IK"),
    ("post_leg.json",   LAY, "EventGraph"),
    ("post_alpha.json", ABP, "SetSmoothedWallHandAlpha"),
    ("post_data.json",  ABP, "SetWallHandData"),
    ("post_front.json", ABP, "SetWallHandFront"),
    ("post_allow.json", ABP, "IsWallHandAllowed"),
    ("post_state.json", ABP, "GetWallHandState"),
    ("post_updvar.json",ABP, "UpdateVariables"),
]
for fn, asset, graph in JOBS:
    out = call("get_graph_data", {"asset_path": asset, "graph_name": graph})
    io.open(os.path.join(HERE, "post", fn), "w", encoding="utf-8").write(out)
    try:
        g = json.loads(json.loads(out)["result"]["content"][0]["text"])
        print(fn, "OK nodes=", len(g.get("nodes", [])))
    except Exception as e:
        print(fn, "FAIL", str(e), out[:200])
