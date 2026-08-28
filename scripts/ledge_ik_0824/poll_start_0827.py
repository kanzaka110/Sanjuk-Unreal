# -*- coding: utf-8 -*-
"""이동 시작 순간 손 타깃 궤적 측정. sleep 없이 최대 속도 폴링.
   기록: 손-액터 상대벡터(튐은 여기 나타남), alpha, 커브, StartDist/TargetDist, SplineRef"""
from mono import *
import time,re,json,sys
dur=int(sys.argv[1]) if len(sys.argv)>1 else 120
V=lambda t:[round(float(x),1) for x in re.findall(r"-?\d+\.\d+",str(t))]
def sub(a,b):
    try: return [round(a[i]-b[i],1) for i in range(3)]
    except Exception: return None
def mag(v):
    try: return round(sum(x*x for x in v)**.5,1)
    except Exception: return None
t0=time.time(); rows=[]; prevT=None; prevRel=None; n=0
print("폴링 시작 — 렛지에 매달린 뒤 좌/우 이동해줘 (%ds)"%dur,flush=True)
while time.time()-t0<dur:
    try: o=pcall("GetLedgeIKDebugMirror",anim=True)["out_params"]
    except Exception: time.sleep(1); continue
    n+=1
    act=V(o.get("ActorLoc")); hl=V(o.get("HandL")); hr=V(o.get("HandR"))
    relL=sub(hl,act); relR=sub(hr,act)
    tgt=o.get("MoveTargetDist"); st=o.get("MoveStartDist")
    sp=(re.search(r"PersistentLevel\.([^.:'\"]+)",str(o.get("SplineRef"))) or [None,"None"])[1][-12:]
    jump=mag(sub(relL,prevRel)) if prevRel else None
    row=dict(t=round(time.time()-t0,2),relL=relL,dL=mag(relL),relR=relR,dR=mag(relR),
             jump=jump,aL=round(o.get("HandAlphaL",0),2),aR=round(o.get("HandAlphaR",0),2),
             cvL=round(o.get("CurveMoveL",0),2),st=st,tgt=tgt,sp=sp)
    if tgt!=prevT: row["EDGE"]=True; prevT=tgt
    if row.get("EDGE") or (jump is not None and jump>3.0) or n%12==0:
        rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
    prevRel=relL
f="poll_start_%d.json"%int(t0); json.dump(rows,open(f,"w"),indent=1)
print("DONE",len(rows),"샘플 ->",f,"| 총폴링",n,flush=True)
