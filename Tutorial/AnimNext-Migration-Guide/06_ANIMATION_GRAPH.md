# 06. Animation Graph 구축

[← 이전: Data Interface 구성](./05_DATA_INTERFACE.md) | [목차](./00_INDEX.md) | [다음: Chooser + Motion Matching →](./07_CHOOSER_AND_MOTION_MATCHING.md)

---

## 6.1 개요

이 단계에서는 기존 ABP의 **AnimGraph (22개 Anim 노드, 1개 State Machine)**를
UAF의 **Animation Graph + TraitStack**으로 재구성합니다.

### 기존 AnimGraph → UAF Animation Graph

```
기존 ABP AnimGraph:                    UAF Animation Graph:
┌─────────────────────────┐           ┌────────────────────────┐
│ State Machine            │           │ TraitStack             │
│   ├── 7 States          │           │   Base: Motion Match   │
│   └── 22 Transitions    │    →      │   +Add: Aim Offset    │
│ Aim Offset Node          │           │   +Add: Lean          │
│ Lean BlendSpace          │           │   +Add: Warping       │
│ Warping Nodes            │           │   +Add: Foot IK       │
│ Foot Placement           │           │   +Add: Root Offset   │
│ Root Offset              │           └────────────────────────┘
│ Output Pose              │
└─────────────────────────┘
  (복잡한 와이어링)                      (스택으로 깔끔하게 쌓기)
```

---

## 6.2 Animation Graph 생성

### 생성 단계

1. **Workspace 에디터** (`WS_SandboxCharacter`)를 엽니다

2. **Asset Tree** → **Graphs** 우클릭 → **Add New Animation Graph**

3. 이름: `AG_SandboxCharacter`

4. 그래프 에디터가 열립니다

### Animation Graph 에디터 화면

```
┌──────────────────────────────────────────────────────────┐
│  AG_SandboxCharacter - Animation Graph                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│   [Input Pose] ──▶ [TraitStack] ──▶ [Output Pose]       │
│                                                           │
│                                                           │
│   TraitStack 내부:                                       │
│   ┌─────────────────────────────────────┐                │
│   │  Slot 6: Foot Placement (Additive) │                │
│   │  Slot 5: Stride Warping (Additive) │                │
│   │  Slot 4: Orient. Warping (Additive)│                │
│   │  Slot 3: Lean (Additive)           │                │
│   │  Slot 2: Aim Offset (Additive)     │                │
│   │  Slot 1: Motion Matching (Base)    │  ← 기반       │
│   └─────────────────────────────────────┘                │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 6.3 TraitStack 구성

### 기존 ABP AnimGraph 노드 → TraitStack 슬롯 매핑

| 순서 | TraitStack 슬롯 | Trait 타입 | 기존 ABP 대응 노드 | 역할 |
|------|-----------------|-----------|-------------------|------|
| 1 (Base) | **Motion Matching** | Base Trait | State Machine + MM 노드 | 기반 포즈 생성 |
| 2 | **Aim Offset** | Additive | Aim Offset 노드 | 상체 조준 보정 |
| 3 | **Additive Lean** | Additive | Lean BlendSpace 노드 | 이동 기울기 |
| 4 | **Orientation Warping** | Additive | Orientation Warping 노드 | 방향 전환 보정 |
| 5 | **Stride Warping** | Additive | Stride Warping 노드 | 보폭 보정 |
| 6 | **Foot Placement** | Additive | Foot Placement 노드 | 발 IK |
| 7 | **Offset Root Bone** | Additive | Offset Root Bone 노드 | 루트 본 오프셋 |

### 각 Trait 상세 설정

#### Trait 1: Motion Matching (Base)

**이것이 핵심입니다.** 기존 State Machine의 역할을 대체합니다.

```
Motion Matching Trait 설정:
  ├── Pose History: 사용 (Get_PoseHistoryReference와 동일)
  ├── Database Selection: Chooser Table에서 동적 선택
  │     (자세한 내용은 07장 참조)
  ├── Blend Time: Get_MMBlendTime 로직 → Trait 파라미터
  ├── Interrupt Mode: Get_MMInterruptMode 로직 → Trait 파라미터
  └── Trajectory: Data Interface에서 자동 수집
```

기존 ABP에서의 대응:
- `Update_MotionMatching` → MM Trait의 Update 콜백
- `Update_MotionMatching_PostSelection` → MM Trait의 PostSelection 콜백
- `Get_MMBlendTime` → Trait 파라미터 바인딩
- `Get_MMInterruptMode` → Trait 파라미터 바인딩

#### Trait 2: Aim Offset (Additive)

```
Aim Offset Trait 설정:
  ├── Asset: BS_Neutral_AO_Stand
  │     (경로: /Game/Characters/UEFN_Mannequin/Animations/AimOffset/)
  ├── Alpha: Enable_AO() 결과에 따라 0.0 또는 1.0
  ├── X Value: Get_AOValue().X (Yaw)
  └── Y Value: Get_AOValue().Y (Pitch)
```

기존 ABP에서의 대응:
- `Enable_AO` → Alpha 파라미터 (0 또는 1)
- `Get_AOValue` → X, Y 입력 파라미터
- `Get_AO_Yaw` → X Value 파라미터

#### Trait 3: Additive Lean (Additive)

```
Additive Lean Trait 설정:
  ├── Asset: BS1D_Additive_Lean_Run
  │     (경로: /Game/Characters/UEFN_Mannequin/Animations/Poses/)
  ├── Alpha: 1.0 (항상 활성)
  └── Value: Get_LeanAmount() 결과
```

기존 ABP에서의 대응:
- `CalculateRelativeAccelerationAmount` → Lean 입력 계산
- `Get_LeanAmount` → BlendSpace 파라미터

#### Trait 4: Orientation Warping (Additive)

```
Orientation Warping Trait 설정:
  ├── Mode: Get_OrientationWarpingWarpingSpace() 결과
  ├── Target Rotation: TargetRotation (Workspace 변수)
  └── Enable: OffsetRootBoneEnabled (Workspace 변수)
```

기존 ABP에서의 대응:
- `Get_OrientationWarpingWarpingSpace` → Mode 파라미터
- `Get_OffsetRootRotationMode` → 회전 모드

#### Trait 5: Stride Warping (Additive)

```
Stride Warping Trait 설정:
  ├── Speed: Speed2D (Workspace 변수)
  ├── Enable: HasVelocity (Workspace 변수)
  └── Play Rate: Get_DynamicPlayRate() 로직 결과
```

기존 ABP에서의 대응:
- `Get_DynamicPlayRate` (53노드) → Stride Warping 파라미터

#### Trait 6: Foot Placement (Additive)

```
Foot Placement Trait 설정:
  ├── Plant Settings: Get_FootPlacementPlantSettings() 결과
  ├── Interpolation Settings: Get_FootPlacementInterpolationSettings() 결과
  ├── Foot Pinning: AllowFootPinning() 결과
  └── Mode: FootPlacementMode (Workspace 변수)
```

기존 ABP에서의 대응:
- `Get_FootPlacementPlantSettings` → Plant Settings
- `Get_FootPlacementInterpolationSettings` → Interpolation Settings
- `AllowFootPinning` → Foot Pinning Enable

#### Trait 7: Offset Root Bone (Additive)

```
Offset Root Bone Trait 설정:
  ├── Translation Mode: Get_OffsetRootTranslationMode() 결과
  ├── Translation HalfLife: Get_OffsetRootTranslationHalfLife() 결과
  ├── Translation Radius: OffsetRootTranslationRadius (Workspace 변수)
  ├── Rotation Mode: Get_OffsetRootRotationMode() 결과
  └── Enable: OffsetRootBoneEnabled (Workspace 변수)
```

---

## 6.4 TraitStack 노드 추가 방법

### Animation Graph에서 Trait 추가

1. **AG_SandboxCharacter** 그래프를 엽니다

2. **빈 공간 우클릭** → "Trait" 또는 특정 Trait 이름 검색

3. **Motion Matching** Trait를 추가합니다 (Base Trait)
   - UE 5.7에서는 "Motion Matching" 노드로 검색 가능

4. 이어서 Additive Trait들을 순서대로 추가:
   - Aim Offset
   - Blend Space Player (Lean용)
   - Orientation Warping
   - Stride Warping
   - Foot Placement
   - Offset Root Bone

5. **연결**:
   ```
   [Motion Matching] → [Aim Offset] → [Lean] → [Warping] → [Foot IK] → [Output]
   ```

### Trait 파라미터 바인딩

각 Trait의 입력 파라미터를 Workspace 변수 또는 Module 출력에 바인딩합니다:

```
예시: Aim Offset Trait의 Alpha 파라미터 바인딩

1. Aim Offset Trait 노드 선택
2. Details 패널에서 "Alpha" 프로퍼티 찾기
3. 바인딩 드롭다운 → "Bind to Variable" 선택
4. Module의 Enable_AO 출력 또는 Workspace 변수 선택
```

---

## 6.5 기존 AnimGraph 22개 Anim 노드 매핑

기존 ABP의 AnimGraph에 있는 22개 Anim 노드가 UAF에서 어떻게 대응되는지:

| # | 기존 Anim 노드 | UAF 대응 | 비고 |
|---|---------------|----------|------|
| 1 | State Machine (State Controller) | Motion Matching Trait | 7상태 → 1 MM 노드 |
| 2 | Motion Matching 노드 | MM Trait (Base) | 통합 |
| 3 | Blend Stack 노드 | MM Trait 내부 | 통합 |
| 4 | Chooser Evaluator | Chooser 바인딩 | 07장 참조 |
| 5 | Aim Offset 노드 | Aim Offset Trait | Additive |
| 6 | Lean BlendSpace | BlendSpace Trait | Additive |
| 7 | Orientation Warping | Warping Trait | Additive |
| 8 | Stride Warping | Warping Trait | Additive |
| 9 | Foot Placement | Foot Placement Trait | Additive |
| 10 | Offset Root Bone | Root Offset Trait | Additive |
| 11-15 | Blend 노드들 | TraitStack 자동 블렌딩 | 불필요 |
| 16-22 | 기타 보조 노드 | Trait 파라미터 또는 제거 | 간소화 |

**핵심**: 22개 노드가 ~7개 Trait로 축소됩니다.

---

## 6.6 평가 순서 이해

### 기존 ABP (재귀 트리 평가)

```
Output Pose를 요청
  → Foot Placement에 포즈 요청
    → Warping에 포즈 요청
      → Lean에 포즈 요청
        → Aim Offset에 포즈 요청
          → State Machine에 포즈 요청
            → Motion Matching → 포즈 반환
          ← Aim Offset 적용
        ← Lean 적용
      ← Warping 적용
    ← Foot Placement 적용
  ← Output Pose 완성

(깊은 재귀 호출 스택, 캐시 비효율)
```

### UAF TraitStack (LIFO 스택 평가)

```
EvaluationProgram (스택 기반):
  1. PUSH: Motion Matching → 기반 포즈 생성
  2. APPLY: Aim Offset → 기반 위에 적용
  3. APPLY: Lean → 그 위에 적용
  4. APPLY: Orientation Warping → 그 위에 적용
  5. APPLY: Stride Warping → 그 위에 적용
  6. APPLY: Foot Placement → 그 위에 적용
  7. APPLY: Offset Root Bone → 그 위에 적용
  8. POP: 최종 포즈 반환

(flat 실행, 함수 호출 오버헤드 최소, 캐시 친화적)
```

---

## 6.7 확인 체크리스트

- [ ] `AG_SandboxCharacter` Animation Graph 생성됨
- [ ] Base Trait (Motion Matching) 추가됨
- [ ] 6개 Additive Trait 추가됨 (AO, Lean, Warping x2, Foot, Root)
- [ ] 각 Trait의 파라미터가 Workspace 변수에 바인딩됨
- [ ] System에서 Animation Graph 실행 노드가 `AG_SandboxCharacter`를 참조
- [ ] 기존 ABP와 동일한 Anim 에셋 참조 확인 (BS_Neutral_AO_Stand 등)

### 현재 진행 상태

```
Phase 0: 사전 준비               ✅ 완료
Phase 1: 기반 구축               ✅ 완료
Phase 2: 애니메이션 파이프라인
  ├── Animation Graph 구축       ✅ 완료 (이번 단계)
  ├── Motion Matching 노드 설정  ⬜ 다음 단계
  └── Chooser Table 구성         ⬜ 다음 단계
Phase 3: 로직 이전               ⬜ 대기
Phase 4: 통합 & 검증             ⬜ 대기
```

---

[← 이전: Data Interface 구성](./05_DATA_INTERFACE.md) | [목차](./00_INDEX.md) | [다음: Chooser + Motion Matching →](./07_CHOOSER_AND_MOTION_MATCHING.md)
