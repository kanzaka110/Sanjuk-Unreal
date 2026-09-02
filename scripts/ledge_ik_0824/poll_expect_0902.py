# -*- coding: utf-8 -*-
"""챠저 기대값 vs 실제 애님 대조 폴러 (9/2)
   LedgeAll_Test 셀을 로컬로 읽어 매 샘플 '나와야 할 애님'을 계산하고,
   실제 BlendStackInputs 와 비교해 불일치(=늦음/안나옴) 구간을 기록한다."""
import sys, time, json, re
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ed = lambda a,p: call('editor_query', a, p)
ch = lambda a,p: call('chooser_query', a, p)
C='/Game/Art/Character/PC/PC_01/StateMachine/CustomMove/LedgeAll_Test'

v = ch('inspect_chooser', {'asset_path':C, 'include_cells':True})
CELLS = {c['index']:{x['row']:x for x in (c.get('cells') or [])} for c in v['columns']}
ASSET = {a['row']:(a['asset'].split('/')[-1].split('.')[0] if a['asset'] else None) for a in v['referenced_assets']}
NROW = v['row_count']

def match(r, vals):
    for i, val in enumerate(vals):
        c = CELLS.get(i, {}).get(r)
        if not c: continue
        if 'min' in c:
            if not (c['min'] <= val <= c['max']): return False
        elif isinstance(val, bool):
            cv = str(c.get('value')).lower()
            if cv in ('any','none'): continue
            if (cv == 'true') != val: return False
        else:
            cmp, cv = c.get('comparison'), c.get('value')
            if cmp == 0 and cv != val: return False
            if cmp == 1 and cv == val: return False
    return True

def expect(vals):
    for r in range(NROW):
        if ASSET.get(r) and match(r, vals): return r, ASSET[r]
    return None, None

PROPS = ['LedgeMoveData','bTransitMoving','PrevMovementMode','MovementMode',
         'StateMachineMoveState','BlendStackInputs']
ANIM_RE = re.compile(r"/Game/[^'\"]+?\.([A-Za-z0-9_]+)")
ENUM_RE = re.compile(r'NewEnumerator(\d+)')
MAX = float(sys.argv[1]) if len(sys.argv) > 1 else 240.0

t0=time.time(); log=[]; last=None; mismatch_since=None
print('기대 vs 실제 대조 — 렛지에서 여러 동작 해줘 (최대 %.0fs)'%MAX, flush=True)
while time.time()-t0 < MAX:
    try:
        p = (ed('pie_get_object_properties', {'class_name':'PC_01','anim_instance':True,
                                              'properties':PROPS})).get('properties') or {}
    except Exception as e:
        if 'PIE not running' in str(e): time.sleep(1); continue
        time.sleep(0.3); continue
    d = str(p.get('LedgeMoveData'))
    def g(k, dv=None):
        m = re.search(k + r'=([^,)]+)', d)
        return m.group(1) if m else dv
    def fnum(k, dv=0.0):
        s = g(k)
        try: return float(s)
        except: return dv
    front = (g('bFrontBlocked','False') == 'True')
    nextf = (g('bNextFrontBlocked','False') == 'True')
    tr    = (g('bTransitingToNextLedge','False') == 'True')
    tm    = (str(p.get('bTransitMoving')) == 'True')
    angv  = fnum('TransitMoveAngleDeg', 0.0)
    distv = fnum('NextLedgeCandidateDist', 3.402823466e38)
    dirv  = fnum('LastNonZeroDirection', 0.0)
    mode  = {'Cross':0,'Jump':1,'Exit':2}.get(g('PendingTransitMode','Cross'), 0)
    tgt   = {'Ledge':0,'Bar':1,'Ladder':2}.get(g('PendingTransitTarget','Ledge'), 0)
    pmm   = ENUM_RE.search(str(p.get('PrevMovementMode')))
    pm    = int(pmm.group(1)) if pmm else 0
    mmm   = ENUM_RE.search(str(p.get('MovementMode')))
    mm    = mmm.group(1) if mmm else '?'
    smsm  = ENUM_RE.search(str(p.get('StateMachineMoveState')))
    sms   = smsm.group(1) if smsm else '?'
    vals = [front, nextf, angv, distv, dirv, tr, tm, mode, tgt, pm]
    row, exp = expect(vals)
    am = ANIM_RE.search(str(p.get('BlendStackInputs')))
    act = am.group(1) if am else 'None'
    bad = (exp is not None and act != exp)
    if bad and mismatch_since is None: mismatch_since = time.time()
    if not bad: mismatch_since = None
    key = (exp, act)
    if key != last:
        last = key
        lag = (time.time()-mismatch_since) if mismatch_since else 0.0
        rec = dict(t=round(time.time()-t0,2), MM=mm, SMS=sms, mode=g('PendingTransitMode','-'),
                   ang=round(angv,1), tr=tr, tm=tm, front=front, pm=pm,
                   expect=exp, actual=act, ok=(not bad))
        log.append(rec)
        print('  t=%6.2f MM=%-2s SMS=%-2s %-6s ang=%-7.1f tr=%-5s tm=%-5s pm=%-2d | 기대 %-34s 실제 %-34s %s'%(
            rec['t'], mm, sms, rec['mode'], rec['ang'], tr, tm, pm,
            (exp or '-')[:34], act[:34], '' if not bad else '★불일치'), flush=True)
    time.sleep(0.03)
json.dump(log, open('poll_expect_vs_actual.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
tot=len(log); badn=sum(1 for r in log if not r['ok'])
print('--- 전환 %d회 / 불일치 %d회 ---'%(tot,badn), flush=True)
