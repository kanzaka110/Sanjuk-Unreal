# -*- coding: utf-8 -*-
from mono import call
import json
LAY='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
txt = u"""[Hook] 8/26 스윙 좌우 기울기 — 앵커 기준 로프 각도만큼 몸을 꺾는다
훅이 걸린 지점(TargetLocation) 기준으로 캐릭터가 좌/우로 벌어진 각도 = 로프가 수직에서 기운 각도.
그 각도만큼 root 를 캐릭터 정면축 둘레로 돌려 시각적으로만 기울인다 (캡슐·카메라·C++ 회전은 손대지 않음).
  각도 계산 : 레이어 UpdateHookshotLand 진입부
              local = UnrotateVector( (0,캐릭터Yaw,0), 캐릭터위치 − TargetLocation )
              angle = Atan2( local.Y, −local.Z )      ← 바로 아래면 0, 옆으로 벌어질수록 커짐
              게이트 = bHookIsSwing AND IsHookshotActive()  (아니면 0)
              → 메인 ABP SetHookSwingLeanTarget(angle)
  감쇠/클램프: 메인 ABP UpdateHookSwingLean (스레드 세이프, BlueprintThreadSafeUpdateAnimation)
              desired = (HookshotPhase != None) ? Clamp(Target × Scale, ±Max) : 0
              HookSwingLeanAngle = FInterpTo(..., HookSwingLeanSpeed)
  적용      : 여기 ModifyBone(root) — Rotation = GetHookSwingLeanRotator()
              = RotatorFromAxisAndAngle( 캐릭터 정면벡터, HookSwingLeanAngle )
              RotationMode = Add to Existing / RotationSpace = World Space
노브: HookSwingLeanScale(1.0) / HookSwingLeanMax(60) / HookSwingLeanSpeed(10) — 전부 메인 ABP
⚠ 감쇠를 메인에 둔 이유: 훅샷이 끝나면 이 레이어가 틱을 멈춰서 여기서 감쇠시키면 각도가 얼어붙는다."""
r=call('blueprint_query','add_comment_node',{'asset_path':LAY,'graph_name':'HookShot','text':txt,'position':[640,340],'size':[1000,300]})
print(json.dumps(r,ensure_ascii=False)[:150])
for p in ['/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP', LAY]:
    c=call('blueprint_query','compile_blueprint',{'blueprint_path':p})
    print(p.split('/')[-1],c.get('status'),c.get('error_count'),c.get('warning_count'))
d=call('editor_query','list_dirty_packages',{})
print('dirty:',[x['package'] for x in d.get('dirty_packages',[])])
