# PC_01 FootClamp 스무스 블랜드 + 진입 딜레이 구현 (2026-05-04)

## 작업 목표

전투 대기(Battle + Idle) 상태에서 FootClamp 클램프 값을 전투용으로 부드럽게 전환.

## 구현된 ControlRig 구조

### 변수 (Monolith로 추가)

| 변수 | 타입 | 기본값 | 용도 |
|---|---|---|---|
| TargetAlpha | float | 0.0 | 딜레이 후 목표 블랜드 값 (0 or 1) |
| BlendSpeed | float | 5.0 | AccumulateLerp 블랜드 속도 |
| CombatEnterDelay | float | 0.3 | 전투 진입 딜레이(초) |
| DelayCounter | float | 0.0 | 딜레이 타이머 누적값 |

### Branch 로직 (IsBattle AND NOT IsMove)

```
True  → DelayCounter 누적 → 임계값 도달 시 TargetAlpha=1.0 (Select 노드)
False → DelayCounter=0.0 → TargetAlpha=0.0
Completed → AccumulateLerp(TargetValue=TargetAlpha, Blend=BlendSpeed) → Set CombatAlpha → ForEach
```

### DelayCounter 노드 체인 (True 브랜치)

```
Get DelayCounter + DeltaTime → Add
Add → Clamp(0, CombatEnterDelay) → Set DelayCounter
Add >= CombatEnterDelay → BoolToInt → Select.Index
  [0] = Get TargetAlpha (미달: 현재값 유지)
  [1] = 1.0             (도달: 전투값으로 전환)
→ Set TargetAlpha
```

### Clamp_1 입력 (Vector Lerp 2개)

| 항목 | A (NonCombat) | B (Combat) | X=Roll, Y=Pitch, Z=Yaw |
|---|---|---|---|
| Minimum | (-15, -5, -10) | (-25, -20, -20) | → Clamp_1.Minimum |
| Maximum | (15, 10, 10) | (25, 35, 20) | → Clamp_1.Maximum |

T = Get CombatAlpha

## 다음 세션 — PIE 검증

| 케이스 | 기대 동작 |
|---|---|
| Peaceful idle/walk | NonCombat 클램프 유지 |
| Battle idle | 0.3초 딜레이 후 Combat 클램프로 블랜드 |
| Battle walk/공격 | NonCombat 클램프 유지 |
| 전투→비전투 전환 | 즉시 NonCombat 복귀 |

이상 있으면 `CombatEnterDelay` (딜레이), `BlendSpeed` (속도) 값 조정.
