# -*- coding: utf-8 -*-
"""bNextFrontBlocked 가 이동 중 true 로 뒤집히는지 확인 (댕글 게이트의 마지막 항)"""
from mono import *
import re,json,sys,time
dur=int(sys.argv[1]) if len(sys.argv)>1 else 70
def flag(s,n): return 'T' if (n+'=True') in s else 'F'
def num(s,n):
    m=re.search(n+r'=(-?[\d.]+)',s); return round(float(m.group(1)),1) if m else None
t0=time.time(); rows=[]; prev=None; n=0
print('폴링 (%ds) — 렛지 매달려 좌우 이동'%dur,flush=True)
while time.time()-t0<dur:
    try:
        s=str(pcall('GetLedgeMoveData',comp='CharMoveComp')['return_value'])
        o=pcall('GetLedgeIKDebugMirror',anim=True)['out_params']
    except Exception: time.sleep(1); continue
    n+=1
    A=flag(s,'bActive'); F=flag(s,'bFrontBlocked'); NF=flag(s,'bNextFrontBlocked')
    wanted = (A=='T') and not (F=='T' or NF=='T')
    row=dict(t=round(time.time()-t0,1), Active=A, Front=F, NextFront=NF,
             Wanted=('T' if wanted else 'F'),
             UnitMove=flag(s,'bUnitMoveInProgress'), Transit=flag(s,'bTransitingToNextLedge'),
             Dangle=round(o.get('DangleAlpha',0),2),
             NextDist=num(s,'NextFrontHitDistance'))
    key=(A,F,NF,row['UnitMove'])
    if key!=prev or n%12==0:
        prev=key; rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
json.dump(rows,open('poll_nextfront_%d.json'%int(t0),'w'),indent=1)
print('DONE',len(rows),'/ 총',n,flush=True)
