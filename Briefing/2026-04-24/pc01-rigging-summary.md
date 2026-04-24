# PC_01 애니메이션 리깅 튜닝 정리 (2026-04-22 ~ 2026-04-24)

> **대상**: SB2 PC_01 캐릭터 (Motion Matching + AnimLayer_IK + FootClamp CtrlRig + Overlay + Groom)
> **엔진**: UE 5.7.4 (SB2 licensee-modified, Engine/Source 없음)
> **체크포인트 일자**: 2026-04-24

---

## ✅ 성공 케이스 (상세)

### 1. Groom 헤어 물리 최종 튜닝 — `PC_01_Hair_Sanjuk`

**시작점**
- 증상: 고속 모션에서 뒤통수 들림
- 진단: `PC_01_Hair_01` Group 0/3 의 `GravityVector.Z=-1` 발견 (사실상 무중력)

**과정**
1. Python 덤프 스크립트로 5개 그룹 전체 파라미터 실측 (`scripts/dump_pc01_hair_params.py`)
2. UE 5.7 Groom 소스 로컬 캐싱 (`cache/ue57_groom/GroomAssetPhysics.h`)
3. 파라미터 의미/단위/상호작용 레퍼런스 메모리화 (`reference_groom_physics_params.md`)
4. Original 보존본 생성 후 Sanjuk 복제본에 튜닝 적용

**결과 — Group별 핵심 변경 (Original → Sanjuk)**

| 그룹 | 역할 | 주요 변경 |
|:-:|---|---|
| 0 (Hero, Size8) | 메인 볼륨 긴 머리 | Deform OFF→**ON**, AirDrag 0.1→**0.015**, BendStiff 0.1→**0.01** (10×), `SolveStretch` F→**T**, StretchDamp 1.0→**0.05** (20×), BendScale 1.0→**0.6+Curve**, StretchScale 1.0→**0.3**, CollRadius뿌리 1.0→**0.5+Curve** |
| 1 (Size4 보조) | 가벼운 가닥 | Deform OFF→**ON**, Density 0.5→**1.5** (3×), StretchDamp→**0.05**, BendScale Curve |
| 2 (Size4 고정) | Sim 미적용 | 실질 변경 없음 |
| 3 (Size4 boundary) | 경계 taper | Deform OFF→**ON**, Smoothing 0.1→**0**, ThicknessScale팁→**0.5**, BendScale Curve |
| 4 (Size4 굵은가닥) | 앞/뒷머리 | Deform OFF→**ON**, **Sim OFF→ON**, Density 1.5→**2.0**, BendStiff→**0.025**, BendScale팁→**0.25**, CollRadius 0.2→**0.5**, StretchDamp→**0.05**, StretchStiff→**1000** |

**전용 커브 에셋**
- `PC_01_Hair_Sanjuk_BendScale` — Grp 0, 1, 3 의 BendScale
- `PC_01_Hair_Sanjuk_Collision` — Grp 0 의 RadiusScale

**솔버**: CosseratRods via `/Game/Art/TA/Groom/SBStableRodsSystem` (공용)

**핵심 교훈 (메모리화)**
- **`ProjectCollision=True` 기본 권장 금지** — Physics Asset head 캡슐이 실제 메시보다 크면 뒷머리 뜸 (PC_01 케이스로 실증)
- Gravity 버그는 `-1` 값으로 나타남 (UE 기본 `-981`)

---

### 2. FootClamp CtrlRig 축 매핑 수정

**문제**: 발목 회전 클램프가 예상과 반대 축에 걸림

**조치**
- Pitch ↔ Roll 축 스왑
- 값 전체 개방 (임시 조치)

**남은 영향**: "값 전체 개방"이 현재 측면 경사 발목 꺾임 이슈를 키우는 원인 중 하나로 재확인됨. Roll 축을 선택적으로 다시 좁혀야 함.

---

### 3. Guard Overlay + IK 충돌 해결

**문제**: Guard 오버레이와 IK 계산이 서로 덮어쓰기

**조치**
- AnimGraph 순서: **IK를 Overlay 앞으로** 이동
- `layering_legs` / `layering_pelvis` = **0** 설정

**일반화 규칙 (메모리화)**: 새 Additive 오버레이 추가 시 동일 패턴 적용 필수

---

### 4. PelvisSettings 3 프로필 구조 확인 (2026-04-24)

**발견**
`PC_01_AnimLayer_IK` CDO에 `FFootPlacementPelvisSettings` 타입 변수 3개 존재:

| 변수 | 용도 |
|---|---|
| `PelvisSettingsDefault` | 기본 대기 |
| `PelvisSettingsMove` | 이동 (Walk/Run/Sprint) |
| `PelvisSettingsProne` | 다운 (바닥에 누움) |

**현재 값**

| 파라미터 | 대기 | 이동 | 다운 | UE 5.7 기본 |
|---|:-:|:-:|:-:|:-:|
| MaxOffset | 50 | **10** ⭐ | 0 | 50 |
| LinearStiffness | 300 | 200 | 300 | 350 |
| LinearDamping | 1.0 | 1.0 | 1.0 | 1.0 |
| HorizontalRebalancingWeight | 0.5 | 0.5 | **0.3** | 0.3 |
| MaxOffsetHorizontal | 15 | 15 | 15 | 10 |
| HeelLiftRatio | 0.5 | 0.5 | 0.5 | 0.5 |
| PelvisHeightMode | FrontPlantedFeetUphill_FrontFeetDownhill | ← | ← | AllLegs |
| ActorMovementCompensationMode | SuddenMotionOnly | ← | ← | SuddenMotionOnly |
| bEnableInterpolation | True | True | True | true |
| bDisablePelvisOffsetInAir | **False** ⚠ | **False** ⚠ | **False** ⚠ | true |

**설계 해석**
- `PelvisHeightMode=FrontPlantedFeetUphill_FrontFeetDownhill` — 슬로프 인지형 선택 (UE 기본 `AllLegs` 대신)
- `MaxOffsetHorizontal=15` — 기본 10보다 확대
- `HorizontalRebalancingWeight=0.5` (대기/이동) — 기본 0.3의 1.7배, 측면 경사 rebalance 강화

**핵심 교훈 (메모리화)**
- **Move.MaxOffset=10은 의도적** — 계단 오르막에서 낮은 쪽 발 plant plane 맞추려 pelvis drop 발생하는 것 방지. **건드리지 말 것**
- `bDisablePelvisOffsetInAir=False`가 UE 기본(`true`)과 반대 — 공중 튐 유발 가능성, 검토 필요

---

### 5. 인프라 구축 (재사용 자산)

**UE 5.7 소스 로컬 캐시**
SB2가 licensee-only라 Engine/Source 없음 → 공식 UE 5.7 소스를 `cache/` 에 저장:
- `cache/ue57/` — FootPlacement, LegIK, Inertialization, CMC, PoseSearch 등 13개 헤더
- `cache/ue57_groom/` — Groom Physics 소스
- `cache/kawaii_physics/` — 세컨더리 모션 대안 플러그인 전체

**Monolith HTTP JSON-RPC 직접 호출**
MCP 툴 미노출 세션에서도 `curl localhost:9316/mcp` 로 15 도메인 988액션 접근 가능.
- 파라미터 구조: `{"action": "...", "params": {"asset_path": "..."}}` (key는 `asset_path`)
- 핵심 액션: `animation_query` → `get_abp_info`, `get_abp_variables`, `get_nodes`, `get_graphs`
- 주의: `get_cdo_properties` 전체 호출 시 응답 중단 → `property_names` 명시 필요

**덤프 스크립트**
- `scripts/dump_pc01_hair_params.py` — Groom Original/Sanjuk 비교 덤프
- `scripts/dump_footplacement_params.py` — AnimBP `_C` 생성 클래스 로드 → CDO 덤프

**프로젝트 구조 분석 (메모리화)**
- SB2 OverlaySystem (ChooserTable + PDA_OverlayData + Additive Pose)
- SB2 Motion Matching 폴더 (Pose Search DB + Chooser)
- SB2 Show 시스템 (Art/Show/ - 액션/스킬 연출 커스텀, AnimSequence+FX+Sound 묶음)
- SB2 Mutable Crowd (Mass AI + AnimNext + Mutable CO + ABP 4중 병렬)
- PC_01_ABP 체인 전체 구조 (T3D parsing 실측)

**ABP 실시간 디버그**
`bDrawDebug` 체크박스 (FootPlacement/LegIK/ControlRig 등 Details 패널)로 PIE 중 3D 기즈모. `ShowDebug Character` 콘솔보다 직관적.

---

## ⚠ 시도했다 접은 것 (한 줄 요약)

| 시도 | 결과 | 관련 커밋/세션 |
|---|---|---|
| LegIK temporal smoothing (TwoBoneIK + LegSmooth) | 엔진 한계로 안정 smoothing 불가 — 포기 | `451fec6` |
| FootPlacement 계단 감지 스크립트 | 실용성 낮아 아이디어만 정리 | `77b3b47` |
| FootPlacement `AnkleTwistReduction=1.0` 측면 꺾임 해결 | ① Ground Alignment 단계를 못 덮음 — 무효 확인 | 2026-04-24 |
| Additive layer 진단 스크립트 | 진단까지만 수행, 실질 조치 없음 | `848d832` |
| UE Python `BlueprintEditorLibrary.get_all_graphs` / `get_variable_names` | SB2 빌드에 미존재 — Monolith HTTP로 우회 | 2026-04-24 |
| Monolith `get_cdo_properties` 전체 호출 | 응답 중단 — `property_names` 명시 필요 | 2026-04-24 |

*스크립트 대부분은 `scripts/_archive/` 에 아카이브 완료.*

---

## 📋 남은 이슈 (행동 가능)

| 우선순위 | 항목 | 조치안 | 상태 |
|:-:|---|---|:-:|
| 🔴 High | 경사 측면 발목 꺾임 | `MaxOffsetHorizontal` 15→25, `HeelLiftRatio` 0.5→0.6 | 권장값 제시, 미적용 |
| 🔴 High | Hair Binding이 `PC_01_Hair_01` 참조 중 (Sanjuk 아님) | Binding Source Groom 교체 or 별도 Sanjuk Binding 생성 | 미적용 |
| 🔴 High | Hair Group 4 `Gravity.Z=-1` + Sim ON | -981로 수정 (의도적이면 문서화) | 미적용 |
| 🟡 Mid | `bDisablePelvisOffsetInAir=False` (UE 기본 true와 반대) | 점프 튐 유발 가능성 — True 복원 검토 | 확인 필요 |
| 🟢 Low | 근본 해결: FootPlacement 뒤 Pelvis Roll 추가 | Transform (Modify) Bone on pelvis, 경사 노말 기반 Roll×0.3~0.5 | 설계안만 |

---

## 🗂 참고 자료 맵

```
cache/
├── ue57/              # UE 5.7 소스 헤더 13개
├── ue57_groom/        # Groom Physics 소스
└── kawaii_physics/    # KawaiiPhysics 플러그인 전체

scripts/
├── dump_pc01_hair_params.py         # Groom 5그룹 전체 덤프
├── dump_footplacement_params.py     # PelvisSettings 3프로필 덤프
├── analyze_abp_graph.py             # ABP 그래프 구조 분석
├── probe_abp_api.py                 # UE Python API 탐색
├── parse_animgraph_t3d.py           # T3D 파싱
├── fix_footclamp_rig.py             # FootClamp Rig 수정 (적용 완료)
└── _archive/                        # 실패/완료된 실험 스크립트
    ├── legik_stair/                 # LegIK smoothing + 계단 시도
    └── fp_stair_detect/             # FP 계단 감지 + Inertialization 탐색

메모리 (C:\Users\SHIFTUP\.claude\projects\C--Dev-Sanjuk-Unreal\memory\)
└── 주제별 그룹핑됨 (MEMORY.md 참조)
```

---

## 📝 출처

- 소스 덤프:
  - Hair: `E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\HairDump.txt`
  - PelvisSettings: `E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\PelvisSettingsDump.txt`
- UE 5.7 레퍼런스: `cache/ue57/AnimNode_FootPlacement.h`, `cache/ue57_groom/GroomAssetPhysics.h`
- Git 히스토리: `ef985f4` (Groom), `451fec6` (LegIK), `77b3b47` (FP 계단), `848d832` (Additive), `47482f7` (에셋 캐시), `352d561` (Hair dump 스크립트), `3323420` (PelvisSettings 스크립트)
