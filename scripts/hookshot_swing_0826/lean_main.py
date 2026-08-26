# -*- coding: utf-8 -*-
"""스윙 좌우 기울기(lean) — 메인 ABP 쪽: 변수 + UpdateHookSwingLean 함수 + 호출 삽입"""
import json
from mono import call
ABP='/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP'
G='UpdateHookSwingLean'

def ok(t,r):
    bad=(not isinstance(r,dict)) or r.get('success') is False or '_text' in r
    print(('FAIL ' if bad else 'ok   ')+t, json.dumps(r,ensure_ascii=False)[:150])
    if bad: raise SystemExit('stop at '+t)
    return r
def var(n,ty,dv,cat,ie=True):
    ok('var '+n, call('blueprint_query','add_variable',
        {'asset_path':ABP,'name':n,'type':ty,'default_value':dv,'category':cat,'instance_editable':ie}))
def node(t,g,**kw):
    p={'asset_path':ABP,'graph_name':g}; p.update(kw)
    return ok('node '+t, call('blueprint_query','add_node',p)).get('id')
def link(g,a,ap,b,bp_):
    ok('link %s.%s->%s.%s'%(a,ap,b,bp_), call('blueprint_query','connect_pins',
        {'asset_path':ABP,'graph_name':g,'source_node':a,'source_pin':ap,'target_node':b,'target_pin':bp_}))
def unlink(g,n,pin):
    ok('unlink %s.%s'%(n,pin), call('blueprint_query','disconnect_pins',
        {'asset_path':ABP,'graph_name':g,'node_id':n,'pin_name':pin}))
def pindef(g,n,pin,val):
    ok('pin %s.%s=%s'%(n,pin,val), call('blueprint_query','set_pin_default',
        {'asset_path':ABP,'graph_name':g,'node_id':n,'pin_name':pin,'value':val}))

# ---- 1. 변수 ----
var('HookSwingLeanTarget','double','0.0','Custom Move|Hookshot')       # 레이어가 매 틱 써 준다
var('HookSwingLeanAngle', 'double','0.0','Custom Move|Hookshot')       # 실제 적용값(보간 결과)
var('HookSwingLeanScale', 'double','1.0','Custom Move|Hookshot|Knob')
var('HookSwingLeanMax',   'double','60.0','Custom Move|Hookshot|Knob')
var('HookSwingLeanSpeed', 'double','10.0','Custom Move|Hookshot|Knob')

# ---- 2. 함수 ----
ok('add_function', call('blueprint_query','add_function',{'asset_path':ABP,'function_name':G}))

I={}
I['getPhase'] = node('getPhase',G, node_type='VariableGet', variable_name='HookshotPhase', position=[-720, 288])
I['neq']      = node('neq',G, node_type='CallFunction', function_name='NotEqual_ByteByte', target_class='KismetMathLibrary', position=[-540, 288])
I['getTgt']   = node('getTgt',G, node_type='VariableGet', variable_name='HookSwingLeanTarget', position=[-720, 432])
I['getScale'] = node('getScale',G, node_type='VariableGet', variable_name='HookSwingLeanScale', position=[-720, 496])
I['mul']      = node('mul',G, node_type='CallFunction', function_name='Multiply_DoubleDouble', target_class='KismetMathLibrary', position=[-540, 432])
I['getMax']   = node('getMax',G, node_type='VariableGet', variable_name='HookSwingLeanMax', position=[-720, 592])
I['neg']      = node('neg',G, node_type='CallFunction', function_name='Multiply_DoubleDouble', target_class='KismetMathLibrary', position=[-540, 592])
I['clamp']    = node('clamp',G, node_type='CallFunction', function_name='FClamp', target_class='KismetMathLibrary', position=[-360, 448])
I['sel']      = node('sel',G, node_type='CallFunction', function_name='SelectFloat', target_class='KismetMathLibrary', position=[-180, 368])
I['getAngle'] = node('getAngle',G, node_type='VariableGet', variable_name='HookSwingLeanAngle', position=[-180, 240])
I['getDt']    = node('getDt',G, node_type='VariableGet', variable_name='Delta Time', position=[-180, 528])
I['getSpd']   = node('getSpd',G, node_type='VariableGet', variable_name='HookSwingLeanSpeed', position=[-180, 592])
I['interp']   = node('interp',G, node_type='CallFunction', function_name='FInterpTo', target_class='KismetMathLibrary', position=[0, 320])
I['setAngle'] = node('setAngle',G, node_type='VariableSet', variable_name='HookSwingLeanAngle', position=[240, 0])
json.dump(I, open('ids_leanmain.json','w'), ensure_ascii=False)

pindef(G, I['neq'],'B','None')
pindef(G, I['neg'],'B','-1.0')
pindef(G, I['sel'],'B','0.0')

link(G, I['getPhase'],'HookshotPhase', I['neq'],'A')
link(G, I['getTgt'],'HookSwingLeanTarget', I['mul'],'A')
link(G, I['getScale'],'HookSwingLeanScale', I['mul'],'B')
link(G, I['getMax'],'HookSwingLeanMax', I['neg'],'A')
link(G, I['mul'],'ReturnValue', I['clamp'],'Value')
link(G, I['neg'],'ReturnValue', I['clamp'],'Min')
link(G, I['getMax'],'HookSwingLeanMax', I['clamp'],'Max')
link(G, I['clamp'],'ReturnValue', I['sel'],'A')
link(G, I['neq'],'ReturnValue', I['sel'],'bPickA')
link(G, I['getAngle'],'HookSwingLeanAngle', I['interp'],'Current')
link(G, I['sel'],'ReturnValue', I['interp'],'Target')
link(G, I['getDt'],'Delta Time', I['interp'],'DeltaTime')
link(G, I['getSpd'],'HookSwingLeanSpeed', I['interp'],'InterpSpeed')
link(G, I['interp'],'ReturnValue', I['setAngle'],'HookSwingLeanAngle')

ents=call('blueprint_query','get_graph_summary',{'blueprint_path':ABP,'graph_name':G})
entry=[n['id'] for n in ents['nodes'] if n['class']=='K2Node_FunctionEntry'][0]
print('entry:',entry)
link(G, entry,'then', I['setAngle'],'execute')
print('DONE main function')
