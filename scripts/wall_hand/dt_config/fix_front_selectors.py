"""Fix: front-overlay selects (A<-FWall) must use CF_53 (front gate) as bPickA, not bRight.
Monolith merged all bPickA into one chain. Disconnect each front select's bPickA, reconnect CF_53.
Side selects (A<-RWall) stay on bRight (already correct). Verify each traces to CF_53.
"""
import json, urllib.request, glob, os, collections
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"
HERE=os.path.dirname(os.path.abspath(__file__))
def call(a,p):
    b={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"blueprint_query","arguments":{"action":a,"params":p}}}
    r=urllib.request.Request(MCP,data=json.dumps(b).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: raw=json.loads(x.read().decode())
    try:
        if "result" in raw and "content" in raw["result"]:
            t=raw["result"]["content"][0]["text"]; return json.loads(t) if t.strip() else {"success":None,"_raw":t}
    except Exception as e: return {"_err":str(e),"_raw":raw}
    return raw
def C(a,**p): p.update(asset_path=BP,graph_name=G); return call(a,p)
def w(m): print(m)
GATE=("K2Node_CallFunction_53","ReturnValue")

# load current export to find front selects (A traces to FWall Break_2)
cur=json.load(open(sorted(glob.glob(os.path.join(HERE,'backup_UpdateWallHandIK_*.json')))[-1],encoding='utf-8'))
nodes={n['id']:n for n in cur['nodes']}
def ttl(n): return nodes[n]['title'].split(chr(10))[0] if n in nodes else n
into={}
for c in cur['connections']: into[(c['to_node'],c['to_pin'])]=(c['from_node'],c['from_pin'])
def trace_break(nid,pin):
    # trace a pin back through knots/breakvec2d to the owning struct-break node
    x=into.get((nid,pin))
    if not x: return None
    fn,fp=x
    while nodes.get(fn,{}).get('class')=='K2Node_Knot':
        y=into.get((fn,'InputPin'));
        if not y: return None
        fn,fp=y
    if ttl(fn)=='Break Vector 2D':  # go through to its InVec source
        return trace_break(fn,'InVec')
    return fn  # the break node (or whatever)
FWALL="K2Node_BreakStruct_2"
fronts=[]
for nid,n in nodes.items():
    if n['class']=='K2Node_CallFunction' and ttl(nid)=='Select Float':
        if trace_break(nid,'A')==FWALL:
            fronts.append(nid)
w(f"front-overlay selects (A<-FWall): {len(fronts)} -> {sorted(fronts)}")
for fs in fronts:
    C("disconnect_pins",node_id=fs,pin_name="bPickA")
    r=C("connect_pins",source_node=GATE[0],source_pin=GATE[1],target_node=fs,target_pin="bPickA")
    w(f"  {fs} bPickA<-CF_53: {r.get('success')}")

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')}")
if r.get('errors'): w("  ERR:"+str(r['errors']))
w("DONE (not saved)")
