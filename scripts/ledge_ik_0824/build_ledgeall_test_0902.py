# -*- coding: utf-8 -*-
"""LedgeAll_Test 챠저 — LedgeClimbing 애님 134종 전수 커버 (9/2, 테스트용)
컬럼: 0 bFrontBlocked 1 bNextFrontBlocked 2 TransitMoveAngleDeg 3 NextLedgeCandidateDist
      4 LastNonZeroDirection 5 bTransitingToNextLedge 6 bTransitMoving
      7 PendingTransitMode 8 PendingTransitTarget 9 PrevMovementMode
Near/Far 임계 = 100cm (승호 지정). Mode: Cross=0 Exit=2 (실측).
Target/PrevMovementMode 일부는 값 미상 → 추정치, 에디터 드롭다운에서 조정 가능.
"""
import os, re, json, sys
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ch = lambda a,p: call('chooser_query', a, p)
C   = '/Game/Art/Character/PC/PC_01/StateMachine/CustomMove/LedgeAll_Test'
ANI = '/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/'
SRC = r'E:\Perforce\SB2\Workspace\Internal\SB2\Content\Art\Character\PC\PC_01\Animation\Body\LedgeClimbing'

ANY_F   = {'min':-999999.0,'max':999999.0}
NEAR    = {'min':0.0,'max':100.0}
FAR     = {'min':100.001,'max':999999.0}
DIR_L   = {'min':-999.0,'max':-0.001}
DIR_R   = {'min':0.001,'max':999.0}
ANG8 = {0:(-25.0,25.0), 45:(26.0,74.0), 90:(75.0,115.0), 135:(116.0,154.0),
        180:(155.0,180.0), 225:(-154.0,-116.0), 270:(-115.0,-75.0), 315:(-74.0,-26.0)}
def ang(a): 
    lo,hi = ANG8[int(a)]; return {'min':lo,'max':hi}
WALLPAIR = {'WallToWall':(True,True), 'WallToWallless':(True,False),
            'WalllessToWall':(False,True), 'WalllessToWallless':(False,False)}
CROSS, EXIT = 0, 2
TGT_LEDGE, TGT_BAR, TGT_LADDER = 0, 1, 2
PM_LEDGE, PM_FALL, PM_GROUND, PM_ROOF = 8, 4, 1, 7

names = [f[:-7] for f in os.listdir(SRC) if f.endswith('.uasset')]
names = [n.replace('P_Player_Ledge_','') for n in names]
names = [n for n in names if not n.startswith('LedgeSeeking') and not n.startswith('BS_')]
rows = []   # (정렬키, 설명, cells, 애님이름)
def R(order, desc, anim, front, nextf, a, dist, d, tr, tm, mode, tgt, pm):
    rows.append((order, desc, [front, nextf, a, dist, d, tr, tm, mode, tgt, pm], anim))

for n in sorted(names):
    # --- End (Mode=Exit) ---
    m = re.match(r'^End_(\w+?)(_Wallless)?$', n)
    if m and m.group(1) in ('Cancel','GoUp','JumpUp','BackwardJump'):
        kind, wl = m.group(1), bool(m.group(2)); front = not wl
        a = {'Cancel':ang(180),'BackwardJump':ang(225),'GoUp':ang(0),'JumpUp':ang(45)}[kind]
        R(10, 'End %s %s'%(kind,'Wallless' if wl else 'Wall'), n,
          front, False, a, ANY_F, ANY_F, True, True, EXIT, TGT_LEDGE, PM_LEDGE); continue
    # --- ToBar / ToLadder ---
    m = re.match(r'^ToBar_Far_(Wallless_)?(\d+)$', n)
    if m:
        wl = bool(m.group(1)); front = not wl
        R(20, 'ToBar %s %s'%(m.group(2),'Wallless' if wl else 'Wall'), n,
          front, False, ang(m.group(2)), FAR, ANY_F, True, True, CROSS, TGT_BAR, PM_LEDGE); continue
    m = re.match(r'^ToLadder_Far_(\d+)$', n)
    if m:
        R(21, 'ToLadder %s'%m.group(1), n,
          True, False, ang(m.group(1)), FAR, ANY_F, True, True, CROSS, TGT_LADDER, PM_LEDGE); continue
    # --- Corner (Far 먼저) ---
    m = re.match(r'^Corner_(Far_)?90([LR])_(\w+)$', n)
    if m:
        far, lr, wp = bool(m.group(1)), m.group(2), m.group(3)
        f, nf = WALLPAIR[wp]
        R(30 if far else 31, 'Corner%s 90%s %s'%(' Far' if far else '', lr, wp), n,
          f, nf, ang(270 if lr=='L' else 90), FAR if far else NEAR,
          DIR_L if lr=='L' else DIR_R, True, True, CROSS, TGT_LEDGE, PM_LEDGE); continue
    # --- Crossing ---
    m = re.match(r'^Crossing_(Near|Far)_(\d+)(_0[12])?_(\w+)$', n)
    if m:
        far = (m.group(1)=='Far'); a = m.group(2); var = m.group(3); wp = m.group(4)
        f, nf = WALLPAIR[wp]
        R(40 if far else 41, 'Crossing %s %s%s %s'%(m.group(1),a,var or '',wp), n,
          f, nf, ang(a), FAR if far else NEAR, ANY_F, True, True, CROSS, TGT_LEDGE, PM_LEDGE); continue
    # --- Start ---
    m = re.match(r'^Start_(Falling|Ground|Rooftop)(_Wallless)?$', n)
    if m:
        kind, wl = m.group(1), bool(m.group(2)); front = not wl
        pm = {'Falling':PM_FALL,'Ground':PM_GROUND,'Rooftop':PM_ROOF}[kind]
        R(50, 'Start %s %s'%(kind,'Wallless' if wl else 'Wall'), n,
          front, False, ANY_F, ANY_F, ANY_F, False, False, CROSS, TGT_LEDGE, pm); continue
    # --- Move_Short ---
    m = re.match(r'^Move_Short([LR])(_0[12]|_Wallless)?$', n)
    if m:
        lr, var = m.group(1), (m.group(2) or '')
        wl = (var=='_Wallless'); front = not wl
        R(60, 'Move_Short%s%s'%(lr,var), n,
          front, False, ang(270 if lr=='L' else 90), ANY_F,
          DIR_L if lr=='L' else DIR_R, False, True, CROSS, TGT_LEDGE, PM_LEDGE); continue
    # --- MoveToIdle ---
    m = re.match(r'^MoveToIdle_(Wallless_)?([LR])$', n)
    if m:
        wl = bool(m.group(1)); front = not wl; lr = m.group(2)
        R(70, 'MoveToIdle %s %s'%(lr,'Wallless' if wl else 'Wall'), n,
          front, False, ANY_F, ANY_F, DIR_L if lr=='L' else DIR_R,
          False, False, CROSS, TGT_LEDGE, PM_LEDGE); continue
    # --- Idle ---
    m = re.match(r'^Idle(_Wallless)?$', n)
    if m:
        wl = bool(m.group(1)); front = not wl
        R(80, 'Idle %s'%('Wallless' if wl else 'Wall'), n,
          front, False, ANY_F, ANY_F, ANY_F, False, False, CROSS, TGT_LEDGE, PM_LEDGE); continue
    R(99, '미분류', n, True, False, ANY_F, ANY_F, ANY_F, False, False, CROSS, TGT_LEDGE, PM_LEDGE)

rows.sort(key=lambda x:(x[0], x[3]))
print('생성할 행:', len(rows), '(애님', len(names), ')', flush=True)
unmatched = [r for r in rows if r[0]==99]
if unmatched: print('★미분류', [r[3] for r in unmatched], flush=True)

ok = 0
for i,(order, desc, cells, anim) in enumerate(rows):
    try:
        ch('add_chooser_row', {'asset_path':C, 'cells':cells, 'output_psd':ANI+'P_Player_Ledge_'+anim})
        ok += 1
    except Exception as e:
        print('  FAIL', anim, str(e)[:110], flush=True)
    if (i+1) % 20 == 0: print('  ...%d/%d'%(i+1,len(rows)), flush=True)
v = ch('inspect_chooser', {'asset_path':C})
print('완료: 추가 %d / 테이블 %d행 %d컬럼 compiled=%s'%(ok, v['row_count'], v['column_count'], v.get('compiled')), flush=True)
json.dump([{'order':r[0],'desc':r[1],'anim':r[3]} for r in rows],
          open('ledgeall_test_rows.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
