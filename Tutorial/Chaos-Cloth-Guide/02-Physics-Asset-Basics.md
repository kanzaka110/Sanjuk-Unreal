# 2. Physics Asset 기초

## 2.1 Physics Asset이란?

Physics Asset은 SkeletalMesh(캐릭터 모델)에 부착되는 **보이지 않는 충돌 볼륨의 모음**입니다.

쉽게 말하면, 캐릭터 몸 주위에 **투명한 캡슐과 구체를 감싸서**, 천 시뮬레이션이 "여기가 몸이니까 뚫고 들어가면 안 돼!"라고 인식하게 만드는 것입니다.

```
[Physics Asset 없이]              [Physics Asset 있을 때]

  천이 캐릭터 몸을                  천이 캡슐에 막혀서
  뚫고 들어감                       몸 위에 자연스럽게 걸림

    😱 관통!                          😊 자연스러움!
```

> Physics Asset은 원래 래그돌(사망 시 물리 반응)에도 쓰이지만, Chaos Cloth에서는 **충돌 경계** 역할을 합니다.

## 2.2 콜리전 바디 유형

Physics Asset에서 사용하는 충돌 형태(Shape)의 종류입니다:

| 바디 유형 | 모양 | 권장 부위 | Cloth 호환 | 초보자 팁 |
|-----------|------|-----------|:---------:|----------|
| **Capsule** | 원통 + 반구 양끝 | 팔, 다리, 몸통, 목 | 최적 | **가장 많이 씀! 기본은 이것** |
| **Sphere** | 구체 | 머리, 관절 | 좋음 | 둥근 부위에 사용 |
| **Tapered Capsule** | 굵기 변하는 캡슐 | 허벅지→무릎 | 좋음 | UE 5.3 이상만 |
| **Convex Hull** | 메시 기반 볼록 형태 | — | **비추천** | Cloth와 불안정! |
| **Box** | 직육면체 | — | **비추천** | Cloth에 부적합 |

### 바디 배치 예시

```
     ○ head       → Sphere
     ║ neck_01    → Capsule
   ┌═══┐ spine_03 → Capsule
   │   │ spine_02 → Capsule
   │   │ spine_01 → Capsule
   └═══┘
  ╱    ╲
 ║      ║ upperarm_l/r → Capsule
 ║      ║ lowerarm_l/r → Capsule
  ╲    ╱
   ║  ║ thigh_l/r → Capsule (또는 Tapered)
   ║  ║ calf_l/r  → Capsule
```

> Cloth 충돌에 **모든 본에 바디를 넣을 필요는 없습니다.** 천이 닿는 부위에만 넣으면 됩니다.

## 2.3 Physics Asset 만들기 — 단계별 가이드

### Step 1: Physics Asset 생성

```
Content Browser에서:
1. SkeletalMesh (캐릭터 모델) 찾기
2. 우클릭 → Create → Physics Asset → Create Asset
3. 이름 지정 (예: PA_MyCharacter)
4. "Minimum Bone Size" 설정 — 작은 값일수록 더 많은 본에 바디 생성
   └─ 처음에는 기본값으로 시작
```

### Step 2: Physics Asset 에디터 열기

```
1. 생성된 Physics Asset을 더블클릭
2. Physics Asset 에디터가 열림:
   ┌────────────────────────────────────────────────┐
   │  [Skeleton Tree]  │  [3D 뷰포트]               │
   │                   │                             │
   │  ○ root           │    캐릭터 + 와이어프레임     │
   │  ├─ pelvis        │    캡슐/구체가 보임          │
   │  ├─ spine_01      │                             │
   │  ├─ spine_02      │                             │
   │  └─ ...           │                             │
   │                   │                             │
   │  [Details 패널]   │                             │
   │  Physics Type:    │                             │
   │  Collision:       │                             │
   └────────────────────────────────────────────────┘
```

### Step 3: 바디 추가/삭제

```
바디 추가:
1. Skeleton Tree에서 본(Bone) 이름 우클릭
2. Add Body 클릭
3. 바디 유형 선택 (Capsule 권장)
4. 뷰포트에서 크기/위치/회전 조절

바디 삭제:
1. Skeleton Tree에서 바디 선택
2. Delete 키
```

### Step 4: 크기 조절

뷰포트에서 바디를 선택하고 **이동/회전/스케일 도구**로 조절합니다:

| 도구 | 단축키 | 용도 |
|------|--------|------|
| 이동 (Move) | W | 캡슐 위치 이동 |
| 회전 (Rotate) | E | 캡슐 방향 회전 |
| 스케일 (Scale) | R | 캡슐 크기 조절 |

## 2.4 크기 조절 — 핵심 원칙

### 올바른 크기

```
[너무 크다]           [적당하다]           [너무 작다]
  ┌──────┐             ┌────┐              ┌──┐
  │      │             │    │              │  │
  │  몸  │             │ 몸 │              │몸│
  │      │             │    │              │  │
  └──────┘             └────┘              └──┘
  천이 뻣뻣해짐        천이 자연스러움       천이 뚫고 들어감
      ❌                  ✅                   ❌
```

| 원칙 | 설명 | 이유 |
|------|------|------|
| **메시보다 약간 작게** | 캐릭터 실루엣 안쪽으로 | 천이 살짝 떠야 자연스러움 |
| **관절 겹침 최소화** | 팔꿈치, 무릎에서 캡슐이 겹치지 않게 | 천이 끼이는 것 방지 |
| **필요한 부위만** | 천이 닿지 않는 곳은 빈칸으로 | 성능 절약 |

> **초보자 팁:** 처음에는 자동 생성된 상태로 시작하고, 천 시뮬레이션을 테스트하면서 관통이 발생하는 부위의 캡슐만 키우세요.

## 2.5 Physics Type 설정 — 반드시 Kinematic!

Cloth 충돌용 바디는 **Kinematic**이어야 합니다. 이것이 가장 중요합니다.

| Physics Type | 의미 | Cloth에서 사용 |
|-------------|------|:--------------:|
| **Kinematic** | 애니메이션을 따라 이동 (물리 무시) | **사용** |
| **Simulated** | 중력/충돌에 반응 (래그돌) | 미사용 |
| **Default** | 프로필에 따라 결정 | 상황에 따라 |

### 설정 방법

```
1. Physics Asset 에디터에서 바디 선택
2. Details 패널 → Physics 섹션
3. Physics Type → Kinematic 선택
```

> **왜 Kinematic?** Simulated로 설정하면 바디가 중력에 의해 떨어져서 천 충돌이 제대로 동작하지 않습니다. Kinematic은 "애니메이션을 따라 움직이되, 물리는 무시"하는 모드입니다.

## 2.6 자동 생성 vs 수동 설정

| 방법 | 장점 | 단점 | 추천 |
|------|------|------|------|
| **자동 생성** (Create Asset 시 기본 설정) | 빠름, 모든 본에 바디 | 불필요한 바디 많음, 크기 부정확 | 초보자 시작점 |
| **수동 설정** (필요한 본에만 추가) | 정밀, 성능 좋음 | 시간 소요 | 경험자 추천 |
| **자동 → 수동 수정** | 빠른 시작 + 정밀 조절 | — | **가장 추천** |

### 추천 워크플로우

```
1. Physics Asset 자동 생성 (기본 설정)
         ↓
2. 불필요한 바디 삭제 (손가락, 발가락 등 천이 안 닿는 곳)
         ↓
3. 남은 바디의 크기를 메시에 맞게 조절
         ↓
4. Physics Type을 모두 Kinematic으로 확인
         ↓
5. 저장
```

## 2.7 실습: 마네킹의 Physics Asset 확인하기

UE5에 기본 포함된 마네킹(SK_Mannequin)으로 연습해보세요:

```
1. Content Browser → Characters/Mannequins/Meshes/
2. SK_Mannequin을 찾아 우클릭
3. Create → Physics Asset 선택 (이미 있으면 기존 것 열기)
4. Physics Asset 에디터에서:
   - Skeleton Tree의 각 본을 클릭하여 바디 확인
   - 뷰포트에서 와이어프레임 캡슐 관찰
   - 손가락 등 불필요한 바디 선택 후 Delete
   - spine_01~03 캡슐을 선택하고 크기 조절 연습
5. 저장
```

## 2.8 MetaHuman용 Physics Asset 팁

MetaHuman 캐릭터를 사용할 경우 추가 팁:

| 방법 | 설명 | 장점 |
|------|------|------|
| **SK_body에서 Physics Asset 생성** | MetaHuman 바디 메시에서 직접 생성 | 가장 간단 |
| **Static Mesh 키네마틱 콜라이더** | SK_body를 Static Mesh로 변환하여 콜라이더로 사용 | 더 정밀한 충돌 |
| **LOD3 활용** | MetaHuman LOD3(저해상도)를 콜라이더로 사용 | 성능 효율적 |

### Static Mesh 콜라이더 만들기 (고급)

```
1. SK_body 열기
2. 상단 메뉴 → Make Static Mesh 클릭
3. 저장 위치 지정
4. 생성된 Static Mesh를 Chaos Cloth Dataflow에서 콜라이더로 사용
   (Kinematic Collider 노드 연결)
```

> 이 방법은 Panel Cloth / Dataflow 방식에서 사용합니다. 기본 Clothing Tool에서는 Physics Asset만으로 충분합니다.

## 체크리스트

- [ ] Physics Asset의 역할 이해 (천이 몸을 뚫지 않게 하는 충돌 볼륨)
- [ ] Capsule, Sphere의 차이 이해
- [ ] Physics Asset 에디터를 열고 바디를 추가/삭제할 수 있음
- [ ] 크기 조절 원칙 이해 (메시보다 약간 작게)
- [ ] Physics Type을 Kinematic으로 설정하는 이유 이해

---
[← 이전: Chaos Cloth 개요](01-Overview.md) | [다음: Chaos Cloth 기본 셋업 →](03-Cloth-Setup.md)
