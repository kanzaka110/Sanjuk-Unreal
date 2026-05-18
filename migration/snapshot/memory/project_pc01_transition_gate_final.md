---
name: pc01-transition-gate-final
description: "PC_01 ABP transition 회전 보정 게이트 최종 검증 완료 (2026-05-15). 5패턴 게이트 + CF_26.B=0 literal + EventGraph fresh set + PSD bias -1.0. PIE 4/4 transition 매칭 시 trd=0 일관, Box swap 후에도 유지. 사용자 호소 완전 해결."
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PC_01 Transition 회전 보정 게이트 최종 (2026-05-15)

## 사용자 호소 (시작점)
1. "락온 + 반대 질주 → 종료 시 Sprint_to_Battle_Jog_B_Lfoot 가 잘 나올 때도 있고 안 나올 때도 있음"
2. "Transition만 나와야 할 구간에 Pivot/Box가 끼어듦"
3. "회전 구간 튐 (wraparound jitter)"
4. "락온 + 180° 입력 Turn 매칭 안 됨"
5. "디버그에서 bIsPlayingTransitionBack=true 적용되지만 mesh가 raw 그대로 회전"
6. "Not 적용 전 (raw turn) 동작이 정확한 느낌"

## 최종 해결 시스템 (4 컴포넌트)

### A. PSD_GroundMovingTransit.ContinuingPoseCostBias = -1.0
디스크 영구화. Pivot/Box 1프레임 swap 일부 차단 (전체 차단 못함, MM Continuing 메커니즘 한계).

### B. UpdateVariables — Contains 5패턴 (bIsPlayingTransitionBack)
```
bIsPlayingTransitionBack =
    Contains(CurrentSequenceName, "Sprint_to_Battle") OR
    Contains(CurrentSequenceName, "Sprint_to_LockOn") OR
    Contains(CurrentSequenceName, "Sprint_to_Jog") OR
    Contains(CurrentSequenceName, "Pivot") OR
    Contains(CurrentSequenceName, "Box")
```
Pivot/Box 도 transition 동일 취급 — Box swap 후에도 게이트 true.

### C. UpdateTargetRotation Strafe 분기 SelectFloat 게이트
```
TargetRotationDelta = bIsPlayingTransitionBack ? 0 : Raw_NormalizeAxis
```
- A = Raw (CF_4 NormalizeAxis)
- **B = 0.0 (literal)** ← 핵심
- bPickA = NOT(bIsPlayingTransitionBack)

### D. EventGraph BlueprintUpdateAnimation event (CurrentSequenceName fresh set)
game thread 매 틱 시점에 BlendStackInputs → BreakStruct → GetDisplayName → Set CurrentSequenceName. UpdateVariables (BPThreadSafe) 가 fresh 값 읽음.

## PIE 검증 결과 (SB2_2.log v10, 2702~3500 새 부분)

| 케이스 | trd | 결과 |
|---|:-:|:-:|
| 4건 transition 진입 (3 B_Lfoot + 1 LL_Lfoot) | **0** | ✓ 4/4 |
| Box swap 후 15+ 프레임 지속 | **0** | ✓ 일관 |
| Sprint_Turn raw 회전 | 178° | ✓ raw 유지 (사용자 의도) |

## 진행 시 발생했던 주요 함정 (메모리 보존)

| 함정 | 해결 |
|---|---|
| ABP compile 시 노드 ID 재할당 (CF_20 → CF_26 등) | dump로 재매핑 후 작업 |
| ContinuingPoseCostBias -0.5 → 메모리만 적용, PIE 시작 시 reload | 사용자 Ctrl+S 직접 + P4 체크아웃 |
| CurrentSequenceName stale (DrawDebug PostEvaluate 시점 set) | EventGraph BlueprintUpdateAnimation 추가 |
| smooth chain 결과 = Raw 와 거의 동일 (Adaptive Alpha=1.0 구간) | smoothing 폐기, literal 0 사용 |
| Transition 1프레임만 매칭 후 Box swap (ContinuingPose 한계) | 패턴에 Pivot, Box 추가 |
| ABP wiring 매번 reload로 사라짐 | save 디스크 영구화 (사용자 Ctrl+S) |

## 잔존 dead code (정리 가능)

- UpdateTargetRotation: K2Node_CallFunction_7/8/10~14, K2Node_VariableGet_3/9 (smooth chain), K2Node_CallFunction_23/24 (Adaptive InRange + SelectFloat), K2Node_VariableSet_0 (Set PrevTargetRotationDelta)
- 변수: PrevTargetRotationDelta (현재 사용 안 됨)

compile clean, 작동 영향 없음. 추후 cleanup 작업 가능.

## 관련
- 게이트 본문: [[pc01-smoothing-scope-restriction]]
- 5패턴 확장: [[pc01-gate-pattern-extended-pivot-box]]
- CurrentSequenceName fresh: [[pc01-currentseqname-eventgraph-fix]]
- CF_26.B literal 0: [[pc01-smoothing-to-zero-revert]]
- PSD bias: [[pc01-psd-gmt-continuing-bias]]
- MM 파이프라인: [[pc01-mm-pipeline]]
