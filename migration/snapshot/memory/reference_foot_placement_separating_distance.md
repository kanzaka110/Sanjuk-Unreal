---
name: FootPlacement SeparatingDistance — 다리 교차 방지 빌트인
description: UE 5.7 FootPlacement의 SeparatingDistance 파라미터로 회전/피벗 시 양다리 교차/관통 방지. PC_01에서 10.0으로 거의 해소 확인.
type: reference
originSessionId: bf06505c-af74-43de-8c6d-4394ecaefd65
---
## 파라미터

`FFootPlacementPlantSettings::SeparatingDistance` (float, ClampMin=0)
- 출처: `Engine/Plugins/Animation/AnimationWarping/.../AnimNode_FootPlacement.h:495-498`
- 공식 코멘트: "The minimum distance the feet can be from the plane that separates the feet. Value of 0 disables this"
- 기본값: **0.0 (비활성)** — UE 5.7 기본 상태에선 다리 교차 방어막 없음

## 메커니즘

매 프레임 양 발 사이 분리 평면(separating plane) 계산 → 발이 침범하면 평면 바깥으로 밀어냄. Spring 보간으로 부드럽게.

관련 보조 파라미터 (FFootPlacementInterpolationSettings):
- `bEnableSeparationInterpolation` = true (기본)
- `SeparationStiffness` = 1000.0
- `SeparationDamping` = 1.0

## PC_01 적용 결과 (2026-04-28)

`SeparatingDistance = 10.0` 으로 **회전 이동 시 양다리 교차/관통 거의 해소** 확인. 1차 권장값 5에서 10까지 점진적 시도 → 10이 sweet spot.

## How to apply

- 회전/피벗에서 다리 교차 호소 시 1순위 처방. 추측/Control Rig 우회 전에 이 빌트인부터.
- 시작값 5.0, 부족하면 10~15까지. 너무 크면 idle 정지 시 발 모음 부자연 가능성.
- PC_01 PelvisSettings는 Default/Move/Prone 3 프로필 운용 (메모리 `project_pc01_pelvis_profiles.md`). PlantSettings도 프로필 분리된 경우 Move 프로필 우선 적용 검토.
- SeparationStiffness 기본 1000은 즉각적 — 분리가 갑작스러우면 500~700으로 감소.
