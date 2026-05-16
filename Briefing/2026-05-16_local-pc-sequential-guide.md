# 2026-05-16 — 로컬 PC 순차 작업 가이드 (Day 1 ~ Day 7+)

## 한 줄 요약

GCP에서 만든 모든 자료(복구 / 처방 / Transition 함수화 / MCP-First Architecture)를 로컬 PC에서 활용하는 시간순 가이드. **첫 명령은 `/pull` 한 줄.**

---

## 🌅 Day 1: 환경 준비 + 진단 + 인프라 검증 (3~4시간)

### Step 1.1 — 환경 동기화 (5분)
```
cd C:\dev\Sanjuk-Unreal
/pull
```
**확인:** 5/16 커밋 `7167364`까지 받아짐 (11개 신규 파일)

### Step 1.2 — Monolith + UE 에디터 가동 (5분)
```
1. UE Editor 실행 → SB2 프로젝트 열기 (E:\Perforce\SB2\Workspace\Internal\SB2\SB2.uproject)
2. Monolith 플러그인 활성화 확인
3. 별도 터미널에서: curl http://localhost:9316/health
   → 응답 있으면 OK
```

### Step 1.3 — ABP 상태 진단 (15분)
**최우선:** SB2 `Saved/Autosaves/` 에서 5/14 17:00 무렵 .uasset 확인 (있으면 Step 1.4 skip)

```
# UE Editor Python Console에서:
py C:/Dev/Sanjuk-Unreal/scripts/dump_consolidated_graph.py
py C:/Dev/Sanjuk-Unreal/scripts/dump_new_ft_pins.py
py C:/Dev/Sanjuk-Unreal/scripts/inspect_ft_routing.py
py C:/Dev/Sanjuk-Unreal/scripts/probe_abp_vars.ps1
```

**의사결정:**
| 진단 결과 | 다음 |
|----------|------|
| ABP 완전 정상 | Step 1.5로 직행 |
| Recorder 손상만 | Step 1.4-A |
| UpdateVariables 손상 | Step 1.4-B |
| 둘 다 손상 | Step 1.4-B → 1.4-A 순서 |

### Step 1.4 — ABP 복구 (필요시, 1~2시간)

**1.4-B (TRACK-B): UpdateVariables 복원**
```
py C:/Dev/Sanjuk-Unreal/scripts/restore_abp_variables.py --dry-run
py C:/Dev/Sanjuk-Unreal/scripts/restore_abp_variables.py
py C:/Dev/Sanjuk-Unreal/scripts/restore_update_variables.py --dry-run
py C:/Dev/Sanjuk-Unreal/scripts/restore_update_variables.py
py C:/Dev/Sanjuk-Unreal/scripts/phase3_gate.py
```
⚠️ PropertyAccess 20개 + AnimNodeReference 는 placeholder만 — 스크립트 끝 로그의 "MANUAL BINDING NEEDED" 따라 수동 binding

**1.4-A (TRACK-A): AnimRewindRecorder 재구축**
```
py C:/Dev/Sanjuk-Unreal/scripts/consolidate_ft_chain_step1.py
py C:/Dev/Sanjuk-Unreal/scripts/consolidate_ft_chain_step2.py
py C:/Dev/Sanjuk-Unreal/scripts/consolidate_ft_chain_step4.py
py C:/Dev/Sanjuk-Unreal/scripts/inspect_ft_routing.py
```

### Step 1.5 — 새 인프라 검증 (1시간) ⭐ 5/16 신규
**1.5-1: discover 실행**
```
py C:/Dev/Sanjuk-Unreal/scripts/discover_monolith_actions.py
```
**확인:**
- `.claude/state/action_catalog.json` 생성됐나
- 어떤 discover API 패턴이 작동했나 (출력 로그 "succeeded")
- `.claude/state/unused_actions.md` 검토 → 즉시 활용 가능 5~10개 노트

**1.5-2: lib import 동작**
```
cd C:\dev\Sanjuk-Unreal\scripts
py -c "from lib import rpc; print('rpc:', rpc); from lib import find_var_get, bulk_connect; print('lookup + bulk: ok')"
```
→ 에러 없으면 lib 정상

**1.5-3: apply_and_verify (PIE 빼고)**
```
py C:/Dev/Sanjuk-Unreal/scripts/workflows/apply_and_verify.py --asset /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP --skip-pie
```
→ compile/save 자동화만 검증. VerifyReport JSON 생성 확인

**1.5-4: apply_and_verify (PIE 포함)**
```
py C:/Dev/Sanjuk-Unreal/scripts/workflows/apply_and_verify.py --asset /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP --pie-seconds 5
```
→ `editor_console_command("ce StartPIE")` 가 작동하는지 확인. **이게 핵심.**

**의사결정:**
- ✅ PIE 자동 시작 → 다음 단계 모두 자동화 가능
- ❌ PIE 시작 안 됨 → `apply_and_verify.py`의 `start_pie()` 두 패턴 외 다른 호출 방식 찾아 fix

---

## 🌞 Day 2: 진단 데이터 수집 + 빠른 처방 (4~5시간)

### Step 2.1 — 노이즈 진단 데이터 수집 (1시간)
PIE에서 3시나리오 × 5회씩 재현:

| 시나리오 | 재현 |
|---------|------|
| **C1** | LockOn OFF, Sprint → 멈춤 → Battle Idle |
| **C2** | Sprint 중 LockOn ON → 멈춤 → Battle |
| **D1** | LockOn ON, 타겟 반대로 Sprint → 멈춤 (핵심) |

각 케이스 직전 0.5초 + 직후 2초 = **150프레임 슬라이스** SB2_2.log 에서 추출.
→ `Sanjuk-Unreal/UE_bot/data/abp_recordings/noise_diag_<scenario>_<n>.jsonl` 로 저장

### Step 2.2 — Q1~Q4 답 도출 (30분)
슬라이스 보면서:
```
Q1. C+D에서 가장 먼저 튀는 enum? (as / ib / pwm / il)
Q2. unstable 윈도우 길이 (프레임 수)?
Q3. unstable 동안 clip 변화 횟수?
Q4. trd / tta 변화 패턴? (수렴 / 발산 / 진동)
```

### Step 2.3 — 빠른 처방 ① 적용 (1시간)
```
# 새 스크립트 작성: scripts/extend_transition_gate.py
# add_transition_back_gate.py 의 EqualEqual_StrStr 노드를 Contains 패턴으로 교체
# Sprint_to_Battle / Sprint_to_LockOn / Sprint_to_Jog 등 매칭
```

### Step 2.4 — 빠른 처방 ② 적용 (1시간)
```
# 새 스크립트 작성: scripts/wire_sprint_window_rotation_gate.py
# bIsSprintStartTransition OR bIsSprintEndTransition → UpdateTargetRotation 게이트
```

### Step 2.5 — 효과 측정 (30분)
```
# Step 2.1 시나리오 재녹화
# before/after [ANIM_REC] 슬라이스 비교
# trd 점프 횟수, unstable 윈도우 길이 비교
```

**의사결정:**
- ✅ 효과 충분 → Day 3 본격 리팩토링 미루거나 skip
- ⚠️ 효과 부족 → Day 3 진행

---

## 🌤 Day 3-5: Transition 함수화 본격 (2~3일)

### Step 3.1 — 자료형 추가 (반나절)
```
# 새 스크립트: scripts/build_transition_state_struct.py (또는 수동)
# ETransitionKind, ETransitionPhase enum
# S_TransitionState struct
# ABP 변수: TS, RotInterpSpeed_Low/High
```
⚠️ Monolith API로 enum/struct 추가 가능한지 첫 step에서 검증. 안 되면 수동 생성.

### Step 3.2 — GetTransitionState 함수 그래프 (반나절~하루)
```
py C:/Dev/Sanjuk-Unreal/scripts/build_transition_state_chain.py
# → lib/ + bulk_ops 활용해서 의사코드대로 노드 빌드
```

### Step 3.3 — UpdateTargetRotation RInterpTo 통합 (1시간)
```
py C:/Dev/Sanjuk-Unreal/scripts/wire_rotinterp_modulation.py
```

### Step 3.4 — Chooser N_LockOn_Moveing 컬럼 (반나절)
```
py C:/Dev/Sanjuk-Unreal/scripts/add_chooser_transition_columns.py
```

### Step 3.5 — Sprint Start/End 변수 마이그레이션 (1~2시간)
```
py C:/Dev/Sanjuk-Unreal/scripts/migrate_sprint_transition_vars.py
```

### Step 3.6 — [ANIM_REC] 5필드 확장 (1시간)
```
py C:/Dev/Sanjuk-Unreal/scripts/extend_ft2_transition_fields.py
# 66 → 71필드 (tsk/tsp/tsa/tsr/ris)
# anim_rec_viewer.py FIELD_LABELS 같이 업데이트
```

→ Step 3.2~3.6 모두 **`apply_and_verify` 데코레이터로 자동 검증** (Day 1 Step 1.5-4 작동 가정)

---

## ☁ Day 6-7: 검증 + 확장 (1~2일)

### Step 4.1 — 핵심 시나리오 D1 검증 (반나절)
```
PIE에서 LockOn 반대방향 Sprint → Jog × 10회
- trd 1프레임 180도 점프 사라짐 확인
- ris (RotInterpSpeed) Low → High ramp 확인
- tsa (TS.Alpha) 곡선 자연스러움 확인
```

### Step 4.2 — 회귀 테스트 (반나절)
```
- 일반 이동 반응성 (너무 둔한지)
- Pivot 동작 (Motion Matching 정상)
- 다른 트랜지션 (Battle Start, Jump Land 등)
```

### Step 4.3 — 부족하면 ③ ④ 추가 (1일)
| 잔존 문제 | 처방 |
|----------|------|
| Stance flicker 잔존 | ③ Multi-Stance Buffer (IsBattle/IsLockOn/MovementState) |
| 큰 turn이 짧은 입력에 트리거 | ④ Sustained Turn Request (`|tta| > 90 AND IsLockOn` 0.2초) |

---

## 🌙 Day 7+: (선택) GASP 비교 검증

### Step 5.1 — GASP USmoothWalkingMode dump
```
1. C:\Users\SHIFTUP\Documents\Unreal Projects\GameAnimationSample 열기
2. USmoothWalkingMode 노드 + 파라미터 dump
3. 우리 RotInterpSpeed_Low/High 값과 비교 → 튜닝 기준값 조정
```

---

## 의존성 그래프

```
Day 1.1 /pull
   ↓
Day 1.2 Monolith + UE 가동 ──── (필수, 모든 후속 의존)
   ↓
Day 1.3 진단
   ├─→ ABP 정상  → Day 1.5 (인프라 검증)
   └─→ ABP 손상 → Day 1.4 복구 → Day 1.5
                                    ↓
Day 1.5 인프라 검증
   ├─→ 모두 OK → Day 2 (자동화 활용)
   └─→ PIE 자동화 X → 수동 PIE로 Day 2 (느리지만 진행 가능)
                                    ↓
Day 2 진단 데이터 + 빠른 처방
   ├─→ 효과 충분 → Day 6 (검증)
   └─→ 효과 부족 → Day 3 (본격 리팩토링)
                                    ↓
Day 3-5 Transition 함수화
   ↓
Day 6-7 검증 + 확장
   ↓
(선택) Day 7+ GASP 비교
```

---

## 시간 추정 + 우선순위

| Phase | 최소 | 평균 | 우선순위 |
|-------|------|------|---------|
| Day 1 (환경 + 진단 + 인프라) | 2시간 | 3~4시간 | 🔴 필수 (root) |
| Day 2 (진단 + 빠른 처방) | 3시간 | 4~5시간 | 🔴 필수 (즉각 효과) |
| Day 3-5 (Transition 함수화) | 1.5일 | 2~3일 | 🟡 효과 부족 시 |
| Day 6-7 (검증 + 확장) | 0.5일 | 1~2일 | 🟡 Day 3 갔으면 필수 |
| Day 7+ (GASP 비교) | 2시간 | 반나절 | 🟢 선택 |

**최소 ROI 경로:** Day 1 + Day 2 까지만 (반나절~하루) → 노이즈 큰 부분 잡고 마무리.

---

## 🚨 막힐 가능성 + 대응

| 막힘 | 대응 |
|------|------|
| Monolith 응답 안 함 | UE Editor 재시작, 9316 포트 충돌 확인, `/recover` 스킬 |
| `discover()` 모든 패턴 실패 | 알려진 도메인 fallback enumerate (스크립트 자동 처리) |
| `editor_console_command` 작동 X | apply_and_verify `--skip-pie` 모드로 우선 사용, PIE는 수동 |
| restore 스크립트 PropertyAccess 깨짐 | placeholder만 만들어지고 수동 binding 안내 — 안내 따라 |
| ABP 컴파일 에러 | 백업 JSON으로 롤백 후 단계별 재시도 |
| lib 모듈 import 실패 | `cd scripts` 한 후 import / sys.path 확인 |

---

## 관련 문서 (의존)

- 복구: `Briefing/2026-05-14_recovery-master-plan.md`
- 처방: `Briefing/2026-05-14_motion-noise-diagnosis-prescription.md`
- Recorder 재구현: `Briefing/2026-05-14_rewind-recorder-final-implementation.md`
- Transition 함수화: `Briefing/2026-05-15_transition-function-design.md`
- 7-Phase 로드맵: `Briefing/2026-05-15_implementation-roadmap.md`
- MCP-First Architecture: `Briefing/2026-05-16_mcp-workflow-architecture.md`
