# -*- coding: utf-8 -*-
"""EventGraph exec 체인 구조 분석 — 이벤트/시퀀스에서 시작해 섹션별 절단선 파악."""
import json, io, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
inner = json.loads(json.loads(io.open(os.path.join(HERE, "layer_EventGraph.json"), encoding="utf-8").read())["result"]["content"][0]["text"])
nodes = {n["id"]: n for n in inner["nodes"]}

def exec_out(n):
    outs = []
    for p in n.get("pins") or []:
        if p.get("type") == "exec" and p["direction"] == "output":
            for t in p.get("connected_to") or []:
                outs.append((p["name"], t.rsplit(".", 1)[0]))
    return outs

# 이벤트 노드에서 exec 체인 추적
events = [n for n in inner["nodes"] if n["class"] in ("K2Node_Event", "K2Node_CustomEvent")]
for ev in events:
    print(f"### EVENT: {ev['title'].splitlines()[0]} [{ev['id']}]")
    seen = set()
    stack = [(ev["id"], 0)]
    order = []
    while stack:
        nid, depth = stack.pop()
        if nid in seen: continue
        seen.add(nid)
        n = nodes[nid]
        title = n["title"].replace("\n", " / ")
        order.append((depth, n["class"].replace("K2Node_",""), title, nid))
        outs = exec_out(n)
        for pin_name, tgt in reversed(outs):
            stack.append((tgt, depth + 1))
    for d, cls, t, nid in order:
        print("  " * min(d,1) + f"{d:2d} {cls:22s} {t[:80]} [{nid}]")
    print()
