"""Wire side (RWall/LWall) HandOffset into side hand target.
Side HandOffset = bRight? RWall.HandOffset : LWall.HandOffset (per-component select).
Then add to walk offset: CF_67.B = Select_0 + HO.X ; CF_68.B = Select_2 + HO.Y.
DA side HandOffset=(0,0) so neutral now, but makes slot tunable. Verify selectors=bRight.
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
FAIL=[]
def conn(sn,sp,tn,tp,tag):
    r=C("connect_pins",source_node=sn,source_pin=sp,target_node=tn,target_pin=tp); ok=r.get('success')
    w(f"   {tag}: {ok}"+("" if ok else f" {r}"));
    if not ok: FAIL.append(tag)
RB,LB="K2Node_BreakStruct_0","K2Node_BreakStruct_1"; BRIGHT=("K2Node_CallFunction_54","bRight")
def fld(nid,short):
    d=C("get_node_details",node_id=nid); return next(p['name'] for p in d['pins'] if p['direction']=='output' and p['name'].split('_')[0]==short)
HO_R=fld(RB,'HandOffset'); HO_L=fld(LB,'HandOffset')
def bv(pos): return C("add_node",node_type="CallFunction",function_name="BreakVector2D",target_class="KismetMathLibrary",position=pos).get("id")
def sel(pos): return C("add_node",node_type="CallFunction",function_name="SelectFloat",target_class="KismetMathLibrary",position=pos).get("id")
def add(pos): return C("add_node",node_type="CallFunction",function_name="Add_DoubleDouble",target_class="KismetMathLibrary",position=pos).get("id")

# break RWall/LWall HandOffset
bR=bv([-1000,-900]); conn(RB,HO_R,bR,"InVec","RWall.HO->break")
bL=bv([-1000,-800]); conn(LB,HO_L,bL,"InVec","LWall.HO->break")
# per-component R/L select
sX=sel([-700,-900]); conn(bR,"X",sX,"A","HO.X R"); conn(bL,"X",sX,"B","HO.X L"); conn(BRIGHT[0],BRIGHT[1],sX,"bPickA","HO.X bRight")
sY=sel([-700,-800]); conn(bR,"Y",sY,"A","HO.Y R"); conn(bL,"Y",sY,"B","HO.Y L"); conn(BRIGHT[0],BRIGHT[1],sY,"bPickA","HO.Y bRight")
# insert add: Select_0 + HO.X -> CF_67.B ; Select_2 + HO.Y -> CF_68.B
aX=add([-400,-900]); C("disconnect_pins",node_id="K2Node_CallFunction_67",pin_name="B")
conn("K2Node_Select_0","ReturnValue",aX,"A","Select_0->addX.A"); conn(sX,"ReturnValue",aX,"B","HO.X->addX.B"); conn(aX,"ReturnValue","K2Node_CallFunction_67","B","addX->CF_67.B")
aY=add([-400,-800]); C("disconnect_pins",node_id="K2Node_CallFunction_68",pin_name="B")
conn("K2Node_Select_2","ReturnValue",aY,"A","Select_2->addY.A"); conn(sY,"ReturnValue",aY,"B","HO.Y->addY.B"); conn(aY,"ReturnValue","K2Node_CallFunction_68","B","addY->CF_68.B")

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')}")
if r.get('errors'): w("  ERR:"+str(r['errors']))
# verify sel bPickA traces to bRight
cur=json.load(open(sorted(glob.glob(os.path.join(HERE,'backup_UpdateWallHandIK_*.json')))[-1],encoding='utf-8'))
w(f"  side HO selects created: sX={sX} sY={sY}  FAILS={FAIL}")
w("DONE (not saved) - re-export to verify selectors")
