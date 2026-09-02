# -*- coding: utf-8 -*-
"""LedgeDebugs 화면 문자열에 Phy 값 6종 추가.
   기존: "HandIK aL {aL}  aR {aR}"  → CF_14(DrawDebugString).Text
   추가: BuildString_Bool/Float 선형 체인(값당 1노드)으로 뒤에 이어붙임."""
from mono import *
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'
G='LedgeDebugs'
bq=lambda a,p: call('blueprint_query',a,p)
def Q(**kw): return dict(asset_path=L, graph_name=G, **kw)
def graph():
    return {n['id']:n for n in bq('get_graph_data',{'asset_path':L,'graph_name':G})['nodes']}
def add(nt,pos,**kw):
    p=Q(node_type=nt,position=[int(pos[0]),int(pos[1])]); p.update(kw)
    rid=bq('add_node',p)['id']; N=graph()
    if rid in N: return rid
    c=[i for i,n in N.items() if n['pos']==[int(pos[0]),int(pos[1])]]   # 스테일 ID → 위치 재조회
    print('  stale',rid,'->',c); return c[-1]
def con(s,sp,t,tp):
    r=bq('connect_pins',Q(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    if not r.get('success',True): print('  CONNECT FAIL',s,sp,'->',t,tp,r)
    return r.get('success',True)
def dflt(n,pin,v):
    bq('set_pin_default',Q(node_id=n,pin_name=pin,value=v))

# (변수, BuildString 함수, 값핀, 라벨)
ITEMS=[
 ('LedgePhysWanted',    'BuildString_Bool',  'InBool',  '\nPhyW:'),
 ('LedgePhysProfileOn', 'BuildString_Bool',  'InBool',  ' On:'),
 ('LedgePhysicsActive', 'BuildString_Bool',  'InBool',  ' Act:'),
 ('LedgeDangleAlpha',   'BuildString_Double', 'InDouble', ' Dangle:'),
 ('LedgePhysAnimAlpha', 'BuildString_Double', 'InDouble', ' AnimA:'),
 ('LedgePhysicsElapsed','BuildString_Double', 'InDouble', ' Elap:'),
]
X0,Y0=-1400,900
prev=('K2Node_CallFunction_12','ReturnValue')      # 기존 문자열 체인 끝
bq('disconnect_pins',Q(node_id='K2Node_CallFunction_14',pin_name='Text'))
made=[]
for i,(var,fn,vpin,label) in enumerate(ITEMS):
    y=Y0+i*140
    b=add('CallFunction',(X0+240,y),function_name=fn,target_class='KismetStringLibrary')
    v=add('VariableGet',(X0,y),variable_name=var)
    made += [b,v]
    con(prev[0],prev[1],b,'AppendTo')
    con(v,var,b,vpin)
    dflt(b,'Prefix',label)   # Suffix 는 기본 빈 문자열 (빈 값 set_pin_default 는 거부됨)
    prev=(b,'ReturnValue')
    print(' +',var,'->',b)
con(prev[0],prev[1],'K2Node_CallFunction_14','Text')

c=bq('compile_blueprint',{'asset_path':L})
print('COMPILE ok=',c.get('success'),'err=',c.get('errors'),'warn=',c.get('warnings'))
if c.get('success'):
    try: print('save:',ed('save_asset',{'asset_path':L})['saved'])
    except Exception as e: print('save_packages:',ed('save_packages',{'packages':[L]})['results'][0]['saved'])
