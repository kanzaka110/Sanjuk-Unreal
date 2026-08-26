# -*- coding: utf-8 -*-
import json
from mono import call
BP='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
G='UpdateHookshotLand'
def ok(t,r):
    bad=(not isinstance(r,dict)) or r.get('success') is False or '_text' in r
    print(('FAIL ' if bad else 'ok   ')+t, json.dumps(r,ensure_ascii=False)[:160])
    if bad: raise SystemExit('stop at '+t)
    return r
def node(t,**kw):
    p={'asset_path':BP,'graph_name':G}; p.update(kw)
    return ok('node '+t, call('blueprint_query','add_node',p)).get('id')
def link(a,ap,b,bp_):
    ok('link %s.%s->%s.%s'%(a,ap,b,bp_), call('blueprint_query','connect_pins',
        {'asset_path':BP,'graph_name':G,'source_node':a,'source_pin':ap,'target_node':b,'target_pin':bp_}))
def unlink(n,pin):
    ok('unlink %s.%s'%(n,pin), call('blueprint_query','disconnect_pins',
        {'asset_path':BP,'graph_name':G,'node_id':n,'pin_name':pin}))

I={}
I['getCMC'] = node('getCMC', node_type='VariableGet', variable_name='SBCharacterMovement', position=[-1920, 300])
I['getType']= node('getType', node_type='CallFunction', function_name='GetHookshotType',
                   target_class='SBCharacterMovementComponent', position=[-1730, 270])
I['getVal'] = node('getVal', node_type='VariableGet', variable_name='HookSwingTypeValue', position=[-1730, 390])
I['eq']     = node('eq', node_type='CallFunction', function_name='EqualEqual_ByteByte',
                   target_class='KismetMathLibrary', position=[-1570, 300])
I['setSw']  = node('setSw', node_type='VariableSet', variable_name='bHookIsSwing', position=[-1440, 160])
json.dump(I, open('ids_isswing.json','w'), ensure_ascii=False)

link(I['getCMC'],'SBCharacterMovement', I['getType'],'self')
link(I['getType'],'ReturnValue', I['eq'],'A')
link(I['getVal'],'HookSwingTypeValue', I['eq'],'B')
link(I['eq'],'ReturnValue', I['setSw'],'bHookIsSwing')

unlink('K2Node_FunctionEntry_0','then')
link('K2Node_FunctionEntry_0','then', I['setSw'],'execute')
link(I['setSw'],'then','K2Node_SwitchEnum_0','execute')
print('DONE')
