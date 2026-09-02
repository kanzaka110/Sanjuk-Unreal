# -*- coding: utf-8 -*-
"""재평가 함수의 신호 소스 교체 (9/2)
   레이어의 LedgeMoveData / bTransitMoving 은 Set 노드가 없어 갱신되지 않는다(기본값 고정).
   살아있는 소스 = 레이어 EventGraph 에서 매 틱 Set 되는 SBCharacterMovement.
     LedgeMoveData  → SBCharacterMovement.GetLedgeMoveData()
     bTransitMoving → SBCharacterMovement.IsTransitMoving()
"""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
bq=lambda a,p: call('blueprint_query',a,p)
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'
FN='UpdateLedgeEndReeval'
MC='SBCharacterMovementComponent'
def Q(**kw): return dict(asset_path=L, graph_name=FN, **kw)
def graph(): return {n['id']:n for n in bq('get_graph_data',{'asset_path':L,'graph_name':FN})['nodes']}
def add(nt,pos,**kw):
    p=Q(node_type=nt,position=[int(pos[0]),int(pos[1])]); p.update(kw)
    rid=bq('add_node',p)['id']; N=graph()
    if rid in N: return rid
    c=[i for i,n in N.items() if n['pos']==[int(pos[0]),int(pos[1])]]
    return c[-1]
def con(s,sp,t,tp):
    r=bq('connect_pins',Q(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    ok=r.get('success',True); print(('  ok   ' if ok else '  FAIL '),s,sp,'->',t,tp); return ok

print('- 살아있는 소스 노드 생성')
gmc1 = add('VariableGet',(-380,120), variable_name='SBCharacterMovement')
gmd  = add('CallFunction',(-180,40), function_name='GetLedgeMoveData', target_class=MC)
gmc2 = add('VariableGet',(120,250),  variable_name='SBCharacterMovement')
itm  = add('CallFunction',(300,190), function_name='IsTransitMoving', target_class=MC)
print('  GetLedgeMoveData',gmd,'| IsTransitMoving',itm)
con(gmc1,'SBCharacterMovement',gmd,'self')
con(gmc2,'SBCharacterMovement',itm,'self')

print('- 죽은 소스 노드 삭제(링크 자동 해제)')
for nid in ['K2Node_VariableGet_0','K2Node_VariableGet_3']:
    try:
        r=bq('remove_node',Q(node_id=nid)); print('   remove',nid,r.get('success',r))
    except Exception as e: print('   remove',nid,'ERR',str(e)[:120])

print('- 새 소스 배선')
con(gmd,'ReturnValue','K2Node_BreakStruct_0','SBLedgeMoveData')
con(itm,'ReturnValue','K2Node_CallFunction_4','A')      # neq2: TM != prevTM
con(itm,'ReturnValue','K2Node_VariableSet_1','bLedgeEndPrevTM')

print('- 컴파일')
r=bq('compile_blueprint',{'asset_path':L})
print('  success',r.get('success'),'errors',r.get('error_count'),'warnings',r.get('warning_count'))
for e in (r.get('errors') or [])[:6]: print('   ',str(e)[:160])
