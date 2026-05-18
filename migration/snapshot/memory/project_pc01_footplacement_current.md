---
name: PC_01_ABP FootPlacement 실측값 (2026-04-20)
description: Monolith CDO 덤프로 확정한 PC_01_ABP + AnimLayer_IK의 FootPlacement 전체 파라미터. 2단 구조(노드 내부+핀주입) 정리.
type: project
originSessionId: c0b37efc-71b6-4348-a2e2-afba5093f18e
---
## 아키텍처

PC_01_ABP는 FootPlacement 설정을 **2단**으로 관리:
1. **노드 내부 고정**: PelvisSettings, TraceSettings, LegDefinitions (PC_01_AnimLayer_IK의 FootPlacement 노드)
2. **핀 주입(동적)**: PlantSettings, InterpolationSettings (PC_01_ABP의 `GetFootPlacementPlantSettings` / `GetFootPlacementInterpolationSettings` 함수가 상태별로 선택)

## 상태별 Plant 선택 로직 (GetFootPlacementPlantSettings)

```
IsFullBodySlotActive → PlantSettingsFullBody
IsLockOn            → PlantSettingsStop
OverlayWeight >= 1  → PlantSettingsStop
CurrentAnimTags 매칭 → PlantSettingsStop
기타               → PlantSettingsDefault
```

## 노드 내부 PelvisSettings (⚠️ 슬로프 튜닝 대상)

| 필드 | 현재 | UE5.7 기본 | 메모 |
|---|---|---|---|
| MaxOffset | 50 | 50 | 슬로프에서 ±50cm 허용 |
| LinearStiffness | 250 | 350 | 부드러움 |
| LinearDamping | 1.2 | 1.0 | 오버슛 억제 |
| HorizontalRebalancingWeight | 0.65 | 0.3 | 좌우 흔들림 강 |
| HeelLiftRatio | 0.6 | 0.5 | 약간 힐 우선 |
| **PelvisHeightMode** | **AllLegs** | AllLegs | ⚠️ 슬로프 부적합 — FrontPlantedFeetUphill_FrontFeetDownhill 권장 |
| ActorMovementCompensationMode | SuddenMotionOnly | SuddenMotionOnly | 기본 |

## 노드 내부 TraceSettings

```
StartOffset = -30  (기본 -75, 얕음 → 큰 계단에서 상방 탐색 부족)
EndOffset = 70     (기본 100)
SweepRadius = 2    (기본 5, 정밀)
MaxGroundPenetration = 20  (기본 10, 보간 여유)
```

## PlantSettings 변형

**PlantSettingsDefault**: SpeedThreshold=50, LockType=PivotAroundAnkle, ReplantRadiusRatio=0.6
**PlantSettingsStop**: SpeedThreshold=10, UnplantRadius=10, bReconstructWorldPlantFromVelocity=true, bAdjustHeelBeforePlanting=true
**PlantSettingsFullBody**: Default 기반 + LockType=PivotAroundBall

## InterpolationSettings 변형 (공통 bSmoothRootBone=true)

**Default/Stops**: UnplantLinearStiffness=250
**FullBody**: UnplantLinearStiffness=400 (몽타주 중 락 유지 강화)

## Leg Definitions

- FKFootBone: foot_r/foot_l, IKFootBone: VB ik_foot_r/l, BallBone: ball_r/l
- **Manual 모드** (Graph 아님) — footspeed_r/l 커브로 속도 판단
- DisableLockCurveName = disablefootlock_r/l

## 검증 출처

2026-04-20 `blueprint_query.get_cdo_properties` via Monolith MCP 직접 덤프.
PC_01_ABP CDO 62개 프로퍼티 중 FootPlacement/Plant/Interpolation/Pelvis 필터링.

## 2026-04-18 메모리와 차이

이전 안착값(`project_pc01_anim_debugging.md`)에 기록된 `PelvisHeightMode=FrontPlantedFeetUphill_FrontFeetDownhill`이 **AllLegs로 되돌아가 있음**. 사용자가 MaxOffset 올린 뒤 슬로프 문제 호소한 원인.
