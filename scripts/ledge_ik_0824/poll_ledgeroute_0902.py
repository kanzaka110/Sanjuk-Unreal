# -*- coding: utf-8 -*-
"""렛지 라우팅 실측 — 루트 분기키 + 실제 선택된 애님 (9/2)"""
import sys, time, json, re
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ed = lambda a, p: call('editor_query', a, p)
PROPS = ['LedgeMoveData','bTransitMoving','PrevMovementMode','MovementMode',
         'StateMachineMoveState','BlendStackInputs']
MAX = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0
ANIM_RE = re.compile(r"/Game/[^'\"]+?\.([A-Za-z0-9_]+)")

def anim(v):
    m = ANIM_RE.search(str(v))
    return m.group(1) if m else 'None'

t0 = time.time(); last = None; log = []
print('렛지 라우팅 폴링 — 이동/정지/이탈 다 해봐줘 (최대 %.0fs)' % MAX, flush=True)
while time.time() - t0 < MAX:
    try:
        p = (ed('pie_get_object_properties', {'class_name':'PC_01','anim_instance':True,
                                              'properties':PROPS})).get('properties') or {}
    except Exception as e:
        if 'PIE not running' in str(e): time.sleep(1); continue
        time.sleep(0.3); continue
    d = str(p.get('LedgeMoveData'))
    def g(k):
        m = re.search(k + r'=([^,)]+)', d)
        return m.group(1) if m else 'false'
    mm = re.search(r'NewEnumerator(\d+)', str(p.get('MovementMode')))
    sms = re.search(r'NewEnumerator(\d+)', str(p.get('StateMachineMoveState')))
    row = (str(p.get('bTransitMoving')), g('bFrontBlocked'), g('bTransitingToNextLedge'),
           g('PendingTransitMode'), g('TransitMoveAngleDeg'),
           sms.group(1) if sms else '?', mm.group(1) if mm else '?', anim(p.get('BlendStackInputs')))
    if row != last:
        last = row
        log.append(dict(zip(['TM','Front','Transiting','Mode','Ang','SMS','MM','Anim'], row),
                        t=round(time.time() - t0, 2)))
        print('  t=%6.2f MM=%-2s SMS=%-2s | TM=%-5s Front=%-5s Tr=%-5s Mode=%-5s ang=%-11s | %s' % (
            log[-1]['t'], row[6], row[5], row[0], row[1], row[2], row[3], row[4], row[7]), flush=True)
    time.sleep(0.05)
json.dump(log, open('poll_ledgeroute_0902.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('--- 샘플', len(log), '---', flush=True)
