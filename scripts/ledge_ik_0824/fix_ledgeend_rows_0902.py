# -*- coding: utf-8 -*-
"""렛지 End 행을 올바른 서브(*_Moving)에 배치 (9/2)
   실측 Exit: PrevMM=8, bTransitMoving=true, bTransitingToNextLedge=true,
              bNextFrontBlocked=false, bFrontBlocked=false, ang=-175.5/121.4/-95.7/176.6 ...
   루트가 bTransitMoving 으로 갈리므로 TM=true → *_Moving 서브가 정답.
   서브 컬럼: 0 PrevMovementMode(Enum) 1 TransitMoveAngleDeg(FloatRange)
              2 bTransitingToNextLedge(Bool) 3 bNextFrontBlocked(Bool) 4 OutputStruct
"""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ch=lambda a,p: call('chooser_query',a,p)
B='/Game/Art/Character/PC/PC_01/StateMachine/CustomMove/LedgeMoving.LedgeMoving:'
ANI='/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/'
# (각도min, 각도max, 설명)
ANG=[(-45.0,  45.0, '위쪽 기어오르기', 'GoUp'),
     (135.0, 180.0, '아래(직하 우)',   'Cancel'),
     (-180.0,-135.0,'아래(직하 좌)',   'Cancel'),
     (45.0,  135.0, '측방-아래 대각(우)','Cancel'),
     (-135.0,-45.0, '측방-아래 대각(좌)','Cancel')]
TARGETS=[('Wall_Moving',      'P_Player_Ledge_End_%s'),
         ('Wallless_Moving',  'P_Player_Ledge_End_%s_Wallless')]
for sub,fmt in TARGETS:
    before=ch('inspect_chooser',{'asset_path':B+sub})['row_count']
    print('==',sub,'(추가 전 %d행)'%before)
    for lo,hi,desc,kind in ANG:
        anim=fmt%kind
        r=ch('add_chooser_row',{'asset_path':B+sub,
                                'cells':[8,{'min':lo,'max':hi},True,False],
                                'output_psd':ANI+anim})
        print('   +행 ang[%7.1f,%7.1f] %-18s → %s'%(lo,hi,desc,anim.replace('P_Player_Ledge_','')))
    after=ch('inspect_chooser',{'asset_path':B+sub})['row_count']
    print('   %d행 → %d행'%(before,after))
