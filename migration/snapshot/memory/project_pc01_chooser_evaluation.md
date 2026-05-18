---
name: PC_01 Chooser 평가 시점 구조
description: GroundMoving Chooser가 State 진입 시 1회만 평가되는 구조. 런타임 변수 변화 즉시 반영 어려움.
type: project
originSessionId: 5c97ced7-4741-424f-8e22-cc55efda4867
---
## 사실

PC_01_ABP의 `EvieAnimChooser_StateMachine` (GroundMoving Chooser) 은 **State 진입 시점에 1회만** 평가됨.

평가 경로:
```
OnStateEntry_GroundMoving / OnStateEntry_TransitGroundMoving / OnStateEntry_GroundIdle / ...
  → SetStateMachineBlendStackAnim(self, bForceBlend, StateMachineState)
    → K2Node_EvaluateChooser2 ("EvieAnimChooser_StateMachine")
      → BlendStackInputs struct 생성 → BlendStack에 공급
```

### StateMachineState enum 매핑 (일부 확인)
- `NewEnumerator1` = GroundMoving

### Sub-chooser 구조 (GroundMoving Chooser 내부)
- Root (21×9)
- `N_LockOn_Transit_Walking` / `Jogging` / `Running` / `Sprinting` — state **진입 순간**용 (transit)
- `N_LockOn_GroundMoving` (27×3) — LockOn 중 **지속 loop**용
- `N_TransitToGroundMoving_Peaceful` / `Battle` (89×6) — 전이 전용
- Terminal 8×4 nested sub-chooser가 `P_Player_Transition_Sprint_to_Battle_Jog_{F,B,LL,RL}_Lfoot` 직접 매핑

### `SetStateMachineBlendStackAnim` 함수 시그니처
```
self            (UObject)
bForceBlend     (bool, default false)   ← true면 현재 재생 시퀀스 강제 중단
StateMachineState (byte enum)            ← 어느 state의 BlendStack을 재설정할지
```

## Why
State 진입 시에만 평가되므로 loop 지속 중 변수 변화로 Chooser 결과 바꾸려면 BlendStack 강제 재호출 필요. 하지만 호출 시점이 엉뚱한 state면 기존 Stop/Start 모션을 GroundMoving Chooser 결과로 덮어써서 파괴적 side effect 발생.

## How to apply
- loop 중 조건 분기는 **Chooser보다 Motion Matching DB의 cost bias**로 제어하는 게 SB2 설계에 맞음
- Chooser Row를 전역 변수(Hysteresis 등)로 런타임 분기하는 접근은 **재평가 타이밍 + state 덮어쓰기** 이중 문제 유발
- 실시간 반응이 필요한 시퀀스 선택은 MM DB에 시퀀스 등록 + bias 조정으로 해결
- Sub-chooser 이름에 `Transit_*` 붙은 건 **진입 순간용** — loop 조건 Row 추가 금지

## 잔존 이슈 (2026-04-24 세션)
- **Sprint_to_Battle_Jog 오발동 (원형 strafe 중)**: Root Row 12의 `PrevMovementMode=Sprint MatchEqual` 조건이 Sprint 안 썼을 때도 매칭. PendingWalkMode 3단계 버퍼(Candidate→Pending→PrevPending)에서 Sprint stuck 의심. 미해결.
- **`JustExitedSprint` 변수**: 로직 수정 완료 — `(PrevPendingWalkMode == Sprint) AND (PendingWalkMode != Sprint)`. 과거엔 Enter 로직 (`Pending==Sprint AND Prev!=Sprint`)이라 이름과 반대였음.
