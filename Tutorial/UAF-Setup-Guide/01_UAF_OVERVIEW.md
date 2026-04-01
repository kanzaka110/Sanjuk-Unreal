# 01. UAF 개요

[목차로 돌아가기](./00_INDEX.md) | [다음: 플러그인 설정 ->](./02_PLUGIN_SETUP.md)

---

## 1.1 UAF란?

**UAF (Unreal Animation Framework)**는 Epic Games가 개발 중인 차세대 애니메이션 시스템입니다.

- 이전 이름: **AnimNext** (UE 5.6까지)
- UE 5.7부터 **UAF**로 리브랜딩
- 기존 **Animation Blueprint(ABP)**를 완전히 대체할 예정
- 현재 상태: **Experimental** (실험적)

> Epic Games: "UAF는 5.8에서 첫 번째 공식 데모가 나올 예정입니다. GASP(Game Animation Sample Project)에서 UAF로 구성된 캐릭터를 선보일 계획입니다."

---

## 1.2 왜 UAF인가?

### 기존 ABP의 한계

```
Character BP (매 프레임):
  Get Anim Instance
    -> Cast to MyABP          <- 강한 결합
      -> Set Velocity          <- 수동 전달
      -> Set Acceleration      <- 수동 전달
      -> Set MovementMode      <- 수동 전달
      -> ... (수십 개의 Set 노드)  <- 유지보수 어려움
```

### UAF의 해결책

```
AnimNextComponent (자동):
  MoverComponent.Velocity      -> 자동 읽기
  MoverComponent.Acceleration  -> 자동 읽기
  Actor.GetActorTransform()    -> 자동 읽기
  (Cast 불필요, Set 노드 불필요)
```

---

## 1.3 ABP vs UAF 비교

| 항목 | ABP (기존) | UAF (차세대) |
|------|-----------|-------------|
| **최상위 에셋** | AnimBlueprint | Workspace |
| **로직 작성** | EventGraph | System (Module) |
| **애니메이션 그래프** | AnimGraph (재귀 트리) | Animation Graph (스택 기반) |
| **실행 엔진** | 애니메이션 스레드 | RigVM (완전 멀티스레드) |
| **상태 관리** | 노드가 상태 보유 | Trait는 무상태 (스레드 안전) |
| **변수 전달** | Character -> ABP 수동 Set | Data Interface 자동 바인딩 |
| **애니메이션 선택** | State Machine | Chooser + Motion Matching |
| **블렌딩** | Blend 노드 트리 | TraitStack 합성 |
| **성능** | AnimGameThreadTime 소비 | AnimGameThreadTime 소비 안 함 |
| **메모리** | 객체 기반 (캐시 미스) | 연속 메모리 (캐시 효율적) |

---

## 1.4 매 프레임 실행 비교

### ABP 실행 순서
```
1. [Game Thread]   AnimInstance::NativeUpdateAnimation()
2. [Game Thread]   BlueprintThreadSafeUpdateAnimation()  <- 무거운 로직
3. [Worker Thread] AnimGraph 평가 (State Machine, MM 등)
4. [Game Thread]   최종 포즈 -> SkeletalMeshComponent
```

### UAF 실행 순서
```
1. [RigVM Worker] System 실행: Reference Pose -> Data Interface -> Module
2. [RigVM Worker] Animation Graph: Chooser -> Motion Matching -> TraitStack
3. [Any Thread]   최종 포즈 -> SkeletalMeshComponent
```

**핵심 차이**: ABP는 Game Thread에서 무거운 로직을 실행하지만, UAF는 거의 모든 것을 RigVM Worker Thread에서 실행합니다.

---

## 1.5 UAF 에셋 계층 구조

```
Workspace (최상위 컨테이너)
  |
  |-- System          실행 흐름 정의 ("무엇을 어떤 순서로 실행할지")
  |                    = ABP의 EventGraph
  |
  |-- Animation Graph  애니메이션 평가
  |                    = ABP의 AnimGraph
  |
  |-- Shared Variables 모듈/그래프 간 공유 변수
  |                    = ABP의 멤버 변수
  |
  |-- (Module)         비즈니스 로직 (UE 5.6 용어)
  |                    = ABP의 Update 함수들
  |
  +-- Data Interface   외부 데이터 자동 수집
                       = ABP의 수동 Set 노드 대체
```

---

## 1.6 UAF 타임라인

| UE 버전 | UAF 상태 | 주요 변화 |
|---------|---------|----------|
| **5.4** | 초기 등장 | AnimNext로 실험적 플러그인 추가, AnimNextMeshComponent 도입 |
| **5.5** | Experimental | 초기 개발, 최소한의 공개 API |
| **5.6** | Experimental | 내부적으로 "Module"이라 불림, Chooser 연동에 DataInterfaceInstance 필요 |
| **5.7** | Experimental, 리브랜딩 | **"UAF"로 이름 변경**, Motion Matching 노드 추가, Mover 2.0 통합 개선 |
| **5.8** (예정) | Experimental | GASP에서 UAF 캐릭터 첫 공개, 커뮤니티 실습 가능 |
| **향후** | Production-Ready 목표 | ABP 완전 대체 |

---

## 1.7 ABP에서 UAF로의 점진적 전환

UAF Animation Graph는 기존 ABP 안에서 특별한 애니메이션 노드를 통해 실행할 수 있습니다.
이를 통해 **점진적 마이그레이션**이 가능합니다:

```
기존 ABP
  |-- AnimGraph
  |     |-- ... 기존 노드들 ...
  |     |-- [UAF Graph Node]  <- UAF 그래프를 ABP 안에서 실행
  |     |-- ... 기존 노드들 ...
```

한꺼번에 모든 것을 UAF로 바꿀 필요 없이, 일부 기능부터 UAF로 전환하면서 동일한 결과를 얻을 수 있습니다.

---

[목차로 돌아가기](./00_INDEX.md) | [다음: 플러그인 설정 ->](./02_PLUGIN_SETUP.md)
