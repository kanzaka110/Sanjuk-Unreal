---
name: pc01-trd-wraparound-smoothing
description: UpdateTargetRotation Strafe 분기 trd wraparound 평활화 (2026-05-15). 180° 경계 부호 반전 (180 → -174) + 큰 step 변동 시 mesh visible jitter 처방. shortest-arc delta + 0.5 lerp + double NormalizeAxis.
metadata: 
  node_type: memory
  type: project
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# PC_01 UpdateTargetRotation trd wraparound 평활화 (2026-05-15)

## 증상
- 사용자 호소: "회전 구간에서 튀는 현상이 좀 심한 것 같아"
- 시나리오: 락온 + 반대 질주 → 질주 해제 시 모션 자체는 정상 (PSD_GMT ContinuingPoseCostBias=-0.5 효과 검증됨), but 회전 진입 시점 visible jitter

## [ANIM_REC] 실측 패턴 (2026-05-15)

### Pattern 1: 180° wraparound (f161-163)
```
f161  Sprint_Stop_F_Rfoot   sp=332   trd=0
f162  Sprint_Stop_F_Rfoot   sp=132   trd=180     ← trd 0 → 180 점프
f163  Sprint_Turn_L_180     sp=31    trd=-174    ← 180 → -174 부호 반전 (NormalizeAxis wrap)
f164  Sprint_Turn_L_180     sp=19    trd=-165    ← 회복
```

### Pattern 2: 큰 step jump (f139-141)
```
f139  Sprint_Start_Evade    sp=630   trd=42
f140  Sprint_Start_Evade    sp=572   trd=80.856  ← 한 프레임 38.8° jump
f141  Sprint_Turn_R_090     sp=562   trd=71      ← clip swap
```

## 원인
UpdateTargetRotation Strafe 분기가 매 프레임 `NormalizeAxis(NormalizedDeltaRotator.Yaw * -1)` 결과를 즉시 Set TargetRotationDelta. 평활화 없음. 180° 경계는 `NormalizeAxis` 의 wraparound 때문에 부호 반전 jitter, 큰 회전 명령은 한 번에 큰 step 변동 → BlendStack BlendTime=0.2 가 따라가지 못해 mesh visible jitter.

## 처방

### Phase 1: 신규 변수
- `PrevTargetRotationDelta` (double, 0.0, Buffer 카테고리, IE=false, BPRO=false)

### Phase 2: Strafe 분기 8노드 chain 삽입
**위치**: UpdateTargetRotation 그래프 Strafe 분기. 기존 `K2Node_CallFunction_4 (NormalizeAxis raw)` → `K2Node_VariableSet_3 (Set TargetRotationDelta)` 직결을 다음 chain으로 교체.

**데이터 흐름**:
```
CF_4 (NormalizeAxis raw) → 1
GetPrev_A.PrevTargetRotationDelta → 2

Subtract(1, 2) = RawDelta - PrevDelta = Diff               [K2Node_CallFunction_10]
NormalizeAxis(Diff) = ShortDelta                            [K2Node_CallFunction_11]   ← shortest-arc 보장
Multiply(ShortDelta, 0.5) = HalfDelta                       [K2Node_CallFunction_12]   ← 50% lerp
Add(GetPrev_B.PrevTargetRotationDelta, HalfDelta) = SmoothRaw [K2Node_CallFunction_13]
NormalizeAxis(SmoothRaw) = WrappedSmooth                    [K2Node_CallFunction_14]   ← 최종 wrap 안전
```

**output 분기**:
- `CF_14.ReturnValue` → `Set_3.TargetRotationDelta` (기존 wiring 교체)
- `CF_14.ReturnValue` → `SetPrev_0.PrevTargetRotationDelta` (신규)

**exec chain**:
- 기존: `Knot_1.OutputPin → Set_3.execute → (end)`
- 변경: `Knot_1.OutputPin → Set_3.execute → Set_3.then → SetPrev_0.execute → (end)`

### 동작 검증 (수치)
| frame | RawDelta | PrevDelta | Diff (NA) | HalfDelta | SmoothRaw | WrappedSmooth |
|-------|---------:|----------:|----------:|----------:|----------:|--------------:|
| 1 (f161) | 0     | 0     | 0    | 0    | 0     | 0     |
| 2 (f162) | 180   | 0     | 180  | 90   | 90    | 90    | ← 한 번에 도달 안 함 (0→90→...)
| 3 (f163) | -174  | 90    | -84  | -42  | 48    | 48    | ← wraparound 회피 (180→-174 점프 없음)
| 4 (f164) | -165  | 48    | -33  | -16  | 32    | 32    | ← 부드럽게 따라감

## 검증
- `add_variable`: success (PrevTargetRotationDelta)
- 신규 노드 8개 추가 (Get×2, Subtract, NA×2, Multiply, Add, SetPrev)
- 모든 wiring 의도대로 connect (CF_14 → Set_3 + SetPrev_0 양방향)
- `compile_blueprint`: success, errors=0, warnings=0
- `save_asset`: P4 잠금 실패 → 사용자 Ctrl+S 필요

## PIE 검증 시나리오
1. 락온 + 반대 질주 → 질주 해제 (이전 처방 검증된 케이스)
2. 회전 진입 시점 mesh가 부드럽게 회전하는지 확인
3. [ANIM_REC] 재캡처:
   - `trd` 값이 매 프레임 작은 차이로 변하는지 (180° 경계 부호 반전 없음)
   - clip swap 시점이 줄어드는지

## Alpha 튜닝 결과 (2026-05-15)

### Phase 1: 단일 Alpha 시도
| Alpha | 결과 | 비고 |
|------:|------|------|
| 0.5 | ❌ "이상하게 나옴" | 큰 lerp 시 mesh 회전이 의도와 다른 방향으로 진행 가능 |
| **0.075** | ✅ 큰 회전엔 best | 7.5% lerp. 단발 큰 회전 부드러움 |
| 0.075 (빠른 입력 시) | ❌ "빠르게 움직였을 때 회전 꼬임" | 7.5% lerp 가 연속 입력 변화 못 따라감 → mesh lag → trajectory 어긋남 → MM 매칭 꼬임 |

### Phase 2: Adaptive Alpha (현재 적용)
조건부 Alpha — diff 크기에 따라 자동 분기.

```
bIsSmall = InRange(NA(diff), -45.0, 45.0)
Alpha    = SelectFloat(A=0.5, B=0.075, bPickA=bIsSmall)
SmoothDelta = PrevDelta + NA(diff) * Alpha
```

| diff 절대값 | Alpha | 의도 |
|----:|---:|------|
| < 45° (작은/빠른 입력) | **1.0** | RawDelta 그대로 (smoothing 0). 빠른 입력 100% 즉시 반응 |
| ≥ 45° (큰 회전) | **0.075** | 부드러운 따라감. wraparound jitter 회피 |

**Alpha=0.5 → 1.0 조정 사유 (2026-05-15)**: 0.5 는 prev와 raw 의 50:50 평균이라 작은 입력에도 smoothing이 약하게 들어감. 사용자 의도는 "작은 입력엔 raw 그대로 반영" 이므로 1.0 (= Diff×1.0 = raw - prev, SmoothDelta = prev + (raw-prev) = raw) 으로 변경. 작은 diff (<45°)는 wraparound jitter 위험 없으므로 0.5도 1.0도 부작용 없음, 1.0 이 의도 명확.

### 추가 노드 (Phase 2)
- `K2Node_CallFunction_16` — InRange_FloatFloat (Value=CF_11.ReturnValue, Min=-45, Max=45)
- `K2Node_CallFunction_17` — SelectFloat (A=0.5, B=0.075, bPickA=InRange.ReturnValue)
- `K2Node_CallFunction_12.B` 핀: SelectFloat.ReturnValue 로 wire input (default 0.075 무시)

## 잠재적 부작용
- 모든 strafe 회전이 50% 평활화됨 — 의도된 빠른 turn (큰 trd) 도 부드러워짐
- DeadBlending / Inertialization 후처리와 중복 보정 — 현재는 같이 작동하지만 over-smoothing 우려 시 0.5 → 0.7 상향
- 락온 OFF 분기 (IsStrafe=false) 는 손대지 않음 (else 분기 K2Node_CallFunction_5 → K2Node_VariableSet_4 그대로)

## 스크립트
- `scripts/add_trd_wraparound_smoothing.py` — Phase 1 + 2 + 3 통합. v0.12.1 schema (add_variable name/type, disconnect_pins node_id/pin_name) 적용.

## 관련
- 이전 처방 [[pc01-psd-gmt-continuing-bias]] — ContinuingPoseCostBias -0.5 (Pivot/Box swap 해결됨, 회전 jitter 별개 문제)
- ABP 체인: [[pc01-abp-chain]] (DeadBlending=SM뒤, Inertialization=Overlay뒤)
- 5/13 작업 [[pc-01-sprint-battle-b-lfoot-abp]] (rolled back) — UpdateTargetRotation Strafe 분기 게이트 패턴
