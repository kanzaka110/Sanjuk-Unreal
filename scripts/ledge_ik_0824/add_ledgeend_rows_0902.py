# -*- coding: utf-8 -*-
"""방향별 렛지 End — LedgeMoving 챠저에 Exit 행 추가 (9/2)
   조건: PrevMovementMode==8(렛지) AND bTransitingToNextLedge==true AND 각도범위 AND bFrontBlocked
   기존 53행은 PrevMM==4(Crossing) / Transiting==false(같은 렛지 이동) 라 충돌 없음.
   컬럼: 0 PrevMovementMode(Enum) 1 TransitMoveAngleDeg(FloatRange) 2 bFrontBlocked(Bool)
         3 bTransitMoving(Bool) 4 bTransitingToNextLedge(Bool) 5 bNextFrontBlocked(Bool)
"""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
import json
ch=lambda a,p: call('chooser_query',a,p)
C='/Game/Art/Character/PC/PC_01/StateMachine/CustomMove/LedgeMoving'
ANI='/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/'

# (각도min, 각도max, bFrontBlocked, 애님, 설명)
ROWS=[
 (135.0, 180.0, True , 'P_Player_Ledge_End_Cancel',          '아래(직하) 발디딤'),
 (135.0, 180.0, False, 'P_Player_Ledge_End_Cancel_Wallless',  '아래(직하) 완전매달림'),
 (-180.0,-135.0, True , 'P_Player_Ledge_End_Cancel',          '아래(직하,좌측) 발디딤'),
 (-180.0,-135.0, False, 'P_Player_Ledge_End_Cancel_Wallless',  '아래(직하,좌측) 완전매달림'),
 (45.0, 135.0, True , 'P_Player_Ledge_End_Cancel',            '측방-아래 대각(우) 발디딤'),
 (45.0, 135.0, False, 'P_Player_Ledge_End_Cancel_Wallless',    '측방-아래 대각(우) 완전매달림'),
 (-135.0,-45.0, True , 'P_Player_Ledge_End_Cancel',           '측방-아래 대각(좌) 발디딤'),
 (-135.0,-45.0, False, 'P_Player_Ledge_End_Cancel_Wallless',   '측방-아래 대각(좌) 완전매달림'),
 (-45.0, 45.0, True , 'P_Player_Ledge_End_GoUp',              '위쪽 기어오르기 발디딤'),
 (-45.0, 45.0, False, 'P_Player_Ledge_End_GoUp_Wallless',      '위쪽 기어오르기 완전매달림'),
]

before=ch('inspect_chooser',{'asset_path':C})['row_count']
print('추가 전 행수',before)
for lo,hi,front,anim,desc in ROWS:
    cells=[8, {'min':lo,'max':hi}, front, 'any', True, 'any']
    r=ch('add_chooser_row',{'asset_path':C,'cells':cells,'output_psd':ANI+anim})
    print('  row+ %-28s ang[%7.1f,%7.1f] front=%-5s  %s  %s'%(
        anim.replace('P_Player_Ledge_',''),lo,hi,front,desc,r.get('success',r)))

v=ch('inspect_chooser',{'asset_path':C,'include_cells':True})
print('추가 후 행수',v['row_count'],'(기대 %d)'%(before+len(ROWS)),'compiled',v.get('compiled'))
