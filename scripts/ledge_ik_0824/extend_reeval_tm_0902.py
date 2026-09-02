# -*- coding: utf-8 -*-
"""재평가 트리거 확장 — bTransitingToNextLedge 엣지 + bTransitMoving 엣지 (9/2)
   실측: TM이 true→false 로 바뀌어도 SMS=11 유지라 챠저 재평가가 없어 MoveToIdle 이 안 나옴.
   조건: (Transiting != prevTransit) OR (TM != prevTM)
"""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
import json
bq=lambda a,p: call('blueprint_query',a,p)
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'
FN='UpdateLedgeEndReeval'
PREV_TM='bLedgeEndPrevTM'
def Q(**kw): return dict(asset_path=L, graph_name=FN, **kw)
def graph(): return {n['id']:n for n in bq('get_graph_data',{'asset_path':L,'graph_name':FN})['nodes']}
def add(nt,pos,**kw):
    p=Q(node_type=nt,position=[int(pos[0]),int(pos[1])]); p.update(kw)
    rid=bq('add_node',p)['id']; N=graph()
    if rid in N: return rid
    c=[i for i,n in N.items() if n['pos']==[int(pos[0]),int(pos[1])]]
    print('  stale',rid,'->',c); return c[-1]
def con(s,sp,t,tp):
    r=bq('connect_pins',Q(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    ok=r.get('success',True); print(('  ok   ' if ok else '  FAIL '),s,sp,'->',t,tp); return ok

have={v['name'] for v in bq('get_variables',{'asset_path':L})['variables']}
if PREV_TM not in have:
    bq('add_variable',{'asset_path':L,'name':PREV_TM,'type':'bool','category':'Custom Move|Ledge|End','default_value':'false'})
    print('add_variable',PREV_TM)

print('- 기존 NOT/AND 삭제 (Condition 링크 해제 목적)')
for nid in ['K2Node_CallFunction_0','K2Node_CallFunction_1']:
    try:
        r=bq('remove_node',Q(node_id=nid)); print('   remove',nid,r.get('success',r))
    except Exception as e: print('   remove',nid,'ERR',str(e)[:120])

print('- 신규 노드')
neq1 = add('CallFunction',(420,-120), function_name='NotEqual_BoolBool')   # Transiting != prev
gtm  = add('VariableGet',(288,120),  variable_name='bTransitMoving')
gptm = add('VariableGet',(288,190),  variable_name=PREV_TM)
neq2 = add('CallFunction',(420,140), function_name='NotEqual_BoolBool')    # TM != prevTM
orn  = add('CallFunction',(560,-40), function_name='BooleanOR')
sptm = add('VariableSet',(900,48),   variable_name=PREV_TM)
print('  neq1',neq1,'neq2',neq2,'or',orn,'setPrevTM',sptm)

print('- 배선')
con('K2Node_BreakStruct_0','bTransitingToNextLedge',neq1,'A')
con('K2Node_VariableGet_1','bLedgeEndPrevTransit',neq1,'B')
con(gtm,'bTransitMoving',neq2,'A')
con(gptm,PREV_TM,neq2,'B')
con(neq1,'ReturnValue',orn,'A')
con(neq2,'ReturnValue',orn,'B')
con(orn,'ReturnValue','K2Node_IfThenElse_0','Condition')
# prevTM 갱신을 기존 prevTransit 갱신 뒤에 직렬
con('K2Node_VariableSet_0','then',sptm,'execute')
con(gtm,'bTransitMoving',sptm,PREV_TM)

print('- 컴파일')
r=bq('compile_blueprint',{'asset_path':L})
print('  success',r.get('success'),'errors',r.get('error_count'),'warnings',r.get('warning_count'))
for e in (r.get('errors') or [])[:5]: print('   ',str(e)[:160])
