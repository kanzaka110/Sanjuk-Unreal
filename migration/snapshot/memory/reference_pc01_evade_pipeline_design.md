---
name: PC_01 회피(Evade) 파이프라인 종합 설계 (2026-05-11 확정)
description: HasEvade 트리거 확장 + 다중 게이트 + PendingWalkMode lock 패턴. 회피 앞·뒤 일반 클립 끼어듦 차단 메커니즘.
type: reference
originSessionId: a44afb55-887c-4d27-8ee8-e38c3eca007b
---
## 최종 식 (2026-05-11)

```
HasEvade 갱신 (UpdateVariables.IfThenElse_2 Condition):
  if (회피 종료 검출) OR (RuleMoveFlag=="Evade") OR (RuleMoveFlag=="AirEvade"):
      HasEvade = true
      HasEvadeDuration = 0.3 (재충전)
  
효과: 회피 입력 시점부터 종료 후 0.3초까지 연속 true
```

```
MovementState 게이트 (UpdateMovementStateWithBuffer.Select_2.Index):
  CandidateMovementState = OR(
    IsMoving(),
    HasEvade,
    RuleMoveFlag=="Evade",
    RuleMoveFlag=="AirEvade"
  ) ? Moving : Idle
  
효과: 회피 동안 GroundIdle 진입 차단 → Run_Stop/Idle_loop 매칭 차단
```

```
PendingWalkMode lock (UpdatePendingWalkModeWithBuffer 시작):
  if HasEvade: SKIP function (회피 중 변경 금지)
  else: 정상 갱신
  
효과: 회피 시작 시점 Sprint/Run/Jog 값 유지 → N_AfterEvade row 매칭 안정
       → Transition_Jog_to_Run 등 속도 변환 시퀀스 끼어듦 차단
```

## 변수 정리

- `HasEvade` (bool, Evade) — 메인 게이트 변수
- `HasEvadeDuration` (double, Evade) — 카운트다운 타이머
- `EvadeDurationThreshold` (double, Evade) — **default 0.3** (0.05 → 0.3 상향)
- `RuleMoveFlag` (name, 디폴트) — "Evade"/"AirEvade"/"None"
- ~~`HasEvadeChanged`~~ — **폐기**됨
- ~~`PrevHasEvade`~~ — **폐기**됨

## Chooser 측 설정

```
Root GroundMoving Chooser:
  Locomotion_AfterEvade row:
    StateMachineMoveState = TransitToGroundMoving OR GroundMoving
    AnimStance            = Any
    PrevMovementMode      = Not InAir
    OverlayPoseState      = Default
    Has Evade             = True            ← 핵심 매칭 조건
    → N_AfterEvade sub-chooser 분기

N_AfterEvade sub-chooser:
  PrevMovementMode 별 row → P_Player_{Run,Sprint,Walk,Jog}_Start_F_Lfoot_Evade 출력
```

## 잔존 한계 (만족 수준이라 작업 종료)

- 완벽한 매끄러움은 아니지만 회피 앞·뒤로 일반 클립 끼어듦은 거의 차단
- 회피 모션 자체의 dynamic 끝 포즈와 AfterEvade Start 클립 시작 frame 차이는 본질적으로 존재
- 추가 개선이 필요하면 옵션:
  - N_AfterEvade row의 BlendStackInputs.BlendTime 0.25
  - FootPlacement Alpha 일시 감소
  - AfterEvade Start 클립 자체 sampling_range_start 조정

## Why
2026-05-11 세션에서 회피 후 Stop/Idle_loop/Reface_Start/Transition_Jog_to_Run 등 다수의 끼어듦을 단계별로 차단. 본질은 HasEvade를 회피 시작 시점부터 종료 후 0.3초까지 연속 true로 유지 + 그 값을 여러 갱신 함수의 게이트로 활용.

## How to apply
- "회피 후 X 클립 끼어듦" 호소 시 → 이 패턴 적용 단계 확인
- 새 끼어듦 시 → 어느 갱신 함수가 회피 중 변하는지 추적 → HasEvade 게이트 추가
- IsStarting 패턴 (B 트리거 + A latch + Tag release)과 일관됨 — `reference_pc01_isstarting_design.md` 참조
