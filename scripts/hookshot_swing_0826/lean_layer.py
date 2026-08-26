# -*- coding: utf-8 -*-
"""스윙 좌우 기울기 — 레이어 쪽: 앵커 기준 좌우 각도 계산 후 메인 ABP 로 전달"""
import json
from mono import call
LAY='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
G='UpdateHookshotLand'

def ok(t,r):
    bad=(not isinstance(r,dict)) or r.get('success') is False or '_text' in r
    print(('FAIL ' if bad else 'ok   ')+t, json.dumps(r,ensure_ascii=False)[:140])
    if bad: raise SystemExit('stop at '+t)
    return r
def node(t,**kw):
    p={'asset_path':LAY,'graph_name':G}; p.update(kw)
    return ok('node '+t, call('blueprint_query','add_node',p)).get('id')
def link(a,ap,b,bp_):
    ok('link %s.%s->%s.%s'%(a,ap,b,bp_), call('blueprint_query','connect_pins',
        {'asset_path':LAY,'graph_name':G,'source_node':a,'source_pin':ap,'target_node':b,'target_pin':bp_}))
def unlink(n,pin):
    ok('unlink %s.%s'%(n,pin), call('blueprint_query','disconnect_pins',
        {'asset_path':LAY,'graph_name':G,'node_id':n,'pin_name':pin}))
def pindef(n,pin,val):
    ok('pin %s.%s=%s'%(n,pin,val), call('blueprint_query','set_pin_default',
        {'asset_path':LAY,'graph_name':G,'node_id':n,'pin_name':pin,'value':val}))
def move(n,x,y):
    ok('move '+n, call('blueprint_query','set_node_position',{'asset_path':LAY,'graph_name':G,'node_id':n,'position':[x,y]}))

move('K2Node_SwitchEnum_0', -1000, 0)

I={}
I['abp']   = node('abp',   node_type='VariableGet', variable_name='As SBCharacterABP', position=[-2432, 620])
I['ct']    = node('ct',    node_type='VariableGet', variable_name='CharacterTransform', position=[-2432, 560])
I['brkT']  = node('brkT',  node_type='CallFunction', function_name='BreakTransform', target_class='KismetMathLibrary', position=[-2240, 540])
I['brkR']  = node('brkR',  node_type='CallFunction', function_name='BreakRotator',   target_class='KismetMathLibrary', position=[-2060, 660])
I['mkR']   = node('mkR',   node_type='CallFunction', function_name='MakeRotator',    target_class='KismetMathLibrary', position=[-1900, 660])
I['sub']   = node('sub',   node_type='CallFunction', function_name='Subtract_VectorVector', target_class='KismetMathLibrary', position=[-2060, 500])
I['unrot'] = node('unrot', node_type='CallFunction', function_name='LessLess_VectorRotator', target_class='KismetMathLibrary', position=[-1740, 540])
I['brkV']  = node('brkV',  node_type='CallFunction', function_name='BreakVector',    target_class='KismetMathLibrary', position=[-1580, 540])
I['negZ']  = node('negZ',  node_type='CallFunction', function_name='Multiply_DoubleDouble', target_class='KismetMathLibrary', position=[-1440, 600])
I['at2']   = node('at2',   node_type='CallFunction', function_name='DegAtan2',       target_class='KismetMathLibrary', position=[-1300, 540])
I['getSw'] = node('getSw', node_type='VariableGet', variable_name='bHookIsSwing', position=[-1600, 800])
I['cmc']   = node('cmc',   node_type='VariableGet', variable_name='SBCharacterMovement', position=[-1740, 880])
I['act']   = node('act',   node_type='CallFunction', function_name='IsHookshotActive', target_class='SBCharacterMovementComponent', position=[-1560, 860])
I['and']   = node('and',   node_type='CallFunction', function_name='BooleanAND', target_class='KismetMathLibrary', position=[-1400, 810])
I['sel']   = node('sel',   node_type='CallFunction', function_name='SelectFloat', target_class='KismetMathLibrary', position=[-1240, 620])
I['call']  = node('call',  node_type='CallFunction', function_name='SetHookSwingLeanTarget', target_class='PC_01_ABP_C', position=[-1240, 160])
I['abp2']  = node('abp2',  node_type='VariableGet', variable_name='As SBCharacterABP', position=[-1420, 300])
json.dump(I, open('ids_leanlayer.json','w'), ensure_ascii=False)

pindef(I['negZ'],'B','-1.0')
pindef(I['sel'],'B','0.0')

link(I['abp'],'As SBCharacterABP', I['ct'],'self')
link(I['ct'],'CharacterTransform', I['brkT'],'InTransform')
link(I['brkT'],'Rotation', I['brkR'],'InRot')
link(I['brkR'],'Yaw', I['mkR'],'Yaw')
link(I['brkT'],'Location', I['sub'],'A')
link('K2Node_PropertyAccess_12','Value', I['sub'],'B')   # SBCharacterMovement.HookshotRuntime.TargetLocation
link(I['sub'],'ReturnValue', I['unrot'],'A')
link(I['mkR'],'ReturnValue', I['unrot'],'B')
link(I['unrot'],'ReturnValue', I['brkV'],'InVec')
link(I['brkV'],'Z', I['negZ'],'A')
link(I['brkV'],'Y', I['at2'],'Y')
link(I['negZ'],'ReturnValue', I['at2'],'X')
link(I['at2'],'ReturnValue', I['sel'],'A')
link(I['cmc'],'SBCharacterMovement', I['act'],'self')
link(I['getSw'],'bHookIsSwing', I['and'],'A')
link(I['act'],'ReturnValue', I['and'],'B')
link(I['and'],'ReturnValue', I['sel'],'bPickA')
link(I['sel'],'ReturnValue', I['call'],'InTarget')
link(I['abp2'],'As SBCharacterABP', I['call'],'self')

unlink('K2Node_VariableSet_27','then')
link('K2Node_VariableSet_27','then', I['call'],'execute')
link(I['call'],'then','K2Node_SwitchEnum_0','execute')
print('DONE')
