---
name: Groom ProjectCollision=True 권장은 Physics Asset 적합성 전제
description: PC_01에서 ProjectCollision=True 시 뒷머리가 뜨는 현상 발견. Physics Asset head 콜리전이 실제 스컬보다 크면 projection이 strand를 경계로 밀어내 lift 발생.
type: feedback
originSessionId: 2ca0199a-2137-4ab5-b982-e90a25c875fe
---
# Groom ProjectCollision=True 적용 전 Physics Asset 검증 필수

## 규칙

`ProjectCollision = True`를 기본 권장으로 제시하지 말 것. **Physics Asset 콜리전 바디가 Skeletal Mesh와 잘 맞는 경우에만** 안전하게 True.

## Why

2026-04-23 PC_01_Hair_Sanjuk Group 0 튜닝 중 사용자가 "ProjectCollision=True 켜면 뒷머리가 뜬다"고 보고.

메커니즘: Physics Asset의 head 콜리전(보통 캡슐/스피어)이 실제 스컬 메시보다 뒷통수 쪽으로 크게 튀어나와 있으면 → 자연스럽게 뒷통수에 닿은 strand들이 "콜리전 바디 안"으로 감지 → projection이 이를 penetration으로 판정 → 강제로 콜리전 경계 밖으로 밀어냄 → **실제 메시가 아닌 콜리전 바디 경계에 strand가 얹힘** → 뒷통수 뜬 것처럼 보임.

Physics Asset 캡슐은 실린더+반구 형태라 타원형 두상보다 뒷통수에서 넘치는 경우가 많음. PC_01은 이 케이스.

## How to apply

Groom 튜닝 권장 시:

1. **ProjectCollision 기본 False** 로 제시. "Physics Asset head 캡슐이 메시와 일치하면 True 가능" 단서 붙일 것
2. 사용자가 "뒤통수 들림"/"특정 부위 뜸" 증상 호소 시 **Gravity + Physics Asset** 두 가지 병렬 의심
3. 근본 해결은 Physics Asset 콜리전을 실제 메시에 맞게 수정 (Sphere 반경 축소, Sphyl 여러 개로 두상 근사)
4. 임시방편: `CollisionRadius` 낮춤 (2.0 → 1.0) 또는 `ProjectCollision=False`

## 관련

- 소스: `cache/ue57_groom/GroomAssetPhysics.h` FHairCollisionConstraint
- PC_01 PhysicsAsset 대상 SKM: `/Game/Art/Character/PC/PC_01/Head/CH_P_01_Head_001`
- 상세 파라미터 레퍼런스: `reference_groom_physics_params.md`
