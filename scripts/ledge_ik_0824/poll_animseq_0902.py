# -*- coding: utf-8 -*-
"""애님 전환 시퀀스 추적 — 같은 애님이 두 번 물리는지 (9/2)"""
import sys, time, json, re
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ed = lambda a, p: call('editor_query', a, p)
PROPS = ['BlendStackInputs','PrevBlendStackInputs','LedgeMoveData','bTransitMoving',
         'PrevMovementMode','MovementMode','StateMachineMoveState']
MAX = float(sys.argv[1]) if len(sys.argv) > 1 else 240.0
ANIM_RE = re.compile(r"/Game/[^'\"]+?\.([A-Za-z0-9_]+)")
def anim(v):
    m = ANIM_RE.search(str(v)); return m.group(1) if m else 'None'
t0=time.time(); lastanim=None; log=[]
print('애님 전환 추적 — 이탈 재현해줘 (최대 %.0fs)'%MAX, flush=True)
while time.time()-t0 < MAX:
    try:
        p=(ed('pie_get_object_properties',{'class_name':'PC_01','anim_instance':True,'properties':PROPS})).get('properties') or {}
    except Exception as e:
        if 'PIE not running' in str(e): time.sleep(1); continue
        time.sleep(0.3); continue
    d=str(p.get('LedgeMoveData'))
    def g(k):
        m=re.search(k+r'=([^,)]+)',d); return m.group(1) if m else 'false'
    a=anim(p.get('BlendStackInputs'))
    if a!=lastanim:
        mm=re.search(r'NewEnumerator(\d+)',str(p.get('MovementMode')))
        pm=re.search(r'NewEnumerator(\d+)',str(p.get('PrevMovementMode')))
        sms=re.search(r'NewEnumerator(\d+)',str(p.get('StateMachineMoveState')))
        rec=dict(t=round(time.time()-t0,2), anim=a,
                 MM=mm.group(1) if mm else '?', PrevMM=pm.group(1) if pm else '?',
                 SMS=sms.group(1) if sms else '?', TM=str(p.get('bTransitMoving')),
                 Tr=g('bTransitingToNextLedge'), Mode=g('PendingTransitMode'),
                 Ang=g('TransitMoveAngleDeg'))
        log.append(rec); lastanim=a
        print('  t=%6.2f MM=%-2s PrevMM=%-2s SMS=%-2s TM=%-5s Tr=%-5s Mode=%-5s ang=%-9s | %s'%(
            rec['t'],rec['MM'],rec['PrevMM'],rec['SMS'],rec['TM'],rec['Tr'],rec['Mode'],
            (rec['Ang'][:9] if rec['Ang'] else '-'),a), flush=True)
    time.sleep(0.03)
json.dump(log,open('poll_animseq_0902.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('--- 전환',len(log),'회 ---', flush=True)
