---
name: pc01-currentseqname-eventgraph-fix
description: PC_01_ABP CurrentSequenceName stale 처방 (2026-05-15). EventGraph 에 BlueprintUpdateAnimation event 신규 추가 + 그 안에서 game thread 매 틱 Set CurrentSequenceName. UpdateVariables (BPThreadSafe) 가 fresh 값 읽도록.
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PC_01 CurrentSequenceName stale 처방 (2026-05-15)

## 증상
- bIsPlayingTransitionBack 가 transition 재생 시점에 false → Strafe 분기 SelectFloat가 Raw 선택 → trd=178° 그대로 → mesh 추가 회전 (root motion 충돌)
- [ANIM_REC] SB2_2.log 1146 frame 분석: Transition_Sprint_to_Battle_Jog_B_Lfoot 진입 시 trd ≈ 178°, 1프레임만 reset 안 됨

## 근본 원인

`CurrentSequenceName` 변수의 SET 위치 = `DrawDebug` 그래프 (PostEvaluateAnimation 시점) **만**.

ABP 매 틱 호출 순서:
1. NativeUpdateAnimation (game thread, C++)
2. BlueprintUpdateAnimation (game thread, **EventGraph 에 노드 없으면 호출 안 됨**) ← 신규 추가
3. **BlueprintThreadSafeUpdateAnimation (worker thread)** ← UpdateVariables 호출. `Get CurrentSequenceName` 시점. 이전 PostEvaluate 시점의 stale 값을 읽음
4. AnimGraph 평가
5. **BlueprintPostEvaluateAnimation (game thread)** ← DrawDebug 호출. `Set CurrentSequenceName` 시점

즉 PostEvaluate(N) → 다음 프레임 BPThreadSafe(N+1) → 매 틱 1프레임 lag. 게다가 DrawDebug의 Set 가 `K2Node_IfThenElse_6.Condition (BooleanAND_19)` false면 영원히 stale.

## 처방

### EventGraph 에 BlueprintUpdateAnimation event 신규 추가

```
[Event BlueprintUpdateAnimation (K2Node_Event_0, game thread, 매 틱)]
    ↓ then
[Set CurrentSequenceName (K2Node_VariableSet_0)]
    ↑ input
[GetDisplayName (K2Node_CallFunction_1, KismetSystemLibrary)] ← game thread, ThreadSafe 무관
    ↑ Object
[BreakStruct S_BlendStackInputs (K2Node_BreakStruct_0).Anim_3_*]
    ↑ S_BlendStackInputs
[Get BlendStackInputs (K2Node_VariableGet_0)]
```

### 새 호출 흐름 (1 틱)
| 시점 | Set CurrentSequenceName | Get CurrentSequenceName | 결과 |
|------|-------------------------|------------------------|------|
| BlueprintUpdateAnimation (신규) | ✓ fresh set | — | 매 틱 game thread 시점 갱신 |
| BlueprintThreadSafeUpdateAnimation (UpdateVariables) | — | ✓ fresh read | Contains 매칭 정확 → bIsPlayingTransitionBack 정확 set |
| BlueprintPostEvaluateAnimation (DrawDebug) | ✓ 또 set | — | 동일 값 또 set (영향 없음) |

## 검증
- 신규 노드 4개 + wire 4개: 성공
- compile_blueprint: success, errors=0, warnings=0
- **save_asset: saved=true, was_dirty=true** (P4 잠금 풀려서 디스크 영구화 성공)

## 동시 보존된 처방
- bIsPlayingTransitionBack 변수 + Contains 3패턴 (Sprint_to_Battle/LockOn/Jog) — UpdateVariables
- UpdateTargetRotation SelectFloat 게이트: A=Raw (CF_4), B=0.0 (literal), bPickA=NOT(bIsPlayingTransitionBack) — 모든 wire 정상
- PSD_GroundMovingTransit.ContinuingPoseCostBias = -1.0 — 별도 처방

## PIE 검증 시나리오
1. 락온 반대 질주 → 종료 (B_Lfoot transition) → **trd=0 기대** (mesh 추가 회전 없음, root motion만)
2. 락온 + 180° 입력 Turn 매칭 → 게이트 false → raw 회전 (사용자 정확한 느낌)
3. 일반 회전 → 게이트 false → raw

## 잠재 부작용
- DrawDebug 의 Set CurrentSequenceName 노드는 그대로 유지 (이중 set, 같은 값). 추후 정리 가능
- BlueprintUpdateAnimation event 활성화로 game thread 부하 미세하게 증가 (BreakStruct + GetDisplayName 한 번씩)

## 스크립트
- `scripts/fix_currentsequencename_via_eventgraph.py` — 신규 event 추가 + chain wiring + compile + save

## 관련
- 게이트 본문: [[pc01-smoothing-scope-restriction]]
- 5/13 패턴 부활: [[pc01-smoothing-to-zero-revert]]
- ABP 호출 순서: [[pc01-abp-chain]]
- ThreadSafe 한계로 UpdateVariables 안에 GetDisplayName 호출 시도 실패 (이 처방의 backstory)
