# -*- coding: utf-8 -*-
from mono import call
import json
BP='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
G='UpdateHookshotLand'
txt = u"""[Hook] 8/26 스윙 LandDir = 발사 시점 높이 비교 1회 래치
스윙(BP_EM_Hookshot_Swing)은 직선 이동이 아니라 앵커를 도는 진자라 "진행 방향"이 매 틱 변한다.
→ 방향을 매 틱 재판정하지 않고, 발사 순간의 내 높이 vs 타깃 높이로 한 번만 정해서 고정한다.
  래치 조건 : isSwing AND NOT bHookSwingDirLatched   (Moving 첫 틱)
  래치 값   : HookSwingStartPitch = Atan2( TargetLocation - HookStartLocation )
              HookSwingStartDist  = | TargetLocation - HookStartLocation |
  리셋      : Casting 의 Set HookStartLocation 직후 (발사마다 1회)
  소비      : Select Float 두 개의 A 핀 (판정각 / 게이트). 비스윙은 기존 전체변위 경로 = B 핀
⚠ HookSwingTypeValue 는 byte 노브(기본 2). ESBHookshotType 은 C++ enum 이라 RPC 로 enum 변수를
   못 만든다 — 실측 순서 추정이 Landing/InAir/Swing 이라 2, PIE 로 확정 필요."""
r=call('blueprint_query','add_comment_node',{'asset_path':BP,'graph_name':G,'text':txt,'position':[560,660],'size':[1360,760]})
print(json.dumps(r,ensure_ascii=False)[:400])
