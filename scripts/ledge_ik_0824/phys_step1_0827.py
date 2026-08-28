# -*- coding: utf-8 -*-
"""1단계: 이동 중 다리 추종 강화
   CF_22 Lerp.B (상수 4.0) → SelectFloat(LedgeUnitMoving ? 12 : 4)
   빈 상수 핀에 새 노드/새 연결만 추가 (기존 입력 재연결 없음)"""
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
print('EventGraph 노드', len(before['nodes']),'/ 연결',len(cb))

sel=add('CallFunction',(640,1248),function_name='SelectFloat',target_class='KismetMathLibrary')
get=add('VariableGet',(416,1312),variable_name='LedgeUnitMoving')
print('신규 노드:',sel,get)

for pin,val in [('A','12.0'),('B','4.0')]:
    r=bq('set_pin_default',P(node_id=sel,pin_name=pin,value=val))
    print('  default',pin,'=',val,'->',r.get('success',r))
for s,sp,t,tp in [(get,'LedgeUnitMoving',sel,'bPickA'), (sel,'ReturnValue','K2Node_CallFunction_22','B')]:
    r=bq('connect_pins',P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    print('  connect %s.%s -> %s.%s : %s'%(s,sp,t,tp,r.get('success',r)))

after,ca=snap()
N={n['id']:n for n in after['nodes']}
print()
print('노드',len(before['nodes']),'->',len(after['nodes']),'(신규 2개 예상)')
print('연결',len(cb),'->',len(ca))
add_c=ca-cb; rem_c=cb-ca
print('추가 연결',len(add_c)); [print('   +',x) for x in add_c]
print('사라진 연결',len(rem_c)); [print('   -',x) for x in rem_c]
print()
for p in N['K2Node_CallFunction_22']['pins']:
    if p['direction']=='input': print('  CF_22 .',p['name'],'->',p['connected_to'] or p.get('default_value'))
for p in N[sel]['pins']:
    if p['direction']=='input': print('  SelectFloat .',p['name'],'->',p['connected_to'] or p.get('default_value'))
print('※ 컴파일 미실행')
