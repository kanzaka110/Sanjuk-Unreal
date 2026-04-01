# 07. Data Interface & Bindings

[<- 이전: Animation Graph](./06_ANIMATION_GRAPH.md) | [목차](./00_INDEX.md) | [다음: Mover 2.0 연동 ->](./08_MOVER_INTEGRATION.md)

---

## 7.1 Data Interface란?

Data Interface는 UAF의 핵심 혁신 중 하나입니다.
기존 ABP에서 Character BP -> ABP로 수십 줄의 Set 노드를 사용하던 패턴을 **자동화**합니다.

### 기존 ABP 패턴 (제거됨)
```
Character BP Event Tick:
  Get Anim Instance
    -> Cast to MyABP                    <- 강한 결합
      -> Set Velocity                   <- 수동
      -> Set Acceleration               <- 수동
      -> Set MovementMode               <- 수동
      -> Set CharacterTransform         <- 수동
      -> ... (수십 개의 Set 노드)        <- 유지보수 악몽
```

### UAF Data Interface 패턴 (대체)
```
AnimNextComponent 자동 바인딩:
  MoverComponent.Velocity        -> 자동 읽기
  MoverComponent.Acceleration    -> 자동 읽기
  MoverComponent.MovementMode    -> 자동 읽기
  Actor.GetActorTransform()      -> 자동 읽기

  (Cast 불필요, Set 노드 불필요, 0줄의 수동 코드)
```

---

## 7.2 스레드 안전 데이터 교환

UAF는 Game Thread와 Worker Thread 간 데이터를 안전하게 교환합니다.

```
Game Thread                            Worker Thread
+-------------------------+           +-------------------------+
| Character BP / Mover    |           | UAF Module / Graph      |
| (게임 로직)               |           | (애니메이션 처리)         |
+------------+------------+           +------------+------------+
             |                                     ^
             v                                     |
    +--------+---------+                  +--------+---------+
    | PublicVariables   | -- dirty copy ->| PublicVariables   |
    | Proxy (GT 측)     | -- 매 프레임 --> | Proxy (WT 측)     |
    +------------------+                  +------------------+
```

### PublicVariablesProxy
- `UAnimNextComponent` 내부에 위치
- 변경된 (dirty-marked) 데이터만 매 프레임 복사
- 향후: 더블 버퍼링으로 성능 개선 예정

---

## 7.3 변수 분류

기존 ABP의 76개 변수가 UAF에서 어떻게 변하는지:

### A. Data Interface가 자동 대체 (삭제 가능)

| 기존 변수 | Data Interface 소스 |
|----------|-------------------|
| `Velocity` | MoverComponent.Velocity |
| `Acceleration` | MoverComponent.Acceleration |
| `MovementMode` | MoverComponent.MovementMode |
| `CharacterTransform` | Actor.GetActorTransform() |
| `Velocity_LastFrame` | 프레임 히스토리 자동 |
| `Mover` (참조) | Data Interface 직접 참조 |

### B. Module에서 간단히 계산 (대폭 축소)

| 기존 변수 | UAF 처리 | 기존 노드 수 -> UAF |
|----------|---------|-------------------|
| `Speed2D` | `Velocity.Size2D()` | 수 노드 -> 1줄 |
| `HasVelocity` | `Speed2D > 1.0` | 수 노드 -> 1줄 |
| `RelativeAcceleration` | InverseTransform | 29노드 -> 3노드 |

### C. 그대로 유지 (Shared Variables)

| 변수 | 이유 |
|------|------|
| `StateMachineState` | 커스텀 상태 로직 |
| `BlendStackInputs` | 블렌드 스택 입력 |
| `TargetRotation` | 목표 회전 |
| `TrajectoryGenerationData` | Pose Search 파라미터 |
| Debug 변수들 | 디버그 전용 |

### 요약
```
기존 76개 변수
  |-- 삭제 (Data Interface 대체):  ~12개
  |-- 대폭 축소 (Module 간소화):   ~15개 -> 각 1~3줄
  |-- 유지 (Shared Variables):     ~30개
  +-- 삭제 (Debug, UAF 내장):     ~19개
                                   -----
                                   ~30개로 축소 (60% 감소)
```

---

## 7.4 Blueprint에서 변수 설정

게임플레이 코드에서 UAF 시스템으로 변수를 보내는 방법:

### C++
```cpp
UAnimNextComponent* AnimComp = FindComponentByClass<UAnimNextComponent>();
AnimComp->SetVariable(FName("Speed2D"), 350.0f);
AnimComp->SetVariable(FName("IsJumping"), true);
AnimComp->SetVariable(FName("TargetRotation"), FVector(0, 90, 0));
```

### Blueprint
1. AnimNext Component 참조 가져오기
2. **Set Variable** 노드 사용
3. 변수 이름 + 값 지정

---

## 7.5 바인딩 시스템 상세

UAF의 바인딩은 컴포넌트 참조를 이름으로 자동 해결합니다.

### 바인딩 Locator Fragment 종류

| Fragment | 설명 | 예시 |
|----------|------|------|
| **Current Actor** | 소유 Actor | 시작점 |
| **Component** | Actor의 컴포넌트 | MoverComponent |
| **Property** | 프로퍼티 접근 | Velocity |
| **Function** | 함수 호출 | GetSkeletalMeshComponent() |
| **Asset** | 에셋 참조 | PSD 에셋 |
| **Cast** | 타입 캐스트 | Cast to MyClass |
| **Actor** | 특정 Actor 참조 | - |

### 바인딩 체인 예시
```
Mover_Component:
  Current Actor -> Component(MoverComponent)

Skeletal_Mesh_Component:
  Current Actor -> Function(GetSkeletalMeshComponent)

Velocity (Data Interface):
  Current Actor -> Component(MoverComponent) -> Property(Velocity)
```

---

[<- 이전: Animation Graph](./06_ANIMATION_GRAPH.md) | [목차](./00_INDEX.md) | [다음: Mover 2.0 연동 ->](./08_MOVER_INTEGRATION.md)
