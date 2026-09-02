# -*- coding: utf-8 -*-
"""Test 프로파일 신설 — 펠비스 위치가 과하게 움직이도록.
   기존 3개 프로파일(LedgeDangle/Kinematic/HookshotAir)은 그대로 보존."""
from mono import *
import json, glob, copy
A='/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl'
bq=lambda a,p: call('blueprint_query',a,p)

bk=sorted(glob.glob('backup_physcontrol_*.json'))[-1]
orig={p['name']:p['value'] for p in json.load(open(bk,encoding='utf-8'))['properties']}
prof=copy.deepcopy(orig['Profiles'])
assert 'Test' not in prof, '이미 Test 있음 — 확인 필요'

CT=copy.deepcopy(prof['LedgeDangle']['ControlUpdates'][0]['Data'])   # 컨트롤 Data 템플릿
MT=copy.deepcopy(prof['LedgeDangle']['ModifierUpdates'][0]['Data'])  # 모디파이어 Data 템플릿

def C(name, **kw):
    d=copy.deepcopy(CT); d.update(kw); return {'Name':name,'Data':d}
def M(name, **kw):
    d=copy.deepcopy(MT); d.update(kw); return {'Name':name,'Data':d}

SIM=dict(MovementType='Simulated', CollisionType='QueryAndPhysics',
         GravityMultiplier=1.0, PhysicsBlendWeight=1.0)

prof['Test']={
 'ControlUpdates':[
   # ▼ 핵심: 골반 월드 스프링을 느슨(1.0)+언더댐프(0.15) → 큰 변위 + 출렁임
   C('WorldSpace_pelvis',
     bEnabled=True,
     LinearStrength=1.0, LinearDampingRatio=0.15, LinearExtraDamping=0.0, MaxForce=0.0,
     AngularStrength=3.0, AngularDampingRatio=1.0, AngularExtraDamping=0.0, MaxTorque=0.0,
     LinearTargetVelocityMultiplier=2.0, AngularTargetVelocityMultiplier=1.0),
   # ▼ 골반이 자유롭게 흔들리게 상·하위 체인을 약한 각도 유지로만 붙잡음
   C('ParentSpace_Spine',    bEnabled=True, AngularStrength=3.0, AngularDampingRatio=1.0, AngularExtraDamping=0.5),
   C('ParentSpace_LegLeft',  bEnabled=True, AngularStrength=3.0, AngularDampingRatio=1.5, AngularExtraDamping=0.5),
   C('ParentSpace_LegRight', bEnabled=True, AngularStrength=3.0, AngularDampingRatio=1.5, AngularExtraDamping=0.5),
 ],
 'ControlMultiplierUpdates':[],
 'ModifierUpdates':[
   # Kinematic 자식이 제약으로 골반을 못박지 않도록 전부 Simulated + 물리 100%
   M('pelvis',   **SIM),
   M('Spine',    **SIM),
   M('LegLeft',  **SIM),
   M('LegRight', **SIM),
 ],
}

print('쓸 프로파일:', list(prof.keys()))
for tgt in ('MyProfiles','Profiles'):
    bq('set_cdo_property',{'asset_path':A,'property_name':tgt,'value':prof})
    print('  write', tgt, 'ok')

# ── 재조회 대조 (TMap 통째 쓰기가 앞선 변경 되돌린 사고 4회 → 필수)
after={p['name']:p['value'] for p in bq('get_cdo_properties',{'asset_path':A})['properties']}
def norm(o):
    if isinstance(o,float): return round(o,4)
    if isinstance(o,bool): return o
    if isinstance(o,int): return round(float(o),4)
    if isinstance(o,dict): return {k:norm(v) for k,v in o.items()}
    if isinstance(o,list): return [norm(v) for v in o]
    return o
print()
print('Profiles   키:', list(after['Profiles'].keys()))
print('MyProfiles 키:', list(after['MyProfiles'].keys()))
print('의도대로 기록? Profiles=', norm(prof)==norm(after['Profiles']),
      '/ MyProfiles=', norm(prof)==norm(after['MyProfiles']))
print('기존 3종 무손상?', all(norm(orig['Profiles'][k])==norm(after['Profiles'][k])
                              for k in ('LedgeDangle','Kinematic','HookshotAir')))
print()
t=after['Profiles']['Test']
for cu in t['ControlUpdates']:
    d=cu['Data']
    print(' [C]',cu['Name'],{k:d[k] for k in ('bEnabled','LinearStrength','LinearDampingRatio','LinearTargetVelocityMultiplier','AngularStrength')})
for mu in t['ModifierUpdates']:
    d=mu['Data']
    print(' [M]',mu['Name'],{k:d[k] for k in ('MovementType','PhysicsBlendWeight','GravityMultiplier')})
