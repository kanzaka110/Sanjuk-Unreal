# 2026-05-14 — Motion Matching 노이즈 진단·처방 패키지

## 컨텍스트

PC_01 ABP에서 **Stance flicker (C)** + **Transition motion interjection (D)** 가 가장 거슬리는 노이즈로 식별됨.
C가 D를 유발하는 경우가 많음 — Stance enum이 flicker하는 동안 Motion Matching이 어울리지 않는 transition 클립을 골라서 끼어드는 패턴. 같이 잡으면 시너지.

이번주 작업 (5/11~5/14)으로 `[ANIM_REC]` 71필드 진단 기반이 마련됨. Sprint Start chain / AnimStance buffer 같은 처방 패턴도 이미 정착. 이제 그 도구로 어디를 만질지 결정하는 단계.

---

## Motion Matching 노이즈 4가지 형태 + 추적 필드

| # | 형태 | 증상 | [ANIM_REC] 추적 필드 |
|---|------|------|---------------------|
| A | **Pose flicker** | 같은 입력인데 클립이 매 프레임 바뀜, 어깨/발 떨림 | `clip`, `seq`, `sc` (SearchCost), `sswseq`, `vac` |
| B | **Direction overshoot** | 작은 입력 대비 큰 회전, 휙 돌고 다시 옴 | `trd` (TargetRotationDelta), `tta` (TrjTurnAngle), `sdpt` (SustainedDirPivotTrigger), `sdt` (SustainedDirTime) |
| **C** | **Stance flicker** | AnimStance/MovementState enum 핑퐁 | `as`, `pwm`, `ms`, `ib` |
| **D** | **Transition motion interjection** | turn 등이 비의도적으로 끼어듦 | `clip`, `trd`, `il`, `tta` |

---

## 진단 워크플로우 (PIE에서 수집)

### 3시나리오 × 5회 재현

| 시나리오 | 재현 방법 | 추적 포인트 |
|---------|----------|------------|
| **C1. Sprint→Battle Idle** | LockOn OFF, Sprint 중 멈춤 | `as`, `pwm`, `ms`, `ib` 정착 타이밍 |
| **C2. Sprint→LockOn 중 Battle** | Sprint 중 LockOn ON → 멈춤 | `il`, `as`, `ib` 동시 변화 패턴 |
| **D1. LockOn 반대방향 Sprint→Battle** | LockOn ON, 타겟 반대로 Sprint → 멈춤 | `clip`, `trd`, `tta`, `as` (turn 끼어드는 순간) |

각 케이스 **직전 0.5초 + 직후 2초 = 150프레임** 슬라이스가 적정.

### 핵심 질문 4가지

```
Q1. C+D 케이스에서 가장 먼저 튀는 enum은 어떤 거?
    (as가 먼저? ib가 먼저? pwm가 먼저?)
Q2. 그 enum이 몇 프레임 동안 unstable?
    (2~3프레임이면 buffer로 잡힘, 10+ 프레임이면 더 근본 처방 필요)
Q3. unstable 윈도우 동안 clip이 몇 번 바뀌었나?
    (= Motion Matching이 얼마나 흔들렸나)
Q4. trd와 tta는 어떻게 변하나?
    (수렴 / 발산 / 진동 패턴)
```

### 데이터 위치

- 로그 소스: `E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2_2.log` (PIE 중 `[ANIM_REC]` prefix 라인)
- 슬라이스 저장: `Sanjuk-Unreal/UE_bot/data/abp_recordings/noise_diag_<scenario>.jsonl` (git untracked)
- 또는 발췌해서 채팅에 붙여넣기 (150줄 × 3 = 450줄 정도, 충분히 처리 가능)

---

## 처방 패키지 4단 (ROI 순서)

### ① Transition 게이트 클립 매칭 확장 ──── 가장 빠른 효과, 비용 작음

**현재 상태:** `bIsPlayingTransitionBack` 은 `P_Player_Transition_Sprint_to_Battle_Jog_B_Lfoot` 한 클립만 매칭

**확장안:**
```
bIsPlayingAnyStanceTransition =
    Contains(CurrentSequenceName, "Sprint_to_Battle") OR
    Contains(CurrentSequenceName, "Sprint_to_LockOn") OR
    Contains(CurrentSequenceName, "Sprint_to_Jog") OR
    (Contains(CurrentSequenceName, "Transition_") AND IsLockOn)
```

→ `UpdateTargetRotation` strafe 분기에 같은 게이트 적용 (`TargetRotationDelta = 0`). D 직접 차단.

**관련 파일:** `scripts/add_transition_back_gate.py` (5/13 작업, Phase 2: UpdateVariables에서 매칭 부분 수정)

### ② Sprint Start/End 윈도우 활용 ──── 이번주 마련됨, 와이어만

이미 `bIsSprintStartTransition` / `bIsSprintEndTransition` 변수 존재 (5/14 작업).
**둘 중 하나라도 true인 동안 회전 보정 0** 만 와이어하면 됨.

→ Sprint 진입·종료 N프레임 동안 turn 일체 차단. D + C 윈도우 진동도 함께 잡힘.

**관련 파일:** `scripts/build_sprint_start_chain.py`, `scripts/wire_sprint_start_chain.py`
**구현 패턴:** `add_transition_back_gate.py` Phase 3의 SelectFloat 게이트와 동일, 입력만 `bIsSprintStartTransition OR bIsSprintEndTransition` 으로 교체

### ③ Multi-Stance Buffer ──── C 직접 처방, 비용 중간

**현재 상태:** `UpdateAnimStanceWithBuffer` 가 AnimStance enum 에만 적용

**확장:** 같은 패턴을 다른 enum 으로 미러링
```
UpdateIsBattleWithBuffer       (버퍼 30~50ms)
UpdateIsLockOnWithBuffer       (버퍼 50~80ms — 토글 자체가 의도적 액션이므로 짧게)
UpdateMovementStateWithBuffer  (버퍼 20ms)
```

→ 같이 튀는 enum 들이 가지런히 정착될 때까지 대기 → Motion Matching 입력 자체가 안정화 → A 까지 부수 효과.

**비용:** 새 함수 그래프 3개 + 새 변수 9개 (each: Current, Candidate, AccumulatedTime). 5/13 작업의 응용이라 패턴 재사용 가능.
**관련 파일:** `scripts/build_animstance_buffer.py`, `scripts/wire_animstance_buffer.py` (이걸 복제·수정)

### ④ Sustained Trigger 패턴 확장 ──── D 정밀 처방

`sdpt` / `sdt` / `csh` 패턴 응용:

```
bSustainedTurnRequest = (|tta| > 90 AND IsLockOn) AND duration > 0.2s
```

→ 큰 turn 요청이 0.2초 유지돼야만 turn 모션 진입 허용. 짧은 입력 노이즈는 무시.

**관련 파일:** 신규 작업 필요. `sdpt` 변수 생성 시 패턴 참조 (`[ANIM_REC]` 의 `sdpt` 추적 필드 원본)

---

## 즉시 액션 우선순위

진단 데이터 없으면 ①+② 먼저 적용해보고 효과 측정 → 부족하면 ③/④:

1. **데이터 수집** — PIE 에서 C1/C2/D1 시나리오 × 5회 재현, `[ANIM_REC]` 로그 슬라이스
2. **① 적용** — `add_transition_back_gate.py` 의 Phase 2 매칭 부분만 부분일치(Contains) 로 확장
3. **② 적용** — Sprint Start/End 윈도우 게이트 와이어 (`UpdateTargetRotation` strafe 분기)
4. **효과 측정** — 같은 시나리오 재녹화, before/after 비교
5. **부족하면 ③** — Multi-Stance Buffer 1개씩 추가 (`IsBattle` → `IsLockOn` → `MovementState`)
6. **그래도 D 잔존하면 ④** — Sustained Turn Request 추가

근거 없이 ③/④ 부터 가면 비용 큰 작업이라 후회할 수 있음. ①+② 먼저.

---

## 관련 파일 인덱스 (이번주 작업 기준)

### 진단 도구 (재사용)
- `scripts/anim_rec_viewer.py` — `[ANIM_REC]` tail viewer (rich)
- `scripts/analyze_animrec.py` — emit 노드 검사
- `scripts/analyze_pivot_log.py` — pivot 분석
- `scripts/analyze_isstarting_log.py` / `_context.py` — bIsStarting 추적

### 처방 패턴 참조
- `scripts/add_transition_back_gate.py` — 게이트 패턴 (① 확장 베이스)
- `scripts/build_animstance_buffer.py` / `wire_animstance_buffer.py` — 버퍼 패턴 (③ 복제 베이스)
- `scripts/build_sprint_start_chain.py` / `wire_sprint_start_chain.py` — Sprint Start chain (② 활용)
- `scripts/phase3_gate.py` — SelectFloat 게이트 패턴

### 백업 (롤백 가능)
- `scripts/backup/UpdateVariables_post_20260514.json` — 가장 최신 ABP 상태 스냅샷
- `scripts/backup/UpdateVariables_post_sprint_start_20260514.json` — Sprint Start chain 적용 후

---

## 환경 제약

- **GCP 세션:** SB2 로그 / Monolith (localhost:9316) 직접 접근 불가. 로그 발췌 받아서 분석만 가능
- **로컬 PC 세션:** Monolith 호출 + Editor Python + 로그 접근 다 가능. 실제 처방 적용은 여기서
