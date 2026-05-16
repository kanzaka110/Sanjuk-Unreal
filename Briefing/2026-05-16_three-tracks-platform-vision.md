# 2026-05-16 — SB2 업무 플랫폼: 3-Track 비전

## Final Goal

> **SB2 데이터 분석 → 구현 → 검증의 최고의 업무 라인 구축**

PC_01 ABP의 Transition 함수화는 이 플랫폼을 검증하는 **첫 use case**일 뿐. 본질은 모든 SB2 작업(Cloth / Groom / GAS / AI BT / Niagara ...)이 같은 플랫폼 위에서 동작하게 만드는 것.

---

## Executive Summary

본 프로젝트는 **세 가지 독립된 영역(트랙)이 서로를 강화하며 발전**하는 형태로 진행:

1. **MCP 활용도 향상** — 개발 효율
2. **로그·정보 수집 시스템** — 관측 가능성
3. **Use Cases** — 구현 검증

각 트랙은 독립적으로 발전하지만 시너지 포인트에서 만나며, 최종적으로 **데이터 분석부터 구현 검증까지 자동화·정밀화된 업무 라인**을 형성.

---

## 시각 재정의 (Key Correction)

| 이전 (잘못된) 시각 | 올바른 시각 |
|-------------------|-----------|
| 한 줄 흐름: Phase 1 → 2 → 3 → 4 → 5 | 세 트랙 동시 발전, 시너지에서 만남 |
| Transition 구현이 최종 목표 | Transition은 첫 use case, 본질은 플랫폼 |
| MCP·정보 수집은 Transition을 위한 보조 | MCP·정보 수집은 모든 SB2 작업의 기반 인프라 |
| 완료 = D1 노이즈 해결 | 완료 = 자동화된 업무 라인 정착 |

---

## Three Track Structure

```
                          [최종 비전]
              SB2 데이터 분석 → 구현 → 검증
                  최고의 업무 라인
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼─────┐       ┌────▼─────┐       ┌────▼─────┐
   │ TRACK 1  │       │ TRACK 2  │       │ TRACK 3  │
   │   MCP    │       │   로그·  │       │   USE    │
   │  활용도  │       │   정보   │       │  CASES   │
   │   향상   │       │   수집   │       │ (구현)   │
   └──────────┘       └──────────┘       └──────────┘
   개발 효율           관측 가능성         첫 사례: Transition
```

---

## 🔧 Track 1 · MCP 활용도 향상 (개발 효율)

**본질:** 언리얼 작업 시 Monolith MCP(1,226 액션)를 가장 효율적으로 활용하는 워크플로우/도구 라이브러리.

**적용 대상:** 모든 향후 SB2 작업 (Transition만이 아니라 Cloth, Niagara, GAS, AI BT, ...)

### 5-Layer 구조

| 영역 | 산출물 | 상태 |
|------|--------|------|
| ① Discovery | `scripts/discover_monolith_actions.py` — 1,226 액션 자동 카탈로그 | ✅ 스켈레톤 (5/16) |
| ② Abstraction | `scripts/lib/` (monolith_client + node_lookup + bulk_ops + workflow_decorators) | ✅ 작성 (5/16) |
| ③ Operations | 기존 119 스크립트 | ✅ 정착 |
| ④ Automation | `scripts/workflows/apply_and_verify.py` — 수정→PIE→VerifyReport 자동화 | ✅ 스켈레톤 (5/16) |
| ⑤ Delegation | `.claude/rules/agent-triggers.md` — 자동 에이전트 위임 | ✅ 작성 (5/16) |

**완료 정의:** 새 작업 시작 시 "이 패턴으로 가면 빨라"가 명확. 어떤 도메인이든 같은 lib + workflows + 에이전트 트리거로 진행.

---

## 📡 Track 2 · 로그·정보 수집 시스템 (관측 가능성)

**본질:** AI(Claude Code / Inspector 에이전트)가 SB2의 실제 동작 상태를 정확하고 풍부하게 받게 하는 채널·표준·자동화 체계.

**철학:** "AI에게 정확한 정보 전달이 모든 진단·처방 품질의 root"

### 채널 / 컴포넌트

| 채널 | 내용 | 상태 |
|------|------|------|
| `[ANIM_REC]` (기반) | PC_01 ABP 매 틱 emit, 66필드 (f, sp, as, ms, ist, ...) | ✅ 완료 (5/14) |
| 채널 A — AnimGraph 노드값 | fpa, bs0_w, bs1_w, ow_a, lbpb_w, pp_a, ik_l_w/r, rotw_a, bs0_seq (+10 → 76) | 🔄 계획 |
| 채널 B' — Motion Matching (cost 외) | ps_db, ps_pi, ps_seq, ps_alt, ps_jr, ps_cnt (+6 → 82) | 🔄 계획 |
| 채널 C — State Machine trace | 신규 `[SM_TRACE]` 채널 (from / to / rule / winner) | 🔄 계획 |
| 채널 D — Notify trace | 신규 `[NOTIFY_TRACE]` 채널 | 🔄 계획 |
| 채널 E — UE Output Log filter | LogAnim / LogPoseSearch / LogChooser 자동 추출 | 🔄 계획 |
| 메타 표준화 | 모든 채널에 `[PIE=N] frame=X t=T` 통일 | 🔄 계획 |
| 채널 L — 자동 컨텍스트 주입 | `scripts/lib/context_injector.py` — Inspector 호출 시 7가지 자동 첨부 | 🔄 계획 |

**완료 정의:** "이 케이스에서 무슨 일?" 질문에 30초 안에 정확한 답을 도출 가능. 어떤 도메인 진단이든 같은 패턴으로 채널 추가 가능.

---

## 🎯 Track 3 · Use Cases (구현 검증)

**본질:** Track 1 + 2를 실제 작업에 적용하면서 검증 + 가치 창출.

**역할:** 플랫폼의 가치를 입증하고, 작업 중 발견되는 부족함을 Track 1/2로 피드백.

### Use Cases

| ID | 케이스 | 상태 |
|----|-------|------|
| **UC-1** | **Transition 함수화 (PC_01 ABP)** — LockOn 반대방향 Sprint→Jog 노이즈 | ✅ 설계 (5/15), 구현 대기 |
| UC-2 | 모션 노이즈 일반 처방 (4 형태 + ① ② ③ ④) | 🔄 UC-1 결합 진행 |
| UC-3+ | Chaos Cloth / Groom 시뮬레이션 / GAS 어빌리티 / AI BT / Niagara | 💡 TBD |

**완료 정의:** 각 케이스별 명확한 검증 기준 통과 (예: UC-1은 D1 시나리오 회전 점프 0회). 작업 회고를 통해 Track 1/2 보강 항목 도출.

---

## 지금까지 작업의 트랙별 매핑

이미 세 트랙이 동시에 진행되고 있었음 — 단지 한 흐름으로 인식했을 뿐.

| 날짜 | 작업 | Track | 산출물 |
|------|------|-------|--------|
| 5/11 | Chooser dump 스크립트 + N_AfterEvade | T3 (정찰) | PC_01 Chooser 인벤토리 |
| 5/13 | [ANIM_REC] 23필드 Recorder | **T2** | 매 틱 emit + viewer |
| 5/13 | Sprint→Battle 게이트 (bIsPlayingTransitionBack) | T3 | B_Lfoot 회전 차단 |
| 5/13 | 모션 노이즈 진단 도구 (pivot/isstarting/drawdebug) | T2 + T3 | 분석 헬퍼 |
| 5/14 | FormatText 통합 8→1, 66필드 | **T2** | 풀 통합 |
| 5/14 | Sprint Start chain | T3 | Transition 윈도우 변수 |
| 5/14 | restore 스크립트 (복구/변환) | **T1** | 2-Track 복구 도구 |
| 5/15 | Transition 함수화 설계 | T3 | 의사코드 + 통합점 |
| 5/15 | GASP USmoothWalkingMode 레퍼런스 | T3 | 설계 방향 검증 |
| 5/16 | MCP-First Architecture (5-Layer + MVP 1~4) | **T1** | discover + lib + workflows + triggers |
| 5/16 | 정보 채널 보강 설계 (Phase α/β/γ) | **T2** | 6채널 + L 설계 |

---

## 트랙 간 시너지 (어디서 만나나)

| 시너지 포인트 | 상호작용 |
|--------------|----------|
| **T1 → T3** | UC-1 Transition 구현 시 lib + bulk_connect로 노드 빌드 가속 (5~6배). apply_and_verify로 매 단계 자동 검증. |
| **T2 → T3** | UC-1 처방 후 [ANIM_REC] 87필드로 before/after 정량 비교. 시각만이 아닌 데이터 기반 검증. |
| **T3 → T1** | UC-1 작업 중 자주 쓰는 패턴 발견 시 lib에 추가. PoseSearch / Chooser 전용 helper 누적. |
| **T3 → T2** | UC-2 Cloth 진단 같은 새 케이스 시 `[CLOTH_TRACE]` 신규 채널 추가. 채널 라이브러리 풍부화. |
| **T1 + T2 → 플랫폼** | discover() → 새 액션 발견 → bulk wrapper 추가 → 채널 emit 자동화. 새 도메인 시작 시 인프라 즉시 마련. |

---

## 트랙별 다음 단계

### 🔧 Track 1 (즉시)
- ✅ **완료:** MVP-1~4 스켈레톤 (discover + lib + workflows + triggers)
- 🎯 **다음:** 로컬 PC 검증 → action_catalog.json 분석 → 미사용 액션 5~10개 흡수 → 첫 use case (UC-1) 작업에서 실전 검증
- 📈 **장기:** action_usage.json 누적 → 월별 갱신 → Epic 5.8 공식 MCP 마이그레이션 대비

### 📡 Track 2 (T1 검증 후)
- ✅ **완료:** [ANIM_REC] 66필드 + 외부 viewer
- 🎯 **다음:** 채널 A → C → B' → D → E 순차 추가 → 메타 표준화 → L 자동 컨텍스트 주입
- 📈 **장기:** 다른 도메인 채널 추가 (`[CLOTH_TRACE]`, `[GROOM_TRACE]`, `[GAS_TRACE]`, ...)

### 🎯 Track 3 (T1+T2 일부 마련 후)
- ✅ **완료:** UC-1 Transition 설계 + 레퍼런스 검증 (5/15)
- 🎯 **다음:** UC-1 Sub A → B → C → 시각 검증 → 정보 수집 강화 후 Sub D~F + 추가 처방 ① ②
- 📈 **장기:** UC-2 (모션 노이즈 일반) → UC-3+ (Cloth/Groom/GAS/AI BT)

---

## 시너지 포인트 (트랙 만나는 시점)

```
T1 인프라 검증 ──→ T3 UC-1 작업 (lib + apply_and_verify 사용)
                          │
                          ▼
                 T3 1차 효과 확인
                          │
                          ▼
T2 채널 확장 (A→C→B'→D→E) ──→ T3 객관적 효과 측정 (87필드)
                          │
                          ▼
                 T2 메타 표준화 + L
                          │
                          ▼
T3 UC-1 완료 (Sub D~F + 처방 ① ②) ──→ T1 lib 개선 피드백
                          │
                          ▼
                 T1+T2+T3 통합 플랫폼 검증 ✓
                          │
                          ▼
              UC-2 또는 새 도메인 (Cloth/Groom...)
              같은 플랫폼 위에서 빠르게 진행
```

---

## 🚀 Day 1 (2026-05-18 월요일) 첫 행동

```
1. cd C:\dev\Sanjuk-Unreal
2. /pull                                        # 모든 5/16 자료 받기
3. py scripts/discover_monolith_actions.py      # T1 MVP-1 검증
4. py -c "from lib import rpc; print('ok')"     # T1 MVP-2 검증
5. py scripts/workflows/apply_and_verify.py \
       --asset /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP \
       --skip-pie                               # T1 MVP-3 (PIE 없이)
6. (위 OK면) --pie-seconds 5 추가하여 PIE 자동화 검증
```

→ Day 1 끝 = Track 1 인프라 작동 확인. Track 3 UC-1 작업 시작 가능 상태.

---

## Action Items 요약

### 🔧 Track 1 (즉시)
1. 로컬 PC `/pull` → MVP-1 검증
2. `discover_monolith_actions.py` 실행 + 미사용 액션 흡수
3. `apply_and_verify` PIE 작동 검증 (editor_console_command 호출 방식)

### 📡 Track 2 (T1 검증 후)
1. 채널 A (AnimGraph 노드값) — 가장 빠른 효과
2. 채널 C (SM trace) + B' (Motion Matching) 병렬 추가
3. 채널 D + E 추가 후 메타 표준화
4. L 자동 컨텍스트 주입 — Inspector 호출 정확도 5~10배 향상

### 🎯 Track 3 (T1+T2 일부 마련 후)
1. UC-1 Sub A (enum/struct/변수) — T1 lib 활용
2. Sub B (함수 그래프) — bulk_connect 적극 활용
3. Sub C (RInterpTo 통합) — apply_and_verify로 즉시 검증
4. 1차 시각 검증 → 효과 보고 Sub D~F + 처방 ① ② 결정
5. UC-1 회고 → T1/T2 보강 피드백

---

## 관련 Briefing 문서 (Track별 인덱스)

### Track 1 (MCP 활용)
- `Briefing/2026-05-16_mcp-workflow-architecture.md` — 5-Layer + MVP 1~4 설계
- `Briefing/2026-05-14_recovery-master-plan.md` — 2-Track 복구 (T1 도구)

### Track 2 (정보 수집)
- `Briefing/2026-05-14_rewind-recorder-final-implementation.md` — 66필드 단일 FT_2
- `Briefing/2026-05-14_motion-noise-diagnosis-prescription.md` — 일부 T2 진단 + T3 처방

### Track 3 (Use Cases)
- `Briefing/2026-05-15_transition-function-design.md` — UC-1 설계
- `Briefing/2026-05-15_implementation-roadmap.md` — UC-1 구현 로드맵 (재해석: T3 중심 시각)

### 메타 / 가이드
- `Briefing/2026-05-16_local-pc-sequential-guide.md` — 로컬 PC 작업 순차 가이드
- `Briefing/2026-05-16_three-tracks-platform-vision.md` — **이 문서 (마스터 인덱스)**

---

## 환경 제약

- Track 1 검증 / Track 2 채널 추가 / Track 3 ABP 수정 — 모두 **로컬 PC + Monolith 동작** 필요
- GCP 세션에서는 설계 / 스크립트 작성 / 문서 정리만 가능
- 일과 병행: 하루 5~6시간 가용 시 약 2.5~3주 캘린더
