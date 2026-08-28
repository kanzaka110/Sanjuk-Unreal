# -*- coding: utf-8 -*-
"""fix_edgetick_0827.py 전량 롤백 — 8/25 저장 상태로 원복"""
from mono import *
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'; FN='Ledge_HandTargetA'
bq=lambda a,p: call('blueprint_query',a,p)
P=lambda **k: dict(asset_path=L,graph_name=FN,**k)
def graph(): return {n['id']:n for n in bq('get_graph_data',{'asset_path':L,'graph_name':FN})['nodes']}
def add(nt,pos,**kw):
    pos=[int(pos[0]),int(pos[1])]
    p=P(node_type=nt,position=pos); p.update(kw)
    rid=bq('add_node',p)['id']; N=graph()
    if rid in N: return rid
    c=[i for i,n in N.items() if n['pos']==pos]; print('  stale->',c); return c[-1]
def con(s,sp,t,tp):
    r=bq('connect_pins',P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    print(('  OK  ' if r.get('success',True) else '  FAIL')+f' {s}.{sp} -> {t}.{tp}')
def dis(s,sp,t,tp):
    try:
        r=bq('disconnect_pins',P(source_node=s,source_pin=sp,target_node=t,target_pin=tp)); print('  dis',s,'->',t,r.get('success',r))
    except Exception as e: print('  dis ERR',str(e)[:120])
def rm(i):
    N=graph()
    if i in N: bq('remove_node',P(node_id=i)); print('  삭제',i)
    else: print('  없음',i)

print('=== 1) 엣지틱 Set HandWorld 제거 (처방 3) ===')
dis('K2Node_VariableSet_18','then','K2Node_VariableSet_26','execute')
dis('K2Node_VariableSet_26','then','K2Node_VariableSet_27','execute')
dis('K2Node_VariableGet_46','LedgeA_FromL','K2Node_VariableSet_26','LedgeHandWorldL')
dis('K2Node_VariableGet_47','LedgeA_FromR','K2Node_VariableSet_27','LedgeHandWorldR')
for i in ('K2Node_VariableSet_26','K2Node_VariableSet_27','K2Node_VariableGet_46','K2Node_VariableGet_47'): rm(i)

print('=== 2) From 소스 원복 (처방 2) ===')
dis('K2Node_VariableGet_44','LedgeA_PrevHandL','K2Node_VariableSet_12','LedgeA_FromL')
dis('K2Node_VariableGet_45','LedgeA_PrevHandR','K2Node_VariableSet_13','LedgeA_FromR')
for i in ('K2Node_VariableGet_44','K2Node_VariableGet_45'): rm(i)
gL=add('VariableGet',(256,-32),variable_name='LedgeHandWorldL')
gR=add('VariableGet',(464,-64),variable_name='LedgeHandWorldR')
con(gL,'LedgeHandWorldL','K2Node_VariableSet_12','LedgeA_FromL')
con(gR,'LedgeHandWorldR','K2Node_VariableSet_13','LedgeA_FromR')

print('=== 3) 진입부 캡처 제거 (처방 1) ===')
dis('K2Node_FunctionEntry_0','then','K2Node_VariableSet_24','execute')
dis('K2Node_VariableSet_24','then','K2Node_VariableSet_25','execute')
dis('K2Node_VariableSet_25','then','K2Node_IfThenElse_0','execute')
dis('K2Node_VariableGet_38','LedgeHandWorldL','K2Node_VariableSet_24','LedgeA_PrevHandL')
dis('K2Node_VariableGet_43','LedgeHandWorldR','K2Node_VariableSet_25','LedgeA_PrevHandR')
for i in ('K2Node_VariableSet_24','K2Node_VariableSet_25','K2Node_VariableGet_38','K2Node_VariableGet_43'): rm(i)
con('K2Node_FunctionEntry_0','then','K2Node_IfThenElse_0','execute')

print('=== 4) 변수 제거 ===')
ex={v['name'] for v in bq('get_variables',{'asset_path':L})['variables']}
for n in ('LedgeA_PrevHandL','LedgeA_PrevHandR'):
    if n in ex: bq('remove_variable',{'asset_path':L,'name':n}); print('  변수삭제',n)

print('=== 5) 컴파일 ===')
r=bq('compile_blueprint',{'asset_path':L})
print('  ',{k:r[k] for k in ('success','error_count','warning_count') if k in r})
if r.get('errors'): print('  errors:',r['errors'][:5])
print('  노드수',len(graph()))
