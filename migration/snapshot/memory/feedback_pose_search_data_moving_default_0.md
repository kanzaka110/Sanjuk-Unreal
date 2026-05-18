---
name: feedback-pose-search-data-moving-default-0
description: "PC_01_ABP `PoseSearchData_Moving.MaxControllerYawRate=0` 은 의도. UE 5.7 native 70/Idle 100과 다르게 0으로 둔 것은 trajectory 좌/우 굽음 차단 → MM cost 분산 방지 → A/D 노이즈 억제 목적. 변경 시 노이즈 폭증 부작용. 2026-05-15 실측 확인."
metadata: 
  node_type: memory
  type: feedback
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PoseSearchData_Moving.MaxControllerYawRate=0 은 의도, 손대지 말 것

## 룰
PC_01_ABP `PoseSearchData_Moving` 디폴트는 `(SpeedRemappingCurve=..., AccelerationRemappingCurve=...)` 만 — **MaxControllerYawRate/RotateTowardsMovementSpeed 명시 안 함 (struct 디폴트 0)**. UE 5.7 native 70 / Idle 100과 다르더라도 **0 유지**.

## Why
- 사용자 호소 (2026-05-15): "MaxControllerYawRate=70 적용 후 노이즈가 훨씬 심해졌는데???"
- 진단 가설: 70으로 풀면 trajectory가 좌/우 controller yaw에 따라 굽어버림 → PSS_SM_LocoTransitions의 Trajectory 채널 22개에 cost 분산 → MM이 매 프레임 다른 클립(Turn/Pivot/Reface 등) 매칭 가능 → A(Pose flicker) + D(Transition motion interjection) 동시 증폭
- 0 유지 시: trajectory 직선 forward만 → Trajectory cost 차이 없음 → Group12 cost로 안정적 매칭
- "Sprint→Battle 좌/우 매칭 안 됨" 호소는 다른 채널(Chooser row + MoveSide)로 풀어야 함, YawRate로는 푸는 게 부작용 큼

## How to apply
- `PoseSearchData_Moving.MaxControllerYawRate` / `RotateTowardsMovementSpeed` 두 필드 **명시적 0 또는 미설정 유지**
- `set_variable_defaults` 호출 시 UE가 native 디폴트로 자동 보강하는 패턴 주의 — 명시적으로 `MaxControllerYawRate=0.000000,RotateTowardsMovementSpeed=0.000000` 으로 override해야 진짜 0으로 잠금
- 좌/우 매칭 회복 시도는 **MM cost bias / Chooser row 좁히기 / PSD 분리** 방향 우선
- `PoseSearchData_Idle.MaxControllerYawRate=100` 은 정상 — Idle 진입 시에는 trajectory 회전 필요

## 관련
- 작업 이력 (취소됨): [[pc01-movesidedir-yaw-rate]] — 본 변경이 노이즈 폭증을 일으켜 같은 날 롤백
- ABP CDO PoseSearchTrajectoryData 필드 5개: `RotateTowardsMovementSpeed`, `MaxControllerYawRate`, `BendVelocityTowardsAcceleration`, `bUseSpeedRemappingCurve`, `bUseAccelerationRemappingCurve`. Source: `Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/PoseSearchTrajectoryLibrary.h`
- MM 파이프라인: [[pc01-mm-pipeline]]
