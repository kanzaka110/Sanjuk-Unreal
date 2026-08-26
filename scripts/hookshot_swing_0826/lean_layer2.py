# -*- coding: utf-8 -*-
import json
from mono import call
LAY='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
G='UpdateHookshotLand'
I=json.load(open('ids_leanlayer.json'))
CT='K2Node_VariableGet_43'   # 복사로 만든 cross-target Get CharacterTransform

def ok(t,r):
    bad=(not isinstance(r,dict)) or r.get('success') is False or '_text' in r
    print(('FAIL ' if bad else 'ok   ')+t, json.dumps(r,ensure_ascii=False)[:130])
    if bad: raise SystemExit('stop at '+t)
def link(a,ap,b,bp_):
    ok('link %s.%s->%s.%s'%(a,ap,b,bp_), call('blueprint_query','connect_pins',
        {'asset_path':LAY,'graph_name':G,'source_node':a,'source_pin':ap,'target_node':b,'target_pin':bp_}))
def unlink(n,pin):
    ok('unlink %s.%s'%(n,pin), call('blueprint_query','disconnect_pins',
        {'asset_path':LAY,'graph_name':G,'node_id':n,'pin_name':pin}))
def move(n,x,y):
    ok('move '+n, call('blueprint_query','set_node_position',{'asset_path':LAY,'graph_name':G,'node_id':n,'position':[x,y]}))

move(CT, -2432, 560)
link(I['abp'],'As SBCharacterABP', CT,'self')
link(CT,'CharacterTransform', I['brkT'],'InTransform')
link(I['brkT'],'Rotation', I['brkR'],'InRot')
link(I['brkR'],'Yaw', I['mkR'],'Yaw')
link(I['brkT'],'Location', I['sub'],'A')
link('K2Node_PropertyAccess_12','Value', I['sub'],'B')
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
