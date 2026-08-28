# -*- coding: utf-8 -*-
"""1b단계: 이동 중 Strength 하한
   CF_22 Lerp.A (상수 0.0) → SelectFloat(LedgeUnitMoving ? 5 : 0)
   이동 애님 ledgephysanimalpha 커브가 t=0~0.25s 구간 0 → Strength 0(순수 랙돌) 되는 것 방지"""
from mono import *
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'; G='EventGraph'
bq=lambda a,p: call('blueprint_query',a,p)
P=lambda **k: dict(asset_path=L,graph_name=G,**k)
def snap():
    d=bq('get_graph_data',{'asset_path':L,'graph_name':G})
    s=set()
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
    c=[i for i,n in N.items() if n['pos']==pos]; print('  stale->',c); return c[-1]

before,cb=snap()
print('EventGraph 노드',len(before['nodes']),'/ 연결',len(cb))
sel=add('CallFunction',(640,1408),function_name='SelectFloat',target_class='KismetMathLibrary')
get=add('VariableGet',(416,1472),variable_name='LedgeUnitMoving')
print('신규:',sel,get)
for pin,val in [('A','5.0'),('B','0.0')]:
    print('  default',pin,'=',val,'->',bq('set_pin_default',P(node_id=sel,pin_name=pin,value=val)).get('success'))
for s,sp,t,tp in [(get,'LedgeUnitMoving',sel,'bPickA'), (sel,'ReturnValue','K2Node_CallFunction_22','A')]:
    print('  connect %s.%s -> %s.%s : %s'%(s,sp,t,tp,bq('connect_pins',P(source_node=s,source_pin=sp,target_node=t,target_pin=tp)).get('success')))

after,ca=snap(); N={n['id']:n for n in after['nodes']}
print()
print('노드',len(before['nodes']),'->',len(after['nodes']),'| 연결',len(cb),'->',len(ca))
print('추가',len(ca-cb)); [print('   +',x) for x in ca-cb]
print('삭제',len(cb-ca)); [print('   -',x) for x in cb-ca]
print()
for p in N['K2Node_CallFunction_22']['pins']:
    if p['direction']=='input': print('  CF_22 .',p['name'],'->',p['connected_to'] or p.get('default_value'))
for p in N[sel]['pins']:
    if p['direction']=='input': print('  새 SelectFloat .',p['name'],'->',p['connected_to'] or p.get('default_value'))
print('※ 컴파일 미실행')
