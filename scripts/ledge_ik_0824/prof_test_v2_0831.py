# -*- coding: utf-8 -*-
"""Test 프로파일 v2 — 발산 제거 + 손 IK 유지.
   v1 실패: DampingRatio 0.15(무감쇠) + TargetVelMult 2.0(에너지 주입) → 진폭 발산해 캐릭터 소실.
   v2 방침: 진폭은 '약한 스프링'으로만 만들고, 감쇠는 임계(1.0)로 잡아 발산 차단.
            상체 PhysicsBlendWeight 를 낮게 둬 애님(=손 IK) 우세 유지."""
from mono import *
import json, copy
A='/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl'
bq=lambda a,p: call('blueprint_query',a,p)

cur={p['name']:p['value'] for p in bq('get_cdo_properties',{'asset_path':A})['properties']}
prof=copy.deepcopy(cur['Profiles'])
CT=copy.deepcopy(prof['LedgeDangle']['ControlUpdates'][0]['Data'])
MT=copy.deepcopy(prof['LedgeDangle']['ModifierUpdates'][0]['Data'])
def C(name,**kw):
    d=copy.deepcopy(CT); d.update(kw); return {'Name':name,'Data':d}
def M(name,**kw):
    d=copy.deepcopy(MT); d.update(kw); return {'Name':name,'Data':d}

prof['Test']={
 'ControlUpdates':[
   # 골반: 약한 스프링(진폭)+임계감쇠(발산 차단). 타겟속도 배율은 1.0 = 에너지 주입 없음
   C('WorldSpace_pelvis', bEnabled=True,
     LinearStrength=1.0, LinearDampingRatio=1.0, LinearExtraDamping=0.0, MaxForce=0.0,
     AngularStrength=6.0, AngularDampingRatio=1.5, AngularExtraDamping=0.5, MaxTorque=0.0,
     LinearTargetVelocityMultiplier=1.0, AngularTargetVelocityMultiplier=1.0),
   # 상체/다리 각도 유지 = HookshotAir·LedgeDangle 에서 검증된 값 그대로
   C('ParentSpace_Spine',    bEnabled=True, AngularStrength=6.0, AngularDampingRatio=1.5, AngularExtraDamping=0.5),
   C('ParentSpace_LegLeft',  bEnabled=True, AngularStrength=3.0, AngularDampingRatio=1.5, AngularExtraDamping=0.5),
   C('ParentSpace_LegRight', bEnabled=True, AngularStrength=3.0, AngularDampingRatio=1.5, AngularExtraDamping=0.5),
 ],
 'ControlMultiplierUpdates':[],
 # 🔴 순서 주의: Spine 림은 bIncludeParentBone=true 라 pelvis 를 삼킨다.
 #    pelvis 전용값이 살아남으려면 Spine 을 먼저 쓰고 pelvis 를 뒤에 써서 덮어써야 한다.
 'ModifierUpdates':[
   M('Spine',    MovementType='Simulated', CollisionType='QueryAndPhysics',
                 PhysicsBlendWeight=0.4, GravityMultiplier=0.8),   # 상체는 애님 우세 → 팔/손 IK 유지
   M('LegLeft',  MovementType='Simulated', CollisionType='QueryAndPhysics',
                 PhysicsBlendWeight=0.7, GravityMultiplier=0.8),   # LedgeDangle 검증값
   M('LegRight', MovementType='Simulated', CollisionType='QueryAndPhysics',
                 PhysicsBlendWeight=0.7, GravityMultiplier=0.8),
   M('pelvis',   MovementType='Simulated', CollisionType='QueryAndPhysics',
                 PhysicsBlendWeight=1.0, GravityMultiplier=1.0),   # 골반만 물리 100% = 변위 최대
 ],
}

for tgt in ('MyProfiles','Profiles'):
    bq('set_cdo_property',{'asset_path':A,'property_name':tgt,'value':prof}); print('write',tgt,'ok')

after={p['name']:p['value'] for p in bq('get_cdo_properties',{'asset_path':A})['properties']}
def norm(o):
    if isinstance(o,bool): return o
    if isinstance(o,(int,float)): return round(float(o),4)
    if isinstance(o,dict): return {k:norm(v) for k,v in o.items()}
    if isinstance(o,list): return [norm(v) for v in o]
    return o
print('키:',list(after['Profiles'].keys()))
print('의도대로? P=',norm(prof)==norm(after['Profiles']),'/ MyP=',norm(prof)==norm(after['MyProfiles']))
print('기존 3종 무손상?',all(norm(cur['Profiles'][k])==norm(after['Profiles'][k]) for k in ('LedgeDangle','Kinematic','HookshotAir')))
t=after['Profiles']['Test']
for cu in t['ControlUpdates']:
    d=cu['Data']; print(' [C]',cu['Name'],{k:d[k] for k in ('bEnabled','LinearStrength','LinearDampingRatio','LinearTargetVelocityMultiplier','AngularStrength')})
for mu in t['ModifierUpdates']:
    d=mu['Data']; print(' [M]',mu['Name'],{k:d[k] for k in ('MovementType','PhysicsBlendWeight','GravityMultiplier')})
print('save:', ed('save_asset',{'asset_path':A})['saved'])
