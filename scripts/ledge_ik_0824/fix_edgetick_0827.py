# -*- coding: utf-8 -*-
"""8/27 이동 시작 엣지 틱 한 틱 튐 수정
 1) LedgeA_PrevHandL/R 신규 — 함수 진입부에서 매 틱 LedgeHandWorldL/R 캡처 (A가 덮어쓰기 전)
 2) 엣지 틱 From = PrevHand (그 틱 B경로 오염값 대신 직전 틱 값)
 3) 엣지 틱 [then] 분기 끝에 Set LedgeHandWorldL/R = From 추가 (B값 노출 차단)
"""
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
    c=[i for i,n in N.items() if n['pos']==pos]
    print('  stale',rid,'-> pos match',c); return c[-1]
def con(s,sp,t,tp):
    r=bq('connect_pins',P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    ok=r.get('success',True)
    print(('  OK  ' if ok else '  FAIL')+f' {s}.{sp} -> {t}.{tp}'+('' if ok else ' '+str(r)))
    return ok
def dis(s,sp,t,tp):
    try:
        r=bq('disconnect_pins',P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
        print('  dis',s,sp,'->',t,tp,r.get('success',r))
    except Exception as e: print('  dis ERR',str(e)[:160])

print('=== 1) 변수 추가 ===')
ex={v['name'] for v in bq('get_variables',{'asset_path':L})['variables']}
for n in ('LedgeA_PrevHandL','LedgeA_PrevHandR'):
    if n in ex: print('  이미 존재',n)
    else:
        bq('add_variable',{'asset_path':L,'name':n,'type':'struct:Vector','category':'Ledge|HandA'})
        print('  추가',n)

print('=== 2) 진입부 PrevHand 캡처 삽입 ===')
ENTRY='K2Node_FunctionEntry_0'; BR0='K2Node_IfThenElse_0'
getL=add('VariableGet',(-2080,128),variable_name='LedgeHandWorldL')
setPL=add('VariableSet',(-2020,16),variable_name='LedgeA_PrevHandL')
getR=add('VariableGet',(-1900,128),variable_name='LedgeHandWorldR')
setPR=add('VariableSet',(-1840,16),variable_name='LedgeA_PrevHandR')
print('  nodes',getL,setPL,getR,setPR)
dis(ENTRY,'then',BR0,'execute')
con(ENTRY,'then',setPL,'execute')
con(setPL,'then',setPR,'execute')
con(setPR,'then',BR0,'execute')
con(getL,'LedgeHandWorldL',setPL,'LedgeA_PrevHandL')
con(getR,'LedgeHandWorldR',setPR,'LedgeA_PrevHandR')

print('=== 3) From 소스를 PrevHand 로 교체 ===')
dis('K2Node_VariableGet_33','LedgeHandWorldL','K2Node_VariableSet_12','LedgeA_FromL')
dis('K2Node_VariableGet_34','LedgeHandWorldR','K2Node_VariableSet_13','LedgeA_FromR')
gpL=add('VariableGet',(240,96),variable_name='LedgeA_PrevHandL')
gpR=add('VariableGet',(448,96),variable_name='LedgeA_PrevHandR')
con(gpL,'LedgeA_PrevHandL','K2Node_VariableSet_12','LedgeA_FromL')
con(gpR,'LedgeA_PrevHandR','K2Node_VariableSet_13','LedgeA_FromR')

print('=== 4) 엣지 틱에도 HandWorld 세팅 ===')
S18='K2Node_VariableSet_18'
gfL=add('VariableGet',(5760,96),variable_name='LedgeA_FromL')
shL=add('VariableSet',(5820,-16),variable_name='LedgeHandWorldL')
gfR=add('VariableGet',(6020,96),variable_name='LedgeA_FromR')
shR=add('VariableSet',(6080,-16),variable_name='LedgeHandWorldR')
print('  nodes',gfL,shL,gfR,shR)
con(S18,'then',shL,'execute')
con(shL,'then',shR,'execute')
con(gfL,'LedgeA_FromL',shL,'LedgeHandWorldL')
con(gfR,'LedgeA_FromR',shR,'LedgeHandWorldR')

print('=== 5) 고아 Get 정리 ===')
N=graph()
for i in ('K2Node_VariableGet_33','K2Node_VariableGet_34'):
    if i in N:
        used=any(p['connected_to'] for p in N[i]['pins'])
        if not used: bq('remove_node',P(node_id=i)); print('  삭제',i)
        else: print('  아직 연결 있음, 보존',i,[p['connected_to'] for p in N[i]['pins']])

print('=== 6) 컴파일 ===')
r=bq('compile_blueprint',{'asset_path':L})
print('  ',{k:r[k] for k in ('success','error_count','warning_count') if k in r})
if r.get('errors'): print('  errors:',r['errors'][:5])
