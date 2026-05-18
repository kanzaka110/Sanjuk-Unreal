---
name: PC_01 점프 후 제자리 착지 freeze 인과 + 처방
description: N_Idle_Land sub-chooser output struct의 UseMotionMatching=True 가 Land anim에 적용되어 BlendStack stuck → freeze. 처방 확정 (2026-04-29).
type: project
originSessionId: 3c08abb7-30a4-4914-aa98-a67f4e1039a6
---

# PC_01 점프 후 제자리 착지 freeze (2026-04-29 해결)

## 증상
- 시나리오: 전진 점프 → 공중에서 입력 release → 제자리 착지
- 결과: Land 포즈에서 freeze (얼음)
- MovementMode: Walking 정상 복귀 (CMC 측 정상)
- JustLanded: 1프레임 정상 true (`project_pc01_justlanded_logic.md` 참조)

## 진단 — 인과 사슬 (실측 기반)

### 1. 트랜지션 + State 진입 정상
```
Falling → TransitToGroundIdle 트랜지션 발동 (frame F)
   ↓
OnStateEntry_TransitGroundIdle 호출
   ↓
SetStateMachineBlendStackAnim(StateMachineState=NewEnumerator2, bForceBlend=true)
   ↓
EvieAnimChooser_StateMachine 평가 (Chooser)
```

### 2. Chooser 매칭 정상
- Frame F 변수 상태: JustLanded=true, MovementMode=OnGround, PrevMovementMode=InAir
- GroundIdle.uasset row[6] **`N_Idle_Land`** 매칭 (JustLanded=True 요구)
- N_Idle_Land sub-chooser 진입
- 7개 row 중 row 0 매칭: `P_Player_Jump_F_Land_Stand_Light_Lfoot` (IsHeavyLand=False, AnimStance=Peaceful)

### 3. Output struct 가 freeze 유발 ⭐
```
N_Idle_Land row 0 output struct:
  (BlendTime=0.1, BlendProfile="InstanceFeet_InstanceRoot", UseMotionMatching=TRUE)
```

**`UseMotionMatching=True` 로 BlendStack 에 입력** → MM이 다음 best 포즈를 Pose Search DB에서 검색 → **Land anim 의 포즈가 DB에 없음** (DB는 Locomotion Idle/Walk/Run/Sprint 위주) → MM 알고리즘이 다음 갈 포즈 못 찾고 한 포즈에서 stuck → 보이는 freeze.

## 핵심 원리 (일반화)

PC_01 은 Motion Matching 기반(`project_sb2_motion_matching.md`) → 모든 anim에 MM이 자동 적용되는 게 기본. 그러나:

- **연속 Locomotion** (Idle/Walk/Run/Sprint Loop) → MM 적합 (DB에 풍부한 포즈)
- **1회성 anim** (Land / Stagger / Knockdown / Hit / Cinematic) → MM 부적합 (DB 미포함)

1회성 anim 이 MM=True 로 BlendStack 에 들어가면 freeze 위험.

상세 원칙은 `reference_motion_matching_blendstack_oneshot.md` 참조.

## 처방 (확정)

**대상 에셋**: `/Game/Art/Character/PC/PC_01/StateMachine/GroundIdle` (sub-chooser N_Idle_Land 가 들어있는 ChooserTable)

**작업**: N_Idle_Land sub-chooser 의 모든 row output struct 에서 `UseMotionMatching` 체크 해제

| row | 시퀀스 | UseMotionMatching |
|---|---|---|
| 0 | P_Player_Jump_F_Land_Stand_Light_Lfoot | True → **False** |
| 1 | P_Player_Jump_F_Land_Stand_Light_Rfoot | True → **False** |
| 2 | P_Player_Jump_F_Land_Stand_Heavy_Lfoot | True → **False** |
| 3 | P_Player_Jump_F_Land_Stand_Heavy_Rfoot | True → **False** |
| 5 | P_Player_Fist_Battle_Jump_F_Land_Stand_Light_Rfoot | True → **False** |

(row 4, 6 은 "없음" — 빈 fallback row, 변경 불필요)

## 작업 위치 (UI)

1. Content Browser → `/Game/Art/Character/PC/PC_01/StateMachine/GroundIdle` 더블클릭
2. Chooser Editor → `N_Idle_Land` sub-chooser 진입
3. 우측 끝 **`SBStateMachineChooserOut`** 컬럼에서 각 row 셀 클릭
4. Details 패널의 InstancedStruct → `UseMotionMatching` 체크 해제
5. (팁) 한 row output struct 우클릭 → Copy → 다른 row 우클릭 → Paste 일괄 적용

## 시도한 변경 + 부작용 (참고용)

### 시도 1 — GroundIdle row[6] N_Idle_Land 의 JustLanded 컬럼 True → Any
- 부작용: 제자리 점프 등 다른 케이스에서도 row[6] 매칭 → N_Idle_Land sub-chooser 진입 → 같은 freeze 발생
- 결론: revert 필요

### 시도 2 — JustLanded 계산식 변경
- bool vs enum 타입 미스매치 가능성 (`JustLanded != OnGround`)
- 효과 없음
- 결론: revert 필요

### 시도 3 (실제 효과 확인) — 시퀀스 자체에서 MM 옵션 끄기
- 사용자 직접 검증: P_Player_Jump_F_Land_Stand_Light_Lfoot 의 시퀀스 옵션에서 MM 끄니 정상
- 그러나 시퀀스 자체 변경은 다른 chooser/state 에서 그 anim 쓸 때도 영향
- **권장 처방으로 대체**: Chooser output struct 에서 끄는 방식 (격리된 컨텍스트)
- 시퀀스 변경 revert 후 Chooser output 처방 적용

## 검증 (회귀 테스트)

수정 후 5종 시나리오 freeze 없는지 확인:
1. 전진 점프 → 공중 release → 제자리 착지 (원래 버그)
2. 전진 점프 → 입력 유지 → 이동 착지
3. 제자리 점프 (전후좌우 입력 없음)
4. Battle 모드 점프 → 제자리 착지
5. Heavy Land (높은 점프 / 빠른 낙하)

## How to apply
- 1회성 anim 을 Chooser row 결과로 둘 때, **output struct UseMotionMatching=False 가 기본 원칙**
- MM=True 는 Locomotion Loop 류에만 사용
- 점프/Stagger/Knockdown/Hit 류 row 추가 시 항상 MM=False 확인
- 같은 freeze 패턴이 보이면 가장 먼저 해당 row 의 output struct 부터 inspect
