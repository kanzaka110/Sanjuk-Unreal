# -*- coding: utf-8 -*-
from mono import call
import json
BP='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_HookShot/PC_01_AnimLayer_Hookshot'
txt = u"""[Hook] 8/26 훅 타입별 조준 AO 2단
InPose → Ground AO → Swing AO → Out (직렬. 알파 0이면 베이스 포즈 그대로 통과)
  Ground(P_Player_Hook_Ground_AO) 알파 = bHookAiming AND NOT bHookIsSwing
  Swing (P_Player_HookSwing_Aim_AO) 알파 = bHookAiming AND bHookIsSwing
  둘 다 Y = HookAimPitch (-60~60), AlphaInputType = Bool (AlphaBoolBlend 로 부드럽게 전환)
bHookIsSwing 은 UpdateHookshotLand 진입부에서 매 틱 GetHookshotType() == HookSwingTypeValue 로 갱신."""
r=call('blueprint_query','add_comment_node',{'asset_path':BP,'graph_name':'HookShot','text':txt,'position':[128,-224],'size':[860,160]})
print(json.dumps(r,ensure_ascii=False)[:200])
c=call('blueprint_query','compile_blueprint',{'blueprint_path':BP})
print('compile:',c.get('status'),c.get('error_count'),c.get('warning_count'))
print(json.dumps(c.get('error_groups',[]),ensure_ascii=False)[:500])
