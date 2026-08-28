# -*- coding: utf-8 -*-
"""이동 중 물리 게이트 추적: bActive / bFrontBlocked / bUnitMoveInProgress / CurrentDistance"""
from mono import *
import re,json,sys,time
dur=int(sys.argv[1]) if len(sys.argv)>1 else 90
def flag(s,name): return 'True' if (name+'=True') in s else 'False'
def num(s,name):
    m=re.search(name+r'=(-?[\d.]+)',s); return round(float(m.group(1)),1) if m else None
t0=time.time(); rows=[]; prev=None; n=0
print('폴링 시작 (%ds) — 렛지에 매달려 좌우로 이동해줘'%dur,flush=True)
while time.time()-t0<dur:
    try: s=str(pcall('GetLedgeMoveData',comp='CharMoveComp')['return_value'])
    except Exception: time.sleep(1); continue
    n+=1
    row=dict(t=round(time.time()-t0,1),
             Active=flag(s,'bActive'), Front=flag(s,'bFrontBlocked'),
             UnitMove=flag(s,'bUnitMoveInProgress'), Transit=flag(s,'bTransitingToNextLedge'),
             Dist=num(s,'CurrentDistance'), Tgt=num(s,'UnitMoveTargetDistance'))
    key=(row['Active'],row['Front'],row['UnitMove'],row['Transit'])
    if key!=prev:
        prev=key; rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
    elif n%15==0:
        rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
json.dump(rows,open('poll_gate_%d.json'%int(t0),'w'),indent=1)
print('DONE 샘플',len(rows),'/ 총폴링',n,flush=True)
