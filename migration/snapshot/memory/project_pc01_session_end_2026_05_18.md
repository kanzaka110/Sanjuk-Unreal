---
name: pc01-session-end-2026-05-18
description: 2026-05-18 세션 종료 상태. IsTransition() 함수 정의 완성 + DrawDebug 마이그레이션 + trd 게이트/SM transition rule 시도 후 통째 롤백. dead code 정리 완료. SprintEnd* dead var 7개 잔존.
metadata: 
  node_type: memory
  type: project
  date: 2026-05-18
  originSessionId: 1299abe5-d83c-4a31-bc04-41fb9e09339f
---

# 2026-05-18 세션 종료 상태

## 최종 살아있는 변경 (디스크 저장 필요 — Ctrl+S)

### 1. IsTransition() BlueprintPure 함수 (신규)
- Pure function, ReturnValue: bool, params 없음
- category: StateMachine
- **NOT** ThreadSafe (Details 수동 활성화 안 됨, monolith 미지원)
- 식: `(PrevPendingWalkMode == SBWalk_Sprinting) AND NOT (PendingWalkMode == SBWalk_Sprinting) AND IsLockOn`
- 노드: VG PrevPwm + VG Pwm + VG IsLockOn + EnumEq×2 (B="SBWalk_Sprinting") + NOT + AND_inner + AND_outer → FunctionResult.ReturnValue
- 호출 위치: **DrawDebug 의 K2Node_CallFunction_66 만** (FT_7.IT 핀)
- 검증: PIE 에서 사용자 확인 — "질주에서 질주 스톱시 1틱 true로 바뀌는걸 확인"

### 2. 변수 IsTransition 삭제 + DrawDebug 마이그레이션
- 기존 변수 IsTransition (bool, IE=true, 디폴트 카테고리) 삭제됨
- DrawDebug 의 Get IsTransition (K2Node_VariableGet_18) → 함수 호출 (K2Node_CallFunction_66) 으로 교체

### 3. bShouldTransitToIdle 변수 (신규)
- bool, Buffer 카테고리, IE=false
- UpdateVariables 식 (단순 wrapper): `NOT bIsMoving AND NOT HasEvade`
- 노드: VG bIsMoving (K2Node_VariableGet_62) + VG HasEvade + NOT×2 + AND_A (K2Node_CallFunction_33) → Set bShouldTransitToIdle (K2Node_VariableSet_69)
- ExecSeq_3.then_12 → Set 실행
- **transition rule 교체 후 되돌릴 수 없음** (monolith set_transition_rule 가 multi-node rule 통째 교체)

### 4. SM transition rule 변경 (영구)
- `FromGroundMoving → TransitToGroundIdle` rule 이 multi-node (`NOT IsMoving AND NOT HasEvade`) → **단일 변수 `bShouldTransitToIdle` wire** 로 교체됨
- 식 자체는 동등 (bShouldTransitToIdle = NOT bIsMoving AND NOT HasEvade)
- 단 monolith API 한계로 multi-node 복원 불가 → bShouldTransitToIdle 삭제하면 transition 작동 안 함

## 시도했다가 통째 롤백한 작업

### A. UpdateTargetRotation trd 게이트 (inline)
- SelectFloat ×2 (Strafe/비-Strafe 분기) + EnumEquality ×2 + NOT + AND_inner + AND_outer + Get PrevPwm/Pwm/LO
- bPickA = IsTransition 식 결과 (한 틱). A=0.0 (차단), B=Normalize Axis raw
- ThreadSafe 에러로 함수 호출 못함 → inline 검증 식 사용
- **롤백 이유**: 사용자 호소 (Sprint→Jog 전환 시 Turn/Box 끼어듦) 영역 다름. trd 게이트는 회전 보정 차원, Turn/Box 는 BlendStack/MM/Chooser 차원. 게다가 정지 상태 raw trd=0.777 / 8.6 등 잔존 (게이트 무관 비정상)
- 10개 노드 모두 제거 → raw Normalize Axis → Set TargetRotationDelta 복원

### B. bShouldTransitToIdle 의 IsTransition AND 게이트
- 초기 식: `(NOT bIsMoving AND NOT HasEvade) AND (PrevPwm==Sprinting AND NOT Pwm==Sprinting AND IsLockOn)`
- **부작용**: 일반 정지 시 (Sprint 안 함) Idle 진입 못함. 사용자 보고 "이동 종료가 안되고 있어"
- 롤백: AND_FINAL 의 IsTransition 부분 disconnect + AND_A 결과 직접 Set bShouldTransitToIdle
- dead code 9개 노드 (EnumEq×2 + Get PrevPwm/Pwm/LO + NOT_PWM + AND_B/C/FINAL) 제거됨

## 사용자 호소 (해결 안 됨)

**Sprint→Jog 전환 시 Transition 앞에는 Turn 모션, 뒤에는 Box 모션이 끼어듦**

- 해결 영역: GroundMoving state 내부 **BlendStack / MM / Chooser** (5/15 메모리에 이미 명시: "Chooser row 영역, Monolith 한계")
- SM transition rule 차원 / UpdateTargetRotation trd 차원 모두 해결 못 함 확인
- 다음 세션 작업 영역: PSD_GroundMovingTransit ContinuingPoseCostBias 또는 Chooser row 수동 편집

## 남은 dead var (cleanup 미진행)

5/14 ~ 5/18 누적된 SprintEnd 관련 변수들. 모두 set 노드 없음 (UpdateVariables 의 isSprintEnding chain 만 살아있고 나머지는 dead var):

- `bIsSprintEndTransition` (bool, Buffer, IE=true)
- `SprintEndTransitionRemain` (real, Buffer)
- `SprintEndTransitionDuration` (real, Essential Values, IE=true, default 0.3)
- `SprintEndForcedDelay` (real, Essential Values, IE=true) — 어디서도 사용 안 됨
- `SprintEndTransitionAngleThreshold` (real, Essential Values, IE=true) — 어디서도 사용 안 됨
- `isSprintEnding` (bool, Buffer) — UpdateVariables 에서 매 틱 set (JustExitedSprint AND IsLockOn AND pwm!=Sprinting)
- `PrevIsSprintEnding` (bool, Buffer) — isSprintEnding 의 이전 값 캐시

AnimRewindRecorderEmit 에 Get 7개 박혀있어 (sset/setr/seta ANIM_REC 키 출력) cleanup 어려움 (220 노드 Append chain). 부작용 없음 (false/0 출력). 다음 세션에서 정리 가능.

## 학습 사항

1. **monolith set_transition_rule 한계**: 단일 boolean 변수만 wire 가능. 기존 multi-node rule 통째 교체. 복원 불가
2. **ABP 함수 ThreadSafe 마킹**: monolith API 에 명시적 액션 없음. set_function_params 도 미지원. ThreadSafe 그래프에서 호출하려면 함수를 ThreadSafe 마킹 필수 — 수동 (Details 패널) 시도 필요
3. **inline 식 우회 패턴**: 함수 호출 못 하면 EnumEquality + AND chain 을 그래프 안에 inline 추가 (copy_nodes 활용 가능)
4. **JustExitedSprint 변수의 naming 함정**: 실제 식은 `(PrevPwm == Sprinting) AND (Pwm == Sprinting)` — Sprint **유지** 의미, "Exit" 아님. 5/14 메모리 해석 오류
5. **사용자 호소가 SM transition rule 차원이 아니라 BlendStack/MM/Chooser 차원**: trd 게이트 / SM transition rule 게이트 모두 효과 없음

## 다음 세션 작업 후보

1. **PSD_GroundMovingTransit ContinuingPoseCostBias 재시도** — 5/15 -1.0 부작용 후 -0.01 원본 복원. 중간값 -0.5 시도
2. **Chooser row 영역** — Sprint→Jog Transition row 의 조건 보강 (Monolith Chooser 한계, 에디터 수동)
3. **dead var 7개 cleanup** — AnimRewindRecorderEmit chain 안 7개 Get 노드 + Append 페어 안전 제거
4. **bShouldTransitToIdle 활용도 결정** — 단순 wrapper 로 남길지 / 다른 transition rule 에도 활용할지

## 관련 메모리

- [[pc01-session-end-2026-05-15]] — 이전 세션. smooth chain 만 살아있다고 적혔지만 5/18 시점에는 UpdateTargetRotation 에 smooth chain 없음 (그 사이 폐기된 듯)
- [[pc01-sprint-end-transition]] — 5/14 작업 메모리, JustExitedSprint 해석 오류
- [[pc01-anim-rec-unmapped-added]] — 5/18 ANIM_REC 키 추가 (sset/setr/seta 등)
- [[reference-animgraph-node-editing]] — IsTransition BlendListByBool 패턴 권장
- [[monolith-animgraph-editing-limits]] — set_transition_rule 한계 추가 사례
