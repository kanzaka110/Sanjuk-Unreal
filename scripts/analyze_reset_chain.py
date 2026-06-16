#!/usr/bin/env python3
"""ResetOffset / ResetOffsetPulse / IsSequenceBindingActor SET 로직 + 조건 추적 (read-only)."""
from __future__ import annotations
import json, urllib.request
from typing import Any

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
EP = "http://localhost:9316/mcp"

def rpc(action, params, name="blueprint_query"):
    body={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":name,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(EP,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=120) as r: d=json.loads(r.read().decode())
    res=d.get("result",{})
    if res.get("isError"): return {"ERROR":res["content"][0]["text"][:300]}
    txt=res["content"][0]["text"]
    try: return json.loads(txt)
    except: return txt

def nm(g): return {n["id"]:n for n in g.get("nodes",[])}

def back(g, to_node, to_pin, depth=0, seen=None):
    if seen is None: seen=set()
    M=nm(g); conns=g.get("connections",[]); ind="  "*depth
    for c in conns:
        if c["to_node"]==to_node and (to_pin=="" or c["to_pin"]==to_pin):
            src,sp=c["from_node"],c["from_pin"]
            scls=M.get(src,{}).get("class","?"); t=(M.get(src,{}).get("title","") or "").replace("\n"," ")[:45]
            # 데이터 핀만 (exec 제외하려면 sp가 then/execute면 스킵)
            print(f"{ind}<= {src}.{sp} [{scls}] {t}")
            if (src,sp) in seen or depth>6: continue
            seen.add((src,sp))
            back(g, src, "", depth+1, seen)

GR = ["UpdateVariables","UpdateStates","UpdateTargetRotation","BlueprintThreadSafeUpdateAnimation"]

# 1. Set ResetOffset / ResetOffsetPulse / IsSequenceBindingActor 위치 + 값/조건
print("="*70); print("1. Set ResetOffset / ResetOffsetPulse / IsSequenceBindingActor"); print("="*70)
for gname in GR:
    g=rpc("export_graph",{"asset_path":ASSET,"graph_name":gname})
    if not isinstance(g,dict) or "ERROR" in g or not g.get("nodes"): continue
    for n in g["nodes"]:
        if "VariableSet" not in n.get("class",""): continue
        setvars=[p["name"] for p in n["pins"] if p["name"] in ("ResetOffset","ResetOffsetPulse","IsSequenceBindingActor")]
        if setvars:
            v=setvars[0]
            valpin=next((p for p in n["pins"] if p["name"]==v), None)
            print(f"\n[{gname}] {n['id']}  Set {v}")
            print(f"   value default={valpin.get('default_value')!r} connected_to={valpin.get('connected_to')}")
            print(f"   값 입력 역추적:")
            back(g, n["id"], v, 2)

# 2. ResetOffsetPulse 와 ResetOffset 관계: ResetOffsetPulse Get/Set 전수
print("\n"+"="*70); print("2. ResetOffsetPulse / IsSequenceBindingActor 가 set 되는 전체 그래프"); print("="*70)
allg=rpc("list_graphs",{"asset_path":ASSET})
names=[ (x if isinstance(x,str) else x.get("name")) for x in (allg if isinstance(allg,list) else allg.get("graphs",allg.get("names",[]))) ]
for gname in names:
    if not gname: continue
    g=rpc("export_graph",{"asset_path":ASSET,"graph_name":gname})
    if not isinstance(g,dict) or "ERROR" in g or not g.get("nodes"): continue
    for n in g["nodes"]:
        if "VariableSet" in n.get("class",""):
            for p in n["pins"]:
                if p["name"] in ("ResetOffsetPulse","IsSequenceBindingActor"):
                    print(f"  [{gname}] {n['id']} Set {p['name']}  val={p.get('default_value')!r} <= {p.get('connected_to')}")

# 3. IsAiming Set (StancePhase==2 확인)
print("\n"+"="*70); print("3. IsAiming SET 로직"); print("="*70)
for gname in GR+["UpdateStates"]:
    g=rpc("export_graph",{"asset_path":ASSET,"graph_name":gname})
    if not isinstance(g,dict) or "ERROR" in g or not g.get("nodes"): continue
    for n in g["nodes"]:
        if "VariableSet" in n.get("class","") and any(p["name"]=="IsAiming" for p in n["pins"]):
            print(f"[{gname}] {n['id']} Set IsAiming:")
            back(g, n["id"], "IsAiming", 1)
