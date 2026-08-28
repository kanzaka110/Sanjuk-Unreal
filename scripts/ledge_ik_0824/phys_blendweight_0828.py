# -*- coding: utf-8 -*-
"""승호 제안: 모션 연결 구간에 모션 0 / 피직스 100
   BW = Lerp(1.0, 0.7, LedgePhysAnimAlpha)   ← alpha 0(전환구간)=1.0, alpha 1(안정)=0.7
   SetBodyModifierPhysicsBlendWeight("LegLeft"/"LegRight", BW)  ← CF_21.then 뒤에 이어붙임
   + Strength 하한/상한 복원 (스프링 필터가 작동하려면 추종력 필요)"""
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
    c=[i for i,n in N.items() if n['pos']==pos]; print('  stale->',c); return c[-1]
def con(s,sp,t,tp):
    r=bq('connect_pins',P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    print(('  OK  ' if r.get('success',True) else '  FAIL')+' %s.%s -> %s.%s'%(s,sp,t,tp))
def dflt(n,pin,v):
    print('  default %s.%s = %s -> %s'%(n,pin,v,bq('set_pin_default',P(node_id=n,pin_name=pin,value=v)).get('success')))

before,cb=snap(); N0={n['id']:n for n in before['nodes']}
print('시작 노드',len(before['nodes']),'/ 연결',len(cb))
# 프로브 잔여 CF_28 (고립) 제거 후 정위치 재생성
if 'K2Node_CallFunction_28' in N0 and not any(p['connected_to'] for p in N0['K2Node_CallFunction_28']['pins']):
    bq('remove_node',P(node_id='K2Node_CallFunction_28')); print('  프로브 CF_28 삭제')
base=N0['K2Node_CallFunction_21']['pos']; print('  CF_21 pos',base)

print('== 노드 생성 ==')
bwL=add('CallFunction',(base[0]+320,base[1]),function_name='SetBodyModifierPhysicsBlendWeight',target_class='PhysicsControlComponent')
bwR=add('CallFunction',(base[0]+640,base[1]),function_name='SetBodyModifierPhysicsBlendWeight',target_class='PhysicsControlComponent')
lerp=add('CallFunction',(base[0]+160,base[1]+240),function_name='Lerp',target_class='KismetMathLibrary')
getA=add('VariableGet',(base[0]-40,base[1]+300),variable_name='LedgePhysAnimAlpha')
print('  ',bwL,bwR,lerp,getA)

print('== 기본값 ==')
dflt(lerp,'A','1.0'); dflt(lerp,'B','0.7')
dflt(bwL,'Name','LegLeft'); dflt(bwR,'Name','LegRight')

print('== 배선 ==')
con('K2Node_CallFunction_21','then',bwL,'execute')
con(bwL,'then',bwR,'execute')
con('K2Node_CallFunction_26','ReturnValue',bwL,'self')
con('K2Node_CallFunction_26','ReturnValue',bwR,'self')
con(getA,'LedgePhysAnimAlpha',lerp,'Alpha')
con(lerp,'ReturnValue',bwL,'PhysicsBlendWeight')
con(lerp,'ReturnValue',bwR,'PhysicsBlendWeight')

print('== Strength 복원 (스프링 필터용) ==')
dflt('K2Node_CallFunction_14','A','12.0')   # 이동 중 상한
dflt('K2Node_CallFunction_20','A','10.0')   # 이동 중 하한

after,ca=snap(); N={n['id']:n for n in after['nodes']}
print()
print('노드',len(before['nodes']),'->',len(after['nodes']),'| 연결',len(cb),'->',len(ca))
print('추가연결',len(ca-cb),' 삭제연결',len(cb-ca))
for x in sorted(cb-ca): print('   -',x)
print()
for i,lab in [(bwL,'BW_Left'),(bwR,'BW_Right'),(lerp,'Lerp')]:
    print(' ',lab,{p['name']:(p['connected_to'] or p.get('default_value')) for p in N[i]['pins'] if p['direction']=='input' and p['name']!='execute'})
print('※ 컴파일 미실행')
