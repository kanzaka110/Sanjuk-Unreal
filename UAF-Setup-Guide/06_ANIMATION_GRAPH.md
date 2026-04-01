# 06. Animation Graph

[<- 이전: System EventGraph](./05_SYSTEM_EVENTGRAPH.md) | [목차](./00_INDEX.md) | [다음: Data Interface ->](./07_DATA_INTERFACE.md)

---

## 6.1 Animation Graph란?

Animation Graph는 ABP의 **AnimGraph**에 해당합니다.
기존의 다양한 애니메이션 노드(State Machine, Blend Space 등) 대신 **TraitStack** 기반의 합성 방식을 사용합니다.

---

## 6.2 기본 구성: Chooser + Motion Matching

가장 일반적인 구성:

```
[Evaluate Chooser]  ──>  [Motion Matching]  ──>  Output Pose
       |                        |
       |                        +-- Trajectory 입력
       |                            (System에서 계산)
       |
       +-- Chooser Table 참조
           (PSD 목록 + 입력 변수 포함)
```

### Evaluate Chooser 노드
- **역할**: Chooser Table을 평가하여 조건에 맞는 PoseSearchDatabase 목록을 반환
- **입력**: Chooser Table 에셋 참조
- **출력**: 매칭에 사용할 Database 목록

### Motion Matching 노드
- **역할**: 주어진 Database와 Trajectory로 최적의 애니메이션 포즈를 검색
- **입력**: Database 목록 (Chooser에서) + Trajectory (System에서)
- **출력**: 최적 포즈

---

## 6.3 TraitStack 아키텍처

### 기존 ABP 방식 (재귀 트리)
```
OutputPose 요청
  -> FootPlacement가 포즈 요청
    -> Warping이 포즈 요청
      -> AimOffset이 포즈 요청
        -> StateMachine이 포즈 요청
          -> MotionMatching이 포즈 반환
        <- AimOffset 적용
      <- Warping 적용
    <- FootPlacement 적용
  <- OutputPose 완료

(깊은 재귀 호출 스택, 캐시 비효율적)
```

### UAF TraitStack 방식 (LIFO 스택)
```
EvaluationProgram (스택 기반):
  1. PUSH: MotionMatching -> 기본 포즈 생성
  2. APPLY: AimOffset -> 위에 적용
  3. APPLY: OrientationWarping -> 위에 적용
  4. APPLY: StrideWarping -> 위에 적용
  5. APPLY: FootPlacement -> 위에 적용
  6. APPLY: OffsetRootBone -> 위에 적용
  7. POP: 최종 포즈 반환

(플랫 실행, 최소 호출 오버헤드, 캐시 친화적)
```

---

## 6.4 Trait 개념

**Trait**는 ABP의 개별 애니메이션 노드를 대체하는 재사용 가능한 기능 단위입니다.

### 핵심 특성
- **무상태(Stateless)**: Trait는 내부 상태를 보유하지 않음
- **스레드 안전**: 여러 Worker Thread에서 동시 실행 가능
- **합성 가능**: 여러 Trait를 스택으로 조합

### Trait 데이터 타입

| 타입 | 설명 | 특성 |
|------|------|------|
| **FSharedData** | 읽기 전용 공유 데이터 | USTRUCT, 직렬화됨, 설정값 |
| **FInstanceData** | 인스턴스별 동적 데이터 | Raw C++ 구조체, 런타임 |
| **Latent Properties** | 인스턴스화 필요한 공유 데이터 | SharedData + Instance 혼합 |

### 상태 저장 위치
Trait 자체는 무상태이므로, 프레임 간 유지가 필요한 상태는 다음에 저장:
- Shared Variables (Workspace 레벨)
- Data Interface 변수
- Module 로컬 변수

---

## 6.5 Animation Graph에서 바인딩 사용

Animation Graph도 System과 동일한 바인딩 시스템을 사용합니다.
Graph의 Details 패널에서 필요한 컴포넌트를 바인딩합니다:

| 변수명 | 용도 |
|--------|------|
| `Mover_Component` | 궤적 데이터 접근 |
| `Skeletal_Mesh_Component` | 메시 참조 |
| `CurrentActor` | 소유 Actor 참조 |

---

## 6.6 Graph 구성 팁

1. **Chooser Table을 먼저 설정**: Motion Matching의 입력이 되므로
2. **Trajectory는 System에서 계산**: Graph에서는 이미 계산된 값을 사용
3. **포즈 출력은 하나**: Graph의 최종 출력이 System의 Write Pose to Mesh로 전달
4. **복잡한 로직은 Module에서**: Graph는 애니메이션 평가에 집중

---

[<- 이전: System EventGraph](./05_SYSTEM_EVENTGRAPH.md) | [목차](./00_INDEX.md) | [다음: Data Interface ->](./07_DATA_INTERFACE.md)
