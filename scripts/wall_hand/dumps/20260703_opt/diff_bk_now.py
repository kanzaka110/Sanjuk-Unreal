# -*- coding: utf-8 -*-
"""bk_*(최적화 전) vs now_*(현재) 링크셋/핀디폴트 diff."""
import json, io

def load(f):
    d = json.load(io.open(f, encoding="utf-8"))
    if "result" in d:
        return json.loads(d["result"]["content"][0]["text"])
    return d

def linkset(g):
    s = set()
    defaults = {}
    for n in g.get("nodes", []):
        nid = n["id"]
        for p in n.get("pins", []):
            key = f"{nid}.{p['name']}"
            if p.get("direction") == "output":
                for t in p.get("connected_to", []) or []:
                    s.add(f"{key} -> {t}")
            dv = p.get("default_value")
            if dv not in (None, ""):
                defaults[key] = dv
    return s, defaults

PAIRS = [
    ("bp",    "bk_bp.json",    "now_bp.json"),
    ("ik",    "bk_ik.json",    "now_ik.json"),
    ("leg",   "bk_leg.json",   "now_leg.json"),
    ("alpha", "bk_alpha.json", "now_alpha.json"),
    ("data",  "bk_data.json",  "now_data.json"),
    ("front", "bk_front.json", "now_front.json"),
    ("allow", "bk_allow.json", "now_allow.json"),
]
out = []
for tag, bkf, nowf in PAIRS:
    bk, now = load(bkf), load(nowf)
    bs, bd = linkset(bk)
    ns, nd = linkset(now)
    removed = sorted(bs - ns)
    added = sorted(ns - bs)
    bnodes = {n["id"] for n in bk["nodes"]}
    nnodes = {n["id"] for n in now["nodes"]}
    gone = sorted(x for x in bnodes - nnodes if not x.startswith("EdGraphNode_Comment"))
    new = sorted(x for x in nnodes - bnodes if not x.startswith("EdGraphNode_Comment"))
    dchg = sorted(f"{k}: {bd[k]!r} -> {nd[k]!r}" for k in (set(bd) & set(nd)) if bd[k] != nd[k])
    out.append(f"\n######## {tag} (bk {len(bk['nodes'])}n/{len(bs)}L -> now {len(now['nodes'])}n/{len(ns)}L)")
    out.append(f"  nodes gone({len(gone)}): " + ", ".join(gone[:40]))
    out.append(f"  nodes new({len(new)}): " + ", ".join(new[:40]))
    out.append(f"  links removed({len(removed)}):")
    out += ["    - " + x for x in removed]
    out.append(f"  links added({len(added)}):")
    out += ["    + " + x for x in added]
    if dchg:
        out.append(f"  default changed({len(dchg)}):")
        out += ["    ~ " + x for x in dchg]
txt = "\n".join(out)
io.open("diff_bk_now.txt", "w", encoding="utf-8").write(txt)
print(txt[:6000])
print("\n... full -> diff_bk_now.txt" if len(txt) > 6000 else "")
