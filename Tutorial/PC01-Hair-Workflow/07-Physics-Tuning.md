# 07. Physics Tuning — SBStableRodsSystem + 5그룹 라이브값 이식

UE 공식 CosseratRods가 아닌 SB2 커스텀 `SBStableRodsSystem` (CosseratRods 파생) 솔버를 사용. 2026-05-04 라이브값을 신규 에셋에 그대로 이식.

## 1. 솔버 지정

GroomAsset Editor → 각 그룹 → Physics 섹션:

| 필드 | 값 |
|---|---|
| NiagaraSolver | `CustomSolver` |
| CustomSystem | `/Game/Art/TA/Groom/SBStableRodsSystem` |
| DataflowAsset | (자동 — SBStableRodsSystem이 Dataflow Engine 기반) |

5그룹 모두 동일 솔버 지정.

⚠ `AngularSprings` 또는 `CosseratRods` (표준) 선택 시 PC_01 룩 재현 불가. **반드시 CustomSolver**.

## 2. 5그룹 파라미터 이식

소스: `project_pc01_hair01_params.md` (2026-05-04 라이브 실측). 신규본도 동일값으로 시작.

### 2.1 Solver Settings

| Grp | EnableSim | bEnableDeformation | SubSteps | IterationCount |
|---|---|---|---|---|
| 0 (Hero) | True | True | **32** | **100** |
| 1 (Size8) | True | True | 32 | 50 |
| 2 (SimOFF) | **False** | False | 5 | 5 |
| 3 (Size4) | True | True | 6 | 5 |
| 4 (Thick) | True | True | 8 | 10 |

> Grp 0 Hero는 다른 그룹 대비 5x SubSteps + 10x Iter. 형태 유지 비용. 후퇴 신중.

### 2.2 Bend Constraint

| Grp | BendStiffness (GPa) | BendDamping | BendScale | ProjectBend |
|---|---|---|---|---|
| 0 | **1.0** | 0.010 | ExtCurve `PC_01_Hair_BendScale` | **False** |
| 1 | 0.010 | 0.005 | ExtCurve | True |
| 2 | 0.015 | 0.005 | inline 1.0 | True |
| 3 | 0.010 | 0.005 | ExtCurve | True |
| 4 | 0.010 | 0.005 | inline tip 0.25 | True |

External Curve `PC_01_Hair_BendScale`은 별도 Curve Asset. 신규 에셋 임포트 후 그룹 0/1/3에 슬롯 할당.

> Grp 0만 ProjectBend=False — Hero가 너무 뻣뻣해지지 않게.

### 2.3 Stretch Constraint

| Grp | SolveStretch | StretchStiffness (GPa) | StretchDamping | ProjectStretch | StretchScale |
|---|---|---|---|---|---|
| 0 | True | 1000 | **0.050** | True | 0.1→1.0 (curve) |
| 1 | True | 1000 | **0.005** | True | inline 1.0 |
| 2 | **False** | 1.0 | 1.0 | True | inline 1.0 |
| 3 | True | 1000 | 1.0 | True | inline 1.0 |
| 4 | True | 1000 | 0.050 | True | inline 1.0 |

> Grp 2 SolveStretch=False — bend만 시뮬, 길이 강체 처리. Sim OFF 그룹이지만 일부 정적 거동을 위해.

### 2.4 Collision Constraint

| Grp | CollisionRadius (cm) | ProjectCollision | RadiusScale | StaticFriction | KineticFriction |
|---|---|---|---|---|---|
| 0 | 0.10 | True | 1.0→0.1 (curve) | 0.1 | 0.1 |
| 1 | 0.20 | True | 1.0→0.1 | 0.1 | 0.1 |
| 2 | 0.10 | True | 1.0→0.1 | 0.1 | 0.1 |
| 3 | 0.10 | True | 1.0→0.1 | 0.1 | 0.1 |
| 4 | 0.50 | True | 1.0→0.1 | 0.1 | 0.1 |

> Grp 4가 CollisionRadius 0.50으로 가장 큼 (굵은 strand 케이스).

⚠ 메모리 두 곳에서 Grp 4 ProjectCollision 값이 충돌:
- `project_pc01_hair01_params.md` (2026-05-04): **False**
- `project_pc01_hair_gravity_bug.md` (2026-04-29): **True**

→ 신규본은 **True**로 시작하고 (안정 기준), 뒷머리 덜덜림 발생 시 False로 토글 검증. PIE에서 확정.

### 2.5 External Forces

| Grp | GravityVector.Z (cm/s²) | AirDrag | AirVelocity |
|---|---|---|---|
| 0 | **-981** | 0.015 (또는 0.20 — 메모리 충돌) | (0,0,0) |
| 1 | -981 | 0.015 | (0,0,0) |
| 2 | -981 | 0.030 | (0,0,0) |
| 3 | -981 | 0.050 | (0,0,0) |
| 4 | **-981** | 0.020 | (0,0,0) |

> **Grp 4 Gravity=-1 버그 절대 금지.** 원본 잔존 버그이며 신규본은 -981 강제.
> AirDrag는 두 메모리 dump 간 차이 있음. 라이브 dump (`hair01_pre_rebuild`) 값을 우선.

### 2.6 Strands Parameters

| Grp | StrandsSize | StrandsDensity | StrandsThickness (cm) | StrandsSmoothing | ThicknessScale |
|---|---|---|---|---|---|
| 0 | Size16 | 1.0 | 0.10 | 0.40 | 1.0→1.0 |
| 1 | Size8 | 1.5 | 0.01 | 0.10 | 1.0→1.0 |
| 2 | Size4 | 1.0 | 0.01 | 0.10 | 1.0→1.0 |
| 3 | Size4 | 1.0 | 0.10 | 0.00 | 1.0→0.5 |
| 4 | Size4 | 2.0 | 0.01 | 0.00 | 1.0→0.5 |

## 3. GroomComponent CDO (BP_Sanjuk 측)

`PC_01_BP_Sanjuk` → Hair_GEN_VARIABLE (SBCharacterGroomComponent). **변경 없음** 확인:

| 필드 | 값 | 변경 가능 여부 |
|---|---|---|
| bOverrideSettings | True | (유지) |
| bLocalSimulation | True | **금지** (False 시 헤어 튐) |
| LocalBone | `root` | **금지** (`head` 시 튐) |
| LinearVelocityScale | 1.0 | 최댓값 |
| AngularVelocityScale | 1.0 | 0.7로 낮춰볼 수 있음 |
| TeleportDistance | 50 | |
| TeleportDetectionThreshold | 25 | SB2 커스텀 |
| bFirstTeleportDetection | True | SB2 커스텀 |
| WindScale | 0.4 | 0.2 검토 중 (잔존 이슈) |
| PhysicsAsset | `Evie_Body_PhysicsAsset` | 유지 |

## 4. 적용 방법 — 수동 vs Monolith

### 4.1 수동 (권장, 검증 안정성)

GroomAsset Editor → 각 그룹 패널에서 직접 입력 → Save Asset.

5그룹 × 약 25필드 = 125 입력. 시간 소요. 그러나 즉시 검증 가능.

### 4.2 Monolith (자동)

```
animation_query("set_groom_asset_group_properties",
  asset_path="/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_01",
  group_index=0,
  properties={
    "SubSteps": 32,
    "IterationCount": 100,
    "BendStiffness": 1.0,
    ...
  })
```

⚠ `//Game/...` 이중 슬래시 절대 금지 (editor fatal crash).

스크립트 자동화:

```powershell
py scripts/apply_pc01_hair01_baseline.py \
    --asset "/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_01" \
    --source-dump "dumps/hair01_pre_rebuild_20260528.json"
```

`apply_pc01_hair01_baseline.py`는 baseline dump JSON을 읽어서 Monolith로 5그룹 일괄 set. ⚠ 본 가이드 작성 시점 미존재 — 필요 시 작성.

## 5. Save + 후 dump

### 5.1 Save Asset

GroomAsset Editor → `Save Asset`. 또는:

```
animation_query("save_asset", asset_path="/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_01")
```

P4 체크아웃 필수.

### 5.2 후 dump

```powershell
py scripts/dump_pc01_hair_params.py
```

산출: `dumps/hair01_post_rebuild_<TIMESTAMP>.json`

### 5.3 Diff 검증

```powershell
py scripts/diff_hair_dump.py `
    dumps/hair01_pre_rebuild_20260528.json `
    dumps/hair01_post_rebuild_20260528.json
```

기대: 5그룹 25필드 모두 **0 차이** (라이브값 그대로 이식한 경우).

차이가 있으면 어느 필드가 누락됐는지 식별 → 수동 보정.

## 6. 잔존 이슈 (적용 후 PIE에서 검증)

라이브값 그대로라도 다음은 PIE에서 검증 필요:

| 이슈 | 메모리 | 처방 후보 |
|---|---|---|
| 뒷머리 (Grp 4) 덜덜림 | `project_pc01_hair01_params.md` 잔존 이슈 | ProjectCollision=False 토글, BendDamp 0.005→0.010 |
| 바람 과반응 | 동상 | AirDrag 전 그룹 ↓, 특히 Grp 3 0.050→0.020 |
| 텔레포트 시 튐 | 동상 | bLocalSimulation=True 조건에서 TeleportDistance 자동 reset 비작동 → BP에서 ResetSimulation() 명시 호출 |
| WindScale 0.4 강함 | 동상 | 0.2 조정 검토 |

→ 08편 PIE Validation에서 한꺼번에.

## 7. 체크포인트

- [ ] 5그룹 모두 NiagaraSolver = CustomSolver
- [ ] CustomSystem = SBStableRodsSystem 연결
- [ ] 5그룹 25필드 입력 또는 Monolith 일괄 적용
- [ ] External Curve `PC_01_Hair_BendScale` 슬롯 할당 (Grp 0/1/3)
- [ ] Save Asset 성공 (P4)
- [ ] `dumps/hair01_post_rebuild_<TIMESTAMP>.json` 저장
- [ ] pre/post diff = 0

OK면 → [08 PIE Validation](08-PIE-Validation.md)
