# -*- coding: utf-8 -*-
"""LedgeIK 의 LedgeDebugs(CF_2) 직후에 LedgePhysDebugs 호출 삽입"""
from mono import *
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'
G='LedgeIK'
bq=lambda a,p: call('blueprint_query',a,p)
def Q(**kw): return dict(asset_path=L, graph_name=G, **kw)

r=bq('add_node',Q(node_type='CallFunction',position=[-112,240],
                  function_name='LedgePhysDebugs',target_class='PC_01_AnimLayer_Ledge_C'))
nid=r['id']; print('call node',nid)
N={n['id']:n for n in bq('get_graph_data',{'asset_path':L,'graph_name':G})['nodes']}
if nid not in N:
    nid=[i for i,n in N.items() if n['pos']==[-112,240]][-1]; print(' stale ->',nid)

bq('disconnect_pins',Q(node_id='K2Node_CallFunction_2',pin_name='then'))
for s,sp,t,tp in [('K2Node_CallFunction_2','then',nid,'execute'),
                  (nid,'then','K2Node_CallFunction_124','execute')]:
    print(' ',sp,'->',tp, bq('connect_pins',Q(source_node=s,source_pin=sp,target_node=t,target_pin=tp)).get('success'))

N2={n['id']:n for n in bq('get_graph_data',{'asset_path':L,'graph_name':G})['nodes']}
for i in ('K2Node_CallFunction_2',nid):
    t=[p for p in N2[i]['pins'] if p['name']=='then'][0]
    print('  ',i,N2[i].get('title','').split(chr(10))[0],'then ->',t['connected_to'])
c=bq('compile_blueprint',{'asset_path':L}); print('COMPILE',c.get('success'),c.get('errors'),c.get('warnings'))
if c.get('success'):
    try: print('save:',ed('save_asset',{'asset_path':L})['saved'])
    except Exception as e: print('save_packages:',ed('save_packages',{'packages':[L]})['results'][0]['saved'])
