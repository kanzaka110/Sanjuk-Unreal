# -*- coding: utf-8 -*-
"""메인 ABP 순수 게터: GetHookSwingLeanRotator = RotatorFromAxisAndAngle(캐릭터 정면, HookSwingLeanAngle)"""
import json
from mono import call
ABP='/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP'
G='GetHookSwingLeanRotator'
def ok(t,r):
    bad=(not isinstance(r,dict)) or r.get('success') is False or '_text' in r
    print(('FAIL ' if bad else 'ok   ')+t, json.dumps(r,ensure_ascii=False)[:150])
    if bad: raise SystemExit('stop at '+t)
    return r
def node(t,**kw):
    p={'asset_path':ABP,'graph_name':G}; p.update(kw)
    return ok('node '+t, call('blueprint_query','add_node',p)).get('id')
def link(a,ap,b,bp_):
    ok('link %s.%s->%s.%s'%(a,ap,b,bp_), call('blueprint_query','connect_pins',
        {'asset_path':ABP,'graph_name':G,'source_node':a,'source_pin':ap,'target_node':b,'target_pin':bp_}))

ok('fn', call('blueprint_query','add_function',{'asset_path':ABP,'name':G,'is_pure':True,'category':'Custom Move|Hookshot'}))
ok('out', call('blueprint_query','set_function_params',{'asset_path':ABP,'function_name':G,
    'outputs':[{'name':'LeanRotator','type':'struct:Rotator'}]}))
ok('ts', call('blueprint_query','set_function_thread_safe',{'asset_path':ABP,'function_name':G,'thread_safe':True}))

I={}
I['ct']  = node('ct',  node_type='VariableGet', variable_name='CharacterTransform', position=[-640, 176])
I['brk'] = node('brk', node_type='CallFunction', function_name='BreakTransform', target_class='KismetMathLibrary', position=[-460, 160])
I['fwd'] = node('fwd', node_type='CallFunction', function_name='GetForwardVector', target_class='KismetMathLibrary', position=[-280, 160])
I['ang'] = node('ang', node_type='VariableGet', variable_name='HookSwingLeanAngle', position=[-280, 260])
I['rot'] = node('rot', node_type='CallFunction', function_name='RotatorFromAxisAndAngle', target_class='KismetMathLibrary', position=[-100, 180])
json.dump(I, open('ids_leangetter.json','w'), ensure_ascii=False)

link(I['ct'],'CharacterTransform', I['brk'],'InTransform')
link(I['brk'],'Rotation', I['fwd'],'InRot')
link(I['fwd'],'ReturnValue', I['rot'],'Axis')
link(I['ang'],'HookSwingLeanAngle', I['rot'],'Angle')

s=call('blueprint_query','get_graph_summary',{'blueprint_path':ABP,'graph_name':G})
ret=[n['id'] for n in s['nodes'] if n['class'] in ('K2Node_FunctionResult','K2Node_FunctionTerminator')]
print('result nodes:',[ (n['id'],n['class']) for n in s['nodes'] ])
if ret:
    link(I['rot'],'ReturnValue', ret[0],'LeanRotator')
c=call('blueprint_query','compile_blueprint',{'blueprint_path':ABP})
print('compile:',c.get('status'),c.get('error_count'))
print(json.dumps([g['message'] for g in c.get('error_groups',[]) if g['severity']=='error'],ensure_ascii=False)[:400])
