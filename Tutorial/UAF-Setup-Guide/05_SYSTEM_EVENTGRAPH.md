# 05. System EventGraph

[<- 이전: 단계별 셋업](./04_STEP_BY_STEP_SETUP.md) | [목차](./00_INDEX.md) | [다음: Animation Graph ->](./06_ANIMATION_GRAPH.md)

---

## 5.1 System EventGraph란?

System은 ABP의 **EventGraph**에 해당합니다.
두 개의 이벤트 노드가 기본 제공됩니다:

| 이벤트 | 실행 시점 | ABP 대응 |
|--------|---------|---------|
| **Initialize** | 시스템 시작 시 **1회** | `NativeInitializeAnimation()` |
| **PrePhysics** | 매 프레임 물리 시뮬레이션 **전** | `BlueprintThreadSafeUpdateAnimation()` |

---

## 5.2 Initialize 이벤트 구성

시스템 초기화 시 기본 포즈를 생성합니다.

```
[Initialize]
     |
     v
[Make Reference Pose]     <- 스켈레톤의 바인드/레퍼런스 포즈 생성
```

### 설정 방법
1. Initialize 노드의 실행 핀(>) 에서 **드래그**
2. `Make Reference Pose` 검색 -> 선택
3. 완료

---

## 5.3 PrePhysics 이벤트 구성

매 프레임 애니메이션을 업데이트합니다.

### 최소 구성 (Motion Matching 없이)
```
[PrePhysics]
     |
     v
[Evaluate Animation Graph]     <- AG_MyCharacter 실행
     |  (Details에서 Graph 에셋 할당)
     v
[Write Pose to Mesh]           <- 최종 포즈를 메시에 적용
```

### 풀 구성 (Motion Matching + Mover)
```
[PrePhysics]
     |
     v
[Calculate Trajectory]          <- Mover에서 궤적 데이터 생성
     |  (Motion Matching에 필요)
     v
[Evaluate Animation Graph]      <- AG_MyCharacter 실행
     |
     v
[Write Pose to Mesh]            <- 최종 포즈 적용
```

---

## 5.4 주요 System 노드 설명

### Make Reference Pose
- **역할**: 스켈레톤의 기본 레퍼런스 포즈를 생성
- **위치**: Initialize 이벤트
- **필수 여부**: 필수 (없으면 포즈 없이 시작)

### Calculate Trajectory
- **역할**: 캐릭터의 과거/현재/미래 이동 궤적을 계산
- **위치**: PrePhysics 이벤트 (Evaluate 전)
- **데이터 소스**: MoverComponent의 Velocity, Acceleration, MovementMode
- **용도**: Motion Matching이 최적 애니메이션을 찾는 데 사용
- **필수 여부**: Motion Matching 사용 시 필수

### Evaluate Animation Graph
- **역할**: 지정된 Animation Graph를 실행하여 포즈 생성
- **위치**: PrePhysics 이벤트
- **설정**: Details 패널에서 `AG_MyCharacter` 할당
- **내부 동작**: `FRigUnit_AnimNextRunAnimationGraph_v2_Execute()` 호출
- **필수 여부**: 필수

### Write Pose to Mesh
- **역할**: 계산된 최종 포즈를 SkeletalMeshComponent에 적용
- **위치**: PrePhysics 이벤트 (Evaluate 후, 항상 마지막)
- **필수 여부**: 필수

### Execute Module
- **역할**: 지정된 Module의 로직 그래프를 실행
- **위치**: PrePhysics 이벤트 (Evaluate 전)
- **용도**: 비즈니스 로직 처리 (파생 변수 계산 등)
- **필수 여부**: 선택 (로직이 필요한 경우)

---

## 5.5 노드 연결 순서 규칙

```
반드시 이 순서를 지켜야 합니다:

1. [Calculate Trajectory]      <- 궤적 먼저 (MM이 사용)
2. [Execute Module]            <- 로직 처리 (선택)
3. [Evaluate Animation Graph]  <- 애니메이션 평가
4. [Write Pose to Mesh]        <- 항상 마지막!
```

### ABP와의 실행 순서 비교

```
ABP:                              UAF System:
+---------------------------+     +---------------------------+
| NativeUpdateAnimation     |     | Initialize:               |
|   v                       |     |   Make Reference Pose     |
| ThreadSafeUpdate          |     +---------------------------+
|   v                       |  =  | PrePhysics:               |
| Update_Logic              |     |   Calculate Trajectory    |
|   v                       |     |   Execute Module          |
| AnimGraph 평가             |     |   Evaluate Animation Graph|
|   v                       |     |   Write Pose to Mesh      |
| 포즈 -> SMC               |     +---------------------------+
+---------------------------+
```

---

## 5.6 Variable Bindings 상세

System은 외부 컴포넌트에 접근하기 위해 **바인딩**을 사용합니다.
이전 ABP의 `Get Owning Actor -> Cast -> Get Component` 패턴을 대체합니다.

### 바인딩 타입

| 타입 | 설명 | 예시 |
|------|------|------|
| **Current Actor** | 소유 Actor 참조 | Actor 자체 |
| **Component** | Actor의 특정 컴포넌트 | MoverComponent |
| **Property** | 컴포넌트/Actor의 프로퍼티 | Velocity |
| **Function** | 함수 호출 결과 | GetSkeletalMeshComponent() |
| **Asset** | 에셋 참조 | PoseSearchDatabase |
| **Cast** | 타입 캐스트 | Cast to MyCharacter |

### 바인딩 추가 절차
1. System의 Details 패널에서 바인딩 섹션 찾기
2. **+** 버튼으로 새 바인딩 추가
3. 변수 이름 입력 (예: `Mover_Component`)
4. 타입 선택 (예: `Mover Component`)
5. 바인딩 소스 설정:
   - 드롭다운 클릭 -> **Add a New Locator Fragment**
   - **Current Actor** 선택 (소유 Actor에서 시작)
   - -> **Component** 선택 (컴포넌트 접근)
   - 컴포넌트 클래스 지정

---

## 5.7 컴파일 에러 해결

### "빨간 노드" 문제
- **원인**: 참조 에셋 누락 또는 바인딩 미설정
- **해결**:
  1. 노드 클릭 -> Details에서 에러 메시지 확인
  2. 누락된 에셋 할당 (예: AG_ 에셋)
  3. 바인딩 소스 설정

### "빈 노드" 컴파일 에러
- **원인**: Initialize/PrePhysics에 아무 노드도 연결하지 않음
- **해결**: 최소 1개 노드라도 연결 (예: Make Reference Pose)

### 컴파일 버튼 위치
- Workspace 에디터 상단 툴바의 **Compile** 버튼

---

[<- 이전: 단계별 셋업](./04_STEP_BY_STEP_SETUP.md) | [목차](./00_INDEX.md) | [다음: Animation Graph ->](./06_ANIMATION_GRAPH.md)
