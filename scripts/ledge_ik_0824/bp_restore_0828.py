# -*- coding: utf-8 -*-
"""BP를 오전(프로파일 실험 이전) 상태로 복원. PhysicControl 롤백에 맞춤."""
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
print('시작 노드',len(before['nodes']),'/ 연결',len(cb))

print('== 1) 프로파일 전환 노드 제거 ==')
for i in ['K2Node_CallFunction_46','K2Node_CallFunction_47','K2Node_IfThenElse_2','K2Node_IfThenElse_7',
          'K2Node_CallFunction_45','K2Node_VariableSet_11','K2Node_VariableGet_20','K2Node_VariableGet_21',
          'K2Node_VariableGet_22','K2Node_VariableGet_23']:
    if i in N0:
        try: bq('remove_node',P(node_id=i)); print('   삭제',i)
        except Exception as e: print('   실패',i,str(e)[:60])

print('== 2) 내가 추가한 SelectFloat / BW Lerp 제거 ==')
for i in ['K2Node_CallFunction_14','K2Node_CallFunction_20','K2Node_CallFunction_39',
          'K2Node_VariableGet_1','K2Node_VariableGet_7','K2Node_VariableGet_12']:
    if i in N0:
        try: bq('remove_node',P(node_id=i)); print('   삭제',i)
        except Exception as e: print('   실패',i,str(e)[:60])

print('== 3) Strength Lerp 상수 복원 (A=0, B=4) ==')
dflt('K2Node_CallFunction_22','A','0.0'); dflt('K2Node_CallFunction_22','B','4.0')

print('== 4) SetControlAngularData 2개 복원 ==')
base=[1232,832]
aL=add('CallFunction',(base[0],base[1]),function_name='SetControlAngularData',target_class='PhysicsControlComponent')
aR=add('CallFunction',(base[0]+368,base[1]),function_name='SetControlAngularData',target_class='PhysicsControlComponent')
for n,nm in [(aL,'ParentSpace_LegLeft'),(aR,'ParentSpace_LegRight')]:
    dflt(n,'Name',nm); dflt(n,'DampingRatio','8.0'); dflt(n,'ExtraDamping','4.0'); dflt(n,'MaxTorque','0.0')
con('K2Node_IfThenElse_6','then',aL,'execute')
con(aL,'then',aR,'execute')
con('K2Node_CallFunction_26','ReturnValue',aL,'self')
con('K2Node_CallFunction_26','ReturnValue',aR,'self')
con('K2Node_CallFunction_22','ReturnValue',aL,'Strength')
con('K2Node_CallFunction_22','ReturnValue',aR,'Strength')

after,ca=snap(); N={n['id']:n for n in after['nodes']}
print()
print('노드',len(before['nodes']),'->',len(after['nodes']),'| 연결',len(cb),'->',len(ca))
print()
print('=== 최종 물리 체인 ===')
for i in [aL,aR]:
    print('  %s %s'%(i,{p['name']:(p['connected_to'] or p.get('default_value')) for p in N[i]['pins'] if p['direction']=='input' and p['name'] in ('Name','Strength','DampingRatio','ExtraDamping')}))
print('  Strength Lerp:',{p['name']:(p['connected_to'] or p.get('default_value')) for p in N['K2Node_CallFunction_22']['pins'] if p['direction']=='input'})
print('=== 프로파일 호출 (LedgeDangle/Kinematic 만 남아야) ===')
for n in after['nodes']:
    if 'Enable Profile' in n['title'].replace(chr(10),' ') or 'Disable Profile' in n['title'].replace(chr(10),' '):
        print('  %s %s'%(n['id'],[p.get('default_value') for p in n['pins'] if p['name']=='InProfileName']))
print('※ 컴파일 미실행')
