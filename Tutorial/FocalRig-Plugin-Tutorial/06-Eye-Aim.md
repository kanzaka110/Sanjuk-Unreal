# 6. Eye Aim 시스템

## 6.1 Eye Aim이란?

Eye Aim은 캐릭터의 **눈(Eye Bone)**이 타겟을 자연스럽게 추적하는 시스템입니다. 단순히 눈을 타겟 방향으로 돌리는 것이 아니라, 실제 사람의 눈 움직임을 과학적으로 시뮬레이션합니다.

```
Eye Aim의 3대 핵심 요소:

1. 스프링 댐핑 추적  → 부드러운 따라가기
2. Saccade 시뮬레이션 → 미세한 떨림 (살아있는 느낌)
3. 각도/거리 제한     → 물리적으로 불가능한 움직임 방지
```

## 6.2 Eye Aim 노드 추가

### Control Rig에 Eye Aim 배치

```
1. Control Rig 에디터 (CR_FocalRig_Character) 열기

2. Rig Graph에서 우클릭 → "Eye Aim" 검색

3. "FocalRig Eye Aim" 노드 추가

4. Quick Setup 자동 적용:
   - 왼쪽 눈 본과 오른쪽 눈 본이 자동 감지
   - 눈의 회전 축이 자동 설정
   
5. 실행 순서 연결:
   [Forwards Solve] → [Aim Chain] → [Eye Aim]
                                      ↑
   Aim Chain 이후에 실행하는 것이 자연스럽습니다
```

### 왜 Aim Chain 뒤에 배치하나?

```
실행 순서가 중요한 이유:

1. Aim Chain이 먼저 실행 → 머리가 타겟 방향으로 회전
2. Eye Aim이 그 다음 실행 → 회전된 머리 위에서 눈이 미세 조정

만약 Eye Aim이 먼저 실행되면:
→ 눈이 타겟을 보고 있는데
→ Aim Chain이 머리를 돌려서
→ 눈이 엉뚱한 곳을 보게 됨!
```

## 6.3 Eye Aim 설정 항목

### 필수 설정

| 설정 | 타입 | 설명 |
|------|------|------|
| Target | Vector | 눈이 바라볼 타겟의 월드 좌표 |
| Left Eye Bone | Bone | 왼쪽 눈 본 (Quick Setup이 자동 감지) |
| Right Eye Bone | Bone | 오른쪽 눈 본 (Quick Setup이 자동 감지) |
| Aim Axis | Axis | 눈의 전방 축 |

### 스프링 댐핑 설정

| 설정 | 타입 | 설명 | 권장값 |
|------|------|------|--------|
| Spring Stiffness | Float | 스프링 강도 (높을수록 빠르게 따라감) | 10.0 ~ 30.0 |
| Spring Damping | Float | 감쇄 강도 (높을수록 오버슈팅 적음) | 1.0 ~ 3.0 |

```
스프링 설정 예시:

[빠르고 날카로운 추적]
  Stiffness: 30.0
  Damping: 3.0
  → 군인, 경계하는 캐릭터에 적합

[느리고 부드러운 추적]
  Stiffness: 10.0
  Damping: 1.0
  → 일반 NPC, 편안한 대화 상황에 적합

[기본 설정]
  Stiffness: 20.0
  Damping: 2.0
  → 대부분의 상황에 적합
```

### 각도 제한 설정

| 설정 | 타입 | 설명 | 권장값 |
|------|------|------|--------|
| Max Horizontal Angle | Float | 좌우 최대 회전 각도 | 30° ~ 50° |
| Max Vertical Angle | Float | 상하 최대 회전 각도 | 25° ~ 40° |
| Min Distance | Float | 최소 거리 (사팔뜨기 방지) | 50 ~ 100 (cm) |

```
각도 제한의 효과:

                    ┌────────────────────────┐
      ×             │        응시 가능       │           ×
   (범위 밖)        │        ★ 타겟          │        (범위 밖)
                    │                        │
                    │    최대 ±50° (좌우)     │
                    │    최대 ±40° (상하)     │
                    └────────────────────────┘
                          캐릭터 시야

범위 밖의 타겟 → 눈은 최대 각도에서 멈춤 → Aim Chain이 몸을 돌려 보충
```

## 6.4 Saccade (급속 안구 운동) 설정

### Saccade란?

```
실제 사람의 눈 움직임을 관찰하면:

고정점을 응시하고 있어도 눈은 계속 미세하게 움직입니다.

1. Microsaccade (미세 사카드)
   - 진폭: 0.2° ~ 1.0°
   - 빈도: 1~3초마다
   - 무의식적으로 발생

2. Regular Saccade (일반 사카드)
   - 진폭: 1.0° ~ 5.0°
   - 시선이 한 고정점에서 다른 고정점으로 이동할 때
   - 매우 빠르게 (50~100ms) 발생

FocalRig은 이 두 가지를 모두 시뮬레이션합니다!
```

### Saccade 설정

| 설정 | 설명 | 권장값 |
|------|------|--------|
| Saccade Amplitude | 사카드의 크기 (각도) | 0.3° ~ 1.5° |
| Saccade Interval | 사카드 발생 간격 (초) | 1.0 ~ 3.0 |
| Saccade Randomness | 무작위성 정도 | 0.3 ~ 0.7 |

```
Saccade 설정 비교:

[기본 설정 — 자연스러움]
  Amplitude: 0.5°
  Interval: 2.0초
  Randomness: 0.5
  → 일반적인 NPC, 대화 장면

[강조 설정 — 긴장감]
  Amplitude: 1.2°
  Interval: 1.0초
  Randomness: 0.7
  → 불안한 NPC, 경계하는 캐릭터

[최소 설정 — 집중]
  Amplitude: 0.2°
  Interval: 3.0초
  Randomness: 0.3
  → 저격수, 집중하는 캐릭터
```

## 6.5 Eye Aim + Aim Chain 연동

### 기본 연동 패턴

```
그래프 구조:

[Forwards Solve]
       │
       ▼
[Aim Chain] ─── Target: AimTarget 변수
       │
       ▼
[Eye Aim] ─── Target: EyeTarget 변수 (보통 AimTarget과 동일)
       │
       ▼
(끝)
```

### 타겟을 같이 쓸까, 따로 쓸까?

```
같은 타겟 사용 (간단, 기본):
─────────────────────────
AimTarget = 적의 위치
Aim Chain Target = AimTarget
Eye Aim Target = AimTarget
→ 몸과 눈이 같은 대상을 봄

다른 타겟 사용 (고급, 리얼리스틱):
──────────────────────────────
Aim Chain Target = 무기가 향하는 방향
Eye Aim Target = 적의 눈/머리 위치
→ 총은 적의 몸통을 조준하지만, 눈은 적의 얼굴을 봄
→ 더 리얼리스틱!

NPC 대화 시:
Aim Chain Target = 대화 상대의 몸
Eye Aim Target = 대화 상대의 눈
→ 몸은 상대를 향하고, 눈은 상대의 눈을 맞춤
→ 실감나는 대화 장면!
```

## 6.6 MetaHuman에서의 Eye Aim

### MetaHuman 특수 사항

```
MetaHuman은 눈 본이 일반 스켈레톤과 다릅니다:

일반 스켈레톤:
└── head
    ├── eye_l  ← 왼쪽 눈
    └── eye_r  ← 오른쪽 눈

MetaHuman:
└── head
    ├── FACIAL_L_Eye  ← 왼쪽 눈
    ├── FACIAL_R_Eye  ← 오른쪽 눈
    ├── (많은 페이셜 본들...)
    └── ...

Quick Setup이 MetaHuman의 본 구조도 자동으로 감지합니다.
만약 자동 감지가 안 되면, 수동으로 본 이름을 지정하세요.
```

### MetaHuman Eye Aim 설정 팁

```
MetaHuman에서 추가로 신경 쓸 점:

1. 눈꺼풀 연동
   - MetaHuman은 눈꺼풀 본이 별도로 있음
   - Eye Aim만으로는 눈꺼풀이 안 따라옴
   - Face Control Rig과 함께 사용 필요

2. 동공 크기
   - FocalRig은 동공 크기를 제어하지 않음
   - 머티리얼 파라미터로 별도 제어

3. 각도 제한을 약간 줄이기
   - MetaHuman은 눈 모델이 정교하므로
   - 극단적 각도에서 홍채가 눈꺼풀 밖으로 보일 수 있음
   - Max Angle을 30° 정도로 제한 권장
```

## 6.7 Eye Aim 디버깅

### 흔한 문제와 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| 눈이 전혀 움직이지 않음 | Eye Bone이 잘못 지정됨 | Quick Setup 재실행 또는 수동 지정 |
| 눈이 반대로 움직임 | Aim Axis가 반대 | Aim Axis 반전 |
| 사팔뜨기가 됨 | Min Distance가 너무 작음 | Min Distance를 100 이상으로 |
| 눈이 너무 빠르게 튐 | Spring Stiffness가 너무 높음 | Stiffness를 10~15로 낮추기 |
| Saccade가 부자연스러움 | Amplitude가 너무 큼 | Amplitude를 0.3~0.5로 |
| 눈만 움직이고 몸은 안 움직임 | Aim Chain이 비활성화됨 | Aim Chain 연결 확인 |

### 디버그 시각화

```
Control Rig 에디터에서:

1. Eye Aim 노드 선택
2. Preview 모드 활성화
3. 뷰포트에서 확인:
   - 눈의 현재 방향 (파란 선)
   - 타겟 위치 (빨간 점)
   - 각도 제한 범위 (원뿔 형태)
   - Saccade 범위 (작은 원)
```

## 6.8 실전 레시피

### 레시피 1: 기본 NPC Eye Contact

```
설정값:
- Target: 플레이어 캐릭터의 Head 본 위치
- Spring Stiffness: 15.0
- Spring Damping: 2.0
- Max Horizontal: 40°
- Max Vertical: 30°
- Min Distance: 80
- Saccade Amplitude: 0.5°
- Saccade Interval: 2.0초

결과: NPC가 플레이어를 자연스럽게 쳐다봄
```

### 레시피 2: 긴장한 적 AI

```
설정값:
- Target: 플레이어 위치
- Spring Stiffness: 25.0
- Spring Damping: 1.5
- Max Horizontal: 50°
- Max Vertical: 40°
- Min Distance: 50
- Saccade Amplitude: 1.0°
- Saccade Interval: 1.0초

결과: 적이 초조하게 플레이어를 경계하는 느낌
```

### 레시피 3: 시네마틱 클로즈업

```
설정값:
- Target: 대화 상대의 눈
- Spring Stiffness: 10.0
- Spring Damping: 3.0
- Max Horizontal: 25°
- Max Vertical: 20°
- Min Distance: 100
- Saccade Amplitude: 0.3°
- Saccade Interval: 2.5초

결과: 영화 같은 자연스러운 아이컨택
```

## 체크리스트

다음 단계로 넘어가기 전에 확인하세요:

- [ ] Eye Aim 노드를 Control Rig에 추가함
- [ ] Quick Setup으로 눈 본이 자동 설정됨
- [ ] 스프링 댐핑 값을 조정해봄
- [ ] Saccade 설정을 이해하고 조정해봄
- [ ] Aim Chain과 Eye Aim의 실행 순서를 이해함
- [ ] 각도 제한과 최소 거리를 설정함

---
[← 이전: Aim Chain 완전 정복](05-Aim-Chain.md) | [다음: Recoil(반동) 시스템 →](07-Recoil-System.md)
