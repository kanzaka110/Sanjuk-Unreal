---
name: pc01-transition-gate-user-corrected
description: "PC_01 ABP transition 회전 처방 최종 (2026-05-15 사용자 정정). NOT 제거 + Get bIsPlayingTransitionBack 직접 wire + Adaptive Alpha 분기 제거 + 단일 alpha=0.075. 사용자가 직접 만든 wiring 이 정답. 우리 \"trd=0\" 가설은 처음부터 잘못."
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PC_01 Transition 회전 처방 — 사용자 정정 최종 (2026-05-15)

## 핵심 — 우리 가설이 잘못이었음

5/13 사용자 호소 "Sprint→Battle 종료 시 root motion + 추가 회전 충돌" 을 우리는 **"transition 중 trd=0"** 으로 해석 → wraparound smoothing + 게이트 + literal 0 등 일련의 처방. 결국 사용자가 직접 정정한 wiring 이 진짜 정답이었음.

사용자 정정 (직접 에디터에서):
- NOT (CF_25) 제거
- Get bIsPlayingTransitionBack → SelectFloat.bPickA **직접** 연결

이로 인해 의미가 반전:
- bIsPlayingTransitionBack=true (transition 재생) → bPickA=true → **A 선택**
- bIsPlayingTransitionBack=false (일반 회전) → bPickA=false → **B 선택**

## 최종 wiring (2026-05-15 검증됨)

```
SelectFloat (CF_26):
    A ← CF_28 (NormalizeAxis Raw, 즉 transition 중 raw 회전)
    B ← CF_22 (NormalizeAxis Smooth chain, 즉 일반 시점 wraparound 처방)
    bPickA ← VG_10 (Get bIsPlayingTransitionBack, NOT 없이 직접)

smooth chain (단일 alpha=0.075, Adaptive 분기 제거):
    CF_7 (Subtract Raw-Prev)
    → CF_8 (NormalizeAxis diff)
    → CF_15 (Multiply * 0.075 literal)   ← Adaptive 분기 (InRange+SelectFloat) 제거됨
    → CF_21 (Add Prev + Multiply)
    → CF_22 (NormalizeAxis smooth) → CF_26.B
```

## 실제 동작 (게이트 의미 정반대)

| 시점 | bIsPlayingTransitionBack | 선택 | 효과 |
|------|:-:|---|---|
| **일반 turn / 큰 회전** (Sprint_Turn, wraparound 발생) | false | **B = Smooth (alpha=0.075)** | jitter 완화 ← 사용자 처음 호소 처방 |
| **Transition_Sprint_to_Battle 재생** | true | **A = Raw** | mesh 자연 회전 |
| Box, Pivot 매칭 | true | A = Raw | mesh 자연 회전 |
| Idle / Loop | false | B = Smooth ≈ Raw | mesh 자연 회전 |

**핵심**: smooth chain 은 **일반 시점 wraparound jitter 처방**으로 작동 중. transition 시점은 Raw 직결. 사용자가 원했던 **mesh 자연스러운 raw 회전** + **wraparound 튐만 부드럽게** 동시 달성.

## 정리 작업 (2026-05-15 16:xx)

### 제거된 노드 (Dependency cycle 해소)
- `K2Node_CallFunction_23` (InRange_FloatFloat, Adaptive 분기)
- `K2Node_CallFunction_24` (SelectFloat A=0.075/B=0.075, 사실상 무의미)
- 이전에 NOT (K2Node_CallFunction_25) 도 사용자가 제거

### CF_15.B 변경
- before: SelectFloat 결과 wire (Adaptive)
- after: **0.075 literal**

### 컴파일 결과
- compile: success, errors=0, warnings=0 (Dependency cycle 해소)
- save: P4 잠금 → 사용자 Ctrl+S 영구화

## 보존된 처방 (모두 의미 있음)

1. **PSD_GroundMovingTransit.ContinuingPoseCostBias = -1.0** — Pivot/Box 1프레임 swap 감소
2. **bIsPlayingTransitionBack 변수 + Contains 5패턴** (Sprint_to_Battle/LockOn/Jog/Pivot/Box) — UpdateVariables 매 틱 매칭
3. **EventGraph BlueprintUpdateAnimation event + Set CurrentSequenceName** — fresh CurrentSequenceName 보장
4. **smooth chain** (alpha=0.075 단일) — 일반 시점 wraparound 처방
5. **SelectFloat 게이트** (A=Raw, B=Smooth, bPickA=bIsPlayingTransitionBack NOT 없이) — 사용자 정정 wiring

## 교훈 (피드백 메모리화 가치)

- ANIM_REC 수치만 보고 "처방 성공" 판단하면 안 됨. **mesh 시각적 동작이 진짜 검증 기준**.
- 처음 호소를 잘못 해석할 수 있음 — "회전 충돌" 이 "trd=0" 의미가 아니었음.
- 사용자가 직접 에디터에서 wiring 조정한 결과가 가장 정확한 의도 표현.
- Adaptive 분기 같은 추가 복잡도는 cycle 위험 + 무의미한 경우 다수.

## 관련 (이전 시도들, 폐기됨)
- [[pc01-trd-wraparound-smoothing]] (모든 strafe 분기 적용 — rolled back)
- [[feedback-pc01-trd-smoothing-alpha-0-075]] (Adaptive Alpha 가설 — 정정됨, alpha=0.075 단일 사용)
- [[pc01-smoothing-scope-restriction]] (게이트 architecture — 살아있지만 의미 반전)
- [[pc01-smoothing-to-zero-revert]] (CF_26.B=0 literal — 사용자가 NOT 제거로 정정)
- [[pc01-gate-pattern-extended-pivot-box]] (5패턴 확장 — 살아있음)
- [[pc01-transition-gate-final]] (잘못된 success 보고 — 본 메모리가 진짜 최종)
- [[pc01-currentseqname-eventgraph-fix]] (CurrentSequenceName fresh — 살아있음)
- [[pc01-psd-gmt-continuing-bias]] (ContinuingPoseCostBias=-1 — 살아있음)
