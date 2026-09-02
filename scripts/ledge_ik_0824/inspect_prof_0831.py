# -*- coding: utf-8 -*-
import json,glob
bk=sorted(glob.glob('backup_physcontrol_*.json'))[-1]
props={p['name']:p['value'] for p in json.load(open(bk,encoding='utf-8'))['properties']}
P=props['Profiles']
for name in P:
    b=P[name]
    print('='*60); print('PROFILE:',name,'| keys:',list(b.keys()))
    for cu in b.get('ControlUpdates',[]):
        print('  [C]',cu.get('Name'),'| Names:',cu.get('Names'),'| Set:',cu.get('Set'))
        print('      Data:',json.dumps(cu.get('Data'),ensure_ascii=False)[:400])
    for mu in b.get('ModifierUpdates',[]):
        print('  [M]',mu.get('Name'),'| Names:',mu.get('Names'),'| Set:',mu.get('Set'))
        print('      Data:',json.dumps(mu.get('Data'),ensure_ascii=False)[:400])
