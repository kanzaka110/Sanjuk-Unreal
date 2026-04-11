# 4. 충돌 설정 — Physics Asset ↔ Chaos Cloth 연결

## 4.1 충돌이 왜 중요한가?

충돌 설정이 없으면 천이 캐릭터 몸을 **그대로 뚫고 들어갑니다.**
이 장에서는 천이 몸에 자연스럽게 걸리도록 만드는 방법을 배웁니다.

```
[충돌 없음]              [충돌 설정 완료]

  망토가 등을 뚫음         망토가 등에 걸림
  치마가 다리를 뚫음       치마가 다리 위에 걸림
       😱                      😊
```

### 충돌의 두 가지 계층

| 계층 | 역할 | 무엇을 막나? |
|------|------|------------|
| **Physics Asset 충돌** | 천 ↔ 캐릭터 몸 | 천이 캐릭터를 뚫는 것 |
| **Self Collision** | 천 ↔ 천 자체 | 천끼리 겹치는 것 |

> **초보자는 Physics Asset 충돌만 신경 쓰면 됩니다.** Self Collision은 성능 비용이 높으므로 나중에 필요할 때 켜세요.

## 4.2 기본 충돌 — 자동으로 동작하는 것

좋은 소식: Chaos Cloth는 **같은 SkeletalMeshComponent의 Physics Asset을 자동으로 참조**합니다.

### 자동 충돌이 동작하려면?

```
✅ SkeletalMesh에 Physics Asset이 할당되어 있음
✅ Physics Asset에 Capsule/Sphere 바디가 있음
✅ 바디의 Physics Type이 Kinematic임
✅ Clothing Data 생성 시 올바른 Physics Asset을 선택했음
```

### 확인 방법

```
1. SkeletalMesh 에디터 열기
2. Asset Details 탭 → Physics 섹션
3. Physics Asset 필드에 에셋이 할당되어 있는지 확인
   └─ 비어있으면: 드롭다운에서 Physics Asset 선택
```

## 4.3 충돌이 안 될 때 — 체크리스트

가장 흔한 문제와 해결법입니다:

| # | 확인 사항 | 확인 방법 | 해결 |
|---|----------|----------|------|
| 1 | Physics Asset이 할당되어 있나? | SkeletalMesh → Asset Details → Physics | Physics Asset 할당 |
| 2 | 해당 본에 바디가 있나? | Physics Asset 에디터에서 확인 | Capsule 추가 |
| 3 | 바디가 너무 작지 않나? | 뷰포트에서 와이어프레임 확인 | 크기 키우기 |
| 4 | Physics Type이 Kinematic인가? | Details → Physics → Physics Type | Kinematic으로 변경 |
| 5 | Clothing Data에서 맞는 Physics Asset을 선택했나? | Clothing Data 재생성 | 올바른 것 선택 |

## 4.4 충돌 캡슐 조절하기 — 실전 가이드

### 관통 부위별 대응

| 관통 부위 | 추가할 바디 | 크기 팁 |
|----------|-----------|--------|
| 등을 뚫는 망토 | spine_01, spine_02, spine_03에 Capsule | 등 쪽으로 약간 크게 |
| 어깨를 뚫는 망토 | upperarm_l/r에 Capsule | 어깨 너비만큼 |
| 다리 사이 치마 | thigh_l/r에 Capsule | 다리 굵기에 맞게 |
| 머리를 뚫는 후드 | head에 Sphere | 머리카락 포함하여 크게 |
| 팔을 뚫는 소매 | lowerarm_l/r에 Capsule | 팔뚝에 맞게 |

### 조절 워크플로우

```
반복 과정:
1. 시뮬레이션 재생 → 관통 발생 지점 확인
         ↓
2. Physics Asset 에디터 열기
         ↓
3. 관통 부위 본에 바디 추가 또는 크기 키우기
         ↓
4. 저장 → 다시 시뮬레이션 테스트
         ↓
5. 관통이 사라질 때까지 반복
```

> **팁:** 시뮬레이션이 켜진 상태에서 Physics Asset을 변경하면 크래시가 발생할 수 있습니다. **시뮬레이션을 끄고 저장한 후** 수정하세요.

## 4.5 Collision Thickness (충돌 두께)

Collision Thickness는 **콜리전 표면에서 추가로 확장되는 두께**입니다.
캡슐 크기 + Thickness = 실제 충돌 범위.

```
[기본 Thickness = 2.5mm]        [Thickness = 5mm]

  ┌──캡슐──┐                     ┌──캡슐──┐
  │ ┃    ┃ │ 2.5mm 간격          │  ┃    ┃  │ 5mm 간격
  │ ┃ 몸 ┃ │                     │  ┃ 몸 ┃  │
  │ ┃    ┃ │                     │  ┃    ┃  │
  └────────┘                     └──────────┘
  천이 바로 붙음                   천이 떠있음
```

### 언제 변경하나?

| 상황 | Thickness | 이유 |
|------|-----------|------|
| 단일 레이어 (셔츠 하나) | 2.5~3mm (기본값) | 몸에 밀착 |
| 두 겹 의상 (셔츠+재킷) | **5mm** | 레이어 간 간격 필요 |
| 두꺼운 코트, 갑옷 | **5~8mm** | 두께감 표현 |

### 설정 방법

```
Clothing Tool:
  SkeletalMesh 에디터 → Cloth Config → Collision Thickness Outer

Panel Cloth (Dataflow):
  SimulationSolveConfig 노드 → Collision Thickness
```

## 4.6 격리된 콜리전 세트 (중급)

AAA 게임에서는 **천 오브젝트마다 다른 콜리전 캡슐 세트**를 사용합니다.

### 왜 격리가 필요한가?

```
[통합 Physics Asset]               [격리된 콜리전 세트]

  망토가 손가락 캡슐에 걸림          망토는 어깨+등 캡슐만 사용
  불필요한 충돌 발생                  깔끔하고 성능 효율적
  성능 낭비                          레이어별 독립 제어
       ❌                                 ✅
```

### 격리 예시

```
망토 (Cape) → 콜리전 세트 A
├── head: Sphere
├── neck_01: Capsule
├── spine_03: Capsule
└── upperarm_l/r: Capsule (확장)

후드 (Hood) → 콜리전 세트 B
├── head: Sphere (큰 크기 — 머리카락 포함)
└── neck_01: Capsule (작은 크기)

치마 (Skirt) → 콜리전 세트 C
├── pelvis: Capsule
├── thigh_l/r: Capsule
└── calf_l/r: Capsule
```

> **같은 head 본이라도** 망토용(작은 Sphere)과 후드용(큰 Sphere)에서 크기가 다릅니다.

> **초보자 팁:** 처음에는 통합 Physics Asset으로 시작하고, 문제가 생기면 격리를 고려하세요. Panel Cloth (Dataflow)에서 격리 설정이 더 쉽습니다.

## 4.7 Self Collision (자기 충돌)

Self Collision은 **천의 다른 부분끼리 겹치지 않도록** 합니다.

### 효과

```
[Self Collision OFF]             [Self Collision ON]

  치마가 다리 사이로               치마가 다리에 걸려서
  찌그러져 들어감                   자연스럽게 펼쳐짐
       😕                              😊
```

### 장단점

| 항목 | 설명 |
|------|------|
| **장점** | 천끼리 자연스러운 접힘, 관통 방지 |
| **단점** | **성능 비용이 매우 높음** (O(n²) 수준) |

### 추천 사용 전략

```
[사용 O]  치마, 드레스 (넓은 면적)
[사용 O]  주인공의 핵심 의상
[사용 X]  작은 장식, 리본 → 차이 미미
[사용 X]  배경 NPC → 보이지도 않음
[사용 X]  LOD 1 이상 → 거리에서 차이 없음
```

### 대안: Buckling Stiffness

Self Collision 없이도 자기 교차를 줄이는 방법:

| 방법 | 성능 비용 | 효과 |
|------|----------|------|
| Self Collision ON | 높음 | 완전 방지 |
| **Buckling Stiffness** 높이기 | **거의 없음** | 부분 방지 |
| Backstop 강화 | 없음 | 안쪽 관통만 방지 |

> Buckling Stiffness는 천이 접힐 때 자기 교차를 방지하는 강성입니다. Self Collision의 100% 대체는 아니지만, **성능 대비 효과가 뛰어납니다.**

## 4.8 충돌 시각화 (디버깅)

### 에디터에서 충돌 볼륨 보기

```
뷰포트 메뉴:
  Show → Clothing → Show Collision Volumes

결과:
  캡슐/구체가 와이어프레임으로 표시됨
  천 파티클과 겹치는 부분을 시각적으로 확인 가능
```

### 디버깅 순서

```
1. Show Collision Volumes 켜기
2. 시뮬레이션 재생
3. 관통이 발생하는 곳 관찰:
   └─ 캡슐이 없는 곳? → 캡슐 추가
   └─ 캡슐이 작은 곳? → 크기 키우기
   └─ 캡슐이 있는데 뚫림? → Iteration Count 올리기 (5장 참조)
```

## 체크리스트

- [ ] 기본 충돌이 자동으로 동작하는 조건 이해
- [ ] 관통 발생 시 캡슐 추가/크기 조절로 해결 가능
- [ ] Collision Thickness 개념 이해
- [ ] Self Collision의 장단점 이해
- [ ] 충돌 시각화(Show Collision Volumes) 사용법 파악

---
[← 이전: Chaos Cloth 기본 셋업](03-Cloth-Setup.md) | [다음: 파라미터 튜닝 →](05-Parameter-Tuning.md)
