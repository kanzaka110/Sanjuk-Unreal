# -*- coding: utf-8 -*-
"""렛지 End 재평가 강제 — 레이어 UpdateLedgeEndReeval 배선 (9/2)
   bTransitingToNextLedge 의 false→true 엣지에서
   메인 ABP(As SBCharacterABP).SetStateMachineBlendStackAnim(bForceBlend=true, State=11) 호출
   → 챠저 재평가 → Exit 조건에 맞는 End 행 선택.
   ※ 트리거를 넓게(전이 전반) 잡아도 되는 이유: 행 조건이 이미 정확해 챠저가 올바른 행을 고른다."""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
import json
bq=lambda a,p: call('blueprint_query',a,p)
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'
FN='UpdateLedgeEndReeval'
PREV='bLedgeEndPrevTransit'
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
    ok=r.get('success',True)
    print(('  ok   ' if ok else '  FAIL '),s,sp,'->',t,tp)
    return ok
def dflt(n,pin,v): bq('set_pin_default',Q(node_id=n,pin_name=pin,value=v))

# 0) 엣지용 변수
have={v['name'] for v in bq('get_variables',{'asset_path':L})['variables']}
if PREV not in have:
    bq('add_variable',{'asset_path':L,'name':PREV,'type':'bool','category':'Custom Move|Ledge|End','default_value':'false'})
    print('add_variable',PREV)

N=graph()
entry=[i for i,n in N.items() if 'FunctionEntry' in n['class']][0]
GET='K2Node_VariableGet_0'; BRK='K2Node_BreakStruct_0'
print('entry',entry)

print('- 노드 생성')
seq  = add('ExecutionSequence',(100,0))
gprev= add('VariableGet',(-500,260), variable_name=PREV)
nt   = add('CallFunction',(-280,260), function_name='Not_PreBool')
ab   = add('CallFunction',(-100,140), function_name='BooleanAND')
br   = add('Branch',(420,0))
gabp = add('VariableGet',(420,300), variable_name='As SBCharacterABP')
callf= add('CallFunction',(700,140), function_name='SetStateMachineBlendStackAnim', target_class='PC_01_ABP_C')
sprev= add('VariableSet',(700,420), variable_name=PREV)
print(' seq',seq,'not',nt,'and',ab,'br',br,'call',callf,'setprev',sprev)

print('- 순수 체인')
con(GET,'LedgeMoveData',BRK,'SBLedgeMoveData')
con(gprev,PREV,nt,'A')
con(nt,'ReturnValue',ab,'A')
con(BRK,'bTransitingToNextLedge',ab,'B')
con(ab,'ReturnValue',br,'Condition')
con(gabp,'As SBCharacterABP',callf,'self')
con(BRK,'bTransitingToNextLedge',sprev,PREV)

print('- exec')
con(entry,'then',seq,'execute')
con(seq,'then_0',br,'execute')
con(br,'then',callf,'execute')
con(seq,'then_1',sprev,'execute')

print('- 기본값')
dflt(callf,'bForceBlend','true')
dflt(callf,'StateMachineState','NewEnumerator11')

print('- 컴파일')
print(json.dumps(bq('compile_blueprint',{'asset_path':L}),ensure_ascii=False)[:300])
