---
name: PC_01 Motion Matching 파이프라인 와이어링
description: PC_01_ABP의 실제 파이프라인 = Chooser→BlendStack (MM은 Chooser row의 UseMotionMatching 토글로만 호출). PSD 7개 카탈로그 + Stop/Pivot 등록 위치.
type: project
originSessionId: 52fcc70d-c480-47be-be56-421b47dea3e8
---

## ⚠️ 가설 정정 (2026-05-15)

**이전 가설 폐기**: `EvaluateChooser2 → ValidAnimFromChooser → MotionMatch` 직선 와이어링은 **사실 아님**. ValidAnimFromChooser 변수는 ABP에 없거나 데드코드. MotionMatch는 메인 AnimGraph에 노드로 존재하지 않음.

**실제 구조 (Inspector 2026-05-15 실측, abp_cdo_chooser.json + ssmbsa_graph.json)**:

```
State Machine 진입 (OnStateEntry_*)
  → SetStateMachineBlendStackAnim(BlendStackInputs)         # 60 노드 그래프
      ├─ EvaluateChooser2(EvieAnimChooser_StateMachine)
      │    → Result: array<AnimationAsset>
      │    → SBStateMachineChooserOut 구조체:
      │         UseMotionMatching:bool          ←← row별 MM 토글
      │         MotionMatchingCostLimit:double  ←← MM cost 상한
      │         StartTime:double
      │         BlendTime:double
      │         BlendProfile:UBlendProfile
      │         Tag:array<FName>
      ├─ Set BlendStackInputs.Anim = ValidAnim (Result 첫 항목)
      └─ BlendStack (메인 AnimGraph 노드, MaxActiveBlends=4)
            └─ PerSample 그래프 4개 × (OrientationWarping + StrideWarping)
  → DeadBlending_0 → ... → Inertialization_1 → Root_0
```

**핵심**: MM은 메인 그래프에 없음. **Chooser row마다 "UseMotionMatching: bool" 토글**이 있어서 그 row가 true일 때만 Pose Search/MM이 호출됨 (`Break Pose Search Blueprint Result` 노드 경로로). 즉 Chooser가 메인 두뇌, MM은 선택적 도구.

## PC_01 PSD 카탈로그 7개 (실측)

| PSD | seq | poses | Schema | search | 카테고리 분포 |
|---|---|---|---|---|---|
| `PSD_GroundMoving` | 57 | 1800 | `PSS_SM_LocoLoops` (cardinality=**1**, Curve "Phase"만) | PCAKDTree | Loop 30 + Arc 16 + Strafe 2 + Battle Walk 9 |
| `PSD_GroundMovingTransit` | 210 | 3327 | `PSS_SM_LocoTransitions` (cardinality=34, Group12+Trajectory22) | BruteForce | Start 49 + Pivot(_Pivot_)30 + Turn_045 12 + Turn_090 16 + Turn_180 16 + Turn_135 8 + Transition 20 + Reface 49 + Jump/Land 26 |
| `PSD_GroundIdleTransit` | 77 | 1176 | `PSS_SM_LocoTransitions` | PCAKDTree | **Stop 48** (Run/Sprint/Jog/Walk) + Jump_Land_Stand 11 + Fist Start/End 등 |
| `PSD_Idles` | 3 | — | `PSS_SM_Idles` | — | Battle/Fist_Battle/Stand Idle Loop |
| `PSD_Falling` | 24 | — | `PSS_SM_Jump` | — | Jump Start Run/Sprint/Stand |
| `PSD_WriggleGroundMoving` | 12 | — | `PSS_SM_LocoLoops` | — | WriggleMove Walk/Jog L/R |
| `PSD_WriggleGroundMovingTransit` | — | — | — | — | (별도 확인) |

CostBias 모든 PSD 공통: ContinuingPose=-0.01, Looping=-0.005, Base=0.

## Stop / Pivot orphan 여부 (확정)

- **Stop**: orphan **NO**. PSD_GroundIdleTransit에 48개 등록.
- **Pivot(=Turn_090/180)**: orphan **NO**. PSD_GroundMovingTransit에 32개 정확히 등록 (Walk/Jog/Run/Sprint × {L,R} × {90,180} × {Lfoot,Rfoot}).

이전 메모리 "Stop 50+개 PSD 미등록", "Turn 시리즈 PSD 0개" 둘 다 **잘못된 진단**. `find_references`가 PoseSearchDatabase 등록을 false negative 한 결과.

## 발견된 진짜 갭 (Inspector 2026-05-15)

| # | 갭 | 영향 | 우선순위 |
|---|---|---|---|
| 1 | **PSS_SM_LocoLoops cardinality=1 (Curve "Phase" 1채널뿐)** | PSD_GroundMoving 57개 Loop/Arc/Strafe 매칭이 사실상 Phase 커브 1개로만 좁힘. Trajectory/Pose 채널 부재. | 🔴 검증 필요 |
| 2 | **PoseSearchHistoryCollector_0 bGenerateTrajectory=False** | PSS_SM_LocoTransitions의 Trajectory 채널(cardinality 22/34=65%) 가동 여부 불명. 외부에서 `PoseSearchData_Moving`/`Idle` 변수 주입 경로 필요. 끊겼으면 Transition 매칭의 65%가 죽음. | 🔴 추적 필요 |
| 3 | `Reface_Start_*_090/180` 49개 ↔ `Turn_*_090/180` 32개 같은 PSD 공존 | Chooser row 분기 잘못되면 사용자가 "Pivot 안 나와"라고 느낄 때 Reface가 매칭될 수 있음 | 🟠 |
| 4 | Walk Turn_045 누락 가능성 (등급 불균등) | 살짝 방향전환이 90도로 점프 | 🟡 |
| 5 | Fist_Battle Turn 시리즈 0 (전투는 _Pivot_ 30개만) | 전투 자세 방향전환 _Pivot_으로 충분한지 검증 | 🟢 |
| 6 | BlendStack `BlendTime=0.2 + bUseInertialBlend=False` | DeadBlending_0이 후처리하지만 BlendStack 자체는 보간 의존 | 🟡 |

## BlendStack 파라미터 (CDO 실측)

- BlendTime=0.20, BlendOption=CubicInOut, MaxActiveBlends=4
- BlendspaceUpdateMode=InitialOnly, BlendProfile=None, bUseInertialBlend=False
- PerSample 4개 슬롯 각각: OrientationWarping + StrideWarping 1쌍씩 = 자동 Warping 통과

**Warping 파라미터 (4슬롯 동일)**:
- OrientationWarping: DistributedBoneOrientationAlpha=0.7, RotationInterpSpeed=13, CounterCompensateInterpSpeed=45, MaxCorrectionDegrees=90, LocomotionAngleDeltaThreshold=135
- StrideWarping: MinRootMotionSpeedThreshold=10, bOrientStrideDirectionUsingFloorNormal=True, bDisableIfMissingRootMotion=True

## PoseSearchHistoryCollector_0 파라미터

- PoseCount=2, SamplingInterval=0
- CollectedBones: foot_l, foot_r, thigh_l, thigh_r, spine_04, pelvis, VB ik_foot_l, ...
- CollectedCurves: ["Phase"]
- **bGenerateTrajectory=False** ← 외부 변수 주입 가정
- TrajectoryPredictionCount=8, HistoryCount=10

## EvieAnimChooser_StateMachine 구조

- 위치: `/Game/Art/Character/PC/PC_01/StateMachine/EvieAnimChooser_StateMachine`
- 6 rows × 2 cols
- 3 nested ChooserTables: `GroundIdle`, `GroundMoving`, `Falling`
- 출력: `SBStateMachineChooserOut` 구조체 (UseMotionMatching/CostLimit/StartTime/BlendTime/BlendProfile/Tag)

## 변경 이력 — Sprint_to_Battle_Jog 4종 PSD_GroundIdleTransit 추가/롤백 (2026-05-13)

- 추가 시도: P_Player_Transition_Sprint_to_Battle_Jog_{F,LL,RL,B}_Lfoot 4종을 PSD_GroundIdleTransit에 등록 (idx 77~80).
- 결과: PIE에서 변화 없음 — 사용자 보고로 전면 롤백.
- 교훈: "loco→loco" 트랜지션을 Idle 진입용 PSD에 넣어도 Chooser가 그 PSD로 가는 조건이 안 맞으면 매치 불가.

## Why
PC_01 MM 작동 진단의 출발점. **Chooser가 메인 두뇌**임이 확정됐으므로, "MM이 X 안 골라" 호소는 거의 모두 Chooser row 조건/UseMotionMatching 토글 문제로 환원됨.

## How to apply
- "MM이 X 모션 안 골라" 호소 시 → Chooser row 시각 확인이 1순위 (Monolith 미접근, 에디터 필수)
- PSD 콘텐츠는 이미 충분. 진짜 처방은 Chooser row 정밀화 + PSS 채널 보강
- Schema cardinality 1짜리(PSS_SM_LocoLoops)는 의도 vs 누락 검증 필요

## Monolith 한계 (확인됨)
- ChooserTable의 `ResultsStructs[i]` / `ColumnsStructs[i]` 는 FInstancedStruct로 opaque
- 행 단위 시각 확인은 에디터에서 직접 열어야 함
- `find_references`는 PoseSearchDatabase 등록을 detection 못 함 (false negative)

## 산출 덤프 파일 (2026-05-15 실측)
- `C:\Dev\Sanjuk-Unreal\Briefing\_tmp\abp_cdo_chooser.json` — ABP CDO 342 properties
- `Briefing\_tmp\ssmbsa_graph.json` — SetStateMachineBlendStackAnim 60 노드
- `Briefing\_tmp\psd_*.json` — 7 PSD 시퀀스 dump
- `Briefing\_tmp\pss_loops.json` / `pss_transitions.json` — Schema cardinality

## 관련 경로
- `/Game/Art/Character/PC/PC_01/MotionMatching/PSD/PSD_*`
- `/Game/Art/Character/PC/PC_01/MotionMatching/PSS/PSS_SM_*`
- `/Game/Art/Character/PC/PC_01/StateMachine/EvieAnimChooser_StateMachine`
- `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP`
