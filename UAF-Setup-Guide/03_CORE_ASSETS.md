# 03. 핵심 에셋 이해

[<- 이전: 플러그인 설정](./02_PLUGIN_SETUP.md) | [목차](./00_INDEX.md) | [다음: 단계별 셋업 ->](./04_STEP_BY_STEP_SETUP.md)

---

## 3.1 UAF 에셋 종류

Content Browser 우클릭 -> Animation 에서 생성할 수 있는 UAF 에셋:

| 에셋 타입 | ABP 대응 | 역할 |
|----------|---------|------|
| **UAF Workspace** | AnimBlueprint 자체 | 모든 UAF 에셋을 묶는 에디터 샌드박스 |
| **UAF System** | EventGraph | 매 프레임 실행 흐름 정의 (Initialize, PrePhysics) |
| **UAF Animation Graph** | AnimGraph | 애니메이션 로직 (TraitStack 기반) |
| **UAF Shared Variables** | ABP 멤버 변수 | System/Graph 간 공유 변수 |
| **UAF State Tree** | State Machine | 상태 머신 로직 |
| **UAF Label Binding** | - | 레이블 바인딩 |
| **UAF Label Collection** | - | 레이블 모음 |
| **UAF Set Binding** | - | 세트 바인딩 |
| **UAF Set Collection** | - | 세트 모음 |
| **UAF Asset Wizard** | - | 자동 에셋 생성 마법사 |

---

## 3.2 Workspace (작업 공간)

**Workspace**는 UAF의 최상위 컨테이너입니다.

### 역할
- 여러 UAF 에셋(System, Graph, Variables)을 **한 곳에서 편집**
- 에디터 샌드박스 -- System과 Graph를 드래그 앤 드롭으로 등록
- ABP 에디터처럼 하나의 창에서 모든 애니메이션 작업 수행

### Workspace 에디터 레이아웃
```
+----------------------------------------------------------+
| WS_MyCharacter - Workspace Editor                         |
+------------+---------------------------+-----------------+
|            |                           |                 |
| Viewport   |     EventGraph            | Workspace      |
|            |     (System 그래프 편집)    | (에셋 트리)     |
+------------+                           +-----------------+
| Variables  |                           | Details         |
|            |                           | (속성 편집)     |
+------------+---------------------------+-----------------+
```

### 명명 규칙
- 접두사: `WS_`
- 예: `WS_UEFN_Mannequin`, `WS_MyCharacter`

---

## 3.3 System (시스템)

**System**은 ABP의 **EventGraph**에 해당합니다.

### 역할
- 매 프레임의 **실행 순서** 정의
- Initialize (1회) / PrePhysics (매 프레임) 이벤트 처리
- "무엇을 어떤 순서로 실행할지" 결정

### System EventGraph 구조
```
[Initialize]                    <- 시스템 시작 시 1회 실행
  -> Make Reference Pose         기본 포즈 생성

[PrePhysics]                    <- 매 프레임 실행
  -> Calculate Trajectory        궤적 계산 (Motion Matching용)
  -> Evaluate Animation Graph    애니메이션 그래프 실행
  -> Write Pose to Mesh          최종 포즈 적용
```

### 명명 규칙
- 접두사: `Sys_` 또는 `UAF_SY_`
- 예: `Sys_UEFN_Mannequin`, `UAF_SY_Main`

---

## 3.4 Animation Graph (애니메이션 그래프)

**Animation Graph**는 ABP의 **AnimGraph**에 해당합니다.

### 역할
- 실제 애니메이션 로직 처리
- TraitStack 기반의 데이터 합성 방식
- Chooser Table 평가 -> Motion Matching -> 포즈 출력

### ABP AnimGraph와의 차이
```
ABP AnimGraph:
  OutputPose <- FootPlacement <- Warping <- AimOffset <- StateMachine <- MotionMatching
  (재귀적 트리 -- 깊은 호출 스택)

UAF Animation Graph:
  1. PUSH: MotionMatching (기본 포즈 생성)
  2. APPLY: AimOffset
  3. APPLY: Warping
  4. APPLY: FootPlacement
  5. POP: 최종 포즈 반환
  (스택 기반 -- 플랫 실행, 캐시 효율적)
```

### 명명 규칙
- 접두사: `AG_` 또는 `UAF_AG_`
- 예: `AG_UEFN_Mannequin`, `UAF_AG_Main`

---

## 3.5 Shared Variables (공유 변수)

**Shared Variables**는 System과 Animation Graph 간에 데이터를 공유합니다.

### 역할
- Module에서 계산한 값을 Graph에서 읽기
- 예: Module이 `Speed2D` 계산 -> Graph가 `Speed2D`로 블렌드 결정

### Data Interface가 대체하는 변수
이전에 수동으로 전달하던 많은 변수가 Data Interface로 자동화됩니다:

| 기존 (ABP) | UAF | 방식 |
|-----------|-----|------|
| Velocity | Data Interface | 자동 (MoverComponent에서) |
| Acceleration | Data Interface | 자동 |
| MovementMode | Data Interface | 자동 |
| CharacterTransform | Data Interface | 자동 |
| Speed2D | Shared Variable | Module에서 1줄 계산 |
| HasVelocity | Shared Variable | Module에서 1줄 계산 |
| StateMachineState | Shared Variable | 수동 유지 |

### 명명 규칙
- 접두사: `SV_`
- 예: `SV_UEFN_Mannequin`

---

## 3.6 에셋 간 관계도

```
                    +-------------------+
                    |    Workspace      |
                    |  (WS_MyChar)      |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v---+  +------v------+  +----v---------+
     |   System   |  | Anim Graph  |  |   Shared     |
     | (Sys_MyChar)|  | (AG_MyChar) |  |  Variables   |
     +--------+---+  +------+------+  | (SV_MyChar)  |
              |              |         +----+---------+
              |              |              |
              |    +---------v---------+    |
              +--->| Data Interface    |<---+
                   | (자동 바인딩)       |
                   +-------------------+
                             |
                    +--------v---------+
                    | AnimNextComponent |
                    | (캐릭터 BP에 부착) |
                    +------------------+
```

---

[<- 이전: 플러그인 설정](./02_PLUGIN_SETUP.md) | [목차](./00_INDEX.md) | [다음: 단계별 셋업 ->](./04_STEP_BY_STEP_SETUP.md)
