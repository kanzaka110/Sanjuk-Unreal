"""Stage 8a: add L/R side-select to config scalar front-overlays (IKStrength/TurnRel/TurnBlock/Elbow).
Currently frontSel.B <- RWall.field. Insert sideSel=SelectFloat(bRight, RWall.field, LWall.field),
reconnect frontSel.B <- sideSel. Behaviorally neutral (R=L) but makes LWall tunable.
"""
import json, urllib.request
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

RB,LB="K2Node_BreakStruct_0","K2Node_BreakStruct_1"
BRIGHT=("K2Node_CallFunction_54","bRight")
def flds(nid):
    d=C("get_node_details",node_id=nid); return {p['name'].split('_')[0]:p['name'] for p in d['pins'] if p['direction']=='output'}
rf,lf=flds(RB),flds(LB)

# (frontSelectNode, field_short, y)
JOBS=[("K2Node_CallFunction_105","IKStrength",-1780),
      ("K2Node_CallFunction_106","TurnReleaseSpeed",-1700),
      ("K2Node_CallFunction_107","TurnBlockHold",-1620),
      ("K2Node_CallFunction_116","ElbowAngleDeg",-1540)]
for frontsel,fs,y in JOBS:
    r=C("add_node",node_type="CallFunction",function_name="SelectFloat",target_class="KismetMathLibrary",position=[2600,y]); sid=r.get("id")
    w(f"[{fs}] sideSel={sid}")
    conn(RB,rf[fs],sid,"A",f"{fs}.A(R)")
    conn(LB,lf[fs],sid,"B",f"{fs}.B(L)")
    conn(BRIGHT[0],BRIGHT[1],sid,"bPickA",f"{fs}.bRight")
    conn(sid,"ReturnValue",frontsel,"B",f"{fs} frontSel.B<-side")  # replaces RWall direct

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w("  ERRORS: "+str(r['errors']))
r2=C("validate_blueprint"); dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  disconnected: {len(dis)}  FAILS: {FAIL}")
w("DONE (not saved)")
