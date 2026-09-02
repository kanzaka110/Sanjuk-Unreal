# -*- coding: utf-8 -*-
"""Test 프로파일 v3 — 손 IK 고정 추가.
   문제: Spine 림(StartBone=spine_01, bIncludeParentBone=true)이 팔·손까지 삼켜 Simulated →
         CR 손 IK 결과가 물리 블렌드에 덮여 손이 렛지에서 떨어짐.
   처방: 8/28 실측 구조 — 팔 체인을 '개별 바디 이름' 모디파이어로 Kinematic(PBW 0) 덮어쓰기.
         모디파이어 배열은 뒤가 이기므로 반드시 Spine 뒤에 배치."""
from mono import *
import copy
A='/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl'
bq=lambda a,p: call('blueprint_query',a,p)

cur={p['name']:p['value'] for p in bq('get_cdo_properties',{'asset_path':A})['properties']}
prof=copy.deepcopy(cur['Profiles'])
MT=copy.deepcopy(prof['LedgeDangle']['ModifierUpdates'][0]['Data'])
def M(name,**kw):
    d=copy.deepcopy(MT); d.update(kw); return {'Name':name,'Data':d}

ARMS=['clavicle_l','upperarm_l','lowerarm_l','hand_l',
      'clavicle_r','upperarm_r','lowerarm_r','hand_r']
KIN=dict(MovementType='Kinematic', CollisionType='QueryAndPhysics',
         PhysicsBlendWeight=0.0, GravityMultiplier=0.0)

mu=[m for m in prof['Test']['ModifierUpdates'] if m['Name'] not in ARMS]
mu += [M(b, **KIN) for b in ARMS]          # ← 반드시 맨 뒤(뒤가 이김)
prof['Test']['ModifierUpdates']=mu

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
print('적용 순서 (뒤가 이김):')
for m in after['Profiles']['Test']['ModifierUpdates']:
    d=m['Data']; print('  ',m['Name'].ljust(12),d['MovementType'],'PBW',round(d['PhysicsBlendWeight'],2),'G',round(d['GravityMultiplier'],2))
print('save:', ed('save_asset',{'asset_path':A})['saved'])
