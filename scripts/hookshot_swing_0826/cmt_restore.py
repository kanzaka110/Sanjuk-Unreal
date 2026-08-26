# -*- coding: utf-8 -*-
from mono import call
import json
LAY='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
def rm(g,n): print('rm',n,call('blueprint_query','remove_node',{'asset_path':LAY,'graph_name':g,'node_id':n}).get('success'))
def add(g,txt,pos,size):
    r=call('blueprint_query','add_comment_node',{'asset_path':LAY,'graph_name':g,'text':txt,'position':pos,'size':size})
    nid=r.get('node_id')
    d=call('blueprint_query','get_node_details',{'blueprint_path':LAY,'graph_name':g,'node_id':nid})
    okk = d.get('title','').startswith(txt.split('\n')[0][:20])
    print(('ok   ' if okk else 'FAIL ')+g, nid, repr(d.get('title',''))[:70])
    return nid

rm('HookShot','EdGraphNode_Comment_1')  # TEST 제거

add('HookShot', u"""[Hook] 8/26 훅 타입별 조준 AO 2단
InPose → Ground AO → Swing AO → (스윙 기울기) → Out. 직렬 — 알파 0이면 베이스 포즈 그대로 통과.
  Ground(P_Player_Hook_Ground_AO)   알파 = bHookAiming AND NOT bHookIsSwing
  Swing (P_Player_HookSwing_Aim_AO) 알파 = bHookAiming AND     bHookIsSwing
  둘 다 Y = HookAimPitch (-60~60), AlphaInputType = Bool (AlphaBoolBlend 로 전환 스무딩)
bHookIsSwing 은 UpdateHookshotLand 진입부에서 매 틱 GetHookshotType() == HookSwingTypeValue 로 갱신.""",
 [-560,-320],[1000,190])

add('UpdateHookshotLand', u"""[Hook] 8/26 스윙 전용 처리 3종 (진입부)
스윙(BP_EM_Hookshot_Swing)은 직선 이동이 아니라 앵커를 도는 진자다
(SwingMinDistance 350 / SwingDamping 0.5 / AutoReleaseAngleDeg 35 / SwingMaxAngularSpeed 720 / SwingInputAccel 200).

① bHookIsSwing = SBCharacterMovement.GetHookshotType() == HookSwingTypeValue   ← 매 틱, Switch 앞
   ⚠ HookSwingTypeValue 는 byte 노브(기본 2). ESBHookshotType 은 C++ enum 이라 RPC 로 enum 변수를
     못 만든다. 실측 순서 추정이 Landing/InAir/Swing 이라 2 — PIE 로 확정 필요.

② 스윙 기울기 타깃 → 메인 ABP
   local = UnrotateVector( (0,캐릭터Yaw,0), 캐릭터위치 − TargetLocation )
   angle = Atan2( local.Y, −local.Z )     ← 앵커 바로 아래면 0, 좌/우로 벌어질수록 커짐
   게이트 = bHookIsSwing AND IsHookshotActive()  (아니면 0)
   → SetHookSwingLeanTarget(angle). 감쇠·클램프·적용은 메인 ABP + HookShot 그래프.

③ 스윙 LandDir 은 방향을 매 틱 재판정하지 않는다 → 아래 '발사시점 1회 래치' 코멘트 참조.""",
 [-2500,1000],[1300,420])

add('UpdateHookshotLand', u"""[Hook] 8/26 스윙 LandDir = 발사 시점 높이 비교 1회 래치
앵커를 도는 진자라 '진행 방향'이 매 틱 뒤집힌다 → 발사 순간의 내 높이 vs 타깃 높이로 한 번만 정해 고정.
  래치 조건 : bHookIsSwing AND NOT bHookSwingDirLatched   (Moving 첫 틱)
  래치 값   : HookSwingStartPitch = Atan2( TargetLocation − HookStartLocation )
              HookSwingStartDist  = | TargetLocation − HookStartLocation |
  리셋      : Casting 의 Set HookStartLocation 직후 (발사마다 1회)
  소비      : Select Float 두 개의 A 핀 (판정각 / 게이트). 비스윙은 기존 전체변위 경로 = B 핀
래치 후에도 매 틱 재평가는 돌지만 입력이 상수라 결과가 고정된다.""",
 [560,660],[1360,300])
