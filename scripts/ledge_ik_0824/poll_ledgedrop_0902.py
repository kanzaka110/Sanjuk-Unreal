# -*- coding: utf-8 -*-
"""렛지 이탈(떨어짐) 트리거 실측 폴러 (9/2)
   렛지 진입을 감지하면 기록 시작 → 이탈 후 HOLD초까지 기록 → 자동 종료.
   사용: python poll_ledgedrop_0902.py [최대초]
"""
import sys, time, json
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ed=lambda a,p: call('editor_query',a,p)

ABP_PROPS=['CustomMoveState','PrevCustomMoveState','StateMachineMoveState',
           'MovementState','PrevMovementState','MovementMode','PrevMovementMode',
           'LedgeMoveData','bLedgeEventAnim','TransitingToNextLedge',
           'JustMoveInProgressLedge','bJumping','JumpCurrentCount','LedgeFrontBlocked']
ACTOR_PROPS=['Velocity']

MAXSEC=float(sys.argv[1]) if len(sys.argv)>1 else 120.0
HOLD=2.5          # 이탈 후 추가 기록 시간
t0=time.time(); samples=[]; armed=False; left_at=None; last=None

def snap():
    d={}
    try:
        r=ed('pie_get_object_properties',{'class_name':'PC_01','anim_instance':True,'properties':ABP_PROPS})
        pr=r.get('properties') or {}
        if isinstance(pr,dict): d.update(pr)
        else:
            for it in pr: d[it['name']]=it.get('value')
    except Exception as e:
        d['_err']=str(e)[:120]
    return d

print('폴링 시작 — 렛지 잡았다가 떨어져줘 (최대 %.0fs)'%MAXSEC)
while time.time()-t0 < MAXSEC:
    s=snap(); s['t']=round(time.time()-t0,3)
    if '_err' in s:
        if 'PIE not running' in s['_err']:
            print('  PIE 대기중...'); time.sleep(1.0); continue
        print('  ERR',s['_err']); time.sleep(0.5); continue
    cms=str(s.get('CustomMoveState'))
    # 변화 있을 때만 기록(노이즈 제거) + 항상 최근값 보관
    key=tuple(str(s.get(k)) for k in ABP_PROPS if k!='LedgeMoveData')
    if key!=last:
        samples.append(s); last=key
        print('  t=%6.2f CMS=%-14s SMS=%-14s MM=%-10s MS=%-12s EvAnim=%s Jump=%s'%(
            s['t'],cms,s.get('StateMachineMoveState'),s.get('MovementMode'),
            s.get('MovementState'),s.get('bLedgeEventAnim'),s.get('JumpCurrentCount')))
    if 'Ledge' in cms: armed=True; left_at=None
    elif armed and left_at is None: left_at=time.time(); print('  >>> 렛지 이탈 감지')
    if left_at and time.time()-left_at>HOLD: print('  >>> 사이클 완료'); break
    time.sleep(0.05)

out='poll_ledgedrop_0902.json'
json.dump(samples,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('샘플',len(samples),'→',out)
