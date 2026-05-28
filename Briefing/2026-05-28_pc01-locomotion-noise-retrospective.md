# PC_01 로코모션 노이즈 디버깅 회고 (2026-05-14 ~ 05-27)

> 약 2주(달력 14일)에 걸친 PC_01 ABP 로코모션 전이·Chooser 노이즈 제거 작업의 회고.
> "왜 이렇게 오래 걸렸나", "무엇이 남았나"를 타임라인·헛다리·교훈으로 정리.
> 출처: 메모리 sub-index `MEMORY_PC01.md` + git log(5/13~5/28).

---

## 0. TL;DR

- **달력 14일** (집중 구간 5/14~5/27), 체감 3주. 코드 시간보다 **"어느 레이어가 범인인지" 좁히는 데 대부분 소요**.
- 노이즈는 단일 버그가 아니라 **양파 구조** — 회피 진입 Stop → ToIdle 고착 → AfterEvade 소실 → Run_Start_F → F방향 오선택까지 까일수록 다음 게 드러남.
- 산출물은 버그 픽스가 아니라 **재사용 분석 도구 4종 + 게이트 단일 원칙 + 실패 레버 카탈로그 + Chooser/SM 구조 규명**.

---

## 1. 타임라인

| 날짜 | 단계 | 핵심 작업 | 결과 |
|------|------|----------|------|
| 5/13~14 | **인프라 구축** | AnimRewindRecorder(BP 디버거) + MM 노이즈 1차 진단/처방 | 정량 측정 기반 마련 |
| 5/15 | 회전 보정 | trd wraparound 평활화, transition 함수화 설계, 7-Phase 로드맵 | smooth chain만 유지(나머지 롤백) |
| 5/18 | 인프라 2차 | ANIM_REC 채널 확장(Chooser 5필드) + 로그 표준화 7-Phase + 시각검증 자동화 + 자동백업 hook | 디버깅 파이프라인 완성 |
| 5/19 | 모디파이어 | AM_SBFootStep/Sync 분리 (FX vs Sync notify 책임 분리) | 별개 트랙 정리 |
| 5/20 | 진단 도구 | Chooser/MoveSide 진단 스크립트, TrjIsCircling off-delay | 채터링 메커니즘 확정 |
| 5/21 | **F→B 해결** | IsPivoting 양분기 SmoothedVelocity>50 통일 + 락온 턴 bPrevIsMoving 제거 | F→B 피벗 ✅ (단 4회 오진 후) |
| 5/22 | **대량 해결** | 질주 반전 Stop / B→F 피벗 / 비락온 정지 지연 / 회피 전후 노이즈 | 4건 동시 ✅ |
| 5/26 | 락온 방향 | 락온 Start/Pivot/Reface (IsPivoting이 bIsStart kill) + R_90 수용 | 방향성 ✅ + MM continuing OFF 발견 |
| 5/27 | **회피 마무리** | 회피 Stop 재발(게이트 유실) 재적용 + F방향 레버 3종 실패 → 수용 | Stop ✅, F방향 엔진팀 이관 |

---

## 2. 헛다리·롤백 이력 (왜 오래 걸렸나)

노이즈 디버깅이 비선형적인 이유 — **틀린 가설에 시간이 갔고, 적용했다 되돌린 처방이 많았다.**

### 2-1. 오진 (가설이 틀림)

| 문제 | 틀린 가설 | 실제 범인 | 교훈 |
|------|----------|----------|------|
| F→B 피벗 | strafe/isc, 임계값, IsBlocked 상수, Stop 게이트 (**4종 오진**) | else 분기 bPrevIsMoving 속도-dip 의존 | 회귀는 상수 아닌 **델타**에서 찾아라(과거 로그 vs 현재 비교) |
| B→F 피벗 | "IsPivoting 대칭 조건 누락" (이틀 소요) | **Chooser 동일 시퀀스 중복 행** | 함수가 대칭이면 입력 아닌 **소비층(Chooser)** 의심 |
| 락온 방향 Start | MoveSide·DB 결백으로 5/20 종결한 줄 | IsPivoting이 bIsStart kill (ip=true→ist=false 96%) | 한 번 "결백" 판정도 다른 각도서 재검증 |
| PSD ContinuingPoseCostBias | "-1.0 검증완료" | continuing search 자체가 **OFF**라 적용 대상 없었음 | "검증완료"도 전제(배선)부터 확인 |

### 2-2. 롤백 (적용했다 되돌림)

- **IsStrafe 강제 true** — 회전 꼬임(Jog_F/Sprint_Loop_F 번짐) → revert
- **MoveSide pre-evade 래치** — trd dip이 3프레임 선행 → 무효 → revert
- **trd-소스 OR게이트** — 이동 전체 고장 → P4 revert
- **MM continuing 배선** — 질주 정지 Stop 미재생·loop 고착 회귀 → disconnect
- **5/22 회피 게이트** — P4 미저장으로 **유실** → 5/27 재적용

> **F방향 오선택 BP 그래프 레버 3종 전부 실패** → trd/MoveSide/IsStrafe가 너무 load-bearing이라 ABP 그래프 수술은 부작용이 큼. 애님(montage full-body) 또는 C++(엔진팀) 영역으로 이관 결론.

---

## 3. 무엇이 해결됐나 (✅실측)

| 노이즈 | Before | After |
|--------|--------|-------|
| 회피 진입 Stop 끼임 | 58% / ~10f(최대 33f) | sms=2 진입 30/30 **0프레임**, 꼬리 0~2f만 |
| 질주 반전 Stop 끼임 | 빈발 | **92%↓** + 락온 방향 보존 |
| B→F 피벗 미발동 | 미발동 | 반전 42건 **전부 발동·플리커 0** |
| 비락온 정지 지연 | 4프레임 | **1프레임** |
| AfterEvade Start 소실 | 미재생 | 정상 재생 |
| F→B 피벗 | 미끄러짐(158건) | Turn 발동(3건) |

**게이트 단일 원칙 확립**: *Start 상태로 들어가게/머물게 = HasEvade 추가, 나가게/Idle로 = HasEvade 금지.*

---

## 4. 수용된 잔여 (intrinsic — 실증 후 수용)

- **감속(Sprint→Run)중 회피 ~8f Transition 클립** — AfterEvade tier가 재가속 후에야 결정되는 본질적 한계(freeze 77% 무효 실증).
- **락온 측면회피 F방향 오선택** — MM trajectory 전방편향. BP 그래프 레버 전부 실패 → 애님/엔진팀.
- **1프레임 타이밍홀 4건** — 극저빈도.
- **Overlay ON 시 다리 떨림** — 파라미터/CtrlRig/Inertialization 무효 → 엔진 C++ 커스텀 필요.

---

## 5. 영구 자산 (다음엔 2주 안 걸리는 이유)

### 분석 도구 (상시 회귀 탐지기)
- `analyze_bf_pivot.py` — sv heading flip 기반 반전 onset 검출
- `analyze_sms_path.py` — sms 인덱스 디코더(state-name 필드 불필요)
- `analyze_stop_latency.py` — 정지 지연 프레임 측정
- `analyze_evade_intrusion.py` — 회피 끼어듦 정량화 (clip/sms 기반)

### 도구 신뢰도 메타지식
- `get_transitions`는 rule 트리 **truncate 안 함** → 신뢰 가능
- ANIM_REC **프레임당 2x emit** → dedup 필수
- **seq 필드 불신**(stale `Stand_Idle_Loop`), `clip`/`sms`만 신뢰
- 천단위 콤마(`3,933,903`) 파싱 함정 → 전처리 안 하면 dedup 1틱으로 붕괴

### 구조 규명 (부산물)
- PC_01 **MM continuing search 통째 OFF**(ContinuingProperties 핀 미연결) → 향후 MM 튜닝 출발점
- 죽은 룰 식별(node32 Re-Transit 컨듀잇은 ToIdle 진입 불가 → 무효)

---

## 6. 교훈 (다음 작업 견적·방법론)

1. **노이즈는 양파다** — 하나 잡으면 가려진 다음 게 드러남. 견적은 "버그 N개"가 아니라 "레이어 깊이"로.
2. **함수 대칭이면 소비층을 봐라** — 입력 함수가 대칭인데 결과가 비대칭이면 Chooser/MM 중복·바인딩 의심.
3. **load-bearing 변수는 건드리지 마라** — trd/MoveSide/IsStrafe는 여러 소비처가 물려 있어 그래프 수술 부작용이 큼.
4. **회귀는 델타에서** — 상수를 뒤지지 말고 "언제부터 깨졌나"(과거 로그 vs 현재)를 비교.
5. **적용 ≠ 저장** — P4 미저장 유실 전례. get_transitions diff로 라이브 반영 확인 후 PIE 검증.
6. **수용도 결론이다** — intrinsic 한계는 추정 아닌 실증 후 명시적으로 수용 → 무한 튜닝 루프 종료.
7. **과적용 금지** — 정확한 엣지만. 전이2에 HasEvade 넣었다가 AfterEvade 소실시킨 회귀 사례.

---

## 관련 메모리
- `MEMORY_PC01.md` (sub-index, ⭐ 현재 최종)
- `project_pc01_bf_pivot_chooser_dup.md` — Chooser 중복행
- `project_pc01_evade_stop_intrusion.md` — 회피 노이즈 전말
- `project_pc01_sprint_reversal_stop_intrusion.md` — 질주 반전
- `project_pc01_ispivoting_smoothedvelocity.md` — F→B
- `project_pc01_lockon_directional_start_pivot.md` — 락온 방향
- `reference_sb2_known_pitfalls.md` — 재발 함정 카탈로그
