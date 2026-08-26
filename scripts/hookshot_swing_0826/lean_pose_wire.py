# -*- coding: utf-8 -*-
import json
from mono import call
LAY='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
G='HookShot'
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
    ok('unlink %s.%s'%(n,pin), call('blueprint_query','disconnect_pins',{'asset_path':LAY,'graph_name':G,'node_id':n,'pin_name':pin}))
def move(n,x,y):
    ok('move '+n, call('blueprint_query','set_node_position',{'asset_path':LAY,'graph_name':G,'node_id':n,'position':[x,y]}))

L2C='AnimGraphNode_LocalToComponentSpace_1'; MB='AnimGraphNode_ModifyBone_1'; C2L='AnimGraphNode_ComponentToLocalSpace_1'
SWING='AnimGraphNode_RotationOffsetBlendSpace_0'; ROOT='AnimGraphNode_Root_0'

move(L2C, 780, 0); move(MB, 960, 0); move(C2L, 1200, 0); move(ROOT, 1420, -48)

I={}
I['abp'] = node('abp', node_type='VariableGet', variable_name='As SBCharacterABP', position=[700, 240])
I['get'] = node('get', node_type='CallFunction', function_name='GetHookSwingLeanRotator', target_class='PC_01_ABP_C', position=[860, 200])
json.dump(I, open('ids_leanposewire.json','w'), ensure_ascii=False)

link(I['abp'],'As SBCharacterABP', I['get'],'self')
link(I['get'],'LeanRotator', MB,'Rotation')

unlink(SWING,'Pose')
link(SWING,'Pose', L2C,'LocalPose')
link(L2C,'ComponentPose', MB,'ComponentPose')
link(MB,'Pose', C2L,'ComponentPose')
link(C2L,'Pose', ROOT,'Result')
print('DONE')
