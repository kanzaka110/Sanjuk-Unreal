# -*- coding: utf-8 -*-
"""메인 AnimGraph 에 넣었던 ModifyBone 클러스터 철거 + 대신 순수 게터 함수 생성"""
import json
from mono import call
ABP='/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP'

def ok(t,r):
    bad=(not isinstance(r,dict)) or r.get('success') is False or '_text' in r
    print(('FAIL ' if bad else 'ok   ')+t, json.dumps(r,ensure_ascii=False)[:130])
    if bad: raise SystemExit('stop at '+t)
    return r
def rm(g,n):
    ok('rm '+n, call('blueprint_query','remove_node',{'asset_path':ABP,'graph_name':g,'node_id':n}))

G='AnimGraph'
# 포즈 체인 원복
ok('relink', call('blueprint_query','connect_pins',{'asset_path':ABP,'graph_name':G,
    'source_node':'AnimGraphNode_PoseSearchHistoryCollector_0','source_pin':'Pose',
    'target_node':'AnimGraphNode_Root_0','target_pin':'Result'}))
for n in ['AnimGraphNode_LocalToComponentSpace_0','AnimGraphNode_ModifyBone_0','AnimGraphNode_ComponentToLocalSpace_0']:
    rm(G,n)
I=json.load(open('ids_leangraph.json'))
for k in ['rot','fwd','brk','getCT','getAng']:
    rm(G, I[k])
ok('move root', call('blueprint_query','set_node_position',{'asset_path':ABP,'graph_name':G,'node_id':'AnimGraphNode_Root_0','position':[7008,-48]}))
print('--- main AnimGraph reverted ---')
