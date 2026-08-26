# -*- coding: utf-8 -*-
"""HookShot 인터페이스 그래프에 스윙 기울기 ModifyBone 삽입"""
import json
from mono import call
LAY='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
def ok(t,r):
    bad=(not isinstance(r,dict)) or r.get('success') is False or '_text' in r
    print(('FAIL ' if bad else 'ok   ')+t, json.dumps(r,ensure_ascii=False)[:160])
    if bad: raise SystemExit('stop at '+t)
    return r

# 1) AnimGraph 에 3노드 생성 (animation 액션은 인터페이스 그래프 타깃 불가)
mb=ok('mb', call('animation_query','add_anim_graph_node',{'asset_path':LAY,'graph_name':'AnimGraph',
    'node_type':'ModifyBone','bone_to_modify':'root','expose_pins':['Rotation'],
    'position_x':900,'position_y':900}))['node_name']
ok('rotmode', call('animation_query','set_anim_graph_node_property',{'asset_path':LAY,'graph_name':'AnimGraph','node_id':mb,'property_path':'RotationMode','value':'BMM_Additive'}))
ok('rotspace', call('animation_query','set_anim_graph_node_property',{'asset_path':LAY,'graph_name':'AnimGraph','node_id':mb,'property_path':'RotationSpace','value':'BCS_WorldSpace'}))
l2c=ok('l2c', call('animation_query','add_anim_graph_node',{'asset_path':LAY,'graph_name':'AnimGraph','node_type':'LocalToComponentSpace','position_x':700,'position_y':900}))['node_name']
c2l=ok('c2l', call('animation_query','add_anim_graph_node',{'asset_path':LAY,'graph_name':'AnimGraph','node_type':'ComponentToLocalSpace','position_x':1150,'position_y':900}))['node_name']

c=ok('copy', call('blueprint_query','copy_nodes',{'source_asset':LAY,'source_graph':'AnimGraph',
    'node_ids':[l2c,mb,c2l],'target_asset':LAY,'target_graph':'HookShot'}))
print('new ids:', c.get('new_node_ids'))
for n in [l2c,mb,c2l]:
    ok('rm tmp '+n, call('blueprint_query','remove_node',{'asset_path':LAY,'graph_name':'AnimGraph','node_id':n}))
json.dump(c.get('new_node_ids'), open('ids_leanpose.json','w'))
