# -*- coding: utf-8 -*-
"""AnimLayer_IK 'IK' 그래프 export_graph 덤프 → 섹션 노드 프로퍼티 추출 (레이어 분리 이식용)."""
import json, subprocess, io, os
MCP = "http://localhost:9316/mcp"
HERE = os.path.dirname(os.path.abspath(__file__))
LAY = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"

def call(action, args):
    p = {"jsonrpc":"2.0","method":"tools/call","id":1,
         "params":{"name":"blueprint_query","arguments":{"action":action, **args}}}
    r = subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],
                       capture_output=True, text=True, timeout=120)
    return r.stdout

out = call("export_graph", {"asset_path": LAY, "graph_name": "IK"})
io.open(os.path.join(HERE, "ik_export.json"), "w", encoding="utf-8").write(out)

g = json.loads(json.loads(out)["result"]["content"][0]["text"])
nodes = g.get("nodes", [])
print("exported nodes =", len(nodes))

TARGETS = ["AnimGraphNode_ControlRig_4", "AnimGraphNode_ControlRig_8",
           "AnimGraphNode_ControlRig_10", "AnimGraphNode_ControlRig_11",
           "AnimGraphNode_SequencePlayer_1", "AnimGraphNode_SequencePlayer_2",
           "AnimGraphNode_LayeredBoneBlend_0"]

sel = {}
for n in nodes:
    nid = n.get("id") or n.get("name")
    if nid in TARGETS:
        sel[nid] = n

io.open(os.path.join(HERE, "ik_section_nodes.json"), "w", encoding="utf-8").write(
    json.dumps(sel, ensure_ascii=False, indent=1))
for nid in TARGETS:
    if nid in sel:
        s = json.dumps(sel[nid], ensure_ascii=False)
        print(f"\n== {nid} == ({len(s)} chars)")
        print(s[:2500])
    else:
        print(f"\n== {nid} == MISSING")
