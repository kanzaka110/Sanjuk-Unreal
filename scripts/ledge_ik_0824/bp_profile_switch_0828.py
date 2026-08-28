# -*- coding: utf-8 -*-
"""BP: 런타임 덮어쓰기 제거 → 프로파일 전환으로 교체
   삭제: SetControlAngularData x2, SetBodyModifierPhysicsBlendWeight x2
   추가: LedgeUnitMoving 엣지에서 EnableProfile(LedgeDangleMove / LedgeDangle)"""
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
base=N0['K2Node_CallFunction_19']['pos']

print('== 1) 변수 추가 ==')
ex={v['name'] for v in bq('get_variables',{'asset_path':L})['variables']}
if 'LedgePhysMoveOn' not in ex:
    bq('add_variable',{'asset_path':L,'name':'LedgePhysMoveOn','type':'bool','category':'Ledge|Phys'}); print('  추가 LedgePhysMoveOn')
else: print('  이미 있음')

print('== 2) 런타임 덮어쓰기 노드 삭제 ==')
for i in ['K2Node_CallFunction_19','K2Node_CallFunction_21','K2Node_CallFunction_37','K2Node_CallFunction_38']:
    bq('remove_node',P(node_id=i)); print('  삭제',i)

print('== 3) 프로파일 전환 로직 ==')
ne  = add('CallFunction',(base[0],base[1]-160),function_name='NotEqual_BoolBool',target_class='KismetMathLibrary')
gM1 = add('VariableGet',(base[0]-260,base[1]-140),variable_name='LedgeUnitMoving')
gM2 = add('VariableGet',(base[0]-260,base[1]-80),variable_name='LedgePhysMoveOn')
brA = add('Branch',(base[0]+220,base[1]))
gM3 = add('VariableGet',(base[0]+40,base[1]+120),variable_name='LedgeUnitMoving')
brB = add('Branch',(base[0]+460,base[1]))
epM = add('CallFunction',(base[0]+700,base[1]-80),function_name='EnableProfile',target_class='SBCharacterPhysicsFeature')
epI = add('CallFunction',(base[0]+700,base[1]+140),function_name='EnableProfile',target_class='SBCharacterPhysicsFeature')
setO= add('VariableSet',(base[0]+1000,base[1]),variable_name='LedgePhysMoveOn')
gM4 = add('VariableGet',(base[0]+860,base[1]+120),variable_name='LedgeUnitMoving')
print('  노드:',ne,brA,brB,epM,epI,setO)

for n,pn,v in [(epM,'InProfileName','LedgeDangleMove'),(epM,'InBlendInTime','0.2'),(epM,'InBlendOutTime','0.2'),
               (epI,'InProfileName','LedgeDangle'),(epI,'InBlendInTime','0.2'),(epI,'InBlendOutTime','0.2')]:
    dflt(n,pn,v)

con(gM1,'LedgeUnitMoving',ne,'A'); con(gM2,'LedgePhysMoveOn',ne,'B')
con(ne,'ReturnValue',brA,'Condition')
con('K2Node_IfThenElse_6','then',brA,'execute')
con(gM3,'LedgeUnitMoving',brB,'Condition')
con(brA,'then',brB,'execute')
con(brB,'then',epM,'execute'); con(brB,'else',epI,'execute')
con('K2Node_CallFunction_25','ReturnValue',epM,'self'); con('K2Node_CallFunction_25','ReturnValue',epI,'self')
con(epM,'then',setO,'execute'); con(epI,'then',setO,'execute')
con(gM4,'LedgeUnitMoving',setO,'LedgePhysMoveOn')

after,ca=snap(); N={n['id']:n for n in after['nodes']}
print()
print('노드',len(before['nodes']),'->',len(after['nodes']),'| 연결',len(cb),'->',len(ca))
print('사라진 연결',len(cb-ca),' 새 연결',len(ca-cb))
print()
print('=== 프로파일 전환 3종 ===')
for i in ['K2Node_CallFunction_60','K2Node_CallFunction_18',epM,epI]:
    if i in N: print('  %-24s %s'%(i,{p['name']:p.get('default_value') for p in N[i]['pins'] if p['name'] in ('InProfileName','InBlendInTime','InBlendOutTime')}))
print('※ 컴파일 미실행')
