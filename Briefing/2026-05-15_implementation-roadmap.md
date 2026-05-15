# 2026-05-15 — PC_01 ABP 구현 로드맵 (전체 정리)

## 최종 목표

**LockOn 상태에서 락온된 캐릭터 반대방향으로 Sprint → Jog 전환 시 회전이 1틱 180도 점프하는 현상을 부드러운 보간으로 해결**, 그리고 일반적인 Motion Matching 노이즈 (Stance flicker + Transition interjection)를 도구화·일반화된 처방으로 잡기.

### 성공 지표

1. LockOn 반대방향 Sprint→Jog 시 회전 점프가 사라지고 부드럽게 따라감 (`[ANIM_REC]` `trd` 필드가 1프레임에 180도 점프 ❌)
2. Stance flicker (`as`, `ib`, `pwm` enum 핑퐁) 감지율 ↓
3. Pivot ↔ Transition 처리 로직이 코드상 명확히 분리되어 유지보수 쉬워짐
4. 진단 → 처방 → 효과 측정의 사이클이 도구화됨 ([ANIM_REC] 71필드)

---

## 시작점 (자산 현황)

| 자산 | 상태 | 위치 |
|------|------|------|
| UpdateVariables 그래프 (5/14 최종) | ✅ JSON 100% 보존 | `scripts/backup/UpdateVariables_post_sprint_start_20260514.json` |
| 변수 130개 백업 (5/14 pre_sprint_start) | ✅ JSON 보존 | `scripts/backup/Variables_pre_sprint_start_20260514.json` |
| AnimRewindRecorder 66필드 정의 | ✅ 스크립트 보존 | `scripts/consolidate_ft_chain_step1~6.py` |
| Transition 함수화 설계 | ✅ 완료 | `Briefing/2026-05-15_transition-function-design.md` |
| 모션 노이즈 4단 처방 | ✅ 완료 | `Briefing/2026-05-14_motion-noise-diagnosis-prescription.md` |
| 복구 마스터 플랜 (2-Track) | ✅ 완료 | `Briefing/2026-05-14_recovery-master-plan.md` |
| restore 스크립트 2개 | ✅ 작성됨 | `scripts/restore_abp_variables.py`, `scripts/restore_update_variables.py` |
| 진단 스크립트 4종 | ✅ 작성됨 | `scripts/dump_*.py`, `scripts/inspect_*.py` |
| SB2 ABP 자체 분석 | ✅ 캐시 보존 | `cache/sb2/sb2_abp_structure.md`, `sb2_motion_matching.md` |
| GASP USmoothWalkingMode 레퍼런스 | ✅ 검증 | 설계 문서 내 |
| Recorder 그래프 백업 | ❌ 없음 | 스크립트 재구축 필요 |
| State Machine/Chooser 백업 | ❌ 없음 | SB2 Autosaves/P4 의존 |

---

## 의존성 그래프

```
Phase 0: 진단 (Day 1, 30분)
   ↓
Phase 1: 복구 (Day 1, 1~2시간)
   │   ├─ TRACK-A: Recorder 재구축
   │   └─ TRACK-B: UpdateVariables + Phase 3 + 변수
   ↓
Phase 2: 진단 데이터 수집 (Day 1-2, 1시간)
   │   C1/C2/D1 시나리오 × 5회 → [ANIM_REC] 로그 슬라이스
   ↓
Phase 3: 빠른 처방 (Day 2, 2~3시간) ── 즉각 효과
   │   ① Transition 게이트 클립 매칭 확장
   │   ② Sprint Start/End 윈도우 회전 차단 와이어
   │   효과 측정 → 부족하면 Phase 4 진행
   ↓
Phase 4: Transition 함수화 (Day 3-5, 2~3일) ── 본격 리팩토링
   │   A. enum/struct/변수 추가
   │   B. GetTransitionState 함수 그래프
   │   C. UpdateTargetRotation RInterpTo 통합
   │   D. Chooser N_LockOn_Moveing 컬럼 추가
   │   E. Sprint Start/End 변수 마이그레이션
   │   F. [ANIM_REC] 5필드 확장 (tsk/tsp/tsa/tsr/ris)
   ↓
Phase 5: 검증 / 확장 (Day 6-7)
   │   회귀 테스트, 부족하면 ③ Multi-Stance Buffer / ④ Sustained Turn
   ↓
Phase 6: GASP 비교 검증 (선택, Day 7+)
       USmoothWalkingMode 파라미터 dump → 튜닝 기준값 비교
```

---

## Phase 0 — 진단 (Day 1, 30분)

### Step 0.1 — SB2 Autosaves/P4 확인 (최우선, 가장 빠른 길)

```
SB2 프로젝트 → Saved/Autosaves/ 폴더 확인
  → 5/14 17:00 무렵 .uasset 있으면 그대로 복사 → 1분 완료, Phase 1 skip
  → 없으면 P4 sync로 5/14 푸시 직전 리비전 시도
  → 둘 다 안 되면 Phase 1 진행
```

### Step 0.2 — Monolith 진단 (4종 한 번에)

```
py C:/Dev/Sanjuk-Unreal/scripts/dump_consolidated_graph.py   # AnimRewindRecorderEmit
py C:/Dev/Sanjuk-Unreal/scripts/dump_new_ft_pins.py          # FT_2 66핀 검증
py C:/Dev/Sanjuk-Unreal/scripts/inspect_ft_routing.py        # downstream 검증
py C:/Dev/Sanjuk-Unreal/scripts/probe_abp_vars.ps1           # 변수 리스트
```

### 의사결정 분기

| 결과 | 다음 단계 |
|------|----------|
| ABP 완전 정상 | Phase 2로 직행 |
| Recorder만 손상 | Phase 1 → TRACK-A만 |
| UpdateVariables만 손상 | Phase 1 → TRACK-B만 |
| 둘 다 손상 | Phase 1 전체 (TRACK-B → TRACK-A 순서) |
| 변수 누락 | restore_abp_variables.py 먼저 |

---

## Phase 1 — 복구 (Day 1, 1~2시간)

> 상세는 `Briefing/2026-05-14_recovery-master-plan.md`

### 1.1 변수 추가 (공통 사전 작업)

```
py C:/Dev/Sanjuk-Unreal/scripts/restore_abp_variables.py --dry-run
py C:/Dev/Sanjuk-Unreal/scripts/restore_abp_variables.py
```
→ 130 + 6 + 1 = 137개 변수 add (idempotent, 이미 있는 건 skip)

### 1.2 TRACK-B — UpdateVariables 복원 + Phase 3 게이트

```
py C:/Dev/Sanjuk-Unreal/scripts/restore_update_variables.py --dry-run
py C:/Dev/Sanjuk-Unreal/scripts/restore_update_variables.py
py C:/Dev/Sanjuk-Unreal/scripts/phase3_gate.py
```
→ 353 노드 재생성 + 와이어 + Phase 3 게이트.  
⚠️ PropertyAccess 20개 + AnimNodeReference 는 placeholder만 — 스크립트 끝 로그의 "MANUAL BINDING NEEDED" 리스트 따라 수동 binding.

### 1.3 TRACK-A — AnimRewindRecorderEmit 재구축

```
py C:/Dev/Sanjuk-Unreal/scripts/consolidate_ft_chain_step1.py
py C:/Dev/Sanjuk-Unreal/scripts/consolidate_ft_chain_step2.py
py C:/Dev/Sanjuk-Unreal/scripts/consolidate_ft_chain_step4.py
py C:/Dev/Sanjuk-Unreal/scripts/inspect_ft_routing.py
```
→ FT_2 (66 input pin) + 65 wire + downstream 2개.

### 1.4 컴파일 + 저장 + PIE 확인

```
compile_blueprint → error_count = 0 확인
save_asset
PIE 실행 → [ANIM_REC] 로그 흐르는지 SB2_2.log 확인
py scripts/anim_rec_viewer.py  → 23필드 표시 (66필드 보려면 FIELD_LABELS 확장 필요)
```

---

## Phase 2 — 진단 데이터 수집 (Day 1-2, 1시간)

> 상세는 `Briefing/2026-05-14_motion-noise-diagnosis-prescription.md`

### 시나리오 × 5회 재현

| 시나리오 | 재현 |
|---------|------|
| **C1** | LockOn OFF, Sprint → 멈춤 → Battle Idle |
| **C2** | Sprint 중 LockOn ON → 멈춤 → Battle |
| **D1** | LockOn ON, 타겟 반대로 Sprint → 멈춤 (핵심) |

각 케이스 직전 0.5초 + 직후 2초 = **150프레임 슬라이스** SB2_2.log에서 추출.

### 분석 — Q1~Q4 답 도출

```
Q1. C+D 케이스에서 가장 먼저 튀는 enum은?
    (as가 먼저? ib가 먼저? pwm가 먼저?)
Q2. unstable 윈도우 길이? (프레임 수)
Q3. unstable 동안 clip이 몇 번 바뀜?
Q4. trd와 tta의 변화 패턴? (수렴/발산/진동)
```

→ 답 기반으로 Phase 3 우선순위 확정 (① 게이트 확장 vs ② Sprint 윈도우 vs 둘 다)

---

## Phase 3 — 빠른 처방 (Day 2, 2~3시간) ── 즉각 효과

### 3.1 ① Transition 게이트 클립 매칭 확장

**작업:** `add_transition_back_gate.py` 의 Phase 2 매칭 부분만 부분일치로 확장.

```python
# 현재 (5/13)
if CurrentSequenceName == "P_Player_Transition_Sprint_to_Battle_Jog_B_Lfoot":
    bIsPlayingTransitionBack = True

# 변경 (확장)
if (Contains(CurrentSequenceName, "Sprint_to_Battle") OR
    Contains(CurrentSequenceName, "Sprint_to_LockOn") OR
    Contains(CurrentSequenceName, "Sprint_to_Jog") OR
    (Contains(CurrentSequenceName, "Transition_") AND IsLockOn)):
    bIsPlayingAnyStanceTransition = True
```

**구현:** 새 스크립트 `extend_transition_gate.py` 또는 기존 게이트의 EqualEqual_StrStr 노드를 Contains로 교체.

**검증:** D1 시나리오 재녹화 → `trd` 가 0으로 잠기는 윈도우 확인.

### 3.2 ② Sprint Start/End 윈도우 회전 차단 와이어

**작업:** 이미 있는 `bIsSprintStartTransition` / `bIsSprintEndTransition` 변수에 OR 게이트 + `UpdateTargetRotation` strafe 분기 `TargetRotationDelta = 0` 와이어 추가.

**구현:** `phase3_gate.py` 의 SelectFloat 패턴 복제 — 입력만 `(bIsSprintStartTransition OR bIsSprintEndTransition)` 으로.

**검증:** Sprint→Battle 진입·종료 윈도우 (0.3초) 동안 회전 잠기는지 [ANIM_REC] 확인.

### 3.3 효과 측정

```
같은 시나리오 (C1/C2/D1 × 5회) 재녹화
→ before/after [ANIM_REC] 슬라이스 비교
→ trd 점프 횟수, unstable 윈도우 길이 비교
```

**부족하면 Phase 4 진행. 충분하면 마무리.**

---

## Phase 4 — Transition 함수화 (Day 3-5, 2~3일) ── 본격 리팩토링

> 상세는 `Briefing/2026-05-15_transition-function-design.md`

### 4.A — 자료형 추가 (반나절)

```
ETransitionKind enum: None, SpeedBucket, LockOnToggle, Combined
ETransitionPhase enum: None, Starting, Mid, Ending
S_TransitionState struct: Kind, Phase, Elapsed, Remain, Duration, Alpha,
                          bShouldSmoothRot, Source/Target SpeedBucket·LockOn

ABP 변수 추가:
  TS (S_TransitionState)
  RotInterpSpeed_Low, RotInterpSpeed_High (instance_editable, 기본 3/15)
```

⚠️ Monolith API로 enum/struct 추가가 가능한지 첫 step에서 검증 (`add_enum`, `add_struct` 같은 액션). 안 되면 수동 생성 후 스크립트는 변수/노드만.

### 4.B — GetTransitionState 함수 그래프 빌드 (반나절~하루)

`UpdateVariables` 안 chain 또는 별도 함수 그래프 (`UpdateTransitionState`).  
의사코드 따라 노드 빌드 — 변화 감지 → 신규 트랜지션 초기화 → 진행 갱신 → Alpha/Phase 계산.

```
build_transition_state_chain.py — 신규 작성
```

### 4.C — UpdateTargetRotation RInterpTo 통합 (1시간)

```
RotInterpSpeed = SelectFloat(
    bPickA = TS.bShouldSmoothRot,
    A = Lerp(RotInterpSpeed_Low, RotInterpSpeed_High, TS.Alpha),
    B = RotInterpSpeed_High
)
→ RInterpTo.InterpSpeed 입력
```

기존 `bIsPlayingTransitionBack` 게이트는 보존 (특정 클립 한정 보강).

```
wire_rotinterp_modulation.py — 신규 작성
```

### 4.D — Chooser N_LockOn_Moveing 컬럼 추가 (반나절)

`/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving.GroundMoving:N_Battle_GroundMoving.N_LockOn_Moveing` 에 TransitionKind, TransitionPhase 컬럼 추가. 트랜지션 row 추가.

```
add_chooser_transition_columns.py — 신규 작성
```

### 4.E — Sprint Start/End 마이그레이션 (1~2시간)

`bIsSprintStartTransition` / `bIsSprintEndTransition` / `*Remain` 변수를 `TS` 기반 derived getter로 교체. 기존 references 전부 새 getter로.

```
migrate_sprint_transition_vars.py — 신규 작성
```

### 4.F — [ANIM_REC] 5필드 확장 (1시간)

`tsk`, `tsp`, `tsa`, `tsr`, `ris` 5개 필드를 FT_2의 FORMAT_STR에 추가. 66 → 71필드.  
`anim_rec_viewer.py` 의 FIELD_LABELS 도 같이 확장.

```
extend_ft2_transition_fields.py — 신규 작성
```

---

## Phase 5 — 검증 / 확장 (Day 6-7)

### 5.1 핵심 검증 — D1 시나리오

LockOn 반대방향 Sprint→Jog × 10회:
- `trd` 1프레임 180도 점프 사라짐 ✅
- `ris` (RotInterpSpeed) 가 Low → High 로 부드럽게 ramp up ✅
- `tsa` (TS.Alpha) 곡선 자연스러움 ✅

### 5.2 회귀 테스트

```
- 일반 이동 반응성 (Walk/Jog/Sprint 진입·종료) — 너무 둔하지 않은지
- Pivot (방향 변화) — Motion Matching 정상 동작
- 다른 트랜지션 (Battle Start/End, Jump Land) — 영향 없는지
```

### 5.3 부족하면 ③ ④ 처방 추가

| 잔존 문제 | 처방 |
|----------|------|
| Stance flicker (as/ib enum 핑퐁) 잔존 | ③ Multi-Stance Buffer (IsBattle/IsLockOn/MovementState 미러링) |
| 큰 각도 turn이 짧은 입력에도 트리거됨 | ④ Sustained Turn Request (`|tta| > 90 AND IsLockOn` 0.2초 유지) |

---

## Phase 6 — GASP 비교 검증 (선택, Day 7+)

```
1. C:\Users\SHIFTUP\Documents\Unreal Projects\GameAnimationSample 의 ABP dump
2. USmoothWalkingMode 노드 + 파라미터 확인:
   - velocity spring strength
   - rotation turn strength
3. 우리 RotInterpSpeed_Low/High 와 비교 → 튜닝 기준값 조정
4. (선택) Daniel Holden 블로그 정독 → spring damper 수학 이해
```

---

## 리스크 + 완화 방안

| 리스크 | 가능성 | 완화 |
|--------|-------|------|
| Monolith API 미지원 (enum/struct 추가) | 中 | 첫 step에서 검증 + 수동 fallback |
| restore_update_variables.py 첫 실행 실패 (PropertyAccess) | 中 | `--dry-run` 먼저 + 수동 binding 안내 따라 |
| 컴파일 에러 (와이어 누락 등) | 中 | 각 phase 사이 `compile_blueprint` 호출 + error_count 확인 |
| RotInterpSpeed 값 튜닝 어려움 | 高 | instance_editable로 노출, PIE에서 즉시 튜닝 |
| Chooser 컬럼 추가 후 기존 row 분기 깨짐 | 中 | 컬럼 추가 시 default `Any` (와일드카드) — 기존 row 영향 없음 |
| Phase 4 시간 초과 (예상 2~3일 → 1주) | 中 | Phase 3 ①+② 효과 측정 후 Phase 4 진행 여부 결정 |
| LockOn 토글 트랜지션 자체가 노이즈 원인 | 低 | Phase 2 진단 데이터로 확인 — 아니면 SpeedBucket만 처리 |

---

## 시간 추정

| 단계 | 최소 | 평균 | 최대 |
|------|------|------|------|
| Phase 0 | 15분 | 30분 | 1시간 |
| Phase 1 (둘 다 복구) | 1시간 | 2시간 | 4시간 (수동 binding 많을 시) |
| Phase 2 | 30분 | 1시간 | 2시간 |
| Phase 3 | 1시간 | 3시간 | 1일 |
| Phase 4 | 2일 | 3일 | 1주 |
| Phase 5 | 반나절 | 1일 | 2일 |
| Phase 6 (선택) | 2시간 | 반나절 | 1일 |

**누적**:
- 핵심 효과만 (Phase 0~3): **Day 2 마무리 가능**
- 본격 리팩토링 포함 (Phase 0~5): **1주일**
- GASP 비교 포함: **1주 + 2일**

---

## 일일 체크포인트

### Day 1 (수요일?)
- [ ] Phase 0 진단 완료 — SB2 Autosaves/P4 우선 확인
- [ ] Phase 1 복구 (TRACK-B 또는 TRACK-A 또는 둘 다)
- [ ] PIE 실행 → [ANIM_REC] 로그 흐름 확인
- [ ] Phase 2 시나리오 C1 데이터 수집

### Day 2
- [ ] Phase 2 시나리오 C2/D1 완료
- [ ] Q1~Q4 답 도출 → 우선순위 확정
- [ ] Phase 3 ①+② 적용
- [ ] 효과 측정 (before/after)

### Day 3
- [ ] Phase 4.A 자료형 추가
- [ ] Phase 4.B GetTransitionState 함수 그래프 빌드
- [ ] Monolith API enum/struct 지원 검증

### Day 4
- [ ] Phase 4.C RInterpTo 통합
- [ ] Phase 4.F [ANIM_REC] 5필드 확장 (조기 통합으로 후속 검증 용이)

### Day 5
- [ ] Phase 4.D Chooser 컬럼
- [ ] Phase 4.E Sprint Start/End 마이그레이션

### Day 6
- [ ] Phase 5.1 핵심 검증 (D1)
- [ ] Phase 5.2 회귀 테스트
- [ ] 부족하면 ③ ④ 추가

### Day 7
- [ ] Phase 6 GASP 비교 (선택)
- [ ] 최종 문서화 + 메모리 업데이트 + 코드리뷰

---

## 작성해야 할 신규 스크립트 (Phase 4 진행 시)

| 스크립트 | Phase | 역할 |
|---------|-------|------|
| `extend_transition_gate.py` | 3.1 | 게이트 매칭 Contains 패턴으로 확장 |
| `wire_sprint_window_rotation_gate.py` | 3.2 | Sprint Start/End OR 게이트 + 회전 차단 |
| `build_transition_state_chain.py` | 4.B | GetTransitionState 함수 그래프 빌드 |
| `wire_rotinterp_modulation.py` | 4.C | UpdateTargetRotation RInterpTo 통합 |
| `add_chooser_transition_columns.py` | 4.D | N_LockOn_Moveing 컬럼 추가 |
| `migrate_sprint_transition_vars.py` | 4.E | 변수 references 마이그레이션 |
| `extend_ft2_transition_fields.py` | 4.F | 66→71필드 + viewer FIELD_LABELS 확장 |

> 이 7개 스크립트는 GCP에서도 작성 가능 (Monolith 안 쓰는 한). 패턴은 기존 step1~6, phase3_gate, build_sprint_start_chain 참조.

---

## 환경별 작업 분리

| 작업 | GCP | 로컬 PC |
|------|-----|---------|
| 스크립트 작성 | ✅ | ✅ |
| 진단 로그 분석 | ✅ | ✅ |
| 설계 문서 작성 | ✅ | ✅ |
| Monolith API 호출 | ❌ | ✅ |
| ABP 그래프 수정 | ❌ | ✅ |
| PIE 검증 | ❌ | ✅ |
| GASP dump | ❌ | ✅ |

**최적 흐름:** Day 1 시작 = 로컬 PC. Day 3~5 중 GCP에서 스크립트 작성 병행 가능 (로컬 PC가 다른 작업 중일 때).

---

## 큰 그림 한 줄

> **이번주 만든 도구(66필드 Recorder + 백업) + 어제 정리한 처방(4단 + 2-Track) + 오늘 설계한 함수화(Transition State + RInterpTo 변조) = 7일 안에 핵심 노이즈 해결 + 일반화된 처방 시스템 완성**.

> Epic이 UE 5.7에서 `USmoothWalkingMode`로 채택한 방향을 SB2 기존 ABP에 점진 적용하는 것이라 위험은 낮고 효과는 검증됨.
