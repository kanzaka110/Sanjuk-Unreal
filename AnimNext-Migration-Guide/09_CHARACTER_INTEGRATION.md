# 09. Character BP 연결

[← 이전: Module 작성](./08_MODULES.md) | [목차](./00_INDEX.md) | [다음: 디버깅 & 검증 →](./10_DEBUGGING_AND_VALIDATION.md)

---

## 9.1 개요

이 단계에서는 UAF 에셋들을 실제 캐릭터에 연결하여 동작하게 만듭니다.

핵심 작업:
1. AnimNextComponent 추가
2. SkeletalMeshComponent 애니메이션 비활성화
3. Workspace 할당
4. 기존 ABP 참조 제거

> **주의**: 테스트 캐릭터 (`BP_TestCharacter_UAF`)에서만 작업하세요.
> 기존 캐릭터를 수정하지 마세요.

---

## 9.2 현재 캐릭터 구조 (ABP 기반)

```
BP_SandboxCharacter (기존):
  ├── CapsuleComponent (Root)
  ├── SkeletalMeshComponent
  │     ├── Animation Mode: "Use Animation Blueprint"
  │     └── Anim Class: SandboxCharacter_CMC_ABP
  ├── MoverComponent
  ├── CharacterMovementComponent (또는 CMC)
  └── SpringArmComponent + CameraComponent
```

### 기존 데이터 흐름

```
Character BP (Tick):
  → MoverComponent 업데이트
  → 입력 처리
  → Get Anim Instance
    → Cast to SandboxCharacter_CMC_ABP
      → 변수 전달 (Velocity, Acceleration 등)

SkeletalMeshComponent:
  → AnimInstance(ABP) 평가
    → AnimGraph → State Machine → Output Pose
      → 스켈레탈 메시에 포즈 적용
```

---

## 9.3 UAF 캐릭터 구조 (목표)

```
BP_TestCharacter_UAF (목표):
  ├── CapsuleComponent (Root)
  ├── SkeletalMeshComponent
  │     ├── Animation Mode: "No Animation" ← 변경!
  │     └── Anim Class: None               ← 제거!
  ├── AnimNextComponent                    ← 새로 추가!
  │     └── Workspace: WS_SandboxCharacter
  ├── MoverComponent (유지)
  └── SpringArmComponent + CameraComponent (유지)
```

### UAF 데이터 흐름

```
Character BP (Tick):
  → MoverComponent 업데이트
  → 입력 처리
  → (변수 전달 불필요 - Data Interface 자동)

AnimNextComponent:
  → System 실행
    → Data Interface로 MoverComponent 데이터 자동 수집
    → Module 실행 (파생 값 계산)
    → Animation Graph 실행 (TraitStack 평가)
      → 최종 포즈 → SkeletalMeshComponent에 직접 전달
```

---

## 9.4 단계별 설정

### Step 1: 테스트 캐릭터 열기

1. Content Browser에서 `BP_TestCharacter_UAF`를 더블클릭
   (03장에서 기존 캐릭터를 복제한 것)

2. Blueprint 에디터가 열립니다

### Step 2: SkeletalMeshComponent 애니메이션 비활성화

**이것은 매우 중요합니다.**
UAF는 SkeletalMeshComponent의 내장 애니메이션 시스템을 **반드시 비활성화**해야 작동합니다.

1. **Components** 패널에서 `SkeletalMeshComponent` (보통 "Mesh")를 선택합니다

2. **Details** 패널에서 **Animation** 섹션을 찾습니다

3. 다음 설정을 변경합니다:

| 프로퍼티 | 기존 값 | 변경할 값 |
|---------|--------|----------|
| **Animation Mode** | Use Animation Blueprint | **No Animation** |
| **Anim Class** | SandboxCharacter_CMC_ABP | **(None)** |

```
⚠️ 경고: Animation Mode를 변경하지 않으면 UAF가 활성화되지 않습니다!
   기존 ABP와 UAF는 동시에 작동할 수 없습니다.
```

4. **Skeletal Mesh Asset**은 그대로 유지합니다 (SK_UEFN_Mannequin)

### Step 3: AnimNextComponent 추가

1. **Components** 패널 → **Add Component** 버튼 클릭

2. 검색: "AnimNext"

3. **AnimNextComponent** 선택하여 추가

4. 이름: `AnimNextComp` (또는 기본 이름 유지)

5. **Details** 패널에서 설정:

| 프로퍼티 | 값 | 설명 |
|---------|-----|------|
| **Workspace** | `WS_SandboxCharacter` | 04장에서 만든 Workspace |
| **Auto Activate** | true | 자동으로 활성화 |
| **Skeletal Mesh Component** | Mesh (자동 감지) | 포즈를 적용할 메시 |

```
Components 계층:
  BP_TestCharacter_UAF
    ├── CapsuleComponent (Root)
    ├── SkeletalMeshComponent (Mesh)     ← Animation Mode: No Animation
    ├── AnimNextComponent (AnimNextComp) ← Workspace: WS_SandboxCharacter
    ├── MoverComponent
    └── SpringArmComponent
          └── CameraComponent
```

### Step 4: 기존 ABP 관련 코드 제거

테스트 캐릭터의 Blueprint EventGraph에서:

1. **Get Anim Instance** 노드를 찾습니다
2. 관련된 **Cast to SandboxCharacter_CMC_ABP** 노드를 찾습니다
3. 이 노드들과 연결된 **변수 전달 로직**을 **삭제합니다**

```
삭제 대상:
  Get Anim Instance
    → Cast to SandboxCharacter_CMC_ABP
      → Set Velocity           ← 삭제 (Data Interface 대체)
      → Set Acceleration       ← 삭제 (Data Interface 대체)
      → Set MovementMode       ← 삭제 (Data Interface 대체)
      → Set CharacterProperties ← 삭제 (Data Interface 대체)
      → ... (모든 수동 전달 삭제)
```

> **참고**: 기존 캐릭터 BP가 아닌 테스트 캐릭터에서만 삭제하세요.

### Step 5: 인터페이스 처리

기존 ABP가 구현하던 인터페이스:
- `BPI_InteractionTransform`
- `BPI_SandboxCharacter_ABP`

UAF에서 이 인터페이스의 역할:

| 인터페이스 | 기존 역할 | UAF에서의 처리 |
|-----------|----------|--------------|
| `BPI_InteractionTransform` | 상호작용 트랜스폼 제공 | Data Interface로 대체 가능 |
| `BPI_SandboxCharacter_ABP` | ABP 전용 통신 | UAF용 새 인터페이스 또는 Data Interface |

필요한 경우 Character BP에서 직접 인터페이스를 구현하거나,
Data Interface를 통해 데이터를 제공합니다.

---

## 9.5 테스트 레벨 설정

### 테스트 레벨에서 캐릭터 배치

1. 테스트 레벨 (`L_UAF_Test`)을 엽니다

2. `BP_TestCharacter_UAF`를 레벨에 드래그 & 드롭

3. **World Settings**에서 Default Pawn Class를 `BP_TestCharacter_UAF`로 설정
   (또는 Player Start에서 직접 배치)

### 기존 캐릭터와 나란히 테스트

비교를 위해 기존 캐릭터도 함께 배치할 수 있습니다:

```
테스트 레벨:
  ├── BP_SandboxCharacter (기존, ABP)     ← 왼쪽에 배치
  ├── BP_TestCharacter_UAF (새로운, UAF)  ← 오른쪽에 배치
  └── Player Start (UAF 캐릭터 조종)
```

---

## 9.6 첫 실행 테스트

### 기대하는 동작

1. **PIE (Play In Editor)** 실행

2. 캐릭터가 **T-Pose가 아닌 Idle 포즈**로 서 있으면 성공

3. 이동 입력 시 **Motion Matching이 적절한 애니메이션을 재생**하면 성공

### 일반적인 문제와 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| **T-Pose로 서 있음** | AnimNextComponent가 Workspace를 찾지 못함 | Workspace 할당 확인 |
| **T-Pose로 서 있음** | SkeletalMeshComponent의 Animation Mode가 아직 ABP | "No Animation"으로 변경 |
| **애니메이션이 없음** | Chooser Table이 적절한 DB를 반환하지 않음 | Chooser 조건 확인 |
| **떨리는 애니메이션** | Data Interface 값이 올바르지 않음 | Module의 출력값 디버그 |
| **에디터 크래시** | 플러그인 호환성 문제 | 로그 확인, 에디터 재시작 |
| **이동이 안 됨** | MoverComponent 참조 끊김 | 컴포넌트 확인 |

### T-Pose 문제 디버그 순서

T-Pose는 가장 흔한 초기 문제입니다:

```
T-Pose 디버그 플로우차트:

1. AnimNextComponent가 있는가?
   └── No → Component 추가

2. Workspace가 할당되었는가?
   └── No → WS_SandboxCharacter 할당

3. SkeletalMeshComponent의 Animation Mode가 "No Animation"인가?
   └── No → "No Animation"으로 변경

4. System이 실행되고 있는가?
   └── Output Log에서 AnimNext 관련 메시지 확인

5. Animation Graph가 포즈를 생성하는가?
   └── AG_SandboxCharacter 그래프 확인

6. Motion Matching이 DB를 찾는가?
   └── Chooser Table + DB 경로 확인
```

---

## 9.7 기존 ABP로 롤백 방법

UAF가 제대로 작동하지 않을 때 기존 ABP로 빠르게 돌아가는 방법:

### 테스트 캐릭터에서 롤백

1. AnimNextComponent **비활성화** (Delete 또는 Active = false)

2. SkeletalMeshComponent 설정 복원:
   - Animation Mode: **Use Animation Blueprint**
   - Anim Class: **SandboxCharacter_CMC_ABP**

3. 기존 변수 전달 코드 복원 (삭제하지 않고 비활성화했다면)

> **팁**: 기존 코드를 삭제하는 대신 **비활성화된 노드** (우클릭 → Disable)로
> 남겨두면 롤백이 쉽습니다.

---

## 9.8 확인 체크리스트

- [ ] `BP_TestCharacter_UAF` 생성됨 (기존 캐릭터 복제)
- [ ] SkeletalMeshComponent Animation Mode = "No Animation"
- [ ] SkeletalMeshComponent Anim Class = None
- [ ] AnimNextComponent 추가됨
- [ ] AnimNextComponent.Workspace = WS_SandboxCharacter
- [ ] AnimNextComponent.Auto Activate = true
- [ ] 기존 ABP 변수 전달 코드 제거/비활성화
- [ ] 테스트 레벨에 캐릭터 배치됨
- [ ] PIE 실행 시 T-Pose가 아닌 올바른 포즈 확인
- [ ] 이동 시 애니메이션 전환 확인

### 현재 진행 상태

```
Phase 0: 사전 준비               ✅ 완료
Phase 1: 기반 구축               ✅ 완료
Phase 2: 애니메이션 파이프라인    ✅ 완료
Phase 3: 로직 이전               ✅ 완료
Phase 4: 통합 & 검증
  ├── Character BP 연결          ✅ 완료 (이번 단계)
  ├── 기존 ABP와 비교 검증       ⬜ 다음 단계
  └── 성능 프로파일링            ⬜ 다음 단계
```

---

[← 이전: Module 작성](./08_MODULES.md) | [목차](./00_INDEX.md) | [다음: 디버깅 & 검증 →](./10_DEBUGGING_AND_VALIDATION.md)
