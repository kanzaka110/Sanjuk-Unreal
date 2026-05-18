---
name: pc01-transition-gate-phase1
description: PC_01_ABP transition 회전 보정 차단 게이트 4패턴 확장 (2026-05-15). 5/13 1패턴 게이트 5/14 ABP 손상으로 분실 → 처음부터 4패턴(Contains)으로 재구축 완료. Save는 P4 잠금으로 사용자 수동.
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
  status: rolled_back_2026-05-15

# ⚠️ ROLLED BACK 2026-05-15 — 노이즈 폭증으로 통째 롤백 (변수/노드 모두 제거). 이력만 보존. 룰: [[feedback-pose-search-data-moving-default-0]]
---

# PC_01 Transition 회전 보정 차단 게이트 — 4패턴 확장 (2026-05-15)

## 컨텍스트

매트릭스 처방 ①. transition 클립 재생 중에 ABP의 Strafe 분기 회전 보정과 클립 root motion 회전이 충돌하는 노이즈 D (Transition motion interjection) 직접 차단.

5/13 작업의 1패턴 EqualEqual_StrStr 게이트는 5/14 ABP 손상 과정에서 변수+노드+게이트 모두 사라짐 (`recovery-master-plan.md` TRACK-B의 C 그룹 미복원 상태). 처음부터 4패턴으로 재구축.

## 매칭 룰 (2026-05-15 — 3패턴으로 축소됨)

```
bIsPlayingTransitionBack =
    Contains(CurrentSequenceName, "Sprint_to_Battle") OR
    Contains(CurrentSequenceName, "Sprint_to_LockOn") OR
    Contains(CurrentSequenceName, "Sprint_to_Jog")
```

**원래 매트릭스 처방의 4번째 패턴 `(Contains("Transition_") AND IsLockOn)` 는 부작용으로 제거됨**:
- PSD_GroundMovingTransit 에 `Transition_Run_to_Sprint_*`, `Transition_Sprint_to_Run_*`, `Transition_Jog_to_Run_*` 등 일반 speed transition 다수 존재
- 락온 sprint 중 이들 클립이 거의 항상 재생됨 → 4번째 패턴이 `true` 유지 → bIsPlayingTransitionBack=true 상시 활성 → UpdateTargetRotation Strafe 분기 TargetRotationDelta=0 항시 → mesh rotation stuck → trajectory forward straight → MM이 F 클립만 매칭
- 사용자 호소 (2026-05-15): "bIsPlayingTransitionBack 이게 적용되는 순간부터 락온 스프린트 방향이 F로만 되는 것 같아"
- 교훈: 매트릭스 처방의 4번째는 **PSD 실측 콘텐츠를 보지 않은 오버디자인**. Inspector(PSD/PSS dump) 우선 → 처방 설계가 옳은 순서.

## 구현 (2026-05-15)

### Phase 1: 변수
- `bIsPlayingTransitionBack` (bool, Buffer 카테고리, default=false, IE=false, BPRO=false)

### Phase 2: UpdateVariables 노드 (4패턴 → 3패턴 축소 후 잔존)
- `K2Node_VariableGet_9` — Get CurrentSequenceName
- `K2Node_CallFunction_7/11/28` — Contains × 3 (Sprint_to_Battle, Sprint_to_LockOn, Sprint_to_Jog)
- `K2Node_CallFunction_34/35` — BooleanOR × 2 (trickle: OR1=Battle|LockOn, OR2=OR1|Jog)
- `K2Node_VariableSet_69` — Set bIsPlayingTransitionBack (input = OR2.ReturnValue)

**제거된 노드 (4번째 패턴 부작용으로 2026-05-15 narrow)**:
- `K2Node_VariableGet_51` (Get IsLockOn)
- `K2Node_CallFunction_32` (Contains "Transition_")
- `K2Node_CallFunction_33` (BooleanAND)
- `K2Node_CallFunction_36` (BooleanOR 최종)

**Exec chain 삽입**: ExecutionSequence_3.then_12 → Knot_1 leg 사이에 Set_69 insert.
- before: ExecutionSequence_3.then_12 → K2Node_Knot_1.InputPin
- after:  ExecutionSequence_3.then_12 → Set_69.execute → Set_69.then → Knot_1.InputPin

### Phase 3: UpdateTargetRotation Strafe 게이트 (3노드 + 재배선)
- `K2Node_CallFunction_7` — SelectFloat
- `K2Node_VariableGet_3` — Get bIsPlayingTransitionBack
- `K2Node_CallFunction_8` — Not_PreBool

**재배선**:
- 기존: K2Node_CallFunction_4 (NormalizeAxis).ReturnValue → K2Node_VariableSet_3.TargetRotationDelta
- 신규: NormalizeAxis → SelectFloat.A, literal 0.0 → SelectFloat.B, Get → NOT → SelectFloat.bPickA, SelectFloat → Set_3.TargetRotationDelta

**동작**:
| bIsPlayingTransitionBack | NOT | bPickA | 선택 | TargetRotationDelta |
|---|---|---|---|---|
| false (정상) | true | true | A | NormalizeAxis 결과 |
| true (transition 재생 중) | false | false | B | **0.0 (회전 보정 차단)** |

## 검증 결과

- **compile_blueprint**: success=True, status=UpToDate, errors=0, warnings=0
- **validate_blueprint**: 새 에러 0 (disconnected_nodes 18건은 모두 기존 잡음 — SprintEndTransition 변수, DrawDebug Print String, OnStateEntry_Falling/Fall 의 Set TargetRotationAtBeginState 등 5/14 이전부터 있던 것)
- **save_asset**: 실패 — SB2 P4 잠금. 사용자 측 Ctrl+S 또는 P4 체크아웃 후 저장 필요

## 스크립트

- `scripts/extend_transition_back_gate.py` — Phase 1+2+3+4 통합 (재실행 시 변수 충돌 주의, idempotent 아님)
- `scripts/extend_transition_back_gate_continue.py` — exec wiring + Phase 3 + compile/save 분리 실행본 (then_13 부재로 then_12 insert 패턴 사용)
- `scripts/narrow_transition_back_gate_3pattern.py` — 4번째 패턴 제거 + OR2 → Set 재배선. compile clean, save success (P4 잠금 풀린 시점)

**v0.12.1 스키마 변경 주의**:
- `add_variable`: `variable_name`→`name`, `variable_type`→`type`
- `disconnect_pins`: `source_node`/`source_pin`→`node_id`/`pin_name`
- `add_node` / `connect_pins`: 5/13 시점 그대로 사용 가능

## 백업

- pre: `scripts/backup/UpdateVariables_pre_phase1_extension_20260515.json`, `UpdateTargetRotation_pre_phase1_extension_20260515.json`
- post: `scripts/backup/UpdateVariables_post_phase1_extension_20260515.json`, `UpdateTargetRotation_post_phase1_extension_20260515.json`

## PIE 검증 시나리오

| 케이스 | 기대 동작 | 추적 필드 |
|--------|----------|----------|
| 락온 + 반대방향 Sprint→Battle (B_Lfoot) | `bIsPlayingTransitionBack=true` 유지, 회전 튐 차단 | clip, trd, il |
| LockOn ON 중 Sprint→Battle (다른 발 시작) | 새로 `true` 잡힘 | clip, trd |
| LockOff Sprint→Jog 종료 | 새로 `true` 잡힘 | clip, trd |
| LockOn 중 임의 Transition_* 클립 | 새로 `true` 잡힘 | clip, il |
| 일반 strafe (transition 미재생) | `false` → 기존 회전 보정 동작 보존 | trd |

## 관련

- 매트릭스 처방: `Briefing/2026-05-14_motion-noise-diagnosis-prescription.md` ① 항목
- 복구 마스터플랜의 TRACK-B C 그룹: [[recovery-master-plan-track-b]] (메모리 미생성)
- 5/13 원본 1패턴: [[pc-01-sprint-battle-b-lfoot-abp]] (project_pc01_sprint_to_battle_transition_fix.md — 이 메모리는 회귀로 노드 ID 다 stale, 본 메모리가 최신 상태)
- ABP 체인 구조: [[pc01-abp-chain]]
- Sprint 종료 transition 검출 (5/14): [[pc01-sprint-end-transition]]
