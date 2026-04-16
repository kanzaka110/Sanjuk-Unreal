# SB2 PC_01 Motion Matching 구조 덤프

수집일: 2026-04-16  
Monolith 버전: 0.12.1  
기준 경로: `/Game/Art/Character/PC/PC_01/MotionMatching/`

---

## 1. PoseSearch Schema 목록 (5개)

| 에셋명 | 경로 | 용도 |
|--------|------|------|
| **PSS_SM_Idles** | `.../PSS/PSS_SM_Idles` | 아이들 상태 |
| **PSS_SM_LocoLoops** | `.../PSS/PSS_SM_LocoLoops` | 이동 루프 |
| **PSS_SM_LocoTransitions** | `.../PSS/PSS_SM_LocoTransitions` | 이동 트랜지션 |
| **PSS_SM_Jump** | `.../PSS/PSS_SM_Jump` | 점프/낙하 |
| **PSS_Travel** | `/Game/Art/Character/PC/PC_01/TravelSystem/PSS_Travel` | 트래블 시스템 |

---

## 2. PoseSearch Database 목록 (7개)

| 에셋명 | 경로 | 사용 Schema | 시퀀스 수 |
|--------|------|------------|---------|
| **PSD_Idles** | `.../PSD/PSD_Idles` | PSS_SM_Idles | 3 |
| **PSD_GroundMoving** | `.../PSD/PSD_GroundMoving` | PSS_SM_LocoLoops | 57 |
| **PSD_GroundMovingTransit** | `.../PSD/PSD_GroundMovingTransit` | PSS_SM_LocoTransitions | 211 |
| **PSD_GroundIdleTransit** | `.../PSD/PSD_GroundIdleTransit` | PSS_SM_LocoTransitions | 77 |
| **PSD_Falling** | `.../PSD/PSD_Falling` | PSS_SM_Jump | 24 |
| **PSD_WriggleGroundMoving** | `.../PSD/PSD_WriggleGroundMoving` | (확인 필요) | - |
| **PSD_WriggleGroundMovingTransit** | `.../PSD/PSD_WriggleGroundMovingTransit` | (확인 필요) | - |

---

## 3. Schema 상세

### PSS_SM_Idles
```
sample_rate:       30 fps
skeleton:          PC_01_Body_001_Skeleton
schema_cardinality: 27
channels:
  [0] PoseSearchFeatureChannel_Pose  cardinality=27  offset=0
```

### PSS_SM_LocoLoops
```
sample_rate:       30 fps
skeleton:          PC_01_Body_001_Skeleton
schema_cardinality: 1
channels:
  [0] PoseSearchFeatureChannel_Curve  cardinality=1  offset=0
```
**참고**: 커브 채널 1개만 사용 — BlendStack 선택용 경량 스키마.

### PSS_SM_LocoTransitions
```
sample_rate:       30 fps
skeleton:          PC_01_Body_001_Skeleton
schema_cardinality: 34
channels:
  [0] PoseSearchFeatureChannel_Group      cardinality=12  offset=0
  [1] PoseSearchFeatureChannel_Trajectory cardinality=22  offset=12
```
**참고**: Group(포즈 12D) + Trajectory(22D) = 34D 피처 벡터.

### PSS_SM_Jump
```
sample_rate:       30 fps
skeleton:          PC_01_Body_001_Skeleton
channels:          미상 (PSD_Falling에서 참조 확인)
```

---

## 4. PSD_Idles 시퀀스 목록 (3개)

모두 `UnmirroredOnly` / sampling_range_start=0, end=0 (전체 사용)

| 인덱스 | 애니메이션명 | 경로 |
|--------|-----------|------|
| 0 | P_Player_Battle_Idle_Loop | `.../Animation/Body/Idle/` |
| 1 | P_Player_Fist_Battle_Idle_Loop | `.../Animation/Body/Idle/` |
| 2 | P_Player_Stand_Idle_Loop | `.../Animation/Body/Idle/` |

---

## 5. PSD_GroundMoving 시퀀스 목록 (57개)

`UnmirroredOnly` 전용. 폴더별 분류:

### Run (달리기) — 7개
- P_Player_Run_Arc_Small_L / _R
- P_Player_Run_Arc_Tight_L / _R
- P_Player_Run_Arc_Wide_L / _R
- P_Player_Run_Loop_F

### Sprint (전력질주) — 9개
- P_Player_Sprint_Arc_Small_L / _R
- P_Player_Sprint_Loop_F
- P_Player_Sprint_Loop_F_L_20 / _R_20
- P_Player_Sprint_Loop_FL / _FR

### Walk (걷기) — 20개
- P_Player_Walk_Arc_F_Small_L / _R
- P_Player_Walk_Arc_F_Tight_L / _R
- P_Player_Walk_Arc_F_Wide_L / _R
- P_Player_Walk_Circle_Strafe_L / _R
- P_Player_Walk_Loop_B / _BL / _BR / _F / _FL / _FR
- P_Player_Walk_Loop_F_L_20 / _F_R_20
- P_Player_Walk_Loop_LL / _LR / _RL / _RR
- P_Player_Fist_Battle_Walk_B / _F / _LL / _RL (배틀 워크 4개)

### Jog (조깅) — 21개
- P_Player_Jog_Arc_Small_L / _R
- P_Player_Jog_Loop_B / _BL / _BR / _F / _FL / _FR
- P_Player_Jog_Loop_F_L_20 / _F_R_20
- P_Player_Jog_Loop_LL / _LR / _RL / _RR
- P_Player_Fist_Battle_Jog_B / _F / _LL / _RL / _RR (배틀 조그 5개)

---

## 6. PSD_GroundMovingTransit 시퀀스 목록 (211개)

PSS_SM_LocoTransitions 스키마 사용. 카테고리:

### Jump Landing → Run (착지 후 달리기) — 4개
- P_Player_Jump_F_Land_Run_Heavy_Lfoot / Rfoot
- P_Player_Jump_F_Land_Run_Light_Lfoot / Rfoot

### Jump Landing → Walk — 4개
- P_Player_Jump_F_Land_Walk_Light_Lfoot / Rfoot
- P_Player_Jump_F_Land_Walk_Light (기타)

### Run Start (달리기 시작) — 다수
### Pivot / Direction Change — 다수
### Wriggle 관련 Transit — 다수
### Fist Battle 전용 Transit — 다수

**규모**: 전환 전용 211개 시퀀스 — 가장 방대한 DB.

---

## 7. PSD_GroundIdleTransit 시퀀스 목록 (77개)

### Stop 애니메이션 (이동 → 아이들)
- Walk Stop: F/FL/FR/B/BL/BR/LL/LR/RL/RR × Lfoot/Rfoot (총 20개+)
- Run Stop: F/FL/FR × Lfoot/Rfoot
- Jog Stop: F × Lfoot/Rfoot
- Sprint Stop: F/FL/FR × Lfoot/Rfoot

### Turn In Place (제자리 회전)
- Stand Turn: 045/090/135/180 × L/R (8개)
- Fist Battle Turn: 045/090/135/180 × L/R (8개)

### Battle 상태 전환
- P_Player_Fist_Battle_End
- P_Player_Fist_Battle_Start

### Jump Landing → Stand
- Jump_F/B/LL/RL Land Stand Heavy/Light × Lfoot/Rfoot (12개+)

---

## 8. PSD_Falling 시퀀스 목록 (24개)

PSS_SM_Jump 스키마 사용.

### Jump Start (지상 → 공중)
- P_Player_Jump_F_Start_Run_Lfoot / Rfoot
- P_Player_Jump_F_Start_Sprint_Lfoot / Rfoot
- P_Player_Jump_F_Start_Stand_Lfoot / Rfoot
- P_Player_Jump_F_Start_Walk_Lfoot / Rfoot
- P_Player_Jump_F_Start_Stand_SB1 / _SB1_2 (SB2 커스텀)
- P_Player_Jump_LL_Start_Lfoot / Rfoot

### Fist Battle Jump Start
- P_Player_Fist_Battle_Jump_F_Start_Jog_Lfoot
- P_Player_Fist_Battle_Jump_LL_Start_Jog_Lfoot
- P_Player_Fist_Battle_Jump_B_Start_Jog_Lfoot
- P_Player_Fist_Battle_Jump_RL_Start_Jog_Lfoot
- P_Player_Fist_Battle_Jump_F_Start_Walk_Lfoot
- P_Player_Fist_Battle_Jump_B_Start_Walk_Lfoot
- P_Player_Fist_Battle_Jump_LL_Start_Walk_Lfoot
- P_Player_Fist_Battle_Jump_RL_Start_Walk_Lfoot
- P_Player_Fist_Battle_Jump_F_Start_Stand_Lfoot

### Fist Battle Jump Landing → Walk (공중)
- P_Player_Fist_Battle_Jump_LL_Land_Walk_Light_Rfoot
- P_Player_Fist_Battle_Jump_RL_Land_Walk_Light_Rfoot
- P_Player_Fist_Battle_Jump_F_Land_Stand_Light_Rfoot

### Fall Loop
- P_Player_Jump_Loop_Fall (전체 사용)

---

## 9. PC_01_ABP에서 Motion Matching 연결

```
PC_01_ABP
  ├── 변수: CurrentSelectedDatabase (PoseSearchDatabase)
  ├── 변수: PoseSearchData_Moving (PoseSearchTrajectoryData)
  ├── 변수: PoseSearchData_Idle (PoseSearchTrajectoryData)
  ├── 변수: TrajectoryCollision (PoseSearchTrajectory_WorldCollisionResults)
  └── 그래프: Update Trajectory (궤적 업데이트)
```

State Machine 상태별 DB 매핑 (추정):
- `GroundIdle` → PSD_Idles
- `GroundMoving` → PSD_GroundMoving
- `TransitToGroundMoving` → PSD_GroundMovingTransit
- `TransitToGroundIdle` → PSD_GroundIdleTransit
- `Falling` / `TransitToFalling` → PSD_Falling

---

## 10. 네이밍 패턴 정리

```
P_Player_{Action}_{Direction}_{Speed}_{Foot}

방향 약자:
  F  = Forward
  B  = Backward
  FL = Forward-Left
  FR = Forward-Right
  BL = Backward-Left
  BR = Backward-Right
  LL = Left-Left (90도 이동)
  LR = Left-Right
  RL = Right-Left
  RR = Right-Right

속도:
  Walk < Jog < Run < Sprint

발:
  Lfoot = 왼발 시작
  Rfoot = 오른발 시작

아크:
  Arc_Small / Arc_Tight / Arc_Wide / Arc_F_* = 호선 이동

배틀 모드:
  Fist_Battle_* = 주먹 배틀 스탠스 전용
```
