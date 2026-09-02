# -*- coding: utf-8 -*-
"""방향별 렛지 End — 1단계: ABP 래치 변수 추가"""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
bq=lambda a,p: call('blueprint_query',a,p)
A='/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP'
CAT='Custom Move|Ledge|End'
VARS=[('bLedgeEndUp','bool','위 입력으로 이탈 (GoUp/JumpUp 계열)'),
      ('bLedgeEndJump','bool','점프 입력으로 이탈 (BackwardJump/JumpUp 계열)'),
      ('bLedgeEndWall','bool','이탈 순간 bFrontBlocked 래치 (Wall/Wallless 분기)'),
      ('bLedgeEndFired','bool','End 애님 선택 대기 래치 — 소비 직후 리셋')]
have={v['name'] for v in bq('get_variables',{'asset_path':A})['variables']}
for n,t,desc in VARS:
    if n in have: print('skip(이미 있음)',n); continue
    r=bq('add_variable',{'asset_path':A,'name':n,'type':t,'category':CAT,
                         'default_value':'false','instance_editable':True})
    print('add',n,r.get('success',r))
after={v['name'] for v in bq('get_variables',{'asset_path':A})['variables']}
print('검증:',[n for n,_,_ in VARS if n in after],'/ 누락',[n for n,_,_ in VARS if n not in after])
