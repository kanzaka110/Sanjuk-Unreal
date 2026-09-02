# -*- coding: utf-8 -*-
"""건너기 시 NextLedgeCandidateDist 실측 (9/2) — Near/Far 임계 결정용"""
import sys, time, json, re
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ed=lambda a,p: call('editor_query',a,p)
PROPS=['LedgeMoveData','bTransitMoving','BlendStackInputs']
ANIM=re.compile(r"/Game/[^'\"]+?\.([A-Za-z0-9_]+)")
MAX=float(sys.argv[1]) if len(sys.argv)>1 else 180.0
t0=time.time(); log=[]; last=None
print('dist 실측 — 가까운 건너기 / 먼 건너기 각각 해줘 (최대 %.0fs)'%MAX, flush=True)
while time.time()-t0<MAX:
    try:
        p=(ed('pie_get_object_properties',{'class_name':'PC_01','anim_instance':True,'properties':PROPS})).get('properties') or {}
    except Exception as e:
        if 'PIE not running' in str(e): time.sleep(1); continue
        time.sleep(0.3); continue
    d=str(p.get('LedgeMoveData'))
    def g(k,dv=None):
        m=re.search(k+r'=([^,)]+)',d); return m.group(1) if m else dv
    def f(k,dv=0.0):
        try: return float(g(k))
        except: return dv
    tr=(g('bTransitingToNextLedge','False')=='True')
    if not tr: 
        time.sleep(0.03); continue
    am=ANIM.search(str(p.get('BlendStackInputs')))
    rec=dict(t=round(time.time()-t0,2),
             dist=f('NextLedgeCandidateDist',-1.0), along=f('NextLedgeCandidateAlong',-1.0),
             cur=f('CurrentDistance',-1.0), ang=round(f('TransitMoveAngleDeg',0.0),1),
             mode=g('PendingTransitMode','-'), tgt=g('PendingTransitTarget','-'),
             anim=(am.group(1) if am else '-'))
    key=(round(rec['dist'],1), rec['anim'])
    if key!=last:
        last=key; log.append(rec)
        ds = ('%.1f'%rec['dist']) if rec['dist']<1e30 else 'INF'
        print('  t=%6.2f dist=%-10s along=%-8.1f cur=%-8.1f ang=%-7.1f %-6s %-10s | %s'%(
            rec['t'], ds, rec['along'], rec['cur'], rec['ang'], rec['mode'], rec['tgt'],
            rec['anim'].replace('P_Player_Ledge_','')), flush=True)
    time.sleep(0.03)
json.dump(log,open('poll_dist_0902.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
vals=[r['dist'] for r in log if 0<=r['dist']<1e30]
print('--- 전이 샘플 %d개 | 유한 dist %d개 ---'%(len(log),len(vals)), flush=True)
if vals:
    vals.sort()
    print('    최소 %.1f / 중앙 %.1f / 최대 %.1f'%(vals[0],vals[len(vals)//2],vals[-1]), flush=True)
