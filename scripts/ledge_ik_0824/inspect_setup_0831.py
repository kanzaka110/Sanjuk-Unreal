# -*- coding: utf-8 -*-
import json,glob
bk=sorted(glob.glob('backup_physcontrol_*.json'))[-1]
props={p['name']:p['value'] for p in json.load(open(bk,encoding='utf-8'))['properties']}
def brief(o,d=0):
    return json.dumps(o,ensure_ascii=False)[:1500]
for k in ['CharacterSetupData','MyCharacterSetupData','AdditionalControlsAndModifiers','MyAdditionalControlsAndModifiers','AdditionalSets','InitialControlAndModifierUpdates','bUseParentCharacterSetupData','ParentAsset','PhysicsAsset']:
    v=props.get(k)
    print('='*20,k)
    print(brief(v))
    print()
