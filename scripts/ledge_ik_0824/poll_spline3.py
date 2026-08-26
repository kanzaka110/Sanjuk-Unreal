from mono import *
import time,re,json
t0=time.time(); prev=None; rows=[]
V=lambda t: [round(float(x),1) for x in re.findall(r"-?\d+\.\d+",t)]
while time.time()-t0<300:
    try:
        s=str(pcall("GetLedgeMoveData",comp="CharMoveComp")["return_value"]); o=pcall("GetLedgeIKDebugMirror",anim=True)["out_params"]; loc=pcall("K2_GetActorLocation")["return_value"]
    except Exception as e: time.sleep(2); continue
    f=lambda k: (re.search(k+r"=([^,()]+)",s) or [None,"0"])[1]
    ref=str(o.get("SplineRef")); m=re.search(r"PersistentLevel\.([^.:'\"]+)",ref); owner=m.group(1) if m else "None"
    stT=re.search(r"Translation=\(([^)]*)\)",str(o.get("MoveStartT"))); stT=V(stT.group(1)) if stT else None
    row=dict(t=round(time.time()-t0,1),spline=owner[-10:],cur=float(f("CurrentDistance")),unit="bUnitMoveInProgress=True" in s,cpp_st=float(f("UnitMoveStartDistance")),cpp_tgt=float(f("UnitMoveTargetDistance")),
             L_st=o.get("MoveStartDist"),L_tgt=o.get("MoveTargetDist"),StartT=stT,actor=V(loc),HL=V(o["HandL"]),aL=round(o["HandAlphaL"],2))
    if owner!="None":
        try:
            row["sp0"]=V(ed("pie_call_function",{"object_name":owner,"component_name":"LedgeSpline","function":"GetLocationAtDistanceAlongSpline","args":{"Distance":0,"CoordinateSpace":1}})["return_value"])
            row["spT"]=V(ed("pie_call_function",{"object_name":owner,"component_name":"LedgeSpline","function":"GetLocationAtDistanceAlongSpline","args":{"Distance":row["L_tgt"] or 0,"CoordinateSpace":1}})["return_value"])
        except Exception as e: row["sp0"]="err"
    key=(owner,row["cur"],row["unit"],row["cpp_tgt"],tuple(row["actor"]),str(stT))
    if key!=prev: prev=key; rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
json.dump(rows,open("poll_spline3_0825.json","w"),indent=1); print("DONE",len(rows))
