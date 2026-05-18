---
name: pc01-session-end-2026-05-18-v2
description: "2026-05-18 두 번째 세션 종료. IsTransition→IsLockOnTransition 변수 backing 완성 (= IsStrafe wrapper). smooth chain 양쪽 분기 시도 후 사용자 직접 제거 (효과 미미). 새 호소 — 회피 후 Start 노이즈, Chooser row 영역. 다음 세션 PIE 로그 분석부터."
metadata: 
  node_type: memory
  type: project
  date: 2026-05-18-v2
  originSessionId: 1299abe5-d83c-4a31-bc04-41fb9e09339f
---

# 2026-05-18 v2 세션 종료 상태

## 살아있는 변경 (디스크 저장 — 사용자 Ctrl+S 필요)

### 1. IsLockOnTransition 변수 (사용자가 IsTransition 에서 rename)
- bool, 디폴트 카테고리, IE=true
- UpdateVariables 식: **IsLockOnTransition = IsStrafe** (단순 wrapper)
- 노드: Set IsStrafe.then → Set IsLockOnTransition.execute (직렬)
- 데이터: Get IsStrafe → Set IsLockOnTransition.input
- IsStrafe 정의: `IsLockOn AND IsMoving AND (PendingWalkMode != Sprinting)`
- 효과: 락온 + 이동 + 비-Sprint 구간 전체에 true (지속 상태)

### 2. DrawDebug 의 Get IsLockOnTransition
- FT_7.IT 핀에 wire. PIE 화면에 `IT=true/false` 출력
- PIE 검증 통과: 락온+Jog 이동 시 true, Sprint 또는 정지 시 false

## 시도했다가 통째 폐기한 작업

### A. UpdateTargetRotation trd 게이트 (한 틱 차단)
- IsTransition=true 시 SelectFloat 로 trd=0 차단
- inline 검증 식 사용 (EnumEquality + NOT + AND ×2)
- **롤백 이유**: 사용자 호소 (Sprint→Jog Turn/Box 끼어듦) 영역 다름. trd 는 회전 보정, Turn/Box 는 BlendStack/MM 영역

### B. SM transition rule wire 변경 (bShouldTransitToIdle)
- FromGroundMoving → TransitToGroundIdle rule 을 multi-node → 단일 변수 wire 로 교체
- monolith set_transition_rule 한계: multi-node 통째 교체
- **부작용**: 일반 정지 시 Idle 진입 못함 (Stop/Pivot/Transit 모션 안 나옴) — 사용자 보고
- 복구: ABP 에디터에서 사용자 수동으로 원본 multi-node rule 재구성

### C. UpdateTargetRotation smooth chain (alpha 동적, 양쪽 분기)
- 식: `alpha = clamp(abs(TrjTurnAngle)/90, 0.075, 1.0)`, `smooth = Prev + (raw-Prev)*alpha`, `output = IsStrafe ? smooth : raw`
- 두 Set TargetRotationDelta (Strafe + 비-Strafe) 모두 적용
- 16 노드 + 27 connections
- **롤백 이유** (사용자 직접 ABP 에디터에서 노드 제거): "smooth chain 효과가 크게 없어서"
- 이론적 부작용: alpha 동적 jitter, PrevTRD 의 stale 값 누적 (회피 후 Start 노이즈 가능성 추정했으나 사용자가 PIE 전 제거)

## 사용자 새 호소

**회피 후 Start 모션에서 노이즈가 심함**
- 영역: GroundMoving state 안의 BlendStack / MM / Chooser
- Monolith 한계: ChooserTable row 데이터 protected — array 메타만 보임 (ResultsStructs 6 row, ColumnsStructs 1 column, ContextData 2)
- 다음 세션: PIE ANIM_REC 로 `he`=true 프레임 → 그 직후 `seq` 키 추적 → 노이즈 시점 매칭 클립 식별

## 학습 사항 (다음 세션 활용)

1. **set_transition_rule 한계**: 단일 boolean 변수 wire 만 가능. 기존 multi-node rule 통째 교체. monolith 자동 복원 불가 → 사용자 수동 복원만 가능
2. **ABP 함수 ThreadSafe 마킹**: monolith API 미노출. ThreadSafe 그래프(UpdateTargetRotation, UpdateVariables 등) 에서 호출하려면 inline 식 우회 또는 ABP 에디터에서 Details 패널 수동 활성화
3. **smooth chain 비율 선형 alpha 효과 미미**: 작은 회전=강한 smooth, 큰 회전=raw 패턴이 사용자 시각 인지에 효과 없음 (5/15 학습과 동일 결론)
4. **alpha 동적 계산 부작용**: 매 틱 alpha 변동 → smooth 강도 jitter → 시각 노이즈 가능성
5. **PrevTRD 갱신 시점 의존성**: output 저장 vs raw 저장 — output 저장 시 회피 잔여값 다음 구간으로 누출
6. **ABP 컴파일 시 노드 ID 재할당**: compile_blueprint 후 K2Node_XXX_N ID 가 재할당될 수 있음. 작업 후 search_nodes 로 재식별 필수
7. **ExecSeq then 핀 자동 확장**: monolith connect_pins 가 ExecSeq.then_N 에 새 wire 추가 시, 기존 N 연결 유지하고 then_N+1 자동 생성. (5/14 메모리의 "덮어쓰기" 가설은 일부 케이스만)
8. **Chooser ChooserTable 한계**: get_cdo_properties 가 array meta 만 보임 (ResultsStructs, ColumnsStructs, ContextData 카운트만). row condition 직접 조회 불가
9. **JustExitedSprint 변수 naming 함정**: 실제 식은 `(PrevPwm == Sprinting) AND (Pwm == Sprinting)` — Sprint **유지** 의미, "Exit" 아님. 5/14 메모리 해석 오류 (한 번 더 확인)
10. **사용자 호소 영역 다단계 검증**: Sprint→Jog Turn/Box, 회피→Start 노이즈 모두 BlendStack/MM/Chooser 영역. trd 게이트나 SM transition rule 차원 시도는 영역 불일치로 효과 없음

## 메모리 동등 관계

- IsLockOnTransition == IsStrafe (UpdateVariables 의 단순 wrapper)
- IsStrafe == IsLockOn AND IsMoving AND (PendingWalkMode != Sprinting)
- 즉 **IsLockOnTransition 가 별도 의미 없음 — IsStrafe 의 alias**

## 다음 세션 작업 순서 (제안)

1. **PIE 회피→Start 시나리오 + ANIM_REC 로그 캡처**
2. `he=true` 프레임 → 그 직후 `seq` 키 변화 grep
3. 노이즈 시점 매칭 클립 식별
4. 클립이 회피 잔여 / 잘못된 Start / Pivot 매칭 중 어느 것인지 분석
5. 결정:
   - Chooser row 보강 (사용자가 ABP 에디터 수동)
   - PSD ContinuingPoseCostBias 조정 (Monolith 가능)
   - 또는 다른 변수 게이트

## 관련 메모리

- [[pc01-session-end-2026-05-18]] — 첫 번째 세션 종료 (오늘 오전)
- [[pc01-session-end-2026-05-15]] — 이전 세션 (5/15)
- [[pc01-evade-pipeline-applied]] — 5/15 회피 pipeline 작업 (EvadeDurationThreshold=0.3, UMSB HasEvade OR 게이트)
- [[pc01-evade-pipeline-design]] — 5/15 회피 설계
- [[pc01-anim-rewind-recorder]] — ANIM_REC 디버거 시스템
- [[monolith-animgraph-editing-limits]] — set_transition_rule + Chooser 한계
