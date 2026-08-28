# -*- coding: utf-8 -*-
"""이동 중 물리 프로파일 매 틱 재적용 (C++ 이 꺼도 즉시 복구)
   CF_21.then -> Branch(LedgeUnitMoving) -> EnableProfile("LedgeDangle", BlendIn 0)"""
from mono import *
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'; G='EventGraph'
bq=lambda a,p: call('blueprint_query',a,p)
P=lambda **k: dict(asset_path=L,graph_name=G,**k)
def snap():
    d=bq('get_graph_data',{'asset_path':L,'graph_name':G}); s=set()
    for n in d['nodes']:
        for p in n['pins']:
            if p['direction']=='output':
                for c in p['connected_to']: s.add((n['id'],p['name'],c))
    return d,s
def add(nt,pos,**kw):
    pos=[int(pos[0]),int(pos[1])]
    p=P(node_type=nt,position=pos); p.update(kw)
    rid=bq('add_node',p)['id']
    d,_=snap(); N={n['id']:n for n in d['nodes']}
    if rid in N: return rid
    c=[i for i,n in N.items() if n['pos']==pos]; return c[-1]
def con(s,sp,t,tp):
    r=bq('connect_pins',P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    print(('  OK  ' if r.get('success',True) else '  FAIL')+' %s.%s -> %s.%s'%(s,sp,t,tp))
def dflt(n,pin,v): bq('set_pin_default',P(node_id=n,pin_name=pin,value=v))

before,cb=snap(); N0={n['id']:n for n in before['nodes']}
base=N0['K2Node_CallFunction_21']['pos']
print('시작 노드',len(before['nodes']),'/ 연결',len(cb))
br  = add('Branch',(base[0]+320,base[1]))
gUM = add('VariableGet',(base[0]+120,base[1]+140),variable_name='LedgeUnitMoving')
ep  = add('CallFunction',(base[0]+560,base[1]),function_name='EnableProfile',target_class='SBCharacterPhysicsFeature')
print('신규:',br,gUM,ep)
dflt(ep,'InProfileName','LedgeDangle'); dflt(ep,'InBlendInTime','0.0'); dflt(ep,'InBlendOutTime','0.0')
con('K2Node_CallFunction_21','then',br,'execute')
con(gUM,'LedgeUnitMoving',br,'Condition')
con(br,'then',ep,'execute')
con('K2Node_CallFunction_25','ReturnValue',ep,'self')
after,ca=snap(); N={n['id']:n for n in after['nodes']}
print()
print('노드',len(before['nodes']),'->',len(after['nodes']),'| 연결',len(cb),'->',len(ca))
print('추가',len(ca-cb),' 삭제',len(cb-ca))
print()
print('EnableProfile 입력:',{p['name']:(p['connected_to'] or p.get('default_value')) for p in N[ep]['pins'] if p['direction']=='input'})
print('Branch 조건:',{p['name']:(p['connected_to'] or p.get('default_value')) for p in N[br]['pins'] if p['name']=='Condition'})
