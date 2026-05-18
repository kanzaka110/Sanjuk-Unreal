---
name: PC_01 락온 측면 질주 정지 턴모션 작업 진행
description: 락온+측면 strafe 정지 시 턴모션 미발현 → 태그 수정으로 1차 해결. 잔존 이슈 root motion이 capsule에 안 들어가는 문제 진단 중.
type: project
originSessionId: 1ac42bc0-21a9-4ffe-b4a1-61251faca330
---
**증상**: 락온(Target Lock) 상태에서 측면 strafe run 후 정지 시 턴 모션 미재생 + idle로 자연 연결 안 됨.

**1차 원인 (해결됨, 2026-05-07)**: AnimSequence `P_Player_Fist_Battle_Sprint_turn_Stop`의 태그가 `Stop`이었음 → 사용자가 **`LockOn_TurnInPlace`로 수정**. 이제 모션은 재생됨.

**잔존 문제**: 모션은 나오지만 **root motion 회전이 capsule에 안 들어감**. mesh는 도는데 capsule은 정지 상태로 보임. "스무스하게 돌아가는" 시각 효과만 남음.

**확인된 실측 (Monolith)**:
- ABP CDO `RootMotionMode = RootMotionFromMontagesOnly` ← AnimSequence는 root motion 무시되는 모드
- OffsetRootBone 노드: RotationMode=Interpolate, RotationHalfLife=0.20s, MaxRotationError=-1, bUseManualRelease=true
- UpdateVariables 그래프 코멘트: "Set Reset Offset Pulse (PC_01_BP의 OnResetOffsetRootBoneEvent에서 Set)" — reset 메커니즘 이미 존재

**시도한 수정 (2026-05-07, 둘 다 효과 없음/회귀)**:
1. OffsetRootBone `MaxRotationError`: -1 → 45 (사용자가 변경. **현재 45 상태**. 효과 없음 — offset 크기 캡일 뿐 reset 아님). 원복 여부 미정.
2. ABP `RootMotionMode`: `RootMotionFromMontagesOnly` → `RootMotionFromEverything`. **캐릭터 자체가 안 움직임 → 즉시 원복 권장**. PC_01은 input-driven CMC 시스템이지 GASP root-motion-driven 패턴이 아님이 확인됨.

**Why:** PC_01은 CMC가 input으로 capsule을 움직이고 Motion Matching은 in-place 포즈만 매칭하는 구조. GASP의 "root motion이 진리" 패턴과 다름. 그래서 turn 시퀀스의 root rotation이 mesh엔 적용되지만 capsule엔 자동 전달 안 됨. OffsetRootBone가 그 차이를 200ms halflife로 흡수해서 시각적으로만 부드럽게 보임.

**How to apply (다음 단계 후보)**:
- **B 옵션 (가장 유력)**: Turn 시퀀스 첫 프레임에 노티파이 추가 → PC_01_BP의 `OnResetOffsetRootBoneEvent` 발화 → ResetOffsetPulse=true → mesh 회전을 capsule에 즉시 commit. 메커니즘 이미 ABP에 존재함.
- **A 옵션**: AnimNotify로 SetActorRotation 직접 호출 (manual, snap 위험)
- **검증 시도**: OffsetRootBone Rotation Mode를 Off로 임시 변경해서 회전이 들어가는지 확인 → 들어가면 OffsetRootBone 흡수가 맞고 B 옵션 정확
- 다음 세션 시작 시: PC_01_BP의 `OnResetOffsetRootBoneEvent`가 어디서 호출되는지 검색 (Monolith `blueprint_query search_nodes`).

**2026-05-12 처방 1 적용 — TranslationMode 항상 Release (Inspector 가설 A)**:
- 가설: `GetOffsetRootTranslationMode` ELSE 분기 (Loop=false일 때)가 Interpolate를 반환 → strafe 정지 시 Release→Interpolate 전환이 1틱 mesh 점프 유발.
- 변경: K2Node_FunctionResult_3 (NodeGuid `7B3A09224A4131C4BC9D5F9FEB04D418`, pos [2048,176], IfThenElse_9.else 입력) ReturnValue default `Interpolate` → `Release`.
- 변경 전 dump 인용: `"default_value":"Interpolate"` (raw API). 이전 세션 Tuner는 FunctionResult_0(pos[2048,0], 항상 Release)를 보고 착각했던 것으로 추정.
- 변경 후 dump: `"default_value":"Release"` 확인. 컴파일 UpToDate, errors 0.
- Save API는 P4 read-only로 실패하지만 `reference_monolith_animgraph_editing_limits.md`에 따라 디스크 적용은 됨.
- PIE 검증 포인트: (1) 락온+측면 strafe→정지 시 mesh 1틱 점프 사라졌는가, (2) 일반 Walk/Run 종료 시 mesh가 root에 release되어 "느슨한" 느낌 강해졌는가.
- 원복: K2Node_FunctionResult_3 ReturnValue `Release` → `Interpolate`.
