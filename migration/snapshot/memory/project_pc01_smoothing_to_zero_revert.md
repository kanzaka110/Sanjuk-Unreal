---
name: pc01-smoothing-to-zero-revert
description: "PC_01_ABP UpdateTargetRotation Strafe 분기 wraparound smoothing 폐기, 5/13 원본 패턴 (transition 중 trd=0) 으로 회귀 (2026-05-15). SelectFloat.B 를 CF_14 wire → literal 0.0 변경."
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PC_01 UpdateTargetRotation smoothing 폐기 + 5/13 패턴 부활 (2026-05-15)

## 증상
사용자 호소: "디버그에서는 True 가 적용되긴해... 그런데 왜 실제 턴에서는 스므스 값이 안들어갈까?"
"mesh 가 raw 그대로 회전 (smooth 효과 안 보임)"
"Not bIsPlayingTransitionBack 적용전 순수하게 턴모션 나오는 구간은 내가 원하는 느낌이 맞아"

## 진단

[ANIM_REC] SB2_2.log (smoothing scope 처방 적용 후) 분석:
```
i=114  StartAfterEvade_B            trd=0          (게이트 false)
i=115  StartAfterEvade_B            trd=178.306    ← 0→178 jump 발생 시점 (게이트 false)
i=116  Sprint_Turn_R_180_Rfoot       trd=178.322
i=117  Sprint_Turn_R_180_Rfoot       trd=178.335
i=118  Transition_Sprint_to_Battle   trd=178.342   ← 게이트 true 진입, 그러나 trd 이미 안정
i=119  ...                          trd=178.351   ← Adaptive Alpha=1.0 (|diff|<45) → Smooth=Raw
i=120                               trd=178.362
...                                 +0.01° per frame
```

**핵심**: trd jump (0→178) 가 **transition 매칭 이전** 시점에 발생 → 게이트 false → smoothing 적용 안 됨. transition 진입 시 (게이트 true) 에는 trd가 이미 178° 안정. Adaptive Alpha=1.0 구간이라 Smooth=Raw 그대로. **smooth chain 결과 = raw 와 거의 동일** → mesh가 root motion 외 추가 178° 회전 받음 → 이중 회전 (5/13 호소 그대로 재발).

## 처방

**SelectFloat.B (CF_20.B 입력) 를 SmoothDelta(CF_14) → literal 0.0 로 변경**.

```
변경 전: CF_20.A = Raw,   CF_20.B = CF_14 (Smooth, 사실상 Raw)
변경 후: CF_20.A = Raw,   CF_20.B = literal 0.0
```

### 최종 동작
| bIsPlayingTransitionBack | bPickA | SelectFloat 선택 | TargetRotationDelta |
|:---:|:---:|---|---|
| false (일반 회전, Turn) | true | A = Raw | NormalizeAxis 그대로 |
| true (Transition_Sprint_to_* 재생) | false | B = 0 | mesh 추가 회전 차단 |

5/13 원본 의도 ([[pc-01-sprint-battle-b-lfoot-abp]]) 와 동일. 우리가 그 사이에 만들었던 wraparound smoothing 처방은 wrong assumption (trd jump 시점 가설 잘못) 으로 무효화.

## Dead code (compile clean, 추후 정리)
- `K2Node_CallFunction_10/11/12/13/14` (Subtract, NA, Multiply, Add, NA — smooth chain)
- `K2Node_VariableGet_6/7` (Get PrevTargetRotationDelta)
- `K2Node_CallFunction_16/17` (Adaptive InRange + SelectFloat)
- `K2Node_VariableSet_0` (Set PrevTargetRotationDelta — 여전히 exec chain 일부)
- `PrevTargetRotationDelta` 변수 (현재 SelectFloat output 저장, 사용 안 함)

## 검증
- `disconnect_pins` CF_14.ReturnValue → CF_20.B: OK
- `set_pin_default` CF_20.B = "0.0": OK
- `compile_blueprint`: success, errors=0, warnings=0
- `save_asset`: P4 잠금 → 사용자 Ctrl+S 필요
- verify: CF_20.B default=0.0, connected_to=[] (literal로 사용)

## 보존된 처방
- bIsPlayingTransitionBack 변수 + Contains 3패턴 OR chain (Sprint_to_Battle/LockOn/Jog) — UpdateVariables 매 틱 매칭
- SelectFloat 게이트 (CF_20) — Raw vs 0 분기
- PSD_GroundMovingTransit ContinuingPoseCostBias = -1.0 (별개 처방, 그대로 유지)

## 관련
- 원본 5/13 처방: [[pc-01-sprint-battle-b-lfoot-abp]] (rolled back 후 같은 패턴으로 다시 도달)
- 우리가 만든 wraparound smoothing (폐기됨): [[pc01-trd-wraparound-smoothing]]
- Smoothing scope 게이트 (현재 사용 중, smooth 대신 0): [[pc01-smoothing-scope-restriction]]
- Alpha 룰 (의미 없어짐): [[feedback-pc01-trd-smoothing-alpha-0-075]]
- ContinuingPoseCostBias 처방: [[pc01-psd-gmt-continuing-bias]]
