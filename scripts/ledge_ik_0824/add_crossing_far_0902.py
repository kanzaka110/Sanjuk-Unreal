# -*- coding: utf-8 -*-
"""LedgeMoving 에 Crossing_Far (멀리 뛰기) 추가 (9/2)
   Near/Far 는 LedgeMoveData.NextLedgeCandidateDist 로 가른다 (임계 100, 승호 지정).
   서브별 담당 벽쌍:
     Wall_Moving(NextFront=false)     → Crossing_Far_*_WallToWallless
     Wall_Jump(NextFront=true)        → Crossing_Far_*_WallToWall
     Wallless_Moving(NextFront=false) → Crossing_Far_*_WalllessToWallless
     Wallless_Jump(NextFront=true)    → Crossing_Far_*_WalllessToWall
   ※ 컬럼 추가 시 기존 행 셀이 [0,0] 으로 오염되므로 즉시 복구한다.
"""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ch=lambda a,p: call('chooser_query',a,p)
R='/Game/Art/Character/PC/PC_01/StateMachine/CustomMove/LedgeMoving'; B=R+'.LedgeMoving:'
ANI='/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/'
FLT=3.402823466e38; NEG=-1.0e30
NEAR=(NEG,100.0); FAR=(100.001,FLT); ALL=(NEG,FLT)
ANG=[(0,-25.0,25.0),(45,26.0,74.0),(90,75.0,115.0),(135,116.0,154.0),
     (180,155.0,180.0),(180,-180.0,-155.0),(225,-154.0,-116.0),(270,-115.0,-75.0),(315,-74.0,-26.0)]
TARGETS=[('Wall_Moving','WallToWallless',False),('Wall_Jump','WallToWall',True),
         ('Wallless_Moving','WalllessToWallless',False),('Wallless_Jump','WalllessToWall',True)]

for sub,wp,nextf in TARGETS:
    d=ch('inspect_chooser',{'asset_path':B+sub,'include_cells':True})
    order=[(c['index'],(c.get('input_binding') or {}).get('display')) for c in d['columns'] if c['type']!='OutputStructColumn']
    assets={a['row']:(a['asset'].split('/')[-1].split('.')[0].replace('P_Player_Ledge_','') if a['asset'] else 'NULL') for a in d['referenced_assets']}
    print('==',sub,d['row_count'],'행')
    res=ch('add_chooser_column',{'asset_path':B+sub,'column_kind':'FloatRange',
                                 'binding_property':'LedgeMoveData.NextLedgeCandidateDist'})
    DI=res['column_index']; print('   dist 컬럼 index',DI)
    # 기존 행 복구: Crossing_* 은 Near, 나머지는 전범위
    for r in range(d['row_count']):
        lo,hi = NEAR if assets.get(r,'').startswith('Crossing_') else ALL
        ch('set_chooser_cell',{'asset_path':B+sub,'column_index':DI,'row_index':r,'float_min':lo,'float_max':hi})
    print('   기존 %d행 dist 복구 (Crossing=Near, 나머지=전범위)'%d['row_count'])
    # Far 행 추가
    names=[n for _,n in order]
    n=0
    for a,lo,hi in ANG:
        cells=[]
        for idx,disp in order:
            if disp=='LedgeMoveData.TransitMoveAngleDeg': cells.append({'min':lo,'max':hi})
            elif disp=='LedgeMoveData.bTransitingToNextLedge': cells.append(True)
            elif disp=='LedgeMoveData.bNextFrontBlocked': cells.append(nextf)
            elif disp=='LedgeMoveData.NextLedgeCandidateDist': cells.append({'min':FAR[0],'max':FAR[1]})
            else: cells.append(True)
        cells.append({'min':FAR[0],'max':FAR[1]})   # 새로 추가된 dist 컬럼(맨 뒤)
        anim='P_Player_Ledge_Crossing_Far_%d_%s'%(a,wp)
        try:
            ch('add_chooser_row',{'asset_path':B+sub,'cells':cells,'output_psd':ANI+anim}); n+=1
        except Exception as e:
            print('   FAIL',anim,str(e)[:110])
    after=ch('inspect_chooser',{'asset_path':B+sub})['row_count']
    print('   Far %d행 추가 → 총 %d행'%(n,after))
