---
name: pc01-session-end-2026-05-15
description: 2026-05-15 작업 세션 종료 시점 ABP 최종 상태 + 다음주 작업 계획 (IsTransition 정의부터). 5/15 일련의 게이트/smooth 처방 시도 → 통째 폐기 후 smooth chain 만 살림.
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# 2026-05-15 세션 종료 상태 + 다음주 계획

## 오늘 작업 요약 (시도 → 결과)

### 시도된 처방 (대부분 폐기됨)
1. **wraparound smoothing** (UpdateTargetRotation 전 strafe 적용) — 빠른 입력 lag 호소로 게이트로 좁힘
2. **bIsPlayingTransitionBack 게이트 (3 → 4 → 5 패턴 → 3패턴 정밀)** — Turn 매칭 안 됨 + Pivot/Box 매칭 부작용 + 일반 이동 sticky → 통째 폐기
3. **SelectFloat (raw vs smooth 선택)** — 게이트 작동했지만 mesh 시각 효과 거의 0 (smooth ≈ raw) → 통째 폐기
4. **CurrentSequenceName stale fix (EventGraph BlueprintUpdateAnimation event 추가)** — bAnimRewindRecording 등 부작용 → 폐기
5. **PSD ContinuingPoseCostBias 강화 (-0.01 → -0.5 → -1.0)** — Pivot/Start 매칭 안 됨 → -0.01 원본 복원
6. **NOT 제거 + A/B swap (사용자 직접 wiring)** — 사실상 게이트 효과 0
7. **3패턴 정밀화 (Sprint_to_Battle + Fist_Battle_Jog_Pivot + Fist_Battle_Jog_Box)** — 여전히 작동 안 함 → 폐기

### 살아남은 처방 (현재 ABP 상태)
1. **smooth chain (단순, 게이트 없이 모든 시점 적용)** — alpha=0.075 단일
   - 데이터 흐름: Raw NA → Subtract(Raw - Prev) → NA(diff) → Multiply(*0.075) → Add(Prev + Half) → NA(smooth) → Set TargetRotationDelta + Set PrevTargetRotationDelta
   - 사용자 평가: "지금까지 한 것 중 가장 좋았던 접근"
2. **IsStarting NOT(IsPivoting()) release 게이트** (5/13 작업 복구) — Pivot 매칭 회복 결정적
3. **EventGraph AnimRewindRecorderEmit chain 복원** — bAnimRewindRecording 회복
4. **bAnimRewindRecording default=True** — auto ON

### 변수 / 노드 상태
- **PrevTargetRotationDelta** (신규, double, Buffer) — smooth chain prev 저장
- **bIsPlayingTransitionBack** 제거됨
- **CurrentSequenceName** 그대로 (DrawDebug에서만 set, 우리 EventGraph 추가는 폐기)
- **PSD_GroundMovingTransit.ContinuingPoseCostBias = -0.01** (원본)

## 다음주 작업 계획

### 1. IsTransition 정의부터
사용자 호소: "IsTransition 에 대한 정의부터 시작하자"

진행 방향:
- "transition" 이 정확히 어떤 클립 / 상태인지 명확히 정의
- 후보 카테고리: Sprint→Battle 변환, Pivot, Box, Stance 변경, 큰 회전 등
- 사용자 의도 명확화: 각 카테고리에서 mesh가 어떻게 움직여야 하는지 (raw / smooth / 차단 등)
- 정의 후 게이트 패턴 다시 설계 — 작동하는 게이트로

### 2. 검토할 미해결 호소
- **Sprint→Battle Transition 시점에 Sprint_Turn 끼어듦** — MM cost / Chooser row 영역 (Monolith 한계, 에디터 작업 필요)
- **Transition 1프레임만 매칭 후 Pivot/Box swap** — 동일 영역
- **사용자가 처음 호소한 root motion + trd 충돌** — 다시 검증 필요

### 3. 학습 사항 (다음 작업 시 활용)
- ANIM_REC 수치만 보고 처방 성공 판단 금지 — mesh 시각 동작이 진짜 기준
- ABP wiring 변경 후 매번 사용자 Ctrl+S 즉시 + P4 체크아웃 확인 필수
- ABP compile 시 노드 ID 재할당 — 작업 후 ID 새로 확인 필요
- 5패턴 같은 광범위 Contains 매칭은 부작용 큼 — 의도된 클립명만 정확히 잡아야

## 사용자 액션 (당일 종료 전 권장)
- PC_01_ABP **Ctrl+S** 마지막 확인 (smooth chain 디스크 영구화)
- PSD_GroundMovingTransit 자체 변경 없으니 추가 작업 X

## 관련 메모리 (모두 outdated 처리 권장)
- [[pc01-transition-gate-phase1]] — rolled back
- [[pc01-smoothing-scope-restriction]] — rolled back
- [[pc01-gate-pattern-extended-pivot-box]] — rolled back
- [[pc01-transition-gate-final]] — outdated
- [[pc01-transition-gate-user-corrected]] — outdated
- [[pc01-smoothing-to-zero-revert]] — rolled back
- [[pc01-currentseqname-eventgraph-fix]] — rolled back (EventGraph chain 제거)
- [[pc01-psd-gmt-continuing-bias]] — rolled back to -0.01 원본

## 유효한 메모리
- [[pc01-trd-wraparound-smoothing]] — smooth chain 본문 (alpha=0.075 단순화 후)
- [[reference_pc01_isstarting_design]] — IsStarting NOT(IsPivoting()) 게이트 패턴
- [[pc01-anim-rewind-recorder]] — ANIM_REC 시스템
- [[feedback-pose-search-data-moving-default-0]] — YawRate=0 룰
- [[feedback-visual-mesh-over-anim-rec]] — mesh 시각 동작이 진짜 검증 기준
