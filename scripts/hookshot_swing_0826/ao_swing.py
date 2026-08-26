# -*- coding: utf-8 -*-
import json
from mono import call
BP='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
G='HookShot'
GROUND='AnimGraphNode_RotationOffsetBlendSpace_1'
SWING ='AnimGraphNode_RotationOffsetBlendSpace_0'

def ok(t,r):
    bad=(not isinstance(r,dict)) or r.get('success') is False or '_text' in r
    print(('FAIL ' if bad else 'ok   ')+t, json.dumps(r,ensure_ascii=False)[:150])
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
def move(n,x,y):
    ok('move '+n, call('blueprint_query','set_node_position',
        {'asset_path':BP,'graph_name':G,'node_id':n,'position':[x,y]}))

# 0. 레이어 변수
ok('var bHookIsSwing', call('blueprint_query','add_variable',
    {'asset_path':BP,'name':'bHookIsSwing','type':'bool','default_value':'false','category':'Hookshot'}))

# 1. 스윙 AO 자리 잡기
move(SWING, 560, 0)

# 2. 헬퍼 노드
I={}
I['getSwing1'] = node('getSwing1', node_type='VariableGet', variable_name='bHookIsSwing', position=[176, 288])
I['notSwing']  = node('notSwing',  node_type='CallFunction', function_name='Not_PreBool', target_class='KismetMathLibrary', position=[320, 288])
I['andGround'] = node('andGround', node_type='CallFunction', function_name='BooleanAND',  target_class='KismetMathLibrary', position=[448, 208])
I['getAim2']   = node('getAim2',   node_type='VariableGet', variable_name='bHookAiming',  position=[560, 400])
I['getSwing2'] = node('getSwing2', node_type='VariableGet', variable_name='bHookIsSwing', position=[560, 448])
I['andSwing']  = node('andSwing',  node_type='CallFunction', function_name='BooleanAND',  target_class='KismetMathLibrary', position=[720, 368])
I['getPitch2'] = node('getPitch2', node_type='VariableGet', variable_name='HookAimPitch', position=[400, 30])
json.dump(I, open('ids_ao.json','w'), ensure_ascii=False)

# 3. 포즈 체인: InPose -> Ground -> Swing -> Root
unlink(GROUND,'Pose')
link(GROUND,'Pose', SWING,'BasePose')
link(SWING,'Pose','AnimGraphNode_Root_0','Result')
link(I['getPitch2'],'HookAimPitch', SWING,'Y')

# 4. 알파: Ground = 조준중 AND NOT 스윙 / Swing = 조준중 AND 스윙
#    K2Node_VariableGet_2 = 미리 만들어 둔 Get bHookAiming (Ground 쪽 AND 용)
link(I['getSwing1'],'bHookIsSwing', I['notSwing'],'A')
link('K2Node_VariableGet_2','bHookAiming', I['andGround'],'A')
link(I['notSwing'],'ReturnValue', I['andGround'],'B')
unlink(GROUND,'bAlphaBoolEnabled')
link(I['andGround'],'ReturnValue', GROUND,'bAlphaBoolEnabled')

link(I['getAim2'],'bHookAiming', I['andSwing'],'A')
link(I['getSwing2'],'bHookIsSwing', I['andSwing'],'B')
link(I['andSwing'],'ReturnValue', SWING,'bAlphaBoolEnabled')
print('DONE')
