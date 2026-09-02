# -*- coding: utf-8 -*-
"""Test v5 — 골반 극단화(승호 지시: '아예 날아갈 정도').
   골반 관련 값만 건드린다. 팔 8종 Kinematic(손 IK)·다리·상체는 그대로."""
from mono import *
import copy
A='/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl'
bq=lambda a,p: call('blueprint_query',a,p)
cur={p['name']:p['value'] for p in bq('get_cdo_properties',{'asset_path':A})['properties']}
prof=copy.deepcopy(cur['Profiles']); T=prof['Test']

for cu in T['ControlUpdates']:
    if cu['Name']=='WorldSpace_pelvis':
        d=cu['Data']
        d['LinearStrength']     = 0.1   # 0.5 → 0.1 : 사실상 무구속(처짐 25배)
        d['LinearDampingRatio'] = 0.1   # 무감쇠
        d['LinearExtraDamping'] = 0.0
        d['LinearTargetVelocityMultiplier'] = 3.0   # 에너지 주입 → 발산(= 날아감)
for mu in T['ModifierUpdates']:
    if mu['Name']=='pelvis':
        mu['Data']['GravityMultiplier']  = 2.0   # 0.2 → 2.0
        mu['Data']['PhysicsBlendWeight'] = 1.0

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
    if cu['Name']=='WorldSpace_pelvis':
        d=cu['Data']; print(' [C]',cu['Name'],{k:round(d[k],2) for k in ('LinearStrength','LinearDampingRatio','LinearExtraDamping','LinearTargetVelocityMultiplier','AngularStrength')})
for mu in t['ModifierUpdates']:
    d=mu['Data']; print(' [M]',mu['Name'].ljust(12),d['MovementType'],'PBW',round(d['PhysicsBlendWeight'],2),'G',round(d['GravityMultiplier'],2))
print('save:', ed('save_packages',{'packages':[A]})['results'][0]['saved'])
