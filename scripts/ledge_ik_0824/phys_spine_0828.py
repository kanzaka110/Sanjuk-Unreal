# -*- coding: utf-8 -*-
"""상체(Spine 림, bIncludeParentBone=true 라 골반 포함)까지 피직스 확대.
   CF_38.then 뒤에 이어붙임:
     SetBodyModifierMovementType("Spine", Simulated)
     SetControlAngularData("ParentSpace_Spine", 다리와 동일 Strength, Damp 8, Extra 4)
     SetBodyModifierPhysicsBlendWeight("Spine", SpineBW = Lerp(0.6, 0.4, alpha))
   Spine BW 를 다리(1.0/0.7)보다 낮게 잡는 이유 = PBIK 손 이펙터 보호"""
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
base=N0['K2Node_CallFunction_38']['pos']
print('시작 노드',len(before['nodes']),'/ 연결',len(cb),'| CF_38 pos',base)

print('== MovementType 함수 확인 ==')
mt=None
for fn in ['SetBodyModifierMovementType','SetBodyModifiersMovementType']:
    try:
        mt=add('CallFunction',(base[0]+320,base[1]),function_name=fn,target_class='PhysicsControlComponent')
        print('  사용:',fn,'->',mt); mtfn=fn; break
    except Exception as e: print('  없음',fn,'|',str(e)[:70])

ang=add('CallFunction',(base[0]+640,base[1]),function_name='SetControlAngularData',target_class='PhysicsControlComponent')
bw =add('CallFunction',(base[0]+960,base[1]),function_name='SetBodyModifierPhysicsBlendWeight',target_class='PhysicsControlComponent')
lerp=add('CallFunction',(base[0]+780,base[1]+240),function_name='Lerp',target_class='KismetMathLibrary')
getA=add('VariableGet',(base[0]+600,base[1]+300),variable_name='LedgePhysAnimAlpha')
print('  노드:',mt,ang,bw,lerp,getA)

print('== 기본값 ==')
nm='Names' if mtfn.startswith('SetBodyModifiers') else 'Name'
if nm=='Name': dflt(mt,'Name','Spine')
else: print('  ! 복수형이라 Names 배열은 수동 필요')
dflt(ang,'Name','ParentSpace_Spine'); dflt(ang,'DampingRatio','8.0'); dflt(ang,'ExtraDamping','4.0'); dflt(ang,'MaxTorque','0.0')
dflt(bw,'Name','Spine')
dflt(lerp,'A','0.6'); dflt(lerp,'B','0.4')

print('== 배선 ==')
con('K2Node_CallFunction_38','then',mt,'execute')
con(mt,'then',ang,'execute')
con(ang,'then',bw,'execute')
for n in (mt,ang,bw): con('K2Node_CallFunction_26','ReturnValue',n,'self')
con('K2Node_CallFunction_22','ReturnValue',ang,'Strength')   # 다리와 동일 Strength 공유
con(getA,'LedgePhysAnimAlpha',lerp,'Alpha')
con(lerp,'ReturnValue',bw,'PhysicsBlendWeight')

after,ca=snap(); N={n['id']:n for n in after['nodes']}
print()
print('노드',len(before['nodes']),'->',len(after['nodes']),'| 연결',len(cb),'->',len(ca))
print('추가',len(ca-cb),' 삭제',len(cb-ca))
for x in sorted(cb-ca): print('   -',x)
print()
for i,l in [(mt,'MovementType'),(ang,'AngularData'),(bw,'BlendWeight'),(lerp,'SpineLerp')]:
    print(' ',l,{p['name']:(p['connected_to'] or p.get('default_value')) for p in N[i]['pins'] if p['direction']=='input' and p['name']!='execute'})
print('※ 컴파일 미실행')
