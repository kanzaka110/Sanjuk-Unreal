---
name: pc01-smoothing-scope-restriction
description: PC_01_ABP UpdateTargetRotation trd smoothing 적용 범위를 transition 클립 재생 중으로 제한 (2026-05-15). bIsPlayingTransitionBack 게이트 부활 (3패턴) + SelectFloat raw vs smooth 출력 선택. Turn 매칭 회복.
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PC_01 trd smoothing 적용 범위를 Transition 재생 시점으로 제한 (2026-05-15)

## 증상
사용자 호소: "락온 상태에서 180도 커맨드를 넣으면 Turn이 아예 매칭이 안 되는 문제가 있어. Transition에서만 smooth가 들어가야 할 것 같아."

## 원인
이전 처방 [[pc01-trd-wraparound-smoothing]] (+ Adaptive Alpha) 가 **모든 Strafe 분기에 항시 적용** → 일반 회전 (Turn 매칭 필요 시점) 에도 trd가 천천히 따라감 → trajectory cost 부적절 → Turn 클립 매칭 X.

## 처방 설계

게이트 + 출력 분기:
```
if bIsPlayingTransitionBack:
    TargetRotationDelta = SmoothDelta (Adaptive Alpha: |diff|<45° → 1.0, else 0.075)
    PrevTargetRotationDelta = SmoothDelta
else:
    TargetRotationDelta = RawDelta (NormalizeAxis 직결, smoothing 0)
    PrevTargetRotationDelta = RawDelta
```

`bIsPlayingTransitionBack` 매칭 (Contains 3패턴 OR, **4번째 패턴 제외** — 이전 부작용 확인됨):
```
bIsPlayingTransitionBack =
    Contains(CurrentSequenceName, "Sprint_to_Battle") OR
    Contains(CurrentSequenceName, "Sprint_to_LockOn") OR
    Contains(CurrentSequenceName, "Sprint_to_Jog")
```

## 구현

### Phase 1: 변수
- `bIsPlayingTransitionBack` (bool, Buffer, default=false, IE=false, BPRO=false)

### Phase 2: UpdateVariables 매칭 chain (신규 7노드)
- `K2Node_VariableGet_52` — Get CurrentSequenceName
- `K2Node_CallFunction_37/38/39` — Contains × 3
- `K2Node_CallFunction_40/41` — BooleanOR × 2 (trickle)
- `K2Node_VariableSet_75` — Set bIsPlayingTransitionBack

**exec chain**: ExecutionSeq_3.then_12 → Set_75.execute → Knot_1.InputPin

### Phase 3: UpdateTargetRotation 출력 게이트 (신규 3노드)
- `K2Node_VariableGet_8` — Get bIsPlayingTransitionBack
- `K2Node_CallFunction_19` — Not_PreBool
- `K2Node_CallFunction_20` — SelectFloat

**wiring**:
- CF_4 (Raw NormalizeAxis).ReturnValue → CF_20.A
- CF_14 (Smooth NA).ReturnValue → CF_20.B (이전 직결 끊김)
- Get bIsPlayingTransitionBack → Not → CF_20.bPickA
- CF_20.ReturnValue → Set_3.TargetRotationDelta (기존 CF_14 직결 끊김)
- CF_20.ReturnValue → SetPrev_0.PrevTargetRotationDelta (기존 CF_14 직결 끊김)

**동작**:
| bIsPlayingTransitionBack | NOT | bPickA | 선택 | TargetRotationDelta |
|---|---|---|---|---|
| false (일반 회전) | true | true | A | RawDelta — 기존 동작, Turn 매칭 정상 |
| true (Sprint_to_* transition 재생 중) | false | false | B | SmoothDelta — Adaptive Alpha 처방 |

## 검증
- 변수 `bIsPlayingTransitionBack`: OK
- 신규 노드 10개 (UV 7 + UTR 3) wire 정상
- CF_4.ReturnValue 가 두 곳 분기 (CF_10 smooth chain + CF_20.A direct)
- compile_blueprint: success, errors=0, warnings=0
- save_asset: P4 잠금 (Ctrl+S 필요)

## PIE 검증 시나리오
1. **락온 + 180° 커맨드** → Turn 클립 매칭 정상 (게이트 false → Raw → 기존 동작)
2. **락온 반대 질주 종료** → Transition_Sprint_to_Battle_Jog_* 재생 시작 → 게이트 true → Smooth 적용 → wraparound jitter 해결
3. **일반 strafe 미세 입력** → 게이트 false → Raw → 즉시 반응
4. **빠른 입력 흔들기** → transition 클립 안 잡히면 게이트 false → Raw → 정상 따라감

## 스크립트
- `scripts/restrict_smoothing_to_transition.py` — Phase 1+2+3+4 통합

## 관련
- 이전 smoothing 처방 본문: [[pc01-trd-wraparound-smoothing]] (Adaptive Alpha 그대로 보존, 게이트만 추가)
- Alpha 룰: [[feedback-pc01-trd-smoothing-alpha-0-075]]
- 5/13 원본 게이트 (rolled back): [[pc-01-sprint-battle-b-lfoot-abp]]
- 이전 4패턴 게이트 부작용: [[pc01-transition-gate-phase1]] (rolled back)
- ContinuingPoseCostBias: [[pc01-psd-gmt-continuing-bias]]
