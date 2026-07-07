"""Surgical revert of today's struct-select refactor (Inc1-3) on UpdateWallHandIK.
Restores the 23 deleted nodes (at original positions) + their 68 original connections
from backup_163909, then removes my 6 helper nodes. Preserves ALL prior work (no P4 revert).
Comment boxes + cruft cleanup handled separately after.
Run with --go to execute; default = dry run.
"""
import json, urllib.request, os, sys, collections
HERE=os.path.dirname(os.path.abspath(__file__))
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"
def call(a,p):
    b={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"blueprint_query","arguments":{"action":a,"params":p}}}
    r=urllib.request.Request(MCP,data=json.dumps(b).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: raw=json.loads(x.read().decode())
    if "result" in raw and "content" in raw["result"]: return json.loads(raw["result"]["content"][0]["text"])
    return raw
def C(a,**p): p.update(asset_path=BP,graph_name=G); return call(a,p)

old=json.load(open(os.path.join(HERE,'backup_UpdateWallHandIK_20260707_163909.json'),encoding='utf-8'))
onodes={n['id']:n for n in old['nodes']}
DELETED=['K2Node_CallFunction_'+s for s in '130 142 144 132 134 138 140 149 151 146 147 156 158 153 154 164 160 166 162'.split()] + \
        ['K2Node_BreakStruct_'+s for s in '8 9 10 11'.split()]
HELPERS=['K2Node_Select_1','K2Node_BreakStruct_0','K2Node_CallFunction_55','K2Node_CallFunction_96','K2Node_BreakStruct_1','K2Node_BreakStruct_2']
DRY = "--go" not in sys.argv

def recreate_args(nid):
    n=onodes[nid]; cls=n['class']; pos=n['pos']
    if cls=='K2Node_CallFunction':
        return dict(node_type="CallFunction",function_name=n['function'],target_class="KismetMathLibrary",position=pos)
    if cls=='K2Node_BreakStruct':
        return dict(node_type="break_struct",struct_type="S_WallHandFollow",position=pos)
    raise Exception("unknown "+cls)

edges=[c for c in old['connections'] if c['from_node'] in DELETED or c['to_node'] in DELETED]
print(f"DRY={DRY}  recreate {len(DELETED)} nodes, replay {len(edges)} edges, delete {len(HELPERS)} helpers")
if DRY:
    byfn=collections.Counter(onodes[n].get('function') or onodes[n]['class'] for n in DELETED)
    print("  recreate types:",dict(byfn)); sys.exit(0)

idmap={}
print("[1] recreate nodes")
for nid in DELETED:
    r=C("add_node",**recreate_args(nid)); nn=r.get("id"); idmap[nid]=nn
    print(f"   {nid} -> {nn}")
def m(x): return idmap.get(x,x)
print("[2] replay edges")
ok=0; fail=0
for c in edges:
    r=C("connect_pins",source_node=m(c['from_node']),source_pin=c['from_pin'],target_node=m(c['to_node']),target_pin=c['to_pin'])
    if r.get('success'): ok+=1
    else: fail+=1; print(f"   FAIL {m(c['from_node'])}.{c['from_pin']}->{m(c['to_node'])}.{c['to_pin']}: {r}")
print(f"   edges ok={ok} fail={fail}")
print("[3] delete my helpers")
for h in HELPERS:
    r=C("remove_node",node_id=h); print(f"   del {h}: {r.get('success')}")
print("[4] compile")
r=C("compile_blueprint"); print(f"   compile success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): print("   ERRORS:",r['errors'])
r2=C("validate_blueprint")
dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
print(f"   UpdateWallHandIK disconnected: {len(dis)} {dis}")
print("DONE (not saved)")
