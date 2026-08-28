# -*- coding: utf-8 -*-
"""LedgeIK 가 이동 중 평가되는지 판별.
   MeshToWorld(LedgeIK 가 매 프레임 세팅) 가 갱신되면 LedgeIK 실행 중."""
from mono import *
import re,json,sys,time
dur=int(sys.argv[1]) if len(sys.argv)>1 else 80
def vec(t):
    m=re.search(r'Translation=\(X=(-?[\d.]+),Y=(-?[\d.]+),Z=(-?[\d.]+)\)',str(t))
    return [round(float(m.group(i)),1) for i in (1,2,3)] if m else None
def flag(s,n): return 'T' if (n+'=True') in s else 'F'
t0=time.time(); rows=[]; prev=None; n=0
print('폴링 시작 (%ds) — 렛지 매달려 좌우 이동'%dur,flush=True)
while time.time()-t0<dur:
    try:
        o=pcall('GetLedgeIKDebugMirror',anim=True)['out_params']
        s=str(pcall('GetLedgeMoveData',comp='CharMoveComp')['return_value'])
    except Exception: time.sleep(1); continue
    n+=1
    mw=vec(o.get('MeshToWorld'))
    hl=re.findall(r'-?\d+\.\d+',str(o.get('HandL')))[:3]
    row=dict(t=round(time.time()-t0,1), MeshToWorld=mw,
             HandL=[round(float(x),1) for x in hl] if len(hl)==3 else None,
             aL=round(o.get('HandAlphaL',0),2), Dangle=round(o.get('DangleAlpha',0),2),
             UnitMove=flag(s,'bUnitMoveInProgress'), Active=flag(s,'bActive'))
    key=(str(mw),row['UnitMove'])
    if key!=prev or n%10==0:
        prev=key; rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
json.dump(rows,open('poll_ledgeik_%d.json'%int(t0),'w'),indent=1)
print('DONE',len(rows),'/ 총',n,flush=True)
