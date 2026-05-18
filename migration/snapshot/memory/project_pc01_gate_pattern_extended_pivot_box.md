---
name: pc01-gate-pattern-extended-pivot-box
description: "PC_01_ABP bIsPlayingTransitionBack 게이트 패턴을 3 → 5패턴 확장 (2026-05-15). Sprint_to_Battle/LockOn/Jog + Pivot + Box. 사용자 호소 \"Transition 1프레임만 잡히고 Box로 swap → mesh가 raw처럼 보임\" 해결. PIE 검증 완료."
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PC_01 bIsPlayingTransitionBack 5패턴 확장 (2026-05-15)

## 증상
[ANIM_REC] SB2_2.log v7 (1410~1848) 분석:
```
i=222 Sprint_Turn_R_180  trd=178  (raw, 게이트 false)
i=223 Transition_Sprint_to_Battle  trd=0   ← 처방 작동! 1프레임
i=224 Fist_Battle_Jog_Box_LL_F  trd=178   ← Box로 swap, 게이트 false → raw
i=225~ Box 매칭 지속  trd=178°
```

Transition 1프레임만 매칭 후 Box로 swap. ContinuingPoseCostBias=-1.0 적용했어도 swap 막힘 안 됨 (MM이 매 프레임 새로 search 하는 듯). Box 시점 게이트 false라 mesh가 raw 178° 회전 = 사용자 "수정 안 됨" 호소.

## 처방

bIsPlayingTransitionBack Contains 패턴 3 → 5 확장:
```
bIsPlayingTransitionBack =
    Contains("Sprint_to_Battle") OR Contains("Sprint_to_LockOn") OR Contains("Sprint_to_Jog")
    OR Contains("Pivot") OR Contains("Box")
```

신규 추가:
- `Pivot` — Fist_Battle_Jog_Pivot_*_Rfoot 시리즈
- `Box` — Fist_Battle_Jog_Box_*_Lfoot/Rfoot 시리즈

사용자 의도 (2026-05-15): "Box/Pivot 도 root motion만 사용 (추가 회전 X), transition과 동일 취급"

## 구현

### UpdateVariables 신규 4노드
- `K2Node_CallFunction_11` — Contains "Pivot"
- `K2Node_CallFunction_28` — Contains "Box"
- `K2Node_CallFunction_32` — BooleanOR (or3, 기존 OR2 + Pivot)
- `K2Node_CallFunction_33` — BooleanOR (or4, or3 + Box)

### 새 chain
```
기존 OR2 (CF_41, Sprint_to_Battle/LockOn/Jog 결과)
  ↓
or3 (CF_32): OR2 OR Contains("Pivot")
  ↓
or4 (CF_33): or3 OR Contains("Box")
  ↓
Set bIsPlayingTransitionBack (K2Node_VariableSet_75)
```

CurrentSequenceName (VG_52) → 5개 Contains 노드 모두 SearchIn 입력.

## PIE 검증 결과 (SB2_2.log v8, 1848~2148 새 부분)

```
i=98  Sprint_Turn_R_180         trd=178.69  raw 유지 ✓
i=101 Transition_Sprint_to_Battle  trd=0    ✓ 게이트 true
i=102 Fist_Battle_Jog_Box_LL_F   trd=0     ✓ Box swap 후에도 0 유지!
i=103~ Box_LL_F 지속              trd=0     ✓ root motion만
```

**모든 transition + Box 재생 구간 동안 trd=0**. mesh 추가 회전 차단, root motion만으로 회전. 사용자 호소 해결.

## 검증
- compile_blueprint: success, errors=0, warnings=0
- save_asset: P4 잠금 (사용자 Ctrl+S 필요)
- PIE 실제 trd 값 검증 ✓

## 잠재 부작용
- "Pivot" / "Box" 명명에 매칭되는 클립 중 의도와 다른 게 있다면 부작용 가능. 현재 알려진 매칭:
  - Fist_Battle_Jog_Pivot_B_F_Rfoot, F_B_Rfoot, LL_RL_Rfoot, RL_LL_Rfoot (4종)
  - Fist_Battle_Jog_Box_F_LL_Rfoot, F_RL_Lfoot, LL_F_Lfoot, RL_B_Lfoot, RL_F_Rfoot (5종)
- PSD_GroundMovingTransit/PSD_GroundMoving 에 다른 "Pivot/Box" 명명 클립 있는지 추후 검증

## 관련
- 게이트 본문: [[pc01-smoothing-scope-restriction]]
- CF_26.B = 0 (transition 중 trd=0): [[pc01-smoothing-to-zero-revert]]
- ABP reload 시 노드 ID 재할당 이슈 (재발견)
- CurrentSequenceName fresh set: [[pc01-currentseqname-eventgraph-fix]]
- PSD bias: [[pc01-psd-gmt-continuing-bias]] (ContinuingPoseCostBias=-1.0 한계 확인. MM Continuing 메커니즘이 PC_01 BlendStack 환경에서 약하게 작동)
