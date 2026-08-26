from mono import *
import time,re,json,sys
dur=int(sys.argv[1]) if len(sys.argv)>1 else 300
V=lambda t: [round(float(x),1) for x in re.findall(r"-?\d+\.\d+",str(t))]
t0=time.time(); prev=None; rows=[]
while time.time()-t0<dur:
    try: o=pcall("GetLedgeIKDebugMirror",anim=True)["out_params"]
    except Exception: time.sleep(2); continue
    stT=re.search(r"Translation=\(([^)]*)\)",str(o.get("MoveStartT"))); 
    row=dict(t=round(time.time()-t0,1),actor=V(o["ActorLoc"]),HL=V(o["HandL"]),HR=V(o["HandR"]),aL=round(o["HandAlphaL"],2),aR=round(o["HandAlphaR"],2),cvL=round(o["CurveMoveL"],2),cvR=round(o["CurveMoveR"],2),
             L_st=o.get("MoveStartDist"),L_tgt=o.get("MoveTargetDist"),StartT=V(stT.group(1)) if stT else None,bs=str(o.get("BSAnimName"))[-28:],ev02=o.get("EvalMoveL02"),spline=(re.search(r"PersistentLevel\.([^.:'\"]+)",str(o.get("SplineRef"))) or [None,"None"])[1][-10:])
    key=(tuple(row["actor"]),tuple(row["HL"]),row["cvL"],row["L_tgt"])
    if key!=prev: prev=key; rows.append(row); print(json.dumps(row),flush=True)
json.dump(rows,open("poll_mirror_%d.json"%int(t0),"w"),indent=1); print("DONE",len(rows))
