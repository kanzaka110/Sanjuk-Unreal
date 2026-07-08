"""Systemic fix: all SIDE selects (A<-RWall) should select by WALL (CF_9 = which wall closer,
same signal the ABP uses for InRight), NOT bRight (=right HAND, true on left wall).
Change every side-select bPickA from bRight -> CF_9. Verify all trace to CF_9. Front selects
(A<-FWall, bPickA=front gate) untouched.
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
CF9=("K2Node_CallFunction_9","ReturnValue")
RWALL="K2Node_BreakStruct_0"

cur=json.load(open(sorted(glob.glob(os.path.join(HERE,'backup_UpdateWallHandIK_*.json')))[-1],encoding='utf-8'))
nodes={n['id']:n for n in cur['nodes']}
def ttl(n): return nodes[n]['title'].split(chr(10))[0] if n in nodes else n
into={}
for c in cur['connections']: into[(c['to_node'],c['to_pin'])]=(c['from_node'],c['from_pin'])
def thru(nid,pin):
    x=into.get((nid,pin))
    if not x: return None
    fn,fp=x
    while nodes.get(fn,{}).get('class')=='K2Node_Knot':
        y=into.get((fn,'InputPin'));
        if not y: return None
        fn,fp=y
    return (fn,fp)
def tb(nid,pin):
    r=thru(nid,pin)
    if not r: return None
    fn,fp=r
    if ttl(fn)=='Break Vector 2D': return tb(fn,'InVec')
    if ttl(fn)=='Break S Wall Hand Follow': return tb(fn,[p['name'] for p in nodes[fn]['pins'] if p['direction']=='input'][0])
    return fn
def bpick_src(nid):
    r=thru(nid,'bPickA'); return ttl(r[0]) if r else None

# find side selects: A traces to RWall break, currently bPickA=bRight
targets=[]
for nid,n in nodes.items():
    if n['class']=='K2Node_CallFunction' and ttl(nid)=='Select Float':
        if tb(nid,'A')==RWALL and bpick_src(nid)=='Get Wall Hand State':
            targets.append(nid)
w(f"side selects to retarget bRight->CF_9: {len(targets)} -> {sorted(targets)}")
for t in targets:
    C("disconnect_pins",node_id=t,pin_name="bPickA")
    r=C("connect_pins",source_node=CF9[0],source_pin=CF9[1],target_node=t,target_pin="bPickA")
    w(f"  {t}: {r.get('success')}")
r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')}")
if r.get('errors'): w("  ERR:"+str(r['errors']))
w("DONE (not saved) - re-verify")
