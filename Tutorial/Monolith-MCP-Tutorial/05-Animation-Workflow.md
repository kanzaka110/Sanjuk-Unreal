# 5. 애니메이션 워크플로우

## 5.1 AnimSequence 작업

### 시퀀스 조회

```
프로젝트의 모든 AnimSequence를 나열해줘
```

### 본 트랙 편집

```
Walk_Fwd 애니메이션의 본 트랙 정보를 보여줘
```

### 커브 추가/편집

```
Run_Fwd 애니메이션에 "Speed" 플로트 커브를 추가해줘.
0초에 0, 0.5초에 300, 1초에 600 값으로 설정해줘
```

### 노티파이 관리

```
Walk_Fwd에 다음 Notify를 추가해줘:
- 0.2초: Footstep_L (AnimNotify)
- 0.7초: Footstep_R (AnimNotify)
```

### 싱크 마커

```
Walk_Fwd의 0.0초와 0.5초에 "FootSync" 싱크 마커를 추가해줘.
이렇게 하면 BlendSpace에서 발 동기화가 됩니다
```

## 5.2 AnimMontage 작업

### Montage 생성

```
다음 설정으로 AnimMontage를 만들어줘:
- 이름: AM_Attack_Combo
- 슬롯: DefaultSlot.UpperBody
- 소스 애니메이션: Attack_Light
- 블렌드 인: 0.25초
- 블렌드 아웃: 0.25초
```

### 섹션 추가

```
AM_Attack_Combo에 다음 섹션들을 추가해줘:
1. "Windup" (0초 ~ 0.3초)
2. "Strike" (0.3초 ~ 0.7초)
3. "Recovery" (0.7초 ~ 1.0초)

그리고 "Strike" → "Recovery" 순서로 자동 이동하게 설정해줘
```

### 몽타주에 애님 세그먼트 추가

```
AM_Attack_Combo의 "Strike" 섹션에
Attack_Heavy 애니메이션 세그먼트를 추가해줘.
시작 시간 0.3초, 길이 0.5초로 설정
```

### 블렌딩 설정

```
AM_Attack_Combo의 블렌딩 설정을 변경해줘:
- 블렌드 인: Cubic (0.2초)
- 블렌드 아웃: Linear (0.3초)
```

## 5.3 BlendSpace 작업

### 1D BlendSpace 생성

```
1D BlendSpace를 만들어줘:
이름: BS_Locomotion_1D
스켈레톤: SK_Mannequin
축: Speed (min: 0, max: 600)

샘플:
- 0: Idle
- 150: Walk_Fwd
- 300: Jog_Fwd
- 600: Run_Fwd
```

### 2D BlendSpace 생성

```
2D BlendSpace를 만들어줘:
이름: BS_Locomotion_2D
스켈레톤: SK_Mannequin

X축: Direction (min: -180, max: 180)
Y축: Speed (min: 0, max: 600)

샘플:
- (0, 0): Idle
- (0, 300): Walk_Fwd
- (0, 600): Run_Fwd
- (-90, 300): Walk_Left
- (90, 300): Walk_Right
- (180, 300): Walk_Bwd
```

### Aim Offset 생성

```
Aim Offset을 만들어줘:
이름: AO_AimOffset
스켈레톤: SK_Mannequin

X축: Yaw (min: -90, max: 90)
Y축: Pitch (min: -90, max: 90)

샘플:
- (0, 0): AimCenter
- (0, 45): AimUp
- (0, -45): AimDown
- (-90, 0): AimLeft
- (90, 0): AimRight
```

### 샘플 포인트 수정

```
BS_Locomotion_1D의 Speed 200 지점에 있는 샘플을
Walk_Fwd에서 Walk_Slow로 교체해줘
```

## 5.4 실전: 로코모션 시스템 한번에 만들기

하나의 프롬프트로 전체 로코모션 시스템을 구축할 수 있습니다:

```
캐릭터 로코모션 시스템을 만들어줘:

1. 1D BlendSpace "BS_Movement":
   - Idle (0), Walk (200), Jog (400), Sprint (600)

2. Aim Offset "AO_Aim":
   - 상하좌우 5방향

3. AnimMontage "AM_Jump":
   - 섹션: Launch, Air, Land
   - 블렌드 인/아웃: 0.15초

모든 에셋은 /Game/Characters/Animations/ 폴더에 만들어줘
```

> 💡 **팁**: AI가 에셋을 찾지 못하면 정확한 에셋 경로를 알려주세요.
> Content Browser에서 에셋을 우클릭 → "Copy Reference"로 경로를 복사할 수 있습니다.

## 체크리스트

- [ ] AnimSequence에 노티파이/커브 추가 성공
- [ ] AnimMontage 생성 및 섹션 설정 성공
- [ ] BlendSpace 생성 및 샘플 포인트 배치 성공
- [ ] UE 에디터에서 모든 에셋 확인 및 저장

---
[← 이전: 기본 사용법](04-Basic-Usage.md) | [다음: Animation Blueprint →](06-Animation-Blueprint.md)
