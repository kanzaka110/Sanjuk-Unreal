# 3. Chaos Cloth 기본 셋업

이 장에서는 **Clothing Tool (기본 방식)**으로 천 시뮬레이션을 처음 만들어봅니다.
두 가지 실습을 포함합니다: 깃발 만들기와 캐릭터 의상 셋업.

## 3.1 메시 준비

### 필요한 것

| 항목 | 설명 | 예시 |
|------|------|------|
| **SkeletalMesh** | 뼈가 있는 3D 모델 | 캐릭터, 깃발 폴대에 달린 깃발 |
| **서브디비전** | 메시에 충분한 삼각형 필요 | 삼각형이 적으면 천이 딱딱해 보임 |
| **리깅** | 스켈레톤에 바인딩되어 있어야 함 | 웨이트 페인팅 완료 상태 |

> **초보자 질문: 왜 StaticMesh가 아니라 SkeletalMesh?**
> Chaos Cloth는 SkeletalMesh의 뼈(Bone) 정보를 사용하여 "어디가 고정이고 어디가 자유인지" 판단합니다. StaticMesh에는 뼈가 없으므로 사용할 수 없습니다.

### Blender에서 간단한 천 메시 만들기

```
1. Blender 실행
2. 평면(Plane) 추가 → 적당한 크기로 스케일
3. Edit 모드 진입 (Tab)
4. 우클릭 → Subdivide (2~3회 반복)
   └─ 삼각형이 충분해야 천이 부드럽게 구부러짐
5. Object 모드로 복귀 (Tab)
6. Ctrl + A → Apply Scale
7. Armature(뼈대) 추가 → 평면에 Parent 설정
8. File → Export → FBX
   └─ Smoothing: "Face"
   └─ "Selected Objects" 체크
```

### UE5로 임포트

```
1. Content Browser에서 Import 클릭 (또는 파일 드래그)
2. FBX Import Options:
   └─ Mesh Type: Skeletal Mesh ← 중요!
   └─ "Reset to Default" 클릭
   └─ Import All
```

> **삼각형 메시도 OK:** Chaos Cloth는 삼각형 메시와 잘 작동합니다. 쿼드로 변환할 필요 없습니다.

## 3.2 Clothing Data 생성 — 단계별 가이드

### Step 1: SkeletalMesh 에디터 열기

```
Content Browser에서 SkeletalMesh를 더블클릭
→ SkeletalMesh 에디터가 열림
```

### Step 2: 섹션에서 Clothing Data 생성

```
1. 뷰포트에서 천으로 만들 메시 영역을 우클릭
   (캐릭터의 경우: 치마, 망토 등의 Section을 우클릭)

2. "Create Clothing Data from Section" 선택

3. 다이얼로그:
   ┌─────────────────────────────┐
   │ Asset Name: [Cloth_Cape]    │ ← 이름 지정
   │ Physics Asset: [PA_Char▼]   │ ← Physics Asset 선택 (중요!)
   │                             │
   │      [Create]  [Cancel]     │
   └─────────────────────────────┘

4. "Create" 클릭
```

> **Physics Asset 선택을 반드시 확인하세요!** 잘못된 Physics Asset을 선택하면 충돌이 동작하지 않습니다.

### Step 3: Cloth Paint 모드 진입

```
1. SkeletalMesh 에디터 상단:
   [Activate Cloth Paint] 버튼 클릭

2. 좌측 패널 → Clothing Data에서 방금 만든 항목 선택
   (예: "Cloth_Cape")

3. 뷰포트가 페인팅 모드로 전환됨
   (메시가 검정색으로 변함 — Max Distance = 0 상태)
```

## 3.3 Max Distance 페인팅 — 가장 중요한 단계!

Max Distance는 "어디가 움직이고 어디가 고정인지"를 결정합니다. 이 페인팅이 천 시뮬레이션의 90%를 결정합니다.

### 페인팅 도구 설명

| 설정 | 용도 | 초보자 추천값 |
|------|------|-------------|
| **Paint Value** | 페인팅할 Max Distance 값 | 10~30으로 시작 |
| **Brush Radius** | 브러시 크기 | 중간 크기 |
| **Brush Strength** | 한 번에 칠해지는 강도 | 0.5~1.0 |
| **Brush Falloff** | 가장자리 부드러움 | 0.5 |

### 페인팅 방법

| 조작 | 동작 |
|------|------|
| **좌클릭 드래그** | 칠하기 (Max Distance 증가) |
| **Shift + 좌클릭** | 지우기 (Max Distance 감소) |
| **Ctrl + 좌클릭** | 부드럽게 (Smooth) |

### Action Type (브러시 모드)

| 모드 | 용도 | 초보자 팁 |
|------|------|----------|
| **Brush** | 자유롭게 칠하기 | 가장 많이 사용 |
| **Gradient** | 그라디언트(위→아래 등) | 치마/망토에 유용 |
| **Fill** | 전체 채우기 | 빠르게 전체 설정 |
| **Smooth** | 페인팅 경계 부드럽게 | 마무리용 |

### 올바른 페인팅 패턴

```
[깃발]                         [캐릭터 망토]

  ■■■■■■ (검정=고정, 깃대쪽)     ■■■■■■ (검정=고정, 어깨)
  ▓▓▓▓▓▓ (회색=전환)            ▓▓▓▓▓▓ (회색=전환)
  ░░░░░░ (밝음=움직임)            ░░░░░░ (밝음=중간)
  □□□□□□ (흰색=최대 자유)        □□□□□□ (흰색=최대 자유, 밑단)


[캐릭터 치마]                    [잘못된 예시]

  ■■■■■■ (검정=고정, 허리)       □□□□□□ (전부 흰색)
  ▓▓▓▓▓▓ (회색=전환)              → 전부 자유 → 천이 떨어짐!
  ░░░░░░ (밝음=움직임)
  □□□□□□ (흰색=최대 자유)       ■□■□■□ (불규칙)
                                  → 경계가 급격 → 찢어지는 느낌!
```

### 핵심 규칙

| 규칙 | 이유 |
|------|------|
| **반드시 고정 영역(검정)을 남겨야 함** | 전부 흰색이면 천이 떨어져 버림 |
| **고정↔자유 사이에 그라디언트** | 급격한 전환은 부자연스러운 접힘 유발 |
| **작은 값부터 시작** | 5~10부터 시작하여 점진적으로 늘리기 |
| **대칭으로 페인팅** | Mirror 옵션 활용 |

## 3.4 Backstop 페인팅

Max Distance를 칠했으면, **Backstop**을 설정하여 안쪽 관통을 방지합니다.

### 설정 방법

```
1. 페인팅 모드에서:
   └─ Paint Type을 "Backstop Distance"로 변경
2. 천이 안쪽으로 들어갈 수 있는 부위를 칠하기:
   └─ 후드 → 머리 쪽
   └─ 치마 → 다리 사이
   └─ 망토 → 등 쪽
3. 값은 작게 시작 (2~5)
```

### 언제 필요한가?

| 상황 | 필요 여부 | 이유 |
|------|:---------:|------|
| 깃발, 커튼 | 거의 불필요 | 안쪽으로 들어갈 몸이 없음 |
| 망토, 코트 | **필요** | 등/어깨를 뚫을 수 있음 |
| 치마, 드레스 | **매우 필요** | 다리 사이로 들어감 |
| 후드 | **필수** | 머리를 뚫고 들어감 |

## 3.5 Clothing Data 적용

페인팅이 끝나면 적용합니다:

```
1. [Deactivate Cloth Paint] 클릭 → 페인팅 모드 종료

2. 뷰포트에서 해당 섹션 우클릭
   └─ "Apply Clothing Data" 선택
   └─ 방금 만든 Cloth 항목 선택

3. Masks 패널 확인:
   └─ ☑ Max Distance  ← 반드시 체크!

4. 저장 (Ctrl + S)
```

> **Max Distance 체크 중요!** 이 체크를 안 하면 천이 끝없이 떨어집니다.

## 3.6 실습 A: 깃발 만들기 (가장 쉬운 예제)

처음 Chaos Cloth를 접한다면 깃발부터 시작하세요.

### 준비물

- 평면 SkeletalMesh (Blender에서 Subdivide된 Plane + Armature)
- 또는 UE5 기본 에셋 활용

### 순서

```
Step 1: 깃발 SkeletalMesh를 레벨에 배치
        └─ 드래그 앤 드롭

Step 2: SkeletalMesh 에디터에서 Clothing Data 생성
        └─ 섹션 우클릭 → Create Clothing Data from Section
        └─ Physics Asset은 깃발용으로 생성 또는 None

Step 3: Max Distance 페인팅
        └─ 깃대에 붙는 쪽 → 검정 (0, 고정)
        └─ 반대쪽으로 갈수록 → 흰색 (자유)
        └─ Gradient 모드가 편함

Step 4: Apply Clothing Data + Max Distance 체크 + 저장

Step 5: 레벨에서 테스트
        └─ Details → Collide with Environment: ☑
        └─ Details → Force Collision Update: ☑
        └─ Play 버튼 오른쪽 [...] → Simulate

Step 6: 바람 추가 (선택)
        └─ Place Actors → All Classes → "Wind Directional Source" 검색
        └─ 방향을 깃발 쪽으로 향하게 배치
        └─ Details → Speed 값 증가
        └─ 시뮬레이트로 확인
```

> 깃발이 펄럭이면 성공입니다!

## 3.7 실습 B: 캐릭터 의상 (치마/로인클로스)

### 순서

```
Step 1: 캐릭터 SkeletalMesh 에디터 열기
        └─ 마네킹 또는 Mixamo 캐릭터

Step 2: Physics Asset 확인/생성
        └─ Content Browser에서 Physics Asset 열기
        └─ 다리(thigh, calf), 몸통(spine)에 캡슐 확인
        └─ Physics Type: Kinematic 확인

Step 3: 의상 섹션에서 Clothing Data 생성
        └─ 치마/로인클로스 Section 우클릭
        └─ Create Clothing Data from Section
        └─ 올바른 Physics Asset 선택!

Step 4: Max Distance 페인팅
        └─ 허리 밴드 → 검정 (고정)
        └─ 허리→무릎 → 그라디언트 (전환)
        └─ 무릎 아래 → 흰색 (자유)

Step 5: Backstop 페인팅
        └─ 다리 안쪽 → Backstop Distance 칠하기
        └─ 다리 사이 관통 방지

Step 6: Apply Clothing Data
        └─ ☑ Max Distance 체크 확인

Step 7: 레벨에서 애니메이션 테스트
        └─ 걷기/달리기 애니메이션 적용
        └─ 치마가 다리를 따라 움직이는지 확인
        └─ 관통 발생 시 → Physics Asset 캡슐 크기 조절
```

## 3.8 시뮬레이션 테스트 방법

### 뷰포트에서 빠른 테스트

```
SkeletalMesh 에디터에서:
1. 상단 메뉴 → Show → Clothing Simulation 체크
2. 또는 뷰포트 좌측 → Enable Cloth Simulation 토글

Preview 설정:
1. Preview Scene 탭 열기
2. Skeletal Mesh에 캐릭터 메시 지정
3. Animation에 테스트할 애니메이션 지정
4. Play 버튼 클릭 → 시뮬레이션 미리보기
```

### 레벨에서 테스트

```
1. SkeletalMesh를 레벨에 배치
2. Play 버튼 옆 [...] → Simulate 선택
3. 실시간으로 천 움직임 확인
```

### 처음 테스트에서 자주 발생하는 문제

| 증상 | 원인 | 해결 |
|------|------|------|
| 아무 변화 없음 | Cloth Paint를 Apply 안 함 | Apply Clothing Data 확인 |
| 아무 변화 없음 | Max Distance 체크 안 됨 | Masks → ☑ Max Distance |
| 천이 바닥으로 떨어짐 | 고정 영역(검정)이 없음 | 허리/어깨를 검정으로 칠하기 |
| 천이 몸을 뚫음 | Physics Asset 없거나 캡슐 작음 | Physics Asset 확인, 캡슐 키우기 |
| 에디터 크래시 | UE 버전 문제 | 최신 패치 설치, 시뮬 끄고 저장 후 재시작 |

## 3.9 Panel Cloth 방식 (맛보기)

기본 Clothing Tool과 별도로, **Panel Cloth** (Dataflow) 방식이 있습니다.
이 방식은 5장(파라미터 튜닝)과 6장(멀티레이어)에서 더 자세히 다룹니다.

### 기본 흐름만 소개

```
1. Content Browser 우클릭 → Physics → Chaos Cloth Asset
2. Dataflow 그래프 에디터가 열림
3. 노드로 워크플로우 구성:
   ┌──────────────┐     ┌──────────────┐     ┌────────────────┐
   │ USD Import   │ ──→ │ WeightMap    │ ──→ │ SimulationSolve│
   │ 또는         │     │ MaxDistance  │     │ ConfigLod0     │
   │ Static Mesh  │     │ (페인팅)     │     │ (시뮬 파라미터)│
   │ Import       │     └──────────────┘     └────────────────┘
   └──────────────┘              │
                                 ↓
                        ┌──────────────┐
                        │ PhysicsAsset │
                        │ (충돌 설정)   │
                        └──────────────┘
```

> **초보자는 기본 Clothing Tool로 충분합니다.** Panel Cloth는 복잡한 의류, 멀티레이어, DCC 연동이 필요할 때 사용하세요.

## 체크리스트

- [ ] SkeletalMesh 에디터에서 Clothing Data 생성 성공
- [ ] Cloth Paint 모드 진입 및 Max Distance 페인팅 완료
- [ ] 고정 영역(검정) + 그라디언트 + 자유 영역(흰색) 패턴 이해
- [ ] Apply Clothing Data + Max Distance 체크 완료
- [ ] 실습 A (깃발) 또는 실습 B (캐릭터 의상) 완료
- [ ] 뷰포트/레벨에서 시뮬레이션 테스트 성공

---
[← 이전: Physics Asset 기초](02-Physics-Asset-Basics.md) | [다음: 충돌 설정 →](04-Collision-Config.md)
