# -*- coding: utf-8 -*-
"""Exit 시점의 bTransitMoving / bNextFrontBlocked 실측 (9/2)"""
import sys,time,json,re
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ed=lambda a,p: call('editor_query',a,p)
PROPS=['LedgeMoveData','bTransitMoving','PrevMovementMode','MovementMode','StateMachineMoveState']
MAX=float(sys.argv[1]) if len(sys.argv)>1 else 120.0
t0=time.time(); hits=[]; seen=set()
print('Exit 폴링 — 렛지에서 떨어져줘 (최대 %.0fs)'%MAX, flush=True)
while time.time()-t0<MAX:
    try:
        r=ed('pie_get_object_properties',{'class_name':'PC_01','anim_instance':True,'properties':PROPS})
        p=r.get('properties') or {}
    except Exception as e:
        if 'PIE not running' in str(e): time.sleep(1); continue
        time.sleep(0.3); continue
    d=str(p.get('LedgeMoveData'))
    if 'PendingTransitMode=Exit' in d:
        f=lambda k:(re.search(k+r'=([^,)]+)',d).group(1) if re.search(k+r'=([^,)]+)',d) else None)
        rec=(str(p.get('bTransitMoving')), f('bNextFrontBlocked'), f('bFrontBlocked'), f('TransitMoveAngleDeg'))
        hits.append(rec)
        if rec[:3] not in seen:
            seen.add(rec[:3])
            print('  Exit! bTransitMoving=%s  bNextFrontBlocked=%s  bFrontBlocked=%s  ang=%s'%rec, flush=True)
    time.sleep(0.05)
print('--- Exit 샘플',len(hits),'개 ---', flush=True)
import collections
for k,v in collections.Counter(h[0] for h in hits).items(): print('  bTransitMoving=%s : %d회'%(k,v), flush=True)
for k,v in collections.Counter(h[1] for h in hits).items(): print('  bNextFrontBlocked=%s : %d회'%(k,v), flush=True)
for k,v in collections.Counter(h[2] for h in hits).items(): print('  bFrontBlocked=%s : %d회'%(k,v), flush=True)
json.dump(hits,open('poll_transitmoving_0902.json','w',encoding='utf-8'),ensure_ascii=False)
