# -*- coding: utf-8 -*-
"""임계 400 적용 후 이동 중 DangleAlpha 가 유지되는지 확인"""
from mono import *
import re,json,sys,time
dur=int(sys.argv[1]) if len(sys.argv)>1 else 70
def flag(s,n): return 'T' if (n+'=True') in s else 'F'
t0=time.time(); rows=[]; prev=None; n=0
print('폴링 시작 (%ds) — 렛지 매달려 좌우 이동'%dur,flush=True)
while time.time()-t0<dur:
    try:
        o=pcall('GetLedgeIKDebugMirror',anim=True)['out_params']
        s=str(pcall('GetLedgeMoveData',comp='CharMoveComp')['return_value'])
    except Exception: time.sleep(1); continue
    n+=1
    row=dict(t=round(time.time()-t0,1),
             Dangle=round(o.get('DangleAlpha',0),2),
             aL=round(o.get('HandAlphaL',0),2), aR=round(o.get('HandAlphaR',0),2),
             fL=round(o.get('FootAlphaL',0),2),
             UnitMove=flag(s,'bUnitMoveInProgress'), Active=flag(s,'bActive'))
    key=(row['Dangle'],row['UnitMove'])
    if key!=prev or n%12==0:
        prev=key; rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
json.dump(rows,open('poll_dangle2_%d.json'%int(t0),'w'),indent=1)
print('DONE',len(rows),'/ 총',n,flush=True)
