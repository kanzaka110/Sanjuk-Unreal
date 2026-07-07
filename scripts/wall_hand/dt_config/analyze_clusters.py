"""Offline cluster analysis for UpdateWallHandIK collapse planning.
Finds the pure-data subtree feeding each terminal Set*/producer node,
treating Knots as transparent, stopping at 'boundary' source nodes.
Reports subtree size + external input cut -> good Collapse-to-Function candidates.
"""
import json, glob, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
bpath = sorted(glob.glob(os.path.join(HERE, "backup_UpdateWallHandIK_*.json")))[-1]
d = json.load(open(bpath, encoding="utf-8"))
nodes = {n["id"]: n for n in d["nodes"]}
def cls(nid): return nodes[nid]["class"] if nid in nodes else "?"
def ttl(nid): return (nodes[nid]["title"].split("\n")[0]) if nid in nodes else nid

EXEC = {"then","execute","exec"}
# reverse data adjacency: node -> set of upstream data-producer nodes
rev = collections.defaultdict(set)
fwd = collections.defaultdict(set)
for c in d["connections"]:
    if c["from_pin"] in EXEC or c["to_pin"] in EXEC:
        continue
    rev[c["to_node"]].add(c["from_node"])
    fwd[c["from_node"]].add(c["to_node"])

# Knots are transparent: collapse them out of the data graph
def is_knot(nid): return cls(nid) == "K2Node_Knot"

def data_parents(nid):
    """upstream producers, skipping through knots"""
    out = set()
    stack = list(rev[nid])
    seen = set()
    while stack:
        p = stack.pop()
        if p in seen: continue
        seen.add(p)
        if is_knot(p):
            stack.extend(rev[p])
        else:
            out.add(p)
    return out

# boundary = source nodes we DON'T pull into a collapsed pure function
BOUNDARY_CLASS = {"K2Node_VariableGet","K2Node_FunctionEntry","K2Node_DynamicCast",
                  "K2Node_BreakStruct"}
BOUNDARY_TITLE = {"Break Hit Result","Get Anim Instance","Get Actor Location",
                  "Get Actor Right Vector","Get Actor Forward Vector","Get Velocity",
                  "Get Socket Location","Sphere Trace By Channel","GetConfig",
                  "GetPendingWalkMode","GetWallHandState","Get Mesh"}
def is_boundary(nid):
    return cls(nid) in BOUNDARY_CLASS or ttl(nid) in BOUNDARY_TITLE

def subtree(root):
    """pure-data ancestors of root, stopping at boundaries. returns (interior, inputs)"""
    interior, inputs, seen = set(), set(), set()
    stack = [root]
    while stack:
        n = stack.pop()
        if n in seen: continue
        seen.add(n)
        for p in data_parents(n):
            if is_boundary(p):
                inputs.add(p)
            else:
                interior.add(p)
                stack.append(p)
    return interior, inputs

terminals = ["K2Node_CallFunction_95","K2Node_CallFunction_20","K2Node_CallFunction_86",
             "K2Node_VariableSet_0","K2Node_VariableSet_1","K2Node_VariableSet_2"]
print("backup:", os.path.basename(bpath))
print("="*70)
for t in terminals:
    interior, inputs = subtree(t)
    hist = collections.Counter(ttl(n) for n in interior)
    print(f"\n### {t}  ({ttl(t)})")
    print(f"  interior pure nodes: {len(interior)}  | external inputs: {len(inputs)}")
    top = ", ".join(f"{v}x {k}" for k,v in hist.most_common(6))
    print(f"  interior top: {top}")
    src = collections.Counter(ttl(n) for n in inputs)
    print(f"  input sources: {', '.join(f'{v}x {k}' for k,v in src.most_common())}")
