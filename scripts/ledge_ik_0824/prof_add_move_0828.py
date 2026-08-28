# -*- coding: utf-8 -*-
"""LedgeDangle 정비 + LedgeDangleMove 신설 (이동 전용)
   BP 런타임 덮어쓰기를 걷어내도 동작이 유지되도록 프로파일에 실효값을 담는다."""
from mono import *
import json,glob,copy
A='/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl'
bq=lambda a,p: call('blueprint_query',a,p)
bk=sorted(glob.glob('backup_physcontrol_*.json'))[-1]
orig={p['name']:p['value'] for p in json.load(open(bk,encoding='utf-8'))['properties']}
prof=copy.deepcopy(orig['Profiles'])

def setC(p,**kw):
    for cu in p['ControlUpdates']:
        for k,v in kw.items(): cu['Data'][k]=v
def setM(p,**kw):
    for mu in p['ModifierUpdates']:
        for k,v in kw.items(): mu['Data'][k]=v

# 1) LedgeDangle = 정지용. BP 하드코딩(Damp8/Extra4)과 동일하게 맞춰 덮어쓰기 제거 대비
setC(prof['LedgeDangle'], AngularStrength=4.0, AngularDampingRatio=8.0,
     AngularExtraDamping=4.0, AngularTargetVelocityMultiplier=1.0)
setM(prof['LedgeDangle'], PhysicsBlendWeight=0.7, GravityMultiplier=0.8)

# 2) LedgeDangleMove = 이동용. 강추종 + 애님비중↑ + 중력↓
mv=copy.deepcopy(prof['LedgeDangle'])
setC(mv, AngularStrength=30.0, AngularDampingRatio=8.0,
     AngularExtraDamping=4.0, AngularTargetVelocityMultiplier=1.0)
setM(mv, PhysicsBlendWeight=0.3, GravityMultiplier=0.3)
prof['LedgeDangleMove']=mv

print('쓸 프로파일:',list(prof.keys()))
for tgt in ['MyProfiles','Profiles']:
    r=bq('set_cdo_property',{'asset_path':A,'property_name':tgt,'value':prof})
    print('  write',tgt,'ok')

after={p['name']:p['value'] for p in bq('get_cdo_properties',{'asset_path':A})['properties']}
def norm(o):
    if isinstance(o,float): return round(o,4)
    if isinstance(o,dict): return {k:norm(v) for k,v in o.items()}
    if isinstance(o,list): return [norm(v) for v in o]
    return o
print()
print('MyProfiles 키:',list(after['MyProfiles'].keys()))
print('Profiles   키:',list(after['Profiles'].keys()))
print('의도대로 기록됐나?', norm(prof)==norm(after['Profiles']), '/', norm(prof)==norm(after['MyProfiles']))
print()
CK=['AngularStrength','AngularDampingRatio','AngularExtraDamping','AngularTargetVelocityMultiplier']
MK=['MovementType','CollisionType','GravityMultiplier','PhysicsBlendWeight']
for name in ['LedgeDangle','LedgeDangleMove','Kinematic','HookshotAir']:
    b=after['Profiles'][name]
    print('==',name)
    cu=b['ControlUpdates'][0]; mu=b['ModifierUpdates'][0]
    print('   [C]',cu['Name'],{k:cu['Data'][k] for k in CK if k in cu['Data']})
    print('   [M]',mu['Name'],{k:mu['Data'][k] for k in MK if k in mu['Data']})
