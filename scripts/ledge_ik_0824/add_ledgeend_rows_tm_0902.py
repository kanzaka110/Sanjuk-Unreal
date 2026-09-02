# -*- coding: utf-8 -*-
"""방향별 렛지 End — bTransitMoving=true 변종 10행 추가 (9/2)
   RPC가 Bool 'any' 를 못 써서(무음 false 고정) true/false 두 벌로 커버한다."""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
ch=lambda a,p: call('chooser_query',a,p)
C='/Game/Art/Character/PC/PC_01/StateMachine/CustomMove/LedgeMoving'
ANI='/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/'
ROWS=[
 (135.0, 180.0, True , 'P_Player_Ledge_End_Cancel'),
 (135.0, 180.0, False, 'P_Player_Ledge_End_Cancel_Wallless'),
 (-180.0,-135.0, True , 'P_Player_Ledge_End_Cancel'),
 (-180.0,-135.0, False, 'P_Player_Ledge_End_Cancel_Wallless'),
 (45.0, 135.0, True , 'P_Player_Ledge_End_Cancel'),
 (45.0, 135.0, False, 'P_Player_Ledge_End_Cancel_Wallless'),
 (-135.0,-45.0, True , 'P_Player_Ledge_End_Cancel'),
 (-135.0,-45.0, False, 'P_Player_Ledge_End_Cancel_Wallless'),
 (-45.0, 45.0, True , 'P_Player_Ledge_End_GoUp'),
 (-45.0, 45.0, False, 'P_Player_Ledge_End_GoUp_Wallless'),
]
before=ch('inspect_chooser',{'asset_path':C})['row_count']
print('추가 전',before,'행')
for lo,hi,front,anim in ROWS:
    # cells: [PrevMM, Ang, bFrontBlocked, bTransitMoving(True), bTransiting(True), bNextFront(False)]
    ch('add_chooser_row',{'asset_path':C,'cells':[8,{'min':lo,'max':hi},front,True,True,False],
                          'output_psd':ANI+anim})
v=ch('inspect_chooser',{'asset_path':C,'include_cells':True})
print('추가 후',v['row_count'],'행 (기대',before+10,') compiled',v.get('compiled'))
cells={c['index']:{x['row']:x for x in (c.get('cells') or [])} for c in v['columns']}
assets={a['row']:(a['asset'].split('/')[-1].split('.')[0] if a['asset'] else 'NULL') for a in v['referenced_assets']}
print('--- End 행 전체 (53~) ---')
for r in range(53,v['row_count']):
    a=cells[1][r]
    print('  %2d | ang[%7s,%7s] front=%-5s TM=%-5s Tr=%-5s NF=%-5s | %s'%(
        r,a.get('min'),a.get('max'),cells[2][r].get('value'),cells[3][r].get('value'),
        cells[4][r].get('value'),cells[5][r].get('value'),assets.get(r,'?').replace('P_Player_Ledge_','')))
