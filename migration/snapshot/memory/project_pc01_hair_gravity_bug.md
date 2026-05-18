---
name: PC_01 헤어 — 활성본(PC_01_Hair_01) 5그룹 현재 상태 + 폴더 자산 구성
description: 2026-04-29 17:44 PC_01_Hair_01 활성 워킹카피 5그룹 파라미터 (재튜닝 후), 폴더 4개 헤어 에셋, 잔존 이슈 갱신본.
type: project
originSessionId: 6d37eb50-96ec-4182-8e48-1395df67c432
---
# PC_01 헤어 — 활성본 현재 상태 (2026-04-29 17:44 실측)

## 폴더 자산 구성

`/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/`:
- `PC_01_Hair_Original` (04-23) — pristine baseline (Grp 4 Gravity=-1 잔존)
- `PC_01_Hair_Sanjuk` (04-23) — 4-23 튜닝본 (구버전)
- **`PC_01_Hair_01` (04-29 17:44) — 활성 워킹카피 (Binding이 가리키는 인게임 본)** ← 분석 대상
- `PC_01_Hair_02` (04-28) — 신규 (용도 미상)
- `PC_01_Hair_BendScale` (04-29) — Curve, Grp 0/1/3 의 BendScale ExternalCurve
- Binding: `PC_01_Hair_01_Binding` → groom = **`PC_01_Hair_01`** ✅ / target = `CH_P_01_Head_001`

## PC_01_Hair_01 활성본 5그룹 현재 값 (17:44 덤프)

| 파라미터 | Grp 0 (Hero/Size16) | Grp 1 (Size8) | Grp 2 (Sim OFF) | Grp 3 (Size4) | Grp 4 (굵은) |
|---|---|---|---|---|---|
| EnableSimulation | T | T | **F** | T | T |
| bEnableDeformation | T | T | F | T | T |
| NiagaraSolver | CustomSolver (SBStableRodsSystem) | 동일 | 동일 | 동일 | 동일 |
| SubSteps | 32 | 6 | 5 | 6 | 4 |
| IterationCount | 100 | 5 | 5 | 5 | 5 |
| GravityVector.Z | -981 | -981 | -981 | -981 | -981 ✅ |
| AirDrag | 0.20 | 0.015 | 0.10 | 0.015 | 0.02 |
| BendStiffness | **1.0** | 0.010 | 0.015 | 0.010 | 0.010 |
| BendDamping | 0.010 | 0.005 | 0.005 | 0.005 | 0.005 |
| BendScale | ExtCurve | ExtCurve | inline 1.0 | ExtCurve | inline tip 0.25 |
| ProjectBend | **F** | T | T | T | T |
| StretchStiffness | 1000 | 1000 | 1.0 | 1000 | 1000 |
| StretchDamping | 0.050 | **0.005** | 1.0 | 1.0 | 0.050 |
| ProjectStretch | T | T | T | T | T |
| StretchScale | 0.1 → 1.0 (커브) | inline 1.0 | inline 1.0 | inline 1.0 | inline 1.0 |
| CollisionRadius | 0.10 | 0.20 | 0.10 | 0.10 | 0.50 |
| ProjectCollision | T | T | T | T | T |
| RadiusScale | 1.0 → 0.1 | 1.0 → 0.1 | 1.0 → 0.1 | 1.0 → 0.1 | 1.0 → 0.1 |
| StrandsSize | Size16 | Size8 | Size4 | Size4 | Size4 |
| StrandsDensity | 1.0 | 1.5 | 1.0 | 1.0 | 2.0 |
| StrandsThickness | 0.10 | 0.01 | 0.01 | 0.10 | 0.01 |
| StrandsSmoothing | 0.40 | 0.10 | 0.10 | 0.00 | 0.00 |
| ThicknessScale | 1.0 → 1.0 | 1.0 → 1.0 | 1.0 → 1.0 | 1.0 → 0.5 | 1.0 → 0.5 |

## 12:14 → 17:44 주요 재튜닝

**Grp 0 Hero 재튜닝:**
- BendStiffness 0.20 → **1.0** (5배 ↑, 형태 강화)
- BendDamping 0.005 → 0.010 (ringing 완화)
- StretchStiffness 500 → 1000
- StretchDamping **1.0 → 0.050** ✅ (덜덜거림 주범 해결)
- IterationCount 300 → 100 (성능 회복)
- StrandsDensity 1.5 → 1.0
- StrandsSmoothing 0.20 → 0.40

**Grp 1 (Size8): StretchDamping 0.10 → 0.005** ✅ (200배 ↓)

**Grp 2/3 회귀 ⚠️:** StretchDamping 0.05 → **1.0** (스프링 죽이는 값으로 복귀, 의도 미상)

**전체 ProjectBend False → True** (Grp 0 제외 4그룹, 안정성 ↑ / 성능 ↓)

## 활성본 핵심 특징

- **Grp 0이 메인 (Size16, hero strand)**. SubSteps=32, IterationCount=100, BendStiffness=1.0
- **Grp 0 / Grp 1 StretchDamping 0.05 / 0.005** — 저감쇠로 "흐르는 느낌"
- **External Curve `PC_01_Hair_BendScale` 사용** (Grp 0/1/3 공유) — root → tip stiffness scaling
- 솔버 = **CustomSolver** (`/Game/Art/TA/Groom/SBStableRodsSystem`) — CosseratRods 파생, GravityPreloading 무시

## GroomComponent 연결 상태 (2026-04-29 BP 실측)

`PC_01_BP_Sanjuk`의 Hair_GEN_VARIABLE (SBCharacterGroomComponent):
- **groom_asset** = `PC_01_Hair_Sanjuk` (BP 슬롯, 사용 안 함 — legacy ref)
- **binding_asset** = `PC_01_Hair_01_Binding` → groom = `PC_01_Hair_01` (실제 런타임 사용 ✅)
- **physics_asset** = `Evie_Body_PhysicsAsset` ✅ (충돌은 이걸로 처리, SkelMesh PhysAsset 무관)
- attachment = (root)
- 4개 archetype 중복 (Hair × 2 부모/자식, Fuzz × 2)

**즉**: 17:44 PC_01_Hair_01 5그룹 튜닝값이 실제 게임에 적용 중. 분석/메모리 갱신 유효.

## 잔존 이슈

- **Grp 2/3 StretchDamping=1.0** — 의도 확인 필요 (스프링 죽이는 값)
- **무브먼트/씬 전환 튐**: ProjectStretch=True 빠른 모션 시 segment 강제 펼침 위험
- ~~PhysAsset head 캡슐 부재~~ — **무관**. GroomComponent.PhysicsAsset 슬롯에 `Evie_Body_PhysicsAsset` 직접 연결됨 (Groom PhysAsset 우선순위는 `reference_groom_physicsasset_slot.md` 참조)
- ~~들림 이슈~~ — **해결됨 (2026-04-29)**

## How to apply

PC_01 헤어 작업 시:
1. 활성본은 **`PC_01_Hair_01`** (17:44 기준). Sanjuk/Original은 baseline 보존
2. Binding의 groom 참조 매번 확인 (현재 정상)
3. **Grp 0 BendStiffness=1.0, IterationCount=100, SubSteps=32** — 사용자가 형태 유지로 의도적으로 올림. 후퇴 신중히
4. 덤프 스크립트: `scripts/dump_pc01_hair_original.py` → `Saved/Logs/HairDump_Original_20260429.txt` (Original + 활성본 둘 다)

## 참고

- UE 5.7 소스: `cache/ue57_groom/GroomAssetPhysics.h`
- 솔버: `/Game/Art/TA/Groom/SBStableRodsSystem` (CosseratRods 파생)
- Binding target SkeletalMesh: `CH_P_01_Head_001` → PhysicsAsset에 **head 본 캡슐 부재** (spine_04/neck_02/face만)
