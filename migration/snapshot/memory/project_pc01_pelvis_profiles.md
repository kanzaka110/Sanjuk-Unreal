---
name: PC_01 FootPlacement PelvisSettings 3 프로필
description: PC_01_AnimLayer_IK의 PelvisSettings를 기본대기/이동/다운 3개 struct 변수로 분리. 상태별 FootPlacement 튜닝.
type: project
originSessionId: 5c97ced7-4741-424f-8e22-cc55efda4867
---
# PC_01 PelvisSettings 3 프로필

## 구조

`PC_01_AnimLayer_IK` 에 `FFootPlacementPelvisSettings` 타입 변수 3개 (2026-04-23 덤프):

| 변수명 | 용도 |
|---|---|
| `PelvisSettingsDefault` | 기본 대기 (Idle 계열) |
| `PelvisSettingsMove` | 이동 (Walk/Run/Sprint) |
| `PelvisSettingsProne` | 다운 (누움) |

## 현재 값 (2026-04-23)

| 파라미터 | 대기 | 이동 | 다운 |
|---|:-:|:-:|:-:|
| MaxOffset | 50 | **10** ⭐ | 0 |
| LinearStiffness | 300 | 200 | 300 |
| LinearDamping | 1.0 | 1.0 | 1.0 |
| HorizontalRebalancingWeight | 0.5 | 0.5 | 0.3 |
| MaxOffsetHorizontal | 15 | 15 | 15 |
| HeelLiftRatio | 0.5 | 0.5 | 0.5 |
| PelvisHeightMode | FrontPlantedFeetUphill_FrontFeetDownhill | ← | ← |
| ActorMovementCompensationMode | SuddenMotionOnly | ← | ← |
| bEnableInterpolation | True | True | True |
| bDisablePelvisOffsetInAir | False | False | False |

## 주요 설계 포인트

- **Move.MaxOffset=10**: **계단 오르막 pelvis drop 방지용** (낮게 유지 필수, `feedback_pelvis_move_maxoffset_stairs.md` 참조)
- **Default.MaxOffset=50**: UE 기본값, 대기 시 슬로프 여유
- **Prone.MaxOffset=0**: 누운 상태 FootPlacement 완전 무효화
- **PelvisHeightMode=FrontPlantedFeetUphill_FrontFeetDownhill**: 슬로프 인지형 (UE 기본 AllLegs 대신)
- **HorizontalRebalancingWeight=0.5** (대기/이동): 기본 0.3의 1.7배, 측면 경사 rebalance 강화
- **MaxOffsetHorizontal=15**: 기본 10보다 확대
- **bDisablePelvisOffsetInAir=False**: UE 기본(true)과 반대 — 공중 튐 유발 가능성, True 복원 검토 권장

## 덤프 경로

- 스크립트: `scripts/dump_footplacement_params.py` (UE Python, 생성 클래스 `.PC_01_AnimLayer_IK_C` 로드 → CDO 덤프)
- 출력: `E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\PelvisSettingsDump.txt`

## 관련

- UE 5.7 소스: `cache/ue57/AnimNode_FootPlacement.h` — FFootPlacementPelvisSettings L366~417
- 측면 경사 발목 꺾임 이슈: MaxOffsetHorizontal↑ 이 직접 해결 경로 (planted feet Roll 트리거 지연)
