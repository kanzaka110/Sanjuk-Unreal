# 02. AnimNext(UAF) 핵심 개념 이해

[← 이전: 현재 ABP 분석](./01_CURRENT_ABP_ANALYSIS.md) | [목차](./00_INDEX.md) | [다음: 사전 준비 →](./03_PREREQUISITES.md)

---

## 2.1 AnimNext란?

**AnimNext**는 Epic Games가 기존 Animation Blueprint(ABP) 시스템을 완전히 대체하기 위해 개발 중인
**차세대 애니메이션 프레임워크**입니다.

UE 5.7부터 **UAF (Unreal Animation Framework)**로 공식 리브랜딩되었습니다.

### 핵심 설계 철학

```
기존 ABP: 상속 기반 (Inheritance) + 재귀 트리 평가
     ↓
UAF:      컴포지션 기반 (Composition) + 데이터 지향 (Data-Oriented) + 스택 기반 평가
```

| 설계 원칙 | 설명 |
|----------|------|
| **데이터 지향** | 오브젝트가 아닌 데이터 스트림을 중심으로 설계 |
| **컴포지션** | 상속 대신 Trait 조합으로 기능 구성 |
| **고성능** | RigVM 기반 멀티스레드 실행, AnimGameThreadTime 미소비 |
| **유연성** | 플러그인으로 기능 확장 가능 |
| **간결성** | ABP의 복잡한 와이어링 대신 선언적 구성 |

---

## 2.2 ABP vs UAF 전체 비교

### 아키텍처 비교

```
┌─────────────────────────────────────────────────────────────┐
│                    기존 ABP 아키텍처                          │
│                                                              │
│  Character BP                                                │
│    └── SkeletalMeshComponent                                │
│          └── AnimInstance (ABP)                              │
│                ├── EventGraph (변수 설정, 로직)              │
│                └── AnimGraph (애니메이션 트리)               │
│                      ├── State Machine                       │
│                      │     ├── State 1 → Animation          │
│                      │     ├── State 2 → BlendSpace         │
│                      │     └── Transitions (수동 와이어링)   │
│                      ├── Blend Nodes                         │
│                      ├── Aim Offset                          │
│                      └── Output Pose                         │
└─────────────────────────────────────────────────────────────┘

                          ↓ 변환 ↓

┌─────────────────────────────────────────────────────────────┐
│                    UAF 아키텍처                               │
│                                                              │
│  Character BP                                                │
│    ├── SkeletalMeshComponent (애니메이션 OFF)               │
│    └── AnimNextComponent                                     │
│          └── Workspace                                       │
│                ├── System (실행 흐름 정의)                   │
│                ├── Module (로직 작성)                        │
│                │     └── Data Interface (자동 바인딩)        │
│                └── Animation Graph                           │
│                      └── TraitStack                          │
│                            ├── Base Trait (Motion Matching)  │
│                            ├── Additive Trait (Aim Offset)   │
│                            ├── Additive Trait (Lean)         │
│                            └── Additive Trait (Foot IK)     │
└─────────────────────────────────────────────────────────────┘
```

### 상세 비교표

| 영역 | ABP (기존) | UAF (AnimNext) |
|------|-----------|----------------|
| **최상위 에셋** | AnimBlueprint (.uasset) | Workspace |
| **로직 작성** | EventGraph (AnimInstance) | Module |
| **애니메이션 그래프** | AnimGraph (재귀 트리) | Animation Graph (스택 기반) |
| **실행 방식** | 재귀적 트리 순회 | LIFO 스택 기반 깊이 우선 탐색 (MemStack) |
| **스레딩** | 제한적 멀티스레드 | RigVM 기반 완전 멀티스레드 |
| **상태 관리** | 노드 내부 상태 (Stateful) | Trait는 Stateless (워커 스레드 안전) |
| **변수 시스템** | AnimInstance 클래스 변수 | Data Interface (자동 바인딩) |
| **데이터 흐름** | Character → ABP 수동 전달 | Data Interface가 자동 읽기 |
| **애니메이션 선택** | State Machine (수동 트랜지션) | Chooser + Motion Matching |
| **블렌딩** | Blend 노드 트리 | TraitStack 컴포지션 |
| **성능 비용** | AnimGameThreadTime 소비 | AnimGameThreadTime 미소비 |
| **확장** | C++ 노드 클래스 상속 | Trait 플러그인 |

---

## 2.3 핵심 개념 상세 설명

### Concept 1: Workspace (작업 공간)

**ABP에서의 대응**: AnimBlueprint 에셋 자체

Workspace는 UAF의 **최상위 컨테이너**입니다.
하나의 Workspace 안에 System, Module, Animation Graph, 공유 변수가 모두 포함됩니다.

```
Workspace (WS_SandboxCharacter)
  ├── System: 실행 흐름 정의
  ├── Module: 로직 작성
  ├── Animation Graph: 애니메이션 처리
  └── Shared Variables: 공유 변수
```

> **비유**: ABP가 "하나의 큰 건물"이라면, Workspace는 "건물 단지의 마스터 플랜"입니다.
> 각 건물(System, Module, Graph)은 독립적이지만 하나의 플랜으로 관리됩니다.

---

### Concept 2: System (시스템)

**ABP에서의 대응**: BlueprintThreadSafeUpdateAnimation + Update 파이프라인

System은 **실행 순서**를 정의합니다. "무엇을 어떤 순서로 실행할지"를 선언합니다.

```
System 실행 흐름 예시:

1. Reference Pose 생성
2. Trajectory 계산
3. Module 실행 (로직 업데이트)
4. Animation Graph 실행 (포즈 계산)
5. 최종 포즈를 SkeletalMeshComponent에 전달
```

> **비유**: System은 "공장의 생산 라인 설계도"입니다.
> 어떤 공정(Module, Graph)을 어떤 순서로 거칠지 정의합니다.

---

### Concept 3: Module (모듈)

**ABP에서의 대응**: EventGraph + Update 함수들

Module은 **로직을 작성하는 공간**입니다.
기존 ABP의 EventGraph에서 하던 변수 계산, 상태 판정 등을 여기서 수행합니다.

```
기존 ABP:
  EventGraph → Update_EssentialValues() → 53개 노드로 수동 계산

UAF Module:
  Data Interface가 자동으로 값 제공 → 최소한의 추가 계산만 수행
```

**ABP 함수 → Module 매핑:**

| ABP 함수 | Module에서의 처리 |
|----------|------------------|
| `Update_PropertiesFromCharacter` | Data Interface가 자동 대체 → **불필요** |
| `Update_EssentialValues` | 대부분 Data Interface 대체 → **대폭 축소** |
| `Update_States` | Mover에서 직접 읽기 → **축소** |
| `Update_Trajectory` | Pose Search 내장 → **자동화** |
| `Update_MotionMatching` | MM 노드 콜백으로 이동 → **Graph 내 처리** |

> **비유**: Module은 "공장의 품질 관리 부서"입니다.
> 원자재(Data Interface의 데이터)를 받아 가공(로직)하여 생산 라인(Graph)에 전달합니다.

---

### Concept 4: Animation Graph & TraitStack

**ABP에서의 대응**: AnimGraph + Animation Nodes

#### TraitStack이란?

TraitStack은 **1개의 Base Trait + N개의 Additive Trait**로 구성된 스택입니다.
기존 AnimGraph의 복잡한 노드 트리를 **레이어 쌓기**로 단순화합니다.

```
기존 ABP AnimGraph:
  State Machine → Blend → Aim Offset → Lean → Warping → Foot IK → Output
  (각 노드를 와이어로 연결, 복잡한 트리 구조)

UAF TraitStack:
  ┌──────────────────────────────┐
  │  Additive: Foot Placement   │  ← 맨 위 (마지막 적용)
  ├──────────────────────────────┤
  │  Additive: Stride Warping   │
  ├──────────────────────────────┤
  │  Additive: Orient. Warping  │
  ├──────────────────────────────┤
  │  Additive: Lean             │
  ├──────────────────────────────┤
  │  Additive: Aim Offset       │
  ├──────────────────────────────┤
  │  Base: Motion Matching Pose │  ← 맨 아래 (기반 포즈)
  └──────────────────────────────┘
  (스택으로 쌓기, 와이어링 불필요)
```

#### Trait의 종류

| Trait 종류 | 설명 | 예시 |
|-----------|------|------|
| **Base Trait** | 기반 포즈 제공 (1개만 가능) | Motion Matching, Sequence Player |
| **Additive Trait** | 기반 위에 추가 효과 (N개 가능) | Aim Offset, Lean, IK, Warping |

#### Trait의 데이터 구조

```
Trait
  ├── FSharedData      : 읽기 전용, 같은 그래프의 모든 인스턴스가 공유
  ├── FInstanceData    : 인스턴스별 동적 데이터
  └── Latent Property  : 공유 데이터이지만 인스턴스화 필요한 것
```

> **핵심**: Trait는 **Stateless**입니다. 내부 상태를 가질 수 없습니다.
> 이는 워커 스레드에서 안전하게 실행하기 위함입니다.
> 상태가 필요한 데이터는 Module의 변수나 Data Interface에 저장합니다.

> **비유**: TraitStack은 "포토샵의 레이어"와 같습니다.
> Base Layer(기본 이미지) 위에 Adjustment Layer(보정 레이어)를 쌓아가며
> 최종 결과물을 만듭니다. 레이어를 끄고 켜거나, 순서를 바꾸거나,
> 새 레이어를 추가하는 것이 간단합니다.

---

### Concept 5: Data Interface (데이터 인터페이스)

**ABP에서의 대응**: AnimInstance 변수 + 수동 값 전달

Data Interface는 UAF에서 **데이터를 자동으로 주고받는 시스템**입니다.
기존 ABP에서 Character BP → ABP로 수동 전달하던 것을 자동화합니다.

```
기존 ABP:
  Character BP:
    Event Tick
      → Get Anim Instance
        → Cast to SandboxCharacter_CMC_ABP
          → Set Velocity
          → Set Acceleration
          → Set MovementMode
          → ... (수십 개의 Set 호출)

UAF Data Interface:
  AnimNextComponent가 자동으로 바인딩:
    MoverComponent.Velocity      → 자동 읽기
    MoverComponent.Acceleration  → 자동 읽기
    MoverComponent.MovementMode  → 자동 읽기
    → 수동 전달 코드 불필요!
```

### Data Interface 작동 원리

```
┌─────────────────┐         ┌──────────────────┐
│  Character BP   │         │  UAF Workspace   │
│                 │         │                   │
│ MoverComponent ─┼────────▶│ Data Interface    │
│ CapsuleComp.  ─┼────────▶│  (자동 바인딩)    │
│ InputAction   ─┼────────▶│                   │
│                 │         │   Module          │
│                 │         │   Animation Graph │
└─────────────────┘         └──────────────────┘
```

스레드 간 데이터 교환은 `AnimNextComponent::PublicVariablesProxy`를 통해 안전하게 수행됩니다.

> **비유**: Data Interface는 "전기 콘센트"와 같습니다.
> 기존 ABP는 "전선을 직접 납땜"하는 방식이었다면,
> Data Interface는 "콘센트에 플러그만 꽂으면" 자동으로 연결됩니다.

---

### Concept 6: Chooser (선택기)

**ABP에서의 대응**: State Machine의 트랜지션 규칙

Chooser는 **조건 테이블 기반으로 에셋을 선택**하는 시스템입니다.
State Machine의 복잡한 트랜지션 와이어링을 선언적 테이블로 대체합니다.

```
기존 State Machine:
  ┌─────────┐  HasAccel=true   ┌──────────────┐
  │  Idle   │─────────────────▶│  Locomotion  │
  │  Loop   │◀─────────────────│  Loop        │
  └─────────┘  HasAccel=false  └──────────────┘
  (각 트랜지션마다 조건 노드를 와이어링)

UAF Chooser Table:
  ┌──────────────┬────────────┬───────────┬──────────────────┐
  │ MovementMode │ HasAccel   │ IsInAir   │ → Result         │
  ├──────────────┼────────────┼───────────┼──────────────────┤
  │ Walking      │ false      │ false     │ DB_Idle          │
  │ Walking      │ true       │ false     │ DB_Locomotion    │
  │ *            │ *          │ true      │ DB_InAir         │
  └──────────────┴────────────┴───────────┴──────────────────┘
  (테이블 한 장으로 모든 조건 관리)
```

> **비유**: State Machine이 "도로 위의 교통 신호 시스템"이라면,
> Chooser는 "내비게이션의 경로 검색"입니다.
> 복잡한 신호 규칙을 하나하나 설정하는 대신,
> 목적지(조건)를 입력하면 최적 경로(애니메이션)를 자동으로 찾아줍니다.

---

## 2.4 실행 흐름 비교

### 기존 ABP의 매 프레임 실행 흐름

```
1. [Game Thread] AnimInstance::NativeUpdateAnimation()
2. [Game Thread] BlueprintThreadSafeUpdateAnimation(DeltaTime)
     ├── Update_Logic()
     │     ├── Update_CVarDrivenVariables()
     │     ├── Update_PropertiesFromCharacter()
     │     ├── Update_EssentialValues()        ← 53노드 (무거움)
     │     ├── Update_States()                 ← 30노드
     │     └── Update_Trajectory()             ← 27노드
     │
3. [Worker Thread] AnimGraph 평가
     ├── State Machine 평가 (트랜지션 체크)
     ├── Motion Matching (포즈 검색)
     ├── Blend Stack (블렌딩)
     ├── Aim Offset 적용
     ├── Lean 적용
     ├── Warping 적용
     └── Foot Placement 적용

4. [Game Thread] 최종 포즈 → SkeletalMeshComponent
```

### UAF의 매 프레임 실행 흐름

```
1. [Any Thread] AnimNextComponent 업데이트 시작
     │
2. [RigVM Worker] System 실행
     ├── Reference Pose 생성
     ├── Data Interface로 데이터 자동 수집
     ├── Module 실행 (최소한의 로직)
     │     ├── 필요한 추가 계산만 수행
     │     └── Chooser 조건 준비
     │
3. [RigVM Worker] Animation Graph 실행
     ├── Chooser → Pose Search DB 선택
     ├── Motion Matching → 최적 포즈 선택
     └── TraitStack 평가
           ├── Base: Motion Matching Pose
           ├── +Additive: Aim Offset
           ├── +Additive: Lean
           ├── +Additive: Warping
           └── +Additive: Foot Placement

4. [Any Thread] 최종 포즈 → SkeletalMeshComponent
```

**핵심 차이**:
- ABP는 Game Thread에서 많은 로직 실행 → **게임 스레드 부하**
- UAF는 RigVM Worker에서 대부분 실행 → **게임 스레드 부하 최소화**

---

## 2.5 성능 이점

| 영역 | ABP | UAF | 개선 |
|------|-----|-----|------|
| **스레드 사용** | Game Thread 의존 | RigVM 멀티스레드 | 게임 로직과 병렬 실행 |
| **AnimGameThreadTime** | 소비함 | 소비하지 않음 | CPU 프레임 시간 감소 |
| **메모리 레이아웃** | 오브젝트 기반 (캐시 미스) | 연속 메모리 (캐시 친화) | 캐시 효율 향상 |
| **변수 전달** | 수동 Copy (매 프레임) | Data Interface (자동) | 불필요한 복사 제거 |
| **평가 방식** | 재귀 트리 (콜 스택 깊음) | 스택 기반 (flat) | 함수 호출 오버헤드 감소 |

---

## 2.6 현재 상태 및 제한사항 (UE 5.7 기준)

### 상태

| 버전 | 상태 |
|------|------|
| UE 5.4 | 최초 등장, 실험적 플러그인, 문서 없음 |
| UE 5.5 | 실험적, 초기 개발 |
| UE 5.6 | 실험적, 사용 가능하나 불완전, "Modules" 명칭 |
| **UE 5.7** | **실험적, UAF로 리브랜딩, MM 노드 추가** |
| UE 5.8 (예정) | 첫 공식 데모 (Game Animation Sample) |

### 제한사항

1. **공식 문서 부족**: API 레퍼런스만 존재, 튜토리얼/가이드 없음
2. **버전 간 호환성 미보장**: 5.6 ↔ 5.7 간에도 API 변경 발생
3. **에디터 안정성**: 일부 에디터 조작 시 크래시 가능
4. **마이그레이션 도구 없음**: ABP → UAF 자동 변환 불가
5. **커뮤니티 리소스 제한**: 소수의 얼리 어답터 블로그만 존재

### 권장 접근법

```
현재 ABP (프로덕션)          UAF (실험)
┌──────────────────┐      ┌──────────────────┐
│ SandboxCharacter │      │ TestCharacter    │
│ _CMC_ABP         │      │ _UAF_ABP         │
│                  │      │                  │
│ (건드리지 않음)   │      │ (여기서 실험)     │
└──────────────────┘      └──────────────────┘
```

**기존 ABP를 유지하면서 별도 테스트 캐릭터에서 UAF를 실험하세요.**

---

[← 이전: 현재 ABP 분석](./01_CURRENT_ABP_ANALYSIS.md) | [목차](./00_INDEX.md) | [다음: 사전 준비 →](./03_PREREQUISITES.md)
