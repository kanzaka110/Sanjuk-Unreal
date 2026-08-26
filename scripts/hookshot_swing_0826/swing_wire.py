# -*- coding: utf-8 -*-
import json
from mono import call
BP = '/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
G  = 'UpdateHookshotLand'
I  = json.load(open('ids_swinglatch.json'))

def ok(tag, r):
    bad = (not isinstance(r, dict)) or r.get('success') is False or '_text' in r
    print(('FAIL ' if bad else 'ok   ') + tag, json.dumps(r, ensure_ascii=False)[:160])
    if bad: raise SystemExit('stop at ' + tag)
def link(a, ap, b, bp_):
    ok('link %s.%s->%s.%s' % (a, ap, b, bp_), call('blueprint_query','connect_pins',
        {'asset_path':BP,'graph_name':G,'source_node':a,'source_pin':ap,'target_node':b,'target_pin':bp_}))
def unlink(n, pin):
    ok('unlink %s.%s' % (n, pin), call('blueprint_query','disconnect_pins',
        {'asset_path':BP,'graph_name':G,'node_id':n,'pin_name':pin}))
def pindef(n, pin, val):
    ok('pin %s.%s=%s' % (n,pin,val), call('blueprint_query','set_pin_default',
        {'asset_path':BP,'graph_name':G,'node_id':n,'pin_name':pin,'value':val}))

# --- 조건: isSwing AND NOT bHookSwingDirLatched ---
link(I['getLatched'],'bHookSwingDirLatched', I['notL'],'A')
link('K2Node_CallFunction_4','ReturnValue', I['andL'],'A')   # Equal(Byte) = isSwing
link(I['notL'],'ReturnValue', I['andL'],'B')
link(I['andL'],'ReturnValue', I['br'],'Condition')

# --- 시작→타깃 각도 (CallFunction_53 = TargetLocation - HookStartLocation) ---
link('K2Node_CallFunction_53','ReturnValue', I['brk'],'InVec')
link('K2Node_CallFunction_53','ReturnValue', I['lxy'],'A')
link(I['brk'],'Z',          I['at2'],'Y')
link(I['lxy'],'ReturnValue',I['at2'],'X')

# --- 래치 값 ---
link(I['at2'],'ReturnValue', I['setPitch'],'HookSwingStartPitch')
link('K2Node_CallFunction_56','ReturnValue', I['setDist'],'HookSwingStartDist')
pindef(I['setLatched'],'bHookSwingDirLatched','true')
pindef(I['resetLatched'],'bHookSwingDirLatched','false')

# --- exec: IfThenElse_0 앞에 래치 브랜치 삽입 ---
unlink('K2Node_VariableSet_6','then')
unlink('K2Node_Knot_4','OutputPin')
link('K2Node_VariableSet_6','then',  I['br'],'execute')
link('K2Node_Knot_4','OutputPin',    I['br'],'execute')
link(I['br'],'then', I['setPitch'],'execute')
link(I['setPitch'],'then', I['setDist'],'execute')
link(I['setDist'],'then',  I['setLatched'],'execute')
link(I['setLatched'],'then','K2Node_IfThenElse_0','execute')
link(I['br'],'else','K2Node_IfThenElse_0','execute')

# --- exec: Casting 에서 래치 리셋 (Set HookStartLocation 직후) ---
unlink('K2Node_VariableSet_26','then')
link('K2Node_VariableSet_26','then', I['resetLatched'],'execute')
link(I['resetLatched'],'then','K2Node_Knot_2','InputPin')

# --- Select 소스 교체: 스윙 = 래치값 ---
unlink('K2Node_CallFunction_17','A')
link(I['getPitch'],'HookSwingStartPitch','K2Node_CallFunction_17','A')
unlink('K2Node_CallFunction_39','A')
link(I['getDist'],'HookSwingStartDist','K2Node_CallFunction_39','A')
print('DONE')
