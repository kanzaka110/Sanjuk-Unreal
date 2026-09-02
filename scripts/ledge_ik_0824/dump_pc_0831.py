# -*- coding: utf-8 -*-
from mono import *
import json, time
A='/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl'
bq=lambda a,p: call('blueprint_query',a,p)
r=bq('get_cdo_properties',{'asset_path':A})
ts=int(time.time())
fn='backup_physcontrol_%d.json'%ts
json.dump(r,open(fn,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('backup ->',fn)
props={p['name']:p['value'] for p in r['properties']}
print('top keys:',list(props.keys()))
for tgt in ('Profiles','MyProfiles'):
    v=props.get(tgt)
    if isinstance(v,dict): print(tgt,'profiles:',list(v.keys()))
