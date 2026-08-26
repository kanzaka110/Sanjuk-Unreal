# -*- coding: utf-8 -*-
"""8/26 스윙 LandDir 시작-시점 래치.
스윙일 때 HookshotLandDir 을 '발사 시점 내 높이 vs 타깃 높이' 로 한 번만 판정하고 고정한다."""
import json
from mono import call

BP = '/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
G  = 'UpdateHookshotLand'

def ok(tag, r):
    bad = (not isinstance(r, dict)) or r.get('success') is False or '_text' in r
    print(('FAIL ' if bad else 'ok   ') + tag, json.dumps(r, ensure_ascii=False)[:200])
    if bad:
        raise SystemExit('stop at ' + tag)
    return r

def addvar(name, typ, default, cat):
    return ok('var ' + name, call('blueprint_query', 'add_variable', {
        'asset_path': BP, 'name': name, 'type': typ,
        'default_value': default, 'category': cat, 'instance_editable': True}))

def addnode(tag, **kw):
    p = {'asset_path': BP, 'graph_name': G}
    p.update(kw)
    r = ok('node ' + tag, call('blueprint_query', 'add_node', p))
    return r.get('node_id') or r.get('id')

def link(a, ap, b, bp_):
    return ok('link %s.%s -> %s.%s' % (a, ap, b, bp_), call('blueprint_query', 'connect_pins', {
        'asset_path': BP, 'graph_name': G,
        'source_node': a, 'source_pin': ap, 'target_node': b, 'target_pin': bp_}))

def unlink(n, pin):
    return ok('unlink %s.%s' % (n, pin), call('blueprint_query', 'disconnect_pins', {
        'asset_path': BP, 'graph_name': G, 'node_id': n, 'pin_name': pin}))

def pindef(n, pin, val):
    return ok('pin %s.%s=%s' % (n, pin, val), call('blueprint_query', 'set_pin_default', {
        'asset_path': BP, 'graph_name': G, 'node_id': n, 'pin_name': pin, 'value': val}))

# ---------- 1. 변수 ----------
addvar('HookSwingStartPitch', 'double', '0.0', 'Hookshot')
addvar('HookSwingStartDist',  'double', '0.0', 'Hookshot')
addvar('bHookSwingDirLatched', 'bool',  'false', 'Hookshot')

ids = {}
# ---------- 2. 래치 조건 ----------
ids['getLatched'] = addnode('getLatched', node_type='VariableGet', variable_name='bHookSwingDirLatched', position=[640, 1000])
ids['notL']  = addnode('notL',  node_type='CallFunction', function_name='Not_PreBool', target_class='KismetMathLibrary', position=[790, 1000])
ids['andL']  = addnode('andL',  node_type='CallFunction', function_name='BooleanAND',  target_class='KismetMathLibrary', position=[880, 900])
ids['br']    = addnode('br',    node_type='Branch', position=[1000, 800])

# ---------- 3. 시작→타깃 각도 (로컬 계산, 소스는 기존 CallFunction_53 = TargetLocation - HookStartLocation) ----------
ids['brk']  = addnode('brk',  node_type='CallFunction', function_name='BreakVector', target_class='KismetMathLibrary', position=[620, 1180])
ids['lxy']  = addnode('lxy',  node_type='CallFunction', function_name='VSizeXY',     target_class='KismetMathLibrary', position=[620, 1310])
ids['at2']  = addnode('at2',  node_type='CallFunction', function_name='DegAtan2',    target_class='KismetMathLibrary', position=[810, 1220])

# ---------- 4. 래치 Set 3종 ----------
ids['setPitch']   = addnode('setPitch',   node_type='VariableSet', variable_name='HookSwingStartPitch',  position=[1180, 800])
ids['setDist']    = addnode('setDist',    node_type='VariableSet', variable_name='HookSwingStartDist',   position=[1400, 800])
ids['setLatched'] = addnode('setLatched', node_type='VariableSet', variable_name='bHookSwingDirLatched', position=[1620, 800])

# ---------- 5. Casting 리셋 ----------
ids['resetLatched'] = addnode('resetLatched', node_type='VariableSet', variable_name='bHookSwingDirLatched', position=[960, -160])

# ---------- 6. Select 소스용 Get ----------
ids['getPitch'] = addnode('getPitch', node_type='VariableGet', variable_name='HookSwingStartPitch', position=[2048, 430])
ids['getDist']  = addnode('getDist',  node_type='VariableGet', variable_name='HookSwingStartDist',  position=[880, 610])

json.dump(ids, open('ids_swinglatch.json', 'w'), ensure_ascii=False)
print(json.dumps(ids, ensure_ascii=False, indent=1))
