# -*- coding: utf-8 -*-
"""렛지 정지 후 챠저 재평가 (9/2)
   전이 종료(tr=false, IsTransitMoving=false)가 Delay 이상 유지되면 1회만
   메인 ABP.SetStateMachineBlendStackAnim(bForceBlend, State=11) 호출 → 챠저 재평가.
   ※ 신호는 레이어 변수(죽은 값)가 아니라 SBCharacterMovement 의 C++ 함수에서 직접 읽는다.
   ※ 실측: 이동 중 깜빡임 0.16~0.49s / 진짜 정지 1.19~3.38s → Delay 0.6s 로 분리.
"""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
import json
bq=lambda a,p: call('blueprint_query',a,p)
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'
FN='UpdateLedgeReeval'
MC='SBCharacterMovementComponent'
STILL='LedgeReevalStill'; FIRED='bLedgeReevalFired'; DELAY='LedgeReevalDelay'
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
    ok=r.get('success',True)
    if not ok: print('  FAIL',s,sp,'->',t,tp)
    return ok
def dflt(n,pin,v): bq('set_pin_default',Q(node_id=n,pin_name=pin,value=v))

have={v['name'] for v in bq('get_variables',{'asset_path':L})['variables']}
for nm,ty,dv in [(STILL,'float','0.0'),(FIRED,'bool','false'),(DELAY,'float','0.6')]:
    if nm not in have:
        bq('add_variable',{'asset_path':L,'name':nm,'type':ty,'category':'Custom Move|Ledge|Reeval','default_value':dv})
        print('add_variable',nm,'=',dv)
try:
    bq('add_function',{'asset_path':L,'function_name':FN,'category':'Custom Move|Ledge|Reeval'})
    print('add_function',FN)
except Exception as e: print('add_function:',str(e)[:120])

N=graph(); entry=[i for i,n in N.items() if 'FunctionEntry' in n['class']][0]
print('entry',entry)

# --- 신호 소스 (C++ 직독) ---
gmc1 = add('VariableGet',(-900,180), variable_name='SBCharacterMovement')
gmd  = add('CallFunction',(-700,140), function_name='GetLedgeMoveData', target_class=MC)
brk  = add('BreakStruct',(-500,140), struct_type='SBLedgeMoveData')
gmc2 = add('VariableGet',(-900,380), variable_name='SBCharacterMovement')
itm  = add('CallFunction',(-700,340), function_name='IsTransitMoving', target_class=MC)
con(gmc1,'SBCharacterMovement',gmd,'self'); con(gmd,'ReturnValue',brk,'SBLedgeMoveData')
con(gmc2,'SBCharacterMovement',itm,'self')

# still = NOT tr AND NOT tm
n1 = add('CallFunction',(-300,140), function_name='Not_PreBool')
n2 = add('CallFunction',(-300,340), function_name='Not_PreBool')
andn=add('CallFunction',(-120,240), function_name='BooleanAND')
con(brk,'bTransitingToNextLedge',n1,'A'); con(itm,'ReturnValue',n2,'A')
con(n1,'ReturnValue',andn,'A'); con(n2,'ReturnValue',andn,'B')

br1 = add('Branch',(100,0))
con(entry,'then',br1,'execute'); con(andn,'ReturnValue',br1,'Condition')

# --- TRUE: Still += DT ; if Still>=Delay AND !Fired -> 재평가 ---
gs   = add('VariableGet',(300,200), variable_name=STILL)
gdt  = add('VariableGet',(300,270), variable_name='Delta Time')
addf = add('CallFunction',(460,220), function_name='Add_DoubleDouble')
sstill=add('VariableSet',(640,0), variable_name=STILL)
con(gs,STILL,addf,'A'); con(gdt,'Delta Time',addf,'B'); con(addf,'ReturnValue',sstill,STILL)
con(br1,'then',sstill,'execute')

gs2  = add('VariableGet',(640,220), variable_name=STILL)
gdl  = add('VariableGet',(640,290), variable_name=DELAY)
ge   = add('CallFunction',(800,240), function_name='GreaterEqual_DoubleDouble')
gf   = add('VariableGet',(800,330), variable_name=FIRED)
nf   = add('CallFunction',(940,330), function_name='Not_PreBool')
and2 = add('CallFunction',(1080,270), function_name='BooleanAND')
br2  = add('Branch',(1240,0))
con(gs2,STILL,ge,'A'); con(gdl,DELAY,ge,'B')
con(gf,FIRED,nf,'A')
con(ge,'ReturnValue',and2,'A'); con(nf,'ReturnValue',and2,'B')
con(and2,'ReturnValue',br2,'Condition'); con(sstill,'then',br2,'execute')

gabp = add('VariableGet',(1420,220), variable_name='As SBCharacterABP')
callf= add('CallFunction',(1600,0), function_name='SetStateMachineBlendStackAnim', target_class='PC_01_ABP_C')
sfire= add('VariableSet',(1860,0), variable_name=FIRED)
con(gabp,'As SBCharacterABP',callf,'self')
con(br2,'then',callf,'execute'); con(callf,'then',sfire,'execute')
dflt(callf,'bForceBlend','true'); dflt(callf,'StateMachineState','NewEnumerator11')
dflt(sfire,FIRED,'true')

# --- FALSE: Still=0, Fired=false ---
rst  = add('VariableSet',(300,480), variable_name=STILL)
rfir = add('VariableSet',(560,480), variable_name=FIRED)
con(br1,'else',rst,'execute'); con(rst,'then',rfir,'execute')
dflt(rst,STILL,'0.0'); dflt(rfir,FIRED,'false')

r=bq('compile_blueprint',{'asset_path':L})
print('컴파일 success',r.get('success'),'errors',r.get('error_count'),'warnings',r.get('warning_count'))
for e in (r.get('errors') or [])[:6]: print('  ',str(e)[:170])
