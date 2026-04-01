# 07. Chooser + Motion Matching

[← 이전: Animation Graph 구축](./06_ANIMATION_GRAPH.md) | [목차](./00_INDEX.md) | [다음: Module 작성 →](./08_MODULES.md)

---

## 7.1 개요

이 단계에서는 기존 ABP의 **State Machine (7상태, 22트랜지션)**을
**Chooser Table + Motion Matching** 조합으로 대체합니다.

이것은 UAF 변환에서 가장 큰 아키텍처 변화입니다.

```
기존: 수동으로 연결된 State Machine
  → 각 상태에 진입/퇴장 조건을 하나하나 와이어링
  → 새 상태 추가 시 여러 트랜지션 추가 필요
  → 복잡해질수록 유지보수 어려움

UAF: Chooser Table + Motion Matching
  → 테이블에 조건-결과 행 추가만으로 확장
  → MM이 최적 포즈를 자동 선택
  → 블렌딩도 자동 처리
```

---

## 7.2 기존 State Machine 분석 (대체 대상)

### State Controller의 구조 요약

```
7개 상태:
  1. Transition to Idle      → 정지 전환
  2. Idle Loop               → 정지 유지
  3. Idle Break              → 정지 모션
  4. Transition to Locomotion → 이동 전환
  5. Locomotion Loop         → 이동 유지
  6. Transition to In Air    → 공중 전환
  7. In Air Loop             → 공중 유지

핵심 조건:
  - HasAcceleration: Idle ↔ Locomotion 전환
  - MovementMode: Ground ↔ InAir 전환
  - 애니메이션 완료: Transition → Loop 전환
```

### 왜 State Machine을 대체하나?

| 문제 | State Machine | Chooser + MM |
|------|--------------|-------------|
| 확장성 | 새 상태 추가 시 N개 트랜지션 필요 | 테이블에 행 1개 추가 |
| 블렌딩 | 수동으로 크로스페이드 설정 | MM이 자동 블렌딩 |
| 포즈 품질 | 고정된 상태별 애니메이션 | 실시간 최적 포즈 검색 |
| 유지보수 | 복잡한 와이어 그래프 | 읽기 쉬운 테이블 |
| 전환 자연스러움 | 크로스페이드에 의존 | 포즈 유사성 기반 전환 |

---

## 7.3 Chooser Table 설계

### Chooser Table이란?

Chooser는 **조건 컬럼과 결과 컬럼으로 구성된 의사결정 테이블**입니다.
런타임에 현재 조건과 가장 일치하는 행의 결과를 반환합니다.

### 메인 Chooser Table: CT_Locomotion

이 테이블이 기존 State Controller의 7개 상태를 대체합니다.

```
CT_Locomotion (Chooser Table):
┌───┬──────────────┬───────────────┬──────────┬────────┬───────────────────────┐
│ # │ MovementMode │ HasAcceleration│ IsInAir  │ Gait   │ → PoseSearch Database │
├───┼──────────────┼───────────────┼──────────┼────────┼───────────────────────┤
│ 1 │ Walking      │ false         │ false    │ *      │ DB_Idle               │
│ 2 │ Walking      │ true          │ false    │ Walk   │ DB_Walk               │
│ 3 │ Walking      │ true          │ false    │ Run    │ DB_Run                │
│ 4 │ Walking      │ true          │ false    │ Sprint │ DB_Sprint             │
│ 5 │ Falling      │ *             │ true     │ *      │ DB_InAir              │
│ 6 │ Walking      │ false         │ false    │ *      │ DB_IdleBreak          │
└───┴──────────────┴───────────────┴──────────┴────────┴───────────────────────┘

조건 컬럼: MovementMode, HasAcceleration, IsInAir, Gait
결과 컬럼: PoseSearch Database (Motion Matching에서 사용)
* = 와일드카드 (모든 값 매치)
```

### 기존 State Machine 상태 → Chooser 행 매핑

| 기존 상태 | Chooser 조건 | 결과 DB |
|----------|-------------|---------|
| Idle Loop | Walking + !HasAccel + !InAir | DB_Idle |
| Idle Break | Walking + !HasAccel + IdleTimer > N | DB_IdleBreak |
| Transition to Locomotion | Walking + HasAccel (시작 순간) | DB_Locomotion_Start |
| Locomotion Loop | Walking + HasAccel + Run | DB_Run |
| Transition to In Air | Falling (시작 순간) | DB_InAir_Start |
| In Air Loop | Falling | DB_InAir |
| Transition to Idle | Walking + !HasAccel (정지 순간) | DB_Locomotion_Stop |

> **핵심**: "Transition to X" 상태는 Chooser에서 별도 행이 아니라
> Motion Matching이 자연스러운 전환 포즈를 **자동으로 찾아줍니다.**
> DB에 Start/Stop 모션이 포함되어 있으면 MM이 알아서 선택합니다.

---

## 7.4 Chooser Table 생성

### 생성 단계

1. **Content Browser** → `/Game/Animation/UAF/Shared/Choosers/` 폴더로 이동

2. **우클릭** → **Miscellaneous** → **Chooser Table**

3. 이름: `CT_Locomotion`

4. 더블클릭하여 Chooser 에디터를 엽니다

### Chooser 에디터에서 설정

#### 조건 컬럼 추가

1. **+ Column** 버튼 클릭

2. 다음 컬럼들을 추가:

| 컬럼 이름 | 타입 | 소스 |
|----------|------|------|
| `MovementMode` | Gameplay Tag / Enum | Data Interface 또는 Workspace 변수 |
| `HasAcceleration` | Bool | Workspace 변수 |
| `Gait` | Gameplay Tag / Enum | Workspace 변수 |
| `IsInAir` | Bool | MovementMode == Falling |

3. 각 컬럼의 **Evaluation** 소스를 설정:
   - Workspace 공유 변수 바인딩
   - 또는 Data Interface에서 직접 읽기

#### 결과 컬럼 설정

1. **Result Column** 타입: `PoseSearchDatabase` (오브젝트 참조)

2. 또는 `Pose Search Column` (UE 5.7의 실험적 기능)을 사용하면
   Chooser와 Pose Search가 더 긴밀하게 통합됩니다.

#### 행 추가

1. **+ Row** 버튼으로 행 추가

2. 각 행에 조건 값과 결과 DB를 설정

```
예시 행 설정:
  Row 1:
    MovementMode: Walking
    HasAcceleration: false
    Gait: (any)
    IsInAir: false
    → Result: DB_Idle
```

---

## 7.5 Pose Search Database 구성

### 기존 DB 재활용

프로젝트에 이미 Pose Search를 사용하고 있으므로, 기존 DB를 재활용할 수 있습니다.

기존 ABP에서 사용하던 DB:
- `CurrentSelectedDatabase` 변수에 할당되던 DB들
- `ValidDatabases` 배열의 DB들

### DB 구성 권장 구조

```
/Game/Animation/PoseSearch/
├── DB_Idle/
│   ├── PSD_Idle_Neutral         ← 기본 Idle
│   └── PSD_Idle_Breaks          ← Idle Break 모션
├── DB_Locomotion/
│   ├── PSD_Walk_FWD             ← 걷기 전방
│   ├── PSD_Walk_Strafe          ← 걷기 스트레이프
│   ├── PSD_Run_FWD              ← 달리기 전방
│   ├── PSD_Run_Strafe           ← 달리기 스트레이프
│   ├── PSD_Sprint               ← 스프린트
│   ├── PSD_Start_*              ← 출발 모션들
│   ├── PSD_Stop_*               ← 정지 모션들
│   └── PSD_Pivot_*              ← 방향 전환 모션들
├── DB_InAir/
│   ├── PSD_Jump_Start           ← 점프 시작
│   ├── PSD_Fall_Loop            ← 낙하 루프
│   └── PSD_Land_*               ← 착지 모션들
└── DB_Slide/
    └── PSD_Slide                ← 슬라이드 (있는 경우)
```

### Chooser에서 DB 선택 흐름

```
매 프레임:

1. Chooser Table 평가:
   현재 조건: {Walking, HasAccel=true, Run, !InAir}
     → 매칭 행: Row 3
       → 결과: DB_Run

2. Motion Matching 실행:
   DB_Run에서 현재 궤적과 가장 유사한 포즈 검색
     → 최적 애니메이션 프레임 선택
       → TraitStack의 Base 포즈로 사용

3. 조건 변경 시 (예: 정지):
   현재 조건: {Walking, HasAccel=false, Run, !InAir}
     → 매칭 행: Row 1
       → 결과: DB_Idle
   DB_Idle에서 현재 포즈와 가장 유사한 Idle 포즈 검색
     → 자연스러운 정지 전환 (크로스페이드 불필요!)
```

---

## 7.6 Motion Matching Trait에 Chooser 연결

### Animation Graph에서 연결

1. `AG_SandboxCharacter` Animation Graph를 엽니다

2. **Motion Matching** Trait (Base) 노드를 선택합니다

3. **Details 패널**에서 다음을 설정:

| 프로퍼티 | 값 | 설명 |
|---------|-----|------|
| **Database Source** | Chooser | "직접 지정" 대신 "Chooser에서 선택" |
| **Chooser Table** | CT_Locomotion | 위에서 만든 Chooser Table |
| **Trajectory** | Workspace 변수 바인딩 | Module에서 계산한 궤적 |
| **Pose History** | 자동 | Trait가 자동 관리 |

### 기존 ABP의 SetBlendStackAnimFromChooser와 비교

```
기존 ABP (64노드):
  SetBlendStackAnimFromChooser():
    1. StateMachineState 확인
    2. 상태별 분기 (Switch)
    3. 각 상태에 맞는 Chooser 평가
    4. 결과를 BlendStack에 전달
    5. 블렌드 시간/모드 설정
    6. 오류 처리 (NoValidAnim)
    7. ...

UAF (0노드, 자동):
  Motion Matching Trait:
    - Chooser Table: CT_Locomotion (선언적)
    - 자동으로 조건 평가 → DB 선택 → 포즈 검색 → 블렌딩
```

**결과**: 64노드 → 선언적 설정 (코드 없음)

---

## 7.7 기존 실험적 SM 함수 대응

기존 ABP의 실험적 State Machine 관련 함수들이 UAF에서 어떻게 대응되는지:

### OnStateEntry_* 함수들 (8개) → Chooser 조건으로 흡수

| 기존 함수 | UAF 대응 |
|----------|---------|
| `OnStateEntry_IdleLoop` | Chooser 행: !HasAccel → DB_Idle |
| `OnStateEntry_TransitionToIdle` | MM이 자동 전환 포즈 선택 |
| `OnStateEntry_LocomotionLoop` | Chooser 행: HasAccel → DB_Run |
| `OnStateEntry_TransitionToLocomotion` | MM이 자동 전환 포즈 선택 |
| `OnStateEntry_InAirLoop` | Chooser 행: IsInAir → DB_InAir |
| `OnStateEntry_TransitionToInAir` | MM이 자동 전환 포즈 선택 |
| `OnStateEntry_IdleBreak` | Chooser 행: IdleTimer 조건 |
| `OnStateEntry_SlideLoop` | Chooser 행: IsSliding → DB_Slide |

**결과**: 8개 콜백 함수 → Chooser Table 행으로 대체 (코드 없음)

### Get_DynamicPlayRate (53노드) → Stride Warping Trait

기존에는 상태별로 동적 재생 속도를 수동 계산했지만,
UAF에서는 **Stride Warping Trait**가 속도 기반 보폭 보정을 자동 처리합니다.

```
기존 (53노드):
  현재 상태 확인 → 속도 가져오기 → 애니메이션 속도와 비교
  → 비율 계산 → 클램프 → 재생 속도 반환

UAF:
  Stride Warping Trait:
    Input: Speed2D (Workspace 변수)
    → 자동으로 보폭 보정
```

### IsAnimationAlmostComplete (10노드) → MM 자동 전환

기존에는 "애니메이션이 거의 끝났는지" 수동 확인하여 전환을 트리거했지만,
MM은 궤적 기반으로 **애니메이션 종료 전에 미리 최적 전환 포즈를 찾습니다.**

---

## 7.8 Movement Direction 처리

### 기존 Update_MovementDirection (49노드)

```
기존 로직:
  1. 속도 방향과 전방 방향의 각도 계산
  2. 임계값(FL, FR, BL, BR)과 비교
  3. 방향 판정 (Forward, Backward, Left, Right)
  4. 이전 프레임과 비교하여 바이어스 적용
  5. MovementDirection 변수 설정
```

### UAF에서의 처리

Movement Direction은 **Chooser의 추가 조건 컬럼**으로 처리할 수 있습니다:

```
CT_Locomotion (확장):
┌───┬──────────┬──────────┬──────┬───────────┬─────────────────┐
│ # │ HasAccel │ Gait     │InAir │ Direction │ → Database      │
├───┼──────────┼──────────┼──────┼───────────┼─────────────────┤
│ 1 │ true     │ Run      │false │ Forward   │ DB_Run_Fwd      │
│ 2 │ true     │ Run      │false │ Backward  │ DB_Run_Bwd      │
│ 3 │ true     │ Run      │false │ Left      │ DB_Run_Left     │
│ 4 │ true     │ Run      │false │ Right     │ DB_Run_Right    │
│...│ ...      │ ...      │ ...  │ ...       │ ...             │
└───┴──────────┴──────────┴──────┴───────────┴─────────────────┘
```

또는 **하나의 큰 DB에 모든 방향을 포함**하고 MM이 궤적 기반으로 자동 선택하게 할 수도 있습니다:

```
DB_Locomotion:
  - Run_Fwd 시퀀스들
  - Run_Bwd 시퀀스들
  - Run_Left 시퀀스들
  - Run_Right 시퀀스들
  - Run_Pivot_* 시퀀스들

→ MM이 궤적과 가장 일치하는 방향의 애니메이션을 자동 선택
→ MovementDirection 변수 자체가 불필요해질 수 있음!
```

---

## 7.9 확인 체크리스트

- [ ] `CT_Locomotion` Chooser Table 생성됨
- [ ] 조건 컬럼 설정: MovementMode, HasAcceleration, Gait, IsInAir
- [ ] 결과 컬럼: PoseSearchDatabase 참조
- [ ] 기존 7개 상태에 대응하는 행 추가됨
- [ ] Motion Matching Trait에 Chooser Table 연결됨
- [ ] Pose Search DB 구조 확인 (기존 DB 재활용 가능 여부)
- [ ] 기존 OnStateEntry_* 함수의 로직이 Chooser 조건으로 흡수됨

---

[← 이전: Animation Graph 구축](./06_ANIMATION_GRAPH.md) | [목차](./00_INDEX.md) | [다음: Module 작성 →](./08_MODULES.md)
