# 8. Leg Adjustment 시스템

## 8.1 Leg Adjustment란?

Leg Adjustment는 Aim Chain으로 인해 상반신(특히 골반)이 회전할 때, **발이 바닥에서 미끄러지는 것을 방지**하는 시스템입니다.

```
왜 이것이 중요한가?

Aim Chain이 골반(Pelvis)을 회전시키면:
→ 골반에 연결된 다리도 같이 회전
→ 발이 원래 위치에서 벗어남
→ 마치 빙판 위에서 미끄러지는 것처럼 보임!

Leg Adjustment가 이것을 해결:
→ 골반 회전 전 발의 위치를 기록
→ 골반 회전 후 IK로 발을 원래 위치에 고정
→ 자연스럽게 보임!
```

## 8.2 Leg Adjustment 노드 추가

### Control Rig에서 설정

```
1. Control Rig 에디터 열기

2. Rig Graph 우클릭 → "Leg Adjustment" 검색

3. "FocalRig Leg Adjustment" 노드 추가

4. 실행 순서 연결 (권장):
   [Forwards Solve] → [Aim Chain] → [Leg Adjustment] → [Eye Aim] → [Recoil]
                                       ↑
                        Aim Chain 바로 다음!
                        (Eye Aim과 Recoil 전)

5. Quick Setup 적용:
   - 좌/우 다리 본이 자동 감지
   - 발 본(Foot Bone)이 자동 설정
   - IK 관련 설정이 자동 채워짐
```

### 실행 순서가 중요한 이유

```
Aim Chain → Leg Adjustment → Eye Aim → Recoil

1. Aim Chain: 골반을 포함한 상반신 회전
2. Leg Adjustment: 회전으로 벗어난 발을 원위치로 (바로 다음!)
3. Eye Aim: 보정된 포즈 위에서 눈 추적
4. Recoil: 최종 포즈에 반동 추가

Leg Adjustment를 Aim Chain 직후에 배치하면,
이후의 모든 처리가 보정된 다리 위에서 진행됩니다.
```

## 8.3 Leg Adjustment 설정 항목

### Quick Setup으로 자동 설정되는 항목

| 설정 | 설명 | 자동 감지 |
|------|------|----------|
| Left Thigh Bone | 왼쪽 허벅지 본 | thigh_l |
| Left Calf Bone | 왼쪽 종아리 본 | calf_l |
| Left Foot Bone | 왼쪽 발 본 | foot_l |
| Right Thigh Bone | 오른쪽 허벅지 본 | thigh_r |
| Right Calf Bone | 오른쪽 종아리 본 | calf_r |
| Right Foot Bone | 오른쪽 발 본 | foot_r |
| Pelvis Bone | 골반 본 | pelvis |

### 수동 조정 가능 항목

| 설정 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| Alpha | Float | 보정 강도 (0~1) | 1.0 |
| Knee Direction | Vector | 무릎이 향하는 방향 | 자동 (전방) |
| Foot Lock Threshold | Float | 발 고정 감지 임계값 | 자동 |
| Max Stretch | Float | 다리가 늘어날 수 있는 최대 비율 | 1.05 (5%) |

## 8.4 작동 원리 상세

### IK (Inverse Kinematics) 기반 보정

```
Leg Adjustment의 내부 작동 과정:

Step 1: 골반 회전 전 상태 저장
────────────────────────────
  발 위치 = 현재 월드 좌표 저장
  예: 왼발 (100, 0, 0), 오른발 (100, 50, 0)

Step 2: Aim Chain이 골반 회전 적용
────────────────────────────────
  골반이 30도 회전
  → 발이 자동으로 이동됨
  예: 왼발 (113, -30, 0), 오른발 (90, 25, 0) ← 밀려남!

Step 3: Leg Adjustment가 IK로 보정
────────────────────────────────
  저장된 원래 위치로 발을 되돌림:
  목표: 왼발 (100, 0, 0), 오른발 (100, 50, 0) ← 원래 위치!
  
  → 발은 원래 위치에 고정
  → 무릎 각도가 자동으로 조정됨
  → 허벅지-종아리 길이 비율 유지
```

### 무릎 방향(Pole Vector) 처리

```
발을 고정한 채 골반이 회전하면, 무릎이 이상하게 꺾일 수 있습니다.

문제:                    해결:
    ○ (골반)              ○ (골반)
   ╱                     ╱
  ╱                     ╱
  ╲ ← 무릎이 안쪽으로   │ ← 무릎이 전방을 유지
   ╲                    ╲
    ─ (발)               ─ (발)

FocalRig은 무릎의 Pole Vector(방향)도 자동으로 보정하여,
무릎이 항상 자연스러운 방향을 향하도록 합니다.
```

## 8.5 Alpha 활용

### 상황별 Alpha 조정

```
Alpha = 1.0 (완전 보정):
→ 발이 완전히 고정됨
→ 정지 상태에서 조준할 때 적합

Alpha = 0.5 (부분 보정):
→ 발이 약간 미끄러짐 허용
→ 느린 이동 중 조준할 때 자연스러움

Alpha = 0.0 (보정 없음):
→ 원래 FK 결과 그대로
→ 빠르게 이동 중에는 보정이 오히려 부자연스러움
```

### 동적 Alpha 전환

```
캐릭터 상태에 따른 Alpha 변경:

[정지 + 에이밍]     → Alpha = 1.0  (발 완전 고정)
[느린 걷기 + 에이밍] → Alpha = 0.7  (약간의 자연스러운 움직임)
[빠른 달리기]       → Alpha = 0.0  (보정 불필요)
[점프/공중]         → Alpha = 0.0  (발이 바닥에 없음)

블루프린트에서:
  MovementSpeed = GetVelocity().Length()
  
  If (MovementSpeed < 10)      → Alpha = 1.0
  Else If (MovementSpeed < 200) → Alpha = Lerp(1.0, 0.0, Speed/200)
  Else                          → Alpha = 0.0
```

## 8.6 Max Stretch (최대 스트레치)

### 다리 길이 한계

```
골반이 많이 회전하면, 발을 원래 위치에 고정하기 위해
다리가 "늘어나야" 하는 상황이 발생할 수 있습니다.

Max Stretch = 1.05 (기본값):
→ 다리가 원래 길이의 105%까지만 늘어남
→ 그 이상이면 발이 조금씩 끌려옴
→ 부자연스러운 길쭉한 다리 방지

Max Stretch = 1.00:
→ 다리가 전혀 늘어나지 않음 (가장 엄격)
→ 골반이 많이 회전하면 발이 바로 끌려옴

Max Stretch = 1.10:
→ 10%까지 허용 (여유 있음)
→ 넓은 스탠스(양발 간격)의 캐릭터에 적합
```

## 8.7 Aim Chain과의 연동 최적화

### 골반 가중치와의 관계

```
Aim Chain에서 골반(Pelvis) 가중치가 높으면:
→ 골반이 많이 회전
→ Leg Adjustment의 부담이 커짐
→ 극단적 각도에서 다리가 부자연스러울 수 있음

권장 설정:

[안전한 조합]
  Aim Chain 골반 가중치: 0.05 ~ 0.15
  Leg Adjustment Alpha: 1.0
  → 골반이 조금만 돌아가므로 보정이 쉬움

[도전적 조합]
  Aim Chain 골반 가중치: 0.20 ~ 0.30
  Leg Adjustment Alpha: 1.0
  Max Stretch: 1.08
  → 골반이 많이 돌아가지만 보정이 잘 작동
  → 더 역동적인 포즈

[골반 고정]
  Aim Chain 골반 가중치: 0.0
  Leg Adjustment: 필요 없음
  → 골반이 안 돌아가니 다리 보정이 불필요
  → 가장 간단하지만 상반신만 움직임
```

## 8.8 디버깅

### 흔한 문제와 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| 발이 여전히 미끄러짐 | Alpha가 0이거나 노드 비활성화 | Alpha = 1.0 확인 |
| 무릎이 안쪽으로 꺾임 | Knee Direction이 잘못됨 | Knee Direction 수정 |
| 다리가 비정상적으로 늘어남 | Max Stretch가 너무 높음 | Max Stretch를 1.05로 |
| 이동 중 발이 떠 있음 | 이동 중에도 Alpha가 1.0 | 속도에 따라 Alpha 조절 |
| 한쪽 다리만 보정됨 | 한쪽 본 매핑이 잘못됨 | Quick Setup 재실행 |

### 시각적 디버그

```
Control Rig 에디터에서:

1. Leg Adjustment 노드 선택
2. Preview 활성화
3. 뷰포트에서 확인:
   - 발의 목표 위치 (녹색 점)
   - 발의 현재 위치 (빨간 점)
   - 무릎 방향 (화살표)
   - IK 체인 (선)

두 점이 일치하면 = 보정 성공!
```

## 8.9 Foot IK와의 차이

```
Q: UE5에 이미 Foot IK가 있는데, Leg Adjustment와 뭐가 달라요?

Foot IK (UE5 기본):
- 지형에 발을 맞추는 용도 (경사면, 계단 등)
- 바닥의 높이에 따라 발 높이 조정
- "발과 바닥의 접촉" 문제 해결

Leg Adjustment (FocalRig):
- Aim Chain으로 인한 골반 회전 보정
- 발의 수평 위치를 유지 (미끄러짐 방지)
- "에이밍 시 다리 안정성" 문제 해결

둘은 서로 다른 문제를 해결합니다!
함께 사용하면 최상의 결과:
  [Aim Chain] → [Leg Adjustment] → [Foot IK]
                  (미끄러짐 방지)    (지형 적응)
```

## 8.10 실전 레시피

### 레시피 1: TPS 정지 에이밍

```
상황: 정지한 채로 좌우로 조준 (커버 슈팅 등)

설정:
- Aim Chain Pelvis Weight: 0.15
- Leg Adjustment Alpha: 1.0
- Max Stretch: 1.05
- Knee Direction: Forward (자동)

결과: 상반신이 좌우로 돌아도 발은 바닥에 고정
```

### 레시피 2: 느린 걷기 에이밍

```
상황: 조심스럽게 걸으면서 조준 (전술 이동)

설정:
- Aim Chain Pelvis Weight: 0.10
- Leg Adjustment Alpha: Speed 기반 보간 (0.3 ~ 0.8)
- Max Stretch: 1.05

결과: 걸으면서도 에이밍이 자연스러움
```

### 레시피 3: 시네마틱 대화

```
상황: NPC가 대화 상대를 바라보며 서 있음

설정:
- Aim Chain Pelvis Weight: 0.10
- Leg Adjustment Alpha: 1.0
- Max Stretch: 1.03 (엄격)

결과: NPC가 자연스럽게 몸을 돌려 상대를 보면서 발은 고정
```

## 체크리스트

다음 단계로 넘어가기 전에 확인하세요:

- [ ] Leg Adjustment 노드를 Control Rig에 추가함
- [ ] Quick Setup으로 다리 본이 자동 설정됨
- [ ] 실행 순서가 Aim Chain 직후에 배치됨
- [ ] Alpha를 캐릭터 상태에 따라 동적으로 변경하는 방법을 이해함
- [ ] Max Stretch의 역할을 이해함
- [ ] Foot IK와의 차이를 이해함

---
[← 이전: Recoil(반동) 시스템](07-Recoil-System.md) | [다음: 블루프린트 & Sequencer 연동 →](09-Blueprint-Sequencer.md)
