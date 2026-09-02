# -*- coding: utf-8 -*-
"""Exit 전후 BlendStackInputs(실제 선택된 애님) 추적 (9/2)"""
import sys,time,json,re
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ed=lambda a,p: call('editor_query',a,p)
PROPS=['LedgeMoveData','bTransitMoving','PrevMovementMode','MovementMode',
       'StateMachineMoveState','BlendStackInputs','PrevBlendStackInputs']
MAX=float(sys.argv[1]) if len(sys.argv)>1 else 300.0
t0=time.time(); last=None; log=[]
def anim(v):
    m=re.search(r'Anim=([^,)]+)',str(v))
    if not m: return None
    s=m.group(1)
    return s.split('.')[-1].rstrip("'\"") if s not in ('None',"None'") else 'None'
print('BlendStack 폴링 — 렛지에서 떨어져줘 (최대 %.0fs)'%MAX, flush=True)
while time.time()-t0<MAX:
    try:
        p=(ed('pie_get_object_properties',{'class_name':'PC_01','anim_instance':True,'properties':PROPS})).get('properties') or {}
    except Exception as e:
        if 'PIE not running' in str(e): time.sleep(1); continue
        time.sleep(0.3); continue
    d=str(p.get('LedgeMoveData'))
    g=lambda k:(re.search(k+r'=([^,)]+)',d).group(1) if re.search(k+r'=([^,)]+)',d) else None)
    sms=re.search(r'NewEnumerator(\d+)',str(p.get('StateMachineMoveState')))
    row=(anim(p.get('BlendStackInputs')), sms.group(1) if sms else '?', g('PendingTransitMode'), g('TransitMoveAngleDeg'))
    if row!=last:
        last=row; log.append({'t':round(time.time()-t0,2),'anim':row[0],'sms':row[1],'mode':row[2],'ang':row[3]})
        print('  t=%6.2f SMS=%-3s mode=%-5s ang=%-11s | anim=%s'%(log[-1]['t'],row[1],row[2],row[3],row[0]), flush=True)
    time.sleep(0.05)
json.dump(log,open('poll_blendstack_0902.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('--- 샘플',len(log),'---', flush=True)
