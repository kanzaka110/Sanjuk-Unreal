# -*- coding: utf-8 -*-
"""방향별 렛지 End — 2단계: LedgeEnd 챠저 생성 (bool 3열 × 8행)"""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
import json
ch=lambda a,p: call('chooser_query',a,p)
C='/Game/Art/Character/PC/PC_01/StateMachine/CustomMove/LedgeEnd'
ABP='/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP.PC_01_ABP_C'
ANI='/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/'

print('1) 테이블 생성')
r=ch('create_chooser_table',{'asset_path':C,'output_type':'ObjectResult',
                             'output_class':'/Script/Engine.AnimationAsset','context_class':ABP})
print('  ',json.dumps(r,ensure_ascii=False)[:200])

print('2) 입력 컬럼 3종 (bool)')
for b in ['bLedgeEndUp','bLedgeEndJump','bLedgeEndWall']:
    r=ch('add_chooser_column',{'asset_path':C,'column_kind':'Bool','binding_property':b})
    print('  ',b,r.get('success',r))

print('3) 행 8개')
# (Up, Jump, Wall) -> 애님
ROWS=[(False,False,True ,'P_Player_Ledge_End_Cancel'),
      (False,False,False,'P_Player_Ledge_End_Cancel_Wallless'),
      (False,True ,True ,'P_Player_Ledge_End_BackwardJump'),
      (False,True ,False,'P_Player_Ledge_End_BackwardJump_Wallless'),
      (True ,False,True ,'P_Player_Ledge_End_GoUp'),
      (True ,False,False,'P_Player_Ledge_End_GoUp_Wallless'),
      (True ,True ,True ,'P_Player_Ledge_End_JumpUp'),
      (True ,True ,False,'P_Player_Ledge_End_JumpUp_Wallless')]
for up,jp,wl,anim in ROWS:
    r=ch('add_chooser_row',{'asset_path':C,'cells':[up,jp,wl],'output_psd':ANI+anim})
    print('  ',anim,r.get('success',r))

print('4) 검증')
v=ch('inspect_chooser',{'asset_path':C,'include_cells':True})
print('   rows',v['row_count'],'cols',v['column_count'],'compiled',v.get('compiled'))
print('   context',json.dumps(v['context_data'],ensure_ascii=False)[:300])
for c in v['columns']:
    b=c.get('input_binding') or {}
    print('   col',c['index'],c['type'],'|',b.get('display'),'|',
          [cell.get('value') for cell in (c.get('cells') or [])])
for a in v['referenced_assets']:
    print('   row',a['row'],(a['asset'].split('/')[-1] if a['asset'] else 'NULL'))
