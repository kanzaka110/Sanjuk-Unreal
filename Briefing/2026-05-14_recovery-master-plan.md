# 2026-05-14 — PC_01 ABP 복구 마스터 플랜 (2-Track 분리)

## 복구 전략

사용자 요청에 따라 **두 트랙으로 명확히 분리**해서 진행. 각 트랙은 독립적으로 실행 가능. 공통 사전 작업(변수 추가)만 한 번 수행하면 두 트랙 어느 쪽이든 먼저 시작 가능.

| 트랙 | 범위 | 백업 보유 | 작업량 |
|------|------|----------|--------|
| **TRACK-A: Rewind Recorder** | `AnimRewindRecorderEmit` 그래프 (66필드 FT_2 + 65 wire) | ❌ 그래프 백업 없음 | 스크립트 재구축 (어제 만든 가이드) |
| **TRACK-B: Rest of ABP** | `UpdateVariables` 그래프 + `UpdateTargetRotation` 게이트 + 변수 130개 + Sprint Start chain 변수 | ✅ UpdateVariables JSON 5/14 최종 100% | JSON → 노드 변환 스크립트 |

> **분리 원칙:** 두 그래프(`AnimRewindRecorderEmit`, `UpdateVariables`)는 독립적이지만 같은 ABP 변수를 공유. 변수만 미리 모두 있으면 어느 트랙부터 해도 됨.

---

## 0단계: 사전 진단 (둘 다 공통)

복구 들어가기 전에 어디까지 살아있는지 확인. SB2 Saved/Autosaves/ 또는 P4 sync로 통째로 복원되면 이후 단계 다 skip 가능.

### 0.1 최우선: SB2 자동 백업/P4 확인

```
1. SB2 프로젝트의 Saved/Autosaves/ 폴더에서 5/14 17:00 무렵 .uasset 확인
2. 있으면 ABP만 그 파일로 덮어쓰기 → 5초 끝
3. 없으면 P4 sync로 5/14 푸시 직전 리비전으로 sync 시도
4. 둘 다 안 되면 → TRACK-A/B 진행
```

### 0.2 현재 ABP 상태 진단 (Monolith)

```
py C:/Dev/Sanjuk-Unreal/scripts/dump_consolidated_graph.py   # AnimRewindRecorderEmit 그래프 dump
py C:/Dev/Sanjuk-Unreal/scripts/dump_new_ft_pins.py          # FT_2 66핀 검증
py C:/Dev/Sanjuk-Unreal/scripts/inspect_ft_routing.py        # downstream 검증
py C:/Dev/Sanjuk-Unreal/scripts/probe_abp_vars.ps1           # 변수 리스트 dump
```

진단 결과로 각 트랙 시작 시나리오 식별 (트랙별 의사결정 표 아래 참고).

---

## 공통 사전 작업: 변수 추가 (조건부)

진단에서 변수가 빠져있다고 나오면 먼저 추가.

### A. 기본 변수 130개 (Variables_pre_sprint_start_20260514.json)

이 백업에 들어있는 130개 변수 — 진단 결과 누락된 것만 add.

핵심 변수 그룹:
- **Essential Values:** `Speed2D`, `Velocity`, `Acceleration`, `IsLockOn`, `TargetRotationDelta`, ...
- **States:** `MovementState`, `MovementMode`, `PendingWalkMode`, `AnimStance`, `MoveSide`
- **Buffer:** `PendingWalkModeAccumulatedTime`, `CandidatePendingWalkMode`, `MovementModeAccumulatedTime`, `HoldTimeThreshold`, `bIsSprintEndTransition`, `SprintEndTransitionRemain`, `SprintEndTransitionDuration`
- **AnimRewind:** `bAnimRewindRecording`, `RewindMonitorLine`
- **StateMachine:** `StateMachineMoveState`, `NullAnim`, `ReTransitState`, `SearchCost`, `RunRetransit`, `RetransitReason`
- **디폴트(한글 카테고리):** `IsStrafe`, `TrjTurnAngle`, `TrjIsCircling`, `CircleStrafeHysteresis`, `bIsStart`, `IsBattle`, `IsGuarding`, `FootClampAlpha`
- **Wriggle:** `bIsWriggling`, `WriggleStart`, `WriggleEnd`, `InWriggle`, `WriggleMoveType`, ...

### B. Sprint Start chain 변수 6개 (백업엔 없음, 5/14 신규)

```
bCurrentPendingSprinting       (bool)
bJustEnteredSprint             (bool)
SprintStartTransitionRemain    (double)
SprintStartTransitionDuration  (double, default 0.3)
bIsSprintStartTransition       (bool)
bPrevPendingSprinting          (bool)
```

### C. Phase 3 게이트 변수 (5/13)
```
bIsPlayingTransitionBack       (bool)
```

> **자동화:** `scripts/restore_abp_variables.py` (작성 예정) 가 위 3 그룹을 한 번에 add. 또는 수동으로 Monolith `add_variable` 호출.

---

## TRACK-A: AnimRewindRecorder 재구현 (66필드)

### 의존성
- ABP 변수 모두 존재 (특히 `RewindMonitorLine`, `bAnimRewindRecording`, 그리고 65 wire가 가리키는 모든 변수)
- `K2Node_CallFunction_4` (InText 받는 다운스트림 노드) 존재 — 이건 보통 ABP의 UE_LOG 호출 또는 PrintString 같은 외부 호출
- `K2Node_VariableSet_1` (RewindMonitorLine 다운스트림) 존재

### 단계 (어제 만든 가이드 그대로)

| 단계 | 스크립트 | 역할 |
|------|---------|------|
| A1 | `consolidate_ft_chain_step1.py` | 새 `K2Node_FormatText_2` (66 input pin) 생성 |
| A2 | `consolidate_ft_chain_step2.py` | 65 wire 연결 + vac default `"-1"` |
| A3 | (인라인 compile) | compile_blueprint 검증 |
| A4 | `consolidate_ft_chain_step4.py` | downstream 스왑 (clean state에서는 connect 2개만) |
| A5 | (인라인 verify) | `inspect_ft_routing.py` |
| A6 | `consolidate_ft_chain_step6.py` | 옛 FT 8개 삭제 (clean state면 skip) |

### TRACK-A 의사결정 표

| 진단 결과 | 시나리오 | 실행 |
|-----------|---------|------|
| 모두 정상 | F | skip |
| FT_2 없음 + 옛 FT chain 살아있음 | B1 | A1→A2→A3→A4→A5→A6 |
| FT_2 없음 + clean state | B2 | A1→A2→A3→A4(connect만)→A5 |
| FT_2 있음, 핀 < 66 | 이상 | FT_2 삭제 후 B2 |
| FT_2 있음, wire < 65 | C | A2 (실패 wire만 재연결 — idempotent 스크립트 필요) |
| FT_2 있음, downstream X | D | A4 |
| 옛 FT 잔존 | E | A6 |
| 그래프 자체 없음 | A | 변수 + 65 source 노드부터 — 큰 작업 |

> **상세 참조:** `Briefing/2026-05-14_rewind-recorder-final-implementation.md`

### TRACK-A 마스터 명령 (가장 흔한 B2 시나리오)

```bash
py C:/Dev/Sanjuk-Unreal/scripts/consolidate_ft_chain_step1.py
py C:/Dev/Sanjuk-Unreal/scripts/consolidate_ft_chain_step2.py
py C:/Dev/Sanjuk-Unreal/scripts/consolidate_ft_chain_step4.py
py C:/Dev/Sanjuk-Unreal/scripts/inspect_ft_routing.py
```

소요: 약 5분.

---

## TRACK-B: Rest of ABP (UpdateVariables + Sprint Start + Phase 3 게이트)

### 의존성
- ABP 자체 존재
- 변수 130개 + Sprint Start 6개 + `bIsPlayingTransitionBack` 모두 존재
- `UpdateVariables` 그래프 존재 (비어있어도 됨)
- `UpdateTargetRotation` 그래프 존재 (Phase 3 게이트용)

### 백업 데이터
- **`scripts/backup/UpdateVariables_post_sprint_start_20260514.json`** (203KB, 353 노드)
- 구조: `{graph_name, graph_type, nodes:[{id, class, title, pos, pins:[{id, name, direction, type, connected_to|default_value}]}]}`
- 노드 클래스 분포: VariableGet 80, VariableSet 79, CallFunction 44, Comment 36, Knot 29, PromotableOperator 23, PropertyAccess 20, CommutativeAssociativeBinaryOperator 18, IfThenElse 8, EnumEquality 5, ExecutionSequence, FunctionEntry, ...

### 단계

| 단계 | 작업 | 비고 |
|------|------|------|
| B0 | 변수 추가 (사전 작업 A+B+C) | `restore_abp_variables.py` (작성 예정) |
| B1 | UpdateVariables 그래프 초기화 또는 비교 | 기존 노드 다 삭제하거나 빈 상태 보장 |
| B2 | **JSON → 노드 재생성** | `restore_update_variables.py` (작성 예정) — JSON 파싱 후 add_node × 353 + connect_pins × 수백 |
| B3 | UpdateTargetRotation Phase 3 게이트 | `phase3_gate.py` 또는 `add_transition_back_gate.py` Phase 3 |
| B4 | compile + save | `compile_blueprint` + `save_asset` |

### TRACK-B 의사결정 표

| 진단 결과 | 시나리오 | 실행 |
|-----------|---------|------|
| UpdateVariables 그래프 정상 (353 노드) | F | skip |
| UpdateVariables 노드 < 100 | 큰 손상 | B0 → B1 → B2 → B3 → B4 |
| UpdateVariables 노드 200~350 | 부분 손상 | diff 비교 후 누락 노드만 추가 — 별도 스크립트 |
| UpdateTargetRotation Phase 3 게이트 누락 | gate 없음 | B3만 |
| 변수만 누락 | vars only | B0만 |

### TRACK-B 마스터 명령 (전체 복구)

```bash
py C:/Dev/Sanjuk-Unreal/scripts/restore_abp_variables.py
py C:/Dev/Sanjuk-Unreal/scripts/restore_update_variables.py
py C:/Dev/Sanjuk-Unreal/scripts/phase3_gate.py
# compile + save는 위 스크립트들이 마지막에 자동 호출
```

소요: 약 30~60분 (353 노드 시퀀스 add). 

### ⚠️ 아직 작성 안 된 스크립트

- `scripts/restore_abp_variables.py` — 변수 130 + 6 + 1 일괄 add
- `scripts/restore_update_variables.py` — backup JSON → 노드 재생성

**이 두 스크립트는 작성 필요.** 내일 복구 요청 시 빠르게 진행하려면 미리 만들어둬야 함.

---

## 실행 우선순위 권장

### 시나리오 1: 전체가 다 날아간 경우
```
0. SB2 Autosaves/P4 확인 (실패 시 ↓)
1. 공통 사전 작업: 변수 추가 (restore_abp_variables.py)
2. TRACK-B: UpdateVariables 그래프 복원 (restore_update_variables.py)
3. TRACK-B: Phase 3 게이트 (phase3_gate.py)
4. TRACK-A: AnimRewindRecorder 재구축 (step1→2→4)
5. compile + save + PIE 검증
```
이유: 변수가 양쪽 다 필요하므로 0번 먼저. 그 다음 B → A 순서가 안전 (B의 변수들이 다 정의돼야 A의 wire가 깔끔).

### 시나리오 2: AnimRewindRecorder만 손상
→ TRACK-A만

### 시나리오 3: UpdateVariables만 손상
→ TRACK-B만

---

## 두 트랙의 명확한 경계

```
TRACK-A 영역:
  /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP::AnimRewindRecorderEmit
    └─ K2Node_FormatText_2 + 65 source nodes + downstream

TRACK-B 영역:
  /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP::UpdateVariables
    └─ 353 노드 전체
  /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP::UpdateTargetRotation
    └─ Phase 3 게이트 (SelectFloat + NOT + bIsPlayingTransitionBack)
  PC_01_ABP 변수 137개 (130 + 6 + 1)

공통 영역 (양쪽 의존):
  PC_01_ABP 변수들 — 양쪽 그래프에서 reference
```

---

## 내일 사용자 트리거별 자동 흐름

| 사용자 트리거 | 자동 진행 |
|--------------|----------|
| "리와인드 로그 복구" / "TRACK-A" | 진단 → TRACK-A 의사결정 표 → 마스터 명령 |
| "나머지 복구" / "TRACK-B" | 진단 → TRACK-B 의사결정 표 → 마스터 명령 |
| "전체 복구" | 시나리오 1 권장 순서 |
| "복구 전 진단" | 0.1 SB2 Autosaves 확인 안내 + 0.2 진단 스크립트 4종 |

---

## 환경 제약

- **Monolith API**는 로컬 PC `localhost:9316` 에서만 접근 가능
- GCP 세션에서는 가이드 검토 + 스크립트 작성/리뷰만 가능
- 실제 ABP 재구축은 로컬 PC + UE Editor 실행 + Monolith 동작 상태에서만
