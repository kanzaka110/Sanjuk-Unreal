---
name: pc01-movesidedir-yaw-rate
description: PC_01_ABP PoseSearchData_Moving.MaxControllerYawRate=0 (override) → trajectory 좌/우 굽음 0 → Sprint→Battle Jog _F_Lfoot만 매칭되던 문제 진단/처방. 70(native)로 복원 + RotateTowardsMovementSpeed=10도 자동 정상화. 2026-05-15.
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
  status: rolled_back_2026-05-15
---

# PC_01 Sprint→Battle 좌/우 오매칭 원인: PoseSearchData_Moving 디폴트

## 증상
- 사용자 호소 (2026-05-15): "질주 이후 모션이 P_Player_Transition_Sprint_to_Battle_Jog_F_Lfoot 만 나오는데 좌/우 이동시는 MoveSide 방향에 맞는 모션이 나와야 해"

## 진단 경로

1. PSD_GroundMovingTransit 에 클립 4종 모두 등록 확인 (F/B/LL/RL Lfoot)
2. PSS_SM_LocoTransitions Schema 확인: Group12 + Trajectory22 = cardinality 34
3. `PoseSearchHistoryCollector_0.bGenerateTrajectory=False` → 외부 trajectory 주입 필요
4. `Update Trajectory` 함수 그래프가 `PoseSearchGenerateTransformTrajectory(InTrajectoryData=PoseSearchData_Moving)` 호출하여 trajectory 자동 생성
5. **변수 비교 발견**:
   - `PoseSearchData_Moving` default = `(SpeedRemappingCurve=..., AccelerationRemappingCurve=...)` — **MaxControllerYawRate 필드 자체 없음 → struct 디폴트 0**
   - `PoseSearchData_Idle` default = `(MaxControllerYawRate=100.000000, SpeedRemappingCurve=..., ...)` — 명시
6. UE 5.7 native 디폴트 확인: `MaxControllerYawRate=70.f`, `RotateTowardsMovementSpeed=10.f`
   - Source: `Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/PoseSearchTrajectoryLibrary.h` 의 `FPoseSearchTrajectoryData` UPROPERTY 5필드
7. **결론**: 누군가 ABP CDO에서 Moving 의 yaw rate를 0으로 override → controller yaw clamp 0 → trajectory가 좌/우로 안 굽음 → Schema의 22채널 Trajectory cost가 4 변종 모두 동일 → Group12 cost 최저인 `_F_Lfoot` 매번 이김

## 처방 적용 (2026-05-15)

`set_variable_defaults` 액션으로 ABP `PoseSearchData_Moving` 디폴트 통째 교체.

**Before** (struct 디폴트 0):
```
(SpeedRemappingCurve=(EditorCurveData=(DefaultValue=3.4e+38, ...)),
 AccelerationRemappingCurve=(EditorCurveData=(DefaultValue=3.4e+38, ...)))
```

**After**:
```
(RotateTowardsMovementSpeed=10.000000,
 MaxControllerYawRate=70.000000,
 SpeedRemappingCurve=(...),
 AccelerationRemappingCurve=(...))
```

- `MaxControllerYawRate=70` 사용자 결정 (Idle 100보다 안전, native 디폴트). PIE에서 효과 부족 시 100 또는 -1(클램프 비활성)로 상향 가능
- `RotateTowardsMovementSpeed=10` 은 UE가 자동 보강 (native 디폴트, struct 누락 필드 추가)

## 검증
- `set_variable_defaults`: success=true
- `compile_blueprint`: success, errors=0, warnings=0
- `save_asset`: P4 잠금 실패 → 사용자 Ctrl+S 필요

## PIE 검증 시나리오
1. **좌 입력 + Sprint 종료**: `P_Player_Transition_Sprint_to_Battle_Jog_LL_Lfoot` 매칭되는지
2. **우 입력 + Sprint 종료**: `_RL_Lfoot` 매칭되는지
3. **후방 입력 + Sprint 종료**: `_B_Lfoot` 매칭되는지
4. **전방 입력 + Sprint 종료**: 기존대로 `_F_Lfoot` 매칭되는지 (회귀 X)
5. [ANIM_REC] `clip`, `trd`, `tta` 필드 확인

효과 부족하면 70 → 100 → -1 순으로 상향.

## 부수 사항

- `PoseSearchData_Moving.MaxControllerYawRate=0` 이 의도였을 가능성도 0이 아님 (Sprint 중 trajectory 회전 차단 목적). 사용자 호소 자체가 좌/우 매칭 회복이라 70으로 복원이 합리적 결정.
- `Rfoot` 변종도 존재 가능 — PSD_GroundMovingTransit grep 시 `_Lfoot` 4종만 확인됨. Rfoot 시리즈 누락 여부는 PIE에서 좌/우 발 시작 패턴 보면서 별도 검증 필요.
- `Update Trajectory` 그래프는 정상 — `Select(Speed2D>0)` 으로 Idle/Moving 분기, Moving 디폴트만 망가져 있어서 movement 시 trajectory 죽었던 것.

## 관련

- 매트릭스 처방 ② 와 별개 — 사용자 호소 응답
- MM 파이프라인 카탈로그: [[pc01-mm-pipeline]]
- Transition 회전 보정 차단 (5/15 ① 처방): [[pc01-transition-gate-phase1]]
- UE 5.7 source: `Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/PoseSearchTrajectoryLibrary.h` (FPoseSearchTrajectoryData struct)
- 캐시: `C:\Users\SHIFTUP\.claude\projects\C--Dev-Sanjuk-Unreal\cache\ue57\pose_search\PoseSearchTrajectoryLibrary.h` (5/15 추가)
