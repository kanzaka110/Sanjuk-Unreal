# -*- coding: utf-8 -*-
"""Test v4 — 골반 움직임 증폭. 손 IK(팔 Kinematic)·다리·상체 설정은 그대로 둔다.
   ω = Strength×2π, 정적 처짐 ≈ g·GravityMult/ω²  → Strength 를 낮추면 처짐·지연·진폭이 함께 커진다.
   발산은 v1 에서 DampingRatio 0.15 + TargetVelMult 2.0 조합이 원인이었으므로
   TargetVelMult 는 1.0 로 두고 DampingRatio 만 0.5(표준 언더댐프, 오버슛 ~16%·수렴 보장)까지 내린다."""
from mono import *
import copy
A='/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl'
bq=lambda a,p: call('blueprint_query',a,p)

cur={p['name']:p['value'] for p in bq('get_cdo_properties',{'asset_path':A})['properties']}
prof=copy.deepcopy(cur['Profiles'])
T=prof['Test']

before={}
for cu in T['ControlUpdates']:
    if cu['Name']=='WorldSpace_pelvis':
        d=cu['Data']
        before=dict(d)
        d['LinearStrength']      = 0.5   # 1.0 → 0.5 : 처짐·지연 4배
        d['LinearDampingRatio']  = 0.5   # 1.0 → 0.5 : 오버슛(출렁임) 추가, 발산 없음
        d['LinearExtraDamping']  = 0.0
        d['LinearTargetVelocityMultiplier'] = 1.0   # 에너지 주입 금지 — 건드리지 말 것
print('pelvis 모디파이어(참고, 미변경):',
      [{k:round(m['Data'][k],2) for k in ('PhysicsBlendWeight','GravityMultiplier')}
       for m in T['ModifierUpdates'] if m['Name']=='pelvis'])

for tgt in ('MyProfiles','Profiles'):
    bq('set_cdo_property',{'asset_path':A,'property_name':tgt,'value':prof}); print('write',tgt,'ok')

after={p['name']:p['value'] for p in bq('get_cdo_properties',{'asset_path':A})['properties']}
def norm(o):
    if isinstance(o,bool): return o
    if isinstance(o,(int,float)): return round(float(o),4)
    if isinstance(o,dict): return {k:norm(v) for k,v in o.items()}
    if isinstance(o,list): return [norm(v) for v in o]
    return o
print('의도대로? P=',norm(prof)==norm(after['Profiles']),'/ MyP=',norm(prof)==norm(after['MyProfiles']))
print('기존 3종 무손상?',all(norm(cur['Profiles'][k])==norm(after['Profiles'][k]) for k in ('LedgeDangle','Kinematic','HookshotAir')))
t=after['Profiles']['Test']
for cu in t['ControlUpdates']:
    d=cu['Data']
    print(' [C]',cu['Name'].ljust(20),{k:round(d[k],2) for k in ('LinearStrength','LinearDampingRatio','LinearTargetVelocityMultiplier','AngularStrength')})
for mu in t['ModifierUpdates']:
    d=mu['Data']
    print(' [M]',mu['Name'].ljust(12),d['MovementType'],'PBW',round(d['PhysicsBlendWeight'],2),'G',round(d['GravityMultiplier'],2))
print('save:', ed('save_asset',{'asset_path':A})['saved'])
