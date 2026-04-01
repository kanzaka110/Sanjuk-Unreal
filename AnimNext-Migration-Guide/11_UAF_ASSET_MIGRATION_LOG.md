# 11. UAF 에셋 마이그레이션 로그

[← 이전: 디버깅 & 검증](./10_DEBUGGING_AND_VALIDATION.md) | [목차](./00_INDEX.md)

---

## 11.1 개요

이 문서는 UEFN_Mannequin 캐릭터 데이터를 UAF 폴더로 마이그레이션한 작업 내역을 기록합니다.

- **작업일**: 2026-03-28
- **도구**: Monolith MCP (Claude Code)
- **원본 경로**: `/Game/Characters/UEFN_Mannequin/`
- **대상 경로**: `/Game/Characters/UAF/UEFN_Mannequin/`
- **원칙**: 원본 에셋은 삭제하지 않고 보존, UAF 폴더에 새로 생성

---

## 11.2 마이그레이션 전략

### 복제 vs 참조 판단 기준

| 에셋 유형 | 전략 | 이유 |
|-----------|------|------|
| Skeleton / SkeletalMesh | **참조** (원본 유지) | UAF/ABP 모두 동일한 메시/스켈레톤 사용 |
| Textures | **참조** (원본 유지) | 렌더링 에셋이므로 시스템 독립적 |
| AnimSequence (1,700+개) | **참조** (원본 유지) | 데이터 에셋으로 UAF/ABP 간 공유 가능 |
| AnimMontage (30+개) | **참조** (원본 유지) | 데이터 에셋으로 공유 가능 |
| IK Rig / Physics Asset / MirrorDataTable | **참조** (원본 유지) | 캐릭터 리깅 에셋으로 공유 가능 |
| Chooser Table (10개) | **참조** (원본 유지) | ABP/UAF 공유 가능 (마이그레이션 가이드 3.7 참조) |
| Pose Search Schema | **새로 생성** | UAF 전용 스키마로 독립적 관리 |
| Pose Search Database | **새로 생성** | UAF 전용 DB로 독립적 관리 |
| BlendSpace / AimOffset | **새로 생성** + 샘플 복제 | UAF 시스템에서 독립적으로 사용 |
| Animation Blueprint | **새로 생성** | UAF용 새 ABP |
| Material / MaterialInstance | **복제** + 파라미터 동일 적용 | UAF 캐릭터 독립적 머티리얼 |

---

## 11.3 생성된 UAF 폴더 구조

```
/Game/Characters/UAF/UEFN_Mannequin/
│
├── Animations/
│   ├── AimOffset/
│   │   ├── BS_Neutral_AO_Stand              (15 samples)
│   │   └── BS_Neutral_AO_Stand_NoSmoothing  (15 samples)
│   └── Poses/
│       ├── BS_Relaxed_Lean_Head             (13 samples)
│       ├── BS_Relaxed_Run_Leans             (5 samples)
│       ├── BS_Relaxed_Walk_Leans            (5 samples)
│       ├── BS_Relaxed_Run_Lean_FB           (13 samples)
│       └── BS_Relaxed_Run_Lean_LR           (13 samples)
│
├── ExperimentalStateMachineData/
│   ├── [Schemas]
│   │   ├── PSS_SM_CMC_Idles
│   │   ├── PSS_SM_CMC_LocoLoops
│   │   ├── PSS_SM_CMC_LocoTransitions
│   │   ├── PSS_SM_Mover_Stops
│   │   ├── PSS_SM_Mover_Loops
│   │   ├── PSS_SM_Mover_Transitions
│   │   ├── PSS_SM_Mover_TraversalTransitions
│   │   └── PSS_SM_Mover_Spins
│   └── [Databases]
│       ├── PSD_SM_CMC_Idles
│       ├── PSD_SM_CMC_Loops
│       ├── PSD_SM_CMC_Transitions
│       ├── PSD_SM_Mover_Stops
│       ├── PSD_SM_Mover_Loops
│       ├── PSD_SM_Mover_Transitions
│       ├── PSD_SM_Mover_TraversalTransitions
│       └── PSD_SM_Mover_Spins
│
├── Materials/
│   ├── M_UEFN_Mannequin                     (Material 복제)
│   ├── M_UEFN_Mannequin_Masked_Bicolor      (Material 복제)
│   ├── MI_UEFN_Mannequin_CMC                (MI - Primary: Gray, Secondary: Brown)
│   └── MI_UEFN_Mannequin_Mover              (MI - Primary: Gray, Secondary: Blue)
│
├── MotionMatchingData/
│   ├── Schemas/
│   │   ├── PSS_Default                      (Trajectory + Group, cardinality 30)
│   │   ├── PSS_Idle                         (Trajectory + Group, cardinality 34)
│   │   ├── PSS_Jump                         (Trajectory + Group, cardinality 39)
│   │   ├── PSS_Stop                         (Trajectory + Group, cardinality 30)
│   │   ├── PSS_Traversal                    (Trajectory + Group, cardinality 18)
│   │   ├── PSS_Default_Mover                (Trajectory + Curve, cardinality 21)
│   │   ├── PSS_Traversal_Chooser            (Trajectory + Group, cardinality 18)
│   │   ├── PSS_Relaxed_Idle                 (Pose + Trajectory, cardinality 34)
│   │   ├── PSS_Relaxed_Loops                (Trajectory + Curve×2 + Heading, cardinality 25)
│   │   ├── PSS_Relaxed_Pivots
│   │   ├── PSS_Relaxed_Starts
│   │   ├── PSS_Relaxed_Stops
│   │   ├── PSS_Relaxed_Slide
│   │   ├── PSS_Relaxed_SlideExit
│   │   ├── PSS_Relaxed_Jump
│   │   ├── PSS_Relaxed_RunSpins
│   │   ├── PSS_Relaxed_StandTurn
│   │   ├── PSS_Relaxed_WalkSpins
│   │   └── PSS_Relaxed_SprintPivots
│   │
│   └── Databases/
│       ├── Dense/                            (35 databases)
│       │   ├── PSD_Dense_Stand_Walk_Loops
│       │   ├── PSD_Dense_Stand_Walk_Starts
│       │   ├── PSD_Dense_Stand_Walk_Stops
│       │   ├── PSD_Dense_Stand_Walk_Pivots
│       │   ├── PSD_Dense_Stand_Walk_SpinTransition
│       │   ├── PSD_Dense_Stand_Walk_Lands_Heavy
│       │   ├── PSD_Dense_Stand_Walk_Lands_Light
│       │   ├── PSD_Dense_Stand_Walk_FromTraversal
│       │   ├── PSD_Dense_Stand_Run_Loops
│       │   ├── PSD_Dense_Stand_Run_Starts
│       │   ├── PSD_Dense_Stand_Run_Stops
│       │   ├── PSD_Dense_Stand_Run_Pivots
│       │   ├── PSD_Dense_Stand_Run_SpinTransition
│       │   ├── PSD_Dense_Stand_Run_Lands_Heavy
│       │   ├── PSD_Dense_Stand_Run_Lands_Light
│       │   ├── PSD_Dense_Stand_Run_FromTraversal
│       │   ├── PSD_Dense_Stand_Sprint_Loops
│       │   ├── PSD_Dense_Stand_Sprint_Starts
│       │   ├── PSD_Dense_Stand_Sprint_Stops
│       │   ├── PSD_Dense_Stand_Sprint_Pivots
│       │   ├── PSD_Dense_Stand_Sprint_Lands_Light
│       │   ├── PSD_Dense_Stand_Sprint_Lands_Heavy
│       │   ├── PSD_Dense_Stand_Idles
│       │   ├── PSD_Dense_Stand_TurnInPlace
│       │   ├── PSD_Dense_Stand_Idle_Lands_Heavy
│       │   ├── PSD_Dense_Stand_Idle_Lands_Light
│       │   ├── PSD_Dense_Jumps
│       │   ├── PSD_Dense_Jumps_Far
│       │   ├── PSD_Dense_Jumps_FromTraversal
│       │   ├── PSD_Dense_Crouch_Walk_Loops
│       │   ├── PSD_Dense_Crouch_Walk_Starts
│       │   ├── PSD_Dense_Crouch_Walk_Stops
│       │   ├── PSD_Dense_Crouch_Walk_Pivots
│       │   ├── PSD_Dense_Crouch_TurnInPlace
│       │   └── PSD_Dense_Crouch_Idles
│       │
│       ├── Sparse/                           (16 databases)
│       │   ├── PSD_Sparse_Stand_Walk_{Loops,Starts,Stops,Pivots}
│       │   ├── PSD_Sparse_Stand_Run_{Loops,Starts,Stops,Pivots}
│       │   ├── PSD_Sparse_Stand_Sprint_{Loops,Starts,Stops,Pivots}
│       │   └── PSD_Sparse_Crouch_Walk_{Loops,Starts,Stops,Pivots}
│       │
│       ├── Extreme_Sparse/                   (16 databases)
│       │   ├── PSD_Extreme_Sparse_Stand_Walk_{Starts,Loops}
│       │   ├── PSD_Extreme_Sparse_Stand_TurnInPlace
│       │   ├── PSD_Extreme_Sparse_Stand_Sprint_{Starts,Loops}
│       │   ├── PSD_Extreme_Sparse_Stand_Run_{Stops,Starts,Loops}
│       │   ├── PSD_Extreme_Sparse_Stand_Idle_Lands
│       │   ├── PSD_Extreme_Sparse_Jumps
│       │   ├── PSD_Extreme_Sparse_Crouch_Walk_{Stops,Starts,Pivots,Loops}
│       │   ├── PSD_Extreme_Sparse_Crouch_TurnInPlace
│       │   └── PSD_Extreme_Sparse_Crouch_Idles
│       │
│       ├── Relaxed/                          (23 databases)
│       │   ├── PSD_Relaxed_Stand_Walk_{Loops,F_Loops,B_Loops,LL_Loops,LR_Loops,RL_Loops}
│       │   ├── PSD_Relaxed_Stand_Walk_{Stops,F_Starts,F_Pivots,F_Spins}
│       │   ├── PSD_Relaxed_Stand_Walk_{Lands_Light,Lands_Heavy,FromTraversal}
│       │   ├── PSD_Relaxed_Stand_WalkAndRun_Jump
│       │   ├── PSD_Relaxed_Stand_TurnInPlace
│       │   ├── PSD_Relaxed_Stand_Sprint_{Loops,Starts,Stops,Turns}
│       │   ├── PSD_Relaxed_Stand_Sprint_{Lands_Light,Lands_Heavy,Jump}
│       │   └── PSD_Relaxed_Stand_Run_Stops
│       │
│       └── PSD_Traversal                     (1 database)
│
└── Rigs/
    ├── ABP_UAF_UEFN_Mannequin               (AnimBlueprint - AnimInstance)
    └── ABP_UAF_UEFN_Mannequin_PostProcess    (AnimBlueprint - AnimInstance)
```

---

## 11.4 Phase별 작업 상세

### Phase 1: Pose Search Schemas (27개) - 완료

모든 스키마는 `SK_UEFN_Mannequin` 스켈레톤을 참조하며, sample_rate 30으로 생성되었습니다.
`add_default_channels=true`로 기본 채널(Trajectory + Pose)이 추가되었습니다.

**MotionMatchingData/Schemas/** (19개):

| 스키마 | 원본 채널 구성 | 비고 |
|--------|--------------|------|
| PSS_Default | Trajectory(19) + Group(11) | 대부분의 로코모션 DB에서 사용 |
| PSS_Idle | Trajectory(16) + Group(18) | Idle 전용 |
| PSS_Jump | Trajectory(27) + Group(12) | 점프 전용 |
| PSS_Stop | Trajectory(19) + Group(11) | 정지 전용 |
| PSS_Traversal | Trajectory(4) + Group(14) | 트래버설 전용 |
| PSS_Default_Mover | Trajectory(20) + Curve(1) | Mover 시스템 전용 |
| PSS_Traversal_Chooser | Trajectory(4) + Group(14) | 트래버설 Chooser용 |
| PSS_Relaxed_Idle | Pose(18) + Trajectory(16) | Relaxed Idle |
| PSS_Relaxed_Loops | Trajectory(20) + Curve×2 + Heading(3) | Relaxed 루프 |
| PSS_Relaxed_{Pivots,Starts,Stops,Slide,SlideExit,Jump,RunSpins,StandTurn,WalkSpins,SprintPivots} | 기본 채널 | Relaxed 서브카테고리 |

**ExperimentalStateMachineData/** (8개):

| 스키마 | 용도 |
|--------|------|
| PSS_SM_CMC_Idles | CMC State Machine - Idle |
| PSS_SM_CMC_LocoLoops | CMC State Machine - 로코모션 루프 |
| PSS_SM_CMC_LocoTransitions | CMC State Machine - 전환 |
| PSS_SM_Mover_{Stops,Loops,Transitions,TraversalTransitions,Spins} | Mover State Machine |

> **참고**: UAF 스키마는 `add_default_channels=true`로 생성되어 기본 채널 구조를 가집니다.
> 원본의 세부 채널 설정(가중치, 특정 본 등)은 에디터에서 수동 조정이 필요할 수 있습니다.

---

### Phase 2: Pose Search Databases (99개) - 완료

데이터베이스는 구조(스키마 매핑)만 생성된 상태이며, **애니메이션 시퀀스 연결은 별도 작업**이 필요합니다.

**스키마 매핑 규칙**:

| DB 이름 패턴 | 매핑된 스키마 |
|-------------|-------------|
| `*_Walk_Loops`, `*_Run_Loops`, `*_Sprint_Loops`, `*_Walk_Starts`, `*_Walk_Pivots`, `*_Run_Starts`, `*_Run_Pivots`, `*_Sprint_Starts`, `*_Sprint_Pivots`, `*_TurnInPlace`, `*_SpinTransition`, `*_Lands_*`, `*_FromTraversal` | PSS_Default |
| `*_Walk_Stops`, `*_Run_Stops`, `*_Sprint_Stops` | PSS_Stop |
| `*_Idles`, `*_Crouch_Idles` | PSS_Idle |
| `*_Jumps*` | PSS_Jump |
| `PSD_Traversal` | PSS_Traversal |
| `PSD_Relaxed_*_Loops`, `*_Lands_*`, `*_FromTraversal` | PSS_Relaxed_Loops |
| `PSD_Relaxed_*_Stops`, `*_Run_Stops` | PSS_Relaxed_Stops |
| `PSD_Relaxed_*_Starts` | PSS_Relaxed_Starts |
| `PSD_Relaxed_*_Pivots` | PSS_Relaxed_Pivots |
| `PSD_Relaxed_*_Jump` | PSS_Relaxed_Jump |
| `PSD_Relaxed_*_TurnInPlace` | PSS_Relaxed_StandTurn |
| `PSD_Relaxed_*_Spins` | PSS_Relaxed_WalkSpins |
| `PSD_Relaxed_*_Turns` | PSS_Relaxed_SprintPivots |
| SM 계열 | 동명의 SM 스키마 |

---

### Phase 3: BlendSpace & AimOffset (7개, 79 샘플) - 완료

모든 샘플이 원본과 동일한 좌표에 원본 애니메이션 참조로 추가되었습니다.

| 에셋 | 타입 | 축 설정 | 샘플 수 |
|------|------|---------|--------|
| BS_Relaxed_Lean_Head | BlendSpace | X(-1~1), Y(-1~1) | 13 |
| BS_Relaxed_Run_Leans | BlendSpace | X(-1~1), Y(-1~1) | 5 |
| BS_Relaxed_Walk_Leans | BlendSpace | X(-1~1), Y(-1~1) | 5 |
| BS_Relaxed_Run_Lean_FB | BlendSpace | X(-1~1), Y(-1~1) | 13 |
| BS_Relaxed_Run_Lean_LR | BlendSpace | X(-1~1), Y(-1~1) | 13 |
| BS_Neutral_AO_Stand | AimOffset | Yaw(-90~90), Pitch(-90~90) | 15 |
| BS_Neutral_AO_Stand_NoSmoothing | AimOffset | Yaw(-90~90), Pitch(-90~90) | 15 |

---

### Phase 4: Animation Blueprints (2개) - 완료

| 에셋 | Parent Class | 스켈레톤 | 용도 |
|------|-------------|----------|------|
| ABP_UAF_UEFN_Mannequin | AnimInstance | SK_UEFN_Mannequin | UAF 메인 애니메이션 |
| ABP_UAF_UEFN_Mannequin_PostProcess | AnimInstance | SK_UEFN_Mannequin | 후처리 애니메이션 |

> **참고**: ABP는 빈 상태로 생성되었습니다. UAF에서는 ABP 대신 AnimNext Workspace/System이
> 애니메이션을 구동하지만, 전환 과정에서의 비교 테스트나 후처리용으로 활용할 수 있습니다.

---

### Phase 5: Materials (4개) - 완료

| 에셋 | 타입 | 원본 | 비고 |
|------|------|------|------|
| M_UEFN_Mannequin | Material | 복제 | 기본 마네킹 머티리얼 |
| M_UEFN_Mannequin_Masked_Bicolor | Material | 복제 | 바이컬러 마스크 머티리얼 |
| MI_UEFN_Mannequin_CMC | MaterialInstance | 새로 생성 | Primary: Gray(0.417), Secondary: Brown(0.276, 0.138, 0.063) |
| MI_UEFN_Mannequin_Mover | MaterialInstance | 새로 생성 | Primary: Gray(0.417), Secondary: Blue(0.076, 0.120, 0.297) |

---

## 11.5 공유 에셋 (참조만, 복제 안 함)

다음 에셋들은 원본 위치에서 그대로 참조합니다:

### Skeleton & Mesh
- `/Game/Characters/UEFN_Mannequin/Meshes/SK_UEFN_Mannequin` — 88개 본
- `/Game/Characters/UEFN_Mannequin/Meshes/SKM_UEFN_Mannequin` — 3 LOD, 1 Material Slot
- `/Game/Characters/UEFN_Mannequin/Meshes/Character_LodSettings`

### Textures
- `/Game/Characters/UEFN_Mannequin/Textures/T_UEFN_Mannequin_D` — Diffuse
- `/Game/Characters/UEFN_Mannequin/Textures/T_UEFN_Mannequin_N` — Normal
- `/Game/Characters/UEFN_Mannequin/Textures/T_UEFN_Mannequin_Mask_Bicolor` — Mask

### Rigs
- `/Game/Characters/UEFN_Mannequin/Rigs/IK_UEFN_Mannequin` — Full Body IK, 4 Goals, 30 Retarget Chains
- `/Game/Characters/UEFN_Mannequin/Rigs/PA_UEFN_Mannequin` — Physics Asset
- `/Game/Characters/UEFN_Mannequin/Rigs/MDT_UEFN_Mannequin` — Mirror Data Table

### Animation Sequences (1,700+개)
원본 위치의 모든 AnimSequence/AnimMontage를 그대로 참조:
- `/Game/Characters/UEFN_Mannequin/Animations/Walk/` (353개)
- `/Game/Characters/UEFN_Mannequin/Animations/Run/` (360개)
- `/Game/Characters/UEFN_Mannequin/Animations/Sprint/` (65개)
- `/Game/Characters/UEFN_Mannequin/Animations/Crouch/` (215개)
- `/Game/Characters/UEFN_Mannequin/Animations/Jump/` (142개)
- `/Game/Characters/UEFN_Mannequin/Animations/Idle/` (47개)
- `/Game/Characters/UEFN_Mannequin/Animations/Slide/` (40개)
- `/Game/Characters/UEFN_Mannequin/Animations/Traversal/` (143개)
- `/Game/Characters/UEFN_Mannequin/Animations/AimOffset/` (45개)
- `/Game/Characters/UEFN_Mannequin/Animations/Poses/` (40개)
- `/Game/Characters/UEFN_Mannequin/Animations/Interactions/` (27개)
- `/Game/Characters/UEFN_Mannequin/Animations/Avoidance/` (12개)

### Chooser Tables (10개)
- `CHT_PoseSearchDatabases` / `CHT_PoseSearchDatabases_{Dense,Sparse,ExtremeSparse,Relaxed}`
- `CHT_CMCCharacterAnimations` / `CHT_MoverCharacterAnimations`
- `CHT_TraversalMontages_{CMC,Mover}`

---

## 11.6 자동화 스크립트

에디터에서 실행할 Python 스크립트가 프로젝트 `Scripts/` 폴더에 준비되어 있습니다.

### 스크립트 실행 방법

Unreal Editor에서:
- **Tools > Execute Python Script** → 파일 선택
- 또는 **Output Log > Python 콘솔**에서:
  ```python
  exec(open(r'프로젝트경로/Scripts/스크립트이름.py').read())
  ```

### 제공 스크립트 목록

| 스크립트 | 용도 | 실행 순서 |
|---------|------|----------|
| `UAF_CopyPSDSequences.py` | 99개 PSD에 원본 시퀀스 일괄 복사 + 저장 | **1번째** |
| `UAF_CreateWorkspaceAndSystem.py` | Workspace/System/Graph/Module 생성 시도 (실패 시 수동 가이드 출력) | **2번째** |

### UAF_CopyPSDSequences.py 상세

- 99개 원본 PSD → UAF PSD 매핑 테이블 내장
- 원본의 `sequences` 프로퍼티를 읽어 UAF DB에 설정
- 이미 시퀀스가 있는 DB는 건너뜀 (중복 방지)
- 완료 후 모든 변경 에셋 자동 저장
- 실행 시간: ~30초 (99개 DB 일괄 처리)

### UAF_CreateWorkspaceAndSystem.py 상세

- AnimNext 팩토리 자동 탐색 후 에셋 생성 시도
- 팩토리 미발견 시 수동 생성 가이드를 Output Log에 출력
- 생성 대상:
  - `WS_UEFN_Mannequin` (Workspace)
  - `Sys_UEFN_Mannequin` (System)
  - `DI_UEFN_Mannequin` (Data Interface)
  - `AG_UEFN_Mannequin` (Animation Graph)
  - `Mod_UEFN_Mannequin_Logic` (Module)

---

## 11.7 공유 에셋 참조 검증 결과

2026-03-28 검증 완료. 모든 UAF 에셋이 원본 공유 에셋을 정상 참조합니다.

| 검증 항목 | 참조 대상 | 상태 |
|----------|----------|------|
| PSS_Default.skeleton | `SK_UEFN_Mannequin` | 정상 |
| PSD_Dense_Stand_Idles.schema | UAF `PSS_Idle` | 정상 |
| PSD_Dense_Stand_Idles.sequences[0] | 원본 `M_Neutral_Stand_Idle_Loop` | 정상 |
| BS_Neutral_AO_Stand.skeleton | `SK_UEFN_Mannequin` | 정상 |
| BS_Neutral_AO_Stand.samples (15개) | 원본 AO 시퀀스 | 정상 |
| ABP_UAF_UEFN_Mannequin.skeleton | `SK_UEFN_Mannequin` | 정상 |
| MI_UEFN_Mannequin_CMC.parent | UAF `M_UEFN_Mannequin_Masked_Bicolor` | 정상 |
| MI_UEFN_Mannequin_CMC.parameters | 원본과 동일 (3개 오버라이드) | 정상 |

---

## 11.8 남은 작업 (TODO)

### 에디터 스크립트 실행 (자동)

- [ ] `Scripts/UAF_CopyPSDSequences.py` 실행 → PSD 시퀀스 일괄 연결
- [ ] PSD 인덱스 리빌드: Content Browser에서 PSD 전체 선택 > 우클릭 > Rebuild Search Index
- [ ] 스키마 채널 세부 설정: 원본 스키마의 세부 채널 가중치/본 설정 수동 복제

### UAF 전용 에셋 (에디터에서 생성)

`Scripts/UAF_CreateWorkspaceAndSystem.py` 실행 후, 실패한 항목은 수동 생성:

- [ ] **UAF Workspace**: `WS_UEFN_Mannequin` → [04_WORKSPACE_AND_SYSTEM.md](./04_WORKSPACE_AND_SYSTEM.md)
- [ ] **UAF System**: `Sys_UEFN_Mannequin` → [04_WORKSPACE_AND_SYSTEM.md](./04_WORKSPACE_AND_SYSTEM.md)
- [ ] **Data Interface**: `DI_UEFN_Mannequin` → [05_DATA_INTERFACE.md](./05_DATA_INTERFACE.md)
- [ ] **Animation Graph**: `AG_UEFN_Mannequin` → [06_ANIMATION_GRAPH.md](./06_ANIMATION_GRAPH.md)
- [ ] **Module**: `Mod_UEFN_Mannequin_Logic` → [08_MODULES.md](./08_MODULES.md)
- [ ] **AnimNextComponent** 추가 → [09_CHARACTER_INTEGRATION.md](./09_CHARACTER_INTEGRATION.md)

### System 실행 흐름 설정

Workspace 내 System에서 다음 순서로 노드를 배치:

```
[System Start]
  → [Generate Reference Pose]
  → [Update Data Interface]
  → [Execute Module: Mod_UEFN_Mannequin_Logic]
  → [Calculate Trajectory]
  → [Execute Animation Graph: AG_UEFN_Mannequin]
  → [Write Pose to Mesh]
[System End]
```

### 선택적 작업

- [ ] Chooser Table UAF 버전 생성 (필요시 - 원본 공유 가능)
- [ ] 새로운 MI 색상 변형 추가 (UAF 캐릭터 시각적 구분용)

---

## 11.9 에셋 수량 요약

| 카테고리 | 생성 수 | 상태 |
|---------|--------|------|
| Pose Search Schemas | 27 | 완료 (기본 채널) |
| Pose Search Databases | 99 | 완료 (일부 시퀀스 연결됨, 나머지는 스크립트 실행 필요) |
| BlendSpace | 5 | 완료 (샘플 포함) |
| AimOffset | 2 | 완료 (샘플 포함) |
| Animation Blueprint | 2 | 완료 (빈 ABP) |
| Material | 2 | 완료 (복제) |
| MaterialInstance | 2 | 완료 (파라미터 동일) |
| Python 자동화 스크립트 | 2 | 완료 |
| **총 생성 에셋** | **139 + 스크립트 2** | |
| 공유 참조 에셋 | ~1,730+ | 검증 완료 |

---

[← 이전: 디버깅 & 검증](./10_DEBUGGING_AND_VALIDATION.md) | [목차](./00_INDEX.md)
