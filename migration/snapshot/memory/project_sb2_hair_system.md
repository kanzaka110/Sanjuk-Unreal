---
name: SB2 PC_01 Hair는 Groom + SB 커스텀 물리 시스템
description: PC_01_Hair_01 분석 결과 — GroomAsset 사용. 물리는 UE 표준이 아닌 SB2 커스텀 SBStableRodsSystem (Dataflow Engine 기반).
type: project
originSessionId: a42ec142-c2aa-46c8-806c-b19970eff37b
---
## 에셋 구조

`/Content/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/`
- `PC_01_Hair_01.uasset` — GroomAsset, 21MB (메인)
- `PC_01_Hair_Sanjuk.uasset` — GroomAsset 변형 (용도 미확인)
- `Binding/PC_01_Hair_01_Binding.uasset` — GroomBindingAsset (Skinning 타입)
- `Material/PC_01_Hair_Material.uasset` — MaterialInstanceConstant

**참조:** `PC_01_BP.uasset` 에서 헤어 컴포넌트로 소환.

## 렌더 구조 (UE 표준 Groom)
- `HairGroupsInfo` × 여러 그룹 (메인/잔머리 등 분리)
- Strands / Cards / Mesh 3단계 LOD (`EGroomGeometryType`)
- Guide 커브로 시뮬 → Strand에 Interpolation 전파 (UE 표준 패턴)
- `NumGuides`, `NumCurves`, `HairToGuideDensity`, `InterpolationQuality`
- Raytracing: `HairRaytracingPercentPoints`, `HairRaytracingRadiusScale`

## 물리 — ★ SB2 커스텀 (중요)
**UE 표준 Groom 물리 안 씀.** 대신 `SBStableRodsSystem` (XPBD Position-Based Dynamics for rods 추정) 을 UE 5.7의 **Dataflow Engine** 프레임워크 위에 구현.
- 참조 모듈: `/Script/DataflowEngine`
- 참조 키: `CustomSystem`, `DataflowAsset`, `DataflowSettings`, `DataflowTerminal`
- Constraint 종류:
  - HairStretchConstraint + Stiffness/Damping/Scale
  - HairBendConstraint + Stiffness/Damping/Scale
  - HairCollisionConstraint + CollisionRadius
  - AngularSpringCompliance, BendSpringCompliance
- Solver: `SubSteps`, `Iterations`, `IterationCount`
- External Forces: `AirDrag`, `AirVelocity`

## Binding
- Type: `EGroomBindingType::Skinning` (스킨드 메쉬 기반)
- TargetSkeletalMesh: PC_01_Body_001_Skeleton 계열 (정확한 경로는 에디터 확인 필요)

## Material (MA_Groomhair 기반 MIC)
Parent: `/Game/ART/Character/Generic/GlobalMasterMaterials/Hair/MA_Groomhair`
노출 파라미터:
- Melanin, Redness (hairRedness), HairRoughness
- HighlightsRootDistance, LightAmount, WhiteAmount
- TwoSided, BlendMode, ShadingModel

→ MetaHuman 스타일 pigment 기반 헤어 착색.

## 경로 주의
Binding 내부 저장 경로가 `/Game/ART/...` (대문자 ART) — 스크립트에서 대소문자 매칭 시 주의.

**Why:** 2026-04-22 PC_01_Hair_01 상세 분석 중 SBStableRodsSystem이 UE 표준이 아닌 SB2 커스텀임을 바이너리에서 확인. 표준 UE Groom 가이드 기준 튜닝 시 파라미터 이름은 같지만 실제 시뮬 엔진이 다르므로 결과 차이 발생 가능.

**How to apply:**
- SB2 헤어 물리 튜닝 시 UE 공식 Groom 문서 단독 참조 금지 — 엔진팀에 Dataflow 기반 Stable Rods 문서 요청
- 새 PC 캐릭터 헤어 제작 시 동일 패턴 (SBStableRodsSystem + Skinning Binding) 사용 추정
- `PC_01_Hair_Sanjuk` 변형의 용도는 별도 세션에서 확인 필요
