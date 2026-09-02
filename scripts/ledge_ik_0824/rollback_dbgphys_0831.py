# -*- coding: utf-8 -*-
"""LedgeDebugs 원복: 추가한 BuildString 6 + VariableGet 6 제거, CF_12 -> CF_14.Text 재연결"""
from mono import *
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'
G='LedgeDebugs'
bq=lambda a,p: call('blueprint_query',a,p)
N={n['id']:n for n in bq('get_graph_data',{'asset_path':L,'graph_name':G})['nodes']}
tgt=[i for i,n in N.items()
     if 'BuildString' in str(n.get('function','')) or
        (n['class']=='K2Node_VariableGet' and n['pos'][1]>=900 and n['pos'][0]<=-1300)]
print('제거:',[(i,N[i].get('title')) for i in tgt])
for i in tgt: bq('remove_node',{'asset_path':L,'graph_name':G,'node_id':i})
r=bq('connect_pins',{'asset_path':L,'graph_name':G,'source_node':'K2Node_CallFunction_12',
                     'source_pin':'ReturnValue','target_node':'K2Node_CallFunction_14','target_pin':'Text'})
print('재연결:',r.get('success'))
N2={n['id']:n for n in bq('get_graph_data',{'asset_path':L,'graph_name':G})['nodes']}
t=[p for p in N2['K2Node_CallFunction_14']['pins'] if p['name']=='Text'][0]
print('DrawDebugString.Text <-',t['connected_to'])
print('BuildString 잔존:',[i for i,n in N2.items() if 'BuildString' in str(n.get('function',''))])
c=bq('compile_blueprint',{'asset_path':L}); print('COMPILE',c.get('success'),c.get('errors'))
if c.get('success'): print('save:',ed('save_asset',{'asset_path':L})['saved'])
