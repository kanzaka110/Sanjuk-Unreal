# -*- coding: utf-8 -*-
"""신규 함수 LedgePhysDebugs — Phy 값 전용 디버그 문자열.
   LedgeDebugs 는 건드리지 않고, LedgeIK 의 LedgeDebugs 호출 바로 뒤에 물린다.
   게이트 = LedgeDebug 변수. 위치는 MeshLocation +Z40 (기존 디버그와 겹침 방지)."""
from mono import *
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'
FN='LedgePhysDebugs'
bq=lambda a,p: call('blueprint_query',a,p)
def Q(**kw): return dict(asset_path=L, graph_name=FN, **kw)
def graph(g=FN): return {n['id']:n for n in bq('get_graph_data',{'asset_path':L,'graph_name':g})['nodes']}
def add(nt,pos,**kw):
    p=Q(node_type=nt,position=[int(pos[0]),int(pos[1])]); p.update(kw)
    rid=bq('add_node',p)['id']; N=graph()
    if rid in N: return rid
    c=[i for i,n in N.items() if n['pos']==[int(pos[0]),int(pos[1])]]
    print('  stale',rid,'->',c); return c[-1]
def con(s,sp,t,tp):
    r=bq('connect_pins',Q(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    if not r.get('success',True): print('  CONNECT FAIL',s,sp,'->',t,tp,r)
def dflt(n,pin,v): bq('set_pin_default',Q(node_id=n,pin_name=pin,value=v))

# 1) 함수 생성
try:
    r=bq('add_function',{'asset_path':L,'function_name':FN,'category':'디버그'}); print('add_function',r.get('success',r))
except Exception as e:
    print('add_function:',str(e)[:200])
N=graph(); entry=[i for i,n in N.items() if 'FunctionEntry' in n['class']][0]
print('entry',entry)

# 2) 게이트
gv  = add('VariableGet',(-900,300), variable_name='LedgeDebug')
br  = add('Branch',(-650,180))
con(entry,'then',br,'execute'); con(gv,'LedgeDebug',br,'Condition')

# 3) 문자열 체인
ITEMS=[('LedgePhysWanted','BuildString_Bool','InBool','W:'),
       ('LedgePhysProfileOn','BuildString_Bool','InBool',' On:'),
       ('LedgePhysicsActive','BuildString_Bool','InBool',' Act:'),
       ('LedgeDangleAlpha','BuildString_Double','InDouble',' Dangle:'),
       ('LedgePhysAnimAlpha','BuildString_Double','InDouble',' AnimA:'),
       ('LedgePhysicsElapsed','BuildString_Double','InDouble',' Elap:')]
prev=None
for i,(var,fn,vpin,label) in enumerate(ITEMS):
    y=600+i*140
    b=add('CallFunction',(-650,y),function_name=fn,target_class='KismetStringLibrary')
    v=add('VariableGet',(-950,y),variable_name=var)
    con(v,var,b,vpin); dflt(b,'Prefix',label)
    if prev: con(prev,'ReturnValue',b,'AppendTo')
    else:    dflt(b,'AppendTo','PHY ')
    prev=b; print(' +',var,'->',b)

# 4) 표시 위치 = MeshLocation + (0,0,40)
ml  = add('VariableGet',(-950,420), variable_name='MeshLocation')
mkv = add('CallFunction',(-900,480), function_name='MakeVector', target_class='KismetMathLibrary')
for ax,val in (('X','0.0'),('Y','0.0'),('Z','40.0')): dflt(mkv,ax,val)
addv= add('CallFunction',(-750,440), function_name='Add_VectorVector', target_class='KismetMathLibrary')
con(ml,'MeshLocation',addv,'A'); con(mkv,'ReturnValue',addv,'B')

# 5) DrawDebugString
dds = add('CallFunction',(-400,180), function_name='DrawDebugString', target_class='KismetSystemLibrary')
con(br,'then',dds,'execute')
con(addv,'ReturnValue',dds,'TextLocation')
con(prev,'ReturnValue',dds,'Text')
dflt(dds,'TextColor','(R=1.000000,G=0.550000,B=0.100000,A=1.000000)')
dflt(dds,'Duration','0.000000')

c=bq('compile_blueprint',{'asset_path':L}); print('COMPILE',c.get('success'),c.get('errors'),c.get('warnings'))
