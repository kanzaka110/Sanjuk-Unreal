from mono import *
import time,re,json
t0=time.time(); prev=None; rows=[]
while time.time()-t0<300:
    try:
        s=str(pcall("GetLedgeMoveData",comp="CharMoveComp")["return_value"]); o=pcall("GetLedgeIKDebugMirror",anim=True)["out_params"]; loc=pcall("K2_GetActorLocation")["return_value"]
    except Exception as e: print("err",str(e)[:60]); time.sleep(2); continue
    f=lambda k: (re.search(k+r"=([^,()]+)",s) or [None,"0"])[1]
    ref=str(o.get("SplineRef")); m=re.search(r"PersistentLevel\.([^.:'\"]+)",ref); owner=m.group(1) if m else "None"
    v=lambda t: [round(float(x)) for x in re.findall(r"-?\d+\.\d+",t)]
    row=dict(t=round(time.time()-t0,1),spline=owner,cur=float(f("CurrentDistance")),unit="bUnitMoveInProgress=True" in s,st=float(f("UnitMoveStartDistance")),tgt=float(f("UnitMoveTargetDistance")),actor=v(loc),HL=v(o["HandL"]),aL=round(o["HandAlphaL"],2))
    if owner!="None":
        try:
            p0=ed("pie_call_function",{"object_name":owner,"component_name":"LedgeSpline","function":"GetLocationAtDistanceAlongSpline","args":{"Distance":0,"CoordinateSpace":1}})["return_value"]
            row["spline_p0"]=v(p0); row["spline_len"]=ed("pie_call_function",{"object_name":owner,"component_name":"LedgeSpline","function":"GetSplineLength"})["return_value"]
        except Exception as e: row["spline_p0"]="err"
    key=(owner,row["cur"],row["unit"],row["tgt"],tuple(row["actor"]))
    if key!=prev:
        prev=key; rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
json.dump(rows,open("poll_spline_0825.json","w"),indent=1)
print("DONE",len(rows))
