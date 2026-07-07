"""Stage 8b: add L/R side-select to AttachSpeed/ReleaseSpeed config V2D fields.
FWall break=CF_108(Attach)/CF_112(Rel), RWall break=CF_109(Attach)/CF_113(Rel).
Front-selects have A<-FWall.comp, B<-RWall.comp. Add LWall break + sideSel(bRight,RWall.comp,LWall.comp),
reconnect frontSel.B<-sideSel. Neutral (R=L) but LWall tunable.
"""
import json, urllib.request, collections
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"
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
FAIL=[]
def conn(sn,sp,tn,tp,tag):
    r=C("connect_pins",source_node=sn,source_pin=sp,target_node=tn,target_pin=tp); ok=r.get('success')
    w(f"   {tag}: {ok}"+("" if ok else f" {r}"));
    if not ok: FAIL.append(tag)

RB,LB="K2Node_BreakStruct_0","K2Node_BreakStruct_1"; BRIGHT=("K2Node_CallFunction_54","bRight")
def flds(nid):
    d=C("get_node_details",node_id=nid); return {p['name'].split('_')[0]:p['name'] for p in d['pins'] if p['direction']=='output'}
lf=flds(LB)

# find front-select consuming a given break-output pin (breaknode.comp -> select.A)
def frontsel_of(fwall_break, comp):
    d=C("get_node_details",node_id=fwall_break)
    conns=[p['connected_to'] for p in d['pins'] if p['name']==comp][0]
    # connected_to like ['K2Node_CallFunction_150.A'] possibly via knot; resolve
    for c in conns:
        tn,tp=c.rsplit('.',1)
        # if knot, follow
        while True:
            dd=C("get_node_details",node_id=tn)
            if dd.get('class')=='K2Node_Knot':
                out=[p['connected_to'] for p in dd['pins'] if p['direction']=='output'][0]
                if not out: break
                tn,tp=out[0].rsplit('.',1); continue
            break
        if tp=='A': return tn
    return None

# add LWall breaks for AttachSpeed & ReleaseSpeed
def addbv(pos,src_break,field):
    r=C("add_node",node_type="CallFunction",function_name="BreakVector2D",target_class="KismetMathLibrary",position=pos); bid=r.get("id")
    conn(src_break,lf[field],bid,"InVec",f"LWall.{field}->break")
    return bid
bvLA=addbv([2300,-1440],LB,"AttachSpeed"); w(f"LWall AttachSpeed break={bvLA}")
bvLR=addbv([2300,-1340],LB,"ReleaseSpeed"); w(f"LWall ReleaseSpeed break={bvLR}")

# (FWall_break, RWall_break, LWall_break, y0)
GROUPS=[("K2Node_CallFunction_108","K2Node_CallFunction_109",bvLA,"AttachSpeed",-1440),
        ("K2Node_CallFunction_112","K2Node_CallFunction_113",bvLR,"ReleaseSpeed",-1340)]
for FBk,RBk,LBk,name,y0 in GROUPS:
    for i,comp in enumerate(["X","Y"]):
        fs=frontsel_of(FBk,comp)
        w(f"[{name}.{comp}] frontSel={fs}")
        if not fs: FAIL.append(f"{name}.{comp} frontSel not found"); continue
        r=C("add_node",node_type="CallFunction",function_name="SelectFloat",target_class="KismetMathLibrary",position=[2600,y0+i*40]); sid=r.get("id")
        conn(RBk,comp,sid,"A",f"{name}.{comp}.A(R)")
        conn(LBk,comp,sid,"B",f"{name}.{comp}.B(L)")
        conn(BRIGHT[0],BRIGHT[1],sid,"bPickA",f"{name}.{comp}.bRight")
        conn(sid,"ReturnValue",fs,"B",f"{name}.{comp} frontSel.B<-side")

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w("  ERRORS: "+str(r['errors']))
r2=C("validate_blueprint"); dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  disconnected: {len(dis)}  FAILS: {FAIL}")
w("DONE (not saved)")
