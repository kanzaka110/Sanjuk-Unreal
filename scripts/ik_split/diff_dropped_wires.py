# -*- coding: utf-8 -*-
"""서브 ABP EventGraph/레이어그래프의 노드들을 원본(layer_EventGraph.json / ik_export.json)과
핀 단위 대조 — 복사 때 드랍된 외부 와이어를 찾는다."""
import json, subprocess, io, os, sys
MCP = "http://localhost:9316/mcp"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "/Game/Art/Character/PC/PC_01/Blueprint/"
ABP = {"WallHand": BASE + "WallHandIK/PC_01_AnimLayer_WallHandIK", "Ledge": BASE + "CustomMove_Ledge/PC_01_AnimLayer_Ledge",
       "WallRun": BASE + "CustomMove_WallRun/PC_01_AnimLayer_WallRun", "Ladder": BASE + "CustomMove_Ladder/PC_01_AnimLayer_Ladder"}
LGRAPH = {"WallHand": "WallHandIK", "Ledge": "Ledge", "WallRun": "WallRun", "Ladder": "Ladder"}

def call(action, args):
    p = {"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":action, **args}}}
    r = subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],
                       capture_output=True, text=True, timeout=120)
    return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])

def load_orig(fn):
    return json.loads(json.loads(io.open(os.path.join(HERE, fn), encoding="utf-8").read())["result"]["content"][0]["text"])

orig_eg = {n["id"]: n for n in load_orig("layer_EventGraph.json")["nodes"]}
orig_ik = {n["id"]: n for n in load_orig("ik_export.json")["nodes"]}

sec = sys.argv[1] if len(sys.argv) > 1 else "Ledge"
for gname, orig in (("EventGraph", orig_eg), (LGRAPH[sec], orig_ik)):
    cur = call("get_graph_data", {"asset_path": ABP[sec], "graph_name": gname})
    cur_by_id = {n["id"]: n for n in cur["nodes"]}
    print(f"### {sec} / {gname}")
    for nid, n in cur_by_id.items():
        o = orig.get(nid)
        if not o: continue
        ocons = {p["name"]: set(p.get("connected_to") or []) for p in o.get("pins") or [] if p["direction"] == "input"}
        ccons = {p["name"]: set(p.get("connected_to") or []) for p in n.get("pins") or [] if p["direction"] == "input"}
        for pname, oset in ocons.items():
            cset = ccons.get(pname, set())
            if oset and not cset:
                print(f"  DROPPED  {nid}.{pname}  (원본: {sorted(oset)})  [{n['title'].splitlines()[0][:40]}]")
    print()
