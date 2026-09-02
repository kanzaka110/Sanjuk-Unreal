# -*- coding: utf-8 -*-
"""재평가 중복 발화 억제 — 쿨다운 (9/2)
   bTransitingToNextLedge 와 bTransitMoving 이 시차를 두고 바뀌어 OR 조건이 2번 발화 → 모션 2회 재생.
   조건에 (CD <= 0) 를 AND 로 걸고, 재평가 시 CD=CooldownTime, 매 틱 DeltaTime 만큼 감산.
"""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
bq=lambda a,p: call('blueprint_query',a,p)
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'
FN='UpdateLedgeEndReeval'
CD='LedgeEndReevalCD'; KNOB='LedgeEndReevalCooldown'
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
def dflt(n,pin,v): bq('set_pin_default',Q(node_id=n,pin_name=pin,value=v))

have={v['name'] for v in bq('get_variables',{'asset_path':L})['variables']}
for nm,ty,dv in [(CD,'float','0.0'),(KNOB,'float','0.25')]:
    if nm not in have:
        bq('add_variable',{'asset_path':L,'name':nm,'type':ty,'category':'Custom Move|Ledge|End','default_value':dv})
        print('add_variable',nm,'=',dv)

print('- 게이트 노드 (CD <= 0)')
gcd  = add('VariableGet',(560,120), variable_name=CD)
le   = add('CallFunction',(700,120), function_name='LessEqual_DoubleDouble')
andn = add('CallFunction',(760,-40), function_name='BooleanAND')
print('  cdGet',gcd,'<=',le,'AND',andn)
con(gcd,CD,le,'A'); dflt(le,'B','0.0')
# 기존 OR(CallFunction_5) → AND.A , 게이트 → AND.B , AND → Branch.Condition
con('K2Node_CallFunction_5','ReturnValue',andn,'A')
con(le,'ReturnValue',andn,'B')
con(andn,'ReturnValue','K2Node_IfThenElse_0','Condition')

print('- 재평가 시 CD 충전 (Call 뒤에 직렬)')
gknob = add('VariableGet',(1150,60), variable_name=KNOB)
scd1  = add('VariableSet',(1320,-208), variable_name=CD)
con('K2Node_CallFunction_2','then',scd1,'execute')
con(gknob,KNOB,scd1,CD)

print('- 매 틱 CD 감산 (then_1 체인 끝에)')
gcd2 = add('VariableGet',(1100,300), variable_name=CD)
gdt  = add('VariableGet',(1100,370), variable_name='Delta Time')
sub  = add('CallFunction',(1260,320), function_name='Subtract_DoubleDouble')
mx   = add('CallFunction',(1420,320), function_name='Max')
scd2 = add('VariableSet',(1600,48), variable_name=CD)
con(gcd2,CD,sub,'A'); con(gdt,'Delta Time',sub,'B')
con(sub,'ReturnValue',mx,'A'); dflt(mx,'B','0.0')
con(mx,'ReturnValue',scd2,CD)
con('K2Node_VariableSet_1','then',scd2,'execute')

print('- 컴파일')
r=bq('compile_blueprint',{'asset_path':L})
print('  success',r.get('success'),'errors',r.get('error_count'),'warnings',r.get('warning_count'))
for e in (r.get('errors') or [])[:6]: print('   ',str(e)[:170])
